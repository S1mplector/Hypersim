"""Battle system - manages combat flow and state."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from .core import (
    CombatState, CombatPhase, CombatResult, CombatAction,
    PlayerSoul, SoulMode, CombatStats, InventoryItem, DEFAULT_ITEMS
)
from .enemies import CombatEnemy, EnemyMood, ACTOption, get_enemy
from .attacks import (
    Bullet, BulletPattern, AttackSequence,
    PatternGenerator, build_attack_from_pattern
)


@dataclass
class BattleBox:
    """The battle box where bullet hell happens."""
    x: float
    y: float
    width: float
    height: float
    
    # Animation
    target_x: float = 0.0
    target_y: float = 0.0
    target_width: float = 0.0
    target_height: float = 0.0
    animation_speed: float = 8.0
    
    # Border
    border_color: Tuple[int, int, int] = (255, 255, 255)
    border_width: int = 3
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get (min_x, min_y, max_x, max_y)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def set_target(self, x: float, y: float, width: float, height: float) -> None:
        """Set target position/size for animation."""
        self.target_x = x
        self.target_y = y
        self.target_width = width
        self.target_height = height
    
    def update(self, dt: float) -> None:
        """Animate towards target."""
        self.x += (self.target_x - self.x) * self.animation_speed * dt
        self.y += (self.target_y - self.y) * self.animation_speed * dt
        self.width += (self.target_width - self.width) * self.animation_speed * dt
        self.height += (self.target_height - self.height) * self.animation_speed * dt
    
    def snap_to_target(self) -> None:
        """Instantly move to target."""
        self.x = self.target_x
        self.y = self.target_y
        self.width = self.target_width
        self.height = self.target_height
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the battle box border."""
        rect = pygame.Rect(int(self.x), int(self.y), int(self.width), int(self.height))
        pygame.draw.rect(screen, self.border_color, rect, self.border_width)


