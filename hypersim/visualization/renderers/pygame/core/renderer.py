"""Main renderer implementation for the Pygame backend.

This module provides the PygameRenderer class which is the main entry point
for rendering 3D/4D graphics using Pygame.
"""

from __future__ import annotations

import pygame
import numpy as np
from typing import Any, List, Optional, Sequence

from hypersim.core.math_4d import Vector4D
from ..graphics.color import Color
from ..graphics.scene.scene import Scene, Renderable
from .camera import Camera
from ..input.handlers import InputHandler

__all__ = ["PygameRenderer"]


class PygameRenderer:
    """Main renderer class for 3D/4D graphics using Pygame.
    
    This class manages the rendering window, camera, scene, and input handling.
    It provides a simple interface for creating interactive 3D/4D visualizations.
    """
    
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "4D Renderer",
        background_color: Optional[Color] = None,
        distance: float = 5.0,
        auto_spin: bool = True,
        spin_rates: Optional[dict[str, float]] = None,
    ) -> None:
        """Initialize the Pygame renderer.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
            background_color: Background color (default: black)
            distance: Distance to the near clipping plane
        """
        if background_color is None:
            background_color = Color(0, 0, 0)
        
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
        
        # Set up camera
        self.camera = Camera(width, height, distance=distance)
        
        # Set up input handling
        self.input_handler = InputHandler(self.camera)
        
        # Set up scene
        self.scene = Scene(background_color)
        self.scene.zbuffer = np.ones((width, height), dtype=np.float32) * float("inf")
        
        # Performance metrics
        self.clock = pygame.time.Clock()
        self.fps = 0.0
        self.frame_count = 0
        self.last_fps_update = pygame.time.get_ticks()
        self._dt_smooth = 1.0 / 60.0
        self.auto_spin = auto_spin
        self.spin_rates = spin_rates or {
            "xy": 0.4,
            "xw": 0.6,
            "yw": 0.5,
            "zw": 0.3,
        }
    
    def clear(self) -> None:
        """Clear the screen and z-buffer."""
        self.screen.fill(self.scene.background_color.to_tuple())
        if self.scene.zbuffer is not None:
            self.scene.zbuffer.fill(float("inf"))
    
    def add_object(self, obj: Renderable) -> None:
        """Add a renderable object to the scene.
        
        Args:
            obj: Object to add (must implement the Renderable protocol)
        """
        self.scene.add_object(obj)
    
    def remove_object(self, obj: Renderable) -> None:
        """Remove a renderable object from the scene.
        
        Args:
            obj: Object to remove
        """
        self.scene.remove_object(obj)
    
    def clear_scene(self) -> None:
        """Remove all objects from the scene."""
        self.scene.clear()
    
    def update(self, dt: float) -> None:
        """Update the scene and all objects.
        
        Args:
            dt: Time since last update in seconds
        """
        safe_dt = min(dt, 0.25)  # Avoid huge jumps after pauses
        # Low-pass filter to smooth jittery frame times
        self._dt_smooth = 0.2 * safe_dt + 0.8 * self._dt_smooth
        smooth_dt = min(self._dt_smooth, 0.05)

        self.scene.update(smooth_dt)

        # Update FPS counter
        self.frame_count += 1
        now = pygame.time.get_ticks()
        if now - self.last_fps_update > 1000:  # Update FPS every second
            self.fps = self.frame_count * 1000.0 / (now - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = now
        # Optional auto-spin of objects (unless explicitly disabled per-object)
        if self.auto_spin:
            for obj in self.scene.objects:
                if not hasattr(obj, "rotate"):
                    continue
                if getattr(obj, "auto_spin_enabled", True) is False:
                    continue
                rates = getattr(obj, "spin_rates", self.spin_rates)
                try:
                    obj.rotate(
                        xy=rates.get("xy", 0.0) * smooth_dt,
                        xw=rates.get("xw", 0.0) * smooth_dt,
                        yw=rates.get("yw", 0.0) * smooth_dt,
                        zw=rates.get("zw", 0.0) * smooth_dt,
                    )
                except Exception:
                    continue
    
    def render(self) -> None:
        """Render the current scene."""
        self.scene.render(self)
        pygame.display.flip()
    
    def run(self, target_fps: int = 60) -> None:
        """Run the main render loop.
        
        Args:
            target_fps: Target frames per second
        """
        running = True
        last_time = pygame.time.get_ticks() / 1000.0
        
        while running:
            # Calculate delta time
            current_time = pygame.time.get_ticks() / 1000.0
            dt = current_time - last_time
            last_time = current_time
            
            # Handle input
            running = self.input_handler.handle_events()
            
            # Update and render
            self.update(dt)
            self.render()
            
            # Cap the frame rate
            self.clock.tick(target_fps)
        
        # Clean up
        pygame.quit()

    # Convenience methods for common operations
    def draw_line_4d(
        self,
        start: Vector4D,
        end: Vector4D,
        color: Color | Sequence[int] | None,
        width: int = 2,
    ) -> None:
        """Draw a 4D line."""
        from ..graphics.primitives.lines import draw_line_4d as draw_line

        draw_line(
            self.screen,
            start,
            end,
            self._coerce_color(color, Color(255, 255, 255)),
            width,
            camera=self.camera,
            zbuffer=self.scene.zbuffer,
        )

    def render_hypercube(
        self,
        hypercube: Any,
        color: Color | Sequence[int] | None = None,
        width: int = 1,
    ) -> None:
        """Render a hypercube."""
        self.render_4d_object(hypercube, color=color, width=width)

    def render_simplex(
        self,
        simplex: Any,
        color: Color | Sequence[int] | None = None,
        width: int = 1,
    ) -> None:
        """Render a 4-D simplex (5-cell)."""
        self.render_4d_object(simplex, color=color, width=width)

    def render_4d_object(
        self,
        obj: Any,
        color: Color | Sequence[int] | None = None,
        width: int = 1,
    ) -> None:
        """Generic renderer for any polytope with `edges` and `get_transformed_vertices()`."""
        if not hasattr(obj, "edges") or not hasattr(obj, "get_transformed_vertices"):
            return

        try:
            verts = obj.get_transformed_vertices()
        except Exception:
            return

        resolved_color = self._coerce_color(
            color if color is not None else getattr(obj, "color", None),
            Color(0, 255, 255),
        )
        resolved_width = getattr(obj, "line_width", width if width is not None else 2)

        for a, b in getattr(obj, "edges", []):
            if a >= len(verts) or b >= len(verts):
                continue
            try:
                self.draw_line_4d(verts[a], verts[b], resolved_color, resolved_width)
            except Exception:
                # Skip problematic edge to keep loop running
                continue

    # Internal helpers
    @staticmethod
    def _coerce_color(value: Color | Sequence[int] | None, fallback: Color) -> Color:
        """Convert tuples/lists into a Color instance."""
        if isinstance(value, Color):
            return value
        if isinstance(value, (list, tuple)):
            if len(value) == 3:
                r, g, b = value
                return Color(int(r), int(g), int(b))
            if len(value) == 4:
                r, g, b, a = value
                return Color(int(r), int(g), int(b), int(a))
        return fallback
