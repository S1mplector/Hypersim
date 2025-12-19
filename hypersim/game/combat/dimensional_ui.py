"""Dimensional Combat UI - Polished UI for the dimensional battle system.

This module provides a complete, polished UI for dimensional combat:
- Animated health bars with damage preview
- Dimensional menu with visual feedback
- Enemy display with boss health bars
- Combat log with recent actions
- Perception and resonance displays
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame

from .core import CombatPhase, CombatAction, CombatStats
from .dimensional_combat import CombatDimension, PerceptionState, DimensionalCombatRules
from .perception_system import DimensionalResonance


@dataclass
class AnimatedBar:
    """An animated bar that smoothly transitions between values."""
    
    x: float
    y: float
    width: float
    height: float
    
    current_value: float = 1.0
    display_value: float = 1.0
    target_value: float = 1.0
    
    # Colors
    fill_color: Tuple[int, int, int] = (0, 255, 0)
    background_color: Tuple[int, int, int] = (40, 40, 40)
    border_color: Tuple[int, int, int] = (100, 100, 100)
    damage_color: Tuple[int, int, int] = (255, 100, 100)
    
    # Animation
    animation_speed: float = 3.0
    damage_display_timer: float = 0.0
    
    def set_value(self, value: float, max_value: float) -> None:
        """Set the bar value (0-1 ratio)."""
        self.target_value = max(0, min(1, value / max_value if max_value > 0 else 0))
    
    def update(self, dt: float) -> None:
        """Update animation."""
        # Smooth transition for display
        diff = self.target_value - self.display_value
        self.display_value += diff * self.animation_speed * dt
        
        # Damage indicator follows slower
        if self.current_value > self.target_value:
            self.damage_display_timer = 0.5
        
        if self.damage_display_timer > 0:
            self.damage_display_timer -= dt
        else:
            self.current_value += (self.target_value - self.current_value) * self.animation_speed * 0.5 * dt
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the animated bar."""
        # Background
        pygame.draw.rect(screen, self.background_color,
                        (int(self.x), int(self.y), int(self.width), int(self.height)))
        
        # Damage preview (red part that fades)
        if self.current_value > self.display_value:
            damage_width = int(self.width * self.current_value)
            pygame.draw.rect(screen, self.damage_color,
                           (int(self.x), int(self.y), damage_width, int(self.height)))
        
        # Current fill
        fill_width = int(self.width * self.display_value)
        if fill_width > 0:
            pygame.draw.rect(screen, self.fill_color,
                           (int(self.x), int(self.y), fill_width, int(self.height)))
        
        # Border
        pygame.draw.rect(screen, self.border_color,
                        (int(self.x), int(self.y), int(self.width), int(self.height)), 1)


@dataclass
class CombatMenuItem:
    """A menu item in the combat menu."""
    action: CombatAction
    label: str
    icon: str  # Simple text icon
    color: Tuple[int, int, int]
    
    # Animation state
    hover_scale: float = 1.0
    selected: bool = False


