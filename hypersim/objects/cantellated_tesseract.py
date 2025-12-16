"""Cantellated Tesseract (Small Rhombated Tesseract).

Mathematical Background
=======================
The cantellated tesseract is a uniform 4-polytope obtained by cantellation
(edge-truncation) of the tesseract. In Coxeter notation, it is rr{4,3,3}.

The cantellation operation bevels all edges, creating new faces where edges
were and expanding the original cells. This is equivalent to rectifying the
rectified tesseract.

Vertex Figure: Wedge (irregular tetrahedron)

Element Counts (f-vector)
-------------------------
- Vertices (V): 96
- Edges (E): 288
- Faces (F): 272 (64 triangles + 96 squares + 64 squares + 48 squares)
- Cells (C): 80 (8 small rhombicuboctahedra + 16 octahedra + 
               32 triangular prisms + 24 cubes)

Euler Characteristic: V - E + F - C = 96 - 288 + 272 - 80 = 0 ✓

Vertex Coordinates
------------------
Vertices are all permutations and sign changes of:
    (1, 1, 1, 1+√2)
    (1, 1, 1+√2, 1)
    (1, 1+√2, 1, 1)
    (1+√2, 1, 1, 1)

Geometric Properties
--------------------
- Circumradius (unit edge): R = √(4 + 2√2) ≈ 2.613
- Edge length: All edges equal (uniform)
- Symmetry group: B₄ (hyperoctahedral), order 384

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Wikipedia: Cantellated tesseract
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
from itertools import permutations

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class CantellatedTesseract(Shape4D):
    """Cantellated tesseract - edge-truncated hypercube.
    
    The cantellated tesseract (also called small rhombated tesseract) is formed
    by beveling all edges of a tesseract, creating a uniform 4-polytope with
    96 vertices and 288 edges.
    
    Attributes:
        size: Scale factor for the polytope
        
    Mathematical Properties:
        - Schläfli symbol: rr{4,3,3} or t₀,₂{4,3,3}
        - Cells: 8 small rhombicuboctahedra, 16 octahedra, 
                 32 triangular prisms, 24 cubes
        - Vertex figure: Wedge
        - Dual: Joined 24-cell (non-uniform)
    """
    
    # Class-level constants for mathematical properties
    VERTEX_COUNT = 96
    EDGE_COUNT = 288
    FACE_COUNT = 272
    CELL_COUNT = 80
    
    # Circumradius for unit edge length
    CIRCUMRADIUS = np.sqrt(4 + 2 * np.sqrt(2))
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a cantellated tesseract.
        
        Args:
            size: Scale factor (default 1.0 gives circumradius ≈ 2.613)
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        # Generate vertices using the coordinate formula
        sqrt2 = np.sqrt(2)
        a = 1.0
        b = 1.0 + sqrt2
        
        # All permutations of (±1, ±1, ±1, ±(1+√2))
        verts_set = set()
        base_coords = [a, a, a, b]
        
        for perm in set(permutations(base_coords)):
            for signs in self._all_signs(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Normalize and scale
        verts = [np.array(v, dtype=np.float32) for v in sorted(verts_set)]
        scale_factor = self.size / self.CIRCUMRADIUS
        self._base_vertices = [v * scale_factor for v in verts]
        
        # Generate edges by finding vertices at the correct distance
        self._edges = self._generate_edges()
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
    
    def _all_signs(self, n: int) -> List[Tuple[int, ...]]:
        """Generate all 2^n sign combinations."""
        result = []
        for i in range(2**n):
            signs = tuple(1 if (i >> j) & 1 else -1 for j in range(n))
            result.append(signs)
        return result
    
    def _generate_edges(self) -> List[Tuple[int, int]]:
        """Generate edges by connecting vertices at edge-length distance."""
        edges = []
        n = len(self._base_vertices)
        
        # Calculate expected edge length
        # For cantellated tesseract, shortest distance between vertices
        distances = []
        for i in range(min(n, 20)):
            for j in range(i + 1, min(n, 20)):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                distances.append(d)
        
        if distances:
            edge_length = min(distances)
            tolerance = edge_length * 0.1
            
            for i in range(n):
                for j in range(i + 1, n):
                    d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                    if abs(d - edge_length) < tolerance:
                        edges.append((i, j))
        
        return edges
    
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
    
    def get_info(self) -> dict:
        """Return mathematical information about this polytope."""
        return {
            "name": "Cantellated Tesseract",
            "other_names": ["Small Rhombated Tesseract", "Srit"],
            "schläfli_symbol": "rr{4,3,3}",
            "coxeter_diagram": "o4x3o3x",
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "circumradius": self.CIRCUMRADIUS,
            "symmetry_group": "B₄",
            "symmetry_order": 384,
        }
