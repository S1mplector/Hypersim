# Tutorial: Getting Started with HyperSim

This tutorial will guide you through the basics of using HyperSim for 4D visualization.

## Understanding 4D Space

In 4D space, we have four perpendicular axes: X, Y, Z, and W. Just as 3D objects cast 2D shadows, 4D objects cast 3D "shadows" through projection.

### 4D Rotations

In 4D, rotations happen in *planes*, not around axes:
- **XY plane**: Rotation in the familiar X-Y plane
- **XZ plane**: Rotation in X-Z (like yaw in 3D)
- **XW plane**: Rotation involving the 4th dimension
- **YZ plane**: Rotation in Y-Z (like pitch in 3D)
- **YW plane**: Rotation involving the 4th dimension
- **ZW plane**: Rotation involving the 4th dimension

## Creating Your First 4D Object

```python
from hypersim.objects import Hypercube

# Create a tesseract (4D hypercube)
cube = Hypercube(size=1.5)

# Check its properties
print(f"Vertices: {cube.vertex_count}")  # 16
print(f"Edges: {cube.edge_count}")       # 32
```

## Transforming Objects

### Position

```python
# Set absolute position
cube.set_position([1.0, 2.0, 0.0, 0.5])

# Or use keyword arguments
cube.set_position(x=1.0, w=0.5)

# Translate relative to current position
cube.translate(0.1, 0.0, 0.0, 0.0)
```

### Rotation

```python
# Rotate in multiple planes at once
cube.rotate(xy=0.5, xw=0.3)  # angles in radians

# Set absolute rotation (resets accumulated rotation)
cube.set_rotation(xy=1.57)  # 90 degrees
```

### Scale

```python
cube.set_scale(2.0)  # uniform scaling
```

## Rendering with Pygame

```python
import pygame
from hypersim.objects import Hypercube
from hypersim.visualization.renderers.pygame import PygameRenderer, Color

# Initialize renderer
renderer = PygameRenderer(
    width=1024,
    height=768,
    title="My 4D Scene",
    distance=5.0,  # projection distance
)

# Create object
cube = Hypercube(size=1.5)

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Animate
    cube.rotate(xy=0.01, xw=0.007)

    # Render
    renderer.clear()
    renderer.render_4d_object(cube, Color(100, 200, 255), width=2)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
```

## Working with Multiple Objects

```python
from hypersim.objects import Hypercube, Simplex4D, SixteenCell

# Create objects at different positions
cube = Hypercube(size=1.0)
cube.set_position([-2, 0, 0, 0])

simplex = Simplex4D(size=1.2)
simplex.set_position([0, 0, 0, 0])

cell = SixteenCell(size=1.0)
cell.set_position([2, 0, 0, 0])

# Render each with different colors
renderer.render_4d_object(cube, Color(255, 100, 100))
renderer.render_4d_object(simplex, Color(100, 255, 100))
renderer.render_4d_object(cell, Color(100, 100, 255))
```

## Interactive Controls

The default Pygame renderer supports:

| Key | Action |
|-----|--------|
| Mouse drag | Orbit camera |
| +/- | Zoom in/out |
| W/S | Move camera forward/back |
| A/D | Move camera left/right |
| Q/E | Move camera up/down |
| Z/X | Move camera along W axis |
| ESC | Quit |

## Next Steps

- Explore the [API Reference](api/index.md) for detailed documentation
- Check out the [Examples](examples.md) for more complex scenarios
- Learn about [creating custom 4D objects](api/objects.md)
