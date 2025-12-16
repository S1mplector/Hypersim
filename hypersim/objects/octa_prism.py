"""4D prism over a 3D octahedron (cross polytope)."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class OctaPrism(Shape4D):
    """Two octahedra separated along W and linked vertex-to-vertex."""

    def __init__(self, size: float = 1.0, height: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.size = float(size)
        self.height = float(height)
        self.auto_spin_enabled = False
        self.spin_rates = {"xy": 0.32, "xw": 0.36, "yw": 0.24, "zw": 0.18}

        # Octahedron vertices on axes
        base = np.array(
            [
                [1, 0, 0],
                [-1, 0, 0],
                [0, 1, 0],
                [0, -1, 0],
                [0, 0, 1],
                [0, 0, -1],
            ],
            dtype=np.float32,
        )
        base *= self.size / 2.0
        w_offset = self.height / 2.0

        self._base_vertices: List[Vector4D] = []
        for w in (-w_offset, w_offset):
            for v in base:
                self._base_vertices.append(np.array([v[0], v[1], v[2], w], dtype=np.float32))

        edges: List[Tuple[int, int]] = []
        # Octahedron edges: each vertex connects to four others (all but its opposite)
        def add_layer_edges(offset: int) -> None:
            opp = {0: 1, 1: 0, 2: 3, 3: 2, 4: 5, 5: 4}
            for i in range(6):
                for j in range(i + 1, 6):
                    if j == opp[i]:
                        continue
                    edges.append((offset + i, offset + j))

        add_layer_edges(0)
        add_layer_edges(6)

        # Vertical links between corresponding vertices
        for i in range(6):
            edges.append((i, i + 6))

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
