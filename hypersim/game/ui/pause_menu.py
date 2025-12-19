"""In-game pause menu for Tessera."""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, List, Optional, Tuple

import pygame


class PauseMenuState(Enum):
    """Pause menu sub-states."""
    MAIN = auto()
    SETTINGS = auto()


@dataclass
class PauseMenuItem:
    """A pause menu item."""
    id: str
    label: str
    action: Optional[Callable] = None
    enabled: bool = True


class PauseMenu:
    """In-game pause menu with options."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.visible = False
        self.state = PauseMenuState.MAIN
        self.selected_index = 0
        self.animation_time = 0.0
        self.fade_alpha = 0.0
        
        # Menu items
        self.items: List[PauseMenuItem] = [
            PauseMenuItem("resume", "Resume"),
            PauseMenuItem("save", "Save Game"),
            PauseMenuItem("load", "Load Game"),
            PauseMenuItem("settings", "Settings"),
            PauseMenuItem("main_menu", "Main Menu"),
            PauseMenuItem("quit", "Quit to Desktop"),
        ]
        
        # Fonts
        self._font_title = pygame.font.Font(None, 64)
        self._font_item = pygame.font.Font(None, 36)
        self._font_hint = pygame.font.Font(None, 22)
        
        # Callbacks
        self.on_resume: Optional[Callable] = None
        self.on_save: Optional[Callable] = None
        self.on_load: Optional[Callable] = None
        self.on_settings: Optional[Callable] = None
        self.on_main_menu: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        
        # Wire up actions
        self._setup_actions()
    
    def _setup_actions(self) -> None:
        """Setup menu item actions."""
        for item in self.items:
            if item.id == "resume":
                item.action = lambda: self._do_action(self.on_resume)
            elif item.id == "save":
                item.action = lambda: self._do_action(self.on_save)
            elif item.id == "load":
                item.action = lambda: self._do_action(self.on_load)
            elif item.id == "settings":
                item.action = lambda: self._do_action(self.on_settings)
            elif item.id == "main_menu":
                item.action = lambda: self._do_action(self.on_main_menu)
            elif item.id == "quit":
                item.action = lambda: self._do_action(self.on_quit)
    
    def _do_action(self, callback: Optional[Callable]) -> None:
        """Execute a callback if it exists."""
        if callback:
            callback()
    
    def show(self) -> None:
        """Show the pause menu."""
        self.visible = True
        self.fade_alpha = 0.0
        self.selected_index = 0
        pygame.mouse.set_visible(True)
    
    def hide(self) -> None:
        """Hide the pause menu."""
        self.visible = False
        pygame.mouse.set_visible(False)
    
    def toggle(self) -> None:
        """Toggle pause menu visibility."""
        if self.visible:
            self.hide()
            if self.on_resume:
                self.on_resume()
        else:
            self.show()
    
    def update(self, dt: float) -> None:
        """Update animations."""
        if not self.visible:
            return
        
        self.animation_time += dt
        
        # Fade in
        if self.fade_alpha < 1.0:
            self.fade_alpha = min(1.0, self.fade_alpha + dt * 5)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.visible:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                if self.on_resume:
                    self.on_resume()
                return True
            elif event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.items)
                return True
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.items)
                return True
            elif event.key == pygame.K_RETURN:
                self._activate_selected()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            # Update selection based on mouse position
            self._update_mouse_selection(event.pos)
            return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._update_mouse_selection(event.pos)
            self._activate_selected()
            return True
        
        return True  # Consume all events while paused
    
    def _update_mouse_selection(self, pos: Tuple[int, int]) -> None:
        """Update selection based on mouse position."""
        item_height = 50
        start_y = self.height // 2 - 50
        
        for i, item in enumerate(self.items):
            y = start_y + i * item_height
            rect = pygame.Rect(self.width // 2 - 150, y - 5, 300, 40)
            if rect.collidepoint(pos):
                self.selected_index = i
                break
    
    def _activate_selected(self) -> None:
        """Activate the selected menu item."""
        item = self.items[self.selected_index]
        if item.enabled and item.action:
            item.action()
    
    def draw(self) -> None:
        """Draw the pause menu."""
        if not self.visible:
            return
        
        # Darken background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        alpha = int(180 * self.fade_alpha)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self._font_title.render("PAUSED", True, (220, 230, 255))
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 150))
        self.screen.blit(title, title_rect)
        
        # Menu items
        item_height = 50
        start_y = self.height // 2 - 50
        
        for i, item in enumerate(self.items):
            is_selected = i == self.selected_index
            y = start_y + i * item_height
            
            # Background for selected
            if is_selected:
                rect = pygame.Rect(self.width // 2 - 150, y - 5, 300, 40)
                pygame.draw.rect(self.screen, (40, 50, 80), rect, border_radius=8)
                pygame.draw.rect(self.screen, (100, 150, 255), rect, 2, border_radius=8)
            
            # Text
            color = (220, 230, 255) if is_selected else (140, 150, 180)
            if not item.enabled:
                color = (80, 80, 100)
            
            text = self._font_item.render(item.label, True, color)
            text_rect = text.get_rect(center=(self.width // 2, y + 15))
            self.screen.blit(text, text_rect)
            
            # Selection indicator
            if is_selected:
                indicator_x = self.width // 2 - 160
                pulse = 0.5 + 0.5 * math.sin(self.animation_time * 4)
                indicator_color = (int(100 + 155 * pulse), int(150 + 105 * pulse), 255)
                pygame.draw.polygon(
                    self.screen, indicator_color,
                    [(indicator_x, y + 10), (indicator_x + 12, y + 18), (indicator_x, y + 26)]
                )
        
        # Controls hint
        hint = self._font_hint.render(
            "↑↓: Navigate | Enter: Select | ESC: Resume",
            True, (80, 90, 110)
        )
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(hint, hint_rect)
