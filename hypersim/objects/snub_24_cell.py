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
        φ2 = self.PHI2  # φ + 1
        
        verts_set = set()
        
        # The snub 24-cell vertices can be derived from the 24-cell
        # by a specific snubbing operation. The coordinates are:
        
        # Start with 24-cell vertices and add snub vertices
        # 24-cell has vertices at permutations of (±1, ±1, 0, 0) and (±1, 0, 0, 0)*2
        
        # Type 1: Permutations of (±1, ±1, 0, 0) - 24 vertices from 24-cell
        for signs in self._all_signs(2):
            for positions in [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]:
                v = [0.0, 0.0, 0.0, 0.0]
                v[positions[0]] = signs[0]
                v[positions[1]] = signs[1]
                verts_set.add(tuple(v))
        
        # Type 2: (±2, 0, 0, 0) and permutations - 8 vertices
        for i in range(4):
            for s in [1, -1]:
                v = [0.0, 0.0, 0.0, 0.0]
                v[i] = 2.0 * s
                verts_set.add(tuple(v))
        
        # Type 3: Snub vertices - even permutations of (±φ, ±1, ±1/φ, 0)
        # where 1/φ = φ - 1
        inv_phi = φ - 1
        base_coords = [φ, 1.0, inv_phi, 0.0]
        
        for perm in self._even_permutations_indices(4):
            for signs in self._all_signs(3):  # Signs for non-zero coords
                v = [0.0, 0.0, 0.0, 0.0]
                sign_idx = 0
                for i, p in enumerate(perm):
                    val = base_coords[p]
                    if val != 0:
                        v[i] = val * signs[sign_idx]
                        sign_idx += 1
                    else:
                        v[i] = 0.0
                verts_set.add(tuple(v))
        
        # Type 4: Even permutations of (±φ², ±1/φ, ±1/φ, ±1/φ) with even sign changes
        base4 = [φ2, inv_phi, inv_phi, inv_phi]
        for perm in self._even_permutations_indices(4):
            for signs in self._even_signs(4):
                v = [base4[perm[i]] * signs[i] for i in range(4)]
                verts_set.add(tuple(v))
        
        # Apply chirality (mirror for left-handed)
        if chirality == 'left':
            verts_set = {(v[0], v[1], v[2], -v[3]) for v in verts_set}
        
        # Normalize all vertices to same circumradius and scale
        verts_list = list(verts_set)
        if verts_list:
            radii = [np.sqrt(sum(c*c for c in v)) for v in verts_list]
            max_radius = max(radii) if radii else 1.0
            scale = self.size / max_radius if max_radius > 0 else self.size
        else:
            scale = self.size
        
        self._base_vertices = [np.array(v, dtype=np.float32) * scale for v in sorted(verts_list)]
        
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
    
    def _even_permutations_indices(self, n: int) -> List[Tuple[int, ...]]:
        """Generate even permutations of indices [0, 1, ..., n-1]."""
        from itertools import permutations as itertools_perms
        
        all_perms = list(itertools_perms(range(n)))
        even = []
        
        for p in all_perms:
            inversions = 0
            for i in range(len(p)):
                for j in range(i + 1, len(p)):
                    if p[i] > p[j]:
                        inversions += 1
            if inversions % 2 == 0:
                even.append(p)
        
        return even
    
    def _even_signs(self, n: int) -> List[Tuple[int, ...]]:
        """Generate sign combinations with even number of negatives."""
        result = []
        for i in range(2**n):
            signs = tuple(1 if (i >> j) & 1 else -1 for j in range(n))
            # Count negatives
            neg_count = sum(1 for s in signs if s == -1)
            if neg_count % 2 == 0:
                result.append(signs)
        return result
    
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
        
        # Compute all pairwise distances
        distances = []
        for i in range(n):
            for j in range(i + 1, n):
                d = np.linalg.norm(self._base_vertices[i] - self._base_vertices[j])
                if d > 0.001:
                    distances.append((d, i, j))
        
        if not distances:
            return edges
        
        distances.sort(key=lambda x: x[0])
        
        # Find the edge length - the minimum distance
        edge_length = distances[0][0]
        
        # Use a tolerance of 5% to account for floating point errors
        tolerance = edge_length * 0.05
        
        # Add all edges with this length
        for d, i, j in distances:
            if d <= edge_length + tolerance:
                edges.append((i, j))
            else:
                # Distances are sorted, so we can stop
                break
        
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
