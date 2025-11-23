"""Prism over a 4D simplex (5-cell prism)."""
from __future__ import annotations

import numpy as np
from typing import List, Tuple

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class SimplexPrism(Shape4D):
    """Prism of a 4D simplex extruded along the W axis.

    Consists of two translated copies of a 5-cell connected vertex-to-vertex.
    """

    def __init__(self, size: float = 1.0, height: float = 0.7, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)
        self.height = float(height)

        # Base simplex vertices (same as Simplex4D but normalized)
        sqrt5 = np.sqrt(5)
        base = [
            np.array([1, 1, 1, -1 / sqrt5], dtype=np.float32),
            np.array([1, -1, -1, -1 / sqrt5], dtype=np.float32),
            np.array([-1, 1, -1, -1 / sqrt5], dtype=np.float32),
            np.array([-1, -1, 1, -1 / sqrt5], dtype=np.float32),
            np.array([0, 0, 0, 4 / sqrt5], dtype=np.float32),
        ]
        base = [v * (self.size / 2.0) for v in base]

        offset = np.array([0, 0, 0, self.height], dtype=np.float32)

        verts: List[Vector4D] = []
        verts.extend([v - offset for v in base])  # bottom simplex
        verts.extend([v + offset for v in base])  # top simplex
        self._base_vertices = verts

        # Edges: within each simplex plus connecting pairs
        self._edges: List[Tuple[int, int]] = []
        # Bottom simplex edges
        for i in range(5):
            for j in range(i + 1, 5):
                self._edges.append((i, j))
        # Top simplex edges
        for i in range(5, 10):
            for j in range(i + 1, 10):
                self._edges.append((i, j))
        # Vertical connections
        for i in range(5):
            self._edges.append((i, i + 5))

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
