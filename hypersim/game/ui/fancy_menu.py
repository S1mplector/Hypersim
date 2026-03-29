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

from hypersim.game.save_system import GameSaveData, SaveSlot, SaveType, get_save_manager


def load_font(candidates: List[str], size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
    """Pick the first available system font from a candidate list."""
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold, italic=italic)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)


def fit_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    """Clamp text to a maximum rendered width."""
    if font.size(text)[0] <= max_width:
        return text

    clipped = text
    while clipped and font.size(f"{clipped}...")[0] > max_width:
        clipped = clipped[:-1]
    return f"{clipped}..." if clipped else "..."


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
    color_normal: Tuple[int, int, int] = (18, 24, 38)
    color_hover: Tuple[int, int, int] = (32, 46, 68)
    color_pressed: Tuple[int, int, int] = (60, 90, 120)
    color_text: Tuple[int, int, int] = (235, 225, 210)
    color_glow: Tuple[int, int, int] = (255, 180, 90)
    
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
    LOAD_SAVE = auto()
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
        self.minimal_mode = True
        self.save_manager = get_save_manager()
        
        # State
        self.state = MenuState.MAIN
        self.transition_alpha = 0.0
        self.title_offset = -100
        self.buttons_visible = False
        self.intro_time = 0.0
        self.intro_done = False
        self.mosaic_phase = 0.0
        self.selection_phase = 0.0
        self.selected_index = 0
        self._dragging_setting: Optional[str] = None
        self._load_page = 0
        self._load_page_size = 4
        self._load_slots: List[SaveSlot] = []
        self._load_slot_buttons: Dict[str, SaveSlot] = {}
        self._load_visible_button_ids: List[str] = []
        self._selected_save_data: Optional[GameSaveData] = None
        
        # Background
        self.cosmic_bg = CosmicBackground(self.width, self.height)
        if self.minimal_mode:
            # Keep only subtle stars for a cleaner menu backdrop.
            self.cosmic_bg.grid_enabled = False
            self.cosmic_bg.stars = self.cosmic_bg.stars[:90]
            self.cosmic_bg.shooting_star_timer = -99999.0
            for star in self.cosmic_bg.stars:
                star.color = random.choice([
                    (225, 228, 232),
                    (165, 176, 194),
                    (218, 200, 176),
                ])
                star.size = min(star.size, 1.6)
                star.brightness *= 0.8
        
        # 4D shape
        self.shape_renderer = Shape4DRenderer()
        self.show_24cell = True  # Show 24-cell instead of tesseract for variety
        
        # Fonts
        self._font_title = load_font(["didot", "baskerville", "georgia", "timesnewroman"], 96)
        self._font_subtitle = load_font(["avenirnext", "gillsans", "helveticaneue", "arial"], 24)
        self._font_button = load_font(["avenirnext", "gillsans", "helveticaneue", "arial"], 30)
        self._font_small = load_font(["avenirnext", "gillsans", "helveticaneue", "arial"], 18)
        self._font_meta = load_font(["avenirnext", "gillsans", "helveticaneue", "arial"], 16)
        self._font_state = load_font(["avenirnext", "gillsans", "helveticaneue", "arial"], 21, bold=True)

        self._menu_blurbs = {
            "new_game": "Create a new game save",
            "load_save": "Choose a specific save.",
            "settings": "Adjust sound, display, and controls",
            "quit": "Leave the lattice",
            "load_prev": "Move toward the newer saves.",
            "load_next": "Move toward the older saves.",
            "load_back": "Return to the primary menu.",
            "audio": "Set the balance between hush and signal.",
            "graphics": "Choose the cleanest way to read the field.",
            "controls": "Tune movement and perception.",
            "back_settings": "Return to the primary menu.",
            "back": "Return to the previous panel.",
        }
        
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
        if self.minimal_mode:
            button_width = 360
            button_height = 44
            start_y = 308
            spacing = 58
            center_x = 96
        else:
            button_width = 320
            button_height = 48
            start_y = self.height // 2 + 10
            spacing = 58
            center_x = self.width // 2 - button_width // 2
        
        # Main menu buttons
        main_buttons = [
            ("new_game", "New Game"),
            ("load_save", "Load Save"),
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

        load_x, load_y, load_width, load_height, load_spacing = self._get_load_layout()
        self.buttons["load_prev"] = AnimatedButton(
            id="load_prev",
            text="Newer Saves",
            x=load_x,
            y=load_y + self._load_page_size * load_spacing + 6,
            width=load_width,
            height=load_height,
        )
        self.buttons["load_next"] = AnimatedButton(
            id="load_next",
            text="Older Saves",
            x=load_x,
            y=load_y + (self._load_page_size + 1) * load_spacing + 6,
            width=load_width,
            height=load_height,
        )
        self.buttons["load_back"] = AnimatedButton(
            id="load_back",
            text="Back",
            x=load_x,
            y=load_y + (self._load_page_size + 2) * load_spacing + 6,
            width=load_width,
            height=load_height,
        )
        
        # Set callbacks
        self.buttons["new_game"].on_click = lambda: self._start_mode("new_game")
        self.buttons["load_save"].on_click = self._open_load_menu
        self.buttons["settings"].on_click = lambda: self._go_to(MenuState.SETTINGS)
        self.buttons["quit"].on_click = self._quit
        self.buttons["load_prev"].on_click = lambda: self._change_load_page(-1)
        self.buttons["load_next"].on_click = lambda: self._change_load_page(1)
        self.buttons["load_back"].on_click = lambda: self._go_to(MenuState.MAIN)
        
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
        self.selected_index = 0
        self._dragging_setting = None

    def _get_load_layout(self) -> Tuple[int, int, int, int, int]:
        """Return layout constants for the load-save submenu."""
        return (96, 292, 390, 38, 48)

    def _open_load_menu(self) -> None:
        """Open the load-save submenu and refresh slots."""
        self._selected_save_data = None
        self._refresh_load_buttons(reset_page=True)
        self._go_to(MenuState.LOAD_SAVE)

    def _change_load_page(self, delta: int) -> None:
        """Change the visible save page."""
        if not self._load_slots:
            return

        page_count = self._get_load_page_count()
        self._load_page = max(0, min(page_count - 1, self._load_page + delta))
        self._refresh_load_buttons()
        self.selected_index = 0

    def _get_loadable_slots(self) -> List[SaveSlot]:
        """Collect all non-empty saves, ordered by recency."""
        slots = [
            slot
            for slot in (
                self.save_manager.get_manual_slots()
                + self.save_manager.get_auto_slots()
                + [self.save_manager.get_quicksave_slot()]
            )
            if not slot.is_empty and slot.metadata
        ]
        slots.sort(key=lambda slot: slot.metadata.updated_at if slot.metadata else 0.0, reverse=True)
        return slots

    def _get_load_page_count(self) -> int:
        """Return the total number of load submenu pages."""
        return max(1, math.ceil(len(self._load_slots) / max(1, self._load_page_size)))

    def _refresh_load_buttons(self, reset_page: bool = False) -> None:
        """Rebuild visible save-slot buttons for the current page."""
        for button_id in list(self._load_slot_buttons):
            self.buttons.pop(button_id, None)
        self._load_slot_buttons.clear()

        self._load_slots = self._get_loadable_slots()
        if reset_page:
            self._load_page = 0
        self._load_page = max(0, min(self._load_page, self._get_load_page_count() - 1))

        load_x, load_y, load_width, load_height, load_spacing = self._get_load_layout()
        start = self._load_page * self._load_page_size
        visible_slots = self._load_slots[start : start + self._load_page_size]

        self._load_visible_button_ids = []
        for index, slot in enumerate(visible_slots):
            button_id = f"load_slot_{start + index}"
            button = AnimatedButton(
                id=button_id,
                text=slot.metadata.save_name if slot.metadata else slot.display_name,
                x=load_x,
                y=load_y + index * load_spacing,
                width=load_width,
                height=load_height,
            )
            button.on_click = lambda slot=slot: self._select_load_slot(slot)
            self.buttons[button_id] = button
            self._load_slot_buttons[button_id] = slot
            self._load_visible_button_ids.append(button_id)

        if self._load_page > 0:
            self._load_visible_button_ids.append("load_prev")
        if self._load_page < self._get_load_page_count() - 1:
            self._load_visible_button_ids.append("load_next")
        self._load_visible_button_ids.append("load_back")

    def _select_load_slot(self, slot: SaveSlot) -> None:
        """Load the selected slot and exit the menu."""
        self._selected_save_data = self.save_manager.load_from_slot(slot.slot_id, slot.slot_type)
        if self._selected_save_data:
            self._start_mode("load_save")

    def consume_selected_save_data(self) -> Optional[GameSaveData]:
        """Return the chosen save data once."""
        save_data = self._selected_save_data
        self._selected_save_data = None
        return save_data

    def _get_preview_slot(self) -> Optional[SaveSlot]:
        """Return the save slot currently highlighted in the load submenu."""
        if not self._load_slot_buttons:
            return None

        if self._load_visible_button_ids:
            button_id = self._load_visible_button_ids[self.selected_index % len(self._load_visible_button_ids)]
            if button_id in self._load_slot_buttons:
                return self._load_slot_buttons[button_id]

        return next(iter(self._load_slot_buttons.values()), None)

    def _format_slot_prefix(self, slot: SaveSlot) -> str:
        """Format a compact save-slot prefix."""
        if slot.slot_type == SaveType.MANUAL:
            return f"M{slot.slot_id:02d}"
        if slot.slot_type == SaveType.AUTO:
            return f"A{slot.slot_id:02d}"
        if slot.slot_type == SaveType.QUICKSAVE:
            return "QS"
        return f"S{slot.slot_id:02d}"
    
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
        hovered_index = None
        for btn_id in active_buttons:
            if btn_id in self.buttons:
                btn = self.buttons[btn_id]
                btn.update(dt, mouse_pos, mouse_pressed)
                if pygame.Rect(btn.x, btn.y, btn.width, btn.height).collidepoint(mouse_pos):
                    hovered_index = active_buttons.index(btn_id)

        if hovered_index is not None:
            self.selected_index = hovered_index
        elif active_buttons:
            self.selected_index %= len(active_buttons)
        else:
            self.selected_index = 0
        
        # Overlay phase for subtle motion
        self.mosaic_phase += dt * 0.35
        self.selection_phase += dt * 2.1
    
    def _get_active_buttons(self) -> List[str]:
        """Get button IDs for current state."""
        if self.state == MenuState.MAIN:
            return ["new_game", "load_save", "settings", "quit"]
        elif self.state == MenuState.LOAD_SAVE:
            return self._load_visible_button_ids
        elif self.state == MenuState.SETTINGS:
            return ["audio", "graphics", "controls", "back_settings"]
        elif self.state in (MenuState.AUDIO, MenuState.GRAPHICS, MenuState.CONTROLS):
            return ["back"]
        return []
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input events."""
        if event.type == pygame.KEYDOWN:
            active_buttons = self._get_active_buttons()
            if event.key == pygame.K_ESCAPE:
                if self.state == MenuState.MAIN:
                    self._quit()
                elif self.state in (MenuState.LOAD_SAVE, MenuState.SETTINGS):
                    self._go_to(MenuState.MAIN)
                else:
                    self._go_to(MenuState.SETTINGS)
                return True
            if active_buttons and event.key in (pygame.K_UP, pygame.K_LEFT):
                self.selected_index = (self.selected_index - 1) % len(active_buttons)
                return True
            if active_buttons and event.key in (pygame.K_DOWN, pygame.K_RIGHT, pygame.K_TAB):
                self.selected_index = (self.selected_index + 1) % len(active_buttons)
                return True
            if active_buttons and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._activate_selected_button()
                return True

        if event.type == pygame.MOUSEMOTION:
            active_buttons = self._get_active_buttons()
            for index, btn_id in enumerate(active_buttons):
                btn = self.buttons.get(btn_id)
                if btn and pygame.Rect(btn.x, btn.y, btn.width, btn.height).collidepoint(event.pos):
                    self.selected_index = index
                    break
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_setting = None
        
        # Handle settings interactions
        if self.state in (MenuState.AUDIO, MenuState.GRAPHICS, MenuState.CONTROLS):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_settings_click(event.pos)
                return True
            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                self._handle_settings_drag(event.pos)
                return True
        
        return False

    def _activate_selected_button(self) -> None:
        """Activate the currently selected button."""
        active_buttons = self._get_active_buttons()
        if not active_buttons:
            return

        btn_id = active_buttons[self.selected_index % len(active_buttons)]
        button = self.buttons.get(btn_id)
        if button and button.enabled and button.on_click:
            button.on_click()
    
    def _handle_settings_click(self, pos: Tuple[int, int]) -> None:
        """Handle click on settings panel."""
        panel_x = self.width // 2 - 200
        panel_y = self.height // 2 - 100
        panel_width = 400
        
        # Get settings for current state
        if self.state == MenuState.AUDIO:
            settings = [
                ("Master Volume", "master_volume"),
                ("Music Volume", "music_volume"),
                ("SFX Volume", "sfx_volume"),
            ]
        elif self.state == MenuState.GRAPHICS:
            settings = [
                ("Fullscreen", "fullscreen"),
                ("VSync", "vsync"),
            ]
        else:
            settings = [
                ("Mouse Sensitivity", "mouse_sensitivity"),
            ]
        
        # Check each setting row
        y = panel_y + 60
        for label, key in settings:
            value = self.settings.get(key, 0)
            
            if isinstance(value, bool):
                # Toggle button area
                toggle_x = panel_x + 20 + panel_width - 40 - 60
                toggle_rect = pygame.Rect(toggle_x, y, 50, 24)
                if toggle_rect.collidepoint(pos):
                    self.settings[key] = not value
                    self._apply_setting(key)
                    return
            else:
                # Slider area
                slider_x = panel_x + 20 + panel_width - 40 - 160
                slider_width = 150
                slider_rect = pygame.Rect(slider_x - 10, y, slider_width + 20, 24)
                if slider_rect.collidepoint(pos):
                    # Calculate new value
                    new_value = (pos[0] - slider_x) / slider_width
                    new_value = max(0.0, min(1.0, new_value))
                    self.settings[key] = new_value
                    self._apply_setting(key)
                    self._dragging_setting = key
                    return
            
            y += 50
    
    def _handle_settings_drag(self, pos: Tuple[int, int]) -> None:
        """Handle dragging on settings sliders."""
        if not hasattr(self, '_dragging_setting') or not self._dragging_setting:
            return
        
        panel_x = self.width // 2 - 200
        panel_width = 400
        slider_x = panel_x + 20 + panel_width - 40 - 160
        slider_width = 150
        
        # Update the dragged slider
        key = self._dragging_setting
        if key in self.settings and not isinstance(self.settings[key], bool):
            new_value = (pos[0] - slider_x) / slider_width
            new_value = max(0.0, min(1.0, new_value))
            self.settings[key] = new_value
            self._apply_setting(key)
    
    def _apply_setting(self, key: str) -> None:
        """Apply a setting change immediately."""
        if key == "master_volume":
            if self.music_playing:
                pygame.mixer.music.set_volume(
                    self.settings["music_volume"] * self.settings["master_volume"]
                )
        elif key == "music_volume":
            if self.music_playing:
                pygame.mixer.music.set_volume(
                    self.settings["music_volume"] * self.settings["master_volume"]
                )
        elif key == "fullscreen":
            if self.settings["fullscreen"]:
                pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
            else:
                pygame.display.set_mode((self.width, self.height))
        elif key == "vsync":
            # VSync requires recreating display
            flags = pygame.FULLSCREEN if self.settings["fullscreen"] else 0
            if self.settings["vsync"]:
                flags |= pygame.DOUBLEBUF
            pygame.display.set_mode((self.width, self.height), flags)
    
    def draw(self) -> None:
        """Draw the menu."""
        # Cosmic background
        self.cosmic_bg.draw(self.screen)
        if self.minimal_mode:
            self._draw_minimal_background()
        else:
            self._draw_dimensional_overlay()
        
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
        
        # Lore snippet panel
        if self.state == MenuState.MAIN and not self.minimal_mode:
            self._draw_lore_panel()
        
        # Buttons (with fade-in)
        if self.buttons_visible:
            self._draw_buttons()
        
        # Settings sliders
        if self.state in (MenuState.AUDIO, MenuState.GRAPHICS, MenuState.CONTROLS):
            self._draw_settings_panel()
        
        # Version
        version_text = self._font_small.render("v0.1.0 Alpha", True, (130, 145, 165))
        self.screen.blit(version_text, (10, self.height - 25))
        
        # Controls hint
        hint = "Arrows / Enter / Mouse • ESC" if self.minimal_mode else "Navigate with mouse • ESC to go back"
        hint_text = self._font_small.render(hint, True, (130, 145, 165))
        hint_rect = hint_text.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(hint_text, hint_rect)

    def _draw_minimal_background(self) -> None:
        """Draw the stripped-back menu framing and right-side geometry panel."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        left_panel = pygame.Rect(58, 54, 470, self.height - 108)
        pygame.draw.rect(overlay, (8, 11, 18, 210), left_panel, border_radius=26)
        pygame.draw.rect(overlay, (72, 82, 94, 85), left_panel, width=1, border_radius=26)
        pygame.draw.line(
            overlay,
            (214, 182, 132, 210),
            (left_panel.x + 32, left_panel.y + 30),
            (left_panel.x + 180, left_panel.y + 30),
            2,
        )

        right_panel = pygame.Rect(self.width - 430, 76, 330, self.height - 152)
        pygame.draw.rect(overlay, (10, 14, 22, 165), right_panel, border_radius=24)
        pygame.draw.rect(overlay, (78, 92, 108, 70), right_panel, width=1, border_radius=24)

        for y in range(self.height):
            alpha = int(46 * (1 - y / max(1, self.height - 1)))
            overlay.fill((18, 24, 38, alpha), rect=pygame.Rect(0, y, self.width, 1))

        self.screen.blit(overlay, (0, 0))

        shape_center = (right_panel.centerx, right_panel.y + 210)
        self.shape_renderer.draw_24cell(
            self.screen,
            shape_center,
            scale=105,
            color=(105, 126, 156),
        )
        if self.state == MenuState.LOAD_SAVE:
            self._draw_load_preview(right_panel)

    def _draw_load_preview(self, panel: pygame.Rect) -> None:
        """Draw selected save details inside the right-side panel."""
        preview_slot = self._get_preview_slot()
        page_text = self._font_meta.render(
            f"ARCHIVE {self._load_page + 1}/{self._get_load_page_count()}",
            True,
            (142, 154, 170),
        )
        self.screen.blit(page_text, (panel.x + 26, panel.bottom - 226))

        pygame.draw.line(
            self.screen,
            (58, 68, 82),
            (panel.x + 26, panel.bottom - 196),
            (panel.right - 26, panel.bottom - 196),
            1,
        )

        if preview_slot is None or not preview_slot.metadata:
            empty_title = self._font_state.render("NO SAVES", True, (228, 232, 238))
            empty_body = self._font_small.render("No save files were found on this machine.", True, (160, 171, 186))
            self.screen.blit(empty_title, (panel.x + 26, panel.bottom - 168))
            self.screen.blit(empty_body, (panel.x + 26, panel.bottom - 130))
            return

        title = fit_text(self._font_state, preview_slot.metadata.save_name.upper(), panel.width - 52)
        title_surf = self._font_state.render(title, True, (236, 232, 220))
        self.screen.blit(title_surf, (panel.x + 26, panel.bottom - 168))

        details = [
            ("Slot", self._format_slot_prefix(preview_slot)),
            ("Type", preview_slot.slot_type.value.title()),
            ("Dimension", preview_slot.metadata.current_dimension.upper()),
            ("Updated", preview_slot.last_played),
            ("Playtime", preview_slot.playtime_display),
            ("Chapter", str(preview_slot.metadata.current_chapter)),
            ("Completion", f"{preview_slot.metadata.completion_percent:.0f}%"),
        ]

        y = panel.bottom - 128
        for label, value in details:
            label_surf = self._font_meta.render(label.upper(), True, (130, 142, 158))
            value_surf = self._font_small.render(value, True, (206, 212, 220))
            self.screen.blit(label_surf, (panel.x + 26, y))
            self.screen.blit(value_surf, (panel.x + 132, y))
            y += 24
    
    def _draw_title(self) -> None:
        """Draw the game title."""
        title_y = 112 + int(self.title_offset)

        if self.minimal_mode:
            left_x = 96
            eyebrow = self._font_meta.render("", True, (148, 158, 171))
            self.screen.blit(eyebrow, (left_x, title_y - 34))

            title_surf = self._font_title.render("TESSERA", True, (236, 232, 220))
            self.screen.blit(title_surf, (left_x, title_y))

            subtitles = {
                MenuState.LOAD_SAVE: "Select a save to resume.",
                MenuState.SETTINGS: "Tune the interface before you step back into the lattice.",
                MenuState.AUDIO: "Balance the room tone, music, and synthetic voices.",
                MenuState.GRAPHICS: "Adjust how sharply the simulation presents itself.",
                MenuState.CONTROLS: "Shape the motion before the world begins to move back.",
            }
            subtitle = subtitles.get(self.state, "")
            if subtitle:
                subtitle_surf = self._font_subtitle.render(subtitle, True, (181, 191, 205))
                self.screen.blit(subtitle_surf, (left_x, title_y + 86))
            return

        # Title text
        title_color = (236, 232, 220)
        title_surf = self._font_title.render("TESSERA", True, title_color)
        title_rect = title_surf.get_rect(center=(self.width // 2, title_y))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle_color = (175, 188, 210)
        subtitle_surf = self._font_subtitle.render("", True, subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, title_y + 50))
        self.screen.blit(subtitle_surf, subtitle_rect)

    def _draw_dimensional_overlay(self) -> None:
        """Layered overlays to match the game's dimensional/lore theme."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Radial glow
        center = (self.width // 2, int(self.height * 0.35))
        max_r = int(max(self.width, self.height) * 0.7)
        for i in range(6):
            radius = max_r - i * int(max_r * 0.12)
            alpha = max(10, 80 - i * 12)
            color = (40, 70, 120, alpha)
            pygame.draw.circle(overlay, color, center, radius)
        
        # Mosaic lines (diagonal cross hatch)
        spacing = 90
        phase = int(self.mosaic_phase * 40)
        mosaic_color = (255, 180, 90, 55)
        for i in range(-self.width, self.width * 2, spacing):
            pygame.draw.line(
                overlay,
                mosaic_color,
                (i + phase, 0),
                (i - self.height + phase, self.height),
                1,
            )
            pygame.draw.line(
                overlay,
                (120, 200, 200, 35),
                (self.width - i - phase, 0),
                (self.width - i + self.height - phase, self.height),
                1,
            )
        
        # Subtle horizon fade
        grad = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.height):
            alpha = int(90 * (1 - y / self.height))
            grad.fill((5, 8, 15, alpha), rect=pygame.Rect(0, y, self.width, 1))
        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_ADD)
        self.screen.blit(grad, (0, 0))

    def _draw_lore_panel(self) -> None:
        """Display a short lore blurb on the main menu."""
        panel_w = 380
        panel_h = 160
        panel_x = self.width // 2 - panel_w - 260
        panel_y = self.height // 2 - 40
        
        surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (8, 10, 18, 180), (0, 0, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(surf, (255, 180, 90, 80), (0, 0, panel_w, panel_h), width=2, border_radius=12)
        self.screen.blit(surf, (panel_x, panel_y))
        
        header = self._font_button.render("Tessera Codex", True, (235, 225, 210))
        self.screen.blit(header, (panel_x + 16, panel_y + 12))
        
        lore_lines = [
            "Monodia was only a line until a Spark knew itself.",
            "Each dimension is a tile in a larger mosaic.",
            "Ascend, but remember: every new axis casts a longer shadow.",
        ]
        y = panel_y + 46
        for line in lore_lines:
            txt = self._font_small.render(line, True, (200, 205, 215))
            self.screen.blit(txt, (panel_x + 16, y))
            y += 26
    
    def _draw_buttons(self) -> None:
        """Draw active buttons."""
        active = self._get_active_buttons()
        if self.minimal_mode:
            if not active:
                return

            pulse = 0.55 + 0.45 * math.sin(self.selection_phase)
            selected_id = active[self.selected_index % len(active)]
            accent_x = self.buttons[selected_id].x - 18
            first_y = self.buttons[active[0]].y
            last_button = self.buttons[active[-1]]
            pygame.draw.line(
                self.screen,
                (88, 99, 114),
                (accent_x, first_y),
                (accent_x, last_button.y + last_button.height),
                1,
            )

            for index, btn_id in enumerate(active):
                btn = self.buttons[btn_id]
                is_selected = index == self.selected_index % len(active)
                rect = pygame.Rect(btn.x, btn.y, btn.width, btn.height)
                slot = self._load_slot_buttons.get(btn_id)

                if is_selected:
                    card = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    highlight_alpha = int(42 + 24 * pulse)
                    pygame.draw.rect(card, (206, 174, 124, highlight_alpha), card.get_rect(), border_radius=14)
                    pygame.draw.rect(card, (218, 196, 156, 110), card.get_rect(), width=1, border_radius=14)
                    self.screen.blit(card, rect.topleft)
                    pygame.draw.line(
                        self.screen,
                        (234, 214, 178),
                        (rect.x - 18, rect.y + 4),
                        (rect.x - 18, rect.bottom - 4),
                        3,
                    )

                number_color = (150, 158, 171) if not is_selected else (250, 232, 205)
                text_color = (193, 199, 208) if not is_selected else (250, 242, 230)
                prefix_text = self._format_slot_prefix(slot) if slot else f"{index + 1:02d}"
                prefix = self._font_meta.render(prefix_text, True, number_color)

                if slot and slot.metadata:
                    slot_label = fit_text(self._font_button, slot.metadata.save_name.upper(), rect.width - 190)
                    label = self._font_button.render(slot_label, True, text_color)
                else:
                    label = self._font_button.render(btn.text.upper(), True, text_color)

                self.screen.blit(prefix, (rect.x + 18, rect.y + 13))
                self.screen.blit(label, (rect.x + 58, rect.y + 9))

                if slot and slot.metadata:
                    meta_text = self._font_meta.render(
                        f"{slot.metadata.current_dimension.upper()}  {slot.playtime_display}",
                        True,
                        (132, 144, 160) if not is_selected else (222, 210, 188),
                    )
                    self.screen.blit(meta_text, (rect.right - meta_text.get_width() - 18, rect.y + 13))

                divider_color = (38, 46, 58) if not is_selected else (110, 98, 78)
                pygame.draw.line(self.screen, divider_color, (rect.x + 18, rect.bottom), (rect.right - 18, rect.bottom), 1)

            blurb = self._menu_blurbs.get(selected_id, "")
            if blurb and self.state != MenuState.LOAD_SAVE:
                blurb_text = self._font_small.render(blurb, True, (162, 173, 188))
                self.screen.blit(
                    blurb_text,
                    (self.buttons[active[0]].x, last_button.y + last_button.height + 28),
                )
            return

        # Glass panel behind main buttons for cohesion
        if self.state == MenuState.MAIN and active and not self.minimal_mode:
            panel_width = 360
            panel_height = len(active) * 65 + 40
            panel_x = self.width // 2 - panel_width // 2
            panel_y = self.height // 2 + 20
            glass = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            pygame.draw.rect(glass, (8, 10, 18, 160), (0, 0, panel_width, panel_height), border_radius=14)
            pygame.draw.rect(glass, (255, 180, 90, 70), (0, 0, panel_width, panel_height), width=2, border_radius=14)
            self.screen.blit(glass, (panel_x, panel_y))
        for btn_id in active:
            if btn_id in self.buttons:
                self.buttons[btn_id].draw(self.screen, self._font_button)
    
    def _draw_settings_panel(self) -> None:
        """Draw settings sliders."""
        panel_x = self.width // 2 - 200
        panel_y = self.height // 2 - 100
        panel_width = 400
        panel_height = 250

        panel_surf = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        if self.minimal_mode:
            pygame.draw.rect(panel_surf, (10, 14, 22, 228), (0, 0, panel_width, panel_height), border_radius=18)
            pygame.draw.rect(panel_surf, (82, 92, 108, 90), (0, 0, panel_width, panel_height), width=1, border_radius=18)
            pygame.draw.line(panel_surf, (208, 181, 136, 180), (24, 26), (108, 26), 2)
        else:
            # Panel background with subtle gold edge
            pygame.draw.rect(panel_surf, (10, 12, 22, 215), (0, 0, panel_width, panel_height), border_radius=12)
            pygame.draw.rect(panel_surf, (255, 190, 110, 90), (0, 0, panel_width, panel_height), width=2, border_radius=12)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        
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
        
        if self.minimal_mode:
            title_surf = self._font_state.render(title.upper(), True, (236, 232, 220))
            self.screen.blit(title_surf, (panel_x + 24, panel_y + 14))
        else:
            title_surf = self._font_button.render(title, True, (235, 225, 210))
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
        label_color = (214, 220, 228) if self.minimal_mode else (230, 225, 215)
        label_surf = self._font_small.render(label, True, label_color)
        self.screen.blit(label_surf, (x, y))
        
        value = self.settings.get(key, 0)
        
        if isinstance(value, bool):
            # Toggle
            toggle_x = x + width - 60
            if self.minimal_mode:
                toggle_color = (192, 167, 128) if value else (54, 63, 78)
            else:
                toggle_color = (120, 200, 140) if value else (70, 80, 100)
            pygame.draw.rect(self.screen, toggle_color, (toggle_x, y, 50, 24), border_radius=12)
            circle_x = toggle_x + 37 if value else toggle_x + 13
            pygame.draw.circle(self.screen, (240, 235, 230), (circle_x, y + 12), 8)
        else:
            # Slider
            slider_x = x + width - 160
            slider_width = 150
            track_color = (34, 42, 54) if self.minimal_mode else (26, 32, 46)
            fill_color = (210, 182, 134) if self.minimal_mode else (255, 180, 90)
            pygame.draw.rect(self.screen, track_color, (slider_x, y + 8, slider_width, 8), border_radius=4)
            fill_width = int(slider_width * value)
            pygame.draw.rect(self.screen, fill_color, (slider_x, y + 8, fill_width, 8), border_radius=4)
            pygame.draw.circle(self.screen, (240, 235, 230), (slider_x + fill_width, y + 12), 8)
            
            # Value text
            value_color = (164, 174, 188) if self.minimal_mode else (190, 200, 210)
            value_text = self._font_small.render(f"{int(value * 100)}%", True, value_color)
            self.screen.blit(value_text, (slider_x + slider_width + 10, y))


def run_tessera_menu() -> Optional[dict]:
    """Run the full Tessera menu experience. Returns data {mode, save_data} or None."""
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
    intro_impulse = ""
    selected_save_data = None
    
    def on_start(mode: str):
        nonlocal selected_mode, running, selected_save_data
        if mode == "new_game":
            menu.stop_music()
            selected_mode = mode
            running = False
        else:
            selected_save_data = menu.consume_selected_save_data()
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
    if selected_mode:
        return {"mode": selected_mode, "intro_impulse": intro_impulse, "save_data": selected_save_data}
    return None
