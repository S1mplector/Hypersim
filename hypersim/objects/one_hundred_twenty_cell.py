"""Regular 120-cell (hecatonicosachoron) implemented as the dual of the 600-cell.

This implementation constructs the 120-cell as the dual of the existing
regular 600-cell:

- Start from the vertices and edges of a regular 600-cell.
- Recover its 600 tetrahedral cells as 4-cliques in the edge graph.
- Take the centroid of each tetrahedral cell as a vertex of the dual 120-cell.
- Connect two dual vertices by an edge when their corresponding tetrahedra
  in the 600-cell share a common triangular face.

The resulting wireframe is a geometrically correct regular 120-cell up to
uniform scaling; we finally rescale so that its shortest edge has length 1
at unit size, and then scale by the requested `size`.
"""
from __future__ import annotations

import itertools
from typing import List, Tuple

import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D
from .six_hundred_cell import SixHundredCell


class OneHundredTwentyCell(Shape4D):
    """Regular 120-cell (dual of the 600-cell), represented as a wireframe."""

    # Class-level cache so we only do the heavy dual construction once
    _cached_vertices: List[Vector4D] | None = None
    _cached_edges: List[Tuple[int, int]] | None = None

    def __init__(self, size: float = 1.0, **kwargs) -> None:
        super().__init__(**kwargs)
        self.size = float(size)

        if OneHundredTwentyCell._cached_vertices is None:
            verts, edges = self._build_dual_from_600_cell()
            OneHundredTwentyCell._cached_vertices = verts
            OneHundredTwentyCell._cached_edges = edges

        # Scale vertices so that the shortest edge has length ~= size
        base_verts = OneHundredTwentyCell._cached_vertices
        assert base_verts is not None
        verts_np = np.stack(base_verts, axis=0)
        dist = np.linalg.norm(verts_np[:, None, :] - verts_np[None, :, :], axis=2)
        mask = dist > 1e-6
        min_edge = float(dist[mask].min()) if np.any(mask) else 1.0
        scale = self.size / min_edge if min_edge > 0 else 1.0

        self._base_vertices: List[Vector4D] = [v * scale for v in base_verts]
        self._edges: List[Tuple[int, int]] = list(OneHundredTwentyCell._cached_edges or [])
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []

        # Gentle autonomous rotation for demos (can be overridden externally)
        self.spin_rates = {"xy": 0.30, "xw": 0.40, "yw": 0.25, "zw": 0.20}

    @classmethod
    def _build_dual_from_600_cell(cls) -> Tuple[List[Vector4D], List[Tuple[int, int]]]:
        """Construct 120-cell vertices/edges as the dual of a regular 600-cell.

        Returns:
            (vertices, edges) where vertices is a list of 4D vectors and
            edges is a list of index pairs.
        """
        # Start from a unit-edge regular 600-cell
        src = SixHundredCell(size=1.0)
        verts_600: List[Vector4D] = list(src.vertices)
        edges_600: List[Tuple[int, int]] = list(src.edges)
        n = len(verts_600)

        # Build adjacency sets for the 600-cell edge graph
        adj: List[set[int]] = [set() for _ in range(n)]
        for i, j in edges_600:
            adj[i].add(j)
            adj[j].add(i)

        # Enumerate all tetrahedral cells as 4-cliques in the adjacency graph.
        # For each i < j < k < l, require that all 6 edges are present.
        cells: List[Tuple[int, int, int, int]] = []
        for i in range(n):
            neigh_i = [j for j in adj[i] if j > i]
            for j in neigh_i:
                common_ij = adj[i].intersection(adj[j])
                for k in [c for c in common_ij if c > j]:
                    common_ijk = common_ij.intersection(adj[k])
                    for l in [c for c in common_ijk if c > k]:
                        # i < j < k < l and all pairs are adjacent by construction
                        cells.append((i, j, k, l))

        if len(cells) != 600:
            raise ValueError(f"Expected 600 tetrahedral cells in 600-cell, got {len(cells)}")

        # Dual vertices: centroids of tetrahedral cells
        verts_120: List[Vector4D] = []
        verts_600_np = np.stack(verts_600, axis=0)
        for (i, j, k, l) in cells:
            centroid = (
                verts_600_np[i]
                + verts_600_np[j]
                + verts_600_np[k]
                + verts_600_np[l]
            ) / 4.0
            verts_120.append(np.array(centroid, dtype=np.float32))

        # Build dual edges: two dual vertices are adjacent iff their
        # corresponding tetrahedra share a triangular face (3 common vertices).
        face_to_cells: dict[Tuple[int, int, int], List[int]] = {}
        for cell_index, (i, j, k, l) in enumerate(cells):
            for tri in itertools.combinations((i, j, k, l), 3):
                key = tuple(sorted(tri))
                face_to_cells.setdefault(key, []).append(cell_index)

        edge_set: set[Tuple[int, int]] = set()
        for cell_indices in face_to_cells.values():
            if len(cell_indices) == 2:
                a, b = cell_indices
                if a > b:
                    a, b = b, a
                edge_set.add((a, b))

        edges_120 = sorted(edge_set)

        # We expect 600 vertices and 1200 edges in the regular 120-cell
        # (up to numerical tolerance in construction).
        if len(verts_120) != 600:
            raise ValueError(f"Expected 600 vertices in 120-cell, got {len(verts_120)}")
        if len(edges_120) != 1200:
            raise ValueError(f"Expected 1200 edges in 120-cell, got {len(edges_120)}")

        # Normalize so that the shortest edge has length 1.0
        verts_np = np.stack(verts_120, axis=0)
        dist = np.linalg.norm(verts_np[:, None, :] - verts_np[None, :, :], axis=2)
        mask = dist > 1e-6
        min_edge = float(dist[mask].min()) if np.any(mask) else 1.0
        scale = 1.0 / min_edge if min_edge > 0 else 1.0
        verts_scaled: List[Vector4D] = [v * scale for v in verts_120]

        return verts_scaled, edges_120

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
        """Gentle autorotation for visualization demos."""
        self.rotate(
            xy=self.spin_rates.get("xy", 0.0) * dt,
            xw=self.spin_rates.get("xw", 0.0) * dt,
            yw=self.spin_rates.get("yw", 0.0) * dt,
            zw=self.spin_rates.get("zw", 0.0) * dt,
        )
