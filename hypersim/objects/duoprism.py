"""Duoprism P(m) x P(n) (Cartesian product of two polygons) in 4D."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Duoprism(Shape4D):
    """Duoprism generated from two regular polygons of sizes m and n.

    Vertices are laid out on a 4D torus: (cos θ_i, sin θ_i, cos φ_j, sin φ_j).
    Edges connect adjacent vertices in each polygonal ring.
    """

    def __init__(self, m: int = 3, n: int = 4, size: float = 1.0, **kwargs):
        if m < 3 or n < 3:
            raise ValueError("m and n must be >= 3 for a valid duoprism")
        super().__init__(**kwargs)
        self.m = int(m)
        self.n = int(n)
        self.size = float(size)

        # Build vertices
        self._base_vertices: List[Vector4D] = []
        for i in range(self.m):
            theta = 2.0 * math.pi * i / self.m
            x = math.cos(theta)
            y = math.sin(theta)
            for j in range(self.n):
                phi = 2.0 * math.pi * j / self.n
                z = math.cos(phi)
                w = math.sin(phi)
                self._base_vertices.append(
                    np.array([x, y, z, w], dtype=np.float32) * self.size
                )

        # Edges: wrap in each polygon direction
        self._edges: List[Tuple[int, int]] = []
        for i in range(self.m):
            for j in range(self.n):
                idx = i * self.n + j
                idx_next_i = ((i + 1) % self.m) * self.n + j
                idx_next_j = i * self.n + ((j + 1) % self.n)
                self._edges.append((idx, idx_next_i))
                self._edges.append((idx, idx_next_j))

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
        # Subtle rotation to illustrate 4D torus structure
        self.rotate(xy=0.25 * dt, zw=0.35 * dt, xw=0.2 * dt, yw=0.18 * dt)
