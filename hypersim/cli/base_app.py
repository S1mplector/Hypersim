"""Base classes for HyperSim Pygame applications.

This module provides shared functionality for all Pygame-based apps:
- Common initialization and cleanup
- Shared rendering utilities
- Input handling framework
- Theme and styling constants
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List, Any

import numpy as np
import pygame


# =============================================================================
# THEME / COLORS
# =============================================================================

@dataclass(frozen=True)
class Theme:
    """Application color theme."""
    # Backgrounds
    bg_dark: Tuple[int, int, int] = (8, 10, 18)
    bg_panel: Tuple[int, int, int] = (18, 22, 32)
    bg_card: Tuple[int, int, int] = (25, 30, 45)
    bg_hover: Tuple[int, int, int] = (35, 42, 62)
    bg_active: Tuple[int, int, int] = (45, 55, 80)
    
    # Text
    text_primary: Tuple[int, int, int] = (230, 235, 245)
    text_secondary: Tuple[int, int, int] = (160, 165, 180)
    text_muted: Tuple[int, int, int] = (100, 105, 120)
    
    # Accents
    accent_blue: Tuple[int, int, int] = (80, 160, 255)
    accent_purple: Tuple[int, int, int] = (160, 100, 255)
    accent_cyan: Tuple[int, int, int] = (80, 220, 220)
    accent_orange: Tuple[int, int, int] = (255, 160, 80)
    accent_green: Tuple[int, int, int] = (80, 220, 140)
    accent_red: Tuple[int, int, int] = (255, 100, 100)
    
    # Borders
    border: Tuple[int, int, int] = (50, 55, 70)
    border_light: Tuple[int, int, int] = (70, 75, 95)


# Default theme instance
THEME = Theme()


# =============================================================================
# FONTS
# =============================================================================

class Fonts:
    """Lazy-loaded font collection."""
    
    _instance: Optional['Fonts'] = None
    
    def __init__(self):
        self._title: Optional[pygame.font.Font] = None
        self._subtitle: Optional[pygame.font.Font] = None
        self._body: Optional[pygame.font.Font] = None
        self._small: Optional[pygame.font.Font] = None
        self._mono: Optional[pygame.font.Font] = None
    
    @classmethod
    def get(cls) -> 'Fonts':
        """Get the singleton Fonts instance."""
        if cls._instance is None:
            cls._instance = Fonts()
        return cls._instance
    
    @property
    def title(self) -> pygame.font.Font:
        if self._title is None:
            self._title = pygame.font.SysFont("Arial", 24, bold=True)
        return self._title
    
    @property
    def subtitle(self) -> pygame.font.Font:
        if self._subtitle is None:
            self._subtitle = pygame.font.SysFont("Arial", 18)
        return self._subtitle
    
    @property
    def body(self) -> pygame.font.Font:
        if self._body is None:
            self._body = pygame.font.SysFont("Arial", 16)
        return self._body
    
    @property
    def small(self) -> pygame.font.Font:
        if self._small is None:
            self._small = pygame.font.SysFont("Arial", 14)
        return self._small
    
    @property
    def mono(self) -> pygame.font.Font:
        if self._mono is None:
            self._mono = pygame.font.SysFont("Consolas", 14)
        return self._mono


# =============================================================================
# 4D CAMERA (shared between apps)
# =============================================================================

@dataclass
class Camera4D:
    """A first-person camera in 4D space.
    
    Uses FPS-style yaw/pitch for 3D look, plus additional angles for 4D rotation.
    """
    # Position
    position: np.ndarray = None
    
    # Standard FPS angles
    yaw: float = 0.0    # XZ rotation (left/right)
    pitch: float = 0.0  # YZ rotation (up/down)
    
    # 4D rotation angles
    roll_4d: float = 0.0   # XW rotation
    pitch_4d: float = 0.0  # YW rotation
    
    # Settings
    move_speed: float = 5.0
    look_sensitivity: float = 0.002
    fov: float = 2.0
    
    def __post_init__(self):
        if self.position is None:
            self.position = np.array([0.0, 0.0, -8.0, 0.0], dtype=np.float64)
    
    def get_rotation_matrix(self) -> np.ndarray:
        """Get the combined view rotation matrix."""
        from hypersim.core import rotation_xz, rotation_yz, rotation_xw, rotation_yw
        m = np.eye(4, dtype=np.float64)
        m = rotation_xz(self.yaw) @ m
        m = rotation_yz(self.pitch) @ m
        m = rotation_xw(self.roll_4d) @ m
        m = rotation_yw(self.pitch_4d) @ m
        return m
    
    def get_forward(self) -> np.ndarray:
        """Get forward direction vector."""
        from hypersim.core import rotation_xz, rotation_yz
        forward = np.array([0.0, 0.0, 1.0, 0.0])
        m = rotation_xz(self.yaw) @ rotation_yz(self.pitch)
        return m @ forward
    
    def get_right(self) -> np.ndarray:
        """Get right direction vector."""
        from hypersim.core import rotation_xz
        right = np.array([1.0, 0.0, 0.0, 0.0])
        return rotation_xz(self.yaw) @ right
    
    def get_up(self) -> np.ndarray:
        """Get up direction vector."""
        return np.array([0.0, 1.0, 0.0, 0.0])
    
    def get_ana(self) -> np.ndarray:
        """Get ana direction (into 4D)."""
        from hypersim.core import rotation_xw, rotation_yw
        ana = np.array([0.0, 0.0, 0.0, 1.0])
        m = rotation_xw(self.roll_4d) @ rotation_yw(self.pitch_4d)
        return m @ ana
    
    def move(self, forward: float, right: float, up: float, ana: float, dt: float) -> None:
        """Move camera relative to its orientation."""
        velocity = np.zeros(4, dtype=np.float64)
        if forward != 0:
            velocity += self.get_forward() * forward
        if right != 0:
            velocity += self.get_right() * right
        if up != 0:
            velocity += self.get_up() * up
        if ana != 0:
            velocity += self.get_ana() * ana
        
        if np.any(velocity != 0):
            velocity = velocity / np.linalg.norm(velocity)
            self.position += velocity * self.move_speed * dt
    
    def look(self, dx: float, dy: float) -> None:
        """Rotate camera based on mouse movement."""
        self.yaw -= dx * self.look_sensitivity
        self.pitch -= dy * self.look_sensitivity
        self.pitch = np.clip(self.pitch, -np.pi/2 + 0.1, np.pi/2 - 0.1)
    
    def project(self, point: np.ndarray, screen_w: int, screen_h: int) -> Optional[Tuple[int, int, float]]:
        """Project a 4D point to screen coordinates.
        
        Returns (x, y, depth) or None if behind camera.
        """
        # Transform to camera space
        relative = point - self.position
        view_matrix = self.get_rotation_matrix().T
        cam_point = view_matrix @ relative
        
        x, y, z, w = cam_point
        
        # 4D perspective
        w_depth = w + 3.0
        if w_depth < 0.1:
            return None
        scale_4d = self.fov / w_depth
        x3, y3, z3 = x * scale_4d, y * scale_4d, z * scale_4d
        
        # 3D perspective
        z_depth = z3 + 5.0
        if z_depth < 0.1:
            return None
        scale_3d = self.fov / z_depth
        
        screen_x = int(screen_w / 2 + x3 * scale_3d * 200)
        screen_y = int(screen_h / 2 - y3 * scale_3d * 200)
        depth = w_depth + z_depth * 0.1
        
        return (screen_x, screen_y, depth)


# =============================================================================
# BASE APPLICATION CLASS
# =============================================================================

class BaseApp(ABC):
    """Abstract base class for Pygame applications."""
    
    def __init__(self, width: int = 1400, height: int = 900, title: str = "HyperSim"):
        self.width = width
        self.height = height
        self.title = title
        
        # Pygame state
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.running = True
        
        # Input state
        self.keys_held: Dict[int, bool] = {}
        self.mouse_captured = False
    
    def init_pygame(self) -> None:
        """Initialize Pygame and create window."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
    
    def init_from_existing(self, screen: pygame.Surface, clock: pygame.time.Clock) -> None:
        """Initialize using existing Pygame context (for embedding)."""
        self.screen = screen
        self.clock = clock
        self.width = screen.get_width()
        self.height = screen.get_height()
        pygame.display.set_caption(self.title)
    
    def capture_mouse(self) -> None:
        """Capture mouse for FPS-style control."""
        self.mouse_captured = True
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)
        pygame.mouse.set_pos(self.width // 2, self.height // 2)
    
    def release_mouse(self) -> None:
        """Release mouse capture."""
        self.mouse_captured = False
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
    
    @abstractmethod
    def handle_events(self) -> bool:
        """Handle input events. Return False to quit."""
        pass
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """Update application state."""
        pass
    
    @abstractmethod
    def render(self) -> None:
        """Render the application."""
        pass
    
    def step(self, dt: float, flip: bool = True) -> bool:
        """Process a single frame. Returns False when the app requests exit."""
        if not self.handle_events():
            self.running = False
            return False
        
        self.update(dt)
        self.render()
        
        if flip:
            pygame.display.flip()
        
        return True
    
    def run(self) -> None:
        """Main application loop."""
        if self.screen is None:
            self.init_pygame()
        elif self.clock is None:
            self.clock = pygame.time.Clock()
        
        self.running = True
        
        last_time = pygame.time.get_ticks() / 1000.0
        
        while self.running:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_time, 0.1)
            last_time = now
            
            if not self.step(dt):
                break
            self.clock.tick(60)
        
        pygame.quit()
    
    # Utility methods
    def draw_text(self, text: str, pos: Tuple[int, int], 
                  color: Tuple[int, int, int] = None, 
                  font: pygame.font.Font = None) -> pygame.Rect:
        """Draw text and return its rect."""
        if color is None:
            color = THEME.text_primary
        if font is None:
            font = Fonts.get().body
        surf = font.render(text, True, color)
        rect = self.screen.blit(surf, pos)
        return rect
    
    def draw_panel(self, rect: pygame.Rect, 
                   bg_color: Tuple[int, int, int] = None,
                   border_color: Tuple[int, int, int] = None,
                   border_radius: int = 8, 
                   alpha: int = 255) -> None:
        """Draw a panel with optional transparency."""
        if bg_color is None:
            bg_color = THEME.bg_panel
        
        if alpha < 255:
            surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            surf.fill((*bg_color, alpha))
            self.screen.blit(surf, rect.topleft)
        else:
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=border_radius)
        
        if border_color:
            pygame.draw.rect(self.screen, border_color, rect, width=1, border_radius=border_radius)
    
    def draw_line_4d(self, camera: Camera4D, p1: np.ndarray, p2: np.ndarray,
                     color: Tuple[int, int, int], width: int = 1) -> None:
        """Draw a line between two 4D points."""
        proj1 = camera.project(p1, self.width, self.height)
        proj2 = camera.project(p2, self.width, self.height)
        
        if proj1 and proj2:
            # Depth-based fading
            avg_depth = (proj1[2] + proj2[2]) / 2
            alpha = max(0.2, min(1.0, 3.0 / (1 + avg_depth * 0.2)))
            faded = tuple(int(c * alpha) for c in color)
            pygame.draw.line(self.screen, faded, (proj1[0], proj1[1]), (proj2[0], proj2[1]), width)
    
    def draw_crosshair(self, color: Tuple[int, int, int] = None) -> None:
        """Draw a center crosshair."""
        if color is None:
            color = (100, 100, 100) if self.mouse_captured else (60, 60, 60)
        
        cx, cy = self.width // 2, self.height // 2
        size, gap = 12, 4
        
        pygame.draw.line(self.screen, color, (cx - size, cy), (cx - gap, cy), 2)
        pygame.draw.line(self.screen, color, (cx + gap, cy), (cx + size, cy), 2)
        pygame.draw.line(self.screen, color, (cx, cy - size), (cx, cy - gap), 2)
        pygame.draw.line(self.screen, color, (cx, cy + gap), (cx, cy + size), 2)
