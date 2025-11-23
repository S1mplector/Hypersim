"""4D helix/coil for variety."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Helix4D(Shape4D):
    """Parametric 4D helix with linked rotation in W."""

    def __init__(
        self,
        turns: int = 3,
        segments: int = 320,
        radius: float = 1.0,
        pitch: float = 2.0,
        w_amp: float = 1.2,
        wrap: bool = False,
        phase: float = 0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.turns = int(turns)
        self.segments = int(segments)
        self.radius = float(radius)
        self.pitch = float(pitch)
        self.w_amp = float(w_amp)
        self.wrap = wrap
        self.phase = float(phase)
        # Let viewer rotation drive the motion to avoid chaotic folds
        self.auto_spin_enabled = False
        # Center the helix closer to the camera for visibility
        self.position = np.array([0.0, 0.0, 1.2, 0.0], dtype=np.float32)

        verts: List[Vector4D] = []
        total_angle = 2.0 * math.pi * self.turns
        for i in range(self.segments):
            s = i / (self.segments - 1)
            t = total_angle * s + self.phase
            # Classic helix in XYZ
            x = self.radius * math.cos(t)
            y = self.radius * math.sin(t)
            z = self.pitch * (s - 0.5)
            # Linear W drift to keep the path from folding back on itself
            w = self.w_amp * (s - 0.5)
            verts.append(np.array([x, y, z, w], dtype=np.float32))
        self._base_vertices = verts

        self._edges: List[Tuple[int, int]] = [(i, i + 1) for i in range(self.segments - 1)]
        if self.wrap:
            self._edges.append((self.segments - 1, 0))
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
        # Gentle rotation to keep motion visible but not chaotic
        self.rotate(xy=0.08 * dt, xw=0.1 * dt, yw=0.08 * dt, zw=0.06 * dt)
