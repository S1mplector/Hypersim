"""2D Plane controller - movement on XY plane."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .base import BaseController, InputHandler


class PlaneController(BaseController):
    """Controller for 2D plane movement (WASD on XY plane)."""
    
    dimension_id = "2d"
    axes_count = 2
    
    def compute_movement(self, input_handler: InputHandler) -> NDArray:
        """Compute 2D movement vector.
        
        Returns:
            4D vector with X and Y components set
        """
        if not self.enabled:
            return np.zeros(4)
        
        movement = np.zeros(4)
        movement[0] = self._get_axis_value("x", input_handler)
        movement[1] = self._get_axis_value("y", input_handler)
        
        # Normalize diagonal movement
        length = np.linalg.norm(movement[:2])
        if length > 1.0:
            movement[:2] /= length
        
        return movement
