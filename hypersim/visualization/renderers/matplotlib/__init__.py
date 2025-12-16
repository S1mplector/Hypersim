"""Matplotlib-based renderer for 4D objects.

This renderer provides static and animated visualization using matplotlib,
suitable for:
- Jupyter notebooks
- Publication-quality figures
- Non-interactive batch rendering
- 3D rotation animations saved as GIF/MP4
"""

from .renderer import MatplotlibRenderer
from .animator import MatplotlibAnimator

__all__ = ["MatplotlibRenderer", "MatplotlibAnimator"]
