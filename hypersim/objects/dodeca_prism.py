"""Prism over a 3D dodecahedron (extruded along W)."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class DodecaPrism(Shape4D):
    """Dodecahedron prism with 40 vertices and 120 edges."""

    def __init__(self, size: float = 1.0, height: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.size = float(size)
        self.height = float(height)

        phi = (1.0 + 5.0**0.5) / 2.0
        a, b = 1.0 / phi, 1.0

        verts3 = [
            (-b, -b, -b),
            (-b, -b, b),
            (-b, b, -b),
            (-b, b, b),
            (b, -b, -b),
            (b, -b, b),
            (b, b, -b),
            (b, b, b),
            (0, -a, -phi),
            (0, -a, phi),
            (0, a, -phi),
            (0, a, phi),
            (-a, -phi, 0),
            (-a, phi, 0),
            (a, -phi, 0),
            (a, phi, 0),
            (-phi, 0, -a),
            (phi, 0, -a),
            (-phi, 0, a),
            (phi, 0, a),
        ]
        verts3 = np.array(verts3, dtype=np.float32)
        verts3 /= np.linalg.norm(verts3[0])  # normalize approx edge length 1.051
        verts3 *= self.size / 1.7

        half_h = self.height / 2.0
        verts: List[Vector4D] = []
        for w in (-half_h, half_h):
            for v in verts3:
                verts.append(np.array([v[0], v[1], v[2], w], dtype=np.float32))
        self._base_vertices = verts

        base_edges = [
            (0, 8), (0, 10), (0, 16),
            (1, 8), (1, 11), (1, 18),
            (2, 10), (2, 12), (2, 17),
            (3, 11), (3, 13), (3, 18),
            (4, 8), (4, 14), (4, 17),
            (5, 9), (5, 14), (5, 19),
            (6, 10), (6, 15), (6, 17),
            (7, 11), (7, 15), (7, 19),
            (8, 9), (9, 11), (10, 12), (12, 13),
            (13, 11), (14, 15), (15, 19), (18, 19),
            (16, 17), (16, 18),
        ]

        self._edges: List[Tuple[int, int]] = []
        for layer in range(2):
            offset = 20 * layer
            for a, b in base_edges:
                self._edges.append((offset + a, offset + b))
        for i in range(20):
            self._edges.append((i, i + 20))

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
        self.rotate(xy=0.18 * dt, xw=0.16 * dt, yw=0.16 * dt, zw=0.12 * dt)
