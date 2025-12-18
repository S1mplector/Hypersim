"""Dimension descriptors for cross-dimensional gameplay."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class DimensionSpec:
    """Describes gameplay rules for a single dimension."""

    id: str
    order: int
    name: str
    axes: int
    movement_axes: List[str]
    render_mode: str
    description: str = ""
    abilities: List[str] = field(default_factory=list)
    control_over_lower: bool = False
    projection_hint: Optional[str] = None

    def dominates(self, other: "DimensionSpec") -> bool:
        """Return True if this dimension can exert control over a lower one."""
        return self.control_over_lower and self.order > other.order

    def can_observe(self, other: "DimensionSpec") -> bool:
        """Return True if this dimension can observe another."""
        return self.order >= other.order


class DimensionTrack:
    """Ordered track of dimensions a campaign can progress through."""

    def __init__(self, specs: Iterable[DimensionSpec]):
        sorted_specs = sorted(specs, key=lambda s: s.order)
        self._specs_by_id: Dict[str, DimensionSpec] = {spec.id: spec for spec in sorted_specs}
        self._ordered_ids: List[str] = [spec.id for spec in sorted_specs]

    def get(self, dimension_id: str) -> DimensionSpec:
        if dimension_id not in self._specs_by_id:
            raise KeyError(f"dimension '{dimension_id}' not registered")
        return self._specs_by_id[dimension_id]

    def all(self) -> List[DimensionSpec]:
        return [self._specs_by_id[i] for i in self._ordered_ids]

    def first(self) -> DimensionSpec:
        return self._specs_by_id[self._ordered_ids[0]]

    def next(self, dimension_id: str) -> Optional[DimensionSpec]:
        try:
            idx = self._ordered_ids.index(dimension_id)
        except ValueError:
            return None
        if idx + 1 >= len(self._ordered_ids):
            return None
        return self._specs_by_id[self._ordered_ids[idx + 1]]

    def previous(self, dimension_id: str) -> Optional[DimensionSpec]:
        try:
            idx = self._ordered_ids.index(dimension_id)
        except ValueError:
            return None
        if idx == 0:
            return None
        return self._specs_by_id[self._ordered_ids[idx - 1]]


DEFAULT_DIMENSIONS: List[DimensionSpec] = [
    DimensionSpec(
        id="1d",
        order=0,
        name="Line Being",
        axes=1,
        movement_axes=["x"],
        render_mode="line",
        description="Exist only along a line; limited visibility of neighbors.",
        abilities=["ping_neighbors"],
    ),
    DimensionSpec(
        id="2d",
        order=1,
        name="Plane Dweller",
        axes=2,
        movement_axes=["x", "y"],
        render_mode="plane",
        description="Traverse a plane; fold or reveal 1D spaces.",
        abilities=["fold_line", "sketch_path"],
        control_over_lower=True,
    ),
    DimensionSpec(
        id="3d",
        order=2,
        name="Spatial Explorer",
        axes=3,
        movement_axes=["x", "y", "z"],
        render_mode="volume",
        description="Move in volume; manipulate 2D holograms and carry 1D beings.",
        abilities=["slice_plane", "carry_line"],
        control_over_lower=True,
        projection_hint="perspective",
    ),
    DimensionSpec(
        id="4d",
        order=3,
        name="Hyper Being",
        axes=4,
        movement_axes=["x", "y", "z", "w"],
        render_mode="hypervolume",
        description="Full 4D perception and control; project objects into lower spaces.",
        abilities=["rotate_hyperplanes", "spawn_slices", "stabilize_lower"],
        control_over_lower=True,
        projection_hint="4d_perspective",
    ),
]
