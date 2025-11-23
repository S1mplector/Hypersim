"""Hypercube lattice (grid) in 4D."""
from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class HypercubeGrid(Shape4D):
    """4D hypercubic lattice with configurable divisions along each axis.

    Vertices are placed on a regular grid in [-size, size]^4. Edges connect
    immediate neighbors along each axis (Manhattan distance 1 in grid space).
    """

    def __init__(self, divisions: int = 3, size: float = 1.0, **kwargs):
        if divisions < 2:
            raise ValueError("divisions must be >= 2 for a grid")
        super().__init__(**kwargs)
        self.divisions = int(divisions)
        self.size = float(size)
        self.auto_spin_enabled = True

        step = 2.0 * self.size / (self.divisions - 1)
        coords = np.linspace(-self.size, self.size, self.divisions, dtype=np.float32)

        self._base_vertices: List[Vector4D] = []
        index_map: Dict[Tuple[int, int, int, int], int] = {}

        for idx, (i, j, k, l) in enumerate(itertools.product(range(self.divisions), repeat=4)):
            v = np.array(
                [coords[i], coords[j], coords[k], coords[l]], dtype=np.float32
            )
            self._base_vertices.append(v)
            index_map[(i, j, k, l)] = idx

        self._edges: List[Tuple[int, int]] = []
        # Connect neighbors along each axis if within bounds
        for i, j, k, l in itertools.product(range(self.divisions), repeat=4):
            src = index_map[(i, j, k, l)]
            if i + 1 < self.divisions:
                self._edges.append((src, index_map[(i + 1, j, k, l)]))
            if j + 1 < self.divisions:
                self._edges.append((src, index_map[(i, j + 1, k, l)]))
            if k + 1 < self.divisions:
                self._edges.append((src, index_map[(i, j, k + 1, l)]))
            if l + 1 < self.divisions:
                self._edges.append((src, index_map[(i, j, k, l + 1)]))

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
        # Add a slow rotation to highlight the lattice structure
        self.rotate(xy=0.18 * dt, zw=0.25 * dt, xw=0.16 * dt, yw=0.14 * dt)
