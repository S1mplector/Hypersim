"""Materials and color gradient system for 4D rendering.

Provides flexible material definitions with support for:
- Solid colors
- Coordinate-based gradients (X, Y, Z, W, radial, depth)
- Procedural patterns
- Animated colors
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Tuple, Optional, Union
import numpy as np
import math


class GradientType(Enum):
    """Types of color gradients."""
    SOLID = auto()
    X_AXIS = auto()
    Y_AXIS = auto()
    Z_AXIS = auto()
    W_AXIS = auto()
    RADIAL = auto()         # Distance from origin
    DEPTH = auto()          # Z after projection
    NORMAL = auto()         # Based on surface normal
    VERTEX_INDEX = auto()   # Based on vertex position in list
    EDGE_LENGTH = auto()    # Based on edge length
    CUSTOM = auto()         # User-defined function


class BlendMode(Enum):
    """Color blending modes."""
    REPLACE = auto()
    ADD = auto()
    MULTIPLY = auto()
    SCREEN = auto()
    OVERLAY = auto()


@dataclass
class ColorStop:
    """A color stop in a gradient."""
    position: float  # 0.0 to 1.0
    color: Tuple[int, int, int]
    
    def __post_init__(self):
        self.position = max(0.0, min(1.0, self.position))


@dataclass
class Gradient:
    """A color gradient with multiple stops."""
    stops: List[ColorStop] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.stops:
            self.stops = [
                ColorStop(0.0, (0, 0, 0)),
                ColorStop(1.0, (255, 255, 255)),
            ]
        self.stops.sort(key=lambda s: s.position)
    
    def sample(self, t: float) -> Tuple[int, int, int]:
        """Sample the gradient at position t (0-1)."""
        t = max(0.0, min(1.0, t))
        
        if len(self.stops) == 1:
            return self.stops[0].color
        
        # Find surrounding stops
        for i in range(len(self.stops) - 1):
            if self.stops[i].position <= t <= self.stops[i + 1].position:
                s1, s2 = self.stops[i], self.stops[i + 1]
                range_ = s2.position - s1.position
                if range_ == 0:
                    return s1.color
                
                local_t = (t - s1.position) / range_
                return tuple(
                    int(s1.color[j] + (s2.color[j] - s1.color[j]) * local_t)
                    for j in range(3)
                )
        
        # Fallback
        return self.stops[-1].color
    
    @classmethod
    def rainbow(cls) -> "Gradient":
        """Create a rainbow gradient."""
        return cls([
            ColorStop(0.0, (255, 0, 0)),
            ColorStop(0.17, (255, 127, 0)),
            ColorStop(0.33, (255, 255, 0)),
            ColorStop(0.5, (0, 255, 0)),
            ColorStop(0.67, (0, 0, 255)),
            ColorStop(0.83, (75, 0, 130)),
            ColorStop(1.0, (148, 0, 211)),
        ])
    
    @classmethod
    def cool_warm(cls) -> "Gradient":
        """Create a cool-to-warm gradient (blue to red)."""
        return cls([
            ColorStop(0.0, (59, 76, 192)),
            ColorStop(0.25, (124, 159, 249)),
            ColorStop(0.5, (247, 247, 247)),
            ColorStop(0.75, (249, 144, 114)),
            ColorStop(1.0, (180, 4, 38)),
        ])
    
    @classmethod
    def viridis(cls) -> "Gradient":
        """Create a viridis-like gradient."""
        return cls([
            ColorStop(0.0, (68, 1, 84)),
            ColorStop(0.25, (59, 82, 139)),
            ColorStop(0.5, (33, 145, 140)),
            ColorStop(0.75, (94, 201, 98)),
            ColorStop(1.0, (253, 231, 37)),
        ])
    
    @classmethod
    def plasma(cls) -> "Gradient":
        """Create a plasma-like gradient."""
        return cls([
            ColorStop(0.0, (13, 8, 135)),
            ColorStop(0.25, (126, 3, 168)),
            ColorStop(0.5, (204, 71, 120)),
            ColorStop(0.75, (248, 149, 64)),
            ColorStop(1.0, (240, 249, 33)),
        ])
    
    @classmethod
    def fire(cls) -> "Gradient":
        """Create a fire gradient."""
        return cls([
            ColorStop(0.0, (0, 0, 0)),
            ColorStop(0.3, (128, 0, 0)),
            ColorStop(0.5, (255, 64, 0)),
            ColorStop(0.7, (255, 200, 0)),
            ColorStop(1.0, (255, 255, 200)),
        ])
    
    @classmethod
    def ocean(cls) -> "Gradient":
        """Create an ocean gradient."""
        return cls([
            ColorStop(0.0, (0, 20, 40)),
            ColorStop(0.3, (0, 60, 100)),
            ColorStop(0.6, (0, 120, 160)),
            ColorStop(0.8, (80, 180, 200)),
            ColorStop(1.0, (180, 240, 255)),
        ])
    
    @classmethod
    def neon(cls) -> "Gradient":
        """Create a neon gradient."""
        return cls([
            ColorStop(0.0, (255, 0, 128)),
            ColorStop(0.5, (0, 255, 255)),
            ColorStop(1.0, (128, 0, 255)),
        ])


@dataclass
class Material:
    """Material definition for 4D object rendering.
    
    Supports solid colors, gradients, and custom color functions.
    """
    
    # Base color (used when gradient_type is SOLID)
    base_color: Tuple[int, int, int] = (100, 200, 255)
    
    # Gradient settings
    gradient_type: GradientType = GradientType.SOLID
    gradient: Optional[Gradient] = None
    
    # Gradient mapping
    gradient_scale: float = 1.0   # Scale factor for coordinate mapping
    gradient_offset: float = 0.0  # Offset for coordinate mapping
    gradient_repeat: bool = False  # Whether to repeat the gradient
    
    # Transparency
    alpha: int = 255
    
    # Line/edge settings
    line_width: int = 2
    line_width_depth_scale: bool = True  # Scale width by depth
    
    # Emission (for glow effects)
    emission: float = 0.0
    emission_color: Optional[Tuple[int, int, int]] = None
    
    # Custom color function: (vertex_4d, vertex_index, time) -> color
    custom_color_func: Optional[Callable[[np.ndarray, int, float], Tuple[int, int, int]]] = None
    
    # Animation
    animate_hue: float = 0.0  # Hue shift per second
    animate_pulse: float = 0.0  # Brightness pulse frequency
    
    def get_vertex_color(
        self,
        vertex: np.ndarray,
        vertex_index: int = 0,
        depth: float = 0.0,
        time: float = 0.0,
        normal: Optional[np.ndarray] = None,
    ) -> Tuple[int, int, int]:
        """Calculate color for a vertex.
        
        Args:
            vertex: 4D vertex position
            vertex_index: Index of vertex in mesh
            depth: Projected depth value
            time: Current time for animations
            normal: Surface normal if available
            
        Returns:
            RGB color tuple
        """
        if self.gradient_type == GradientType.SOLID:
            color = self.base_color
        elif self.gradient_type == GradientType.CUSTOM and self.custom_color_func:
            color = self.custom_color_func(vertex, vertex_index, time)
        elif self.gradient is not None:
            t = self._calculate_gradient_t(vertex, vertex_index, depth, normal)
            color = self.gradient.sample(t)
        else:
            color = self.base_color
        
        # Apply animations
        if self.animate_hue != 0 or self.animate_pulse != 0:
            color = self._apply_animation(color, time)
        
        return color
    
    def _calculate_gradient_t(
        self,
        vertex: np.ndarray,
        vertex_index: int,
        depth: float,
        normal: Optional[np.ndarray],
    ) -> float:
        """Calculate gradient parameter t based on gradient type."""
        if self.gradient_type == GradientType.X_AXIS:
            t = vertex[0]
        elif self.gradient_type == GradientType.Y_AXIS:
            t = vertex[1]
        elif self.gradient_type == GradientType.Z_AXIS:
            t = vertex[2]
        elif self.gradient_type == GradientType.W_AXIS:
            t = vertex[3]
        elif self.gradient_type == GradientType.RADIAL:
            t = np.linalg.norm(vertex)
        elif self.gradient_type == GradientType.DEPTH:
            t = depth
        elif self.gradient_type == GradientType.VERTEX_INDEX:
            t = vertex_index / 100.0  # Normalize by assumed max
        elif self.gradient_type == GradientType.NORMAL and normal is not None:
            # Use normal's angle with view direction
            t = (normal[2] + 1) / 2  # Map -1..1 to 0..1
        else:
            t = 0.5
        
        # Apply scale and offset
        t = t * self.gradient_scale + self.gradient_offset
        
        # Normalize to 0-1
        if self.gradient_repeat:
            t = t % 1.0
        else:
            t = max(0.0, min(1.0, (t + 1) / 2))  # Map typical -1..1 to 0..1
        
        return t
    
    def _apply_animation(
        self,
        color: Tuple[int, int, int],
        time: float,
    ) -> Tuple[int, int, int]:
        """Apply animation effects to color."""
        r, g, b = color
        
        # Hue shift
        if self.animate_hue != 0:
            h, s, v = self._rgb_to_hsv(r, g, b)
            h = (h + time * self.animate_hue) % 1.0
            r, g, b = self._hsv_to_rgb(h, s, v)
        
        # Pulse effect
        if self.animate_pulse != 0:
            pulse = 0.5 + 0.5 * math.sin(time * self.animate_pulse * 2 * math.pi)
            factor = 0.7 + 0.3 * pulse
            r = int(min(255, r * factor))
            g = int(min(255, g * factor))
            b = int(min(255, b * factor))
        
        return (r, g, b)
    
    @staticmethod
    def _rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]:
        """Convert RGB to HSV."""
        r, g, b = r / 255, g / 255, b / 255
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        diff = max_c - min_c
        
        if diff == 0:
            h = 0
        elif max_c == r:
            h = ((g - b) / diff) % 6
        elif max_c == g:
            h = (b - r) / diff + 2
        else:
            h = (r - g) / diff + 4
        h /= 6
        
        s = 0 if max_c == 0 else diff / max_c
        v = max_c
        
        return h, s, v
    
    @staticmethod
    def _hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB."""
        if s == 0:
            r = g = b = int(v * 255)
            return r, g, b
        
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        i %= 6
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return int(r * 255), int(g * 255), int(b * 255)
    
    def get_edge_color(
        self,
        v1: np.ndarray,
        v2: np.ndarray,
        v1_idx: int,
        v2_idx: int,
        depth: float,
        time: float = 0.0,
    ) -> Tuple[int, int, int]:
        """Get color for an edge (average of vertex colors)."""
        c1 = self.get_vertex_color(v1, v1_idx, depth, time)
        c2 = self.get_vertex_color(v2, v2_idx, depth, time)
        
        return tuple((c1[i] + c2[i]) // 2 for i in range(3))
    
    def get_line_width(self, depth: float) -> int:
        """Get line width, optionally scaled by depth."""
        if not self.line_width_depth_scale:
            return self.line_width
        
        # Scale: near objects thicker, far objects thinner
        scale = 1.0 - max(0, min(1, (depth + 2) / 4)) * 0.5
        return max(1, int(self.line_width * scale))


# Preset materials
class Materials:
    """Collection of preset materials."""
    
    @staticmethod
    def solid(color: Tuple[int, int, int], line_width: int = 2) -> Material:
        """Create a solid color material."""
        return Material(base_color=color, line_width=line_width)
    
    @staticmethod
    def rainbow() -> Material:
        """Create a rainbow gradient material."""
        return Material(
            gradient_type=GradientType.W_AXIS,
            gradient=Gradient.rainbow(),
            gradient_scale=0.5,
        )
    
    @staticmethod
    def depth_fade(near_color: Tuple[int, int, int], far_color: Tuple[int, int, int]) -> Material:
        """Create a depth-based fade material."""
        return Material(
            gradient_type=GradientType.DEPTH,
            gradient=Gradient([
                ColorStop(0.0, far_color),
                ColorStop(1.0, near_color),
            ]),
        )
    
    @staticmethod
    def radial_gradient(inner: Tuple[int, int, int], outer: Tuple[int, int, int]) -> Material:
        """Create a radial gradient from center."""
        return Material(
            gradient_type=GradientType.RADIAL,
            gradient=Gradient([
                ColorStop(0.0, inner),
                ColorStop(1.0, outer),
            ]),
            gradient_scale=0.5,
        )
    
    @staticmethod
    def w_gradient(neg_w: Tuple[int, int, int], pos_w: Tuple[int, int, int]) -> Material:
        """Create a gradient along the W axis."""
        return Material(
            gradient_type=GradientType.W_AXIS,
            gradient=Gradient([
                ColorStop(0.0, neg_w),
                ColorStop(1.0, pos_w),
            ]),
        )
    
    @staticmethod
    def animated_rainbow(speed: float = 0.5) -> Material:
        """Create an animated rainbow material."""
        return Material(
            gradient_type=GradientType.RADIAL,
            gradient=Gradient.rainbow(),
            animate_hue=speed,
        )
    
    @staticmethod
    def pulsing(color: Tuple[int, int, int], frequency: float = 1.0) -> Material:
        """Create a pulsing material."""
        return Material(
            base_color=color,
            animate_pulse=frequency,
        )
    
    @staticmethod
    def fire() -> Material:
        """Create a fire-colored material."""
        return Material(
            gradient_type=GradientType.Y_AXIS,
            gradient=Gradient.fire(),
        )
    
    @staticmethod
    def ocean() -> Material:
        """Create an ocean-colored material."""
        return Material(
            gradient_type=GradientType.DEPTH,
            gradient=Gradient.ocean(),
        )
    
    @staticmethod
    def plasma() -> Material:
        """Create a plasma-colored material."""
        return Material(
            gradient_type=GradientType.W_AXIS,
            gradient=Gradient.plasma(),
        )
    
    @staticmethod
    def neon_glow(color: Tuple[int, int, int] = (0, 255, 255)) -> Material:
        """Create a neon glow material."""
        return Material(
            base_color=color,
            emission=0.5,
            emission_color=color,
            line_width=3,
        )
