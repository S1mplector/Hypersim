"""Rendering pipeline for 4D objects.

Provides a structured pipeline for rendering 4D objects with
multiple render modes, effects, and optimizations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Tuple, Optional, Dict, Any, Callable
import numpy as np
import pygame

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D
    from .camera_4d import Camera4D

from hypersim.core.vectorized import (
    batch_compute_edge_depths,
    depth_sort_edges,
)


class RenderMode(Enum):
    """Available rendering modes."""
    WIREFRAME = auto()
    SOLID = auto()
    POINTS = auto()
    DEPTH_COLORED = auto()
    TRANSPARENT = auto()
    HIDDEN_LINE = auto()


class BlendMode(Enum):
    """Blending modes for transparent rendering."""
    NORMAL = auto()
    ADDITIVE = auto()
    MULTIPLY = auto()


@dataclass
class RenderStyle:
    """Style configuration for rendering an object."""
    mode: RenderMode = RenderMode.WIREFRAME
    color: Tuple[int, int, int] = (100, 200, 255)
    line_width: int = 2
    point_size: int = 4
    alpha: int = 255
    
    # Depth coloring
    near_color: Tuple[int, int, int] = (255, 255, 255)
    far_color: Tuple[int, int, int] = (50, 50, 80)
    depth_range: Tuple[float, float] = (-2.0, 2.0)
    
    # Solid mode
    face_color: Tuple[int, int, int] = (60, 120, 180)
    face_alpha: int = 180
    draw_edges: bool = True
    backface_culling: bool = True
    lighting: bool = True
    
    # Effects
    glow: bool = False
    glow_radius: int = 3
    glow_intensity: float = 0.5


@dataclass
class RenderStats:
    """Statistics from the last render pass."""
    vertices_processed: int = 0
    edges_rendered: int = 0
    faces_rendered: int = 0
    objects_rendered: int = 0
    render_time_ms: float = 0.0
    culled_edges: int = 0


class RenderPipeline:
    """Manages the rendering pipeline for 4D objects.
    
    Provides optimized rendering with multiple modes, depth sorting,
    and various visual effects.
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        camera: "Camera4D",
    ):
        """Initialize the render pipeline.
        
        Args:
            screen: Pygame surface to render to
            camera: Camera for projection
        """
        self.screen = screen
        self.camera = camera
        self.stats = RenderStats()
        
        # Default style
        self.default_style = RenderStyle()
        
        # Render queue
        self._render_queue: List[Tuple["Shape4D", RenderStyle]] = []
        
        # Caches
        self._glow_surface: Optional[pygame.Surface] = None
        self._depth_buffer: Optional[np.ndarray] = None
    
    def begin_frame(self) -> None:
        """Begin a new frame, resetting stats and caches."""
        self.stats = RenderStats()
        self._render_queue.clear()
    
    def queue_object(
        self,
        obj: "Shape4D",
        style: Optional[RenderStyle] = None,
    ) -> None:
        """Add an object to the render queue.
        
        Args:
            obj: Object to render
            style: Optional style override
        """
        self._render_queue.append((obj, style or self.default_style))
    
    def render_frame(self) -> RenderStats:
        """Render all queued objects and return statistics."""
        import time
        start_time = time.perf_counter()
        
        # Sort queue by render mode for batching
        # Render opaque objects first, then transparent
        opaque = [(o, s) for o, s in self._render_queue if s.alpha == 255]
        transparent = [(o, s) for o, s in self._render_queue if s.alpha < 255]
        
        for obj, style in opaque:
            self._render_object(obj, style)
        
        for obj, style in transparent:
            self._render_object(obj, style)
        
        self.stats.render_time_ms = (time.perf_counter() - start_time) * 1000
        return self.stats
    
    def render_object(
        self,
        obj: "Shape4D",
        style: Optional[RenderStyle] = None,
    ) -> None:
        """Render a single object immediately.
        
        Args:
            obj: Object to render
            style: Optional style override
        """
        self._render_object(obj, style or self.default_style)
    
    def _render_object(
        self,
        obj: "Shape4D",
        style: RenderStyle,
    ) -> None:
        """Internal object rendering."""
        vertices_4d = obj.get_transformed_vertices()
        vertices_4d = np.array(vertices_4d, dtype=np.float32)
        edges = np.array(obj.edges, dtype=np.int32)
        
        self.stats.vertices_processed += len(vertices_4d)
        self.stats.objects_rendered += 1
        
        # Project vertices
        screen_coords, depths = self.camera.batch_project_4d_to_2d(vertices_4d)
        
        # Dispatch to appropriate render method
        if style.mode == RenderMode.WIREFRAME:
            self._render_wireframe(screen_coords, depths, edges, style)
        elif style.mode == RenderMode.DEPTH_COLORED:
            self._render_depth_colored(screen_coords, depths, edges, style)
        elif style.mode == RenderMode.POINTS:
            self._render_points(screen_coords, depths, style)
        elif style.mode == RenderMode.SOLID:
            self._render_solid(obj, vertices_4d, screen_coords, depths, style)
        elif style.mode == RenderMode.HIDDEN_LINE:
            self._render_hidden_line(screen_coords, depths, edges, style)
        
        # Apply glow effect if enabled
        if style.glow:
            self._apply_glow(style)
    
    def _render_wireframe(
        self,
        screen_coords: np.ndarray,
        depths: np.ndarray,
        edges: np.ndarray,
        style: RenderStyle,
    ) -> None:
        """Render in wireframe mode."""
        # Compute edge depths for sorting
        edge_depths = (depths[edges[:, 0]] + depths[edges[:, 1]]) / 2
        
        # Sort back to front
        sorted_indices = np.argsort(edge_depths)[::-1]
        
        color = (*style.color, style.alpha) if style.alpha < 255 else style.color
        
        for idx in sorted_indices:
            a, b = edges[idx]
            p1 = tuple(screen_coords[a])
            p2 = tuple(screen_coords[b])
            
            # Frustum culling
            if not self._is_edge_visible(p1, p2):
                self.stats.culled_edges += 1
                continue
            
            if style.alpha < 255:
                self._draw_line_alpha(p1, p2, color, style.line_width)
            else:
                pygame.draw.line(self.screen, style.color, p1, p2, style.line_width)
            
            self.stats.edges_rendered += 1
    
    def _render_depth_colored(
        self,
        screen_coords: np.ndarray,
        depths: np.ndarray,
        edges: np.ndarray,
        style: RenderStyle,
    ) -> None:
        """Render with depth-based coloring."""
        min_d, max_d = style.depth_range
        
        # Compute edge depths
        edge_depths = (depths[edges[:, 0]] + depths[edges[:, 1]]) / 2
        
        # Sort back to front
        sorted_indices = np.argsort(edge_depths)[::-1]
        
        for idx in sorted_indices:
            a, b = edges[idx]
            p1 = tuple(screen_coords[a])
            p2 = tuple(screen_coords[b])
            
            if not self._is_edge_visible(p1, p2):
                self.stats.culled_edges += 1
                continue
            
            # Calculate depth-based color
            avg_depth = edge_depths[idx]
            t = np.clip((avg_depth - min_d) / (max_d - min_d), 0, 1)
            
            color = tuple(
                int(style.far_color[i] + (style.near_color[i] - style.far_color[i]) * (1 - t))
                for i in range(3)
            )
            
            # Vary line width by depth
            width = max(1, int(style.line_width * (1 - t * 0.5)))
            
            pygame.draw.line(self.screen, color, p1, p2, width)
            self.stats.edges_rendered += 1
    
    def _render_points(
        self,
        screen_coords: np.ndarray,
        depths: np.ndarray,
        style: RenderStyle,
    ) -> None:
        """Render vertices as points."""
        # Sort by depth
        sorted_indices = np.argsort(depths)[::-1]
        
        for idx in sorted_indices:
            x, y = screen_coords[idx]
            
            if not (0 <= x < self.screen.get_width() and 0 <= y < self.screen.get_height()):
                continue
            
            # Size varies with depth
            t = np.clip((depths[idx] - (-2)) / 4, 0, 1)
            size = max(1, int(style.point_size * (1 - t * 0.5)))
            
            pygame.draw.circle(self.screen, style.color, (x, y), size)
    
    def _render_solid(
        self,
        obj: "Shape4D",
        vertices_4d: np.ndarray,
        screen_coords: np.ndarray,
        depths: np.ndarray,
        style: RenderStyle,
    ) -> None:
        """Render with filled faces."""
        if not hasattr(obj, 'faces') or not obj.faces:
            # Fall back to wireframe
            edges = np.array(obj.edges, dtype=np.int32)
            self._render_wireframe(screen_coords, depths, edges, style)
            return
        
        # Compute face depths and sort
        face_data = []
        for face in obj.faces:
            avg_depth = np.mean([depths[i] for i in face])
            
            # Get 2D points for this face
            points = [tuple(screen_coords[i]) for i in face]
            
            # Compute winding for backface culling
            if style.backface_culling:
                winding = self._compute_winding(points)
                if winding < 0:
                    continue
            
            # Simple lighting based on depth
            color = list(style.face_color)
            if style.lighting:
                intensity = 0.5 + 0.5 * (1 - np.clip((avg_depth + 2) / 4, 0, 1))
                color = [int(c * intensity) for c in color]
            
            face_data.append({
                'depth': avg_depth,
                'points': points,
                'color': tuple(color),
            })
        
        # Sort by depth
        face_data.sort(key=lambda f: f['depth'], reverse=True)
        
        # Draw faces
        for face in face_data:
            if len(face['points']) < 3:
                continue
            
            if style.face_alpha < 255:
                surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
                color_alpha = (*face['color'], style.face_alpha)
                pygame.draw.polygon(surface, color_alpha, face['points'])
                self.screen.blit(surface, (0, 0))
            else:
                pygame.draw.polygon(self.screen, face['color'], face['points'])
            
            if style.draw_edges:
                edge_color = (255, 255, 255) if style.face_alpha < 200 else (200, 200, 200)
                pygame.draw.polygon(self.screen, edge_color, face['points'], 1)
            
            self.stats.faces_rendered += 1
    
    def _render_hidden_line(
        self,
        screen_coords: np.ndarray,
        depths: np.ndarray,
        edges: np.ndarray,
        style: RenderStyle,
    ) -> None:
        """Render with hidden line removal approximation."""
        # Compute edge depths
        edge_depths = (depths[edges[:, 0]] + depths[edges[:, 1]]) / 2
        
        # Sort back to front
        sorted_indices = np.argsort(edge_depths)[::-1]
        
        # Draw back edges dimmer
        mid_depth = np.median(edge_depths)
        
        for idx in sorted_indices:
            a, b = edges[idx]
            p1 = tuple(screen_coords[a])
            p2 = tuple(screen_coords[b])
            
            if not self._is_edge_visible(p1, p2):
                continue
            
            depth = edge_depths[idx]
            if depth > mid_depth:
                # Back edge - draw dimmer and thinner
                color = tuple(c // 3 for c in style.color)
                width = max(1, style.line_width - 1)
            else:
                # Front edge - draw full
                color = style.color
                width = style.line_width
            
            pygame.draw.line(self.screen, color, p1, p2, width)
            self.stats.edges_rendered += 1
    
    def _draw_line_alpha(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
        color: Tuple[int, int, int, int],
        width: int,
    ) -> None:
        """Draw a line with alpha blending."""
        # Create a temporary surface for the line
        min_x = max(0, min(p1[0], p2[0]) - width)
        min_y = max(0, min(p1[1], p2[1]) - width)
        max_x = min(self.screen.get_width(), max(p1[0], p2[0]) + width)
        max_y = min(self.screen.get_height(), max(p1[1], p2[1]) + width)
        
        if max_x <= min_x or max_y <= min_y:
            return
        
        surface = pygame.Surface((max_x - min_x, max_y - min_y), pygame.SRCALPHA)
        offset_p1 = (p1[0] - min_x, p1[1] - min_y)
        offset_p2 = (p2[0] - min_x, p2[1] - min_y)
        pygame.draw.line(surface, color, offset_p1, offset_p2, width)
        self.screen.blit(surface, (min_x, min_y))
    
    def _is_edge_visible(
        self,
        p1: Tuple[int, int],
        p2: Tuple[int, int],
    ) -> bool:
        """Check if an edge is at least partially visible on screen."""
        w, h = self.screen.get_size()
        margin = 50
        
        # Check if both points are outside the same edge
        if p1[0] < -margin and p2[0] < -margin:
            return False
        if p1[0] > w + margin and p2[0] > w + margin:
            return False
        if p1[1] < -margin and p2[1] < -margin:
            return False
        if p1[1] > h + margin and p2[1] > h + margin:
            return False
        
        return True
    
    def _compute_winding(self, points: List[Tuple[int, int]]) -> float:
        """Compute the winding order of a polygon (positive = CCW)."""
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return area / 2.0
    
    def _apply_glow(self, style: RenderStyle) -> None:
        """Apply a glow effect to the current render."""
        # This is a simplified glow - full implementation would use shaders
        # For now, we just draw bright edges slightly larger
        pass
