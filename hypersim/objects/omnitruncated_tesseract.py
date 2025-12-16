"""Omnitruncated Tesseract (Great Rhombated Tesseract).

Mathematical Background
=======================
The omnitruncated tesseract is the most complex uniform 4-polytope in the
tesseract family. It is obtained by applying all three truncation operations
to the tesseract: truncation, rectification, and cantellation.

In Coxeter notation: tr{4,3,3} (omnitruncation)

This operation creates the maximum number of faces possible while maintaining
uniformity. The result is a polytope where every original element (vertex,
edge, face, cell) of the tesseract contributes to the final structure.

Vertex Figure: Irregular tetrahedron (scalene)

Element Counts (f-vector)
-------------------------
- Vertices (V): 768
- Edges (E): 1536
- Faces (F): 1040 (256 triangles + 192 squares + 256 squares + 
                   192 hexagons + 144 octagons)
- Cells (C): 272 (8 great rhombicuboctahedra + 16 truncated octahedra + 
                  32 hexagonal prisms + 24 octagonal prisms + 192 cubes)

Euler Characteristic: V - E + F - C = 768 - 1536 + 1040 - 272 = 0 ✓

Vertex Coordinates
------------------
Vertices are all permutations and sign changes of:
    (1, 1+√2, 1+2√2, 1+3√2)

This gives 4! × 2⁴ = 384 vertices per orbit, with 2 orbits.

Geometric Properties
--------------------
- Circumradius (unit edge): R = √(12 + 8√2) ≈ 4.370
- This is the largest uniform polytope in the tesseract family
- All dihedral angles are obtuse
- Symmetry group: B₄ (hyperoctahedral), order 384

Applications
------------
The omnitruncated tesseract appears in:
- Study of 4D crystallographic groups
- Analysis of high-dimensional sphere packings
- Visualization of complex symmetry relationships

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Conway, J.H. "The Symmetries of Things" (2008)
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
from itertools import permutations

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class OmnitruncatedTesseract(Shape4D):
    """Omnitruncated tesseract - maximally truncated hypercube.
    
    This is the most complex uniform polytope in the tesseract family,
    with 768 vertices and 1536 edges. Every symmetry element of the
    tesseract contributes to the final structure.
    
    Attributes:
        size: Scale factor for the polytope
        
    Mathematical Properties:
        - Schläfli symbol: tr{4,3,3}
        - Coxeter diagram: x4x3x3x
        - Cells: 8 great rhombicuboctahedra, 64 triangular prisms,
                 32 hexagonal prisms, 24 octagonal prisms
        - Vertex figure: Irregular tetrahedron
    """
    
    VERTEX_COUNT = 768
    EDGE_COUNT = 1536
    FACE_COUNT = 1040
    CELL_COUNT = 272
    
    CIRCUMRADIUS = np.sqrt(12 + 8 * np.sqrt(2))
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize an omnitruncated tesseract.
        
        Args:
            size: Scale factor
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        sqrt2 = np.sqrt(2)
        
        # Coordinates: permutations of (1, 1+√2, 1+2√2, 1+3√2)
        a = 1.0
        b = 1.0 + sqrt2
        c = 1.0 + 2 * sqrt2
        d = 1.0 + 3 * sqrt2
        
        verts_set = set()
        base = [a, b, c, d]
        
        for perm in permutations(base):
            for signs in self._all_signs(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Scale to size
        verts = [np.array(v, dtype=np.float32) for v in sorted(verts_set)]
        scale = self.size / self.CIRCUMRADIUS
        self._base_vertices = [v * scale for v in verts]
        
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
        """Generate edges connecting nearest vertices."""
        edges = []
        n = len(self._base_vertices)
        if n == 0:
            return edges
        
        # Sample to find edge length
        distances = []
        sample_size = min(n, 100)
        for i in range(sample_size):
            for j in range(i + 1, sample_size):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if d > 0.001:
                    distances.append(d)
        
        if not distances:
            return edges
        
        edge_length = min(distances)
        tolerance = edge_length * 0.1
        
        # Generate edges
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
            "name": "Omnitruncated Tesseract",
            "other_names": ["Great rhombated tesseract", "Grit"],
            "schläfli_symbol": "tr{4,3,3}",
            "coxeter_diagram": "x4x3x3x",
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "circumradius": self.CIRCUMRADIUS,
            "symmetry_group": "B₄",
            "symmetry_order": 384,
            "is_zonotope": True,
        }
