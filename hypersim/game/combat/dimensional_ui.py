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
        """Draw the animated bar with polished 3D effect."""
        x, y, w, h = int(self.x), int(self.y), int(self.width), int(self.height)
        
        # Dark background
        pygame.draw.rect(screen, (20, 15, 25), (x, y, w, h))
        
        # Damage preview (red part that fades)
        if self.current_value > self.display_value:
            damage_width = int(w * self.current_value)
            pygame.draw.rect(screen, self.damage_color, (x, y, damage_width, h))
        
        # Current fill with gradient effect
        fill_width = int(w * self.display_value)
        if fill_width > 0:
            # Main bar
            pygame.draw.rect(screen, self.fill_color, (x, y, fill_width, h))
            
            # Highlight at top (brighter)
            highlight = (
                min(255, self.fill_color[0] + 60),
                min(255, self.fill_color[1] + 40),
                min(255, self.fill_color[2] + 30),
            )
            highlight_h = max(2, h // 4)
            pygame.draw.rect(screen, highlight, (x, y, fill_width, highlight_h))
            
            # Shadow at bottom (darker)
            shadow = (
                max(0, self.fill_color[0] - 50),
                max(0, self.fill_color[1] - 50),
                max(0, self.fill_color[2] - 30),
            )
            shadow_h = max(2, h // 5)
            pygame.draw.rect(screen, shadow, (x, y + h - shadow_h, fill_width, shadow_h))
        
        # Border
        pygame.draw.rect(screen, self.border_color, (x, y, w, h), 1)


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
        
        # Menu items (5 options including SHIFT for dimensional actions)
        self.menu_items = [
            CombatMenuItem(CombatAction.FIGHT, "FIGHT", "⚔", (255, 100, 100)),
            CombatMenuItem(CombatAction.ACT, "ACT", "✦", (255, 200, 100)),
            CombatMenuItem(CombatAction.ITEM, "ITEM", "◆", (100, 255, 100)),
            CombatMenuItem(CombatAction.MERCY, "MERCY", "♥", (255, 255, 100)),
            CombatMenuItem(CombatAction.SHIFT, "SHIFT", "◈", (100, 200, 255)),
        ]
        
        # Combat log
        self.combat_log: List[Tuple[str, float]] = []  # (message, age)
        self.max_log_entries = 4
        
        # Animation state
        self.menu_animation_timer = 0.0
        self.dialogue_char_index = 0.0
        
        # Enemy preview animation state
        self._enemy_preview_time = 0.0
        self._enemy_particles: List[Dict] = []  # Dynamic particles around enemy
        self._enemy_oscillation = 0.0  # For movement animation
        self._last_enemy_id: Optional[str] = None
        
        # Enemy speech bubble system
        self._speech_bubble_text: str = ""
        self._speech_bubble_char_index: float = 0.0
        self._speech_bubble_duration: float = 0.0
        self._speech_bubble_max_duration: float = 0.0
        self._speech_bubble_visible: bool = False
        self._speech_bubble_fade: float = 1.0
        self._speech_typewriter_speed: float = 30.0  # Characters per second
        
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
        
        # Update enemy preview animation
        self._enemy_preview_time += dt
        
        # Update speech bubble
        if self._speech_bubble_visible:
            # Typewriter effect
            if self._speech_bubble_char_index < len(self._speech_bubble_text):
                self._speech_bubble_char_index += self._speech_typewriter_speed * dt
            
            # Duration countdown
            if self._speech_bubble_char_index >= len(self._speech_bubble_text):
                self._speech_bubble_duration -= dt
                if self._speech_bubble_duration <= 0:
                    # Start fade out
                    self._speech_bubble_fade -= dt * 2
                    if self._speech_bubble_fade <= 0:
                        self._speech_bubble_visible = False
                        self._speech_bubble_fade = 1.0
        
        # Age combat log entries
        self.combat_log = [(msg, age + dt) for msg, age in self.combat_log if age < 5.0]
    
    def add_log_entry(self, message: str) -> None:
        """Add entry to combat log."""
        self.combat_log.append((message, 0.0))
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)
    
    def show_enemy_speech(self, text: str, duration: float = 3.0) -> None:
        """Show a speech bubble near the enemy with the given text.
        
        Args:
            text: The dialogue text to display
            duration: How long to show after text is fully typed (seconds)
        """
        self._speech_bubble_text = text
        self._speech_bubble_char_index = 0.0
        self._speech_bubble_duration = duration
        self._speech_bubble_max_duration = duration
        self._speech_bubble_visible = True
        self._speech_bubble_fade = 1.0
    
    def hide_enemy_speech(self) -> None:
        """Immediately hide the enemy speech bubble."""
        self._speech_bubble_visible = False
        self._speech_bubble_text = ""
        self._speech_bubble_char_index = 0.0
    
    def is_speech_active(self) -> bool:
        """Check if a speech bubble is currently showing."""
        return self._speech_bubble_visible
    
    def draw(self, screen: pygame.Surface, phase: CombatPhase, 
             menu_index: int, submenu_index: int, in_submenu: bool,
             dialogue: str, dialogue_progress: float,
             dimension: CombatDimension, rules: DimensionalCombatRules,
             resonance: DimensionalResonance,
             enemy_name: str = "", player_stats: Optional[CombatStats] = None,
             enemy_stats: Optional[CombatStats] = None,
             act_options: Optional[List] = None,
             inventory: Optional[List[str]] = None,
             fight_bar_position: float = 0.0,
             enemy: Optional[object] = None) -> None:
        """Draw the complete combat UI."""
        # Draw dimension indicator
        self._draw_dimension_indicator(screen, dimension)
        
        # Draw enemy area with preview
        self._draw_enemy_area(screen, enemy_name, enemy_stats, enemy, dimension)
        
        # Draw enemy speech bubble if active
        if self._speech_bubble_visible:
            self._draw_enemy_speech_bubble(screen)
        
        # Draw player area
        self._draw_player_area(screen, player_stats)
        
        # Draw perception HUD
        self._draw_perception_hud(screen, rules)
        
        # Draw resonance
        self._draw_resonance(screen, resonance)
        
        # Draw dialogue box (only during certain phases)
        if phase in (CombatPhase.INTRO, CombatPhase.ENEMY_DIALOGUE, 
                     CombatPhase.RESOLUTION, CombatPhase.VICTORY, 
                     CombatPhase.DEFEAT, CombatPhase.SPARE, CombatPhase.FLEE):
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
        elif phase == CombatPhase.PLAYER_SHIFT:
            shift_options = self._get_shift_options(dimension, rules)
            self._draw_shift_menu(screen, shift_options, submenu_index, rules)
        elif phase == CombatPhase.PLAYER_FIGHT:
            self._draw_fight_bar(screen, fight_bar_position)
        
        # Draw combat log
        self._draw_combat_log(screen)
        
        # Draw controls hint
        self._draw_controls_hint(screen, phase, dimension)
    
    def _draw_dimension_indicator(self, screen: pygame.Surface, dimension: CombatDimension) -> None:
        """Draw current dimension indicator in top-left panel."""
        dim_names = {
            CombatDimension.ONE_D: "1D",
            CombatDimension.TWO_D: "2D", 
            CombatDimension.THREE_D: "3D",
            CombatDimension.FOUR_D: "4D",
        }
        dim_subtitles = {
            CombatDimension.ONE_D: "LINEAR REALM",
            CombatDimension.TWO_D: "PLANAR REALM", 
            CombatDimension.THREE_D: "SPATIAL REALM",
            CombatDimension.FOUR_D: "TEMPORAL REALM",
        }
        
        color = self.dimension_colors.get(dimension, (255, 255, 255))
        
        # Panel background with rounded feel
        panel_x, panel_y = 10, 10
        panel_w, panel_h = 100, 50
        
        pygame.draw.rect(screen, (15, 20, 30), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, color, (panel_x, panel_y, panel_w, panel_h), 2)
        
        # Dimension number (large)
        dim_text = self.font_large.render(dim_names.get(dimension, "?D"), True, color)
        screen.blit(dim_text, (panel_x + 10, panel_y + 5))
        
        # Subtitle (small)
        subtitle = self.font_small.render(dim_subtitles.get(dimension, ""), True, (120, 140, 160))
        screen.blit(subtitle, (panel_x + 8, panel_y + 32))
    
    def _draw_enemy_area(self, screen: pygame.Surface, enemy_name: str, 
                         enemy_stats: Optional[CombatStats],
                         enemy: Optional[object] = None,
                         dimension: CombatDimension = CombatDimension.TWO_D) -> None:
        """Draw enemy name, health, and preview."""
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
        
        # Enemy preview/sprite below health bar
        self._draw_enemy_preview(screen, enemy, dimension, cx, 120)
    
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
        """Draw perception state and energy in a clear panel."""
        # === PERCEPTION PANEL (top-right) ===
        panel_x = self.screen_width - 220
        panel_y = 10
        panel_w = 210
        panel_h = 95
        
        # Panel background
        pygame.draw.rect(screen, (15, 20, 30), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (60, 80, 100), (panel_x, panel_y, panel_w, panel_h), 2)
        
        # Panel title
        title = self.font_small.render("◆ PERCEPTION", True, (100, 150, 200))
        screen.blit(title, (panel_x + 8, panel_y + 5))
        
        # Horizontal divider
        pygame.draw.line(screen, (50, 60, 80), 
                        (panel_x + 5, panel_y + 22), (panel_x + panel_w - 5, panel_y + 22), 1)
        
        # Current perception state (large)
        state_name = rules.current_perception.value.upper()
        color = self.perception_colors.get(rules.current_perception, (255, 255, 255))
        state_text = self.font_medium.render(state_name, True, color)
        screen.blit(state_text, (panel_x + 10, panel_y + 26))
        
        # SHIFT energy bar
        bar_x = panel_x + 10
        bar_y = panel_y + 48
        bar_w = panel_w - 20
        bar_h = 10
        
        # Update bar position
        self.perception_bar.x = bar_x
        self.perception_bar.y = bar_y
        self.perception_bar.width = bar_w
        self.perception_bar.height = bar_h
        
        shift_label = self.font_small.render("SHIFT", True, (80, 120, 160))
        screen.blit(shift_label, (bar_x, bar_y - 12))
        self.perception_bar.draw(screen)
        
        # TRANSCEND bar
        trans_y = bar_y + 18
        self.transcendence_bar.x = bar_x
        self.transcendence_bar.y = trans_y
        self.transcendence_bar.width = bar_w
        self.transcendence_bar.height = bar_h
        
        trans_label = self.font_small.render("TRANS", True, (160, 120, 80))
        screen.blit(trans_label, (bar_x, trans_y - 12))
        self.transcendence_bar.draw(screen)
        
        # Ready indicator
        if rules.can_transcend():
            ready = self.font_small.render("[T] READY!", True, (255, 220, 100))
            screen.blit(ready, (bar_x + bar_w - 60, trans_y - 12))
        
        # === SHIFT BUTTONS (below panel) ===
        btn_y = panel_y + panel_h + 5
        btn_w = 48
        btn_spacing = 52
        
        perceptions = [
            ("1", PerceptionState.POINT, "0D"),
            ("2", PerceptionState.LINE, "1D"),
            ("3", PerceptionState.PLANE, "2D"),
            ("4", PerceptionState.VOLUME, "3D"),
        ]
        
        for i, (key, state, dim_label) in enumerate(perceptions):
            can_shift = rules.can_shift_perception(state)
            is_current = rules.current_perception == state
            
            btn_x = panel_x + i * btn_spacing
            
            if is_current:
                bg_color = (50, 60, 40)
                border_color = (150, 200, 100)
                text_color = (200, 255, 150)
            elif can_shift:
                bg_color = (35, 40, 50)
                border_color = (70, 90, 110)
                text_color = (140, 160, 180)
            else:
                bg_color = (25, 25, 30)
                border_color = (40, 40, 50)
                text_color = (60, 60, 70)
            
            pygame.draw.rect(screen, bg_color, (btn_x, btn_y, btn_w, 22))
            pygame.draw.rect(screen, border_color, (btn_x, btn_y, btn_w, 22), 1)
            
            btn_text = self.font_small.render(f"[{key}]{dim_label}", True, text_color)
            screen.blit(btn_text, (btn_x + 4, btn_y + 4))
    
    def _draw_resonance(self, screen: pygame.Surface, resonance: DimensionalResonance) -> None:
        """Draw resonance meters in a separate panel."""
        # === RESONANCE PANEL (top-right, below perception) ===
        panel_x = self.screen_width - 220
        panel_y = 135
        panel_w = 210
        panel_h = 75
        
        # Panel background
        pygame.draw.rect(screen, (15, 20, 30), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (80, 60, 100), (panel_x, panel_y, panel_w, panel_h), 2)
        
        # Panel title
        title = self.font_small.render("◆ RESONANCE", True, (150, 100, 180))
        screen.blit(title, (panel_x + 8, panel_y + 5))
        
        # Horizontal divider
        pygame.draw.line(screen, (60, 50, 80), 
                        (panel_x + 5, panel_y + 22), (panel_x + panel_w - 5, panel_y + 22), 1)
        
        dimensions = [
            ("0D", resonance.point_resonance, (100, 100, 255)),
            ("1D", resonance.line_resonance, (100, 200, 255)),
            ("2D", resonance.plane_resonance, (200, 200, 200)),
            ("3D", resonance.volume_resonance, (200, 100, 255)),
            ("4D", resonance.hyper_resonance, (255, 200, 100)),
        ]
        
        bar_width = 35
        bar_height = 30
        bar_spacing = 38
        bar_y = panel_y + 28
        
        for i, (name, value, color) in enumerate(dimensions):
            bar_x = panel_x + 10 + i * bar_spacing
            
            # Background
            pygame.draw.rect(screen, (25, 25, 35), (bar_x, bar_y, bar_width, bar_height))
            
            # Fill (vertical, bottom-up)
            fill_height = int(bar_height * (value / resonance.max_resonance))
            if fill_height > 0:
                # Gradient effect
                fill_color = tuple(min(255, c + 30) for c in color)
                pygame.draw.rect(screen, color,
                               (bar_x, bar_y + bar_height - fill_height, bar_width, fill_height))
            
            # Border
            border_color = color if value > 0 else (40, 40, 50)
            pygame.draw.rect(screen, border_color, (bar_x, bar_y, bar_width, bar_height), 1)
            
            # Label below bar
            text = self.font_small.render(name, True, color if value > 0 else (80, 80, 90))
            screen.blit(text, (bar_x + 6, bar_y + bar_height + 3))
    
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
        item_width = 95  # Narrower to fit 5 items
        total_width = len(self.menu_items) * item_width
        start_x = (self.screen_width - total_width) // 2
        
        for i, item in enumerate(self.menu_items):
            x = start_x + i * item_width
            is_selected = i == selected_index
            
            # Pulse animation for selected
            scale = 1.0
            if is_selected:
                scale = 1.0 + 0.05 * math.sin(self.menu_animation_timer * 5)
            
            # Background
            bg_color = (50, 50, 60) if is_selected else (30, 30, 40)
            pygame.draw.rect(screen, bg_color, (x, menu_y, item_width - 5, 35))
            
            # Border
            border_color = item.color if is_selected else (60, 60, 70)
            pygame.draw.rect(screen, border_color, (x, menu_y, item_width - 5, 35), 2 if is_selected else 1)
            
            # Text
            text_color = item.color if is_selected else (150, 150, 150)
            text = self.font_medium.render(item.label, True, text_color)
            text_x = x + (item_width - 5 - text.get_width()) // 2
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
    
    def _draw_fight_bar(self, screen: pygame.Surface, position: float) -> None:
        """Draw the fight timing bar with moving indicator."""
        bar_x = self.screen_width // 2 - 150
        bar_y = self.screen_height // 2 - 10
        bar_width = 300
        bar_height = 24
        
        # Background
        pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_width, bar_height))
        
        # Center zone (best timing) - green sweet spot
        center_width = 40
        center_x = bar_x + bar_width // 2 - center_width // 2
        pygame.draw.rect(screen, (40, 80, 40), (center_x, bar_y, center_width, bar_height))
        pygame.draw.rect(screen, (100, 255, 100), (center_x, bar_y, center_width, bar_height), 2)
        
        # Border
        pygame.draw.rect(screen, (150, 150, 160), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Moving indicator line (the part that was missing!)
        indicator_x = bar_x + int(position * bar_width)
        indicator_color = (255, 255, 255)
        
        # Check if in sweet spot for color feedback
        sweet_spot_start = bar_x + bar_width // 2 - center_width // 2
        sweet_spot_end = sweet_spot_start + center_width
        if sweet_spot_start <= indicator_x <= sweet_spot_end:
            indicator_color = (100, 255, 100)
        
        # Draw indicator as a thick line
        pygame.draw.rect(screen, indicator_color, 
                        (indicator_x - 3, bar_y - 4, 6, bar_height + 8))
        pygame.draw.rect(screen, (255, 255, 255),
                        (indicator_x - 3, bar_y - 4, 6, bar_height + 8), 1)
        
        # Instructions
        text = self.font_medium.render("Press Z at the center!", True, (255, 255, 255))
        screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, bar_y - 35))
    
    def _draw_enemy_speech_bubble(self, screen: pygame.Surface) -> None:
        """Draw an animated speech bubble near the enemy."""
        if not self._speech_bubble_text:
            return
        
        # Get visible text (typewriter effect)
        visible_chars = int(self._speech_bubble_char_index)
        visible_text = self._speech_bubble_text[:visible_chars]
        
        if not visible_text:
            return
        
        # Calculate alpha for fade effect
        alpha = int(255 * self._speech_bubble_fade)
        
        # Speech bubble position (above/right of enemy area)
        bubble_x = self.screen_width // 2 + 80
        bubble_y = 100
        
        # Wrap text for bubble
        max_width = 200
        words = visible_text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            test_width = self.font_small.size(test_line)[0]
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Calculate bubble size
        padding = 12
        line_height = 18
        bubble_width = max(self.font_small.size(line)[0] for line in lines) + padding * 2
        bubble_height = len(lines) * line_height + padding * 2
        
        # Create bubble surface with alpha
        bubble_surf = pygame.Surface((bubble_width + 20, bubble_height + 15), pygame.SRCALPHA)
        
        # Draw bubble background with rounded effect
        bubble_color = (40, 35, 50, alpha)
        border_color = (150, 140, 180, alpha)
        
        # Main bubble rect
        pygame.draw.rect(bubble_surf, bubble_color, 
                        (0, 0, bubble_width, bubble_height), border_radius=8)
        pygame.draw.rect(bubble_surf, border_color,
                        (0, 0, bubble_width, bubble_height), 2, border_radius=8)
        
        # Speech tail (triangle pointing to enemy)
        tail_points = [
            (10, bubble_height),
            (25, bubble_height),
            (0, bubble_height + 12),
        ]
        pygame.draw.polygon(bubble_surf, bubble_color, tail_points)
        pygame.draw.lines(bubble_surf, border_color, False, 
                         [(10, bubble_height), (0, bubble_height + 12), (25, bubble_height)], 2)
        
        # Draw text
        for i, line in enumerate(lines):
            text_color = (230, 225, 240, alpha)
            text_surf = self.font_small.render(line, True, text_color[:3])
            text_surf.set_alpha(alpha)
            bubble_surf.blit(text_surf, (padding, padding + i * line_height))
        
        # Add subtle animation (gentle bob)
        bob_offset = int(math.sin(self._enemy_preview_time * 2) * 3)
        
        # Blit to screen
        screen.blit(bubble_surf, (bubble_x, bubble_y + bob_offset))
    
    def _draw_enemy_preview(self, screen: pygame.Surface, enemy: Optional[object],
                            dimension: CombatDimension, cx: int, y: int) -> None:
        """Draw a visual preview of the enemy based on dimension."""
        if not enemy:
            return
        
        preview_y = y + 10
        
        # Get enemy color if available, default to white
        enemy_color = getattr(enemy, 'color', (255, 255, 255))
        if not enemy_color:
            enemy_color = (255, 255, 255)
        
        # Get enemy ID for tracking
        enemy_id = getattr(enemy, 'id', None)
        
        # Draw dimension-appropriate preview
        if dimension == CombatDimension.ONE_D:
            # Animated 1D enemy with particles and motion
            self._draw_1d_enemy_animated(screen, cx, preview_y, enemy_color, enemy_id)
            
        elif dimension == CombatDimension.TWO_D:
            # 2D enemy = flat shape
            points = [
                (cx - 30, preview_y + 50),
                (cx + 30, preview_y + 50),
                (cx + 20, preview_y + 10),
                (cx - 20, preview_y + 10),
            ]
            pygame.draw.polygon(screen, (40, 40, 60), points)
            pygame.draw.polygon(screen, enemy_color, points, 2)
            
        elif dimension == CombatDimension.THREE_D:
            # 3D enemy = cube outline
            size = 25
            # Front face
            pygame.draw.rect(screen, (40, 40, 60), 
                           (cx - size, preview_y + 15, size * 2, size * 2))
            pygame.draw.rect(screen, enemy_color,
                           (cx - size, preview_y + 15, size * 2, size * 2), 2)
            # Depth lines
            offset = 12
            pygame.draw.line(screen, enemy_color, 
                           (cx - size, preview_y + 15), (cx - size + offset, preview_y + 15 - offset), 1)
            pygame.draw.line(screen, enemy_color,
                           (cx + size, preview_y + 15), (cx + size + offset, preview_y + 15 - offset), 1)
            pygame.draw.line(screen, enemy_color,
                           (cx + size, preview_y + 15 + size * 2), 
                           (cx + size + offset, preview_y + 15 + size * 2 - offset), 1)
            
        elif dimension == CombatDimension.FOUR_D:
            # 4D enemy = tesseract-like
            size = 20
            # Inner cube
            pygame.draw.rect(screen, (60, 40, 80),
                           (cx - size//2, preview_y + 25, size, size))
            # Outer cube
            pygame.draw.rect(screen, enemy_color,
                           (cx - size, preview_y + 15, size * 2, size * 2), 1)
            # Connections
            for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                pygame.draw.line(screen, (150, 100, 200),
                               (cx + dx * size//2, preview_y + 25 + (size//2 if dy > 0 else 0)),
                               (cx + dx * size, preview_y + 15 + (size * 2 if dy > 0 else 0)), 1)
    
    def _draw_1d_enemy_animated(self, screen: pygame.Surface, cx: int, y: int,
                                 enemy_color: Tuple[int, int, int], enemy_id: Optional[str]) -> None:
        """Draw animated 1D enemy with particles and motion."""
        import random
        
        # Reset particles when enemy changes
        if enemy_id != self._last_enemy_id:
            self._enemy_particles = []
            self._last_enemy_id = enemy_id
        
        # Calculate oscillation motion
        osc_x = math.sin(self._enemy_preview_time * 1.5) * 8
        osc_y = math.sin(self._enemy_preview_time * 2.3) * 4
        
        # Enemy position with motion
        enemy_x = cx + osc_x
        enemy_y = y + 30 + osc_y
        
        # Spawn new particles occasionally
        if random.random() < 0.15:
            # Determine particle type based on enemy color
            is_aggressive = enemy_color[0] > 200 and enemy_color[1] < 150  # Red-ish
            is_calm = enemy_color[1] > 200 or enemy_color[2] > 200  # Blue/green-ish
            
            if is_aggressive:
                # Aggressive particles - spikes shooting outward
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(40, 80)
                self._enemy_particles.append({
                    'x': enemy_x,
                    'y': enemy_y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': random.uniform(0.3, 0.6),
                    'max_life': 0.6,
                    'size': random.uniform(2, 5),
                    'color': enemy_color,
                    'type': 'spike',
                })
            elif is_calm:
                # Calm particles - gentle floating
                angle = random.uniform(0, 2 * math.pi)
                dist = random.uniform(20, 40)
                self._enemy_particles.append({
                    'x': enemy_x + math.cos(angle) * dist,
                    'y': enemy_y + math.sin(angle) * dist,
                    'vx': random.uniform(-10, 10),
                    'vy': random.uniform(-20, -5),
                    'life': random.uniform(1.0, 2.0),
                    'max_life': 2.0,
                    'size': random.uniform(2, 4),
                    'color': enemy_color,
                    'type': 'wisp',
                    'phase': random.uniform(0, 2 * math.pi),
                })
            else:
                # Default particles - orbiting
                angle = random.uniform(0, 2 * math.pi)
                self._enemy_particles.append({
                    'x': enemy_x,
                    'y': enemy_y,
                    'angle': angle,
                    'radius': random.uniform(25, 45),
                    'speed': random.uniform(1.5, 3.0),
                    'life': random.uniform(1.5, 2.5),
                    'max_life': 2.5,
                    'size': random.uniform(2, 4),
                    'color': enemy_color,
                    'type': 'orbit',
                })
        
        # Update and draw particles
        dt = 1/60  # Approximate dt
        particles_to_remove = []
        
        for i, p in enumerate(self._enemy_particles):
            p['life'] -= dt
            if p['life'] <= 0:
                particles_to_remove.append(i)
                continue
            
            alpha = int(255 * (p['life'] / p['max_life']))
            size = int(p['size'])
            
            if p['type'] == 'spike':
                # Accelerate outward
                p['x'] += p['vx'] * dt
                p['y'] += p['vy'] * dt
                p['vx'] *= 1.02
                p['vy'] *= 1.02
                
                # Draw spike
                end_x = p['x'] + p['vx'] * 0.05
                end_y = p['y'] + p['vy'] * 0.05
                color = (*p['color'], alpha)
                
                surf = pygame.Surface((abs(int(end_x - p['x'])) + 10, abs(int(end_y - p['y'])) + 10), pygame.SRCALPHA)
                pygame.draw.line(surf, color, (5, 5), (int(end_x - p['x']) + 5, int(end_y - p['y']) + 5), max(1, size))
                screen.blit(surf, (int(p['x']) - 5, int(p['y']) - 5))
                
            elif p['type'] == 'wisp':
                # Float with oscillation
                p['phase'] = p.get('phase', 0) + dt * 3
                p['x'] += p['vx'] * dt + math.sin(p['phase']) * 0.3
                p['y'] += p['vy'] * dt
                
                # Draw glowing wisp
                glow_size = size * 2
                color = (*p['color'], int(alpha * 0.4))
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, color, (glow_size, glow_size), glow_size)
                screen.blit(glow_surf, (int(p['x']) - glow_size, int(p['y']) - glow_size))
                
                core_color = (*p['color'], alpha)
                core_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(core_surf, core_color, (size, size), size)
                screen.blit(core_surf, (int(p['x']) - size, int(p['y']) - size))
                
            elif p['type'] == 'orbit':
                # Orbit around enemy
                p['angle'] += p['speed'] * dt
                p['x'] = enemy_x + math.cos(p['angle']) * p['radius']
                p['y'] = enemy_y + math.sin(p['angle']) * p['radius'] * 0.6  # Elliptical
                
                # Draw orbiting particle
                color = (*p['color'], alpha)
                surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size, size), size)
                screen.blit(surf, (int(p['x']) - size, int(p['y']) - size))
        
        # Remove dead particles
        for i in reversed(particles_to_remove):
            if i < len(self._enemy_particles):
                self._enemy_particles.pop(i)
        
        # Limit particles
        if len(self._enemy_particles) > 30:
            self._enemy_particles = self._enemy_particles[-30:]
        
        # Draw the main enemy point with pulsing glow
        pulse = 0.8 + 0.2 * math.sin(self._enemy_preview_time * 4)
        glow_radius = int(30 * pulse)
        
        # Outer glow layers
        for i in range(4):
            layer_radius = glow_radius - i * 5
            if layer_radius > 0:
                alpha = int(50 * (1 - i * 0.2))
                glow_color = (*enemy_color, alpha)
                glow_surf = pygame.Surface((layer_radius * 2, layer_radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (layer_radius, layer_radius), layer_radius)
                screen.blit(glow_surf, (int(enemy_x) - layer_radius, int(enemy_y) - layer_radius))
        
        # Dark core background
        pygame.draw.circle(screen, (30, 30, 50), (int(enemy_x), int(enemy_y)), 15)
        
        # Main colored circle
        pygame.draw.circle(screen, enemy_color, (int(enemy_x), int(enemy_y)), 12)
        
        # Bright center
        pygame.draw.circle(screen, (255, 255, 255), (int(enemy_x), int(enemy_y)), 5)
        
        # Sparkle effect
        if random.random() < 0.1:
            sparkle_angle = random.uniform(0, 2 * math.pi)
            sparkle_dist = random.uniform(8, 15)
            sparkle_x = int(enemy_x + math.cos(sparkle_angle) * sparkle_dist)
            sparkle_y = int(enemy_y + math.sin(sparkle_angle) * sparkle_dist)
            pygame.draw.circle(screen, (255, 255, 255), (sparkle_x, sparkle_y), 2)
        
        # Label with dimension indicator
        label = self.font_small.render("◆ POINT ENTITY", True, (100, 150, 200))
        screen.blit(label, (cx - label.get_width() // 2, y + 60))
    
    def _get_shift_options(self, dimension: CombatDimension, 
                           rules: DimensionalCombatRules) -> List[Tuple[str, str, int, bool]]:
        """Get available perception shift options based on dimension.
        
        Returns list of (name, description, energy_cost, is_current).
        """
        from .dimensional_combat import PerceptionState, PerceptionAbilities
        
        options = []
        current = rules.current_perception
        
        # Base options available in all dimensions
        options.append((
            "POINT", 
            "Freeze in place, become invulnerable",
            15,
            current == PerceptionState.POINT
        ))
        options.append((
            "LINE",
            "Horizontal only, block vertical attacks",
            5,
            current == PerceptionState.LINE
        ))
        options.append((
            "PLANE",
            "Normal 2D movement (free)",
            0,
            current == PerceptionState.PLANE
        ))
        
        # 3D and above get VOLUME
        if dimension in (CombatDimension.THREE_D, CombatDimension.FOUR_D):
            options.append((
                "VOLUME",
                "Phase between depth layers",
                10,
                current == PerceptionState.VOLUME
            ))
        
        # 4D gets HYPER
        if dimension == CombatDimension.FOUR_D:
            options.append((
                "HYPER",
                "See trajectories, slow time",
                25,
                current == PerceptionState.HYPER
            ))
        
        return options
    
    def _draw_shift_menu(self, screen: pygame.Surface, 
                         options: List[Tuple[str, str, int, bool]],
                         selected_index: int,
                         rules: DimensionalCombatRules) -> None:
        """Draw perception shift menu with energy costs."""
        box_x = 50
        box_y = self.screen_height - 180
        box_width = self.screen_width - 100
        box_height = 130
        
        # Background panel
        pygame.draw.rect(screen, (15, 20, 30), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (100, 150, 200), (box_x, box_y, box_width, box_height), 2)
        
        # Title with current energy
        energy_pct = int(rules.perception_energy / rules.max_perception_energy * 100)
        title = f"◈ SHIFT PERCEPTION  [Energy: {energy_pct}%]"
        title_surf = self.font_medium.render(title, True, (100, 200, 255))
        screen.blit(title_surf, (box_x + 15, box_y + 8))
        
        # Options in grid
        col_width = box_width // 2
        y_start = box_y + 35
        
        for i, (name, desc, cost, is_current) in enumerate(options):
            col = i % 2
            row = i // 2
            x = box_x + 20 + col * col_width
            y = y_start + row * 32
            
            is_selected = i == selected_index
            can_afford = rules.perception_energy >= cost or cost == 0
            
            # Selection indicator
            if is_selected:
                pygame.draw.rect(screen, (40, 60, 80), (x - 5, y - 2, col_width - 30, 28))
                indicator = self.font_medium.render("❤", True, (255, 100, 100))
                screen.blit(indicator, (x - 3, y + 2))
            
            # Name with current indicator
            name_color = (100, 200, 255) if is_selected else (180, 180, 180)
            if is_current:
                name_color = (100, 255, 150)  # Green for current
                name = f"● {name}"
            elif not can_afford:
                name_color = (100, 100, 100)  # Gray if can't afford
            
            name_surf = self.font_medium.render(name, True, name_color)
            screen.blit(name_surf, (x + 15, y))
            
            # Cost
            cost_text = f"({cost})" if cost > 0 else "(free)"
            cost_color = (150, 150, 150) if can_afford else (255, 100, 100)
            cost_surf = self.font_small.render(cost_text, True, cost_color)
            screen.blit(cost_surf, (x + 15 + name_surf.get_width() + 5, y + 3))
            
            # Description (only for selected)
            if is_selected:
                desc_surf = self.font_small.render(desc, True, (120, 140, 160))
                screen.blit(desc_surf, (box_x + 15, box_y + box_height - 22))
    
    def _draw_combat_log(self, screen: pygame.Surface) -> None:
        """Draw recent combat log entries in a subtle area."""
        if not self.combat_log:
            return
            
        # Position below dimension indicator
        x = 15
        y = 70
        
        for message, age in self.combat_log:
            alpha = max(0, 255 - int(age * 50))
            color = (150, 150, 170)
            
            text_surf = self.font_small.render(f"• {message}", True, color)
            screen.blit(text_surf, (x, y))
            y += 14
    
    def _draw_controls_hint(self, screen: pygame.Surface, phase: CombatPhase,
                            dimension: CombatDimension) -> None:
        """Draw context-sensitive control hints in a panel."""
        hints = []
        
        if phase == CombatPhase.ENEMY_ATTACK:
            hints = [
                ("MOVE", "←→↑↓"),
                ("SHIFT", "1-4"),
                ("TRANS", "T"),
            ]
            if dimension == CombatDimension.THREE_D:
                hints.append(("DEPTH", "Q/E"))
            elif dimension == CombatDimension.FOUR_D:
                hints.append(("TIME", "Q/E"))
        elif phase == CombatPhase.PLAYER_MENU:
            hints = [("SELECT", "←→"), ("CONFIRM", "Z")]
        elif phase in (CombatPhase.PLAYER_ACT, CombatPhase.PLAYER_ITEM, CombatPhase.PLAYER_MERCY, CombatPhase.PLAYER_SHIFT):
            hints = [("SELECT", "↑↓"), ("CONFIRM", "Z"), ("BACK", "X")]
        elif phase == CombatPhase.INTRO:
            hints = [("CONTINUE", "Z")]
        elif phase == CombatPhase.ENEMY_DIALOGUE:
            hints = [("SKIP", "Z")]
        
        if not hints:
            return
        
        # === CONTROLS PANEL (bottom-right) ===
        panel_w = 130
        panel_h = 18 + len(hints) * 16
        panel_x = self.screen_width - panel_w - 10
        panel_y = self.screen_height - panel_h - 10
        
        # Panel background
        pygame.draw.rect(screen, (15, 20, 25), (panel_x, panel_y, panel_w, panel_h))
        pygame.draw.rect(screen, (50, 60, 70), (panel_x, panel_y, panel_w, panel_h), 1)
        
        # Title
        title = self.font_small.render("CONTROLS", True, (80, 100, 120))
        screen.blit(title, (panel_x + 5, panel_y + 2))
        
        # Hints
        y = panel_y + 18
        for label, key in hints:
            # Key in brackets
            key_text = self.font_small.render(f"[{key}]", True, (120, 150, 180))
            screen.blit(key_text, (panel_x + 5, y))
            
            # Label
            label_text = self.font_small.render(label, True, (80, 90, 100))
            screen.blit(label_text, (panel_x + 55, y))
            y += 14
