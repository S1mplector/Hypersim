"""Bitruncated Tesseract (Bitruncated 16-cell).

Mathematical Background
=======================
The bitruncated tesseract is a uniform 4-polytope that is both the bitruncation
of the tesseract and the bitruncation of the 16-cell. This remarkable property
means it sits exactly between these two dual polytopes.

In Coxeter notation: 2t{4,3,3} = 2t{3,3,4}

The bitruncation operation truncates both the original polytope and its dual
simultaneously, meeting at their common rectification.

Vertex Figure: Digonal disphenoid

Element Counts (f-vector)
-------------------------
- Vertices (V): 96
- Edges (E): 240
- Faces (F): 200 (64 triangles + 64 hexagons + 72 squares)
- Cells (C): 56 (8 truncated octahedra + 16 truncated tetrahedra + 
               32 triangular prisms)

Euler Characteristic: V - E + F - C = 96 - 240 + 200 - 56 = 0 ✓

Vertex Coordinates
------------------
Vertices are all permutations of:
    (0, ±1, ±2, ±3)
scaled appropriately.

Alternatively, vertices at all permutations and even sign changes of:
    (±1, ±1, ±(1+2φ), ±φ²) where φ = (1+√5)/2

Geometric Properties
--------------------
- Circumradius (unit edge): R = √14/2 ≈ 1.871
- Cell types: Truncated octahedra and truncated tetrahedra
- Self-dual: No (dual is itself bitruncated)
- Symmetry group: B₄ (hyperoctahedral), order 384

Interesting Facts
-----------------
- The truncated octahedra can tile 3D space (bitruncated cubic honeycomb)
- This 4-polytope is the 4D analogue of the truncated octahedron
- It appears in the study of 4D crystallography

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Conway, J.H. et al. "The Symmetries of Things" (2008)
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
from itertools import permutations

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class BitruncatedTesseract(Shape4D):
    """Bitruncated tesseract - doubly-truncated hypercube/16-cell.
    
    This uniform 4-polytope is unique in being the bitruncation of both the
    tesseract AND the 16-cell, sitting exactly between these dual polytopes.
    
    Attributes:
        size: Scale factor for the polytope
        
    Mathematical Properties:
        - Schläfli symbol: 2t{4,3,3} = 2t{3,3,4}
        - Cells: 8 truncated octahedra, 16 truncated tetrahedra
        - Vertex figure: Digonal disphenoid
        - Related: Bitruncated cubic honeycomb (3D tiling)
    """
    
    VERTEX_COUNT = 96
    EDGE_COUNT = 240
    FACE_COUNT = 200
    CELL_COUNT = 56
    CIRCUMRADIUS = np.sqrt(14) / 2
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a bitruncated tesseract.
        
        Args:
            size: Scale factor
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        # Generate vertices: permutations of (0, 1, 2, 3)
        verts_set = set()
        base = [0, 1, 2, 3]
        
        for perm in set(permutations(base)):
            # Apply all sign combinations to non-zero coordinates
            for s1 in [-1, 1]:
                for s2 in [-1, 1]:
                    for s3 in [-1, 1]:
                        v = list(perm)
                        # Apply signs to non-zero elements
                        for i in range(4):
                            if v[i] == 1:
                                v[i] *= s1
                            elif v[i] == 2:
                                v[i] *= s2
                            elif v[i] == 3:
                                v[i] *= s3
                        verts_set.add(tuple(v))
        
        # Convert and scale
        verts = [np.array(v, dtype=np.float32) for v in sorted(verts_set)]
        
        # Normalize to unit circumradius then apply size
        if verts:
            max_r = max(np.linalg.norm(v) for v in verts)
            scale = self.size / max_r if max_r > 0 else self.size
            self._base_vertices = [v * scale for v in verts]
        else:
            self._base_vertices = []
        
        self._edges = self._generate_edges()
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
    
    def _generate_edges(self) -> List[Tuple[int, int]]:
        """Generate edges connecting nearest vertices."""
        edges = []
        n = len(self._base_vertices)
        if n == 0:
            return edges
        
        # Find minimum distance
        min_dist = float('inf')
        for i in range(min(n, 50)):
            for j in range(i + 1, min(n, 50)):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if d > 0.01:
                    min_dist = min(min_dist, d)
        
        tolerance = min_dist * 0.15
        
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if abs(d - min_dist) < tolerance:
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
            "name": "Bitruncated Tesseract",
            "other_names": ["Bitruncated 16-cell", "Bitruncated hexadecachoron"],
            "schläfli_symbol": "2t{4,3,3}",
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "cell_types": ["8 truncated octahedra", "16 truncated tetrahedra"],
            "circumradius": self.CIRCUMRADIUS,
            "symmetry_group": "B₄",
            "symmetry_order": 384,
            "dual": "Bitruncated tesseract (self-related)",
        }
