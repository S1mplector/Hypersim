"""Regular 600-cell (hexacosichoron) wireframe."""
from __future__ import annotations

import math
import itertools
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class SixHundredCell(Shape4D):
    """Regular 600-cell with 120 vertices and 720 edges."""

    def __init__(self, size: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.size = float(size)
        self.auto_spin_enabled = False  # driven by its own update()
        self.spin_rates = {"xy": 0.35, "xw": 0.45, "yw": 0.3, "zw": 0.25}

        phi = (1.0 + math.sqrt(5.0)) / 2.0
        a = 0.5
        b = phi / 2.0
        c = 1.0 / (2.0 * phi)

        verts: List[Vector4D] = []

        # Type 1: axis-aligned vertices
        for axis in range(4):
            for sign in (-1.0, 1.0):
                v = np.zeros(4, dtype=np.float32)
                v[axis] = sign
                verts.append(v)

        # Type 2: all-sign combinations of (1/2, 1/2, 1/2, 1/2)
        for signs in itertools.product((-1.0, 1.0), repeat=4):
            verts.append(np.array([s * a for s in signs], dtype=np.float32))

        # Type 3: even permutations of (0, 1/2, phi/2, 1/(2phi)) with all sign flips
        base_vals = [0.0, a, b, c]

        def is_even_perm(p: Tuple[int, int, int, int]) -> bool:
            inv = 0
            for i in range(len(p)):
                for j in range(i + 1, len(p)):
                    if p[i] > p[j]:
                        inv += 1
            return inv % 2 == 0

        perms = [p for p in set(itertools.permutations(range(4))) if is_even_perm(p)]
        for perm in perms:
            reordered = [base_vals[i] for i in perm]
            for signs in itertools.product((-1.0, 1.0), repeat=3):
                k = 0
                v: List[float] = []
                for val in reordered:
                    if abs(val) < 1e-8:
                        v.append(0.0)
                    else:
                        v.append(val * signs[k])
                        k += 1
                verts.append(np.array(v, dtype=np.float32))

        # Deduplicate any numerical duplicates
        unique: List[Vector4D] = []
        seen = set()
        for v in verts:
            key = tuple(np.round(v, 6))
            if key in seen:
                continue
            seen.add(key)
            unique.append(v)

        if len(unique) != 120:
            raise ValueError(f"Expected 120 vertices for 600-cell, got {len(unique)}")

        # Scale so that the shortest edge ~ size
        verts_np = np.stack(unique, axis=0)
        dist = np.linalg.norm(verts_np[:, None, :] - verts_np[None, :, :], axis=2)
        mask = dist > 1e-6
        min_edge = float(dist[mask].min())
        scale = self.size / min_edge if min_edge > 0 else 1.0
        self._base_vertices: List[Vector4D] = [v * scale for v in unique]

        # Compute edges by connecting vertices at the shortest edge length (with slack)
        verts_np = np.stack(self._base_vertices, axis=0)
        dist = np.linalg.norm(verts_np[:, None, :] - verts_np[None, :, :], axis=2)
        mask = dist > 1e-6
        edge_len = float(dist[mask].min())
        tol = edge_len * 1.05
        edges: List[Tuple[int, int]] = []
        n = len(self._base_vertices)
        for i in range(n):
            for j in range(i + 1, n):
                if dist[i, j] <= tol:
                    edges.append((i, j))
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
        """Gentle autorotation for standalone demos."""
        self.rotate(
            xy=self.spin_rates.get("xy", 0.0) * dt,
            xw=self.spin_rates.get("xw", 0.0) * dt,
            yw=self.spin_rates.get("yw", 0.0) * dt,
            zw=self.spin_rates.get("zw", 0.0) * dt,
        )
