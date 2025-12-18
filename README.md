# HyperSim

A Python framework for 4D visualization and simulation. This project provides tools for working with 4D geometry, including 4D objects, transformations, and visualizations.

## Features

- 4D geometric primitives (hypercube/tesseract, 4D simplex, 16-cell)
- 4D to 3D perspective projection utilities
- Interactive visualization using Pygame (real-time controls)
- Extensible architecture for adding new 4D objects and renderers

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hypersim.git
   cd hypersim
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Unix/macOS
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

## Quick Start

```python
import pygame
from hypersim.objects import Hypercube
from hypersim.visualization import PygameRenderer, Color

# Create a renderer window
renderer = PygameRenderer(width=1024, height=768, title="HyperSim - Tesseract")

# Create a hypercube, tweak initial transform
cube = Hypercube(size=1.5)
cube.set_position([0, 0, 0, 1.0])
cube.rotate(xy=0.3, xw=0.2, zw=0.1)

# Minimal render loop
running = True
clock = pygame.time.Clock()
while running:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False
    if hasattr(renderer, 'clear'):
        renderer.clear()
    renderer.render_4d_object(cube, Color(80, 200, 255), 2)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()
```

## Project Structure

```
hypersim/
├── hypersim/               # Main package
│   ├── core/              # Core simulation and math
│   ├── objects/           # 4D object definitions
│   └── visualization/     # Visualization components
├── examples/              # Example scripts
├── tests/                 # Unit and integration tests
└── docs/                  # Documentation
```

## Running Examples

Check the `examples/` directory for example scripts. To run the included examples:

```bash
python examples/pygame_simplex.py
python examples/pygame_sixteen_cell.py
python examples/game_session_bootstrap.py  # progression/campaign bootstrap
python -m hypersim.cli --demo game         # progression-enabled sandbox mode
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
