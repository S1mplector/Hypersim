"""4D Object Editor module.

Provides tools for interactive editing of 4D objects.
"""

from .object_editor import (
    ObjectEditor,
    EditMode,
    Axis,
    SelectionInfo,
    TransformGizmo,
    GizmoConfig,
)

__all__ = [
    "ObjectEditor",
    "EditMode",
    "Axis",
    "SelectionInfo",
    "TransformGizmo",
    "GizmoConfig",
]
