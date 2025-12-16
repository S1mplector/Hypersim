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

        # Generate faces: each face is a square in 4D (4 vertices differing in 2 coords)
        # A tesseract has 24 square faces
        self._faces: List[Tuple[int, ...]] = self._generate_faces(idx_to_vec)
        
        # Generate cells: each cell is a cube (8 vertices differing in 3 coords)
        # A tesseract has 8 cubic cells
        self._cells: List[Tuple[int, ...]] = self._generate_cells(idx_to_vec)

    def _generate_faces(self, idx_to_vec) -> List[Tuple[int, ...]]:
        """Generate the 24 square faces of the tesseract."""
        faces = []
        # For each pair of axes, we have faces in that plane
        axes = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        for ax1, ax2 in axes:
            # Fixed axes are the other two
            other_axes = [i for i in range(4) if i not in (ax1, ax2)]
            # For each combination of fixed values
            for f0 in [0, 1]:
                for f1 in [0, 1]:
                    # Get the 4 vertices of this face
                    face_verts = []
                    for v0 in [0, 1]:
                        for v1 in [0, 1]:
                            coords = [0, 0, 0, 0]
                            coords[ax1] = v0
                            coords[ax2] = v1
                            coords[other_axes[0]] = f0
                            coords[other_axes[1]] = f1
                            idx = (coords[0] << 3) | (coords[1] << 2) | (coords[2] << 1) | coords[3]
                            face_verts.append(idx)
                    # Order vertices for proper winding (square)
                    faces.append((face_verts[0], face_verts[1], face_verts[3], face_verts[2]))
        return faces

    def _generate_cells(self, idx_to_vec) -> List[Tuple[int, ...]]:
        """Generate the 8 cubic cells of the tesseract."""
        cells = []
        # Each cell is defined by fixing one axis at 0 or 1
        for fixed_axis in range(4):
            for fixed_val in [0, 1]:
                cell_verts = []
                for bits in range(8):  # 2^3 = 8 vertices per cube
                    coords = [0, 0, 0, 0]
                    bit_idx = 0
                    for axis in range(4):
                        if axis == fixed_axis:
                            coords[axis] = fixed_val
                        else:
                            coords[axis] = (bits >> bit_idx) & 1
                            bit_idx += 1
                    idx = (coords[0] << 3) | (coords[1] << 2) | (coords[2] << 1) | coords[3]
                    cell_verts.append(idx)
                cells.append(tuple(cell_verts))
        return cells

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
