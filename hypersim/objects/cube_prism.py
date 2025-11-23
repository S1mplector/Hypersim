"""Prism over a 3D cube (cube extruded along the W axis)."""
from __future__ import annotations

import itertools
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class CubePrism(Shape4D):
    """Cube prism with 16 vertices and 48 edges."""

    def __init__(self, size: float = 1.0, height: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)
        self.height = float(height)

        # Base cube vertices in XYZ, w offset by ±height/2
        half = self.size / 2.0
        half_h = self.height / 2.0
        verts: List[Vector4D] = []
        for x, y, z in itertools.product((-half, half), repeat=3):
            verts.append(np.array([x, y, z, -half_h], dtype=np.float32))
        for x, y, z in itertools.product((-half, half), repeat=3):
            verts.append(np.array([x, y, z, half_h], dtype=np.float32))
        self._base_vertices = verts

        # Edges: within each cube plus vertical links
        self._edges: List[Tuple[int, int]] = []
        # Bottom cube edges
        bottom_indices = list(range(8))
        top_indices = list(range(8, 16))

        def cube_edges(offset_indices: List[int]) -> List[Tuple[int, int]]:
            edges: List[Tuple[int, int]] = []
            for i in range(4):
                edges.append((offset_indices[i], offset_indices[(i + 1) % 4]))
            for i in range(4, 8):
                edges.append((offset_indices[i], offset_indices[4 + ((i + 1 - 4) % 4)]))
            for i in range(4):
                edges.append((offset_indices[i], offset_indices[i + 4]))
            return edges

        self._edges.extend(cube_edges(bottom_indices))
        self._edges.extend(cube_edges(top_indices))
        # Vertical edges
        for i in range(8):
            self._edges.append((bottom_indices[i], top_indices[i]))

        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []

    @property
    def vertices(self) -> List[Vector4D]:
        return self._base_vertices

    @property
    def edges(self) -> List[Tuple[int, int]]:
        return self._edges

    @property
    def faces(self) -> List[Tuple[int, ...]]:
        return self._faces

    @property
    def cells(self) -> List[Tuple[int, ...]]:
        return self._cells

    def update(self, dt: float) -> None:
        self.rotate(xy=0.25 * dt, xw=0.2 * dt, yw=0.2 * dt, zw=0.15 * dt)
