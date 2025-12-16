# API Reference

## Core Modules

### hypersim.core.math_4d

4D vector and matrix math utilities.

#### Functions

- `create_vector_4d(x, y, z, w)` - Create a 4D vector
- `create_rotation_matrix_4d(angle_xy, angle_xz, angle_xw, angle_yz, angle_yw, angle_zw)` - Create 4D rotation matrix
- `create_scale_matrix_4d(sx, sy, sz, sw)` - Create 4D scaling matrix
- `perspective_projection_4d_to_3d(points_4d, distance)` - Project 4D points to 3D
- `normalize_vector(v)` - Normalize a vector to unit length
- `dot_product_4d(v1, v2)` - Dot product of two 4D vectors
- `cross_product_4d(a, b, c)` - Generalized cross product (3 vectors → 1 perpendicular vector)

### hypersim.core.shape_4d

Base class for all 4D shapes.

#### Shape4D Class

Abstract base class with common functionality:

**Properties:**
- `vertices` - List of 4D vertex positions (abstract)
- `edges` - List of (start, end) vertex index pairs (abstract)
- `faces` - List of vertex index tuples forming faces (abstract)
- `cells` - List of face index tuples forming 3D cells
- `vertex_count`, `edge_count`, `face_count`, `cell_count`

**Methods:**
- `set_position(x, y, z, w)` or `set_position([x, y, z, w])`
- `translate(dx, dy, dz, dw)`
- `rotate(**plane_angles)` - e.g., `rotate(xy=0.5, xw=0.3)`
- `set_rotation(**plane_angles)`
- `set_scale(scale)`
- `get_transformed_vertices()` - Get vertices with transformations applied
- `get_bounding_box()` - Returns (min_corner, max_corner)

## Objects Module

### hypersim.objects

All 4D geometric objects inherit from `Shape4D`.

#### Regular Polytopes

| Class | Vertices | Edges | Description |
|-------|----------|-------|-------------|
| `Simplex4D` | 5 | 10 | 4D simplex (5-cell) |
| `Hypercube` | 16 | 32 | 4D hypercube (tesseract) |
| `SixteenCell` | 8 | 24 | 4D cross-polytope |
| `TwentyFourCell` | 24 | 96 | Self-dual 24-cell |
| `SixHundredCell` | 120 | 720 | 600-cell |
| `OneHundredTwentyCell` | 600 | 1200 | 120-cell |

#### Prisms

| Class | Parameters | Description |
|-------|------------|-------------|
| `CubePrism` | size, height | 3D cube extruded in W |
| `TetraPrism` | size, height | Tetrahedron extruded in W |
| `OctaPrism` | size, height | Octahedron extruded in W |
| `SimplexPrism` | size, height | 4D simplex extruded in W |
| `IcosaPrism` | size, height | Icosahedron extruded in W |
| `DodecaPrism` | size, height | Dodecahedron extruded in W |

#### Other Shapes

| Class | Parameters | Description |
|-------|------------|-------------|
| `Duoprism` | m, n, size | Product of m-gon and n-gon |
| `HypercubeGrid` | divisions, size | 4D lattice grid |
| `CliffordTorus` | segments_u, segments_v, size | Flat torus in S³ |
| `Spherinder` | radius, height, segments, stacks | Sphere × interval |
| `Mobius4D` | radius, width, segments_u, segments_v | 4D Möbius strip |
| `TorusKnot4D` | p, q, segments, radius | (p,q) torus knot in 4D |
| `HopfLink4D` | radius, segments | Two linked circles |
| `RectifiedTesseract` | size | Rectified hypercube |
| `PenteractFrame` | size | 5D cube projected to 4D |

## Visualization Module

### hypersim.visualization.renderers.pygame

#### PygameRenderer Class

```python
PygameRenderer(
    width=800,
    height=600,
    title="4D Renderer",
    background_color=Color(0, 0, 0),
    distance=5.0,
)
```

**Methods:**
- `clear()` - Clear the screen
- `render_4d_object(obj, color, width)` - Render any Shape4D object
- `handle_events()` - Process input events
- `update(dt)` - Update animations
- `run(target_fps=60)` - Run the main loop

#### Color Class

```python
Color(r, g, b, a=255)
```

- `to_tuple()` - Returns (r, g, b, a)

## Engine Module

### hypersim.engine.scene

#### Scene Class

Container for multiple objects with update dispatching.

```python
scene = Scene()
scene.add(cube)
scene.update(dt)  # Calls update(dt) on all objects
```

### hypersim.engine.simulation

#### Simulation Class

Simple real-time simulation loop.

```python
sim = Simulation(scene, tick=1/60.0)
sim.set_step_callback(my_callback)
sim.run(duration=10.0)  # Run for 10 seconds
sim.stop()
```
