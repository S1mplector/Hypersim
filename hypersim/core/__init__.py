"""Core functionality for 4D geometry and transformations."""

from .math_utils import *  # noqa: F403
from .math_4d import (
    create_vector_4d,
    create_rotation_matrix_4d,
    create_scale_matrix_4d,
    perspective_projection_4d_to_3d,
    normalize_vector,
    dot_product_4d,
    cross_product_4d,
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
    'math_utils',
    'create_vector_4d',
    'create_rotation_matrix_4d',
    'create_scale_matrix_4d',
    'perspective_projection_4d_to_3d',
    'normalize_vector',
    'dot_product_4d',
    'cross_product_4d',
    'Shape4D',
    'compute_cross_section',
    'compute_w_range',
    'slice_edge_at_w',
    'CrossSection',
    'SliceAnimator',
]
