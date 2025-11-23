"""Main Pygame-based 4-D renderer implementation.

Separated from ``__init__.py`` for better maintainability.  All heavy logic
lives here; the package root simply re-exports :class:`PygameRenderer` and
:class:`Color` for convenience:

    from hypersim.visualization.renderers.pygame import PygameRenderer, Color
"""
from __future__ import annotations

from typing import Any, List, Tuple
import numpy as np
import pygame

from hypersim.core.math_4d import (
    Vector4D,
    create_vector_4d,
    create_rotation_matrix_4d,
    create_look_at_matrix,
)

from .graphics.color import Color  # reuse the unified Color helper

__all__ = ["PygameRenderer"]


class PygameRenderer:
    """Custom 4-D renderer using Pygame hardware acceleration."""

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        title: str = "4D Renderer",
        background_color: Color | None = None,
        distance: float = 5.0,
    ) -> None:
        if background_color is None:
            background_color = Color(0, 0, 0)

        # Pygame window -----------------------------------------------------------
        pygame.init()
        pygame.display.set_caption(title)
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)

        # Basic params ------------------------------------------------------------
        self.width = width
        self.height = height
        self.background_color = background_color
        self.distance = distance
        self.clock = pygame.time.Clock()

        # Camera ------------------------------------------------------------------
        self.camera_pos = create_vector_4d(0, 0, -distance * 2, 0)
        self.target = create_vector_4d(0, 0, 0, 0)
        self.up = create_vector_4d(0, 1, 0, 0)
        self.rotation_speed = 0.02
        self.move_speed = 0.1
        self.is_rotating = False
        self.last_mouse_pos: Tuple[int, int] = (0, 0)
        self.view_matrix = np.eye(4, dtype=np.float32)
        self._update_view_matrix()

        # Scene -------------------------------------------------------------------
        self.objects: List[Any] = []
        self.zbuffer = np.ones((width, height), dtype=np.float32) * float("inf")

        # HUD ---------------------------------------------------------------------
        self.font = pygame.font.Font(None, 36)
        self.fps = 0.0
        self.frame_count = 0
        self.last_fps_update = pygame.time.get_ticks()

    # -----------------------------------------------------------------------
    # Camera helpers
    # -----------------------------------------------------------------------
    def _update_view_matrix(self) -> None:
        self.view_matrix = create_look_at_matrix(
            eye=self.camera_pos, target=self.target, up=self.up
        )

    # -----------------------------------------------------------------------
    # Projection helpers
    # -----------------------------------------------------------------------
    def _project_4d_to_2d(self, p: Vector4D) -> Tuple[int, int, float]:
        # Improved 4D projection using W-based scaling to prevent vertex collapse
        x, y, z, w = p
        
        # Use W coordinate to scale the X,Y coordinates (prevents symmetrical collapse)
        scale = 1.0 / (1.0 + abs(w) * 0.3)  # Scale based on W distance
        
        # Apply scaling and convert to screen coordinates
        screen_x = int(x * scale * 120 + self.width // 2)   # Increased scale factor
        screen_y = int(-y * scale * 120 + self.height // 2)  # Increased scale factor
        
        # Use Z coordinate for depth (for potential z-buffering)
        depth = z * scale
        
        return screen_x, screen_y, depth

    # -----------------------------------------------------------------------
    # Rendering primitives
    # -----------------------------------------------------------------------
    def clear(self) -> None:
        self.screen.fill(self.background_color.to_tuple())
        self.zbuffer.fill(float("inf"))

    def draw_line_4d(self, s: Vector4D, e: Vector4D, color: Color, width: int = 1) -> None:
        x1, y1, z1 = self._project_4d_to_2d(s)
        x2, y2, z2 = self._project_4d_to_2d(e)
        # Simple near-plane clipping based on current projection distance
        if z1 > self.distance and z2 > self.distance:
            return
        pygame.draw.line(self.screen, color.to_tuple(), (x1, y1), (x2, y2), width)

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------
    def render_hypercube(self, hypercube, color: Color = Color(0, 255, 0), width: int = 1) -> None:
        # Get the transformed vertices from the hypercube
        transformed_vertices = hypercube.get_transformed_vertices()
        
        # Draw all edges using the transformed vertices
        for a, b in hypercube.edges:
            self.draw_line_4d(transformed_vertices[a], transformed_vertices[b], color, width)
    
    def render_simplex(self, simplex, color: Color = Color(255, 100, 0), width: int = 1) -> None:
        """Render a 4D simplex object.
        
        Args:
            simplex: The 4D simplex object to render
            color: Color to draw the simplex edges
            width: Line width for drawing edges
        """
        # Get the transformed vertices from the simplex
        transformed_vertices = simplex.get_transformed_vertices()
        
        # Draw all edges using the transformed vertices
        for a, b in simplex.edges:
            self.draw_line_4d(transformed_vertices[a], transformed_vertices[b], color, width)
    
    def render_4d_object(self, obj, color: Color = Color(0, 255, 255), width: int = 1) -> None:
        """Generic method to render any 4D object with vertices and edges.
        
        Args:
            obj: Any 4D object with get_transformed_vertices() method and edges attribute
            color: Color to draw the object edges
            width: Line width for drawing edges
        """
        # Get the transformed vertices from the object
        transformed_vertices = obj.get_transformed_vertices()
        
        # Draw all edges using the transformed vertices
        for a, b in obj.edges:
            self.draw_line_4d(transformed_vertices[a], transformed_vertices[b], color, width)

    # Event loop ---------------------------------------------------------------
    def handle_events(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                elif ev.key == pygame.K_w:
                    self.camera_pos[2] += self.move_speed
                elif ev.key == pygame.K_s:
                    self.camera_pos[2] -= self.move_speed
                elif ev.key == pygame.K_a:
                    self.camera_pos[0] -= self.move_speed
                elif ev.key == pygame.K_d:
                    self.camera_pos[0] += self.move_speed
                elif ev.key == pygame.K_q:
                    self.camera_pos[1] += self.move_speed
                elif ev.key == pygame.K_e:
                    self.camera_pos[1] -= self.move_speed
                elif ev.key == pygame.K_z:
                    self.camera_pos[3] += self.move_speed
                elif ev.key == pygame.K_x:
                    self.camera_pos[3] -= self.move_speed
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    self.distance *= 1.1
                elif ev.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    self.distance = max(0.1, self.distance / 1.1)
                self._update_view_matrix()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.is_rotating = True
                self.last_mouse_pos = ev.pos
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                self.is_rotating = False
            elif ev.type == pygame.MOUSEMOTION and self.is_rotating:
                dx = ev.pos[0] - self.last_mouse_pos[0]
                dy = ev.pos[1] - self.last_mouse_pos[1]
                rot_x = create_rotation_matrix_4d(angle_xy=dx * 0.01)
                rot_y = create_rotation_matrix_4d(angle_xz=dy * 0.01)
                cam_to_target = self.camera_pos - self.target
                cam_to_target = rot_x @ (rot_y @ cam_to_target)
                self.camera_pos = self.target + cam_to_target
                self.last_mouse_pos = ev.pos
                self._update_view_matrix()
        return True

    def update(self, dt: float) -> None:
        # Apply continuous 4D rotations to any object that supports it
        for obj in self.objects:
            if hasattr(obj, "rotate"):
                obj.rotate(
                    xy=dt * 0.4,  # XY rotation (3D spin)
                    xw=dt * 0.6,  # XW rotation (4D fold)
                    yw=dt * 0.5,  # YW rotation (4D fold)
                    zw=dt * 0.3,  # ZW rotation (4D spin)
                )
        
        # FPS counter update
        self.frame_count += 1
        now = pygame.time.get_ticks()
        if now - self.last_fps_update > 1000:
            self.fps = self.frame_count * 1000 / (now - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = now

    def render(self) -> None:
        self.clear()
        for obj in self.objects:
            if hasattr(obj, "render"):
                obj.render(self)
        pygame.display.flip()

    def run(self, target_fps: int = 60) -> None:
        running = True
        last = pygame.time.get_ticks() / 1000.0
        while running:
            now = pygame.time.get_ticks() / 1000.0
            dt = now - last
            last = now
            running = self.handle_events()
            self.update(dt)
            self.render()
            self.clock.tick(target_fps)
        pygame.quit()
