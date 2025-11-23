"""Spherinder: 3D sphere extruded along the 4th dimension (W)."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Spherinder(Shape4D):
    """Approximate spherinder surface using latitude/longitude rings duplicated in W."""

    def __init__(
        self,
        radius: float = 1.0,
        height: float = 1.0,
        segments: int = 24,
        stacks: int = 12,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.radius = float(radius)
        self.height = float(height)
        self.segments = max(8, int(segments))
        self.stacks = max(4, int(stacks))
        self.auto_spin_enabled = True

        w_offsets = (-self.height / 2.0, self.height / 2.0)
        verts: List[Vector4D] = []
        for w in w_offsets:
            for i in range(self.stacks + 1):
                phi = math.pi * i / self.stacks  # 0..pi
                sin_phi = math.sin(phi)
                cos_phi = math.cos(phi)
                for j in range(self.segments):
                    theta = 2.0 * math.pi * j / self.segments
                    x = self.radius * math.cos(theta) * sin_phi
                    y = self.radius * math.sin(theta) * sin_phi
                    z = self.radius * cos_phi
                    verts.append(np.array([x, y, z, w], dtype=np.float32))
        self._base_vertices = verts

        # Connect along theta, along phi, and between w layers
        self._edges: List[Tuple[int, int]] = []
        ring_size = (self.stacks + 1) * self.segments
        for layer in range(2):
            base = layer * ring_size
            for i in range(self.stacks + 1):
                for j in range(self.segments):
                    idx = base + i * self.segments + j
                    # theta wrap
                    idx_theta = base + i * self.segments + ((j + 1) % self.segments)
                    self._edges.append((idx, idx_theta))
                    # phi connection (except last stack)
                    if i < self.stacks:
                        idx_phi = base + (i + 1) * self.segments + j
                        self._edges.append((idx, idx_phi))
        # Connect corresponding points between W layers
        for i in range(ring_size):
            self._edges.append((i, i + ring_size))

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
        self.rotate(xy=0.15 * dt, xw=0.18 * dt, yw=0.14 * dt, zw=0.1 * dt)
