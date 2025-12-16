"""Orthogonal circle pair (Hopf link) embedded in 4D."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D, create_vector_4d
from ..core.shape_4d import Shape4D


class HopfLink4D(Shape4D):
    """Two orthogonal circles forming a Hopf link when projected to 3D."""

    def __init__(self, radius: float = 1.0, segments: int = 160, **kwargs) -> None:
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.segments = int(max(segments, 24))
        self.auto_spin_enabled = False
        self.spin_rates = {"xy": 0.22, "xw": 0.32, "yw": 0.26, "zw": 0.18}
        # Give both loops an initial tilt so the projection shows the link
        self.rotate(xy=0.4, xw=0.55, yw=0.35, zw=0.25)

        verts: List[Vector4D] = []
        # Circle A: lies in XY-plane
        for i in range(self.segments):
            t = 2.0 * math.pi * i / self.segments
            verts.append(create_vector_4d(self.radius * math.cos(t), self.radius * math.sin(t), 0.0, 0.0))
        # Circle B: lies in ZW-plane
        for i in range(self.segments):
            t = 2.0 * math.pi * i / self.segments
            verts.append(create_vector_4d(0.0, 0.0, self.radius * math.cos(t), self.radius * math.sin(t)))

        self._base_vertices = verts

        edges: List[Tuple[int, int]] = []
        # Connect loop A
        for i in range(self.segments):
            edges.append((i, (i + 1) % self.segments))
        # Connect loop B
        offset = self.segments
        for i in range(self.segments):
            edges.append((offset + i, offset + (i + 1) % self.segments))
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
