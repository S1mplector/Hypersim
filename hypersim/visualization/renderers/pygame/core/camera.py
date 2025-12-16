"""Camera implementation for the Pygame renderer.

This module provides the Camera class which handles view and projection
matrices, as well as camera movement and orientation in 4D space.
"""

from __future__ import annotations

import numpy as np
import pygame
from typing import Tuple

from hypersim.core.math_4d import (
    Vector4D,
    create_vector_4d,
    create_rotation_matrix_4d,
    perspective_projection_4d_to_3d,
    create_look_at_matrix,
)
from ..graphics.color import Color

__all__ = ["Camera"]


class Camera:
    """A 4D camera that handles view and projection transformations.
    
    This class manages the camera's position, orientation, and projection
    settings for rendering 4D scenes in a 2D viewport.
    """
    
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        position: Vector4D | None = None,
        target: Vector4D | None = None,
        up: Vector4D | None = None,
        distance: float = 5.0,
    ) -> None:
        """Initialize the camera with the given parameters.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            position: Camera position in 4D space
            target: Camera look-at target in 4D space
            up: Up vector for camera orientation
            distance: Distance from camera to near clipping plane
        """
        self.width = width
        self.height = height
        self.distance = distance
        
        # Set up camera position and orientation
        self.position = position if position is not None else create_vector_4d(0, 0, -distance * 2, 0)
        self.target = target if target is not None else create_vector_4d(0, 0, 0, 0)
        self.up = up if up is not None else create_vector_4d(0, 1, 0, 0)
        
        # Camera movement properties
        self.rotation_speed = 0.02
        self.move_speed = 0.1
        self.is_rotating = False
        self.last_mouse_pos: Tuple[int, int] = (0, 0)
        
        # Matrices
        self.view_matrix = np.eye(4, dtype=np.float32)
        self._update_view_matrix()
    
    def _update_view_matrix(self) -> None:
        """Update the view matrix based on the current camera position and orientation."""
        self.view_matrix = create_look_at_matrix(
            eye=self.position,
            target=self.target,
            up=self.up,
        )

    def world_to_view(self, point_4d: Vector4D) -> Vector4D:
        """Transform a world-space point into camera view space."""
        return self.view_matrix @ (point_4d - self.position)

    def project_view_point(self, view_point: Vector4D) -> Tuple[int, int, float]:
        """Project a view-space 4D point directly to 2D screen coordinates."""
        effective_distance = max(self.distance, 0.01)
        projected = perspective_projection_4d_to_3d(
            view_point[np.newaxis, :],
            effective_distance,
        )[0]

        if not np.isfinite(projected).all():
            raise ValueError("Projection produced non-finite values")

        scale = 140  # UI-friendly default scale
        x = int(projected[0] * scale + self.width // 2)
        y = int(-projected[1] * scale + self.height // 2)  # y-axis is inverted for screen

        return x, y, projected[2]
    
    def project_4d_to_2d(self, point_4d: Vector4D) -> Tuple[int, int, float]:
        """Project a 4D point to 2D screen coordinates with depth.
        
        Args:
            point_4d: 4D point to project
            
        Returns:
            A tuple of (x, y, depth) where (x, y) are screen coordinates
            and depth is the distance from the camera.
        """
        view_point = self.world_to_view(point_4d)
        return self.project_view_point(view_point)
    
    def handle_mouse_motion(self, dx: float, dy: float) -> None:
        """Handle mouse movement for camera rotation.
        
        Args:
            dx: Change in x position
            dy: Change in y position
        """
        if not self.is_rotating:
            return
            
        rot_x = create_rotation_matrix_4d(angle_xy=dx * 0.01)
        rot_y = create_rotation_matrix_4d(angle_xz=dy * 0.01)
        cam_to_target = self.position - self.target
        cam_to_target = rot_x @ (rot_y @ cam_to_target)
        self.position = self.target + cam_to_target
        self._update_view_matrix()
    
    def handle_key_press(self, key: int) -> None:
        """Handle keyboard input for camera movement.
        
        Args:
            key: Pygame key constant
        """
        # Camera movement in 3D space (x, y, z)
        if key == pygame.K_w:
            self.position[2] += self.move_speed
        elif key == pygame.K_s:
            self.position[2] -= self.move_speed
        elif key == pygame.K_a:
            self.position[0] -= self.move_speed
        elif key == pygame.K_d:
            self.position[0] += self.move_speed
        elif key == pygame.K_q:
            self.position[1] += self.move_speed
        elif key == pygame.K_e:
            self.position[1] -= self.move_speed
            
        # Camera movement in 4D space (w-axis)
        elif key == pygame.K_z:
            self.position[3] += self.move_speed
        elif key == pygame.K_x:
            self.position[3] -= self.move_speed
            
        # Zoom controls
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.distance *= 1.1  # Zoom out
        elif key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
            self.distance = max(0.1, self.distance / 1.1)  # Zoom in
            
        self._update_view_matrix()
