"""Dimensional Battle System - Integrated combat using all dimensional mechanics.

This is the main battle system that replaces/extends the original Undertale-like
combat with the new dimensional mechanics:

1. Combat dimension determines fundamental rules
2. Perception states replace soul modes
3. Dimensional resonance provides combat bonuses
4. Battle box transforms based on dimension
5. Attack patterns are dimension-specific
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from .core import (
    CombatState, CombatPhase, CombatResult, CombatAction,
    PlayerSoul, CombatStats, DEFAULT_ITEMS
)
from .enemies import CombatEnemy, get_enemy
from .attacks import Bullet, BulletPattern, AttackSequence

from .dimensional_combat import (
    CombatDimension, PerceptionState, DimensionalCombatRules,
    DimensionalBullet, DimensionalPatternGenerator,
    get_dimension_from_enemy, PerceptionAbilities
)
from .dimensional_battlebox import DimensionalBattleBox, create_dimensional_battlebox
from .perception_system import (
    PerceptionController, PerceptionHUD, DimensionalResonance,
    ResonanceMeter, RESONANCE_ACTIONS
)


@dataclass
class DimensionalSoul:
    """Enhanced player soul with dimensional awareness."""
    
    x: float = 0.0
    y: float = 0.0
    
    # Movement
    speed: float = 200.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    
    # Dimensional position
    depth: float = 0.5  # 3D depth layer (0=front, 1=back)
    time_position: float = 0.0  # 4D time position
    
    # Collision
    radius: float = 8.0
    
    # State
    invincible: bool = False
    invincible_timer: float = 0.0
    invincible_duration: float = 1.0
    
    # Visual
    color: Tuple[int, int, int] = (255, 0, 0)  # Red by default
    pulse_timer: float = 0.0
    
    def update(
        self,
        dt: float,
        input_x: float,
        input_y: float,
        depth_input: float,
        rules: DimensionalCombatRules,
        box_bounds: Tuple[float, float, float, float]
    ) -> None:
        """Update soul with dimensional rules applied."""
        # Update invincibility
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Apply dimensional movement
        new_x, new_y, new_depth = rules.apply_movement(
            input_x, input_y, depth_input,
            self.x, self.y,
            self.speed, dt,
            box_bounds
        )
        
        self.x = new_x
        self.y = new_y
        self.depth = new_depth
        
        # Update visual pulse
        self.pulse_timer += dt * 5
        
        # Update color based on perception
        self._update_color(rules.current_perception)
    
    def _update_color(self, perception: PerceptionState) -> None:
        """Update soul color based on perception state."""
        colors = {
            PerceptionState.POINT: (100, 100, 255),
            PerceptionState.LINE: (100, 200, 255),
            PerceptionState.PLANE: (255, 0, 0),
            PerceptionState.VOLUME: (200, 100, 255),
            PerceptionState.HYPER: (255, 200, 100),
            PerceptionState.SHIFTING: (200, 200, 200),
            PerceptionState.FRACTURED: (255, 100, 100),
        }
        self.color = colors.get(perception, (255, 0, 0))
    
    def make_invincible(self, duration: Optional[float] = None) -> None:
        """Make soul invincible."""
        self.invincible = True
        self.invincible_timer = duration or self.invincible_duration
    
    def draw(self, screen: pygame.Surface, rules: DimensionalCombatRules) -> None:
        """Draw the soul with dimensional effects."""
        # Base soul
        x, y = int(self.x), int(self.y)
        
        # Pulsing effect
        pulse = abs(math.sin(self.pulse_timer)) * 0.2 + 0.8
        
        # Invincibility flicker
        if self.invincible and int(self.invincible_timer * 10) % 2 == 0:
            return  # Skip drawing for flicker effect
        
        # Perception-based visual effects
        perception = rules.current_perception
        
        if perception == PerceptionState.POINT:
            # Collapsed point - smaller, brighter
            radius = int(self.radius * 0.5)
            pygame.draw.circle(screen, (255, 255, 255), (x, y), radius + 2)
            pygame.draw.circle(screen, self.color, (x, y), radius)
            
        elif perception == PerceptionState.LINE:
            # Extended horizontally
            line_width = int(self.radius * 2)
            pygame.draw.ellipse(screen, self.color,
                              (x - line_width, y - int(self.radius * 0.5),
                               line_width * 2, int(self.radius)))
            
        elif perception == PerceptionState.VOLUME:
            # 3D effect - show depth indicator
            # Draw shadow based on depth
            shadow_offset = int((self.depth - 0.5) * 10)
            pygame.draw.circle(screen, (50, 50, 50),
                             (x + shadow_offset, y + abs(shadow_offset)), int(self.radius * 0.8))
            pygame.draw.circle(screen, self.color, (x, y), int(self.radius * pulse))
            
        elif perception == PerceptionState.HYPER:
            # Transcendent - glowing, trailing
            # Outer glow
            for i in range(3):
                glow_radius = int(self.radius * (1.5 + i * 0.3))
                glow_alpha = int(100 - i * 30)
                glow_surf = pygame.Surface((glow_radius * 2 + 4,) * 2, pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*self.color, glow_alpha),
                                 (glow_radius + 2, glow_radius + 2), glow_radius)
                screen.blit(glow_surf, (x - glow_radius - 2, y - glow_radius - 2))
            
            pygame.draw.circle(screen, self.color, (x, y), int(self.radius * pulse))
            pygame.draw.circle(screen, (255, 255, 255), (x, y), int(self.radius * 0.5))
            
        else:
            # Default plane perception
            pygame.draw.circle(screen, self.color, (x, y), int(self.radius * pulse))
        
        # Shifting effect
        if rules.is_shifting:
            shift_radius = int(self.radius * (1 + rules.shift_progress))
            pygame.draw.circle(screen, (255, 255, 255), (x, y), shift_radius, 1)


class DimensionalBattleSystem:
    """Main battle system with dimensional mechanics."""
    
    def __init__(self, screen_width: int = 640, screen_height: int = 480):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Combat state
        self.state: Optional[CombatState] = None
        self.enemy: Optional[CombatEnemy] = None
        
        # Dimensional systems
        self.dimension = CombatDimension.TWO_D
        self.rules = DimensionalCombatRules(dimension=self.dimension)
        self.resonance = DimensionalResonance()
        
        # Soul and battle box
        self.soul = DimensionalSoul()
        self.battle_box = create_dimensional_battlebox(screen_width, screen_height)
        
        # Input controller
        self.perception_controller = PerceptionController(self.rules)
        
        # HUD
        self.hud = PerceptionHUD(screen_width, screen_height)
        self.resonance_meter = ResonanceMeter(x=15, y=60)
        
        # Bullets (using dimensional bullets)
        self.bullets: List[DimensionalBullet] = []
        self.current_attack: Optional[str] = None
        
        # Input state
        self.input_x = 0.0
        self.input_y = 0.0
        
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
        self.dialogue_speed = 30.0
        
        # Grazing tracking
        self.grazed_bullets: set = set()
        self.graze_distance = 25.0
        
        # Callbacks
        self.on_battle_end: Optional[Callable[[CombatResult, int, int], None]] = None
    
    def start_battle(
        self,
        enemy_id: str,
        player_stats: Optional[CombatStats] = None
    ) -> bool:
        """Start a dimensional battle."""
        enemy = get_enemy(enemy_id)
        if not enemy:
            return False
        
        self.enemy = enemy
        
        # Determine combat dimension from enemy
        enemy_dim = getattr(enemy, 'dimension', '2d')
        self.dimension = get_dimension_from_enemy(enemy_dim)
        
        # Initialize dimensional rules
        self.rules = DimensionalCombatRules(dimension=self.dimension)
        self.rules.set_dimension(self.dimension)
        self.perception_controller = PerceptionController(self.rules)
        
        # Initialize battle box for dimension
        self.battle_box.set_dimension(self.dimension, instant=False)
        
        # Reset resonance
        self.resonance = DimensionalResonance()
        
        # Initialize combat state
        self.state = CombatState(
            phase=CombatPhase.INTRO,
            player_stats=player_stats or CombatStats(),
        )
        
        # Initialize soul position
        cx, cy = self.battle_box.center
        self.soul.x = cx
        self.soul.y = cy
        self.soul.depth = 0.5
        
        # Set intro dialogue
        self.state.current_dialogue = enemy.encounter_text
        self.dialogue_char_index = 0
        self.phase_timer = 0.0
        
        # Clear bullets
        self.bullets.clear()
        self.grazed_bullets.clear()
        
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
        
        # Update dimensional systems
        self.rules.update(dt)
        self.resonance.update(dt)
        self.battle_box.update(dt)
        
        # Phase-specific updates
        if self.state.phase == CombatPhase.INTRO:
            self._update_intro(dt)
        elif self.state.phase == CombatPhase.PLAYER_MENU:
            self._update_menu(dt)
        elif self.state.phase == CombatPhase.PLAYER_FIGHT:
            self._update_fight(dt)
        elif self.state.phase == CombatPhase.PLAYER_ACT:
            pass  # Input-driven
        elif self.state.phase == CombatPhase.PLAYER_ITEM:
            pass  # Input-driven
        elif self.state.phase == CombatPhase.PLAYER_MERCY:
            pass  # Input-driven
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
        self.dialogue_char_index += self.dialogue_speed * dt
        
        if self.phase_timer > 2.0:
            self._transition_to_menu()
    
    def _update_menu(self, dt: float) -> None:
        """Update menu phase."""
        pass
    
    def _update_fight(self, dt: float) -> None:
        """Update fight minigame."""
        if self.fight_bar_moving:
            self.state.fight_bar_position += self.fight_bar_direction * self.state.fight_bar_speed * dt
            
            if self.state.fight_bar_position >= 1.0:
                self.state.fight_bar_position = 1.0
                self.fight_bar_direction = -1
            elif self.state.fight_bar_position <= 0.0:
                self.state.fight_bar_position = 0.0
                self.fight_bar_direction = 1
    
    def _update_dialogue(self, dt: float) -> None:
        """Update dialogue phase."""
        self.dialogue_char_index += self.dialogue_speed * dt
        
        max_chars = len(self.state.current_dialogue)
        if self.dialogue_char_index >= max_chars and self.phase_timer > 1.5:
            self._start_enemy_attack()
    
    def _update_attack(self, dt: float) -> None:
        """Update enemy attack phase with dimensional mechanics."""
        # Get movement modifiers from perception
        x_mult, y_mult, depth_input, time_input = self.perception_controller.get_movement_modifiers()
        
        # Update soul
        self.soul.update(
            dt,
            self.input_x * x_mult,
            self.input_y * y_mult,
            depth_input,
            self.rules,
            self.battle_box.bounds
        )
        
        # Update attack timer
        self.state.attack_timer += dt
        
        # Get time slow factor
        abilities = PerceptionAbilities.for_state(self.rules.current_perception)
        effective_dt = dt * abilities.time_slow_factor
        
        # Update bullets with time slow
        for bullet in self.bullets:
            bullet.x += bullet.velocity_x * effective_dt
            bullet.y += bullet.velocity_y * effective_dt
            
            # Update temporal state for 4D
            if bullet.temporal_state:
                bullet.temporal_state.record_position(bullet.x, bullet.y)
        
        # Check collisions
        self._check_bullet_collisions()
        
        # Check grazing
        self._check_grazing()
        
        # Remove off-screen bullets
        self._cleanup_bullets()
        
        # Check if attack is done
        if self.state.is_attack_finished():
            self._end_attack_phase()
    
    def _check_bullet_collisions(self) -> None:
        """Check bullet collisions with dimensional rules."""
        for bullet in self.bullets:
            if not bullet.active:
                continue
            
            hit, damage = self.rules.check_bullet_collision(
                bullet,
                self.soul.x, self.soul.y,
                self.soul.radius
            )
            
            if hit and damage > 0:
                actual_damage = self.state.player_stats.take_damage(damage)
                
                if actual_damage > 0:
                    self.soul.make_invincible()
                    bullet.active = False
                    
                    # Fractured perception on hit
                    if random.random() < 0.1:  # 10% chance
                        self.rules.current_perception = PerceptionState.FRACTURED
                    
                    if not self.state.player_stats.is_alive:
                        self.state.phase = CombatPhase.DEFEAT
                        self.state.result = CombatResult.DEFEAT
    
    def _check_grazing(self) -> None:
        """Check for grazing near-misses."""
        for i, bullet in enumerate(self.bullets):
            if i in self.grazed_bullets or not bullet.active:
                continue
            
            dist = math.sqrt((self.soul.x - bullet.x)**2 + (self.soul.y - bullet.y)**2)
            hit_dist = bullet.radius + self.soul.radius
            graze_dist = hit_dist + self.graze_distance
            
            if hit_dist < dist <= graze_dist:
                self.grazed_bullets.add(i)
                
                # Build resonance and transcendence
                self.rules.add_transcendence(2.0)
                
                # Add resonance based on dimension
                dim_str = self.dimension.value
                self.resonance.add_resonance(dim_str, 3.0)
                self.resonance.add_resonance("plane", 1.0)  # Always some plane resonance
    
    def _cleanup_bullets(self) -> None:
        """Remove inactive bullets."""
        min_x, min_y, max_x, max_y = self.battle_box.bounds
        margin = 50
        
        active_bullets = []
        for bullet in self.bullets:
            if not bullet.active:
                continue
            
            # Check bounds
            if (bullet.x < min_x - margin or bullet.x > max_x + margin or
                bullet.y < min_y - margin or bullet.y > max_y + margin):
                continue
            
            active_bullets.append(bullet)
        
        self.bullets = active_bullets
    
    def _update_resolution(self, dt: float) -> None:
        """Update resolution phase."""
        if not self.state.player_stats.is_alive:
            self.state.phase = CombatPhase.DEFEAT
            self.state.result = CombatResult.DEFEAT
        elif not self.enemy.stats.is_alive:
            self.state.phase = CombatPhase.VICTORY
            self.state.result = CombatResult.VICTORY
        else:
            self.enemy.end_turn()
            self.state.advance_turn()
            self._transition_to_menu()
    
    def _update_ending(self, dt: float) -> None:
        """Update ending phase."""
        self.dialogue_char_index += self.dialogue_speed * dt
        
        if self.phase_timer > 3.0:
            self._end_battle()
    
    def _transition_to_menu(self) -> None:
        """Transition to player menu."""
        self.state.phase = CombatPhase.PLAYER_MENU
        self.phase_timer = 0.0
        self.menu_index = 0
        self.in_submenu = False
        
        # Return to plane perception
        self.rules.current_perception = PerceptionState.PLANE
        
        # Center soul
        cx, cy = self.battle_box.center
        self.soul.x = cx
        self.soul.y = cy
    
    def _start_enemy_attack(self) -> None:
        """Start enemy attack phase with dimensional patterns."""
        pattern = self.enemy.get_next_attack()
        
        self.state.start_attack_phase(pattern.duration)
        self.phase_timer = 0.0
        
        # Generate dimensional bullets
        self.bullets = self._generate_dimensional_attack(pattern)
        self.grazed_bullets.clear()
    
    def _generate_dimensional_attack(self, pattern) -> List[DimensionalBullet]:
        """Generate attack bullets based on dimension."""
        bounds = self.battle_box.bounds
        difficulty = getattr(pattern, 'base_difficulty', 1.0)
        
        if self.dimension == CombatDimension.ONE_D:
            attack_type = random.choice(["line_sweep", "converging_points", "segment_wave"])
            return DimensionalPatternGenerator.generate_1d_attack(bounds, attack_type, difficulty)
        
        elif self.dimension == CombatDimension.TWO_D:
            attack_type = random.choice(["triangle_formation", "square_grid", "circle_spiral"])
            return DimensionalPatternGenerator.generate_2d_attack(bounds, attack_type, difficulty)
        
        elif self.dimension == CombatDimension.THREE_D:
            attack_type = random.choice(["depth_wave", "phasing_cubes", "shadow_assault"])
            return DimensionalPatternGenerator.generate_3d_attack(bounds, attack_type, difficulty)
        
        elif self.dimension == CombatDimension.FOUR_D:
            attack_type = random.choice(["temporal_burst", "past_echo", "future_convergence"])
            return DimensionalPatternGenerator.generate_4d_attack(bounds, attack_type, difficulty)
        
        return []
    
    def _end_attack_phase(self) -> None:
        """End attack phase."""
        self.state.phase = CombatPhase.RESOLUTION
        self.phase_timer = 0.0
        self.bullets.clear()
    
    def _end_battle(self) -> None:
        """End battle and trigger callback."""
        if self.on_battle_end:
            xp = self.enemy.xp_reward if self.state.result == CombatResult.VICTORY else 0
            gold = self.enemy.gold_reward
            if self.state.result == CombatResult.SPARE:
                gold = self.enemy.spare_gold_reward
            
            self.on_battle_end(self.state.result, xp, gold)
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if not self.state:
            return False
        
        # Handle perception input during attack phase
        if self.state.phase == CombatPhase.ENEMY_ATTACK:
            if self.perception_controller.handle_input(event):
                return True
        
        # Movement input
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.input_x = -1
            elif event.key == pygame.K_RIGHT:
                self.input_x = 1
            elif event.key == pygame.K_UP:
                self.input_y = -1
            elif event.key == pygame.K_DOWN:
                self.input_y = 1
            elif event.key in (pygame.K_z, pygame.K_RETURN):
                return self._handle_confirm()
            elif event.key in (pygame.K_x, pygame.K_ESCAPE):
                return self._handle_cancel()
        
        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.input_x = 0
            elif event.key in (pygame.K_UP, pygame.K_DOWN):
                self.input_y = 0
        
        return True
    
    def _handle_confirm(self) -> bool:
        """Handle confirm button."""
        if self.state.phase == CombatPhase.INTRO:
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
            self.dialogue_char_index = len(self.state.current_dialogue)
            return True
        
        return False
    
    def _handle_cancel(self) -> bool:
        """Handle cancel button."""
        if self.in_submenu:
            self.in_submenu = False
            self.state.phase = CombatPhase.PLAYER_MENU
            return True
        return False
    
    def _select_menu_option(self) -> bool:
        """Select menu option."""
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
        """Confirm fight with resonance bonus."""
        self.fight_bar_moving = False
        
        position = self.state.fight_bar_position
        accuracy = 1.0 - abs(position - 0.5) * 2
        
        # Apply resonance damage bonus
        base_damage = self.state.player_stats.attack
        resonance_mult = self.resonance.get_damage_multiplier()
        damage = int(base_damage * (0.5 + accuracy * 1.5) * resonance_mult)
        
        actual_damage = self.enemy.stats.take_damage(damage)
        self.enemy.times_hurt += 1
        
        # Build resonance from attacking
        self.resonance.add_resonance("line", 5.0)  # Attacking builds line resonance
        
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
        """Confirm ACT with resonance-unlocked options."""
        if not self.enemy.act_options:
            return False
        
        # Get available acts (including resonance-unlocked ones)
        base_acts = [act.id for act in self.enemy.act_options]
        available_acts = self.resonance.get_available_acts(base_acts)
        
        if 0 <= self.submenu_index < len(self.enemy.act_options):
            act = self.enemy.act_options[self.submenu_index]
            
            if act.id == "check":
                self.state.current_dialogue = self.enemy.check_text
            else:
                success, dialogue, _ = self.enemy.perform_act(act.id)
                self.state.current_dialogue = dialogue
                
                # Build resonance from ACTs
                self.resonance.add_resonance("plane", 8.0)
            
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
                if item.heal_amount > 0:
                    healed = self.state.player_stats.heal(item.heal_amount)
                    self.state.current_dialogue = f"* You used {item.name}.\n* Recovered {healed} HP!"
                else:
                    self.state.current_dialogue = f"* You used {item.name}."
                
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
                    self.state.current_dialogue = "* Couldn't escape!"
                    self.state.phase = CombatPhase.ENEMY_DIALOGUE
            else:
                self.state.current_dialogue = "* Can't flee this battle!"
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
                max_index = 1
            else:
                max_index = 0
            
            self.submenu_index = max(0, min(max_index, self.submenu_index + direction))
        else:
            self.menu_index = max(0, min(3, self.menu_index + direction))
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the battle."""
        if not self.state:
            return
        
        # Draw battle box
        self.battle_box.draw(screen)
        
        # Draw bullets with dimensional effects
        if self.dimension == CombatDimension.THREE_D:
            self.battle_box.draw_bullets_with_depth(screen, self.bullets, self.soul.depth)
        elif self.dimension == CombatDimension.FOUR_D:
            abilities = PerceptionAbilities.for_state(self.rules.current_perception)
            self.battle_box.draw_temporal_bullets(
                screen, self.bullets,
                self.rules.time_position,
                abilities.can_see_trajectories
            )
        else:
            # Standard bullet drawing
            for bullet in self.bullets:
                if bullet.active:
                    pygame.draw.circle(screen, bullet.color,
                                     (int(bullet.x), int(bullet.y)), int(bullet.radius))
        
        # Draw soul
        if self.state.phase == CombatPhase.ENEMY_ATTACK:
            self.soul.draw(screen, self.rules)
        
        # Draw HUD
        self.hud.draw(screen, self.rules, self.dimension)
        self.resonance_meter.draw(screen, self.resonance)
        
        # Draw menu/dialogue
        self._draw_ui(screen)
    
    def _draw_ui(self, screen: pygame.Surface) -> None:
        """Draw menu and dialogue UI."""
        font = pygame.font.Font(None, 24)
        
        # Draw dialogue
        if self.state.current_dialogue:
            visible_text = self.state.current_dialogue[:int(self.dialogue_char_index)]
            dialogue_surf = font.render(visible_text, True, (255, 255, 255))
            screen.blit(dialogue_surf, (50, self.screen_height - 120))
        
        # Draw menu
        if self.state.phase == CombatPhase.PLAYER_MENU:
            actions = ["FIGHT", "ACT", "ITEM", "MERCY"]
            x = 80
            for i, action in enumerate(actions):
                color = (255, 255, 0) if i == self.menu_index else (255, 255, 255)
                text = font.render(action, True, color)
                screen.blit(text, (x, self.screen_height - 50))
                x += 120
        
        # Draw HP
        hp_text = f"HP {self.state.player_stats.hp}/{self.state.player_stats.max_hp}"
        hp_surf = font.render(hp_text, True, (255, 255, 255))
        screen.blit(hp_surf, (50, self.screen_height - 80))


def create_dimensional_battle_system(
    screen_width: int = 640,
    screen_height: int = 480
) -> DimensionalBattleSystem:
    """Create a new dimensional battle system."""
    return DimensionalBattleSystem(screen_width, screen_height)
