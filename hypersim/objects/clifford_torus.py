"""Clifford torus embedded in 4D space."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class CliffordTorus(Shape4D):
    """Clifford torus S1 x S1 embedded in S3 ⊂ R4, discretized as a grid."""

    def __init__(self, segments_u: int = 32, segments_v: int = 16, size: float = 1.0, **kwargs):
        if segments_u < 3 or segments_v < 3:
            raise ValueError("segments_u and segments_v must be >= 3")
        super().__init__(**kwargs)
        self.segments_u = int(segments_u)
        self.segments_v = int(segments_v)
        self.size = float(size)

        self._base_vertices: List[Vector4D] = []
        inv_root2 = 1.0 / math.sqrt(2.0)
        for i in range(self.segments_u):
            u = 2.0 * math.pi * i / self.segments_u
            cu, su = math.cos(u), math.sin(u)
            for j in range(self.segments_v):
                v = 2.0 * math.pi * j / self.segments_v
                cv, sv = math.cos(v), math.sin(v)
                self._base_vertices.append(
                    np.array(
                        [
                            inv_root2 * cu,
                            inv_root2 * su,
                            inv_root2 * cv,
                            inv_root2 * sv,
                        ],
                        dtype=np.float32,
                    )
                    * self.size
                )

        # Edges wrap around in both directions
        self._edges: List[Tuple[int, int]] = []
        for i in range(self.segments_u):
            for j in range(self.segments_v):
                idx = i * self.segments_v + j
                idx_u = ((i + 1) % self.segments_u) * self.segments_v + j
                idx_v = i * self.segments_v + ((j + 1) % self.segments_v)
                self._edges.append((idx, idx_u))
                self._edges.append((idx, idx_v))

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
        # Smooth rotations to show the torus embedding
        self.rotate(xy=0.25 * dt, zw=0.3 * dt, xw=0.22 * dt, yw=0.18 * dt)
