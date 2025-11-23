"""Möbius band embedded in 4D."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Mobius4D(Shape4D):
    """Möbius strip embedded in 4D to avoid self-intersection in 3D."""

    def __init__(
        self,
        radius: float = 1.0,
        width: float = 0.4,
        segments_u: int = 64,
        segments_v: int = 12,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.width = float(width)
        self.segments_u = max(16, int(segments_u))
        self.segments_v = max(4, int(segments_v))
        self.auto_spin_enabled = True

        # Build vertex grid
        verts: List[Vector4D] = []
        for i in range(self.segments_u):
            u = 2.0 * math.pi * i / self.segments_u
            cos_u = math.cos(u)
            sin_u = math.sin(u)
            twist = u / 2.0
            cos_twist = math.cos(twist)
            sin_twist = math.sin(twist)
            for j in range(self.segments_v):
                v = self.width * (j / (self.segments_v - 1) - 0.5)
                x = (self.radius + v * cos_twist) * cos_u
                y = (self.radius + v * cos_twist) * sin_u
                z = v * sin_twist
                # Add 4th-dim displacement to separate the twist cleanly
                w = v * math.sin(twist + math.pi / 4.0) * 0.8
                verts.append(np.array([x, y, z, w], dtype=np.float32))
        self._base_vertices = verts

        # Edges along u and v with Möbius wrapping
        self._edges: List[Tuple[int, int]] = []
        for i in range(self.segments_u):
            for j in range(self.segments_v):
                idx = i * self.segments_v + j
                # v-direction (across width)
                if j + 1 < self.segments_v:
                    self._edges.append((idx, idx + 1))
                # u-direction (along length) with twist on wrap
                next_i = (i + 1) % self.segments_u
                if i + 1 < self.segments_u:
                    next_idx = next_i * self.segments_v + j
                    self._edges.append((idx, next_idx))
                else:
                    # wrap with reversed v index to implement the Möbius twist
                    next_idx = 0 * self.segments_v + (self.segments_v - 1 - j)
                    self._edges.append((idx, next_idx))

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
        self.rotate(xy=0.12 * dt, xw=0.15 * dt, yw=0.12 * dt, zw=0.1 * dt)
