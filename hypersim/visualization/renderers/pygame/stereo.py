"""Stereoscopic 3D rendering for enhanced depth perception.

Provides side-by-side and anaglyph (red-cyan) stereoscopic rendering
modes for viewing 4D objects with true depth perception.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Tuple, List
import numpy as np
import pygame

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D


class StereoMode(Enum):
    """Stereoscopic rendering modes."""
    SIDE_BY_SIDE = "side_by_side"
    ANAGLYPH_RED_CYAN = "anaglyph_red_cyan"
    ANAGLYPH_GREEN_MAGENTA = "anaglyph_green_magenta"
    CROSS_EYE = "cross_eye"


class StereoRenderer:
    """Stereoscopic renderer for 4D objects.
    
    Renders two views from slightly different positions to create
    a 3D stereoscopic effect when viewed with appropriate glasses
    or by crossing/relaxing eyes.
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        mode: StereoMode = StereoMode.ANAGLYPH_RED_CYAN,
        eye_separation: float = 0.1,
        projection_distance: float = 5.0,
        projection_scale: float = 100.0,
        w_scale_factor: float = 0.3,
    ):
        """Initialize the stereo renderer.
        
        Args:
            screen: Pygame surface to render to
            mode: Stereoscopic mode to use
            eye_separation: Distance between virtual eyes
            projection_distance: 4D projection distance
            projection_scale: Scale for screen projection
            w_scale_factor: W coordinate influence
        """
        self.screen = screen
        self.mode = mode
        self.eye_separation = eye_separation
        self.projection_distance = projection_distance
        self.projection_scale = projection_scale
        self.w_scale_factor = w_scale_factor
        
        self._width, self._height = screen.get_size()
        
        # Create surfaces for each eye
        if mode in (StereoMode.SIDE_BY_SIDE, StereoMode.CROSS_EYE):
            half_width = self._width // 2
            self._left_surface = pygame.Surface((half_width, self._height))
            self._right_surface = pygame.Surface((half_width, self._height))
        else:
            self._left_surface = pygame.Surface((self._width, self._height))
            self._right_surface = pygame.Surface((self._width, self._height))
    
    def _project_vertex(
        self,
        v: np.ndarray,
        eye_offset: float,
        center_x: int,
        center_y: int,
    ) -> Tuple[int, int, float]:
        """Project a 4D vertex to 2D with eye offset.
        
        Args:
            v: 4D vertex
            eye_offset: Horizontal offset for this eye
            center_x: Screen center X
            center_y: Screen center Y
            
        Returns:
            (screen_x, screen_y, depth)
        """
        x, y, z, w = v
        
        # Apply eye offset in X
        x = x - eye_offset
        
        # 4D to 3D projection
        w_scale = 1.0 / (1.0 + abs(w) * self.w_scale_factor)
        
        # 3D to 2D projection with depth
        z_adjusted = z * w_scale
        depth_factor = self.projection_distance / (self.projection_distance - z_adjusted)
        depth_factor = max(0.1, min(10.0, depth_factor))
        
        screen_x = int(x * w_scale * self.projection_scale * depth_factor + center_x)
        screen_y = int(-y * w_scale * self.projection_scale * depth_factor + center_y)
        
        return screen_x, screen_y, z_adjusted
    
    def _render_eye_view(
        self,
        surface: pygame.Surface,
        obj: "Shape4D",
        eye_offset: float,
        color: Tuple[int, int, int],
        line_width: int,
        background: Tuple[int, int, int],
    ) -> None:
        """Render the view for one eye.
        
        Args:
            surface: Surface to render to
            obj: Object to render
            eye_offset: Eye offset from center
            color: Line color
            line_width: Line width
            background: Background color
        """
        surface.fill(background)
        
        width, height = surface.get_size()
        center_x = width // 2
        center_y = height // 2
        
        vertices = obj.get_transformed_vertices()
        
        # Project all vertices
        projected = [
            self._project_vertex(np.array(v), eye_offset, center_x, center_y)
            for v in vertices
        ]
        
        # Sort edges by depth for proper ordering
        edge_depths = []
        for a, b in obj.edges:
            avg_depth = (projected[a][2] + projected[b][2]) / 2
            edge_depths.append((avg_depth, a, b))
        edge_depths.sort(reverse=True)
        
        # Draw edges
        for _, a, b in edge_depths:
            p1 = (projected[a][0], projected[a][1])
            p2 = (projected[b][0], projected[b][1])
            pygame.draw.line(surface, color, p1, p2, line_width)
    
    def render(
        self,
        obj: "Shape4D",
        color: Tuple[int, int, int] = (255, 255, 255),
        line_width: int = 2,
        background: Tuple[int, int, int] = (0, 0, 0),
    ) -> None:
        """Render an object in stereoscopic mode.
        
        Args:
            obj: The Shape4D object to render
            color: Base line color (may be modified by mode)
            line_width: Line width
            background: Background color
        """
        left_offset = -self.eye_separation / 2
        right_offset = self.eye_separation / 2
        
        if self.mode == StereoMode.SIDE_BY_SIDE:
            # Left eye on left, right eye on right
            self._render_eye_view(
                self._left_surface, obj, left_offset, color, line_width, background
            )
            self._render_eye_view(
                self._right_surface, obj, right_offset, color, line_width, background
            )
            
            self.screen.blit(self._left_surface, (0, 0))
            self.screen.blit(self._right_surface, (self._width // 2, 0))
            
        elif self.mode == StereoMode.CROSS_EYE:
            # Right eye on left (for cross-eyed viewing)
            self._render_eye_view(
                self._left_surface, obj, right_offset, color, line_width, background
            )
            self._render_eye_view(
                self._right_surface, obj, left_offset, color, line_width, background
            )
            
            self.screen.blit(self._left_surface, (0, 0))
            self.screen.blit(self._right_surface, (self._width // 2, 0))
            
        elif self.mode == StereoMode.ANAGLYPH_RED_CYAN:
            # Red for left eye, cyan for right eye
            self._render_eye_view(
                self._left_surface, obj, left_offset, (255, 0, 0), line_width, background
            )
            self._render_eye_view(
                self._right_surface, obj, right_offset, (0, 255, 255), line_width, background
            )
            
            # Blend surfaces
            self.screen.fill(background)
            self.screen.blit(self._left_surface, (0, 0), special_flags=pygame.BLEND_ADD)
            self.screen.blit(self._right_surface, (0, 0), special_flags=pygame.BLEND_ADD)
            
        elif self.mode == StereoMode.ANAGLYPH_GREEN_MAGENTA:
            # Green for left eye, magenta for right eye
            self._render_eye_view(
                self._left_surface, obj, left_offset, (0, 255, 0), line_width, background
            )
            self._render_eye_view(
                self._right_surface, obj, right_offset, (255, 0, 255), line_width, background
            )
            
            self.screen.fill(background)
            self.screen.blit(self._left_surface, (0, 0), special_flags=pygame.BLEND_ADD)
            self.screen.blit(self._right_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def set_mode(self, mode: StereoMode) -> None:
        """Change the stereoscopic mode.
        
        Args:
            mode: New stereo mode
        """
        self.mode = mode
        
        # Recreate surfaces if needed
        if mode in (StereoMode.SIDE_BY_SIDE, StereoMode.CROSS_EYE):
            half_width = self._width // 2
            self._left_surface = pygame.Surface((half_width, self._height))
            self._right_surface = pygame.Surface((half_width, self._height))
        else:
            self._left_surface = pygame.Surface((self._width, self._height))
            self._right_surface = pygame.Surface((self._width, self._height))
    
    def set_eye_separation(self, separation: float) -> None:
        """Adjust the eye separation.
        
        Args:
            separation: New eye separation value
        """
        self.eye_separation = max(0.01, min(1.0, separation))
