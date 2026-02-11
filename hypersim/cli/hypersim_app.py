"""HyperSim Master Application - Unified 4D Visualization Suite.

A unified launcher that provides access to all HyperSim features:
- Object Explorer: Browse and visualize 4D polytopes
- 4D Sandbox: Immersive 4D space exploration
- Settings: Configure display and controls
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple, Optional, Callable

import numpy as np
import pygame


# =============================================================================
# App Modes
# =============================================================================

class AppMode(Enum):
    """Application modes."""
    MAIN_MENU = auto()
    EXPLORER = auto()
    SANDBOX = auto()
    SETTINGS = auto()
    ABOUT = auto()


# =============================================================================
# UI Theme
# =============================================================================

@dataclass
class Theme:
    """UI color theme."""
    bg_dark: Tuple[int, int, int] = (8, 10, 18)
    bg_panel: Tuple[int, int, int] = (18, 22, 32)
    bg_card: Tuple[int, int, int] = (25, 30, 45)
    bg_card_hover: Tuple[int, int, int] = (35, 42, 62)
    bg_card_active: Tuple[int, int, int] = (45, 55, 80)
    
    text_primary: Tuple[int, int, int] = (230, 235, 245)
    text_secondary: Tuple[int, int, int] = (160, 165, 180)
    text_muted: Tuple[int, int, int] = (100, 105, 120)
    
    accent_blue: Tuple[int, int, int] = (80, 160, 255)
    accent_purple: Tuple[int, int, int] = (160, 100, 255)
    accent_cyan: Tuple[int, int, int] = (80, 220, 220)
    accent_orange: Tuple[int, int, int] = (255, 160, 80)
    accent_green: Tuple[int, int, int] = (80, 220, 140)
    
    border: Tuple[int, int, int] = (50, 55, 70)
    border_light: Tuple[int, int, int] = (70, 75, 95)


THEME = Theme()


# =============================================================================
# App Settings
# =============================================================================

@dataclass
class AppSettings:
    """User-configurable settings for the launcher UI."""
    animate_background: bool = True
    show_particles: bool = True
    show_tesseract: bool = True
    show_grid: bool = True
    reduced_motion: bool = False

# =============================================================================
# Animated Background
# =============================================================================

class AnimatedBackground:
    """Animated 4D-inspired background."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.time = 0.0
        self.grid_scroll = 0.0
        
        # Backdrop layers
        self.gradient = self._build_gradient((6, 10, 18), (3, 5, 12))
        self.vignette = self._build_vignette()
        
        # Floating particles
        self.particles = []
        for _ in range(30):
            self.particles.append({
                'x': np.random.uniform(0, width),
                'y': np.random.uniform(0, height),
                'z': np.random.uniform(0, 1),
                'w': np.random.uniform(0, 2 * np.pi),
                'speed': np.random.uniform(0.2, 0.5),
                'size': np.random.uniform(2, 5),
            })

        # Starfield + nebulae
        self.stars = self._init_stars(180)
        self.nebulae = self._init_nebulae(4)
        
        # Wireframe tesseract vertices
        self.tesseract_verts = self._create_tesseract()
        self.tesseract_edges = [
            (0,1),(1,3),(3,2),(2,0),(4,5),(5,7),(7,6),(6,4),
            (0,4),(1,5),(2,6),(3,7),(8,9),(9,11),(11,10),(10,8),
            (12,13),(13,15),(15,14),(14,12),(8,12),(9,13),(10,14),(11,15),
            (0,8),(1,9),(2,10),(3,11),(4,12),(5,13),(6,14),(7,15)
        ]
    
    def _create_tesseract(self) -> np.ndarray:
        """Create tesseract vertices."""
        verts = []
        for i in range(16):
            x = 1 if (i & 1) else -1
            y = 1 if (i & 2) else -1
            z = 1 if (i & 4) else -1
            w = 1 if (i & 8) else -1
            verts.append([x, y, z, w])
        return np.array(verts, dtype=np.float64)

    def _build_gradient(self, top: Tuple[int, int, int], bottom: Tuple[int, int, int]) -> pygame.Surface:
        """Create a vertical gradient background."""
        surf = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = (
                int(top[0] + (bottom[0] - top[0]) * t),
                int(top[1] + (bottom[1] - top[1]) * t),
                int(top[2] + (bottom[2] - top[2]) * t),
            )
            pygame.draw.line(surf, color, (0, y), (self.width, y))
        return surf

    def _build_vignette(self) -> pygame.Surface:
        """Create a soft vignette to focus the center."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center = (self.width // 2, self.height // 2)
        max_radius = int(max(self.width, self.height) * 0.75)
        for i in range(10):
            radius = int(max_radius * (0.55 + i * 0.04))
            alpha = min(140, 12 + i * 12)
            pygame.draw.circle(surf, (0, 0, 0, alpha), center, radius, width=160)
        return surf

    def _init_stars(self, count: int) -> List[Tuple[float, float, float, float, float]]:
        """Initialize starfield points."""
        stars = []
        for _ in range(count):
            stars.append((
                np.random.uniform(0, self.width),
                np.random.uniform(0, self.height),
                np.random.uniform(0.2, 1.0),
                np.random.uniform(0.6, 2.0),
                np.random.uniform(0, math.tau),
            ))
        return stars

    def _init_nebulae(self, count: int) -> List[Tuple[float, float, float, Tuple[int, int, int], float, float]]:
        """Initialize nebula glows."""
        colors = [
            (60, 80, 160),
            (120, 60, 160),
            (50, 120, 140),
            (100, 80, 140),
        ]
        nebulae = []
        for _ in range(count):
            nebulae.append((
                np.random.uniform(-200, self.width + 200),
                np.random.uniform(-200, self.height + 200),
                np.random.uniform(180, 360),
                colors[np.random.randint(0, len(colors))],
                np.random.uniform(0.04, 0.12),
                np.random.uniform(-6, 6),
            ))
        return nebulae
    
    def update(self, dt: float, settings: Optional[AppSettings] = None) -> None:
        """Update animation."""
        if settings and not settings.animate_background:
            return

        motion = 0.4 if settings and settings.reduced_motion else 1.0
        dt *= motion
        self.time += dt

        if settings is None or settings.show_particles:
            for p in self.particles:
                p['y'] -= p['speed'] * 30 * dt
                p['w'] += dt * 0.5
                if p['y'] < -10:
                    p['y'] = self.height + 10
                    p['x'] = np.random.uniform(0, self.width)

        if settings is None or settings.show_grid:
            self.grid_scroll += dt * 20

        # Nebula drift
        for idx, nebula in enumerate(self.nebulae):
            x, y, radius, color, alpha, drift = nebula
            x += drift * dt
            y += drift * 0.6 * dt
            if x < -radius:
                x = self.width + radius
            if x > self.width + radius:
                x = -radius
            if y < -radius:
                y = self.height + radius
            if y > self.height + radius:
                y = -radius
            self.nebulae[idx] = (x, y, radius, color, alpha, drift)
    
    def draw(self, surface: pygame.Surface, settings: Optional[AppSettings] = None) -> None:
        """Draw animated background."""
        surface.blit(self.gradient, (0, 0))

        # Nebulae
        for x, y, radius, color, alpha, _ in self.nebulae:
            nebula_surf = pygame.Surface((int(radius * 2), int(radius * 2)), pygame.SRCALPHA)
            for i in range(4):
                r = int(radius * (1 - i * 0.18))
                a = int(255 * alpha * (1 - i * 0.2))
                pygame.draw.circle(nebula_surf, (*color, a), (int(radius), int(radius)), r)
            surface.blit(nebula_surf, (int(x - radius), int(y - radius)), special_flags=pygame.BLEND_ADD)

        # Grid
        if settings is None or settings.show_grid:
            self._draw_grid(surface)

        # Stars
        for x, y, depth, size, phase in self.stars:
            twinkle = 0.6 + 0.4 * math.sin(self.time * 0.8 + phase)
            brightness = int(40 + 160 * twinkle * depth)
            color = (brightness, brightness, min(255, brightness + 40))
            radius = max(1, int(size * (0.7 + twinkle * 0.4)))
            surface.fill(color, (int(x), int(y), radius, radius))

        # Floating particles
        if settings is None or settings.show_particles:
            for p in self.particles:
                size = int(p['size'] * (0.5 + 0.5 * p['z']))
                color = (
                    int(60 + 30 * math.sin(p['w'])),
                    int(80 + 20 * math.sin(p['w'] + 1)),
                    int(120 + 30 * math.sin(p['w'] + 2)),
                )
                if 0 < p['y'] < self.height:
                    pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), size)

        # Draw rotating tesseract in corner
        if settings is None or settings.show_tesseract:
            self._draw_tesseract(surface)

        surface.blit(self.vignette, (0, 0))
    
    def _draw_tesseract(self, surface: pygame.Surface) -> None:
        """Draw a small rotating tesseract."""
        cx, cy = self.width - 120, self.height - 120
        scale = 50
        
        # Apply rotation
        angle_xy = self.time * 0.3
        angle_xw = self.time * 0.2
        angle_zw = self.time * 0.15
        
        def rotate(v):
            x, y, z, w = v
            # XY rotation
            c, s = math.cos(angle_xy), math.sin(angle_xy)
            x, y = x * c - y * s, x * s + y * c
            # XW rotation
            c, s = math.cos(angle_xw), math.sin(angle_xw)
            x, w = x * c - w * s, x * s + w * c
            # ZW rotation
            c, s = math.cos(angle_zw), math.sin(angle_zw)
            z, w = z * c - w * s, z * s + w * c
            return x, y, z, w
        
        def project(v):
            x, y, z, w = rotate(v)
            # 4D to 2D projection
            f = 2.0 / (3.0 + w)
            px = cx + x * scale * f
            py = cy - y * scale * f
            return int(px), int(py), w
        
        projected = [project(v) for v in self.tesseract_verts]
        
        # Draw edges
        for a, b in self.tesseract_edges:
            p1, p2 = projected[a], projected[b]
            depth = (p1[2] + p2[2]) / 2
            alpha = max(0.2, min(0.6, 0.4 + depth * 0.1))
            color = (
                int(60 * alpha),
                int(100 * alpha),
                int(180 * alpha),
            )
            pygame.draw.line(surface, color, (p1[0], p1[1]), (p2[0], p2[1]), 1)

    def _draw_grid(self, surface: pygame.Surface) -> None:
        """Draw subtle perspective grid lines."""
        grid_color = (18, 24, 40)
        spacing = 70
        horizon_y = int(self.height * 0.3)
        scroll = int(self.grid_scroll) % spacing

        for i in range(18):
            y = self.height - i * spacing + scroll
            if y < horizon_y:
                continue
            pygame.draw.line(surface, grid_color, (0, y), (self.width, y), 1)

        for i in range(-8, 9):
            x_bottom = self.width // 2 + i * spacing
            x_top = int(self.width // 2 + i * spacing * 0.3)
            pygame.draw.line(surface, grid_color, (x_bottom, self.height), (x_top, horizon_y), 1)


# =============================================================================
# Menu Card
# =============================================================================

class MenuCard:
    """A clickable menu card."""
    
    def __init__(
        self,
        rect: pygame.Rect,
        title: str,
        description: str,
        icon_char: str,
        accent_color: Tuple[int, int, int],
        on_click: Optional[Callable] = None,
    ):
        self.rect = rect
        self.title = title
        self.description = description
        self.icon_char = icon_char
        self.accent_color = accent_color
        self.on_click = on_click
        
        self.hovered = False
        self.focused = False
        self.hover_anim = 0.0
        self._pulse = 0.0
        
        self._font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self._font_desc = pygame.font.SysFont("Arial", 16)
        self._font_icon = pygame.font.SysFont("Arial", 48, bold=True)
    
    def set_focus(self, focused: bool) -> None:
        """Set keyboard focus state."""
        self.focused = focused

    def update(self, dt: float, mouse_pos: Tuple[int, int]) -> None:
        """Update hover state."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        target = 1.0 if (self.hovered or self.focused) else 0.0
        self.hover_anim += (target - self.hover_anim) * dt * 10
        if self.focused:
            self._pulse = (self._pulse + dt * 2.0) % (math.tau)
        else:
            self._pulse = 0.0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle click events."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.on_click:
                self.on_click()
                return True
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw the card."""
        # Background with hover effect
        focus_boost = 0.2 if self.focused else 0.0
        bg_color = (
            int(THEME.bg_card[0] + (THEME.bg_card_hover[0] - THEME.bg_card[0]) * self.hover_anim + 12 * focus_boost),
            int(THEME.bg_card[1] + (THEME.bg_card_hover[1] - THEME.bg_card[1]) * self.hover_anim + 12 * focus_boost),
            int(THEME.bg_card[2] + (THEME.bg_card_hover[2] - THEME.bg_card[2]) * self.hover_anim + 12 * focus_boost),
        )
        
        # Draw card with slight lift on hover
        offset_y = int(-5 * self.hover_anim)
        draw_rect = pygame.Rect(self.rect.x, self.rect.y + offset_y, self.rect.width, self.rect.height)
        
        # Shadow
        if self.hover_anim > 0.1:
            shadow_rect = pygame.Rect(
                draw_rect.x + 5, draw_rect.y + 8,
                draw_rect.width, draw_rect.height
            )
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, int(40 * self.hover_anim)))
            surface.blit(shadow_surf, shadow_rect.topleft)
        
        # Card background
        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=16)
        
        # Accent border on hover
        pulse = 0.6 + 0.4 * math.sin(self._pulse)
        border_color = (
            int(THEME.border[0] + (self.accent_color[0] - THEME.border[0]) * (self.hover_anim * 0.5 + focus_boost * pulse)),
            int(THEME.border[1] + (self.accent_color[1] - THEME.border[1]) * (self.hover_anim * 0.5 + focus_boost * pulse)),
            int(THEME.border[2] + (self.accent_color[2] - THEME.border[2]) * (self.hover_anim * 0.5 + focus_boost * pulse)),
        )
        pygame.draw.rect(surface, border_color, draw_rect, width=2, border_radius=16)
        
        # Icon circle
        icon_radius = 40
        icon_cx = draw_rect.x + 50
        icon_cy = draw_rect.centery
        
        icon_bg = (
            int(self.accent_color[0] * 0.2),
            int(self.accent_color[1] * 0.2),
            int(self.accent_color[2] * 0.2),
        )
        pygame.draw.circle(surface, icon_bg, (icon_cx, icon_cy), icon_radius)
        pygame.draw.circle(surface, self.accent_color, (icon_cx, icon_cy), icon_radius, 2)
        
        # Icon character
        icon_surf = self._font_icon.render(self.icon_char, True, self.accent_color)
        icon_rect = icon_surf.get_rect(center=(icon_cx, icon_cy))
        surface.blit(icon_surf, icon_rect)
        
        # Title
        title_color = (
            int(THEME.text_primary[0] + (255 - THEME.text_primary[0]) * self.hover_anim * 0.3),
            int(THEME.text_primary[1] + (255 - THEME.text_primary[1]) * self.hover_anim * 0.3),
            int(THEME.text_primary[2] + (255 - THEME.text_primary[2]) * self.hover_anim * 0.3),
        )
        title_surf = self._font_title.render(self.title, True, title_color)
        surface.blit(title_surf, (draw_rect.x + 110, draw_rect.y + 25))
        
        # Description
        desc_surf = self._font_desc.render(self.description, True, THEME.text_secondary)
        surface.blit(desc_surf, (draw_rect.x + 110, draw_rect.y + 60))
        
        # Arrow indicator
        if self.hover_anim > 0.1 or self.focused:
            arrow_x = draw_rect.right - 40
            arrow_y = draw_rect.centery
            arrow_color = (*self.accent_color, int(200 * self.hover_anim))
            
            # Draw arrow
            points = [
                (arrow_x, arrow_y - 8),
                (arrow_x + 12, arrow_y),
                (arrow_x, arrow_y + 8),
            ]
            pygame.draw.polygon(surface, self.accent_color, points)


# =============================================================================
# Main Application
# =============================================================================

class HyperSimApp:
    """Main HyperSim application."""
    
    def __init__(self, width: int = 1400, height: int = 900):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("HyperSim - 4D Visualization Suite")
        self.clock = pygame.time.Clock()
        
        # Current mode
        self.mode = AppMode.MAIN_MENU
        self.running = True

        # Settings
        self.settings = AppSettings()
        
        # Background
        self.background = AnimatedBackground(width, height)
        
        # Fonts
        self.font_logo = pygame.font.SysFont("Futura", 68, bold=True)
        self.font_tagline = pygame.font.SysFont("Avenir", 20)
        self.font_version = pygame.font.SysFont("Avenir", 14)
        self.font_hint = pygame.font.SysFont("Avenir", 16)
        self.font_section = pygame.font.SysFont("Avenir", 18, bold=True)
        self.font_body = pygame.font.SysFont("Avenir", 16)
        
        # Menu cards
        self._create_menu_cards()

        self.menu_grid_cols = 2
        self.selected_card = 0
        
        # Sub-applications (lazy loaded)
        self._explorer = None
        self._sandbox = None

        # Settings UI state
        self.settings_index = 0
        self.settings_items = [
            {"label": "Animated background", "type": "toggle", "attr": "animate_background"},
            {"label": "Show particles", "type": "toggle", "attr": "show_particles"},
            {"label": "Show tesseract", "type": "toggle", "attr": "show_tesseract"},
            {"label": "Show grid", "type": "toggle", "attr": "show_grid"},
            {"label": "Reduced motion", "type": "toggle", "attr": "reduced_motion"},
            {"label": "Back to menu", "type": "action", "action": self._return_to_menu},
        ]
        self._settings_rects: List[pygame.Rect] = []

        # Explorer metadata (optional)
        self.shape_count: Optional[int] = None
        try:
            from .demo_menu_v2 import DEMO_OBJECTS
            self.shape_count = len(DEMO_OBJECTS)
        except Exception:
            self.shape_count = None
    
    def _create_menu_cards(self) -> None:
        """Create the main menu cards."""
        card_width = 520
        card_height = 130
        cols = 2
        gap_x = 40
        gap_y = 30
        grid_width = card_width * cols + gap_x * (cols - 1)
        start_x = (self.width - grid_width) // 2
        start_y = 300

        card_defs = [
            ("Object Explorer", "Browse and visualize 4D polytopes with interactive controls", "◇", THEME.accent_blue, self._launch_explorer),
            ("4D Sandbox", "Explore 4D space as a 4D being - spawn objects, move freely", "◈", THEME.accent_purple, self._launch_sandbox),
            ("Settings", "Configure display, controls, and preferences", "⚙", THEME.accent_cyan, self._show_settings),
            ("About HyperSim", "Learn about the project and 4D visualization", "?", THEME.accent_orange, self._show_about),
        ]

        self.menu_cards = []
        for idx, (title, desc, icon, accent, action) in enumerate(card_defs):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (card_width + gap_x)
            y = start_y + row * (card_height + gap_y)
            self.menu_cards.append(MenuCard(
                rect=pygame.Rect(x, y, card_width, card_height),
                title=title,
                description=desc,
                icon_char=icon,
                accent_color=accent,
                on_click=action,
            ))

    def _activate_selected_card(self) -> None:
        """Launch the currently selected menu card."""
        if not self.menu_cards:
            return
        card = self.menu_cards[self.selected_card % len(self.menu_cards)]
        if card.on_click:
            card.on_click()

    def _move_card_selection(self, dx: int, dy: int) -> None:
        """Move keyboard selection in the card grid."""
        if not self.menu_cards:
            return
        cols = self.menu_grid_cols
        rows = (len(self.menu_cards) + cols - 1) // cols
        row = self.selected_card // cols
        col = self.selected_card % cols
        row = max(0, min(rows - 1, row + dy))
        col = max(0, min(cols - 1, col + dx))
        idx = row * cols + col
        if idx >= len(self.menu_cards):
            idx = len(self.menu_cards) - 1
        self.selected_card = idx

    def _toggle_setting(self, index: int) -> None:
        """Toggle a settings item or run its action."""
        if index < 0 or index >= len(self.settings_items):
            return
        item = self.settings_items[index]
        if item["type"] == "toggle":
            attr = item["attr"]
            current = getattr(self.settings, attr)
            setattr(self.settings, attr, not current)
        elif item["type"] == "action":
            action = item.get("action")
            if callable(action):
                action()
    
    def _launch_explorer(self) -> None:
        """Launch the object explorer mode."""
        self.mode = AppMode.EXPLORER
        
        # Import and run explorer
        from .demo_menu_v2 import DemoMenu
        
        # Create explorer with our screen
        self._explorer = DemoMenu.__new__(DemoMenu)
        self._explorer.width = self.width
        self._explorer.height = self.height
        self._explorer.screen = self.screen
        self._explorer.clock = self.clock
        self._explorer.running = True
        
        # Initialize the rest
        self._explorer._init_from_app()
    
    def _launch_sandbox(self) -> None:
        """Launch the 4D sandbox mode."""
        self.mode = AppMode.SANDBOX
        
        # Import and create sandbox
        from .sandbox_4d import Sandbox4D
        
        self._sandbox = Sandbox4D.__new__(Sandbox4D)
        self._sandbox.width = self.width
        self._sandbox.height = self.height
        self._sandbox.screen = self.screen
        self._sandbox.clock = self.clock
        self._sandbox._init_from_app()
    
    def _show_settings(self) -> None:
        """Show settings panel."""
        self.mode = AppMode.SETTINGS
    
    def _show_about(self) -> None:
        """Show about panel."""
        self.mode = AppMode.ABOUT
    
    def _return_to_menu(self) -> None:
        """Return to main menu."""
        if self._sandbox and getattr(self._sandbox, "mouse_captured", False):
            self._sandbox.release_mouse()
        self.mode = AppMode.MAIN_MENU
        self._explorer = None
        self._sandbox = None
        pygame.display.set_caption("HyperSim - 4D Visualization Suite")
    
    def handle_events(self) -> None:
        """Handle input events."""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if self.mode == AppMode.MAIN_MENU:
                for card in self.menu_cards:
                    if card.handle_event(event):
                        return
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._activate_selected_card()
                    elif event.key == pygame.K_UP:
                        self._move_card_selection(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self._move_card_selection(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self._move_card_selection(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self._move_card_selection(1, 0)
                    elif event.key == pygame.K_1:
                        self._launch_explorer()
                    elif event.key == pygame.K_2:
                        self._launch_sandbox()
                    elif event.key == pygame.K_3:
                        self._show_settings()
                    elif event.key == pygame.K_4:
                        self._show_about()
            
            elif self.mode == AppMode.SETTINGS:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._return_to_menu()
                    elif event.key == pygame.K_UP:
                        self.settings_index = max(0, self.settings_index - 1)
                    elif event.key == pygame.K_DOWN:
                        self.settings_index = min(len(self.settings_items) - 1, self.settings_index + 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                        self._toggle_setting(self.settings_index)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for idx, rect in enumerate(self._settings_rects):
                        if rect.collidepoint(event.pos):
                            self.settings_index = idx
                            self._toggle_setting(idx)
                            return
            
            elif self.mode == AppMode.ABOUT:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self._return_to_menu()
    
    def update(self, dt: float) -> None:
        """Update application state."""
        mouse_pos = pygame.mouse.get_pos()
        
        if self.mode in (AppMode.MAIN_MENU, AppMode.SETTINGS, AppMode.ABOUT):
            self.background.update(dt, self.settings)

        if self.mode == AppMode.MAIN_MENU:
            hovered_any = False
            for idx, card in enumerate(self.menu_cards):
                card.set_focus(idx == self.selected_card)
                card.update(dt, mouse_pos)
                if card.hovered:
                    self.selected_card = idx
                    hovered_any = True
            if hovered_any:
                for idx, card in enumerate(self.menu_cards):
                    card.set_focus(idx == self.selected_card)
    
    def render_main_menu(self) -> None:
        """Render the main menu."""
        # Background
        self.screen.fill(THEME.bg_dark)
        self.background.draw(self.screen, self.settings)
        
        # Logo
        logo_text = "HyperSim"
        shadow = self.font_logo.render(logo_text, True, (20, 24, 36))
        shadow_rect = shadow.get_rect(center=(self.width // 2 + 3, 88))
        self.screen.blit(shadow, shadow_rect)
        logo_surf = self.font_logo.render(logo_text, True, THEME.text_primary)
        logo_x = (self.width - logo_surf.get_width()) // 2
        self.screen.blit(logo_surf, (logo_x, 80))
        
        # Accent line under logo
        line_width = 240
        line_x = (self.width - line_width) // 2
        pygame.draw.line(self.screen, THEME.accent_blue, (line_x, 160), (line_x + line_width, 160), 3)
        
        # Tagline
        tagline = "Explore polytopes, space, and motion beyond 3D"
        tagline_surf = self.font_tagline.render(tagline, True, THEME.text_secondary)
        tagline_x = (self.width - tagline_surf.get_width()) // 2
        self.screen.blit(tagline_surf, (tagline_x, 180))
        
        # Status chips
        chip_y = 215
        chips = []
        if self.shape_count is not None:
            chips.append(f"{self.shape_count} shapes")
        chips.append("Sandbox ready")
        chips.append("GPU: Pygame")
        x_cursor = (self.width - sum(self.font_hint.size(c)[0] + 28 for c in chips)) // 2
        for chip in chips:
            text_surf = self.font_hint.render(chip, True, THEME.text_secondary)
            chip_rect = pygame.Rect(x_cursor, chip_y, text_surf.get_width() + 20, 26)
            pygame.draw.rect(self.screen, THEME.bg_panel, chip_rect, border_radius=12)
            pygame.draw.rect(self.screen, THEME.border, chip_rect, width=1, border_radius=12)
            self.screen.blit(text_surf, (chip_rect.x + 10, chip_rect.y + 6))
            x_cursor += chip_rect.width + 8
        
        # Version
        version = "v1.0.0"
        version_surf = self.font_version.render(version, True, THEME.text_muted)
        self.screen.blit(version_surf, (self.width - version_surf.get_width() - 20, 20))
        
        # Menu cards
        for card in self.menu_cards:
            card.draw(self.screen)

        # Selected card helper
        if self.menu_cards:
            selected = self.menu_cards[self.selected_card]
            hint_text = f"Selected: {selected.title}  (Enter to open)"
            selected_surf = self.font_hint.render(hint_text, True, THEME.text_secondary)
            self.screen.blit(selected_surf, (40, self.height - 70))
        
        # Keyboard hints
        hint_y = self.height - 40
        hints = ["Arrows: Navigate", "Enter: Open", "1-4: Quick launch", "Esc: Quit"]
        hint_text = "  |  ".join(hints)
        hint_surf = self.font_hint.render(hint_text, True, THEME.text_muted)
        hint_x = (self.width - hint_surf.get_width()) // 2
        self.screen.blit(hint_surf, (hint_x, hint_y))
    
    def render_settings(self) -> None:
        """Render settings panel."""
        self.screen.fill(THEME.bg_dark)
        self.background.draw(self.screen, self.settings)

        # Title
        title = self.font_logo.render("Settings", True, THEME.text_primary)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 60))

        # Panel
        panel_width = 560
        panel_height = 420
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = (self.width // 2, self.height // 2 + 30)
        pygame.draw.rect(self.screen, THEME.bg_panel, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, THEME.border, panel_rect, width=2, border_radius=16)

        # Items
        self._settings_rects = []
        y = panel_rect.y + 40
        for idx, item in enumerate(self.settings_items):
            item_rect = pygame.Rect(panel_rect.x + 30, y, panel_rect.width - 60, 44)
            self._settings_rects.append(item_rect)
            selected = idx == self.settings_index
            bg = THEME.bg_card_hover if selected else THEME.bg_panel
            pygame.draw.rect(self.screen, bg, item_rect, border_radius=10)
            if selected:
                pygame.draw.rect(self.screen, THEME.accent_cyan, item_rect, width=2, border_radius=10)

            label = item["label"]
            label_surf = self.font_body.render(label, True, THEME.text_primary if selected else THEME.text_secondary)
            self.screen.blit(label_surf, (item_rect.x + 12, item_rect.y + 12))

            if item["type"] == "toggle":
                value = getattr(self.settings, item["attr"])
                status = "ON" if value else "OFF"
                status_color = THEME.accent_green if value else THEME.text_muted
                pill = pygame.Rect(item_rect.right - 90, item_rect.y + 10, 70, 24)
                pygame.draw.rect(self.screen, THEME.bg_dark, pill, border_radius=12)
                pygame.draw.rect(self.screen, status_color, pill, width=2, border_radius=12)
                status_surf = self.font_hint.render(status, True, status_color)
                self.screen.blit(status_surf, (pill.x + 18, pill.y + 4))
            else:
                action_surf = self.font_hint.render("Enter", True, THEME.text_muted)
                self.screen.blit(action_surf, (item_rect.right - 60, item_rect.y + 13))

            y += 54

        # Back hint
        hint = self.font_hint.render("Arrow keys to move, Enter to toggle, ESC to return", True, THEME.text_muted)
        self.screen.blit(hint, ((self.width - hint.get_width()) // 2, self.height - 50))
    
    def render_about(self) -> None:
        """Render about panel."""
        self.screen.fill(THEME.bg_dark)
        self.background.draw(self.screen, self.settings)
        
        # Title
        title = self.font_logo.render("About HyperSim", True, THEME.text_primary)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 60))
        
        panel_width = 760
        panel_height = 520
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = (self.width // 2, self.height // 2 + 30)
        pygame.draw.rect(self.screen, THEME.bg_panel, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, THEME.border, panel_rect, width=2, border_radius=16)

        about_lines = [
            "HyperSim is a 4D visualization and exploration toolkit.",
            "",
            "Highlights:",
            "  - Visualize 4D polytopes (tesseract, 24-cell, 600-cell, and more).",
            "  - Explore 4D space with movement across X, Y, Z, and W.",
            "  - Inspect 3D cross-sections and 4D rotations in six planes.",
            "",
            "The Fourth Dimension:",
            "  Just as a 3D being can see inside a 2D square,",
            "  a 4D being can see inside a 3D cube - all at once.",
            "  Move in W to experience this impossible viewpoint.",
            "",
            "Controls:",
            "  WASD + QE for XYZ, R/F for W (ana/kata),",
            "  arrow keys for 4D rotation.",
        ]

        y = panel_rect.y + 40
        for line in about_lines:
            if line.endswith(":") and not line.startswith("  "):
                color = THEME.accent_orange
            elif line.startswith("  -"):
                color = THEME.text_secondary
            else:
                color = THEME.text_secondary
            surf = self.font_body.render(line, True, color)
            self.screen.blit(surf, (panel_rect.x + 40, y))
            y += 26
        
        # Back hint
        hint = self.font_hint.render("Press any key to return to menu", True, THEME.text_muted)
        self.screen.blit(hint, ((self.width - hint.get_width()) // 2, self.height - 50))
    
    def render(self) -> None:
        """Render current view."""
        if self.mode == AppMode.MAIN_MENU:
            self.render_main_menu()
        elif self.mode == AppMode.SETTINGS:
            self.render_settings()
        elif self.mode == AppMode.ABOUT:
            self.render_about()
        
        pygame.display.flip()
    
    def run(self) -> None:
        """Main application loop."""
        last_time = pygame.time.get_ticks() / 1000.0
        
        while self.running:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_time, 0.1)
            last_time = now
            
            if self.mode == AppMode.EXPLORER and self._explorer:
                # Run explorer loop iteration
                self._explorer.handle_events()
                if not self._explorer.running:
                    self._return_to_menu()
                else:
                    self._explorer.update(dt)
                    self._explorer.render()
            
            elif self.mode == AppMode.SANDBOX and self._sandbox:
                # Run sandbox loop iteration  
                if not self._sandbox.step(dt):
                    self._return_to_menu()
            
            else:
                self.handle_events()
                self.update(dt)
                self.render()
            
            self.clock.tick(60)
        
        pygame.quit()


def run_hypersim_app() -> None:
    """Launch the HyperSim application."""
    app = HyperSimApp()
    app.run()


if __name__ == "__main__":
    run_hypersim_app()
