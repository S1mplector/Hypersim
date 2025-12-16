"""Truncated Tesseract - a uniform 4-polytope.

The truncated tesseract is formed by truncating (cutting off) the vertices
of a tesseract. It has 64 vertices, 128 edges, 88 faces, and 24 cells.
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class TruncatedTesseract(Shape4D):
    """Truncated Tesseract - tesseract with cut corners.
    
    The truncation operation cuts off the vertices of the tesseract,
    replacing each vertex with a tetrahedron. The result is a uniform
    4-polytope with:
    - 64 vertices
    - 128 edges
    - 88 faces (64 triangles + 24 octagons)
    - 24 cells (8 truncated cubes + 16 tetrahedra)
    
    Vertices are at all permutations of (±1, ±(√2-1), ±(√2-1), ±(√2-1))
    and similar coordinates.
    """
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a truncated tesseract.
        
        Args:
            size: Overall scale
            **kwargs: Passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        # Truncation parameter
        sqrt2 = np.sqrt(2)
        t = sqrt2 - 1  # Truncation depth
        
        verts_set = set()
        
        # Generate vertices
        # Each original tesseract vertex (±1, ±1, ±1, ±1) becomes 4 vertices
        # by moving along each adjacent edge
        for s0 in [-1, 1]:
            for s1 in [-1, 1]:
                for s2 in [-1, 1]:
                    for s3 in [-1, 1]:
                        # Original vertex at (s0, s1, s2, s3)
                        # Truncated vertices along each axis
                        verts_set.add((s0, s1 * t, s2 * t, s3 * t))
                        verts_set.add((s0 * t, s1, s2 * t, s3 * t))
                        verts_set.add((s0 * t, s1 * t, s2, s3 * t))
                        verts_set.add((s0 * t, s1 * t, s2 * t, s3))
        
        # Convert to numpy arrays and scale
        verts: List[Vector4D] = [
            np.array(v, dtype=np.float32) * self.size
            for v in sorted(verts_set)
        ]
        self._base_vertices = verts
        
        # Generate edges
        edges: List[Tuple[int, int]] = []
        edge_length = 2 * t * self.size  # Expected edge length
        tolerance = 0.15 * edge_length
        
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                dist = np.linalg.norm(verts[i] - verts[j])
                if abs(dist - edge_length) < tolerance:
                    edges.append((i, j))
        
        # Also add longer edges for the octagonal faces
        long_edge = 2 * (1 - t) * self.size
        for i in range(len(verts)):
            for j in range(i + 1, len(verts)):
                dist = np.linalg.norm(verts[i] - verts[j])
                if abs(dist - long_edge) < tolerance:
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
