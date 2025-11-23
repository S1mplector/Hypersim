"""24-cell (icositetrachoron) implementation."""
from __future__ import annotations

import itertools
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class TwentyFourCell(Shape4D):
    """Self-dual regular 4-polytope with 24 vertices and 96 edges."""

    def __init__(self, size: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)

        # Base vertices: 8 axis vertices ±1 and 16 half-vertices (±1/2, ±1/2, ±1/2, ±1/2)
        verts: List[Vector4D] = []
        for axis in range(4):
            for sign in (-1.0, 1.0):
                v = np.zeros(4, dtype=np.float32)
                v[axis] = sign
                verts.append(v)

        for signs in itertools.product((-0.5, 0.5), repeat=4):
            verts.append(np.array(signs, dtype=np.float32))

        # Scale all vertices; base edge length is 1, so scaling also scales edges
        self._base_vertices: List[Vector4D] = [v * self.size for v in verts]

        # Edges connect vertices at distance == size (tolerance-based)
        self._edges: List[Tuple[int, int]] = []
        n = len(self._base_vertices)
        tol = 1e-4 * max(1.0, self.size)
        target = self.size
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if np.isclose(dist, target, atol=tol, rtol=1e-5):
                    self._edges.append((i, j))

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
        # Gentle autonomous rotation for demos
        self.rotate(xy=0.35 * dt, xw=0.25 * dt, yw=0.2 * dt, zw=0.18 * dt)
