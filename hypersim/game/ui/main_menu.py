"""Main menu system for HyperSim."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame
import numpy as np
import math


class MenuState(Enum):
    """States of the main menu."""
    TITLE = auto()
    MAIN = auto()
    SETTINGS = auto()
    CREDITS = auto()


@dataclass
class MenuItem:
    """A selectable menu item."""
    id: str
    label: str
    action: Optional[Callable] = None
    submenu: Optional[str] = None
    enabled: bool = True


class MainMenu:
    """Main menu with animated 4D background."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.state = MenuState.TITLE
        self.selected_index = 0
        self.animation_time = 0.0
        
        # Menu items per state
        self._menus: Dict[MenuState, List[MenuItem]] = {
            MenuState.MAIN: [
                MenuItem("new_game", "New Game", action=self._new_game),
                MenuItem("load_save", "Load Save", action=self._load_save),
                MenuItem("settings", "Settings", submenu="settings"),
                MenuItem("credits", "Credits", submenu="credits"),
                MenuItem("quit", "Quit", action=self._quit),
            ],
            MenuState.SETTINGS: [
                MenuItem("audio", "Audio Settings", action=self._audio_settings),
                MenuItem("controls", "Controls", action=self._control_settings),
                MenuItem("graphics", "Graphics", action=self._graphics_settings),
                MenuItem("back", "Back", submenu="main"),
            ],
            MenuState.CREDITS: [
                MenuItem("back", "Back", submenu="main"),
            ],
        }
        
        # Callbacks
        self.on_start_game: Optional[Callable[[str], None]] = None  # mode -> callback
        self.on_quit: Optional[Callable] = None
        
        # 4D tesseract animation
        self._tesseract_rotation = 0.0
        self._tesseract_vertices = self._generate_tesseract()
        
        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 96)
        self._font_subtitle = pygame.font.Font(None, 36)
        self._font_menu = pygame.font.Font(None, 42)
        self._font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (5, 8, 15)
        self.title_color = (100, 180, 255)
        self.menu_color = (180, 180, 200)
        self.selected_color = (255, 220, 100)
        self.disabled_color = (80, 80, 100)
        
        # Title animation
        self._title_pulse = 0.0
    
    def _generate_tesseract(self) -> np.ndarray:
        """Generate tesseract vertices."""
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append([x, y, z, w])
        return np.array(vertices, dtype=float)
    
    def _get_tesseract_edges(self) -> List[Tuple[int, int]]:
        """Get tesseract edge connections."""
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                diff = bin(i ^ j).count('1')
                if diff == 1:
                    edges.append((i, j))
        return edges
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        self.animation_time += dt
        self._tesseract_rotation += dt * 0.3
        self._title_pulse += dt * 2.0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if event consumed."""
        if event.type == pygame.KEYDOWN:
            if self.state == MenuState.TITLE:
                # Any key to continue from title
                self.state = MenuState.MAIN
                self.selected_index = 0
                return True
            
            menu_items = self._menus.get(self.state, [])
            
            if event.key == pygame.K_UP:
                self._move_selection(-1)
                return True
            elif event.key == pygame.K_DOWN:
                self._move_selection(1)
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_current()
                return True
            elif event.key == pygame.K_ESCAPE:
                if self.state != MenuState.MAIN:
                    self.state = MenuState.MAIN
                    self.selected_index = 0
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == MenuState.TITLE:
                self.state = MenuState.MAIN
                self.selected_index = 0
                return True
        
        return False
    
    def _move_selection(self, delta: int) -> None:
        """Move menu selection."""
        menu_items = self._menus.get(self.state, [])
        if not menu_items:
            return
        
        self.selected_index = (self.selected_index + delta) % len(menu_items)
        
        # Skip disabled items
        attempts = 0
        while not menu_items[self.selected_index].enabled and attempts < len(menu_items):
            self.selected_index = (self.selected_index + delta) % len(menu_items)
            attempts += 1
    
    def _select_current(self) -> None:
        """Select the current menu item."""
        menu_items = self._menus.get(self.state, [])
        if not menu_items or self.selected_index >= len(menu_items):
            return
        
        item = menu_items[self.selected_index]
        if not item.enabled:
            return
        
        if item.submenu:
            submenu_map = {
                "main": MenuState.MAIN,
                "settings": MenuState.SETTINGS,
                "credits": MenuState.CREDITS,
            }
            new_state = submenu_map.get(item.submenu)
            if new_state:
                self.state = new_state
                self.selected_index = 0
        elif item.action:
            item.action()
    
    def draw(self) -> None:
        """Draw the menu."""
        # Clear background
        self.screen.fill(self.bg_color)
        
        # Draw animated tesseract background
        self._draw_tesseract_background()
        
        # Draw based on state
        if self.state == MenuState.TITLE:
            self._draw_title_screen()
        elif self.state == MenuState.CREDITS:
            self._draw_credits()
        else:
            self._draw_menu()
    
    def _draw_tesseract_background(self) -> None:
        """Draw rotating tesseract in background."""
        # Project tesseract to 2D
        angle_xw = self._tesseract_rotation
        angle_yz = self._tesseract_rotation * 0.7
        
        cos_xw = math.cos(angle_xw)
        sin_xw = math.sin(angle_xw)
        cos_yz = math.cos(angle_yz)
        sin_yz = math.sin(angle_yz)
        
        projected = []
        for v in self._tesseract_vertices:
            # XW rotation
            x = v[0] * cos_xw - v[3] * sin_xw
            w = v[0] * sin_xw + v[3] * cos_xw
            
            # YZ rotation
            y = v[1] * cos_yz - v[2] * sin_yz
            z = v[1] * sin_yz + v[2] * cos_yz
            
            # 4D to 2D projection
            scale = 120
            perspective = 3.0 / (3.0 + w * 0.5)
            
            px = int(self.width // 2 + x * scale * perspective)
            py = int(self.height // 2 - y * scale * perspective)
            
            projected.append((px, py, perspective))
        
        # Draw edges with depth-based color
        edges = self._get_tesseract_edges()
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            alpha = min(1.0, (p1[2] + p2[2]) / 2) * 0.3
            color = (
                int(50 * alpha),
                int(80 * alpha),
                int(150 * alpha),
            )
            pygame.draw.line(self.screen, color, (p1[0], p1[1]), (p2[0], p2[1]), 1)
        
        # Draw vertices
        for px, py, depth in projected:
            radius = max(1, int(3 * depth * 0.3))
            color = (int(80 * depth * 0.4), int(120 * depth * 0.4), int(200 * depth * 0.4))
            pygame.draw.circle(self.screen, color, (px, py), radius)
    
    def _draw_title_screen(self) -> None:
        """Draw the title screen."""
        # Pulsing title
        pulse = 0.1 * math.sin(self._title_pulse) + 0.9
        title_color = tuple(int(c * pulse) for c in self.title_color)
        
        # Main title
        title = self._font_title.render("HYPERSIM", True, title_color)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self._font_subtitle.render("Cross-Dimensional Adventure", True, (150, 150, 180))
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 3 + 60))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Press any key
        blink = int(self.animation_time * 2) % 2 == 0
        if blink:
            prompt = self._font_small.render("Press any key to continue", True, (120, 120, 140))
            prompt_rect = prompt.get_rect(center=(self.width // 2, self.height * 2 // 3))
            self.screen.blit(prompt, prompt_rect)
        
        # Version
        version = self._font_small.render("v0.1.0 - Alpha", True, (60, 60, 80))
        self.screen.blit(version, (10, self.height - 30))
    
    def _draw_menu(self) -> None:
        """Draw menu items."""
        # Title
        state_titles = {
            MenuState.MAIN: "HYPERSIM",
            MenuState.CAMPAIGN: "CAMPAIGN",
            MenuState.SETTINGS: "SETTINGS",
        }
        
        title_text = state_titles.get(self.state, "MENU")
        title = self._font_title.render(title_text, True, self.title_color)
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Menu items
        menu_items = self._menus.get(self.state, [])
        start_y = self.height // 2 - (len(menu_items) * 50) // 2
        
        for i, item in enumerate(menu_items):
            is_selected = i == self.selected_index
            
            if not item.enabled:
                color = self.disabled_color
            elif is_selected:
                color = self.selected_color
            else:
                color = self.menu_color
            
            # Selection indicator
            if is_selected:
                indicator = "▸ "
                # Glow effect
                glow_surface = self._font_menu.render(item.label, True, (255, 255, 200))
                glow_surface.set_alpha(50)
                glow_rect = glow_surface.get_rect(center=(self.width // 2 + 2, start_y + i * 50 + 2))
                self.screen.blit(glow_surface, glow_rect)
            else:
                indicator = "  "
            
            text = self._font_menu.render(indicator + item.label, True, color)
            text_rect = text.get_rect(center=(self.width // 2, start_y + i * 50))
            self.screen.blit(text, text_rect)
        
        # Navigation hint
        hint = self._font_small.render("↑↓: Navigate | Enter: Select | ESC: Back", True, (80, 80, 100))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 40))
        self.screen.blit(hint, hint_rect)
    
    def _draw_credits(self) -> None:
        """Draw credits screen."""
        title = self._font_title.render("CREDITS", True, self.title_color)
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        credits_text = [
            "HyperSim - Cross-Dimensional Adventure",
            "",
            "A game about exploring dimensions",
            "from 1D to 4D and beyond",
            "",
            "Built with Python and Pygame",
            "",
            "4D Mathematics and Visualization",
            "inspired by 'Flatland' and",
            "the study of higher dimensions",
            "",
            "Thank you for playing!",
        ]
        
        y = 180
        for line in credits_text:
            if line:
                text = self._font_small.render(line, True, (150, 150, 170))
                text_rect = text.get_rect(center=(self.width // 2, y))
                self.screen.blit(text, text_rect)
            y += 30
        
        # Back hint
        hint = self._font_small.render("Press ESC or Enter to return", True, (80, 80, 100))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 40))
        self.screen.blit(hint, hint_rect)
        
        # Check for back
        menu_items = self._menus.get(self.state, [])
        start_y = self.height - 100
        for i, item in enumerate(menu_items):
            is_selected = i == self.selected_index
            color = self.selected_color if is_selected else self.menu_color
            text = self._font_menu.render("▸ " + item.label if is_selected else "  " + item.label, True, color)
            text_rect = text.get_rect(center=(self.width // 2, start_y))
            self.screen.blit(text, text_rect)
    
    # Action callbacks
    def _new_game(self) -> None:
        if self.on_start_game:
            self.on_start_game("new_game")
    
    def _load_save(self) -> None:
        if self.on_start_game:
            self.on_start_game("load_save")
    
    def _audio_settings(self) -> None:
        pass  # TODO: Audio settings menu
    
    def _control_settings(self) -> None:
        pass  # TODO: Control settings menu
    
    def _graphics_settings(self) -> None:
        pass  # TODO: Graphics settings menu
    
    def _quit(self) -> None:
        if self.on_quit:
            self.on_quit()


def run_with_menu() -> None:
    """Run the game with main menu."""
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("HyperSim")
    clock = pygame.time.Clock()
    
    menu = MainMenu(screen)
    running = True
    game_mode = None
    
    def start_game(mode: str):
        nonlocal game_mode, running
        game_mode = mode
        running = False
    
    def quit_game():
        nonlocal running, game_mode
        game_mode = None
        running = False
    
    menu.on_start_game = start_game
    menu.on_quit = quit_game
    
    # Menu loop
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            else:
                menu.handle_event(event)
        
        menu.update(dt)
        menu.draw()
        pygame.display.flip()
    
    # Start game if mode selected
    if game_mode:
        from hypersim.game.loop import run_game
        from hypersim.game import GameSession, DimensionTrack, DEFAULT_DIMENSIONS
        from hypersim.game.save import load_progression
        from hypersim.game.progression import ProgressionState
        
        track = DimensionTrack(DEFAULT_DIMENSIONS)
        
        if game_mode == "new_campaign":
            # Fresh start
            progression = ProgressionState()
        elif game_mode in ("continue_campaign", "quickplay"):
            # Load saved progress
            progression = load_progression() or ProgressionState()
        else:
            progression = ProgressionState()
        
        session = GameSession(dimensions=track, progression=progression)
        
        from hypersim.game.loop import GameLoop
        game = GameLoop(session, title="HyperSim - Cross-Dimensional Adventure")
        game.run()
    
    pygame.quit()
