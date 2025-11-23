"""Sparse frame of a 5D hypercube (penteract) projected into 4D."""
from __future__ import annotations

import itertools
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class PenteractFrame(Shape4D):
    """Constructs a 4D projection of a 5D hypercube by omitting the 5th coord visually."""

    def __init__(self, size: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)
        # Vertices: all combinations of (±1, ±1, ±1, ±1, ±1) scaled
        verts5d = []
        for coords in itertools.product((-1.0, 1.0), repeat=5):
            verts5d.append(np.array(coords, dtype=np.float32))
        scale = self.size / 2.0
        verts5d = [v * scale for v in verts5d]

        # Project 5D -> 4D by dropping last coord into a scale factor
        self._base_vertices: List[Vector4D] = []
        for v in verts5d:
            w5 = v[4]
            projected = v[:4] * (1.0 / (1.0 + abs(w5) * 0.4))
            self._base_vertices.append(projected)

        # Edges: connect vertices differing in exactly one of the 5 coords
        self._edges: List[Tuple[int, int]] = []
        n = len(verts5d)
        for i in range(n):
            for j in range(i + 1, n):
                if np.sum(verts5d[i] != verts5d[j]) == 1:
                    self._edges.append((i, j))

        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
        self.line_width = 2

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
        self.rotate(xy=0.2 * dt, xw=0.18 * dt, yw=0.16 * dt, zw=0.14 * dt)
