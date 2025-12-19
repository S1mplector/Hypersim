"""Dimension-specific renderers."""

from .base_renderer import DimensionRenderer
from .line_renderer import LineRenderer
from .plane_renderer import PlaneRenderer
from .volume_renderer import VolumeRenderer
from .hyper_renderer import HyperRenderer

__all__ = [
    "DimensionRenderer",
    "LineRenderer",
    "PlaneRenderer",
    "VolumeRenderer",
    "HyperRenderer",
]
