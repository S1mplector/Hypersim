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
# Animated Background
# =============================================================================

class AnimatedBackground:
    """Animated 4D-inspired background."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.time = 0.0
        
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
    
    def update(self, dt: float) -> None:
        """Update animation."""
        self.time += dt
        
        for p in self.particles:
            p['y'] -= p['speed'] * 30 * dt
            p['w'] += dt * 0.5
            if p['y'] < -10:
                p['y'] = self.height + 10
                p['x'] = np.random.uniform(0, self.width)
    
    def draw(self, surface: pygame.Surface) -> None:
        """Draw animated background."""
        # Draw particles
        for p in self.particles:
            alpha = int(80 + 40 * math.sin(p['w']))
            size = int(p['size'] * (0.5 + 0.5 * p['z']))
            color = (
                int(60 + 30 * math.sin(p['w'])),
                int(80 + 20 * math.sin(p['w'] + 1)),
                int(120 + 30 * math.sin(p['w'] + 2)),
            )
            if 0 < p['y'] < self.height:
                pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), size)
        
        # Draw rotating tesseract in corner
        self._draw_tesseract(surface)
    
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
        self.hover_anim = 0.0
        
        self._font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self._font_desc = pygame.font.SysFont("Arial", 16)
        self._font_icon = pygame.font.SysFont("Arial", 48, bold=True)
    
    def update(self, dt: float, mouse_pos: Tuple[int, int]) -> None:
        """Update hover state."""
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        target = 1.0 if self.hovered else 0.0
        self.hover_anim += (target - self.hover_anim) * dt * 10
    
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
        bg_color = (
            int(THEME.bg_card[0] + (THEME.bg_card_hover[0] - THEME.bg_card[0]) * self.hover_anim),
            int(THEME.bg_card[1] + (THEME.bg_card_hover[1] - THEME.bg_card[1]) * self.hover_anim),
            int(THEME.bg_card[2] + (THEME.bg_card_hover[2] - THEME.bg_card[2]) * self.hover_anim),
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
        border_color = (
            int(THEME.border[0] + (self.accent_color[0] - THEME.border[0]) * self.hover_anim * 0.5),
            int(THEME.border[1] + (self.accent_color[1] - THEME.border[1]) * self.hover_anim * 0.5),
            int(THEME.border[2] + (self.accent_color[2] - THEME.border[2]) * self.hover_anim * 0.5),
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
        if self.hover_anim > 0.1:
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
        
        # Background
        self.background = AnimatedBackground(width, height)
        
        # Fonts
        self.font_logo = pygame.font.SysFont("Arial", 64, bold=True)
        self.font_tagline = pygame.font.SysFont("Arial", 20)
        self.font_version = pygame.font.SysFont("Arial", 14)
        self.font_hint = pygame.font.SysFont("Arial", 16)
        
        # Menu cards
        self._create_menu_cards()
        
        # Sub-applications (lazy loaded)
        self._explorer = None
        self._sandbox = None
    
    def _create_menu_cards(self) -> None:
        """Create the main menu cards."""
        card_width = 500
        card_height = 100
        card_x = (self.width - card_width) // 2
        start_y = 320
        spacing = 130
        
        self.menu_cards = [
            MenuCard(
                rect=pygame.Rect(card_x, start_y, card_width, card_height),
                title="Object Explorer",
                description="Browse and visualize 4D polytopes with interactive controls",
                icon_char="◇",
                accent_color=THEME.accent_blue,
                on_click=lambda: self._launch_explorer(),
            ),
            MenuCard(
                rect=pygame.Rect(card_x, start_y + spacing, card_width, card_height),
                title="4D Sandbox",
                description="Explore 4D space as a 4D being - spawn objects, move freely",
                icon_char="◈",
                accent_color=THEME.accent_purple,
                on_click=lambda: self._launch_sandbox(),
            ),
            MenuCard(
                rect=pygame.Rect(card_x, start_y + spacing * 2, card_width, card_height),
                title="Settings",
                description="Configure display, controls, and preferences",
                icon_char="⚙",
                accent_color=THEME.accent_cyan,
                on_click=lambda: self._show_settings(),
            ),
            MenuCard(
                rect=pygame.Rect(card_x, start_y + spacing * 3, card_width, card_height),
                title="About HyperSim",
                description="Learn about the project and 4D visualization",
                icon_char="?",
                accent_color=THEME.accent_orange,
                on_click=lambda: self._show_about(),
            ),
        ]
    
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
            
            elif self.mode == AppMode.ABOUT:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self._return_to_menu()
    
    def update(self, dt: float) -> None:
        """Update application state."""
        mouse_pos = pygame.mouse.get_pos()
        
        if self.mode == AppMode.MAIN_MENU:
            self.background.update(dt)
            for card in self.menu_cards:
                card.update(dt, mouse_pos)
    
    def render_main_menu(self) -> None:
        """Render the main menu."""
        # Background
        self.screen.fill(THEME.bg_dark)
        self.background.draw(self.screen)
        
        # Logo
        logo_text = "HyperSim"
        logo_surf = self.font_logo.render(logo_text, True, THEME.text_primary)
        logo_x = (self.width - logo_surf.get_width()) // 2
        self.screen.blit(logo_surf, (logo_x, 80))
        
        # Accent line under logo
        line_width = 200
        line_x = (self.width - line_width) // 2
        pygame.draw.line(self.screen, THEME.accent_blue, (line_x, 160), (line_x + line_width, 160), 3)
        
        # Tagline
        tagline = "4D Visualization Suite"
        tagline_surf = self.font_tagline.render(tagline, True, THEME.text_secondary)
        tagline_x = (self.width - tagline_surf.get_width()) // 2
        self.screen.blit(tagline_surf, (tagline_x, 180))
        
        # Version
        version = "v1.0.0"
        version_surf = self.font_version.render(version, True, THEME.text_muted)
        self.screen.blit(version_surf, (self.width - version_surf.get_width() - 20, 20))
        
        # Menu cards
        for card in self.menu_cards:
            card.draw(self.screen)
        
        # Keyboard hints
        hint_y = self.height - 40
        hints = ["1-4: Quick select", "Esc: Quit"]
        hint_text = "  |  ".join(hints)
        hint_surf = self.font_hint.render(hint_text, True, THEME.text_muted)
        hint_x = (self.width - hint_surf.get_width()) // 2
        self.screen.blit(hint_surf, (hint_x, hint_y))
    
    def render_settings(self) -> None:
        """Render settings panel."""
        self.screen.fill(THEME.bg_dark)
        
        # Title
        title = self.font_logo.render("Settings", True, THEME.text_primary)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 60))
        
        # Settings content
        settings_text = [
            "Display Settings",
            "  Resolution: 1400 x 900",
            "  Fullscreen: Off",
            "",
            "Controls",
            "  Mouse Sensitivity: 1.0",
            "  Invert Y-Axis: Off",
            "",
            "Rendering",
            "  Line Width: 2",
            "  Show Grid: On",
            "  Particles: On",
        ]
        
        y = 180
        font = pygame.font.SysFont("Arial", 18)
        for line in settings_text:
            color = THEME.accent_cyan if not line.startswith("  ") and line else THEME.text_secondary
            surf = font.render(line, True, color)
            self.screen.blit(surf, (self.width // 2 - 150, y))
            y += 30
        
        # Back hint
        hint = self.font_hint.render("Press ESC to return to menu", True, THEME.text_muted)
        self.screen.blit(hint, ((self.width - hint.get_width()) // 2, self.height - 50))
    
    def render_about(self) -> None:
        """Render about panel."""
        self.screen.fill(THEME.bg_dark)
        self.background.draw(self.screen)
        
        # Title
        title = self.font_logo.render("About HyperSim", True, THEME.text_primary)
        self.screen.blit(title, ((self.width - title.get_width()) // 2, 60))
        
        # About content
        about_lines = [
            "HyperSim is a 4D visualization and exploration toolkit.",
            "",
            "Features:",
            "  • Visualize 4D polytopes (tesseract, 24-cell, 600-cell, etc.)",
            "  • Explore 4D space with full movement in X, Y, Z, and W",
            "  • See how 3D objects appear from a 4D perspective",
            "  • Interactive rotation in all 6 planes",
            "",
            "The Fourth Dimension:",
            "  Just as a 3D being can see inside a 2D square,",
            "  a 4D being can see inside a 3D cube - all at once.",
            "  Move in W to experience this impossible viewpoint.",
            "",
            "Controls use WASD + QE for XYZ, R/F for W (ana/kata),",
            "and arrow keys for 4D rotation.",
        ]
        
        y = 180
        font = pygame.font.SysFont("Arial", 18)
        for line in about_lines:
            if line.endswith(":") and not line.startswith(" "):
                color = THEME.accent_orange
            elif line.startswith("  •"):
                color = THEME.text_secondary
            else:
                color = THEME.text_secondary
            surf = font.render(line, True, color)
            self.screen.blit(surf, ((self.width - 600) // 2, y))
            y += 28
        
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
                if not self._sandbox.handle_input(dt):
                    self._return_to_menu()
                else:
                    self._sandbox.render()
            
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
