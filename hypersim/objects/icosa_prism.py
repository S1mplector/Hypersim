"""Prism over a 3D icosahedron (extruded along W)."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class IcosaPrism(Shape4D):
    """Icosahedron prism with 24 vertices and 90 edges."""

    def __init__(self, size: float = 1.0, height: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)
        self.height = float(height)
        phi = (1.0 + 5.0**0.5) / 2.0

        # Base icosahedron vertices (centered)
        verts3 = [
            (-1,  phi, 0), (1,  phi, 0), (-1, -phi, 0), (1, -phi, 0),
            (0, -1,  phi), (0, 1,  phi), (0, -1, -phi), (0, 1, -phi),
            (phi, 0, -1), (phi, 0, 1), (-phi, 0, -1), (-phi, 0, 1),
        ]
        verts3 = np.array(verts3, dtype=np.float32)
        verts3 /= np.linalg.norm(verts3[0])  # normalize so edge length ~1.051
        verts3 *= self.size / 1.7  # scale so edge ~size

        half_h = self.height / 2.0
        verts: List[Vector4D] = []
        for w in (-half_h, half_h):
            for v in verts3:
                verts.append(np.array([v[0], v[1], v[2], w], dtype=np.float32))
        self._base_vertices = verts

        # Standard icosahedron edges (indices 0..11)
        base_edges = [
            (0, 1), (0, 5), (0, 7), (0, 10), (0, 11),
            (1, 5), (1, 7), (1, 8), (1, 9),
            (2, 3), (2, 4), (2, 6), (2, 10), (2, 11),
            (3, 4), (3, 6), (3, 8), (3, 9),
            (4, 5), (4, 9), (4, 11),
            (5, 9), (5, 11),
            (6, 7), (6, 8), (6, 10),
            (7, 8), (7, 10),
            (8, 9),
            (10, 11),
        ]

        self._edges: List[Tuple[int, int]] = []
        # Edges in bottom and top layers
        for layer in range(2):
            offset = 12 * layer
            for a, b in base_edges:
                self._edges.append((offset + a, offset + b))
        # Vertical edges linking layers
        for i in range(12):
            self._edges.append((i, i + 12))

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
        self.rotate(xy=0.2 * dt, xw=0.18 * dt, yw=0.18 * dt, zw=0.14 * dt)
