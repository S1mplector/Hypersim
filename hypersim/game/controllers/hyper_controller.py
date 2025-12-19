"""4D Hyper controller - 3D movement plus W-axis control."""
from __future__ import annotations

import math
import numpy as np
from numpy.typing import NDArray

from .base import BaseController, InputHandler, DEFAULT_MAPPINGS
from .volume_controller import VolumeController


class HyperController(VolumeController):
    """Controller for 4D hyperspace movement (3D + W axis)."""
    
    dimension_id = "4d"
    axes_count = 4
    
    def __init__(self, mapping=None):
        super().__init__(mapping or DEFAULT_MAPPINGS.get("4d"))
        self.w_position = 0.0  # Current W coordinate
        self.w_speed_multiplier = 0.5  # W movement is slower/more deliberate
    
    def compute_movement(self, input_handler: InputHandler) -> NDArray:
        """Compute 4D movement vector.
        
        Returns:
            4D vector with X, Y, Z, W components
        """
        if not self.enabled:
            return np.zeros(4)
        
        # Get 3D movement from parent
        movement = super().compute_movement(input_handler)
        
        # Add W-axis movement (Q/E keys)
        w_input = self._get_axis_value("w", input_handler)
        movement[3] = w_input * self.w_speed_multiplier
        
        return movement
    
    def get_4d_rotation_planes(self) -> dict[str, float]:
        """Get rotation angles for 4D visualization.
        
        Returns rotation angles for the 6 rotation planes in 4D:
        XY, XZ, XW, YZ, YW, ZW
        """
        return {
            "xy": 0.0,
            "xz": self.yaw,
            "xw": 0.0,
            "yz": self.pitch,
            "yw": 0.0,
            "zw": 0.0,
        }
    
    def rotate_4d(self, plane: str, angle: float) -> None:
        """Apply a 4D rotation in a specific plane.
        
        Args:
            plane: One of "xy", "xz", "xw", "yz", "yw", "zw"
            angle: Rotation angle in radians
        """
        if plane == "xz":
            self.yaw += angle
            self.yaw = self.yaw % (2 * math.pi)
        elif plane == "yz":
            self.pitch += angle
            self.pitch = np.clip(self.pitch, -self.pitch_limit, self.pitch_limit)