class DimensionalCombatUI:
    """Complete UI for dimensional combat."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Fonts
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self._init_fonts()
        
        # Player health bar
        self.player_hp_bar = AnimatedBar(
            x=50, y=screen_height - 85,
            width=200, height=20,
            fill_color=(255, 50, 50),
        )
        
        # Enemy health bar
        self.enemy_hp_bar = AnimatedBar(
            x=screen_width // 2 - 100, y=80,
            width=200, height=12,
            fill_color=(200, 50, 50),
        )
        
        # Perception energy bar
        self.perception_bar = AnimatedBar(
            x=screen_width - 170, y=15,
            width=150, height=12,
            fill_color=(100, 200, 255),
        )
        
        # Transcendence bar
        self.transcendence_bar = AnimatedBar(
            x=screen_width - 170, y=32,
            width=150, height=10,
            fill_color=(255, 200, 100),
        )
        
        # Menu items
        self.menu_items = [
            CombatMenuItem(CombatAction.FIGHT, "FIGHT", "⚔", (255, 100, 100)),
            CombatMenuItem(CombatAction.ACT, "ACT", "✦", (255, 200, 100)),
            CombatMenuItem(CombatAction.ITEM, "ITEM", "◆", (100, 255, 100)),
            CombatMenuItem(CombatAction.MERCY, "MERCY", "♥", (255, 255, 100)),
        ]
        
        # Combat log
        self.combat_log: List[Tuple[str, float]] = []  # (message, age)
        self.max_log_entries = 4
        
        # Animation state
        self.menu_animation_timer = 0.0
        self.dialogue_char_index = 0.0
        
        # Dimension colors
        self.dimension_colors = {
            CombatDimension.ONE_D: (100, 200, 255),
            CombatDimension.TWO_D: (255, 255, 255),
            CombatDimension.THREE_D: (200, 150, 255),
            CombatDimension.FOUR_D: (255, 200, 100),
        }
        
        # Perception colors
        self.perception_colors = {
            PerceptionState.POINT: (100, 100, 255),
            PerceptionState.LINE: (100, 200, 255),
            PerceptionState.PLANE: (255, 255, 255),
            PerceptionState.VOLUME: (200, 100, 255),
            PerceptionState.HYPER: (255, 200, 100),
            PerceptionState.SHIFTING: (200, 200, 200),
            PerceptionState.FRACTURED: (255, 100, 100),
        }
    
    def _init_fonts(self) -> None:
        """Initialize fonts."""
        try:
            self.font_large = pygame.font.Font(None, 32)
            self.font_medium = pygame.font.Font(None, 24)
            self.font_small = pygame.font.Font(None, 18)
        except:
            self.font_large = pygame.font.SysFont('arial', 28)
            self.font_medium = pygame.font.SysFont('arial', 20)
            self.font_small = pygame.font.SysFont('arial', 14)
    
    def update(self, dt: float, player_stats: CombatStats, enemy_stats: CombatStats,
               rules: DimensionalCombatRules) -> None:
        """Update UI state."""
        # Update health bars
        self.player_hp_bar.set_value(player_stats.hp, player_stats.max_hp)
        self.player_hp_bar.update(dt)
        
        self.enemy_hp_bar.set_value(enemy_stats.hp, enemy_stats.max_hp)
        self.enemy_hp_bar.update(dt)
        
        # Update perception bars
        self.perception_bar.set_value(rules.perception_energy, rules.max_perception_energy)
        self.perception_bar.fill_color = self.perception_colors.get(
            rules.current_perception, (255, 255, 255)
        )
        self.perception_bar.update(dt)
        
        self.transcendence_bar.set_value(rules.transcendence, rules.transcendence_max)
        self.transcendence_bar.update(dt)
        
        # Update menu animation
        self.menu_animation_timer += dt
        
        # Age combat log entries
        self.combat_log = [(msg, age + dt) for msg, age in self.combat_log if age < 5.0]
    
    def add_log_entry(self, message: str) -> None:
        """Add entry to combat log."""
        self.combat_log.append((message, 0.0))
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)
    
    def draw(self, screen: pygame.Surface, phase: CombatPhase, 
             menu_index: int, submenu_index: int, in_submenu: bool,
             dialogue: str, dialogue_progress: float,
             dimension: CombatDimension, rules: DimensionalCombatRules,
             resonance: DimensionalResonance,
             enemy_name: str = "", player_stats: Optional[CombatStats] = None,
             enemy_stats: Optional[CombatStats] = None,
             act_options: Optional[List] = None,
             inventory: Optional[List[str]] = None) -> None:
        """Draw the complete combat UI."""
        # Draw dimension indicator
        self._draw_dimension_indicator(screen, dimension)
        
        # Draw enemy area
        self._draw_enemy_area(screen, enemy_name, enemy_stats)
        
        # Draw player area
        self._draw_player_area(screen, player_stats)
        
        # Draw perception HUD
        self._draw_perception_hud(screen, rules)
        
        # Draw resonance
        self._draw_resonance(screen, resonance)
        
        # Draw dialogue box
        self._draw_dialogue_box(screen, dialogue, dialogue_progress)
        
        # Draw menu (if applicable)
        if phase == CombatPhase.PLAYER_MENU:
            self._draw_main_menu(screen, menu_index)
        elif phase == CombatPhase.PLAYER_ACT:
            self._draw_submenu(screen, "ACT", act_options or [], submenu_index)
        elif phase == CombatPhase.PLAYER_ITEM:
            self._draw_submenu(screen, "ITEM", inventory or [], submenu_index)
        elif phase == CombatPhase.PLAYER_MERCY:
            self._draw_submenu(screen, "MERCY", ["Spare", "Flee"], submenu_index)
        elif phase == CombatPhase.PLAYER_FIGHT:
            self._draw_fight_bar(screen, rules)
        
        # Draw combat log
        self._draw_combat_log(screen)
        
        # Draw controls hint
        self._draw_controls_hint(screen, phase, dimension)
    
    def _draw_dimension_indicator(self, screen: pygame.Surface, dimension: CombatDimension) -> None:
        """Draw current dimension indicator."""
        dim_names = {
            CombatDimension.ONE_D: "1D - LINEAR",
            CombatDimension.TWO_D: "2D - PLANAR", 
            CombatDimension.THREE_D: "3D - SPATIAL",
            CombatDimension.FOUR_D: "4D - TEMPORAL",
        }
        
        color = self.dimension_colors.get(dimension, (255, 255, 255))
        text = dim_names.get(dimension, "UNKNOWN")
        
        # Background box
        pygame.draw.rect(screen, (20, 20, 30), (10, 10, 130, 25))
        pygame.draw.rect(screen, color, (10, 10, 130, 25), 1)
        
        label = self.font_small.render(text, True, color)
        screen.blit(label, (15, 15))
    
    def _draw_enemy_area(self, screen: pygame.Surface, enemy_name: str, 
                         enemy_stats: Optional[CombatStats]) -> None:
        """Draw enemy name and health."""
        cx = self.screen_width // 2
        
        # Enemy name
        if enemy_name:
            name_surf = self.font_medium.render(enemy_name, True, (255, 255, 255))
            screen.blit(name_surf, (cx - name_surf.get_width() // 2, 55))
        
        # Health bar
        if enemy_stats:
            self.enemy_hp_bar.draw(screen)
            
            # HP text
            hp_text = f"{enemy_stats.hp}/{enemy_stats.max_hp}"
            hp_surf = self.font_small.render(hp_text, True, (200, 200, 200))
            screen.blit(hp_surf, (cx - hp_surf.get_width() // 2, 94))
    
    def _draw_player_area(self, screen: pygame.Surface, 
                          player_stats: Optional[CombatStats]) -> None:
        """Draw player health and stats."""
        if not player_stats:
            return
        
        # HP label
        hp_label = self.font_medium.render("HP", True, (255, 255, 255))
        screen.blit(hp_label, (25, self.screen_height - 87))
        
        # HP bar
        self.player_hp_bar.draw(screen)
        
        # HP numbers
        hp_text = f"{player_stats.hp} / {player_stats.max_hp}"
        hp_surf = self.font_small.render(hp_text, True, (255, 255, 255))
        screen.blit(hp_surf, (255, self.screen_height - 82))
    
    def _draw_perception_hud(self, screen: pygame.Surface, rules: DimensionalCombatRules) -> None:
        """Draw perception state and energy."""
        x = self.screen_width - 180
        y = 10
        
        # Perception label
        state_name = rules.current_perception.value.upper()
        color = self.perception_colors.get(rules.current_perception, (255, 255, 255))
        
        label = self.font_small.render(f"PERCEPTION [{state_name}]", True, color)
        screen.blit(label, (x - 5, y))
        
        # Energy bar
        self.perception_bar.draw(screen)
        
        # Transcendence
        trans_label = self.font_small.render("TRANSCEND", True, (200, 150, 100))
        screen.blit(trans_label, (x - 5, y + 20))
        self.transcendence_bar.draw(screen)
        
        # Ready indicator
        if rules.can_transcend():
            ready = self.font_small.render("[T] READY!", True, (255, 220, 100))
            screen.blit(ready, (x + 100, y + 32))
        
        # Shift options
        y_offset = 50
        perceptions = [
            ("1", PerceptionState.POINT, "0D"),
            ("2", PerceptionState.LINE, "1D"),
            ("3", PerceptionState.PLANE, "2D"),
            ("4", PerceptionState.VOLUME, "3D"),
        ]
        
        for key, state, label in perceptions:
            can_shift = rules.can_shift_perception(state)
            is_current = rules.current_perception == state
            
            if is_current:
                bg_color = (60, 60, 40)
                text_color = (255, 255, 100)
            elif can_shift:
                bg_color = (40, 40, 50)
                text_color = (150, 150, 150)
            else:
                bg_color = (30, 30, 35)
                text_color = (80, 80, 80)
            
            box_x = x + (int(key) - 1) * 38
            pygame.draw.rect(screen, bg_color, (box_x, y + y_offset, 35, 18))
            pygame.draw.rect(screen, text_color if is_current else (50, 50, 60),
                           (box_x, y + y_offset, 35, 18), 1)
            
            text = self.font_small.render(f"{key}:{label}", True, text_color)
            screen.blit(text, (box_x + 2, y + y_offset + 2))
    
    def _draw_resonance(self, screen: pygame.Surface, resonance: DimensionalResonance) -> None:
        """Draw resonance meters."""
        x = self.screen_width - 180
        y = 90
        
        label = self.font_small.render("RESONANCE", True, (150, 150, 180))
        screen.blit(label, (x, y))
        
        dimensions = [
            ("0D", resonance.point_resonance, (100, 100, 255)),
            ("1D", resonance.line_resonance, (100, 200, 255)),
            ("2D", resonance.plane_resonance, (255, 255, 255)),
            ("3D", resonance.volume_resonance, (200, 100, 255)),
            ("4D", resonance.hyper_resonance, (255, 200, 100)),
        ]
        
        bar_width = 28
        for i, (name, value, color) in enumerate(dimensions):
            bar_x = x + i * (bar_width + 2)
            bar_y = y + 15
            bar_height = 40
            
            # Background
            pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_width, bar_height))
            
            # Fill (vertical)
            fill_height = int(bar_height * (value / resonance.max_resonance))
            if fill_height > 0:
                pygame.draw.rect(screen, color,
                               (bar_x, bar_y + bar_height - fill_height, bar_width, fill_height))
            
            # Border
            pygame.draw.rect(screen, (60, 60, 70), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Label
            text = self.font_small.render(name, True, color)
            screen.blit(text, (bar_x + 2, bar_y + bar_height + 2))
    
    def _draw_dialogue_box(self, screen: pygame.Surface, dialogue: str, 
                           progress: float) -> None:
        """Draw dialogue/text box."""
        box_x = 30
        box_y = self.screen_height - 150
        box_width = self.screen_width - 60
        box_height = 55
        
        # Background
        pygame.draw.rect(screen, (10, 10, 20), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (100, 100, 120), (box_x, box_y, box_width, box_height), 2)
        
        # Text with typewriter effect
        if dialogue:
            visible_chars = int(progress)
            visible_text = dialogue[:visible_chars]
            
            # Handle multi-line
            lines = visible_text.split('\n')
            for i, line in enumerate(lines[:2]):  # Max 2 lines
                text_surf = self.font_medium.render(line, True, (255, 255, 255))
                screen.blit(text_surf, (box_x + 15, box_y + 10 + i * 22))
    
    def _draw_main_menu(self, screen: pygame.Surface, selected_index: int) -> None:
        """Draw main action menu."""
        menu_y = self.screen_height - 55
        total_width = len(self.menu_items) * 120
        start_x = (self.screen_width - total_width) // 2
        
        for i, item in enumerate(self.menu_items):
            x = start_x + i * 120
            is_selected = i == selected_index
            
            # Pulse animation for selected
            scale = 1.0
            if is_selected:
                scale = 1.0 + 0.05 * math.sin(self.menu_animation_timer * 5)
            
            # Background
            bg_color = (50, 50, 60) if is_selected else (30, 30, 40)
            pygame.draw.rect(screen, bg_color, (x, menu_y, 110, 35))
            
            # Border
            border_color = item.color if is_selected else (60, 60, 70)
            pygame.draw.rect(screen, border_color, (x, menu_y, 110, 35), 2 if is_selected else 1)
            
            # Text
            text_color = item.color if is_selected else (150, 150, 150)
            text = self.font_medium.render(item.label, True, text_color)
            text_x = x + (110 - text.get_width()) // 2
            screen.blit(text, (text_x, menu_y + 8))
            
            # Selection indicator
            if is_selected:
                indicator = self.font_medium.render("❤", True, (255, 0, 0))
                screen.blit(indicator, (x + 5, menu_y + 8))
    
    def _draw_submenu(self, screen: pygame.Surface, title: str,
                      options: List, selected_index: int) -> None:
        """Draw submenu options."""
        box_x = 50
        box_y = self.screen_height - 150
        box_width = self.screen_width - 100
        
        # Title
        title_surf = self.font_medium.render(f"* {title}", True, (255, 255, 100))
        screen.blit(title_surf, (box_x + 10, box_y - 25))
        
        # Options (2 columns)
        col_width = box_width // 2
        for i, option in enumerate(options[:6]):  # Max 6 options
            col = i % 2
            row = i // 2
            
            x = box_x + col * col_width + 20
            y = box_y + 10 + row * 22
            
            is_selected = i == selected_index
            
            # Get display text
            if hasattr(option, 'name'):
                text = option.name
            else:
                text = str(option)
            
            color = (255, 255, 100) if is_selected else (200, 200, 200)
            
            # Selection indicator
            if is_selected:
                indicator = self.font_medium.render("❤", True, (255, 0, 0))
                screen.blit(indicator, (x - 20, y))
            
            text_surf = self.font_medium.render(text, True, color)
            screen.blit(text_surf, (x, y))
    
    def _draw_fight_bar(self, screen: pygame.Surface, rules: DimensionalCombatRules) -> None:
        """Draw the fight timing bar."""
        bar_x = self.screen_width // 2 - 150
        bar_y = self.screen_height // 2 - 10
        bar_width = 300
        bar_height = 20
        
        # Background
        pygame.draw.rect(screen, (40, 40, 50), (bar_x, bar_y, bar_width, bar_height))
        
        # Center zone (best timing)
        center_width = 30
        center_x = bar_x + bar_width // 2 - center_width // 2
        pygame.draw.rect(screen, (100, 255, 100), (center_x, bar_y, center_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Instructions
        text = self.font_medium.render("Press Z at the center!", True, (255, 255, 255))
        screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, bar_y - 30))
    
    def _draw_combat_log(self, screen: pygame.Surface) -> None:
        """Draw recent combat log entries."""
        x = 15
        y = 40
        
        for message, age in self.combat_log:
            alpha = max(0, 255 - int(age * 50))
            color = (200, 200, 200)
            
            text_surf = self.font_small.render(f"• {message}", True, color)
            text_surf.set_alpha(alpha)
            screen.blit(text_surf, (x, y))
            y += 15
    
    def _draw_controls_hint(self, screen: pygame.Surface, phase: CombatPhase,
                            dimension: CombatDimension) -> None:
        """Draw context-sensitive control hints."""
        hints = []
        
        if phase == CombatPhase.ENEMY_ATTACK:
            hints = ["[←→↑↓] Move", "[1-4] Shift", "[T] Transcend"]
            if dimension == CombatDimension.THREE_D:
                hints.append("[Q/E] Depth")
            elif dimension == CombatDimension.FOUR_D:
                hints.append("[Q/E] Time")
        elif phase == CombatPhase.PLAYER_MENU:
            hints = ["[←→] Select", "[Z] Confirm"]
        elif phase in (CombatPhase.PLAYER_ACT, CombatPhase.PLAYER_ITEM, CombatPhase.PLAYER_MERCY):
            hints = ["[↑↓] Select", "[Z] Confirm", "[X] Back"]
        
        if not hints:
            return
        
        x = self.screen_width - 150
        y = self.screen_height - 60
        
        for hint in hints:
            text = self.font_small.render(hint, True, (100, 100, 120))
            screen.blit(text, (x, y))
            y += 14
