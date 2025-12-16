"""Example: Matplotlib renderer for static and animated 4D visualization.

Demonstrates the matplotlib renderer for publication-quality figures
and GIF animations.
"""
from hypersim.objects import Hypercube, Simplex4D, SixteenCell
from hypersim.visualization.renderers.matplotlib import (
    MatplotlibRenderer,
    MatplotlibAnimator,
)


def render_static():
    """Render static images of 4D objects."""
    print("Rendering static images...")
    
    renderer = MatplotlibRenderer(
        figsize=(10, 8),
        projection_distance=5.0,
        style="dark_background",
    )
    
    # Single object
    cube = Hypercube(size=1.2)
    cube.rotate(xy=0.3, xw=0.2, yw=0.15)
    
    renderer.render_object(
        cube,
        color="cyan",
        linewidth=1.5,
        title="Tesseract (4D Hypercube)",
        elevation=20,
        azimuth=45,
    )
    
    # Multiple objects
    renderer.clear()
    
    cube = Hypercube(size=0.8)
    cube.set_position([-1.5, 0, 0, 0])
    cube.rotate(xy=0.3)
    
    simplex = Simplex4D(size=1.0)
    simplex.rotate(xz=0.4)
    
    cell = SixteenCell(size=0.9)
    cell.set_position([1.5, 0, 0, 0])
    cell.rotate(yw=0.3)
    
    renderer.add_object(cube, color="cyan", linewidth=1.5, label="Hypercube")
    renderer.add_object(simplex, color="orange", linewidth=1.5, label="5-cell")
    renderer.add_object(cell, color="lime", linewidth=1.5, label="16-cell")
    
    renderer.render(
        title="Regular 4-Polytopes Comparison",
        elevation=25,
        azimuth=60,
    )


def render_with_faces():
    """Render objects with filled faces."""
    print("Rendering with faces...")
    
    renderer = MatplotlibRenderer(
        figsize=(10, 8),
        style="dark_background",
    )
    
    cube = Hypercube(size=1.2)
    cube.rotate(xy=0.4, xw=0.25, yw=0.2)
    
    renderer.render_faces(
        cube,
        face_color="steelblue",
        edge_color="white",
        alpha=0.4,
        title="Tesseract with Filled Faces",
    )


def create_animation():
    """Create a rotating animation."""
    print("Creating animation (this may take a moment)...")
    
    animator = MatplotlibAnimator(
        figsize=(8, 8),
        style="dark_background",
    )
    
    cube = Hypercube(size=1.2)
    cube.rotate(xy=0.3, xw=0.2)
    
    # 3D view rotation
    anim = animator.animate_rotation_3d(
        cube,
        frames=60,
        color="cyan",
        linewidth=2,
        title="Tesseract - 3D View Rotation",
    )
    
    # Uncomment to save:
    # animator.save(anim, "tesseract_rotation.gif", fps=30)
    
    import matplotlib.pyplot as plt
    plt.show()


def create_4d_animation():
    """Create a 4D rotation animation."""
    print("Creating 4D rotation animation...")
    
    animator = MatplotlibAnimator(
        figsize=(8, 8),
        style="dark_background",
    )
    
    cube = Hypercube(size=1.2)
    
    anim = animator.animate_rotation_4d(
        cube,
        frames=120,
        rotation_planes={"xy": 0.05, "xw": 0.03, "zw": 0.02},
        color="cyan",
        linewidth=2,
        title="Tesseract - 4D Rotation",
    )
    
    import matplotlib.pyplot as plt
    plt.show()


if __name__ == "__main__":
    print("Matplotlib Renderer Demo")
    print("=" * 40)
    
    # Uncomment the demos you want to run:
    render_static()
    # render_with_faces()
    # create_animation()
    # create_4d_animation()
