"""Combat UI rendering - Undertale-style interface."""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

import pygame

from .core import (
    CombatState, CombatPhase, CombatAction,
    PlayerSoul, SoulMode, DEFAULT_ITEMS
)
from .enemies import CombatEnemy, EnemyMood
from .attacks import Bullet, BulletType


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
GREEN = (0, 255, 0)
PURPLE = (200, 100, 255)
BLUE = (100, 100, 255)

# Soul colors
SOUL_COLORS = {
    SoulMode.RED: (255, 0, 0),
    SoulMode.BLUE: (0, 100, 255),
    SoulMode.ORANGE: (255, 165, 0),
    SoulMode.CYAN: (0, 255, 255),
    SoulMode.GREEN: (0, 255, 0),
    SoulMode.PURPLE: (200, 100, 255),
    SoulMode.YELLOW: (255, 255, 0),
}

# Bullet colors
BULLET_COLORS = {
    BulletType.NORMAL: WHITE,
    BulletType.ORANGE: ORANGE,
    BulletType.CYAN: CYAN,
    BulletType.GREEN: GREEN,
    BulletType.YELLOW: YELLOW,
    BulletType.PURPLE: PURPLE,
    BulletType.BLUE: BLUE,
}


class CombatUI:
    """Renders the combat interface."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Fonts
        self._font_large = pygame.font.Font(None, 48)
        self._font_medium = pygame.font.Font(None, 32)
        self._font_small = pygame.font.Font(None, 24)
        self._font_dialogue = pygame.font.Font(None, 28)
        
        # UI layout
        self.dialogue_box_height = 120
        self.menu_height = 80
        self.hp_bar_width = 200
        
        # Animation
        self.time = 0.0
        self.soul_bob = 0.0
    
    def update(self, dt: float) -> None:
        """Update UI animations."""
        self.time += dt
        self.soul_bob = math.sin(self.time * 4) * 2
    
    def draw(self, state: CombatState, enemy: CombatEnemy, 
             battle_box: "BattleBox", bullets: List[Bullet]) -> None:
        """Draw the complete combat UI."""
        # Background
        self.screen.fill(BLACK)
        
        # Draw based on phase
        if state.phase == CombatPhase.INTRO:
            self._draw_intro(state, enemy)
        elif state.phase in (CombatPhase.PLAYER_MENU, CombatPhase.PLAYER_ACT,
                            CombatPhase.PLAYER_ITEM, CombatPhase.PLAYER_MERCY):
            self._draw_menu_phase(state, enemy, battle_box)
        elif state.phase == CombatPhase.PLAYER_FIGHT:
            self._draw_fight_phase(state, enemy, battle_box)
        elif state.phase == CombatPhase.ENEMY_DIALOGUE:
            self._draw_dialogue_phase(state, enemy, battle_box)
        elif state.phase == CombatPhase.ENEMY_ATTACK:
            self._draw_attack_phase(state, enemy, battle_box, bullets)
        elif state.phase in (CombatPhase.VICTORY, CombatPhase.SPARE, 
                            CombatPhase.DEFEAT, CombatPhase.FLEE):
            self._draw_ending(state, enemy)
        else:
            self._draw_dialogue_phase(state, enemy, battle_box)
        
        # Always draw HP
        self._draw_hp_bar(state)
    
    def _draw_intro(self, state: CombatState, enemy: CombatEnemy) -> None:
        """Draw intro sequence."""
        # Enemy sprite area
        self._draw_enemy_sprite(enemy, self.width // 2, 150)
        
        # Encounter text
        self._draw_dialogue_box(state.current_dialogue, state)
    
    def _draw_menu_phase(self, state: CombatState, enemy: CombatEnemy, 
                         battle_box: "BattleBox") -> None:
        """Draw player menu phase."""
        # Enemy sprite
        self._draw_enemy_sprite(enemy, self.width // 2, 150)
        
        # Dialogue box (shows enemy dialogue or prompt)
        if state.current_dialogue:
            self._draw_dialogue_box(state.current_dialogue, state)
        else:
            self._draw_dialogue_box(enemy.get_dialogue(), state)
        
        # Action buttons
        self._draw_action_buttons(state)
        
        # Submenus
        if state.phase == CombatPhase.PLAYER_ACT:
            self._draw_act_menu(state, enemy)
        elif state.phase == CombatPhase.PLAYER_ITEM:
            self._draw_item_menu(state)
        elif state.phase == CombatPhase.PLAYER_MERCY:
            self._draw_mercy_menu(state, enemy)
    
    def _draw_fight_phase(self, state: CombatState, enemy: CombatEnemy,
                          battle_box: "BattleBox") -> None:
        """Draw fight timing minigame."""
        # Enemy sprite
        self._draw_enemy_sprite(enemy, self.width // 2, 150)
        
        # Fight bar
        bar_width = 300
        bar_height = 20
        bar_x = self.width // 2 - bar_width // 2
        bar_y = self.height // 2 + 50
        
        # Bar background
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Target zone (center)
        target_width = 40
        target_x = bar_x + bar_width // 2 - target_width // 2
        pygame.draw.rect(self.screen, (50, 255, 50), 
                        (target_x, bar_y + 2, target_width, bar_height - 4))
        
        # Moving indicator
        indicator_x = bar_x + int(state.fight_bar_position * bar_width)
        pygame.draw.rect(self.screen, WHITE, 
                        (indicator_x - 2, bar_y - 5, 4, bar_height + 10))
        
        # Instructions
        text = self._font_small.render("Press Z when the bar is in the center!", True, WHITE)
        self.screen.blit(text, text.get_rect(center=(self.width // 2, bar_y + 50)))
        
        # Action buttons
        self._draw_action_buttons(state)
    
    def _draw_dialogue_phase(self, state: CombatState, enemy: CombatEnemy,
                             battle_box: "BattleBox") -> None:
        """Draw enemy dialogue phase."""
        # Enemy sprite
        self._draw_enemy_sprite(enemy, self.width // 2, 150)
        
        # Dialogue
        self._draw_dialogue_box(state.current_dialogue, state)
        
        # Action buttons (grayed out)
        self._draw_action_buttons(state, disabled=True)
    
    def _draw_attack_phase(self, state: CombatState, enemy: CombatEnemy,
                           battle_box: "BattleBox", bullets: List[Bullet]) -> None:
        """Draw bullet hell attack phase."""
        # Battle box
        battle_box.draw(self.screen)
        
        # Draw bullets
        for bullet in bullets:
            self._draw_bullet(bullet)
        
        # Draw soul
        self._draw_soul(state.player_soul)
        
        # Attack timer bar
        if state.attack_duration > 0:
            progress = state.attack_timer / state.attack_duration
            bar_width = int(battle_box.width * 0.8)
            bar_height = 6
            bar_x = battle_box.x + (battle_box.width - bar_width) // 2
            bar_y = battle_box.y - 15
            
            pygame.draw.rect(self.screen, (50, 50, 50), 
                           (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(self.screen, GREEN,
                           (bar_x, bar_y, int(bar_width * progress), bar_height))
        
        # Attack dialogue (above battle box)
        if state.current_dialogue:
            text = self._font_small.render(state.current_dialogue, True, WHITE)
            self.screen.blit(text, text.get_rect(center=(self.width // 2, battle_box.y - 40)))
        
        # Enemy name
        name_text = self._font_medium.render(enemy.name, True, WHITE)
        self.screen.blit(name_text, (20, 20))
        
        # Enemy HP bar (small, top)
        self._draw_enemy_hp_bar(enemy, 20, 50)
    
    def _draw_ending(self, state: CombatState, enemy: CombatEnemy) -> None:
        """Draw battle ending."""
        # Result text
        if state.phase == CombatPhase.VICTORY:
            title = "YOU WON!"
            color = YELLOW
        elif state.phase == CombatPhase.SPARE:
            title = "YOU SPARED THE ENEMY!"
            color = YELLOW
        elif state.phase == CombatPhase.DEFEAT:
            title = "YOU LOST..."
            color = RED
        elif state.phase == CombatPhase.FLEE:
            title = "GOT AWAY SAFELY!"
            color = WHITE
        else:
            title = ""
            color = WHITE
        
        title_surf = self._font_large.render(title, True, color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, self.height // 3)))
        
        # Dialogue
        if state.current_dialogue:
            self._draw_dialogue_box(state.current_dialogue, state)
        
        # Rewards
        if state.phase in (CombatPhase.VICTORY, CombatPhase.SPARE):
            reward_y = self.height // 2 + 50
            xp_text = f"Earned {enemy.xp_reward} XP" if state.phase == CombatPhase.VICTORY else "Earned 0 XP"
            gold_text = f"Got {enemy.gold_reward}G" if state.phase == CombatPhase.VICTORY else f"Got {enemy.spare_gold_reward}G"
            
            xp_surf = self._font_medium.render(xp_text, True, YELLOW)
            gold_surf = self._font_medium.render(gold_text, True, YELLOW)
            
            self.screen.blit(xp_surf, xp_surf.get_rect(center=(self.width // 2, reward_y)))
            self.screen.blit(gold_surf, gold_surf.get_rect(center=(self.width // 2, reward_y + 35)))
    
    def _draw_enemy_sprite(self, enemy: CombatEnemy, x: int, y: int) -> None:
        """Draw enemy sprite (placeholder geometric shape)."""
        size = 80
        color = enemy.color
        
        # Draw based on dimension
        if enemy.dimension == "1d":
            # Line
            pygame.draw.line(self.screen, color, (x - size, y), (x + size, y), 4)
            # Endpoints
            pygame.draw.circle(self.screen, color, (x - size, y), 8)
            pygame.draw.circle(self.screen, color, (x + size, y), 8)
        
        elif enemy.dimension == "2d":
            if "triangle" in enemy.id.lower():
                # Triangle
                points = [
                    (x, y - size),
                    (x - size, y + size // 2),
                    (x + size, y + size // 2)
                ]
                pygame.draw.polygon(self.screen, color, points, 3)
            elif "square" in enemy.id.lower():
                # Square
                pygame.draw.rect(self.screen, color, 
                               (x - size // 2, y - size // 2, size, size), 3)
            elif "circle" in enemy.id.lower():
                # Circle
                pygame.draw.circle(self.screen, color, (x, y), size // 2, 3)
            else:
                # Default polygon
                pygame.draw.polygon(self.screen, color, [
                    (x, y - size // 2),
                    (x + size // 2, y),
                    (x, y + size // 2),
                    (x - size // 2, y)
                ], 3)
        
        elif enemy.dimension == "3d":
            if "cube" in enemy.id.lower():
                # Isometric cube
                s = size // 2
                pygame.draw.polygon(self.screen, color, [
                    (x, y - s), (x + s, y - s // 2), (x + s, y + s // 2),
                    (x, y + s), (x - s, y + s // 2), (x - s, y - s // 2)
                ], 3)
            elif "sphere" in enemy.id.lower():
                # Sphere (circle with shading lines)
                pygame.draw.circle(self.screen, color, (x, y), size // 2, 3)
                pygame.draw.arc(self.screen, color, 
                              (x - size // 3, y - size // 4, size // 2, size // 2),
                              0, math.pi, 2)
            else:
                # Tetrahedron
                s = size // 2
                pygame.draw.polygon(self.screen, color, [
                    (x, y - s), (x - s, y + s // 2), (x + s, y + s // 2)
                ], 3)
                pygame.draw.line(self.screen, color, (x, y - s), (x, y + s // 3), 2)
        
        elif enemy.dimension == "4d":
            # Tesseract projection
            s = size // 3
            # Outer cube
            pygame.draw.polygon(self.screen, color, [
                (x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s)
            ], 2)
            # Inner cube
            inner_s = s // 2
            pygame.draw.polygon(self.screen, color, [
                (x - inner_s, y - inner_s), (x + inner_s, y - inner_s),
                (x + inner_s, y + inner_s), (x - inner_s, y + inner_s)
            ], 2)
            # Connections
            pygame.draw.line(self.screen, color, (x - s, y - s), (x - inner_s, y - inner_s), 2)
            pygame.draw.line(self.screen, color, (x + s, y - s), (x + inner_s, y - inner_s), 2)
            pygame.draw.line(self.screen, color, (x + s, y + s), (x + inner_s, y + inner_s), 2)
            pygame.draw.line(self.screen, color, (x - s, y + s), (x - inner_s, y + inner_s), 2)
        
        else:
            # Default: circle
            pygame.draw.circle(self.screen, color, (x, y), size // 2, 3)
        
        # HP indicator (color changes with HP)
        if enemy.stats.hp_ratio < 0.25:
            indicator_color = RED
        elif enemy.stats.hp_ratio < 0.5:
            indicator_color = ORANGE
        else:
            indicator_color = None
        
        if indicator_color and enemy.stats.hp_ratio < 1.0:
            pygame.draw.circle(self.screen, indicator_color, (x, y), 5)
    
    def _draw_dialogue_box(self, text: str, state: CombatState) -> None:
        """Draw dialogue box with typewriter effect."""
        box_y = self.height - self.dialogue_box_height - self.menu_height - 20
        box_height = self.dialogue_box_height
        
        # Box background
        pygame.draw.rect(self.screen, BLACK, 
                        (20, box_y, self.width - 40, box_height))
        pygame.draw.rect(self.screen, WHITE,
                        (20, box_y, self.width - 40, box_height), 3)
        
        # Render visible text (typewriter effect)
        visible_chars = int(getattr(state, 'dialogue_char_index', len(text)))
        visible_text = text[:visible_chars] if visible_chars < len(text) else text
        
        # Word wrap and render
        lines = self._wrap_text(visible_text, self.width - 60)
        y_offset = box_y + 15
        
        for line in lines[:4]:  # Max 4 lines
            text_surf = self._font_dialogue.render(line, True, WHITE)
            self.screen.blit(text_surf, (35, y_offset))
            y_offset += 28
        
        # Continue indicator
        if visible_chars >= len(text):
            indicator_y = box_y + box_height - 20
            indicator_x = self.width - 50
            # Animated triangle
            offset = int(math.sin(self.time * 5) * 3)
            pygame.draw.polygon(self.screen, WHITE, [
                (indicator_x, indicator_y + offset),
                (indicator_x + 10, indicator_y + offset),
                (indicator_x + 5, indicator_y + 8 + offset)
            ])
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
        lines = []
        for paragraph in text.split('\n'):
            words = paragraph.split(' ')
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = self._font_dialogue.render(test_line, True, WHITE)
                
                if test_surf.get_width() <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
        
        return lines
    
    def _draw_action_buttons(self, state: CombatState, disabled: bool = False) -> None:
        """Draw FIGHT/ACT/ITEM/MERCY buttons."""
        buttons = [
            ("FIGHT", CombatAction.FIGHT, ORANGE),
            ("ACT", CombatAction.ACT, ORANGE),
            ("ITEM", CombatAction.ITEM, ORANGE),
            ("MERCY", CombatAction.MERCY, YELLOW),
        ]
        
        button_width = 120
        total_width = button_width * len(buttons) + 20 * (len(buttons) - 1)
        start_x = (self.width - total_width) // 2
        button_y = self.height - self.menu_height + 10
        
        # Get current selection from battle system (will be passed via state)
        selected_index = 0
        if hasattr(state, '_menu_index'):
            selected_index = state._menu_index
        
        for i, (label, action, color) in enumerate(buttons):
            x = start_x + i * (button_width + 20)
            
            # Determine if selected
            is_selected = (i == selected_index) and not disabled and state.phase == CombatPhase.PLAYER_MENU
            
            # Button color
            btn_color = color if not disabled else (80, 80, 80)
            if is_selected:
                # Draw soul indicator
                soul_x = x - 15
                soul_y = button_y + 20 + self.soul_bob
                self._draw_mini_soul(soul_x, soul_y)
            
            # Button box
            pygame.draw.rect(self.screen, btn_color, (x, button_y, button_width, 40), 3)
            
            # Button text
            text_color = btn_color if not disabled else (80, 80, 80)
            text_surf = self._font_medium.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=(x + button_width // 2, button_y + 20))
            self.screen.blit(text_surf, text_rect)
    
    def _draw_act_menu(self, state: CombatState, enemy: CombatEnemy) -> None:
        """Draw ACT submenu."""
        self._draw_submenu(
            [act.name for act in enemy.act_options],
            getattr(state, '_submenu_index', 0)
        )
    
    def _draw_item_menu(self, state: CombatState) -> None:
        """Draw item submenu."""
        items = []
        for item_id in state.inventory:
            item = DEFAULT_ITEMS.get(item_id)
            if item:
                items.append(item.name)
        
        if not items:
            items = ["(No items)"]
        
        self._draw_submenu(items, getattr(state, '_submenu_index', 0))
    
    def _draw_mercy_menu(self, state: CombatState, enemy: CombatEnemy) -> None:
        """Draw MERCY submenu."""
        options = []
        
        # Spare (yellow if spareable)
        spare_text = "Spare"
        options.append((spare_text, enemy.is_spareable))
        
        # Flee
        options.append(("Flee", True))
        
        self._draw_submenu(
            [opt[0] for opt in options],
            getattr(state, '_submenu_index', 0),
            highlights=[opt[1] for opt in options]
        )
    
    def _draw_submenu(self, options: List[str], selected: int, 
                      highlights: Optional[List[bool]] = None) -> None:
        """Draw a submenu overlay."""
        menu_x = self.width // 2 - 150
        menu_y = self.height // 2 - 50
        menu_width = 300
        item_height = 35
        
        # Background
        pygame.draw.rect(self.screen, BLACK,
                        (menu_x - 5, menu_y - 5, menu_width + 10, 
                         item_height * len(options) + 10))
        pygame.draw.rect(self.screen, WHITE,
                        (menu_x - 5, menu_y - 5, menu_width + 10,
                         item_height * len(options) + 10), 2)
        
        for i, option in enumerate(options):
            y = menu_y + i * item_height
            
            # Highlight color
            if highlights and i < len(highlights) and highlights[i]:
                color = YELLOW
            else:
                color = WHITE
            
            # Selection indicator
            if i == selected:
                self._draw_mini_soul(menu_x + 10, y + 15 + self.soul_bob)
            
            # Option text
            text_surf = self._font_medium.render(option, True, color)
            self.screen.blit(text_surf, (menu_x + 35, y + 5))
    
    def _draw_hp_bar(self, state: CombatState) -> None:
        """Draw player HP bar."""
        bar_x = 20
        bar_y = self.height - 35
        bar_width = self.hp_bar_width
        bar_height = 20
        
        # Label
        label = self._font_small.render("HP", True, WHITE)
        self.screen.blit(label, (bar_x, bar_y))
        
        # Bar background
        pygame.draw.rect(self.screen, RED, (bar_x + 30, bar_y, bar_width, bar_height))
        
        # Bar fill
        fill_width = int(bar_width * state.player_stats.hp_ratio)
        pygame.draw.rect(self.screen, YELLOW, (bar_x + 30, bar_y, fill_width, bar_height))
        
        # HP text
        hp_text = f"{state.player_stats.hp} / {state.player_stats.max_hp}"
        hp_surf = self._font_small.render(hp_text, True, WHITE)
        self.screen.blit(hp_surf, (bar_x + bar_width + 40, bar_y + 2))
    
    def _draw_enemy_hp_bar(self, enemy: CombatEnemy, x: int, y: int) -> None:
        """Draw enemy HP bar."""
        bar_width = 150
        bar_height = 15
        
        # Bar background
        pygame.draw.rect(self.screen, (50, 50, 50), (x, y, bar_width, bar_height))
        
        # Bar fill
        fill_width = int(bar_width * enemy.stats.hp_ratio)
        color = GREEN if enemy.stats.hp_ratio > 0.5 else (YELLOW if enemy.stats.hp_ratio > 0.25 else RED)
        pygame.draw.rect(self.screen, color, (x, y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(self.screen, WHITE, (x, y, bar_width, bar_height), 1)
    
    def _draw_soul(self, soul: PlayerSoul) -> None:
        """Draw the player's soul."""
        color = SOUL_COLORS.get(soul.mode, RED)
        
        # Flash when invincible
        if soul.invincible:
            if int(self.time * 10) % 2 == 0:
                color = WHITE
        
        # Draw heart shape
        x, y = int(soul.x), int(soul.y)
        r = int(soul.radius)
        
        # Simple heart using circles and triangle
        pygame.draw.circle(self.screen, color, (x - r // 2, y - r // 3), r // 2)
        pygame.draw.circle(self.screen, color, (x + r // 2, y - r // 3), r // 2)
        pygame.draw.polygon(self.screen, color, [
            (x - r, y - r // 3),
            (x + r, y - r // 3),
            (x, y + r)
        ])
        
        # Green soul shield
        if soul.mode == SoulMode.GREEN:
            shield_length = r * 2.5
            shield_x = x + math.cos(soul.shield_angle) * shield_length
            shield_y = y + math.sin(soul.shield_angle) * shield_length
            pygame.draw.line(self.screen, GREEN, (x, y), (int(shield_x), int(shield_y)), 4)
    
    def _draw_mini_soul(self, x: float, y: float) -> None:
        """Draw a small soul indicator for menus."""
        r = 6
        x, y = int(x), int(y)
        pygame.draw.circle(self.screen, RED, (x - r // 2, y - r // 3), r // 2)
        pygame.draw.circle(self.screen, RED, (x + r // 2, y - r // 3), r // 2)
        pygame.draw.polygon(self.screen, RED, [
            (x - r, y - r // 3),
            (x + r, y - r // 3),
            (x, y + r)
        ])
    
    def _draw_bullet(self, bullet: Bullet) -> None:
        """Draw a bullet."""
        color = BULLET_COLORS.get(bullet.bullet_type, WHITE)
        x, y = int(bullet.x), int(bullet.y)
        r = int(bullet.radius)
        
        if bullet.shape == "circle":
            pygame.draw.circle(self.screen, color, (x, y), r)
        elif bullet.shape == "square":
            if bullet.spinning:
                # Rotated square
                angle = bullet.spin_angle
                points = []
                for i in range(4):
                    a = angle + i * math.pi / 2
                    px = x + math.cos(a) * r
                    py = y + math.sin(a) * r
                    points.append((px, py))
                pygame.draw.polygon(self.screen, color, points)
            else:
                pygame.draw.rect(self.screen, color, (x - r, y - r, r * 2, r * 2))
        elif bullet.shape == "triangle":
            if bullet.spinning:
                angle = bullet.spin_angle
            else:
                angle = math.atan2(bullet.velocity_y, bullet.velocity_x)
            
            points = []
            for i in range(3):
                a = angle + i * 2 * math.pi / 3
                px = x + math.cos(a) * r
                py = y + math.sin(a) * r
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
        elif bullet.shape == "bone":
            # Bone shape (rectangle with circles on ends)
            pygame.draw.rect(self.screen, color, (x - 2, y - r, 4, r * 2))
            pygame.draw.circle(self.screen, color, (x, y - r), 4)
            pygame.draw.circle(self.screen, color, (x, y + r), 4)
        elif bullet.shape == "star":
            # Star shape
            points = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                radius = r if i % 2 == 0 else r // 2
                px = x + math.cos(angle) * radius
                py = y + math.sin(angle) * radius
                points.append((px, py))
            pygame.draw.polygon(self.screen, color, points)
        else:
            pygame.draw.circle(self.screen, color, (x, y), r)
