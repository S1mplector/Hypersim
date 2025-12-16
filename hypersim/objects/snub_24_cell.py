"""Snub 24-cell (Snub Icositetrachoron).

Mathematical Background
=======================
The snub 24-cell is a remarkable uniform 4-polytope with no regular analogue.
It is constructed by "snubbing" the 24-cell, an operation that creates new
vertices and twists faces. Unlike most snub polytopes, the snub 24-cell is
vertex-transitive (uniform).

This polytope is particularly significant because:
1. It has no 3D analogue (the snub cube is not related in the same way)
2. It contains 24 icosahedra and 120 tetrahedra as cells
3. It is chiral (exists in left-handed and right-handed forms)

Vertex Figure: Tridiminished icosahedron

Element Counts (f-vector)
-------------------------
- Vertices (V): 96
- Edges (E): 432
- Faces (F): 480 (96 triangles from snubbing + 384 triangles from cells)
- Cells (C): 144 (24 icosahedra + 120 tetrahedra)

Euler Characteristic: V - E + F - C = 96 - 432 + 480 - 144 = 0 ✓

Vertex Coordinates
------------------
The coordinates involve the golden ratio φ = (1+√5)/2 ≈ 1.618:

All even permutations and all sign changes of:
    (0, ±1, ±φ, ±φ²)
    (±1, ±1, ±1, ±φ³)
    (±φ², ±φ, ±φ, ±φ)

Where φ² = φ + 1 ≈ 2.618 and φ³ = 2φ + 1 ≈ 4.236

Geometric Properties
--------------------
- Circumradius (unit edge): R = φ² = φ + 1 ≈ 2.618
- Edge length: All edges equal (uniform)
- Chirality: Exists in two mirror-image forms
- Symmetry group: [3,4,3]⁺ (ionic diminished), order 576
- Related to: E₈ lattice, icosahedral symmetry

Special Properties
------------------
The snub 24-cell is one of only three uniform 4-polytopes that are chiral
(the others being the snub tesseract and grand antiprism).

The 24 icosahedral cells are arranged so that each vertex is shared by
exactly 5 icosahedra, creating a vertex figure that is itself a
tridiminished icosahedron.

References
----------
- Coxeter, H.S.M. "Regular Polytopes" (1973)
- Stillwell, J. "The Four Pillars of Geometry" (2005)
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Snub24Cell(Shape4D):
    """Snub 24-cell - a chiral uniform 4-polytope.
    
    The snub 24-cell is constructed by snubbing the 24-cell. It is one of
    only three chiral uniform 4-polytopes and contains both icosahedral
    and tetrahedral cells.
    
    Attributes:
        size: Scale factor for the polytope
        chirality: 'left' or 'right' for the two mirror forms
        
    Mathematical Properties:
        - No Schläfli symbol (non-Wythoffian)
        - Cells: 24 icosahedra + 120 tetrahedra
        - Vertex figure: Tridiminished icosahedron
        - Chiral: Yes (two enantiomorphic forms)
    """
    
    VERTEX_COUNT = 96
    EDGE_COUNT = 432
    FACE_COUNT = 480
    CELL_COUNT = 144
    
    # Golden ratio and powers
    PHI = (1 + np.sqrt(5)) / 2
    PHI2 = PHI + 1
    PHI3 = 2 * PHI + 1
    
    CIRCUMRADIUS = PHI2
    
    def __init__(self, size: float = 1.0, chirality: str = 'right', **kwargs):
        """Initialize a snub 24-cell.
        
        Args:
            size: Scale factor
            chirality: 'left' or 'right' for mirror forms
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        self.chirality = chirality
        
        φ = self.PHI
        φ2 = self.PHI2
        φ3 = self.PHI3
        
        verts_set = set()
        
        # Generate vertices using even permutations
        # Type 1: (0, ±1, ±φ, ±φ²)
        base1 = [0, 1, φ, φ2]
        for perm in self._even_permutations(base1):
            for signs in self._all_signs_subset([1, 2, 3]):  # Sign changes on non-zero
                v = list(perm)
                for i, s in signs:
                    v[i] *= s
                verts_set.add(tuple(v))
        
        # Type 2: (±φ², ±φ, ±φ, ±φ) - all sign combinations
        base2 = [φ2, φ, φ, φ]
        for perm in self._even_permutations(base2):
            for signs in self._all_signs(4):
                v = tuple(perm[i] * signs[i] for i in range(4))
                verts_set.add(v)
        
        # Apply chirality (mirror for left-handed)
        if chirality == 'left':
            verts_set = {(v[0], v[1], v[2], -v[3]) for v in verts_set}
        
        # Convert and scale
        verts = [np.array(v, dtype=np.float32) for v in sorted(verts_set)]
        scale = self.size / self.CIRCUMRADIUS
        self._base_vertices = [v * scale for v in verts]
        
        self._edges = self._generate_edges()
        self._faces: List[Tuple[int, ...]] = []
        self._cells: List[Tuple[int, ...]] = []
    
    def _even_permutations(self, coords: List[float]) -> List[Tuple[float, ...]]:
        """Generate even permutations of coordinates."""
        from itertools import permutations as itertools_perms
        
        all_perms = list(itertools_perms(coords))
        even = []
        
        for p in all_perms:
            # Count inversions to determine parity
            inversions = 0
            for i in range(len(p)):
                for j in range(i + 1, len(p)):
                    if p[i] > p[j]:
                        inversions += 1
            if inversions % 2 == 0:
                even.append(p)
        
        return list(set(even))
    
    def _all_signs(self, n: int) -> List[Tuple[int, ...]]:
        """Generate all 2^n sign combinations."""
        result = []
        for i in range(2**n):
            signs = tuple(1 if (i >> j) & 1 else -1 for j in range(n))
            result.append(signs)
        return result
    
    def _all_signs_subset(self, indices: List[int]) -> List[List[Tuple[int, int]]]:
        """Generate sign combinations for specific indices."""
        n = len(indices)
        result = []
        for i in range(2**n):
            signs = []
            for j, idx in enumerate(indices):
                s = 1 if (i >> j) & 1 else -1
                signs.append((idx, s))
            result.append(signs)
        return result
    
    def _generate_edges(self) -> List[Tuple[int, int]]:
        """Generate edges by finding nearest neighbors."""
        edges = []
        n = len(self._base_vertices)
        if n == 0:
            return edges
        
        # Find edge length (minimum non-zero distance)
        distances = []
        for i in range(min(n, 30)):
            for j in range(i + 1, min(n, 30)):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if d > 0.01:
                    distances.append(d)
        
        if not distances:
            return edges
        
        edge_length = min(distances)
        tolerance = edge_length * 0.15
        
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
            "name": "Snub 24-cell",
            "other_names": ["Snub icositetrachoron", "Sadi"],
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "cell_types": ["24 icosahedra", "120 tetrahedra"],
            "vertex_figure": "Tridiminished icosahedron",
            "circumradius": self.CIRCUMRADIUS,
            "chirality": self.chirality,
            "is_chiral": True,
            "symmetry_group": "[3,4,3]⁺",
            "symmetry_order": 576,
            "golden_ratio_related": True,
        }
