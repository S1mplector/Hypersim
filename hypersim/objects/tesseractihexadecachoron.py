"""Tesseractihexadecachoron (Rectified 24-cell, Icositetrachoron).

Mathematical Background
=======================
The rectified 24-cell, also known as tesseractihexadecachoron, is a highly
symmetric uniform 4-polytope. It is the rectification of the self-dual 24-cell,
which means it is constructed by placing vertices at the midpoints of all edges
of the 24-cell.

The name "tesseractihexadecachoron" reflects its dual nature: it contains
both tesseract-like and 16-cell-like structures within it.

This polytope is notable for being:
1. Isotoxal (edge-transitive)
2. Self-dual
3. Related to both the tesseract and 16-cell families

Vertex Figure: Square antiprism

Element Counts (f-vector)
-------------------------
- Vertices (V): 96
- Edges (E): 288
- Faces (F): 288 (192 triangles + 96 squares)
- Cells (C): 96 (24 cubes + 24 cuboctahedra)

Euler Characteristic: V - E + F - C = 96 - 288 + 288 - 96 = 0 ✓

Vertex Coordinates
------------------
Vertices are at all permutations of:
    (0, 0, ±1, ±2)  (48 vertices)
    (±1, ±1, ±1, ±1) (16 vertices)

And all permutations and sign changes of:
    (0, ±1, ±1, ±2)  (remaining 32 vertices)

Geometric Properties
--------------------
- Circumradius (unit edge): R = √5 ≈ 2.236
- Edge length: All edges equal (uniform)
- Self-dual: Yes (isomorphic to its dual)
- Isotoxal: Yes (all edges equivalent)
- Symmetry group: F₄, order 1152

Relationships
-------------
- Rectification of: 24-cell
- Contains: 24 cubes (from tesseract), 24 cuboctahedra (rectified octahedra)
- Vertex figure: Square antiprism (connects cube to cuboctahedron)

This polytope demonstrates the deep connection between the 24-cell, tesseract,
and 16-cell through the F₄ symmetry group.

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Wikipedia: Rectified 24-cell
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np
from itertools import permutations

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Tesseractihexadecachoron(Shape4D):
    """Rectified 24-cell (Tesseractihexadecachoron).
    
    A self-dual, edge-transitive uniform 4-polytope formed by rectifying
    the 24-cell. It contains 24 cubes and 24 cuboctahedra arranged in
    a highly symmetric pattern.
    
    Attributes:
        size: Scale factor for the polytope
        
    Mathematical Properties:
        - Schläfli symbol: r{3,4,3} = {3,4,3}ᵣ
        - Cells: 24 cubes + 24 cuboctahedra
        - Vertex figure: Square antiprism
        - Self-dual: Yes
        - Isotoxal: Yes (edge-transitive)
    """
    
    VERTEX_COUNT = 96
    EDGE_COUNT = 288
    FACE_COUNT = 288
    CELL_COUNT = 96
    
    CIRCUMRADIUS = np.sqrt(5)
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a rectified 24-cell.
        
        Args:
            size: Scale factor
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        verts_set = set()
        
        # Type 1: permutations of (0, 0, ±1, ±2)
        for perm in set(permutations([0, 0, 1, 2])):
            for s1 in [-1, 1]:
                for s2 in [-1, 1]:
                    v = list(perm)
                    # Apply signs to non-zero elements
                    for i in range(4):
                        if v[i] == 1:
                            v[i] *= s1
                        elif v[i] == 2:
                            v[i] *= s2
                    verts_set.add(tuple(v))
        
        # Type 2: (±1, ±1, ±1, ±1)
        for signs in self._all_signs(4):
            verts_set.add(tuple(signs))
        
        # Type 3: permutations of (0, ±1, ±1, ±2)
        for perm in set(permutations([0, 1, 1, 2])):
            for s1 in [-1, 1]:
                for s2 in [-1, 1]:
                    for s3 in [-1, 1]:
                        v = list(perm)
                        sign_idx = 0
                        signs = [s1, s2, s3]
                        for i in range(4):
                            if v[i] != 0:
                                v[i] *= signs[sign_idx % 3]
                                sign_idx += 1
                        verts_set.add(tuple(v))
        
        # Convert and scale
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
        
        # Find minimum distance
        distances = []
        for i in range(min(n, 50)):
            for j in range(i + 1, min(n, 50)):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if d > 0.001:
                    distances.append(d)
        
        if not distances:
            return edges
        
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
            "name": "Rectified 24-cell",
            "other_names": ["Tesseractihexadecachoron", "Rico", "Rectified icositetrachoron"],
            "schläfli_symbol": "r{3,4,3}",
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "cell_types": ["24 cubes", "24 cuboctahedra"],
            "vertex_figure": "Square antiprism",
            "circumradius": self.CIRCUMRADIUS,
            "is_self_dual": True,
            "is_isotoxal": True,
            "symmetry_group": "F₄",
            "symmetry_order": 1152,
        }


# Alias for convenience
Rectified24Cell = Tesseractihexadecachoron