class BattleSystem:
    """Main battle system that orchestrates combat."""
    
    def __init__(self, screen_width: int = 640, screen_height: int = 480):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Combat state
        self.state: Optional[CombatState] = None
        self.enemy: Optional[CombatEnemy] = None
        
        # Battle box
        self.battle_box = BattleBox(
            x=screen_width // 2 - 150,
            y=screen_height // 2 - 75,
            width=300,
            height=150
        )
        self.battle_box.set_target(
            self.battle_box.x, self.battle_box.y,
            self.battle_box.width, self.battle_box.height
        )
        
        # Active bullets
        self.bullets: List[Bullet] = []
        self.current_attack: Optional[AttackSequence] = None
        
        # Input state
        self.input_x = 0.0
        self.input_y = 0.0
        self.soul_moving = False
        self.last_soul_x = 0.0
        self.last_soul_y = 0.0
        
        # Menu state
        self.menu_index = 0
        self.submenu_index = 0
        self.in_submenu = False
        
        # Fight minigame
        self.fight_bar_moving = False
        self.fight_bar_direction = 1
        
        # Timing
        self.phase_timer = 0.0
        self.dialogue_char_index = 0
        self.dialogue_speed = 30.0  # chars per second
        
        # Callbacks
        self.on_battle_end: Optional[Callable[[CombatResult, int, int], None]] = None
        
        # Sound flags
        self.damage_sound_played = False
    
    def start_battle(self, enemy_id: str, player_stats: Optional[CombatStats] = None) -> bool:
        """Start a battle with an enemy."""
        enemy = get_enemy(enemy_id)
        if not enemy:
            return False
        
        self.enemy = enemy
        self.state = CombatState(
            phase=CombatPhase.INTRO,
            player_stats=player_stats or CombatStats(),
        )
        
        # Initialize soul position
        cx, cy = self.battle_box.center
        self.state.player_soul.x = cx
        self.state.player_soul.y = cy
        
        # Set intro dialogue
        self.state.current_dialogue = enemy.encounter_text
        self.dialogue_char_index = 0
        self.phase_timer = 0.0
        
        # Clear bullets
        self.bullets.clear()
        self.current_attack = None
        
        # Reset menu
        self.menu_index = 0
        self.submenu_index = 0
        self.in_submenu = False
        
        return True
    
    def update(self, dt: float) -> None:
        """Update battle state."""
        if not self.state or not self.enemy:
            return
        
        self.phase_timer += dt
        
        # Update battle box animation
        self.battle_box.update(dt)
        
        # Phase-specific updates
        if self.state.phase == CombatPhase.INTRO:
            self._update_intro(dt)
        elif self.state.phase == CombatPhase.PLAYER_MENU:
            self._update_menu(dt)
        elif self.state.phase == CombatPhase.PLAYER_FIGHT:
            self._update_fight(dt)
        elif self.state.phase == CombatPhase.PLAYER_ACT:
            self._update_act_menu(dt)
        elif self.state.phase == CombatPhase.PLAYER_ITEM:
            self._update_item_menu(dt)
        elif self.state.phase == CombatPhase.PLAYER_MERCY:
            self._update_mercy_menu(dt)
        elif self.state.phase == CombatPhase.ENEMY_DIALOGUE:
            self._update_dialogue(dt)
        elif self.state.phase == CombatPhase.ENEMY_ATTACK:
            self._update_attack(dt)
        elif self.state.phase == CombatPhase.RESOLUTION:
            self._update_resolution(dt)
        elif self.state.phase in (CombatPhase.VICTORY, CombatPhase.SPARE, CombatPhase.DEFEAT):
            self._update_ending(dt)
    
    def _update_intro(self, dt: float) -> None:
        """Update intro phase."""
        # Typewriter effect for dialogue
        self.dialogue_char_index += self.dialogue_speed * dt
        
        # Auto-advance after intro
        if self.phase_timer > 2.0:
            self._transition_to_menu()
    
    def _update_menu(self, dt: float) -> None:
        """Update player menu phase."""
        pass  # Menu is input-driven
    
    def _update_fight(self, dt: float) -> None:
        """Update fight minigame."""
        if self.fight_bar_moving:
            # Move the bar
            self.state.fight_bar_position += self.fight_bar_direction * self.state.fight_bar_speed * dt
            
            # Reverse at edges
            if self.state.fight_bar_position >= 1.0:
                self.state.fight_bar_position = 1.0
                self.fight_bar_direction = -1
            elif self.state.fight_bar_position <= 0.0:
                self.state.fight_bar_position = 0.0
                self.fight_bar_direction = 1
    
    def _update_act_menu(self, dt: float) -> None:
        """Update ACT submenu."""
        pass  # Input-driven
    
    def _update_item_menu(self, dt: float) -> None:
        """Update item submenu."""
        pass  # Input-driven
    
    def _update_mercy_menu(self, dt: float) -> None:
        """Update mercy submenu."""
        pass  # Input-driven
    
    def _update_dialogue(self, dt: float) -> None:
        """Update enemy dialogue phase."""
        self.dialogue_char_index += self.dialogue_speed * dt
        
        # Auto-advance after dialogue
        max_chars = len(self.state.current_dialogue)
        if self.dialogue_char_index >= max_chars and self.phase_timer > 1.5:
            self._start_enemy_attack()
    
    def _update_attack(self, dt: float) -> None:
        """Update enemy attack phase."""
        # Update soul
        self._update_soul_movement()
        self.state.player_soul.update(
            dt, self.input_x, self.input_y,
            self.battle_box.bounds
        )
        
        # Track if soul is moving
        dx = abs(self.state.player_soul.x - self.last_soul_x)
        dy = abs(self.state.player_soul.y - self.last_soul_y)
        self.soul_moving = (dx > 0.1 or dy > 0.1)
        self.last_soul_x = self.state.player_soul.x
        self.last_soul_y = self.state.player_soul.y
        
        # Update attack timer
        self.state.attack_timer += dt
        
        # Update attack sequence
        if self.current_attack:
            wave = self.current_attack.current_wave
            if wave:
                wave.elapsed += dt
                
                # Set soul mode
                if wave.soul_mode != self.state.player_soul.mode:
                    self.state.player_soul.set_mode(wave.soul_mode)
                
                # Update patterns
                for pattern in wave.patterns:
                    new_bullets = pattern.update(
                        dt, self.state.player_soul, self.battle_box.bounds
                    )
                    self.bullets.extend(new_bullets)
                
                # Check if wave is done
                if wave.elapsed >= wave.duration:
                    if not self.current_attack.advance_wave():
                        self.current_attack.completed = True
        
        # Update bullets
        for bullet in self.bullets:
            bullet.update(dt, self.state.player_soul, self.battle_box.bounds)
        
        # Check collisions
        self._check_bullet_collisions()
        
        # Remove inactive bullets
        self.bullets = [b for b in self.bullets if b.active]
        
        # Check if attack is done
        if self.state.is_attack_finished() or (self.current_attack and self.current_attack.completed):
            self._end_attack_phase()
    
    def _update_soul_movement(self) -> None:
        """Update soul input from current input state."""
        pass  # Input is set externally via handle_input
    
    def _check_bullet_collisions(self) -> None:
        """Check for bullet-soul collisions."""
        soul = self.state.player_soul
        
        for bullet in self.bullets:
            if bullet.check_hit(soul, self.soul_moving):
                # Take damage
                damage = bullet.damage
                actual_damage = self.state.player_stats.take_damage(damage)
                
                if actual_damage > 0:
                    soul.make_invincible()
                    bullet.active = False
                    
                    # Check defeat
                    if not self.state.player_stats.is_alive:
                        self.state.phase = CombatPhase.DEFEAT
                        self.state.result = CombatResult.DEFEAT
    
    def _update_resolution(self, dt: float) -> None:
        """Update resolution phase."""
        # Check win/lose conditions
        if not self.state.player_stats.is_alive:
            self.state.phase = CombatPhase.DEFEAT
            self.state.result = CombatResult.DEFEAT
        elif not self.enemy.stats.is_alive:
            self.state.phase = CombatPhase.VICTORY
            self.state.result = CombatResult.VICTORY
            self.state.current_dialogue = self.enemy.kill_dialogue
        else:
            # Continue to next turn
            self.enemy.end_turn()
            self.state.advance_turn()
            self._transition_to_menu()
    
    def _update_ending(self, dt: float) -> None:
        """Update ending phase."""
        self.dialogue_char_index += self.dialogue_speed * dt
        
        # End battle after delay
        if self.phase_timer > 3.0:
            self._end_battle()
    
    def _transition_to_menu(self) -> None:
        """Transition to player menu phase."""
        self.state.phase = CombatPhase.PLAYER_MENU
        self.phase_timer = 0.0
        self.menu_index = 0
        self.in_submenu = False
        
        # Reset soul mode
        self.state.player_soul.set_mode(SoulMode.RED)
        
        # Center soul
        cx, cy = self.battle_box.center
        self.state.player_soul.x = cx
        self.state.player_soul.y = cy
    
    def _start_enemy_attack(self) -> None:
        """Start the enemy attack phase."""
        pattern = self.enemy.get_next_attack()
        
        self.state.start_attack_phase(pattern.duration)
        self.state.current_dialogue = pattern.attack_dialogue
        self.dialogue_char_index = 0
        self.phase_timer = 0.0
        
        # Set soul mode
        self.state.player_soul.set_mode(pattern.soul_mode)
        
        # Build attack sequence
        self.current_attack = build_attack_from_pattern(
            pattern.pattern_type,
            self.battle_box.bounds,
            pattern.duration,
            difficulty=pattern.base_difficulty
        )
        
        # Clear old bullets
        self.bullets.clear()
    
    def _end_attack_phase(self) -> None:
        """End the attack phase."""
        self.state.phase = CombatPhase.RESOLUTION
        self.phase_timer = 0.0
        self.bullets.clear()
        self.current_attack = None
        
        # Reset soul mode
        self.state.player_soul.set_mode(SoulMode.RED)
    
    def _end_battle(self) -> None:
        """End the battle and trigger callback."""
        if self.on_battle_end:
            xp = self.enemy.xp_reward if self.state.result == CombatResult.VICTORY else 0
            gold = self.enemy.gold_reward
            if self.state.result == CombatResult.SPARE:
                gold = self.enemy.spare_gold_reward
            
            self.on_battle_end(self.state.result, xp, gold)
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input event. Returns True if consumed."""
        if not self.state:
            return False
        
        # Movement input for attack phase
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.input_x = -1
            elif event.key == pygame.K_RIGHT:
                self.input_x = 1
            elif event.key == pygame.K_UP:
                self.input_y = -1
            elif event.key == pygame.K_DOWN:
                self.input_y = 1
            elif event.key == pygame.K_z or event.key == pygame.K_RETURN:
                return self._handle_confirm()
            elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
                return self._handle_cancel()
        
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.input_x = 0
            elif event.key in (pygame.K_UP, pygame.K_DOWN):
                self.input_y = 0
        
        return True
    
    def _handle_confirm(self) -> bool:
        """Handle confirm button (Z/Enter)."""
        if self.state.phase == CombatPhase.INTRO:
            # Skip intro
            self._transition_to_menu()
            return True
        
        elif self.state.phase == CombatPhase.PLAYER_MENU:
            return self._select_menu_option()
        
        elif self.state.phase == CombatPhase.PLAYER_FIGHT:
            return self._confirm_fight()
        
        elif self.state.phase == CombatPhase.PLAYER_ACT:
            return self._confirm_act()
        
        elif self.state.phase == CombatPhase.PLAYER_ITEM:
            return self._confirm_item()
        
        elif self.state.phase == CombatPhase.PLAYER_MERCY:
            return self._confirm_mercy()
        
        elif self.state.phase == CombatPhase.ENEMY_DIALOGUE:
            # Skip dialogue
            self.dialogue_char_index = len(self.state.current_dialogue)
            return True
        
        return False
    
    def _handle_cancel(self) -> bool:
        """Handle cancel button (X/Escape)."""
        if self.in_submenu:
            self.in_submenu = False
            self.state.phase = CombatPhase.PLAYER_MENU
            return True
        return False
    
    def _select_menu_option(self) -> bool:
        """Select current menu option."""
        actions = [CombatAction.FIGHT, CombatAction.ACT, CombatAction.ITEM, CombatAction.MERCY]
        
        if 0 <= self.menu_index < len(actions):
            action = actions[self.menu_index]
            self.state.current_action = action
            
            if action == CombatAction.FIGHT:
                self.state.phase = CombatPhase.PLAYER_FIGHT
                self.fight_bar_moving = True
                self.state.fight_bar_position = 0.0
                self.fight_bar_direction = 1
            elif action == CombatAction.ACT:
                self.state.phase = CombatPhase.PLAYER_ACT
                self.in_submenu = True
                self.submenu_index = 0
            elif action == CombatAction.ITEM:
                self.state.phase = CombatPhase.PLAYER_ITEM
                self.in_submenu = True
                self.submenu_index = 0
            elif action == CombatAction.MERCY:
                self.state.phase = CombatPhase.PLAYER_MERCY
                self.in_submenu = True
                self.submenu_index = 0
            
            return True
        return False
    
    def _confirm_fight(self) -> bool:
        """Confirm fight timing."""
        self.fight_bar_moving = False
        
        # Calculate damage based on timing
        # Center = max damage, edges = min damage
        position = self.state.fight_bar_position
        accuracy = 1.0 - abs(position - 0.5) * 2  # 0 at edges, 1 at center
        
        base_damage = self.state.player_stats.attack
        damage = int(base_damage * (0.5 + accuracy * 1.5))  # 50%-200% based on accuracy
        
        # Apply damage to enemy
        actual_damage = self.enemy.stats.take_damage(damage)
        self.enemy.times_hurt += 1
        
        # Set dialogue
        if self.enemy.stats.is_alive:
            self.state.current_dialogue = f"* You dealt {actual_damage} damage!"
        else:
            self.state.current_dialogue = self.enemy.kill_dialogue or "* You won!"
            self.state.result = CombatResult.VICTORY
        
        self.state.phase = CombatPhase.ENEMY_DIALOGUE
        self.dialogue_char_index = 0
        self.phase_timer = 0.0
        
        return True
    
    def _confirm_act(self) -> bool:
        """Confirm ACT selection."""
        if not self.enemy.act_options:
            return False
        
        if 0 <= self.submenu_index < len(self.enemy.act_options):
            act = self.enemy.act_options[self.submenu_index]
            
            if act.id == "check":
                self.state.current_dialogue = self.enemy.check_text
            else:
                success, dialogue, _ = self.enemy.perform_act(act.id)
                self.state.current_dialogue = dialogue
            
            self.state.phase = CombatPhase.ENEMY_DIALOGUE
            self.dialogue_char_index = 0
            self.phase_timer = 0.0
            self.in_submenu = False
            
            return True
        return False
    
    def _confirm_item(self) -> bool:
        """Confirm item use."""
        if not self.state.inventory:
            self.state.current_dialogue = "* You have no items!"
            self.state.phase = CombatPhase.ENEMY_DIALOGUE
            self.dialogue_char_index = 0
            self.phase_timer = 0.0
            self.in_submenu = False
            return True
        
        if 0 <= self.submenu_index < len(self.state.inventory):
            item_id = self.state.inventory[self.submenu_index]
            item = DEFAULT_ITEMS.get(item_id)
            
            if item:
                # Use item
                if item.heal_amount > 0:
                    healed = self.state.player_stats.heal(item.heal_amount)
                    self.state.current_dialogue = f"* You ate the {item.name}.\n* You recovered {healed} HP!"
                else:
                    self.state.current_dialogue = f"* You used the {item.name}."
                
                # Remove if consumable
                if item.consumable:
                    self.state.inventory.remove(item_id)
            
            self.state.phase = CombatPhase.ENEMY_DIALOGUE
            self.dialogue_char_index = 0
            self.phase_timer = 0.0
            self.in_submenu = False
            
            return True
        return False
    
    def _confirm_mercy(self) -> bool:
        """Confirm mercy option."""
        mercy_options = ["Spare", "Flee"]
        
        if self.submenu_index == 0:  # Spare
            if self.enemy.is_spareable:
                self.state.current_dialogue = self.enemy.spare_dialogue
                self.state.phase = CombatPhase.SPARE
                self.state.result = CombatResult.SPARE
            else:
                self.enemy.times_spared += 1
                self.state.current_dialogue = "* You spared the enemy.\n* But nothing happened..."
                self.state.phase = CombatPhase.ENEMY_DIALOGUE
        
        elif self.submenu_index == 1:  # Flee
            if self.enemy.can_flee:
                flee_chance = 0.5 + self.state.flee_attempts * 0.1
                if random.random() < flee_chance:
                    self.state.current_dialogue = "* You fled!"
                    self.state.phase = CombatPhase.FLEE
                    self.state.result = CombatResult.FLEE
                else:
                    self.state.flee_attempts += 1
                    self.state.current_dialogue = "* You couldn't escape!"
                    self.state.phase = CombatPhase.ENEMY_DIALOGUE
            else:
                self.state.current_dialogue = "* You can't flee from this battle!"
                self.state.phase = CombatPhase.ENEMY_DIALOGUE
        
        self.dialogue_char_index = 0
        self.phase_timer = 0.0
        self.in_submenu = False
        
        return True
    
    def move_menu(self, direction: int) -> None:
        """Move menu selection."""
        if self.in_submenu:
            if self.state.phase == CombatPhase.PLAYER_ACT:
                max_index = len(self.enemy.act_options) - 1
            elif self.state.phase == CombatPhase.PLAYER_ITEM:
                max_index = len(self.state.inventory) - 1
            elif self.state.phase == CombatPhase.PLAYER_MERCY:
                max_index = 1  # Spare, Flee
            else:
                max_index = 0
            
            self.submenu_index = max(0, min(max_index, self.submenu_index + direction))
        else:
            self.menu_index = max(0, min(3, self.menu_index + direction))
