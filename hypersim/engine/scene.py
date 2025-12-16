"""Scene graph for 4D simulations.

The `Scene` class aggregates objects and handles hierarchical transformations
as well as update dispatching to objects each simulation tick.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Any

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D


class Scene:
    """A collection of 4D objects and their relationships."""

    def __init__(self) -> None:
        self._objects: List[Shape4D] = []

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def add(self, obj: "Shape4D") -> None:
        """Add an object (e.g., `Hypercube`) to the scene."""
        self._objects.append(obj)

    def remove(self, obj: "Shape4D") -> bool:
        """Remove an object from the scene. Returns True if removed."""
        try:
            self._objects.remove(obj)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """Remove all objects from the scene."""
        self._objects.clear()

    def objects(self) -> List["Shape4D"]:
        """Return objects currently in the scene (read-only)."""
        return list(self._objects)

    def __len__(self) -> int:
        """Return number of objects in scene."""
        return len(self._objects)

    def __iter__(self):
        """Iterate over objects in the scene."""
        return iter(self._objects)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Update all objects in the scene.

        Args:
            dt: Delta-time (seconds) since last update.
        """
        # Placeholder: Objects may implement an `update(dt)` method.
        for obj in self._objects:
            update_fn = getattr(obj, "update", None)
            if callable(update_fn):
                update_fn(dt)
