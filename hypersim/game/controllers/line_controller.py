"""1D Line controller - movement on a single axis."""
from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .base import BaseController, InputHandler


class LineController(BaseController):
    """Controller for 1D line movement (left/right only)."""
    
    dimension_id = "1d"
    axes_count = 1
    
    def compute_movement(self, input_handler: InputHandler) -> NDArray:
        """Compute 1D movement vector.
        
        Returns:
            4D vector with only X component set
        """
        if not self.enabled:
            return np.zeros(4)
        
        movement = np.zeros(4)
        movement[0] = self._get_axis_value("x", input_handler)
        return movement
