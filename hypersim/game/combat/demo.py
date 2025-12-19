"""Combat system demo - standalone test of the battle system.

Run with: python -m hypersim.game.combat.demo

Features demonstrated:
- Full combat flow (INTRO -> MENU -> FIGHT/ACT -> ATTACK -> RESOLUTION)
- All enemy types from each dimension
- Dimensional shift mechanics
- Grazing system
- Reality warping effects
- NPC dialogue preview
"""
from __future__ import annotations

import sys
import random
from typing import List, Optional

import pygame

from .core import CombatStats, CombatPhase, CombatResult
from .battle import BattleSystem
from .ui import CombatUI
from .enemies_expanded import get_all_expanded_enemies, get_expanded_enemy
from .dimensional_mechanics import (
    DimensionalCombatState, PerceptionLevel, RealityWarpType
)
from .realms import get_realms_for_dimension, ALL_REALMS
from .npcs import get_npcs_for_dimension, ALL_NPCS


class CombatDemo:
    """Standalone combat demo application."""
    
    def __init__(self, width: int = 800, height: int = 600):
        pygame.init()
        pygame.font.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("HyperSim Combat Demo")
        self.clock = pygame.time.Clock()
        
        # Systems
        self.battle_system = BattleSystem(width, height)
        self.combat_ui = CombatUI(self.screen)
        self.dimensional_state = DimensionalCombatState()
        
        # State
        self.running = True
        self.in_battle = False
        self.in_menu = True
        self.in_npc_dialogue = False
        
        # Menu state
        self.menu_mode = "main"  # main, dimension, enemy, npc
        self.selected_dimension = "1d"
        self.selected_index = 0
        self.available_enemies: List[str] = []
        self.available_npcs: List[str] = []
        
        # Player stats (persisted)
        self.player_stats = CombatStats(hp=50, max_hp=50, attack=15, defense=10)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Results
        self.last_result: Optional[CombatResult] = None
        self.total_xp = 0
        self.total_gold = 0
        self.battles_won = 0
        self.battles_fled = 0
        self.enemies_spared = 0
        
        # Dialogue state
        self.current_npc = None
        self.dialogue_index = 0
        
        # Load enemies
        self._load_enemies()
    
    def _load_enemies(self) -> None:
        """Load all available enemies."""
        all_enemies = get_all_expanded_enemies()
        self.enemies_by_dimension = {
            "1d": [],
            "2d": [],
            "3d": [],
            "4d": [],
        }
        
        for enemy_id, enemy in all_enemies.items():
            if enemy.dimension in self.enemies_by_dimension:
                self.enemies_by_dimension[enemy.dimension].append(enemy_id)
        
        self._update_available_enemies()
    
    def _update_available_enemies(self) -> None:
        """Update available enemies for selected dimension."""
        self.available_enemies = self.enemies_by_dimension.get(self.selected_dimension, [])
        self.available_npcs = [npc.id for npc in get_npcs_for_dimension(self.selected_dimension)]
        self.selected_index = 0
    
    def run(self) -> None:
        """Run the demo."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            self._handle_events()
            self._update(dt)
            self._draw()
            
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_events(self) -> None:
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if self.in_battle:
                    self._handle_battle_input(event)
                elif self.in_npc_dialogue:
                    self._handle_dialogue_input(event)
                else:
                    self._handle_menu_input(event)
    
    def _handle_menu_input(self, event: pygame.event.Event) -> None:
        """Handle menu input."""
        if event.key == pygame.K_ESCAPE:
            if self.menu_mode == "main":
                self.running = False
            else:
                self.menu_mode = "main"
                self.selected_index = 0
        
        elif event.key == pygame.K_UP:
            self.selected_index = max(0, self.selected_index - 1)
        
        elif event.key == pygame.K_DOWN:
            if self.menu_mode == "main":
                self.selected_index = min(5, self.selected_index + 1)
            elif self.menu_mode == "dimension":
                self.selected_index = min(3, self.selected_index + 1)
            elif self.menu_mode == "enemy":
                self.selected_index = min(len(self.available_enemies) - 1, self.selected_index + 1)
            elif self.menu_mode == "npc":
                self.selected_index = min(len(self.available_npcs) - 1, self.selected_index + 1)
        
        elif event.key == pygame.K_RETURN or event.key == pygame.K_z:
            self._select_menu_option()
        
        elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
            if self.menu_mode == "main" and self.selected_index == 0:
                # Change dimension
                dims = ["1d", "2d", "3d", "4d"]
                idx = dims.index(self.selected_dimension)
                if event.key == pygame.K_LEFT:
                    idx = (idx - 1) % 4
                else:
                    idx = (idx + 1) % 4
                self.selected_dimension = dims[idx]
                self._update_available_enemies()
    
    def _select_menu_option(self) -> None:
        """Handle menu selection."""
        if self.menu_mode == "main":
            if self.selected_index == 0:
                # Change dimension (handled by left/right)
                pass
            elif self.selected_index == 1:
                # Select enemy
                self.menu_mode = "enemy"
                self.selected_index = 0
            elif self.selected_index == 2:
                # Random encounter
                if self.available_enemies:
                    enemy_id = random.choice(self.available_enemies)
                    self._start_battle(enemy_id)
            elif self.selected_index == 3:
                # Talk to NPC
                self.menu_mode = "npc"
                self.selected_index = 0
            elif self.selected_index == 4:
                # View realms
                pass  # TODO: Realm viewer
            elif self.selected_index == 5:
                # Quit
                self.running = False
        
        elif self.menu_mode == "dimension":
            dims = ["1d", "2d", "3d", "4d"]
            self.selected_dimension = dims[self.selected_index]
            self._update_available_enemies()
            self.menu_mode = "main"
            self.selected_index = 0
        
        elif self.menu_mode == "enemy":
            if self.available_enemies:
                enemy_id = self.available_enemies[self.selected_index]
                self._start_battle(enemy_id)
        
        elif self.menu_mode == "npc":
            if self.available_npcs:
                npc_id = self.available_npcs[self.selected_index]
                self._start_npc_dialogue(npc_id)
    
    def _start_battle(self, enemy_id: str) -> None:
        """Start a battle with an enemy."""
        if self.battle_system.start_battle(enemy_id, self.player_stats):
            self.in_battle = True
            self.in_menu = False
            self.dimensional_state = DimensionalCombatState()
            
            # Set up callback
            self.battle_system.on_battle_end = self._on_battle_end
    
    def _on_battle_end(self, result: CombatResult, xp: int, gold: int) -> None:
        """Handle battle end."""
        self.last_result = result
        self.total_xp += xp
        self.total_gold += gold
        
        if result == CombatResult.VICTORY:
            self.battles_won += 1
        elif result == CombatResult.FLEE:
            self.battles_fled += 1
        elif result == CombatResult.SPARE:
            self.enemies_spared += 1
        
        # Update player stats
        if self.battle_system.state:
            self.player_stats.hp = self.battle_system.state.player_stats.hp
        
        # Heal a bit after battle
        heal_amount = self.player_stats.max_hp // 4
        self.player_stats.heal(heal_amount)
        
        self.in_battle = False
        self.in_menu = True
        self.menu_mode = "main"
        self.selected_index = 0
    
    def _start_npc_dialogue(self, npc_id: str) -> None:
        """Start dialogue with an NPC."""
        from .npcs import get_npc
        self.current_npc = get_npc(npc_id)
        if self.current_npc:
            self.in_npc_dialogue = True
            self.in_menu = False
            self.dialogue_index = 0
    
    def _handle_dialogue_input(self, event: pygame.event.Event) -> None:
        """Handle NPC dialogue input."""
        if event.key in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            self.dialogue_index += 1
            # Check if dialogue is done
            dialogue_lines = self._get_dialogue_lines()
            if self.dialogue_index >= len(dialogue_lines):
                self.in_npc_dialogue = False
                self.in_menu = True
                self.current_npc = None
        
        elif event.key == pygame.K_ESCAPE:
            self.in_npc_dialogue = False
            self.in_menu = True
            self.current_npc = None
    
    def _get_dialogue_lines(self) -> List[str]:
        """Get all dialogue lines for current NPC."""
        if not self.current_npc:
            return []
        
        lines = []
        dialogue = self.current_npc.dialogue
        
        # First meeting
        if dialogue.first_meeting and not self.current_npc.met_before:
            lines.append(dialogue.first_meeting)
            self.current_npc.met_before = True
        else:
            lines.append(dialogue.greeting)
        
        # Random dialogue lines
        for key, line in dialogue.lines.items():
            lines.append(f"[{key.upper()}]\n{line.text}")
        
        lines.append(dialogue.farewell)
        
        return lines
    
    def _handle_battle_input(self, event: pygame.event.Event) -> None:
        """Handle battle input."""
        # Dimensional shift hotkeys during attack phase
        if self.battle_system.state and self.battle_system.state.phase == CombatPhase.ENEMY_ATTACK:
            if event.key == pygame.K_1:
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.POINT):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.POINT)
                    return
            elif event.key == pygame.K_2:
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.LINE):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.LINE)
                    return
            elif event.key == pygame.K_3:
                self.dimensional_state.shift_state.current_perception = PerceptionLevel.PLANE
                return
            elif event.key == pygame.K_4:
                if self.dimensional_state.shift_state.can_shift_to(PerceptionLevel.VOLUME):
                    self.dimensional_state.shift_state.shift_to(PerceptionLevel.VOLUME)
                    return
            elif event.key == pygame.K_t:
                if self.dimensional_state.shift_state.can_transcend():
                    self.dimensional_state.shift_state.activate_transcendence()
                    return
        
        # Handle menu navigation
        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            direction = -1 if event.key == pygame.K_LEFT else 1
            self.battle_system.move_menu(direction)
        
        # Pass to battle system
        self.battle_system.handle_input(event)
    
    def _update(self, dt: float) -> None:
        """Update game state."""
        if self.in_battle:
            self.battle_system.update(dt)
            self.dimensional_state.update(dt)
            self.combat_ui.update(dt)
            
            # Update grazing during attacks
            if (self.battle_system.state and 
                self.battle_system.state.phase == CombatPhase.ENEMY_ATTACK):
                self._check_grazing()
                self._apply_perception_effects(dt)
    
    def _check_grazing(self) -> None:
        """Check for grazing near-misses."""
        if not self.battle_system.state:
            return
        
        soul = self.battle_system.state.player_soul
        
        for i, bullet in enumerate(self.battle_system.bullets):
            if self.dimensional_state.grazing.check_graze(
                soul.x, soul.y, i,
                bullet.x, bullet.y,
                bullet.radius, soul.radius
            ):
                trans, res = self.dimensional_state.grazing.get_rewards()
                self.dimensional_state.shift_state.add_transcendence(trans)
    
    def _apply_perception_effects(self, dt: float) -> None:
        """Apply perception-based movement modifications."""
        if not self.battle_system.state:
            return
        
        perception = self.dimensional_state.shift_state.current_perception
        soul = self.battle_system.state.player_soul
        
        if perception == PerceptionLevel.POINT:
            # Frozen but invulnerable
            soul.invincible = True
            self.battle_system.input_x = 0
            self.battle_system.input_y = 0
        
        elif perception == PerceptionLevel.LINE:
            # Only horizontal movement
            self.battle_system.input_y = 0
        
        elif perception == PerceptionLevel.HYPER:
            # Slow time effect (make bullets slower)
            for bullet in self.battle_system.bullets:
                bullet.velocity_x *= 0.98
                bullet.velocity_y *= 0.98
    
    def _draw(self) -> None:
        """Draw current state."""
        self.screen.fill((0, 0, 0))
        
        if self.in_battle:
            self._draw_battle()
        elif self.in_npc_dialogue:
            self._draw_npc_dialogue()
        else:
            self._draw_menu()
    
    def _draw_menu(self) -> None:
        """Draw the main menu."""
        # Title
        title = self.font_large.render("HYPERSIM COMBAT DEMO", True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 50)))
        
        # Subtitle
        subtitle = self.font_small.render(
            "Dimensional Combat System with Unique Mechanics",
            True, (150, 150, 200)
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(self.width // 2, 85)))
        
        # Current dimension
        dim_text = f"Current Dimension: {self.selected_dimension.upper()}"
        dim_color = {
            "1d": (100, 200, 255),
            "2d": (255, 150, 100),
            "3d": (150, 255, 150),
            "4d": (255, 150, 255),
        }.get(self.selected_dimension, (255, 255, 255))
        dim_surf = self.font_medium.render(dim_text, True, dim_color)
        self.screen.blit(dim_surf, dim_surf.get_rect(center=(self.width // 2, 130)))
        
        if self.menu_mode == "main":
            self._draw_main_menu()
        elif self.menu_mode == "enemy":
            self._draw_enemy_menu()
        elif self.menu_mode == "npc":
            self._draw_npc_menu()
        
        # Stats
        self._draw_stats()
        
        # Controls
        controls = [
            "↑↓: Navigate | ←→: Change Dimension",
            "Z/Enter: Select | ESC: Back/Quit",
        ]
        for i, ctrl in enumerate(controls):
            ctrl_surf = self.font_small.render(ctrl, True, (100, 100, 120))
            self.screen.blit(ctrl_surf, (20, self.height - 50 + i * 20))
    
    def _draw_main_menu(self) -> None:
        """Draw main menu options."""
        options = [
            f"Dimension: < {self.selected_dimension.upper()} >",
            "Select Enemy",
            "Random Encounter",
            "Talk to NPC",
            "View Realms",
            "Quit",
        ]
        
        start_y = 180
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == self.selected_index else (200, 200, 200)
            prefix = "► " if i == self.selected_index else "  "
            text = self.font_medium.render(prefix + option, True, color)
            self.screen.blit(text, text.get_rect(center=(self.width // 2, start_y + i * 40)))
    
    def _draw_enemy_menu(self) -> None:
        """Draw enemy selection menu."""
        title = self.font_medium.render(
            f"Select Enemy ({self.selected_dimension.upper()})",
            True, (255, 200, 100)
        )
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 160)))
        
        if not self.available_enemies:
            no_enemies = self.font_small.render(
                "No enemies available for this dimension",
                True, (150, 100, 100)
            )
            self.screen.blit(no_enemies, no_enemies.get_rect(center=(self.width // 2, 220)))
            return
        
        # List enemies
        start_y = 200
        visible_start = max(0, self.selected_index - 5)
        visible_end = min(len(self.available_enemies), visible_start + 10)
        
        for i in range(visible_start, visible_end):
            enemy_id = self.available_enemies[i]
            enemy = get_expanded_enemy(enemy_id)
            if not enemy:
                continue
            
            is_selected = i == self.selected_index
            color = (255, 255, 0) if is_selected else (200, 200, 200)
            prefix = "► " if is_selected else "  "
            
            # Boss indicator
            boss_tag = " [BOSS]" if enemy.is_boss else ""
            text = f"{prefix}{enemy.name}{boss_tag}"
            
            text_surf = self.font_small.render(text, True, color)
            y_pos = start_y + (i - visible_start) * 30
            self.screen.blit(text_surf, (self.width // 2 - 150, y_pos))
            
            # Stats
            if is_selected:
                stats = f"HP: {enemy.stats.hp} | ATK: {enemy.stats.attack} | DEF: {enemy.stats.defense}"
                stats_surf = self.font_small.render(stats, True, (150, 150, 200))
                self.screen.blit(stats_surf, stats_surf.get_rect(center=(self.width // 2, start_y + 320)))
                
                # Check text preview
                check_preview = enemy.check_text[:80] + "..." if len(enemy.check_text) > 80 else enemy.check_text
                check_surf = self.font_small.render(check_preview, True, (100, 150, 200))
                self.screen.blit(check_surf, check_surf.get_rect(center=(self.width // 2, start_y + 350)))
    
    def _draw_npc_menu(self) -> None:
        """Draw NPC selection menu."""
        title = self.font_medium.render(
            f"Talk to NPC ({self.selected_dimension.upper()})",
            True, (100, 255, 200)
        )
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 160)))
        
        if not self.available_npcs:
            no_npcs = self.font_small.render(
                "No NPCs available for this dimension",
                True, (150, 100, 100)
            )
            self.screen.blit(no_npcs, no_npcs.get_rect(center=(self.width // 2, 220)))
            return
        
        from .npcs import get_npc
        
        start_y = 200
        for i, npc_id in enumerate(self.available_npcs[:8]):
            npc = get_npc(npc_id)
            if not npc:
                continue
            
            is_selected = i == self.selected_index
            color = (255, 255, 0) if is_selected else (200, 200, 200)
            prefix = "► " if is_selected else "  "
            
            text = f"{prefix}{npc.name} ({npc.role.name.title()})"
            text_surf = self.font_small.render(text, True, color)
            self.screen.blit(text_surf, (self.width // 2 - 150, start_y + i * 30))
    
    def _draw_stats(self) -> None:
        """Draw player stats and results."""
        # Player HP
        hp_text = f"HP: {self.player_stats.hp}/{self.player_stats.max_hp}"
        hp_color = (0, 255, 0) if self.player_stats.hp > self.player_stats.max_hp // 2 else (255, 255, 0)
        if self.player_stats.hp <= self.player_stats.max_hp // 4:
            hp_color = (255, 0, 0)
        hp_surf = self.font_medium.render(hp_text, True, hp_color)
        self.screen.blit(hp_surf, (20, 20))
        
        # Session stats
        stats_y = self.height - 150
        stats = [
            f"XP: {self.total_xp}",
            f"Gold: {self.total_gold}G",
            f"Victories: {self.battles_won}",
            f"Spared: {self.enemies_spared}",
            f"Fled: {self.battles_fled}",
        ]
        
        for i, stat in enumerate(stats):
            stat_surf = self.font_small.render(stat, True, (180, 180, 100))
            self.screen.blit(stat_surf, (self.width - 150, stats_y + i * 20))
        
        # Last result
        if self.last_result:
            result_colors = {
                CombatResult.VICTORY: (0, 255, 0),
                CombatResult.SPARE: (255, 255, 0),
                CombatResult.FLEE: (200, 200, 200),
                CombatResult.DEFEAT: (255, 0, 0),
            }
            result_text = f"Last Battle: {self.last_result.name}"
            result_color = result_colors.get(self.last_result, (255, 255, 255))
            result_surf = self.font_small.render(result_text, True, result_color)
            self.screen.blit(result_surf, (20, 50))
    
    def _draw_battle(self) -> None:
        """Draw battle screen."""
        if self.battle_system.state and self.battle_system.enemy:
            # Update menu index for UI
            self.battle_system.state._menu_index = self.battle_system.menu_index
            self.battle_system.state._submenu_index = self.battle_system.submenu_index
            
            # Draw main combat UI
            self.combat_ui.draw(
                self.battle_system.state,
                self.battle_system.enemy,
                self.battle_system.battle_box,
                self.battle_system.bullets
            )
            
            # Draw dimensional UI
            self._draw_dimensional_ui()
    
    def _draw_dimensional_ui(self) -> None:
        """Draw dimensional combat UI elements."""
        shift_state = self.dimensional_state.shift_state
        
        # Shift energy bar
        bar_width = 150
        bar_height = 12
        bar_x = self.width - bar_width - 20
        bar_y = 20
        
        pygame.draw.rect(self.screen, (40, 40, 60), (bar_x, bar_y, bar_width, bar_height))
        fill_width = int(bar_width * shift_state.shift_energy / shift_state.max_shift_energy)
        pygame.draw.rect(self.screen, (100, 200, 255), (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(self.screen, (150, 150, 200), (bar_x, bar_y, bar_width, bar_height), 1)
        
        label = self.font_small.render("SHIFT", True, (150, 150, 200))
        self.screen.blit(label, (bar_x - 50, bar_y))
        
        # Current perception
        perception_text = shift_state.current_perception.value.upper()
        perc_label = self.font_small.render(f"[{perception_text}]", True, (200, 200, 255))
        self.screen.blit(perc_label, (bar_x + bar_width + 5, bar_y))
        
        # Transcendence gauge
        trans_y = bar_y + 20
        trans_fill = int(bar_width * shift_state.transcendence_gauge / shift_state.transcendence_max)
        pygame.draw.rect(self.screen, (40, 40, 60), (bar_x, trans_y, bar_width, bar_height))
        pygame.draw.rect(self.screen, (255, 200, 100), (bar_x, trans_y, trans_fill, bar_height))
        pygame.draw.rect(self.screen, (200, 150, 100), (bar_x, trans_y, bar_width, bar_height), 1)
        
        trans_label = self.font_small.render("TRANS", True, (200, 150, 100))
        self.screen.blit(trans_label, (bar_x - 50, trans_y))
        
        if shift_state.can_transcend():
            ready = self.font_small.render("[T] READY!", True, (255, 220, 100))
            self.screen.blit(ready, (bar_x + bar_width + 5, trans_y))
        
        # Graze counter
        graze_y = trans_y + 20
        graze_text = f"GRAZE: {self.dimensional_state.grazing.graze_count}"
        if self.dimensional_state.grazing.combo_count > 1:
            graze_text += f" (x{self.dimensional_state.grazing.combo_count})"
        graze_label = self.font_small.render(graze_text, True, (100, 255, 200))
        self.screen.blit(graze_label, (bar_x, graze_y))
        
        # Control hints (during attack phase)
        if (self.battle_system.state and 
            self.battle_system.state.phase == CombatPhase.ENEMY_ATTACK):
            hint_y = self.height - 80
            hints = [
                "[1] Point (Freeze+Invuln)",
                "[2] Line (Horizontal only)",
                "[3] Plane (Normal)",
                "[4] Volume (Phase)",
                "[T] Transcend (4D Power)",
            ]
            for i, hint in enumerate(hints):
                hint_surf = self.font_small.render(hint, True, (100, 100, 140))
                self.screen.blit(hint_surf, (10, hint_y + i * 15))
    
    def _draw_npc_dialogue(self) -> None:
        """Draw NPC dialogue screen."""
        if not self.current_npc:
            return
        
        # Background
        self.screen.fill((20, 20, 40))
        
        # NPC name
        name_surf = self.font_large.render(self.current_npc.name, True, (255, 255, 200))
        self.screen.blit(name_surf, name_surf.get_rect(center=(self.width // 2, 60)))
        
        # Role
        role_surf = self.font_small.render(
            f"[{self.current_npc.role.name.title()}]",
            True, (150, 150, 200)
        )
        self.screen.blit(role_surf, role_surf.get_rect(center=(self.width // 2, 95)))
        
        # Dialogue box
        box_y = 150
        box_height = 350
        pygame.draw.rect(self.screen, (0, 0, 0), (40, box_y, self.width - 80, box_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (40, box_y, self.width - 80, box_height), 2)
        
        # Get current dialogue
        dialogue_lines = self._get_dialogue_lines()
        if self.dialogue_index < len(dialogue_lines):
            current_text = dialogue_lines[self.dialogue_index]
            
            # Word wrap
            words = current_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = self.font_small.render(test_line, True, (255, 255, 255))
                if test_surf.get_width() > self.width - 120:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)
            
            # Draw lines
            for i, line in enumerate(lines[:12]):
                line_surf = self.font_small.render(line, True, (255, 255, 255))
                self.screen.blit(line_surf, (60, box_y + 20 + i * 25))
        
        # Continue indicator
        indicator_text = "[Z/ENTER] Continue" if self.dialogue_index < len(dialogue_lines) - 1 else "[Z/ENTER] End"
        indicator = self.font_small.render(indicator_text, True, (150, 150, 200))
        self.screen.blit(indicator, (self.width - 200, box_y + box_height + 10))
        
        # Progress
        progress = f"{self.dialogue_index + 1}/{len(dialogue_lines)}"
        progress_surf = self.font_small.render(progress, True, (100, 100, 150))
        self.screen.blit(progress_surf, (60, box_y + box_height + 10))


def run_demo():
    """Run the combat demo."""
    demo = CombatDemo()
    demo.run()


if __name__ == "__main__":
    run_demo()
