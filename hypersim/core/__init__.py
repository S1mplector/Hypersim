"""Core functionality for 4D geometry and transformations.

This module provides the mathematical foundation for 4D visualization:
- Vector and matrix operations in 4D
- Rotation matrices for all 6 rotation planes
- Perspective projection from 4D to 3D to 2D
- Shape base class for all 4D polytopes
"""

from .math_utils import *  # noqa: F403
from .math_4d import (
    # Constants
    X, Y, Z, W,
    PLANE_XY, PLANE_XZ, PLANE_XW, PLANE_YZ, PLANE_YW, PLANE_ZW,
    ALL_PLANES,
    # Type aliases
    Vector4D, Matrix4D, Vector3D, Matrix3D,
    # Vector creation
    create_vector_4d,
    vec4,
    # Vector operations
    length_4d,
    length_squared_4d,
    distance_4d,
    normalize_vector,
    normalize_4d,
    dot_product_4d,
    cross_product_4d,
    lerp_4d,
    slerp_4d,
    angle_between_4d,
    project_onto_4d,
    reject_from_4d,
    reflect_4d,
    # Matrix operations
    identity_4d,
    create_translation_matrix_4d,
    create_scale_matrix_4d,
    uniform_scale_4d,
    # Rotation matrices
    rotation_matrix_plane,
    rotation_xy, rotation_xz, rotation_yz,
    rotation_xw, rotation_yw, rotation_zw,
    create_rotation_matrix_4d,
    # Projection
    perspective_projection_4d_to_3d,
    project_4d_to_2d,
    # Camera
    create_look_at_matrix,
)
from .shape_4d import Shape4D
from .slicer import (
    compute_cross_section,
    compute_w_range,
    slice_edge_at_w,
    CrossSection,
    SliceAnimator,
)

__all__ = [
    # Constants
    'X', 'Y', 'Z', 'W',
    'PLANE_XY', 'PLANE_XZ', 'PLANE_XW', 'PLANE_YZ', 'PLANE_YW', 'PLANE_ZW',
    'ALL_PLANES',
    # Types
    'Vector4D', 'Matrix4D', 'Vector3D', 'Matrix3D',
    # Vectors
    'create_vector_4d', 'vec4',
    'length_4d', 'length_squared_4d', 'distance_4d',
    'normalize_vector', 'normalize_4d',
    'dot_product_4d', 'cross_product_4d',
    'lerp_4d', 'slerp_4d',
    'angle_between_4d', 'project_onto_4d', 'reject_from_4d', 'reflect_4d',
    # Matrices
    'identity_4d',
    'create_translation_matrix_4d', 'create_scale_matrix_4d', 'uniform_scale_4d',
    # Rotations
    'rotation_matrix_plane',
    'rotation_xy', 'rotation_xz', 'rotation_yz',
    'rotation_xw', 'rotation_yw', 'rotation_zw',
    'create_rotation_matrix_4d',
    # Projection
    'perspective_projection_4d_to_3d', 'project_4d_to_2d',
    # Camera
    'create_look_at_matrix',
    # Shape
    'Shape4D',
    # Slicer
    'compute_cross_section', 'compute_w_range', 'slice_edge_at_w',
    'CrossSection', 'SliceAnimator',
]
