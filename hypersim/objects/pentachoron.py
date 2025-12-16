"""Pentachoron (5-cell, 4-simplex, Hypertetrahedron).

Mathematical Background
=======================
The pentachoron is the simplest regular 4-polytope, analogous to the
tetrahedron in 3D. It is the 4-dimensional simplex, formed by 5 vertices
where each vertex is equidistant from all others.

The name comes from Greek: "penta" (five) + "choron" (room/cell),
referring to its 5 tetrahedral cells.

Schläfli Symbol: {3,3,3}

This symbol indicates:
- Faces are triangles {3}
- Three triangles meet at each edge {3,3}  
- Three tetrahedra meet at each edge {3,3,3}

Element Counts (f-vector)
-------------------------
- Vertices (V): 5
- Edges (E): 10
- Faces (F): 10 triangles
- Cells (C): 5 tetrahedra

Euler Characteristic: V - E + F - C = 5 - 10 + 10 - 5 = 0 ✓

Combinatorial Formula:
- V = C(5,1) = 5
- E = C(5,2) = 10  
- F = C(5,3) = 10
- C = C(5,4) = 5

This is the f-vector of the 4-simplex: (5, 10, 10, 5).

Vertex Coordinates
------------------
Standard coordinates (vertices of regular 4-simplex with edge length √2):

    v₀ = (1, 1, 1, -1/√5)
    v₁ = (1, -1, -1, -1/√5)
    v₂ = (-1, 1, -1, -1/√5)
    v₃ = (-1, -1, 1, -1/√5)
    v₄ = (0, 0, 0, √5 - 1/√5)

Alternative (centered at origin with unit edge):
    vᵢ = eᵢ - (1/5)∑eⱼ  (unit vectors minus their mean)

Geometric Properties
--------------------
- Circumradius: R = √(2/5) ≈ 0.632 (for unit edge)
- Inradius: r = 1/(2√10) ≈ 0.158 (for unit edge)  
- Edge length to circumradius ratio: √(5/2) ≈ 1.581
- Cell dihedral angle: arccos(1/4) ≈ 75.52°
- Self-dual: Yes (dual is another pentachoron)
- Symmetry group: A₄ (symmetric group S₅), order 120

Interesting Properties
----------------------
1. The pentachoron is self-dual (like the tetrahedron in 3D)
2. It is the only regular 4-polytope with odd numbers in its f-vector
3. Every pair of vertices is connected by an edge (complete graph K₅)
4. It has the smallest number of vertices of any 4-polytope (5)
5. Its skeleton is the Petersen graph's complement

Historical Note
---------------
The pentachoron was first described by Ludwig Schläfli in the 1850s
as part of his pioneering work on higher-dimensional geometry.

References
----------
- Schläfli, L. "Theorie der vielfachen Kontinuität" (1852)
- Coxeter, H.S.M. "Regular Polytopes" (1973)
"""
from __future__ import annotations

from typing import List, Tuple
import numpy as np

from ..core.math_4d import Vector4D
from ..core.shape_4d import Shape4D


class Pentachoron(Shape4D):
    """Pentachoron (5-cell) - the 4-dimensional tetrahedron.
    
    The simplest regular 4-polytope, consisting of 5 tetrahedral cells.
    It is the 4D analogue of the tetrahedron and is self-dual.
    
    Attributes:
        size: Scale factor (circumradius when size=1)
        
    Mathematical Properties:
        - Schläfli symbol: {3,3,3}
        - Vertices: 5
        - Edges: 10 (complete graph K₅)
        - Faces: 10 triangles
        - Cells: 5 tetrahedra
        - Self-dual: Yes
    """
    
    VERTEX_COUNT = 5
    EDGE_COUNT = 10
    FACE_COUNT = 10
    CELL_COUNT = 5
    
    # For unit edge length
    CIRCUMRADIUS = np.sqrt(2/5)
    INRADIUS = 1 / (2 * np.sqrt(10))
    DIHEDRAL_ANGLE = np.arccos(1/4)  # ≈ 75.52°
    
    def __init__(self, size: float = 1.0, **kwargs):
        """Initialize a pentachoron.
        
        Args:
            size: Scale factor
            **kwargs: Additional arguments passed to Shape4D
        """
        super().__init__(**kwargs)
        self.size = float(size)
        
        # Generate vertices using the standard simplex coordinates
        sqrt5 = np.sqrt(5)
        
        # Regular 4-simplex vertices
        vertices = [
            np.array([1, 1, 1, -1/sqrt5], dtype=np.float32),
            np.array([1, -1, -1, -1/sqrt5], dtype=np.float32),
            np.array([-1, 1, -1, -1/sqrt5], dtype=np.float32),
            np.array([-1, -1, 1, -1/sqrt5], dtype=np.float32),
            np.array([0, 0, 0, sqrt5 - 1/sqrt5], dtype=np.float32),
        ]
        
        # Center at origin and scale
        centroid = sum(vertices) / len(vertices)
        vertices = [v - centroid for v in vertices]
        
        # Scale to desired size
        if vertices:
            max_r = max(np.linalg.norm(v) for v in vertices)
            scale = self.size / max_r if max_r > 0 else self.size
            self._base_vertices = [v * scale for v in vertices]
        else:
            self._base_vertices = vertices
        
        # All pairs connected (complete graph K₅)
        self._edges = [(i, j) for i in range(5) for j in range(i+1, 5)]
        
        # All triples form faces
        self._faces = [
            (i, j, k)
            for i in range(5) for j in range(i+1, 5) for k in range(j+1, 5)
        ]
        
        # All quadruples form tetrahedral cells
        self._cells = [
            (i, j, k, l)
            for i in range(5) for j in range(i+1, 5) 
            for k in range(j+1, 5) for l in range(k+1, 5)
        ]
    
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
            "name": "Pentachoron",
            "other_names": ["5-cell", "4-simplex", "Hypertetrahedron", "Pentatope"],
            "schläfli_symbol": "{3,3,3}",
            "vertices": self.VERTEX_COUNT,
            "edges": self.EDGE_COUNT,
            "faces": self.FACE_COUNT,
            "cells": self.CELL_COUNT,
            "cell_type": "Tetrahedron",
            "circumradius": self.CIRCUMRADIUS,
            "inradius": self.INRADIUS,
            "dihedral_angle_deg": np.degrees(self.DIHEDRAL_ANGLE),
            "is_self_dual": True,
            "is_regular": True,
            "symmetry_group": "A₄ (S₅)",
            "symmetry_order": 120,
            "graph": "Complete graph K₅",
        }


# Aliases for different naming conventions
FiveCell = Pentachoron
Hypertetrahedron = Pentachoron
Pentatope = Pentachoron
