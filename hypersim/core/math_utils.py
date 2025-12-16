"""Mathematical utilities for 4D operations."""
import numpy as np

from .math_4d import perspective_projection_4d_to_3d as _perspective_projection_4d_to_3d


def rotation_matrix_4d(plane1: int, plane2: int, angle: float) -> np.ndarray:
    """Create a 4D rotation matrix for rotation in the specified plane.
    
    Args:
        plane1: First axis of rotation plane (0-3)
        plane2: Second axis of rotation plane (0-3)
        angle: Rotation angle in radians
        
    Returns:
        4x4 rotation matrix
    """
    rotation = np.eye(4)
    c, s = np.cos(angle), np.sin(angle)
    rotation[plane1, plane1] = c
    rotation[plane1, plane2] = -s
    rotation[plane2, plane1] = s
    rotation[plane2, plane2] = c
    return rotation


def perspective_projection_4d_to_3d(points_4d: np.ndarray, distance: float = 5.0) -> np.ndarray:
    """Alias to the robust implementation in :mod:`hypersim.core.math_4d`."""
    return _perspective_projection_4d_to_3d(points_4d, distance)
