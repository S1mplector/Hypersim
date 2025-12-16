# 4D Polytope Reference

A comprehensive guide to the 4-dimensional polytopes available in HyperSim.

## Table of Contents

1. [Regular Polytopes](#regular-polytopes)
2. [Uniform Polytopes](#uniform-polytopes)
3. [Prisms and Products](#prisms-and-products)
4. [Manifolds and Surfaces](#manifolds-and-surfaces)
5. [Mathematical Concepts](#mathematical-concepts)

---

## Regular Polytopes

There are exactly **6 regular convex 4-polytopes** (analogous to the 5 Platonic solids in 3D):

### Pentachoron (5-cell)
```
Schläfli symbol: {3,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 5 |
| Edges | 10 |
| Faces | 10 triangles |
| Cells | 5 tetrahedra |
| Symmetry | A₄ (order 120) |

The simplest regular 4-polytope. Self-dual. Every pair of vertices is connected (complete graph K₅).

**Usage:**
```python
from hypersim.objects import Pentachoron
shape = Pentachoron(size=1.0)
```

---

### Tesseract (8-cell, Hypercube)
```
Schläfli symbol: {4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 16 |
| Edges | 32 |
| Faces | 24 squares |
| Cells | 8 cubes |
| Symmetry | B₄ (order 384) |

The 4D analogue of the cube. Vertices at (±1, ±1, ±1, ±1).

**Usage:**
```python
from hypersim.objects import Hypercube
shape = Hypercube(size=1.0)
```

---

### 16-cell (Hexadecachoron)
```
Schläfli symbol: {3,3,4}
```

| Property | Value |
|----------|-------|
| Vertices | 8 |
| Edges | 24 |
| Faces | 32 triangles |
| Cells | 16 tetrahedra |
| Symmetry | B₄ (order 384) |

Dual of the tesseract. Vertices on coordinate axes at distance 1. The 4D analogue of the octahedron.

**Usage:**
```python
from hypersim.objects import SixteenCell
shape = SixteenCell(size=1.0)
```

---

### 24-cell (Icositetrachoron)
```
Schläfli symbol: {3,4,3}
```

| Property | Value |
|----------|-------|
| Vertices | 24 |
| Edges | 96 |
| Faces | 96 triangles |
| Cells | 24 octahedra |
| Symmetry | F₄ (order 1152) |

**Self-dual** and unique to 4D (no 3D analogue). Vertices are permutations of (±1, ±1, 0, 0).

**Usage:**
```python
from hypersim.objects import TwentyFourCell
shape = TwentyFourCell(size=1.0)
```

---

### 120-cell (Hecatonicosachoron)
```
Schläfli symbol: {5,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 600 |
| Edges | 1200 |
| Faces | 720 pentagons |
| Cells | 120 dodecahedra |
| Symmetry | H₄ (order 14400) |

The largest regular 4-polytope. Contains golden ratio in its coordinates.

**Usage:**
```python
from hypersim.objects import OneHundredTwentyCell
shape = OneHundredTwentyCell(size=1.0)
```

---

### 600-cell (Hexacosichoron)
```
Schläfli symbol: {3,3,5}
```

| Property | Value |
|----------|-------|
| Vertices | 120 |
| Edges | 720 |
| Faces | 1200 triangles |
| Cells | 600 tetrahedra |
| Symmetry | H₄ (order 14400) |

Dual of the 120-cell. Densest packing of tetrahedra around a point in 4D.

**Usage:**
```python
from hypersim.objects import SixHundredCell
shape = SixHundredCell(size=1.0)
```

---

## Uniform Polytopes

Uniform polytopes have regular faces and vertex-transitive symmetry.

### Rectified Tesseract
```
Schläfli symbol: r{4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 24 |
| Edges | 96 |
| Faces | 64 (32△ + 24□) |
| Cells | 24 (8 cuboctahedra + 16 tetrahedra) |

Formed by truncating the tesseract to edge midpoints.

---

### Truncated Tesseract
```
Schläfli symbol: t{4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 64 |
| Edges | 128 |
| Faces | 88 |
| Cells | 24 |

Tesseract with corners cut off.

---

### Cantellated Tesseract
```
Schläfli symbol: rr{4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 96 |
| Edges | 288 |
| Faces | 272 |
| Cells | 80 |

Tesseract with edges beveled.

---

### Bitruncated Tesseract
```
Schläfli symbol: 2t{4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 96 |
| Edges | 240 |
| Faces | 200 |
| Cells | 56 |

Both the tesseract and 16-cell truncated to this common form.

---

### Omnitruncated Tesseract
```
Schläfli symbol: tr{4,3,3}
```

| Property | Value |
|----------|-------|
| Vertices | 768 |
| Edges | 1536 |
| Faces | 1040 |
| Cells | 272 |

Maximum truncation - the largest uniform polytope in the tesseract family.

---

### Snub 24-cell
```
No Schläfli symbol (non-Wythoffian)
```

| Property | Value |
|----------|-------|
| Vertices | 96 |
| Edges | 432 |
| Faces | 480 |
| Cells | 144 (24 icosahedra + 120 tetrahedra) |

**Chiral** - exists in left and right-handed forms. Related to the golden ratio.

---

### Rectified 24-cell (Tesseractihexadecachoron)
```
Schläfli symbol: r{3,4,3}
```

| Property | Value |
|----------|-------|
| Vertices | 96 |
| Edges | 288 |
| Faces | 288 |
| Cells | 96 (24 cubes + 24 cuboctahedra) |

**Self-dual** and **isotoxal** (edge-transitive).

---

## Prisms and Products

### Duoprism
```
Symbol: {p} × {q}
```

The Cartesian product of two polygons. A {3}×{4} duoprism has:
- Vertices: 3 × 4 = 12
- Cells: 3 cubes + 4 triangular prisms

**Usage:**
```python
from hypersim.objects import Duoprism
shape = Duoprism(m=5, n=6)  # Pentagon × Hexagon
```

---

### Polyhedral Prisms

Prisms formed by extruding 3D polyhedra into 4D:

| Prism | Base | Vertices | Cells |
|-------|------|----------|-------|
| Cube Prism | Cube | 16 | 2 cubes + 6 cubes |
| Tetra Prism | Tetrahedron | 8 | 2 tetra + 4 prisms |
| Octa Prism | Octahedron | 12 | 2 octa + 8 prisms |
| Icosa Prism | Icosahedron | 24 | 2 icosa + 20 prisms |
| Dodeca Prism | Dodecahedron | 40 | 2 dodeca + 12 prisms |

---

## Manifolds and Surfaces

### Clifford Torus
A flat torus embedded in the 3-sphere S³ ⊂ ℝ⁴.

```python
from hypersim.objects import CliffordTorus
shape = CliffordTorus(segments_u=30, segments_v=30)
```

- Intrinsically flat (zero Gaussian curvature)
- Product of two circles: S¹ × S¹

---

### Klein Bottle (4D)
A non-orientable surface that can only be embedded without self-intersection in 4D.

```python
from hypersim.objects import KleinBottle4D
shape = KleinBottle4D(radius=1.0, segments_u=40, segments_v=20)
```

- Euler characteristic: 0
- Non-orientable
- Cannot exist in 3D without self-intersection

---

### Möbius Strip (4D)
```python
from hypersim.objects import Mobius4D
shape = Mobius4D(radius=1.0, width=0.5)
```

---

### Torus Knots
Knots that lie on the surface of a torus.

```python
from hypersim.objects import TorusKnot4D
shape = TorusKnot4D(p=3, q=5)  # Trefoil-like
```

---

## Mathematical Concepts

### Schläfli Symbol
The notation {p, q, r} describes a regular 4-polytope where:
- Faces are {p}-gons
- {p, q} polyhedra meet at vertices  
- {p, q, r} indicates r cells meet at each edge

### Euler Characteristic
For any 4-polytope: **V - E + F - C = 0**

This is the 4D analogue of V - E + F = 2 for polyhedra.

### Symmetry Groups

| Group | Order | Polytopes |
|-------|-------|-----------|
| A₄ | 120 | Pentachoron |
| B₄ | 384 | Tesseract, 16-cell |
| F₄ | 1152 | 24-cell |
| H₄ | 14400 | 120-cell, 600-cell |

### Duality
Every 4-polytope has a dual where:
- Vertices ↔ Cells
- Edges ↔ Faces

Self-dual polytopes: Pentachoron, 24-cell, Rectified 24-cell

### Golden Ratio Polytopes
The 120-cell, 600-cell, and snub 24-cell all involve the golden ratio:
```
φ = (1 + √5) / 2 ≈ 1.618
```

---

## Complete Object List

| Object | Type | V | E | F | C |
|--------|------|---|---|---|---|
| Pentachoron | Regular | 5 | 10 | 10 | 5 |
| Tesseract | Regular | 16 | 32 | 24 | 8 |
| 16-cell | Regular | 8 | 24 | 32 | 16 |
| 24-cell | Regular | 24 | 96 | 96 | 24 |
| 120-cell | Regular | 600 | 1200 | 720 | 120 |
| 600-cell | Regular | 120 | 720 | 1200 | 600 |
| Rectified Tesseract | Uniform | 24 | 96 | 64 | 24 |
| Truncated Tesseract | Uniform | 64 | 128 | 88 | 24 |
| Cantellated Tesseract | Uniform | 96 | 288 | 272 | 80 |
| Bitruncated Tesseract | Uniform | 96 | 240 | 200 | 56 |
| Runcinated Tesseract | Uniform | 64 | 192 | 192 | 80 |
| Omnitruncated Tesseract | Uniform | 768 | 1536 | 1040 | 272 |
| Snub 24-cell | Uniform | 96 | 432 | 480 | 144 |
| Rectified 24-cell | Uniform | 96 | 288 | 288 | 96 |
| Grand Antiprism | Uniform | 100 | 500 | 720 | 320 |
