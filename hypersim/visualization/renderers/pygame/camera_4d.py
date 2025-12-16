"""4D Camera system for perspective projection.

Provides a proper 4D camera with position, orientation, and projection
parameters for rendering 4D scenes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple
import numpy as np
import math

from hypersim.core.math_4d import (
    Vector4D,
    Matrix4D,
    create_vector_4d,
    create_rotation_matrix_4d,
    normalize_vector,
)


@dataclass
class Camera4D:
    """A 4D camera for rendering 4D scenes.
    
    The camera has a position in 4D space, looks at a target point,
    and projects the 4D world to 2D screen coordinates.
    """
    
    # Screen dimensions
    screen_width: int = 800
    screen_height: int = 600
    
    # Camera position and orientation in 4D
    position: np.ndarray = field(default_factory=lambda: np.array([0, 0, -5, 0], dtype=np.float32))
    target: np.ndarray = field(default_factory=lambda: np.array([0, 0, 0, 0], dtype=np.float32))
    up: np.ndarray = field(default_factory=lambda: np.array([0, 1, 0, 0], dtype=np.float32))
    
    # 4D to 3D projection parameters
    projection_distance: float = 5.0
    w_perspective_factor: float = 0.3
    
    # 3D to 2D projection parameters
    fov: float = 60.0  # Field of view in degrees
    near_clip: float = 0.1
    far_clip: float = 100.0
    
    # Rendering scale
    scale: float = 150.0
    
    # Camera control speeds
    move_speed: float = 0.15
    rotation_speed: float = 0.01
    zoom_speed: float = 1.1
    
    # Accumulated rotation angles for orbit mode
    _orbit_yaw: float = field(default=0.0, init=False)
    _orbit_pitch: float = field(default=0.0, init=False)
    _orbit_distance: float = field(default=5.0, init=False)
    
    def __post_init__(self):
        """Initialize derived values."""
        self._orbit_distance = np.linalg.norm(self.position - self.target)
        self._update_orbit_angles()
    
    def _update_orbit_angles(self) -> None:
        """Calculate orbit angles from current position."""
        offset = self.position - self.target
        dist_xz = math.sqrt(offset[0]**2 + offset[2]**2)
        self._orbit_yaw = math.atan2(offset[0], -offset[2])
        self._orbit_pitch = math.atan2(offset[1], dist_xz)
    
    def _update_position_from_orbit(self) -> None:
        """Update position from orbit parameters."""
        cos_pitch = math.cos(self._orbit_pitch)
        self.position = self.target + np.array([
            self._orbit_distance * math.sin(self._orbit_yaw) * cos_pitch,
            self._orbit_distance * math.sin(self._orbit_pitch),
            -self._orbit_distance * math.cos(self._orbit_yaw) * cos_pitch,
            self.position[3],  # Keep W coordinate
        ], dtype=np.float32)
    
    def orbit(self, delta_yaw: float, delta_pitch: float) -> None:
        """Orbit the camera around the target.
        
        Args:
            delta_yaw: Change in yaw angle (radians)
            delta_pitch: Change in pitch angle (radians)
        """
        self._orbit_yaw += delta_yaw
        self._orbit_pitch = np.clip(
            self._orbit_pitch + delta_pitch,
            -math.pi / 2 + 0.1,
            math.pi / 2 - 0.1
        )
        self._update_position_from_orbit()
    
    def zoom(self, factor: float) -> None:
        """Zoom the camera in or out.
        
        Args:
            factor: Zoom factor (>1 zooms out, <1 zooms in)
        """
        self._orbit_distance = max(0.5, self._orbit_distance * factor)
        self._update_position_from_orbit()
    
    def move(self, dx: float, dy: float, dz: float, dw: float = 0.0) -> None:
        """Move the camera in world space.
        
        Args:
            dx, dy, dz, dw: Movement deltas in each axis
        """
        delta = np.array([dx, dy, dz, dw], dtype=np.float32)
        self.position += delta
        self.target += delta
    
    def move_w(self, dw: float) -> None:
        """Move the camera along the W axis only.
        
        Args:
            dw: Movement delta in W axis
        """
        self.position[3] += dw
    
    def set_position(self, x: float, y: float, z: float, w: float = 0.0) -> None:
        """Set the camera position directly."""
        self.position = np.array([x, y, z, w], dtype=np.float32)
        self._orbit_distance = np.linalg.norm(self.position - self.target)
        self._update_orbit_angles()
    
    def set_target(self, x: float, y: float, z: float, w: float = 0.0) -> None:
        """Set the camera target directly."""
        self.target = np.array([x, y, z, w], dtype=np.float32)
        self._orbit_distance = np.linalg.norm(self.position - self.target)
        self._update_orbit_angles()
    
    def reset(self) -> None:
        """Reset camera to default position."""
        self.position = np.array([0, 0, -5, 0], dtype=np.float32)
        self.target = np.array([0, 0, 0, 0], dtype=np.float32)
        self._orbit_distance = 5.0
        self._orbit_yaw = 0.0
        self._orbit_pitch = 0.0
    
    def project_4d_to_3d(self, point_4d: np.ndarray) -> np.ndarray:
        """Project a 4D point to 3D using perspective projection.
        
        Args:
            point_4d: 4D point [x, y, z, w]
            
        Returns:
            3D point [x, y, z]
        """
        x, y, z, w = point_4d
        
        # 4D perspective: scale based on W distance
        w_factor = 1.0 / (1.0 + abs(w) * self.w_perspective_factor)
        
        return np.array([
            x * w_factor,
            y * w_factor,
            z * w_factor,
        ], dtype=np.float32)
    
    def project_3d_to_2d(self, point_3d: np.ndarray) -> Tuple[int, int, float]:
        """Project a 3D point to 2D screen coordinates.
        
        Args:
            point_3d: 3D point [x, y, z]
            
        Returns:
            Tuple of (screen_x, screen_y, depth)
        """
        x, y, z = point_3d
        
        # Simple orthographic-like projection with scale
        screen_x = int(x * self.scale + self.screen_width / 2)
        screen_y = int(-y * self.scale + self.screen_height / 2)
        
        return screen_x, screen_y, z
    
    def project_4d_to_2d(self, point_4d: np.ndarray) -> Tuple[int, int, float]:
        """Project a 4D point directly to 2D screen coordinates.
        
        Args:
            point_4d: 4D point [x, y, z, w]
            
        Returns:
            Tuple of (screen_x, screen_y, depth)
        """
        x, y, z, w = point_4d
        
        # 4D perspective projection
        w_scale = 1.0 / (1.0 + abs(w) * self.w_perspective_factor)
        
        # Apply W-based scaling
        proj_x = x * w_scale
        proj_y = y * w_scale
        proj_z = z * w_scale
        
        # Convert to screen coordinates
        screen_x = int(proj_x * self.scale + self.screen_width / 2)
        screen_y = int(-proj_y * self.scale + self.screen_height / 2)
        
        return screen_x, screen_y, proj_z
    
    def batch_project_4d_to_2d(
        self,
        vertices_4d: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Project multiple 4D vertices to 2D in a vectorized operation.
        
        Args:
            vertices_4d: Array of shape (N, 4)
            
        Returns:
            Tuple of:
            - screen_coords: Array of shape (N, 2) with int screen coordinates
            - depths: Array of shape (N,) with depth values
        """
        vertices_4d = np.asarray(vertices_4d, dtype=np.float32)
        
        w = vertices_4d[:, 3]
        w_scale = 1.0 / (1.0 + np.abs(w) * self.w_perspective_factor)
        
        proj_x = vertices_4d[:, 0] * w_scale
        proj_y = vertices_4d[:, 1] * w_scale
        proj_z = vertices_4d[:, 2] * w_scale
        
        screen_x = (proj_x * self.scale + self.screen_width / 2).astype(np.int32)
        screen_y = (-proj_y * self.scale + self.screen_height / 2).astype(np.int32)
        
        screen_coords = np.stack([screen_x, screen_y], axis=1)
        
        return screen_coords, proj_z
    
    def is_point_visible(self, screen_x: int, screen_y: int, depth: float) -> bool:
        """Check if a screen point is within visible bounds.
        
        Args:
            screen_x, screen_y: Screen coordinates
            depth: Depth value
            
        Returns:
            True if point is visible
        """
        if screen_x < -100 or screen_x > self.screen_width + 100:
            return False
        if screen_y < -100 or screen_y > self.screen_height + 100:
            return False
        if depth > self.far_clip or depth < -self.far_clip:
            return False
        return True
