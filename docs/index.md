# HyperSim Documentation

HyperSim is a Python framework for 4D visualization and simulation. It provides tools for working with 4D geometry, including objects, transformations, and interactive visualizations.

## Quick Start

```python
from hypersim.objects import Hypercube
from hypersim.visualization.renderers.pygame import PygameRenderer, Color

# Create a renderer and hypercube
renderer = PygameRenderer(width=800, height=600)
cube = Hypercube(size=1.5)

# Render loop
renderer.run()
```

## Features

- **4D Geometric Primitives**: Hypercube, simplex, 16-cell, 24-cell, 600-cell, and more
- **4D Transformations**: Rotation in 6 planes (XY, XZ, XW, YZ, YW, ZW), translation, scaling
- **Projection**: 4D to 3D perspective projection with configurable distance
- **Interactive Visualization**: Real-time rendering with Pygame, mouse/keyboard controls
- **Extensible Architecture**: Easy to add new 4D objects and renderers

## Contents

- [Installation](installation.md)
- [Tutorial](tutorial.md)
- [API Reference](api/index.md)
- [Examples](examples.md)
- [Contributing](contributing.md)

## Supported 4D Objects

### Regular Polytopes
- 5-cell (Simplex4D)
- 8-cell/Tesseract (Hypercube)
- 16-cell (SixteenCell)
- 24-cell (TwentyFourCell)
- 120-cell (OneHundredTwentyCell)
- 600-cell (SixHundredCell)

### Prisms and Products
- Duoprism (m×n polygon products)
- CubePrism, TetraPrism, OctaPrism
- SimplexPrism, IcosaPrism, DodecaPrism

### Manifolds and Surfaces
- CliffordTorus
- Spherinder
- Mobius4D
- TorusKnot4D
- HopfLink4D

### Other
- HypercubeGrid
- RectifiedTesseract
- PenteractFrame (5D projection)

## License

MIT License - see LICENSE file for details.
