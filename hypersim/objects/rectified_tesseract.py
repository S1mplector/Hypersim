"""Rectified tesseract (4D cuboctachoron)."""
from __future__ import annotations

import itertools
import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class RectifiedTesseract(Shape4D):
    """Rectified tesseract with 24 vertices and 96 edges.

    Vertices are all permutations of (±1, ±1, 0, 0) scaled to the target edge length.
    """

    def __init__(self, size: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)

        verts: List[Vector4D] = []
        for signs in itertools.product((-1.0, 1.0), repeat=2):
            for perm in set(itertools.permutations([signs[0], signs[1], 0.0, 0.0])):
                verts.append(np.array(perm, dtype=np.float32))

        # Base edge length is sqrt(2); scale so edge ~= size
        scale = self.size / math.sqrt(2.0)
        self._base_vertices = [v * scale for v in verts]

        # Edges connect vertices with distance == size (within tolerance)
        self._edges: List[Tuple[int, int]] = []
        n = len(self._base_vertices)
        tol = 1e-4 * max(1.0, self.size)
        for i in range(n):
            for j in range(i + 1, n):
                dist = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if np.isclose(dist, self.size, atol=tol, rtol=1e-4):
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
        self.rotate(xy=0.32 * dt, xw=0.28 * dt, yw=0.22 * dt, zw=0.2 * dt)
