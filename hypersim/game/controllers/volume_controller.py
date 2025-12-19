"""3D Volume controller - FPS-style movement with mouse look."""
from __future__ import annotations

import math
import numpy as np
from numpy.typing import NDArray

from .base import BaseController, InputHandler, DEFAULT_MAPPINGS


class VolumeController(BaseController):
    """Controller for 3D volume movement (FPS-style with mouse look)."""
    
    dimension_id = "3d"
    axes_count = 3
    
    def __init__(self, mapping=None):
        super().__init__(mapping or DEFAULT_MAPPINGS.get("3d"))
        self.yaw = 0.0    # Horizontal rotation (radians)
        self.pitch = 0.0  # Vertical rotation (radians)
        self.pitch_limit = math.pi / 2 - 0.1  # Prevent gimbal lock
        self.mouse_captured = False
        self.fly_mode = True  # If False, gravity applies
    
    def compute_movement(self, input_handler: InputHandler) -> NDArray:
        """Compute 3D movement vector based on input and camera orientation.
        
        Returns:
            4D vector with X, Y, Z components set (Y is vertical)
        """
        if not self.enabled:
            return np.zeros(4)
        
        # Get raw input
        forward = self._get_axis_value("z", input_handler)  # W/S
        strafe = self._get_axis_value("x", input_handler)   # A/D
        
        # Vertical movement (fly mode or jump)
        vertical = 0.0
        if self.fly_mode:
            if input_handler.is_held(self.mapping.actions.get("jump", 0)):
                vertical = 1.0
            if input_handler.is_held(self.mapping.actions.get("crouch", 0)):
                vertical = -1.0
        
        # Build movement vector in local space
        # Forward is -Z in our coordinate system
        movement = np.zeros(4)
        
        # Calculate forward/right vectors from yaw (ignore pitch for ground movement)
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        
        # Forward vector (in XZ plane)
        forward_vec = np.array([-sin_yaw, 0.0, -cos_yaw])
        # Right vector (perpendicular to forward in XZ plane)
        right_vec = np.array([cos_yaw, 0.0, -sin_yaw])
        
        # Combine inputs
        move_dir = forward_vec * forward + right_vec * strafe
        
        # Normalize horizontal movement
        horiz_len = np.linalg.norm(move_dir[:3])
        if horiz_len > 1.0:
            move_dir /= horiz_len
        
        movement[0] = move_dir[0]  # X
        movement[1] = vertical     # Y (up/down)
        movement[2] = move_dir[2]  # Z
        
        return movement
    
    def process_mouse(self, input_handler: InputHandler) -> None:
        """Update camera orientation from mouse movement."""
        if not self.mouse_captured or not self.mapping.mouse_look:
            return
        
        dx, dy = input_handler.get_mouse_delta()
        
        # Apply sensitivity
        self.yaw += dx * self.mapping.mouse_sensitivity
        self.pitch -= dy * self.mapping.mouse_sensitivity
        
        # Clamp pitch
        self.pitch = np.clip(self.pitch, -self.pitch_limit, self.pitch_limit)
        
        # Wrap yaw
        self.yaw = self.yaw % (2 * math.pi)
    
    def get_view_matrix(self) -> NDArray:
        """Get the camera view direction as a 3x3 rotation matrix."""
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)
        
        # Forward vector
        forward = np.array([
            -sin_yaw * cos_pitch,
            sin_pitch,
            -cos_yaw * cos_pitch
        ])
        
        # Right vector
        right = np.array([cos_yaw, 0.0, -sin_yaw])
        
        # Up vector
        up = np.cross(right, forward)
        
        return np.array([right, up, -forward])
    
    def get_forward_vector(self) -> NDArray:
        """Get the camera's forward direction."""
        cos_yaw = math.cos(self.yaw)
        sin_yaw = math.sin(self.yaw)
        cos_pitch = math.cos(self.pitch)
        sin_pitch = math.sin(self.pitch)
        
        return np.array([
            -sin_yaw * cos_pitch,
            sin_pitch,
            -cos_yaw * cos_pitch
        ])
    
    def look_at(self, target: NDArray, position: NDArray) -> None:
        """Orient the camera to look at a target position."""
        direction = target[:3] - position[:3]
        dist = np.linalg.norm(direction)
        if dist < 0.001:
            return
        
        direction /= dist
        
        self.yaw = math.atan2(-direction[0], -direction[2])
        self.pitch = math.asin(np.clip(direction[1], -1.0, 1.0))
