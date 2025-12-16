# Installation

## Requirements

- Python 3.8 or higher
- NumPy >= 1.21.0
- Matplotlib >= 3.4.0
- SciPy >= 1.7.0
- Pygame >= 2.1.0

## Installing from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hypersim.git
   cd hypersim
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Unix/macOS
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   ```

## Installing with Development Dependencies

For running tests and building documentation:

```bash
pip install -e ".[dev]"
```

This installs additional packages:
- pytest (testing)
- black, isort (code formatting)
- mypy (type checking)
- sphinx (documentation)

## Verifying Installation

```python
import hypersim
print(hypersim.__version__)

from hypersim.objects import Hypercube
cube = Hypercube(size=1.0)
print(f"Hypercube has {cube.vertex_count} vertices and {cube.edge_count} edges")
```

## Running Tests

```bash
pytest tests/
```

## Troubleshooting

### Pygame Display Issues

If you encounter display issues with Pygame:

```bash
# On Linux, you may need:
sudo apt-get install python3-pygame

# On macOS with M1/M2:
pip install pygame --pre
```

### NumPy Compatibility

If you see NumPy-related errors, ensure you have a compatible version:

```bash
pip install "numpy>=1.21.0,<2.0.0"
```
