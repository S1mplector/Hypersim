"""4D Hypercube (Tesseract) implementation.

This class defines a 4D hypercube with 16 vertices and 32 edges.
Faces and cells are not strictly required by the current Pygame renderer,
so we provide edges which are sufficient for wireframe rendering.
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Hypercube(Shape4D):
    """A 4D hypercube (tesseract)."""

    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a tesseract.

        Args:
            size: overall scale (edge length is proportional to size)
            **kwargs: forwarded to `Shape4D`
        """
        super().__init__(**kwargs)
        self.size = float(size)
        # Let the shape drive its own iconic spin instead of relying on global auto-spin
        self.auto_spin_enabled = False

        # 16 vertices at all combinations of (±1, ±1, ±1, ±1)
        # Scale them to control overall size
        base = [-1.0, 1.0]
        verts: List[Vector4D] = []
        for x in base:
            for y in base:
                for z in base:
                    for w in base:
                        verts.append(np.array([x, y, z, w], dtype=np.float32))
        # Normalize so that the default edge length is ~2, then scale by size/2 to make edge≈size
        # Edge length between vertices that differ by one axis is 2. So to make edge≈size, multiply by (size/2).
        scale = self.size / 2.0
        self._base_vertices: List[Vector4D] = [v * scale for v in verts]

        # Edges: connect vertices that differ in exactly one coordinate (Hamming distance 1)
        # Index mapping for 4-bit binary to vertex index
        def bits_to_index(bx: int, by: int, bz: int, bw: int) -> int:
            return (bx << 3) | (by << 2) | (bz << 1) | bw

        # Build a mapping from index -> coordinates in {-1,1}
        idx_to_vec = []
        for ix in range(2):
            for iy in range(2):
                for iz in range(2):
                    for iw in range(2):
                        idx_to_vec.append((ix, iy, iz, iw))

        edges: List[Tuple[int, int]] = []
        for index, (ix, iy, iz, iw) in enumerate(idx_to_vec):
            # Flip each axis one at a time to connect neighbors; ensure j>i to avoid duplicates
            neighbors = [
                (1 - ix, iy, iz, iw),
                (ix, 1 - iy, iz, iw),
                (ix, iy, 1 - iz, iw),
                (ix, iy, iz, 1 - iw),
            ]
            for nx, ny, nz, nw in neighbors:
                j = (nx << 3) | (ny << 2) | (nz << 1) | nw
                if j > index:
                    edges.append((index, j))
        self._edges: List[Tuple[int, int]] = edges

        # For now faces and cells are omitted; they can be derived if needed later
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
        """Iconic gentle rotation that always runs, even if global spin is off."""
        self.rotate(
            xy=0.5 * dt,
            xw=0.35 * dt,
            yw=0.3 * dt,
            zw=0.25 * dt,
        )
