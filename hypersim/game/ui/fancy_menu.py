"""Fancy animated main menu for Tessera."""
from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple
from pathlib import Path

import pygame
import numpy as np


# =============================================================================
# COSMIC BACKGROUND
# =============================================================================

@dataclass
class Star:
    """A star in the cosmic background."""
    x: float
    y: float
    z: float  # Depth (for parallax)
    size: float
    brightness: float
    twinkle_phase: float
    twinkle_speed: float
    color: Tuple[int, int, int] = (255, 255, 255)


@dataclass
class Nebula:
    """A nebula cloud in the background."""
    x: float
    y: float
    radius: float
    color: Tuple[int, int, int]
    alpha: float
    drift_x: float
    drift_y: float


class CosmicBackground:
    """Animated cosmic vector background with stars, nebulae, and grid lines."""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.time = 0.0
        
        # Stars
        self.stars: List[Star] = []
        self._init_stars(200)
        
        # Nebulae
        self.nebulae: List[Nebula] = []
        self._init_nebulae(5)
        
        # Grid lines (dimensional grid effect)
        self.grid_enabled = True
        self.grid_scroll = 0.0
        
        # Shooting stars
        self.shooting_stars: List[Dict] = []
        self.shooting_star_timer = 0.0
    
    def _init_stars(self, count: int) -> None:
        """Initialize star field."""
        for _ in range(count):
            self.stars.append(Star(
                x=random.uniform(0, self.width),
                y=random.uniform(0, self.height),
                z=random.uniform(0.1, 1.0),
                size=random.uniform(0.5, 2.5),
                brightness=random.uniform(0.3, 1.0),
                twinkle_phase=random.uniform(0, math.pi * 2),
                twinkle_speed=random.uniform(1.0, 4.0),
                color=random.choice([
                    (255, 255, 255),
                    (200, 220, 255),
                    (255, 200, 200),
                    (200, 255, 200),
                    (255, 255, 200),
                ]),
            ))
    
    def _init_nebulae(self, count: int) -> None:
        """Initialize nebula clouds."""
        nebula_colors = [
            (100, 50, 150),   # Purple
            (50, 100, 150),   # Blue
            (150, 50, 100),   # Pink
            (50, 150, 100),   # Teal
            (100, 100, 150),  # Lavender
        ]
        
        for _ in range(count):
            self.nebulae.append(Nebula(
                x=random.uniform(-100, self.width + 100),
                y=random.uniform(-100, self.height + 100),
                radius=random.uniform(150, 400),
                color=random.choice(nebula_colors),
                alpha=random.uniform(0.05, 0.15),
                drift_x=random.uniform(-5, 5),
                drift_y=random.uniform(-5, 5),
            ))
    
    def update(self, dt: float) -> None:
        """Update cosmic animation."""
        self.time += dt
        
        # Update stars (twinkle)
        for star in self.stars:
            star.twinkle_phase += star.twinkle_speed * dt
        
        # Update nebulae (slow drift)
        for nebula in self.nebulae:
            nebula.x += nebula.drift_x * dt
            nebula.y += nebula.drift_y * dt
            
            # Wrap around
            if nebula.x < -nebula.radius:
                nebula.x = self.width + nebula.radius
            elif nebula.x > self.width + nebula.radius:
                nebula.x = -nebula.radius
            if nebula.y < -nebula.radius:
                nebula.y = self.height + nebula.radius
            elif nebula.y > self.height + nebula.radius:
                nebula.y = -nebula.radius
        
        # Grid scroll
        self.grid_scroll += dt * 20
        
        # Shooting stars
        self.shooting_star_timer += dt
        if self.shooting_star_timer > random.uniform(3, 8):
            self.shooting_star_timer = 0
            self._spawn_shooting_star()
        
        # Update shooting stars
        for ss in self.shooting_stars[:]:
            ss["progress"] += dt * ss["speed"]
            if ss["progress"] > 1.0:
                self.shooting_stars.remove(ss)
    
    def _spawn_shooting_star(self) -> None:
        """Spawn a shooting star."""
        self.shooting_stars.append({
            "x": random.uniform(0, self.width),
            "y": random.uniform(0, self.height * 0.5),
            "angle": random.uniform(math.pi * 0.6, math.pi * 0.9),
            "length": random.uniform(50, 150),
            "speed": random.uniform(0.8, 1.5),
            "progress": 0.0,
        })
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the cosmic background."""
        # Deep space background
        screen.fill((3, 5, 15))
        
        # Draw dimensional grid
        if self.grid_enabled:
            self._draw_grid(screen)
        
        # Draw stars
        for star in self.stars:
            self._draw_star(screen, star)
        
        # Draw shooting stars
        for ss in self.shooting_stars:
            self._draw_shooting_star(screen, ss)
    
    def _draw_nebula(self, screen: pygame.Surface, nebula: Nebula) -> None:
        """Draw a nebula cloud."""
        # Create gradient circles
        for i in range(5):
            radius = int(nebula.radius * (1 - i * 0.15))
            alpha = int(nebula.alpha * 255 * (1 - i * 0.2))
            if alpha > 0 and radius > 0:
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color = (*nebula.color, alpha)
                pygame.draw.circle(surf, color, (radius, radius), radius)
                screen.blit(surf, (int(nebula.x - radius), int(nebula.y - radius)), special_flags=pygame.BLEND_ADD)
    
    def _draw_grid(self, screen: pygame.Surface) -> None:
        """Draw dimensional grid lines."""
        grid_color = (15, 20, 40)
        spacing = 60
        
        # Horizontal lines with perspective
        for i in range(20):
            y = self.height - i * spacing + int(self.grid_scroll) % spacing
            if 0 <= y <= self.height:
                # Fade based on distance
                alpha = max(0, min(255, 255 - i * 12))
                color = (grid_color[0], grid_color[1], grid_color[2])
                pygame.draw.line(screen, color, (0, y), (self.width, y), 1)
        
        # Vertical lines converging to horizon
        horizon_y = self.height * 0.3
        for i in range(-10, 11):
            x_bottom = self.width // 2 + i * spacing
            x_top = self.width // 2 + i * spacing * 0.3
            pygame.draw.line(screen, grid_color, 
                           (x_bottom, self.height), 
                           (int(x_top), int(horizon_y)), 1)
    
    def _draw_star(self, screen: pygame.Surface, star: Star) -> None:
        """Draw a twinkling star."""
        # Calculate twinkle
        twinkle = 0.5 + 0.5 * math.sin(star.twinkle_phase)
        brightness = star.brightness * (0.7 + 0.3 * twinkle)
        
        # Color with brightness
        color = tuple(int(c * brightness) for c in star.color)
        
        # Size with twinkle
        size = star.size * (0.8 + 0.2 * twinkle)
        
        # Draw star (no glow)
        pygame.draw.circle(screen, color, (int(star.x), int(star.y)), max(1, int(size)))
    
    def _draw_shooting_star(self, screen: pygame.Surface, ss: Dict) -> None:
        """Draw a shooting star."""
        progress = ss["progress"]
        
        # Calculate positions
        start_x = ss["x"] + math.cos(ss["angle"]) * ss["length"] * progress
        start_y = ss["y"] + math.sin(ss["angle"]) * ss["length"] * progress
        
        tail_length = ss["length"] * 0.5 * (1 - progress)
        end_x = start_x - math.cos(ss["angle"]) * tail_length
        end_y = start_y - math.sin(ss["angle"]) * tail_length
        
        # Draw with gradient
        alpha = int(255 * (1 - progress))
        color = (255, 255, 255)
        
        pygame.draw.line(screen, color, (int(start_x), int(start_y)), (int(end_x), int(end_y)), 2)


# =============================================================================
# 4D SHAPE RENDERER
# =============================================================================

class Shape4DRenderer:
    """Renders animated 4D shapes with proper rotations."""
    
    def __init__(self):
        self.time = 0.0
        
        # Rotation angles (6 rotation planes in 4D)
        self.angle_xy = 0.0
        self.angle_xz = 0.0
        self.angle_xw = 0.0
        self.angle_yz = 0.0
        self.angle_yw = 0.0
        self.angle_zw = 0.0
        
        # Animation speeds
        self.speed_xy = 0.3
        self.speed_xz = 0.2
        self.speed_xw = 0.5  # This creates the "4D rotation" effect
        self.speed_yz = 0.25
        self.speed_yw = 0.4
        self.speed_zw = 0.35
    
    def update(self, dt: float) -> None:
        """Update rotation angles."""
        self.time += dt
        self.angle_xy += self.speed_xy * dt
        self.angle_xz += self.speed_xz * dt
        self.angle_xw += self.speed_xw * dt
        self.angle_yz += self.speed_yz * dt
        self.angle_yw += self.speed_yw * dt
        self.angle_zw += self.speed_zw * dt
    
    def _rotate_4d(self, vertex: np.ndarray) -> np.ndarray:
        """Apply 4D rotations to a vertex."""
        x, y, z, w = vertex
        
        # XW rotation (the key 4D rotation!)
        cos_xw, sin_xw = math.cos(self.angle_xw), math.sin(self.angle_xw)
        x, w = x * cos_xw - w * sin_xw, x * sin_xw + w * cos_xw
        
        # YW rotation
        cos_yw, sin_yw = math.cos(self.angle_yw), math.sin(self.angle_yw)
        y, w = y * cos_yw - w * sin_yw, y * sin_yw + w * cos_yw
        
        # ZW rotation
        cos_zw, sin_zw = math.cos(self.angle_zw), math.sin(self.angle_zw)
        z, w = z * cos_zw - w * sin_zw, z * sin_zw + w * cos_zw
        
        # XY rotation
        cos_xy, sin_xy = math.cos(self.angle_xy), math.sin(self.angle_xy)
        x, y = x * cos_xy - y * sin_xy, x * sin_xy + y * cos_xy
        
        # XZ rotation
        cos_xz, sin_xz = math.cos(self.angle_xz), math.sin(self.angle_xz)
        x, z = x * cos_xz - z * sin_xz, x * sin_xz + z * cos_xz
        
        return np.array([x, y, z, w])
    
    def _project_4d_to_2d(self, vertex: np.ndarray, scale: float, center: Tuple[int, int]) -> Tuple[int, int, float]:
        """Project 4D vertex to 2D screen coordinates."""
        x, y, z, w = vertex
        
        # 4D to 3D perspective projection
        distance_4d = 3.0
        factor_4d = distance_4d / (distance_4d - w)
        x3d = x * factor_4d
        y3d = y * factor_4d
        z3d = z * factor_4d
        
        # 3D to 2D perspective projection
        distance_3d = 4.0
        factor_3d = distance_3d / (distance_3d - z3d)
        x2d = x3d * factor_3d
        y2d = y3d * factor_3d
        
        screen_x = int(center[0] + x2d * scale)
        screen_y = int(center[1] - y2d * scale)
        depth = w + z3d  # For coloring
        
        return (screen_x, screen_y, depth)
    
    def draw_tesseract(self, screen: pygame.Surface, center: Tuple[int, int], 
                       scale: float = 100, color: Tuple[int, int, int] = (100, 180, 255)) -> None:
        """Draw an animated tesseract."""
        # Generate tesseract vertices
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append(np.array([x, y, z, w], dtype=float))
        
        # Generate edges (vertices differ in exactly one coordinate)
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                diff = bin(i ^ j).count('1')
                if diff == 1:
                    edges.append((i, j))
        
        # Rotate and project vertices
        projected = []
        for v in vertices:
            rotated = self._rotate_4d(v)
            proj = self._project_4d_to_2d(rotated, scale, center)
            projected.append(proj)
        
        # Draw edges with depth-based coloring
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            
            # Depth-based alpha/color
            avg_depth = (p1[2] + p2[2]) / 2
            depth_factor = (avg_depth + 2) / 4  # Normalize to 0-1
            depth_factor = max(0.2, min(1.0, depth_factor))
            
            edge_color = tuple(int(c * depth_factor) for c in color)
            width = max(1, int(2 * depth_factor))
            
            pygame.draw.line(screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), width)
        
        # Draw vertices
        for p in projected:
            depth_factor = (p[2] + 2) / 4
            depth_factor = max(0.3, min(1.0, depth_factor))
            vertex_color = tuple(int(c * depth_factor) for c in color)
            radius = max(2, int(4 * depth_factor))
            pygame.draw.circle(screen, vertex_color, (p[0], p[1]), radius)
    
    def draw_24cell(self, screen: pygame.Surface, center: Tuple[int, int],
                    scale: float = 100, color: Tuple[int, int, int] = (255, 150, 200)) -> None:
        """Draw an animated 24-cell (the unique self-dual 4D polytope)."""
        # 24-cell has 24 vertices: permutations of (±1, ±1, 0, 0)
        vertices = []
        
        # 8 vertices from (±1, ±1, 0, 0) permutations
        for i in range(4):
            for j in range(i + 1, 4):
                for s1 in [-1, 1]:
                    for s2 in [-1, 1]:
                        v = [0, 0, 0, 0]
                        v[i] = s1
                        v[j] = s2
                        vertices.append(np.array(v, dtype=float))
        
        # Generate edges (distance = sqrt(2))
        edges = []
        for i in range(len(vertices)):
            for j in range(i + 1, len(vertices)):
                dist_sq = np.sum((vertices[i] - vertices[j]) ** 2)
                if abs(dist_sq - 2.0) < 0.01:  # sqrt(2) distance
                    edges.append((i, j))
        
        # Rotate and project
        projected = []
        for v in vertices:
            rotated = self._rotate_4d(v)
            proj = self._project_4d_to_2d(rotated, scale, center)
            projected.append(proj)
        
        # Draw edges
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            avg_depth = (p1[2] + p2[2]) / 2
            depth_factor = (avg_depth + 2) / 4
            depth_factor = max(0.2, min(1.0, depth_factor))
            
            edge_color = tuple(int(c * depth_factor) for c in color)
            pygame.draw.line(screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1)
        
        # Draw vertices
        for p in projected:
            depth_factor = (p[2] + 2) / 4
            depth_factor = max(0.3, min(1.0, depth_factor))
            vertex_color = tuple(int(c * depth_factor) for c in color)
            radius = max(2, int(3 * depth_factor))
            pygame.draw.circle(screen, vertex_color, (p[0], p[1]), radius)


# =============================================================================
# ANIMATED BUTTON
# =============================================================================

class ButtonState(Enum):
    """Button animation states."""
    NORMAL = auto()
    HOVER = auto()
    PRESSED = auto()
    DISABLED = auto()


@dataclass
class AnimatedButton:
    """A fancy animated menu button."""
    id: str
    text: str
    x: int
    y: int
    width: int
    height: int
    
    # State
    state: ButtonState = ButtonState.NORMAL
    hover_progress: float = 0.0
    press_progress: float = 0.0
    glow_phase: float = 0.0
    
    # Callbacks
    on_click: Optional[Callable] = None
    enabled: bool = True
    
    # Style
    color_normal: Tuple[int, int, int] = (30, 40, 60)
    color_hover: Tuple[int, int, int] = (50, 70, 100)
    color_pressed: Tuple[int, int, int] = (70, 100, 140)
    color_text: Tuple[int, int, int] = (200, 210, 230)
    color_glow: Tuple[int, int, int] = (100, 150, 255)
    
    def update(self, dt: float, mouse_pos: Tuple[int, int], mouse_pressed: bool) -> bool:
        """Update button. Returns True if clicked."""
        if not self.enabled:
            self.state = ButtonState.DISABLED
            return False
        
        # Check hover
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        is_hovered = rect.collidepoint(mouse_pos)
        
        # Update state
        clicked = False
        if is_hovered:
            if mouse_pressed:
                if self.state != ButtonState.PRESSED:
                    self.state = ButtonState.PRESSED
            else:
                if self.state == ButtonState.PRESSED:
                    # Released while hovering = click
                    clicked = True
                    if self.on_click:
                        self.on_click()
                self.state = ButtonState.HOVER
        else:
            self.state = ButtonState.NORMAL
        
        # Animate hover
        target_hover = 1.0 if is_hovered else 0.0
        self.hover_progress += (target_hover - self.hover_progress) * dt * 8
        
        # Animate press
        target_press = 1.0 if self.state == ButtonState.PRESSED else 0.0
        self.press_progress += (target_press - self.press_progress) * dt * 15
        
        # Glow animation
        self.glow_phase += dt * 2
        
        return clicked
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button."""
        # Calculate current color
        if self.state == ButtonState.DISABLED:
            bg_color = (20, 20, 30)
            text_color = (80, 80, 100)
        else:
            # Interpolate between states
            bg_color = self._lerp_color(
                self._lerp_color(self.color_normal, self.color_hover, self.hover_progress),
                self.color_pressed,
                self.press_progress
            )
            text_color = self.color_text
        
        # Offset for press effect
        offset_y = int(self.press_progress * 2)
        
        # Draw glow
        if self.hover_progress > 0.1 and self.enabled:
            glow_alpha = int(50 * self.hover_progress * (0.7 + 0.3 * math.sin(self.glow_phase)))
            glow_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            glow_color = (*self.color_glow, glow_alpha)
            pygame.draw.rect(glow_surf, glow_color, (0, 0, self.width + 20, self.height + 20), border_radius=12)
            screen.blit(glow_surf, (self.x - 10, self.y - 10 + offset_y), special_flags=pygame.BLEND_ADD)
        
        # Draw button background
        rect = pygame.Rect(self.x, self.y + offset_y, self.width, self.height)
        pygame.draw.rect(screen, bg_color, rect, border_radius=8)
        
        # Draw border
        border_color = self._lerp_color((50, 60, 80), self.color_glow, self.hover_progress)
        pygame.draw.rect(screen, border_color, rect, width=2, border_radius=8)
        
        # Draw text
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2 + offset_y))
        screen.blit(text_surf, text_rect)
        
        # Draw shine effect
        if self.hover_progress > 0.5:
            shine_x = self.x + int((self.glow_phase * 100) % (self.width + 100)) - 50
            if self.x <= shine_x <= self.x + self.width:
                pygame.draw.line(screen, (255, 255, 255, 50), 
                               (shine_x, self.y + offset_y + 5), 
                               (shine_x + 30, self.y + offset_y + 5), 2)
    
    def _lerp_color(self, c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        """Linearly interpolate between two colors."""
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


# =============================================================================
# MAIN MENU
# =============================================================================

class MenuState(Enum):
    """Menu screen states."""
    MAIN = auto()
    SETTINGS = auto()
    AUDIO = auto()
    GRAPHICS = auto()
    CONTROLS = auto()


class FancyMainMenu:
    """The main menu for Tessera with all fancy effects."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # State
        self.state = MenuState.MAIN
        self.transition_alpha = 0.0
        self.title_offset = -100
        self.buttons_visible = False
        self.intro_time = 0.0
        self.intro_done = False
        
        # Background
        self.cosmic_bg = CosmicBackground(self.width, self.height)
        
        # 4D shape
        self.shape_renderer = Shape4DRenderer()
        self.show_24cell = True  # Show 24-cell instead of tesseract for variety
        
        # Fonts
        self._font_title = pygame.font.Font(None, 120)
        self._font_subtitle = pygame.font.Font(None, 36)
        self._font_button = pygame.font.Font(None, 32)
        self._font_small = pygame.font.Font(None, 24)
        
        # Buttons
        self.buttons: Dict[str, AnimatedButton] = {}
        self._init_buttons()
        
        # Music
        self.music_playing = False
        self.music_path = Path(__file__).parent.parent / "assets" / "bgm" / "mainmenu.mp3"
        
        # Callbacks
        self.on_start_game: Optional[Callable[[str], None]] = None
        self.on_quit: Optional[Callable] = None
        
        # Settings values
        self.settings = {
            "master_volume": 0.8,
            "music_volume": 0.7,
            "sfx_volume": 0.8,
            "fullscreen": False,
            "vsync": True,
            "mouse_sensitivity": 1.0,
        }
    
    def _init_buttons(self) -> None:
        """Initialize menu buttons."""
        button_width = 280
        button_height = 50
        start_y = self.height // 2 + 50
        spacing = 65
        center_x = self.width // 2 - button_width // 2
        
        # Main menu buttons
        main_buttons = [
            ("campaign", "Campaign"),
            ("quickplay", "Quick Play"),
            ("multiplayer", "Multiplayer"),
            ("settings", "Settings"),
            ("quit", "Quit"),
        ]
        
        for i, (btn_id, text) in enumerate(main_buttons):
            self.buttons[btn_id] = AnimatedButton(
                id=btn_id,
                text=text,
                x=center_x,
                y=start_y + i * spacing,
                width=button_width,
                height=button_height,
            )
        
        # Settings buttons
        settings_buttons = [
            ("audio", "Audio"),
            ("graphics", "Graphics"),
            ("controls", "Controls"),
            ("back_settings", "Back"),
        ]
        
        for i, (btn_id, text) in enumerate(settings_buttons):
            self.buttons[btn_id] = AnimatedButton(
                id=btn_id,
                text=text,
                x=center_x,
                y=start_y + i * spacing,
                width=button_width,
                height=button_height,
            )
        
        # Back button for sub-menus
        self.buttons["back"] = AnimatedButton(
            id="back",
            text="Back",
            x=center_x,
            y=start_y + 4 * spacing,
            width=button_width,
            height=button_height,
        )
        
        # Set callbacks
        self.buttons["campaign"].on_click = lambda: self._start_mode("campaign")
        self.buttons["quickplay"].on_click = lambda: self._start_mode("quickplay")
        self.buttons["multiplayer"].on_click = lambda: self._start_mode("multiplayer")
        self.buttons["settings"].on_click = lambda: self._go_to(MenuState.SETTINGS)
        self.buttons["quit"].on_click = self._quit
        
        self.buttons["audio"].on_click = lambda: self._go_to(MenuState.AUDIO)
        self.buttons["graphics"].on_click = lambda: self._go_to(MenuState.GRAPHICS)
        self.buttons["controls"].on_click = lambda: self._go_to(MenuState.CONTROLS)
        self.buttons["back_settings"].on_click = lambda: self._go_to(MenuState.MAIN)
        self.buttons["back"].on_click = lambda: self._go_to(MenuState.SETTINGS)
    
    def start_music(self) -> None:
        """Start background music."""
        if not self.music_playing and self.music_path.exists():
            try:
                pygame.mixer.music.load(str(self.music_path))
                pygame.mixer.music.set_volume(self.settings["music_volume"] * self.settings["master_volume"])
                pygame.mixer.music.play(-1)  # Loop forever
                self.music_playing = True
            except Exception as e:
                print(f"Could not play music: {e}")
    
    def stop_music(self) -> None:
        """Stop background music."""
        if self.music_playing:
            pygame.mixer.music.fadeout(500)
            self.music_playing = False
    
    def _start_mode(self, mode: str) -> None:
        """Start a game mode."""
        if self.on_start_game:
            self.stop_music()
            self.on_start_game(mode)
    
    def _quit(self) -> None:
        """Quit the game."""
        if self.on_quit:
            self.stop_music()
            self.on_quit()
    
    def _go_to(self, state: MenuState) -> None:
        """Navigate to a menu state."""
        self.state = state
    
    def update(self, dt: float) -> None:
        """Update menu animations."""
        # Intro animation
        self.intro_time += dt
        if self.intro_time > 0.5 and self.title_offset < 0:
            self.title_offset = min(0, self.title_offset + dt * 200)
        if self.intro_time > 1.0:
            self.buttons_visible = True
            self.intro_done = True
        
        # Fade in
        if self.transition_alpha < 1.0:
            self.transition_alpha = min(1.0, self.transition_alpha + dt * 2)
        
        # Background
        self.cosmic_bg.update(dt)
        
        # 4D shape
        self.shape_renderer.update(dt)
        
        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        
        active_buttons = self._get_active_buttons()
        for btn_id in active_buttons:
            if btn_id in self.buttons:
                self.buttons[btn_id].update(dt, mouse_pos, mouse_pressed)
    
    def _get_active_buttons(self) -> List[str]:
        """Get button IDs for current state."""
        if self.state == MenuState.MAIN:
            return ["campaign", "quickplay", "multiplayer", "settings", "quit"]
        elif self.state == MenuState.SETTINGS:
            return ["audio", "graphics", "controls", "back_settings"]
        elif self.state in (MenuState.AUDIO, MenuState.GRAPHICS, MenuState.CONTROLS):
            return ["back"]
        return []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == MenuState.MAIN:
                    self._quit()
                else:
                    self._go_to(MenuState.MAIN if self.state == MenuState.SETTINGS else MenuState.SETTINGS)
                return True
        return False
    
    def draw(self) -> None:
        """Draw the menu."""
        # Cosmic background
        self.cosmic_bg.draw(self.screen)
        
        # 4D shape in background
        shape_center = (self.width // 2, self.height // 2 - 50)
        if self.show_24cell:
            self.shape_renderer.draw_24cell(
                self.screen, shape_center, 
                scale=150, color=(60, 100, 180)
            )
        else:
            self.shape_renderer.draw_tesseract(
                self.screen, shape_center,
                scale=120, color=(60, 100, 180)
            )
        
        # Title
        self._draw_title()
        
        # Buttons (with fade-in)
        if self.buttons_visible:
            self._draw_buttons()
        
        # Settings sliders
        if self.state in (MenuState.AUDIO, MenuState.GRAPHICS, MenuState.CONTROLS):
            self._draw_settings_panel()
        
        # Version
        version_text = self._font_small.render("v0.1.0 Alpha", True, (60, 60, 80))
        self.screen.blit(version_text, (10, self.height - 25))
        
        # Controls hint
        hint_text = self._font_small.render("Navigate with mouse • ESC to go back", True, (60, 60, 80))
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint_text, hint_rect)
    
    def _draw_title(self) -> None:
        """Draw the game title."""
        title_y = 100 + int(self.title_offset)
        
        # Title text
        title_color = (220, 230, 255)
        title_surf = self._font_title.render("TESSERA", True, title_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, title_y))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle_color = (120, 140, 180)
        subtitle_surf = self._font_subtitle.render("A Cross-Dimensional Adventure", True, subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, title_y + 50))
        self.screen.blit(subtitle_surf, subtitle_rect)
    
    def _draw_buttons(self) -> None:
        """Draw active buttons."""
        active = self._get_active_buttons()
        for btn_id in active:
            if btn_id in self.buttons:
                self.buttons[btn_id].draw(self.screen, self._font_button)
    
    def _draw_settings_panel(self) -> None:
        """Draw settings sliders."""
        panel_x = self.width // 2 - 200
        panel_y = self.height // 2 - 100
        panel_width = 400
        
        # Panel background
        panel_surf = pygame.Surface((panel_width, 250), pygame.SRCALPHA)
        panel_surf.fill((20, 25, 40, 200))
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (50, 60, 80), (panel_x, panel_y, panel_width, 250), 2, border_radius=8)
        
        # Title
        if self.state == MenuState.AUDIO:
            title = "Audio Settings"
            settings = [
                ("Master Volume", "master_volume"),
                ("Music Volume", "music_volume"),
                ("SFX Volume", "sfx_volume"),
            ]
        elif self.state == MenuState.GRAPHICS:
            title = "Graphics Settings"
            settings = [
                ("Fullscreen", "fullscreen"),
                ("VSync", "vsync"),
            ]
        else:
            title = "Control Settings"
            settings = [
                ("Mouse Sensitivity", "mouse_sensitivity"),
            ]
        
        title_surf = self._font_button.render(title, True, (200, 210, 230))
        title_rect = title_surf.get_rect(center=(self.width // 2, panel_y + 25))
        self.screen.blit(title_surf, title_rect)
        
        # Settings
        y = panel_y + 60
        for label, key in settings:
            self._draw_setting_row(panel_x + 20, y, panel_width - 40, label, key)
            y += 50
    
    def _draw_setting_row(self, x: int, y: int, width: int, label: str, key: str) -> None:
        """Draw a single setting row."""
        # Label
        label_surf = self._font_small.render(label, True, (180, 190, 210))
        self.screen.blit(label_surf, (x, y))
        
        value = self.settings.get(key, 0)
        
        if isinstance(value, bool):
            # Toggle
            toggle_x = x + width - 60
            toggle_color = (100, 180, 100) if value else (80, 80, 100)
            pygame.draw.rect(self.screen, toggle_color, (toggle_x, y, 50, 24), border_radius=12)
            circle_x = toggle_x + 37 if value else toggle_x + 13
            pygame.draw.circle(self.screen, (255, 255, 255), (circle_x, y + 12), 8)
        else:
            # Slider
            slider_x = x + width - 160
            slider_width = 150
            pygame.draw.rect(self.screen, (40, 50, 70), (slider_x, y + 8, slider_width, 8), border_radius=4)
            fill_width = int(slider_width * value)
            pygame.draw.rect(self.screen, (100, 150, 255), (slider_x, y + 8, fill_width, 8), border_radius=4)
            pygame.draw.circle(self.screen, (200, 220, 255), (slider_x + fill_width, y + 12), 8)
            
            # Value text
            value_text = self._font_small.render(f"{int(value * 100)}%", True, (150, 160, 180))
            self.screen.blit(value_text, (slider_x + slider_width + 10, y))


def run_tessera_menu() -> Optional[str]:
    """Run the full Tessera menu experience. Returns selected mode or None."""
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Tessera")
    clock = pygame.time.Clock()
    
    # Splash sequence
    from .splash_screen import create_tessera_splash_sequence
    splash = create_tessera_splash_sequence(screen)
    
    # Main menu
    menu = FancyMainMenu(screen)
    
    running = True
    in_splash = True
    selected_mode = None
    
    def on_start(mode: str):
        nonlocal selected_mode, running
        selected_mode = mode
        running = False
    
    def on_quit():
        nonlocal running
        running = False
    
    menu.on_start_game = on_start
    menu.on_quit = on_quit
    
    while running:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif in_splash:
                splash.handle_event(event)
            else:
                menu.handle_event(event)
        
        if in_splash:
            if splash.update(dt):
                in_splash = False
                menu.start_music()
            splash.draw()
        else:
            menu.update(dt)
            menu.draw()
        
        pygame.display.flip()
    
    pygame.quit()
    return selected_mode
