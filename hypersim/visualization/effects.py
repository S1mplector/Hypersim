"""Visual effects for 4D rendering.

Provides post-processing effects including motion blur, glow,
bloom, and other visual enhancements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional, Deque
from collections import deque
import numpy as np
import pygame


@dataclass
class MotionBlurConfig:
    """Configuration for motion blur effect."""
    samples: int = 8          # Number of previous frames to blend
    decay: float = 0.7        # Decay factor per frame (0-1)
    enabled: bool = True


class MotionBlur:
    """Motion blur effect using frame accumulation.
    
    Blends multiple previous frames together with decay
    to create a motion blur effect.
    """
    
    def __init__(self, config: Optional[MotionBlurConfig] = None):
        self.config = config or MotionBlurConfig()
        self._frame_buffer: Deque[pygame.Surface] = deque(maxlen=self.config.samples)
        self._result_surface: Optional[pygame.Surface] = None
    
    def add_frame(self, surface: pygame.Surface) -> None:
        """Add a frame to the blur buffer."""
        if not self.config.enabled:
            return
        
        # Store a copy of the surface
        frame_copy = surface.copy()
        self._frame_buffer.append(frame_copy)
    
    def apply(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply motion blur effect to the current frame.
        
        Args:
            surface: Current frame surface
            
        Returns:
            Blurred surface
        """
        if not self.config.enabled or len(self._frame_buffer) < 2:
            return surface
        
        # Create result surface if needed
        if (self._result_surface is None or 
            self._result_surface.get_size() != surface.get_size()):
            self._result_surface = pygame.Surface(
                surface.get_size(), pygame.SRCALPHA
            )
        
        self._result_surface.fill((0, 0, 0, 0))
        
        # Blend frames with decay
        total_weight = 0.0
        weight = 1.0
        
        # Current frame has highest weight
        frames = list(self._frame_buffer)
        frames.append(surface)
        
        for i, frame in enumerate(reversed(frames)):
            alpha = int(255 * weight / (i + 1))
            frame.set_alpha(alpha)
            self._result_surface.blit(frame, (0, 0))
            total_weight += weight
            weight *= self.config.decay
        
        # Blit result onto original surface
        result = surface.copy()
        result.blit(self._result_surface, (0, 0))
        
        return result
    
    def clear(self) -> None:
        """Clear the frame buffer."""
        self._frame_buffer.clear()
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable motion blur."""
        self.config.enabled = enabled
        if not enabled:
            self.clear()


@dataclass 
class GlowConfig:
    """Configuration for glow effect."""
    radius: int = 5
    intensity: float = 0.5
    color: Optional[Tuple[int, int, int]] = None  # None = use source color
    enabled: bool = True


class Glow:
    """Glow/bloom effect for bright areas.
    
    Creates a soft glow around bright pixels.
    """
    
    def __init__(self, config: Optional[GlowConfig] = None):
        self.config = config or GlowConfig()
        self._blur_surface: Optional[pygame.Surface] = None
    
    def apply(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply glow effect.
        
        Args:
            surface: Source surface
            
        Returns:
            Surface with glow applied
        """
        if not self.config.enabled or self.config.radius <= 0:
            return surface
        
        width, height = surface.get_size()
        
        # Create blur surface
        if (self._blur_surface is None or 
            self._blur_surface.get_size() != (width, height)):
            self._blur_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Simple box blur approximation
        # For better results, would use Gaussian blur
        self._blur_surface.fill((0, 0, 0, 0))
        
        # Downsample, blur, upsample approach
        scale = max(1, self.config.radius // 2)
        small_size = (width // scale, height // scale)
        
        if small_size[0] > 0 and small_size[1] > 0:
            # Downscale
            small = pygame.transform.smoothscale(surface, small_size)
            
            # Upscale (creates blur effect)
            blurred = pygame.transform.smoothscale(small, (width, height))
            
            # Tint if color specified
            if self.config.color:
                tint = pygame.Surface((width, height), pygame.SRCALPHA)
                tint.fill((*self.config.color, int(255 * self.config.intensity)))
                blurred.blit(tint, (0, 0), special_flags=pygame.BLEND_MULT)
            
            # Set intensity
            blurred.set_alpha(int(255 * self.config.intensity))
            
            # Combine with original using additive blend
            result = surface.copy()
            result.blit(blurred, (0, 0), special_flags=pygame.BLEND_ADD)
            
            return result
        
        return surface


@dataclass
class LightSource:
    """A light source in 4D space."""
    position: np.ndarray  # 4D position
    color: Tuple[int, int, int] = (255, 255, 255)
    intensity: float = 1.0
    falloff: float = 1.0  # Distance falloff exponent
    ambient: float = 0.2  # Ambient contribution


class Lighting:
    """4D lighting system.
    
    Calculates lighting for vertices based on position
    relative to light sources.
    """
    
    def __init__(self):
        self.lights: List[LightSource] = []
        self.ambient_color: Tuple[int, int, int] = (30, 30, 40)
        self.ambient_intensity: float = 0.3
    
    def add_light(self, light: LightSource) -> None:
        """Add a light source."""
        self.lights.append(light)
    
    def remove_light(self, light: LightSource) -> None:
        """Remove a light source."""
        if light in self.lights:
            self.lights.remove(light)
    
    def clear_lights(self) -> None:
        """Remove all lights."""
        self.lights.clear()
    
    def calculate_vertex_lighting(
        self,
        vertex: np.ndarray,
        normal: Optional[np.ndarray] = None,
        base_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Tuple[int, int, int]:
        """Calculate lit color for a vertex.
        
        Args:
            vertex: 4D vertex position
            normal: Surface normal (optional)
            base_color: Base material color
            
        Returns:
            Lit RGB color
        """
        if not self.lights:
            return base_color
        
        # Start with ambient
        total_r = self.ambient_color[0] * self.ambient_intensity
        total_g = self.ambient_color[1] * self.ambient_intensity
        total_b = self.ambient_color[2] * self.ambient_intensity
        
        for light in self.lights:
            # Distance to light
            diff = light.position - vertex
            distance = np.linalg.norm(diff)
            
            if distance < 0.001:
                distance = 0.001
            
            # Attenuation
            attenuation = light.intensity / (1 + light.falloff * distance)
            
            # Directional factor (if normal provided)
            if normal is not None:
                direction = diff / distance
                dot = max(0, np.dot(normal[:3], direction[:3]))
                attenuation *= dot
            
            # Add light contribution
            total_r += light.color[0] * attenuation
            total_g += light.color[1] * attenuation
            total_b += light.color[2] * attenuation
        
        # Apply to base color
        r = int(min(255, base_color[0] * total_r / 255))
        g = int(min(255, base_color[1] * total_g / 255))
        b = int(min(255, base_color[2] * total_b / 255))
        
        return (r, g, b)
    
    def calculate_edge_lighting(
        self,
        v1: np.ndarray,
        v2: np.ndarray,
        base_color: Tuple[int, int, int] = (255, 255, 255),
    ) -> Tuple[int, int, int]:
        """Calculate lighting for an edge (average of endpoints)."""
        c1 = self.calculate_vertex_lighting(v1, None, base_color)
        c2 = self.calculate_vertex_lighting(v2, None, base_color)
        
        return tuple((c1[i] + c2[i]) // 2 for i in range(3))


@dataclass
class TrailConfig:
    """Configuration for object trails."""
    length: int = 30       # Number of trail points
    width_start: int = 3   # Starting width
    width_end: int = 1     # Ending width
    color_start: Tuple[int, int, int] = (255, 255, 255)
    color_end: Tuple[int, int, int] = (50, 50, 80)
    fade_alpha: bool = True
    enabled: bool = True


class Trail:
    """Renders a trail behind a moving point.
    
    Useful for visualizing motion paths in 4D.
    """
    
    def __init__(self, config: Optional[TrailConfig] = None):
        self.config = config or TrailConfig()
        self._positions: Deque[np.ndarray] = deque(maxlen=self.config.length)
    
    def add_position(self, position: np.ndarray) -> None:
        """Add a position to the trail."""
        if self.config.enabled:
            self._positions.append(position.copy())
    
    def render(
        self,
        surface: pygame.Surface,
        project_func,  # Function to project 4D -> 2D
    ) -> None:
        """Render the trail.
        
        Args:
            surface: Surface to draw on
            project_func: Function that takes 4D point and returns (x, y)
        """
        if not self.config.enabled or len(self._positions) < 2:
            return
        
        positions = list(self._positions)
        num_points = len(positions)
        
        for i in range(num_points - 1):
            t = i / (num_points - 1)
            
            # Interpolate color
            color = tuple(
                int(self.config.color_start[j] + 
                    (self.config.color_end[j] - self.config.color_start[j]) * t)
                for j in range(3)
            )
            
            # Interpolate width
            width = int(self.config.width_start + 
                       (self.config.width_end - self.config.width_start) * t)
            width = max(1, width)
            
            # Project positions
            try:
                p1 = project_func(positions[i])
                p2 = project_func(positions[i + 1])
                
                if self.config.fade_alpha:
                    alpha = int(255 * (1 - t))
                    s = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                    pygame.draw.line(s, (*color, alpha), p1[:2], p2[:2], width)
                    surface.blit(s, (0, 0))
                else:
                    pygame.draw.line(surface, color, p1[:2], p2[:2], width)
            except (IndexError, TypeError):
                continue
    
    def clear(self) -> None:
        """Clear the trail."""
        self._positions.clear()


class EffectsManager:
    """Manages multiple visual effects."""
    
    def __init__(self):
        self.motion_blur = MotionBlur()
        self.glow = Glow()
        self.lighting = Lighting()
        self.trails: List[Trail] = []
    
    def add_trail(self, config: Optional[TrailConfig] = None) -> Trail:
        """Create and add a new trail."""
        trail = Trail(config)
        self.trails.append(trail)
        return trail
    
    def apply_all(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply all enabled effects."""
        result = surface
        
        # Motion blur
        if self.motion_blur.config.enabled:
            result = self.motion_blur.apply(result)
        
        # Glow
        if self.glow.config.enabled:
            result = self.glow.apply(result)
        
        return result
    
    def update(self, surface: pygame.Surface) -> None:
        """Update effect state with new frame."""
        self.motion_blur.add_frame(surface)
    
    def clear(self) -> None:
        """Clear all effect state."""
        self.motion_blur.clear()
        for trail in self.trails:
            trail.clear()
