"""4D torus knot embedded in S1 x S1 (wire loop)."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D, create_vector_4d
from ..core.shape_4d import Shape4D


class TorusKnot4D(Shape4D):
    """(p,q) torus knot living on a Clifford torus inside 4D."""

    def __init__(self, p: int = 3, q: int = 5, segments: int = 240, radius: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.p = int(p)
        self.q = int(q)
        self.segments = int(max(segments, 40))
        self.radius = float(radius)
        self.auto_spin_enabled = False
        self.spin_rates = {"xy": 0.28, "xw": 0.4, "yw": 0.34, "zw": 0.22}

        verts: List[Vector4D] = []
        for i in range(self.segments):
            t = 2.0 * math.pi * i / self.segments
            u = self.p * t
            v = self.q * t
            x = self.radius * math.cos(u)
            y = self.radius * math.sin(u)
            z = self.radius * math.cos(v)
            w = self.radius * math.sin(v)
            verts.append(create_vector_4d(x, y, z, w))
        self._base_vertices = verts

        edges: List[Tuple[int, int]] = []
        for i in range(self.segments):
            edges.append((i, (i + 1) % self.segments))
        self._edges = edges
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
        self.rotate(
            xy=self.spin_rates.get("xy", 0.0) * dt,
            xw=self.spin_rates.get("xw", 0.0) * dt,
            yw=self.spin_rates.get("yw", 0.0) * dt,
            zw=self.spin_rates.get("zw", 0.0) * dt,
        )
