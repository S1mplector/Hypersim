"""Main menu system for HyperSim."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple
import random

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
        self._last_state = self.state
        self._selection_y = 0.0
        self._selection_alpha = 0.0
        
        # Menu items per state
        self._menus: Dict[MenuState, List[MenuItem]] = {
            MenuState.MAIN: [
                MenuItem("new_game", "New Adventure", action=self._new_game),
                MenuItem("load_save", "Continue", action=self._load_save),
                MenuItem("quickplay", "Quickplay", action=self._quickplay),
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
        self._tesseract_edges = self._get_tesseract_edges()
        
        # Fonts
        pygame.font.init()
        self._font_title = pygame.font.Font(None, 96)
        self._font_subtitle = pygame.font.Font(None, 38)
        self._font_menu = pygame.font.Font(None, 42)
        self._font_small = pygame.font.Font(None, 24)
        self._font_hint = pygame.font.Font(None, 22)
        
        # Colors
        self.bg_color = (5, 8, 15)
        self.title_color = (100, 180, 255)
        self.menu_color = (190, 190, 210)
        self.selected_color = (255, 230, 140)
        self.disabled_color = (80, 80, 100)
        self.panel_color = (20, 24, 40)
        self.panel_border = (50, 70, 110)
        
        # Title animation
        self._title_pulse = 0.0
        
        # Background overlays
        self._gradient_surface = self._build_vertical_gradient(
            self.width,
            self.height,
            (6, 10, 18),
            (2, 4, 10),
        )
        self._vignette_surface = self._build_vignette(self.width, self.height)
        
        # Starfield
        self._rng = random.Random(17)
        self._stars = self._generate_starfield(160)
        
        # Cached menu layout
        self._item_rects: List[pygame.Rect] = []
        self._menu_panel_rect: Optional[pygame.Rect] = None
    
    def _generate_tesseract(self) -> np.ndarray:
        """Generate tesseract vertices."""
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append([x, y, z, w])
        return np.array(vertices, dtype=float)

    def _generate_starfield(self, count: int) -> List[Tuple[float, float, float, float, float, float]]:
        """Generate a simple starfield for background depth."""
        stars = []
        for _ in range(count):
            x = self._rng.uniform(0, self.width)
            y = self._rng.uniform(0, self.height)
            depth = self._rng.uniform(0.2, 1.0)
            size = self._rng.uniform(0.6, 2.0)
            phase = self._rng.uniform(0.0, math.tau)
            speed = self._rng.uniform(0.6, 1.8)
            stars.append((x, y, depth, size, phase, speed))
        return stars

    def _build_vertical_gradient(
        self,
        width: int,
        height: int,
        top: Tuple[int, int, int],
        bottom: Tuple[int, int, int],
    ) -> pygame.Surface:
        """Create a vertical gradient surface."""
        surf = pygame.Surface((width, height))
        for y in range(height):
            t = y / max(1, height - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(surf, color, (0, y), (width, y))
        return surf

    def _build_vignette(self, width: int, height: int) -> pygame.Surface:
        """Create a subtle vignette to focus the center."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        center = (width // 2, height // 2)
        max_radius = int(max(width, height) * 0.7)
        for i in range(12):
            radius = int(max_radius * (0.55 + i * 0.04))
            alpha = int(18 + i * 12)
            color = (0, 0, 0, min(120, alpha))
            pygame.draw.circle(surf, color, center, radius, width=140)
        return surf
    
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

        if self.state != self._last_state:
            self._last_state = self.state
            self._selection_y = 0.0
            self._selection_alpha = 0.0

        menu_items, rects = self._menu_layout()
        if rects and 0 <= self.selected_index < len(rects):
            target_y = rects[self.selected_index].centery
            if self._selection_y == 0.0:
                self._selection_y = target_y
            else:
                self._selection_y += (target_y - self._selection_y) * min(1.0, dt * 10.0)
            self._selection_alpha = min(1.0, self._selection_alpha + dt * 3.0)
    
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
        
        elif event.type == pygame.MOUSEMOTION:
            if self.state != MenuState.TITLE:
                if self._update_hover(event.pos):
                    return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == MenuState.TITLE:
                self.state = MenuState.MAIN
                self.selected_index = 0
                return True
            if event.button == 1:
                if self._update_hover(event.pos):
                    self._select_current()
                    return True
            if event.button == 3 and self.state != MenuState.MAIN:
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
        self.screen.blit(self._gradient_surface, (0, 0))
        
        # Draw animated tesseract background
        self._draw_tesseract_background()
        self._draw_starfield()
        self.screen.blit(self._vignette_surface, (0, 0))
        
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
        angle_xy = self._tesseract_rotation * 0.4
        
        cos_xw = math.cos(angle_xw)
        sin_xw = math.sin(angle_xw)
        cos_yz = math.cos(angle_yz)
        sin_yz = math.sin(angle_yz)
        cos_xy = math.cos(angle_xy)
        sin_xy = math.sin(angle_xy)
        
        projected = []
        for v in self._tesseract_vertices:
            # XW rotation
            x = v[0] * cos_xw - v[3] * sin_xw
            w = v[0] * sin_xw + v[3] * cos_xw
            
            # YZ rotation
            y = v[1] * cos_yz - v[2] * sin_yz
            z = v[1] * sin_yz + v[2] * cos_yz

            # XY rotation
            x2 = x * cos_xy - y * sin_xy
            y2 = x * sin_xy + y * cos_xy
            
            # 4D to 2D projection
            scale = 140 + 12 * math.sin(self.animation_time * 0.7)
            perspective = 3.0 / (3.0 + w * 0.5)
            perspective = max(0.25, min(1.6, perspective))
            
            center_x = self.width // 2 + int(math.sin(self.animation_time * 0.6) * 28)
            center_y = self.height // 2 + int(math.cos(self.animation_time * 0.4) * 18)
            
            px = int(center_x + x2 * scale * perspective)
            py = int(center_y - y2 * scale * perspective)
            
            projected.append((px, py, perspective))
        
        # Draw edges with depth-based color
        for i, j in self._tesseract_edges:
            p1, p2 = projected[i], projected[j]
            depth = (p1[2] + p2[2]) / 2
            intensity = min(1.0, max(0.15, depth))
            color = (
                int(40 + 120 * intensity),
                int(60 + 150 * intensity),
                int(120 + 180 * intensity),
            )
            width = 1 if depth < 1.1 else 2
            pygame.draw.line(self.screen, color, (p1[0], p1[1]), (p2[0], p2[1]), width)
        
        # Draw vertices
        for px, py, depth in projected:
            radius = max(1, int(2 + depth * 2.0))
            glow = min(1.0, depth)
            color = (
                int(70 + 120 * glow),
                int(110 + 130 * glow),
                int(170 + 160 * glow),
            )
            pygame.draw.circle(self.screen, color, (px, py), radius)

        # Dimensional rings
        ring_color = (30, 50, 80)
        ring_radius = int(min(self.width, self.height) * 0.32)
        ring_offset = int(8 * math.sin(self.animation_time * 0.9))
        pygame.draw.circle(self.screen, ring_color, (self.width // 2, self.height // 2 + ring_offset), ring_radius, 1)
        pygame.draw.circle(self.screen, ring_color, (self.width // 2, self.height // 2 - ring_offset), ring_radius - 40, 1)

    def _draw_starfield(self) -> None:
        """Draw subtle twinkling stars in the background."""
        for x, y, depth, size, phase, speed in self._stars:
            twinkle = 0.6 + 0.4 * math.sin(self.animation_time * speed + phase)
            brightness = int(40 + 140 * twinkle * depth)
            color = (brightness, brightness, min(255, brightness + 30))
            radius = max(1, int(size * (0.7 + twinkle * 0.6)))
            self.screen.fill(color, (int(x), int(y), radius, radius))
    
    def _draw_title_screen(self) -> None:
        """Draw the title screen."""
        # Pulsing title
        pulse = 0.1 * math.sin(self._title_pulse) + 0.9
        title_color = tuple(int(c * pulse) for c in self.title_color)
        
        # Main title
        title = self._font_title.render("HYPERSIM", True, title_color)
        title_rect = title.get_rect(center=(self.width // 2, self.height // 3))
        shadow = self._font_title.render("HYPERSIM", True, (20, 30, 45))
        shadow_rect = shadow.get_rect(center=(self.width // 2 + 2, self.height // 3 + 2))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title, title_rect)
        pygame.draw.line(
            self.screen,
            (60, 100, 150),
            (self.width // 2 - 140, title_rect.bottom + 12),
            (self.width // 2 + 140, title_rect.bottom + 12),
            2,
        )
        
        # Subtitle
        subtitle = self._font_subtitle.render("Cross-Dimensional Adventure", True, (150, 160, 190))
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 3 + 68))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Press any key
        blink = int(self.animation_time * 2) % 2 == 0
        if blink:
            prompt = self._font_small.render("Press any key to continue", True, (130, 140, 160))
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
            MenuState.SETTINGS: "SETTINGS",
        }
        
        title_text = state_titles.get(self.state, "MENU")
        title = self._font_title.render(title_text, True, self.title_color)
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Menu items
        menu_items, rects = self._menu_layout()
        if not menu_items:
            return
        start_y = rects[0].centery
        spacing = rects[1].centery - rects[0].centery if len(rects) > 1 else 52

        # Panel backdrop
        panel_width = min(560, int(self.width * 0.65))
        panel_height = int(spacing * len(menu_items) + 40)
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = (self.width // 2, start_y + (len(menu_items) - 1) * spacing // 2)
        self._menu_panel_rect = panel_rect
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((*self.panel_color, 200))
        pygame.draw.rect(panel_surface, (*self.panel_border, 120), panel_surface.get_rect(), 2, border_radius=14)
        self.screen.blit(panel_surface, panel_rect.topleft)

        # Animated selection highlight
        if 0 <= self.selected_index < len(rects):
            highlight_rect = rects[self.selected_index].copy()
            highlight_rect.width = int(panel_width * 0.92)
            highlight_rect.height = rects[self.selected_index].height + 6
            highlight_rect.centerx = panel_rect.centerx
            highlight_rect.centery = int(self._selection_y)
            glow_surface = pygame.Surface(highlight_rect.size, pygame.SRCALPHA)
            glow_alpha = int(120 * self._selection_alpha)
            glow_surface.fill((60, 90, 140, glow_alpha))
            pygame.draw.rect(glow_surface, (120, 170, 220, glow_alpha), glow_surface.get_rect(), 2, border_radius=12)
            self.screen.blit(glow_surface, highlight_rect.topleft)
        
        self._item_rects = rects
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
                indicator = ">"
                # Glow effect
                glow_surface = self._font_menu.render(item.label, True, (255, 255, 210))
                glow_surface.set_alpha(60)
                glow_rect = glow_surface.get_rect(center=(self.width // 2 + 6, rects[i].centery + 2))
                self.screen.blit(glow_surface, glow_rect)
            else:
                indicator = "  "
            
            label = f"{indicator}  {item.label}"
            text = self._font_menu.render(label, True, color)
            text_rect = text.get_rect(center=(self.width // 2, rects[i].centery))
            self.screen.blit(text, text_rect)
        
        # Navigation hint
        hint_text = "Arrows/Mouse: Navigate   Enter/Click: Select   ESC: Back"
        hint = self._font_hint.render(hint_text, True, (90, 100, 120))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 36))
        self.screen.blit(hint, hint_rect)
        
        # Breadcrumb
        if self.state != MenuState.MAIN:
            crumb = self._font_small.render("Main Menu  >  " + title_text.title(), True, (90, 100, 120))
            self.screen.blit(crumb, (28, 24))
    
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
        hint = self._font_small.render("Press ESC or Enter to return", True, (90, 100, 120))
        hint_rect = hint.get_rect(center=(self.width // 2, self.height - 40))
        self.screen.blit(hint, hint_rect)
        
        # Check for back
        menu_items, rects = self._menu_layout()
        self._item_rects = rects
        for i, item in enumerate(menu_items):
            is_selected = i == self.selected_index
            color = self.selected_color if is_selected else self.menu_color
            prefix = "> " if is_selected else "  "
            text = self._font_menu.render(prefix + item.label, True, color)
            text_rect = text.get_rect(center=(self.width // 2, rects[i].centery))
            self.screen.blit(text, text_rect)

    def _menu_layout(self) -> Tuple[List[MenuItem], List[pygame.Rect]]:
        """Compute menu item rects for layout and input."""
        menu_items = self._menus.get(self.state, [])
        if not menu_items:
            return [], []
        if self.state == MenuState.CREDITS:
            rect = pygame.Rect(0, 0, 260, 42)
            rect.center = (self.width // 2, self.height - 90)
            return menu_items, [rect]
        spacing = 54
        start_y = self.height // 2 - (len(menu_items) * spacing) // 2
        panel_width = min(520, int(self.width * 0.6))
        item_height = 42
        rects: List[pygame.Rect] = []
        for i, _ in enumerate(menu_items):
            rect = pygame.Rect(0, 0, panel_width, item_height)
            rect.center = (self.width // 2, start_y + i * spacing)
            rects.append(rect)
        return menu_items, rects

    def _update_hover(self, pos: Tuple[int, int]) -> bool:
        """Update selection based on mouse position."""
        menu_items, rects = self._menu_layout()
        if not rects:
            return False
        for idx, rect in enumerate(rects):
            if rect.collidepoint(pos):
                if menu_items[idx].enabled:
                    if self.selected_index != idx:
                        self.selected_index = idx
                    return True
        return False
    
    # Action callbacks
    def _new_game(self) -> None:
        if self.on_start_game:
            self.on_start_game("new_campaign")
    
    def _load_save(self) -> None:
        if self.on_start_game:
            self.on_start_game("continue_campaign")

    def _quickplay(self) -> None:
        if self.on_start_game:
            self.on_start_game("quickplay")
    
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
