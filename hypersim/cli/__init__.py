"""Command-line interface for hypersim."""

import argparse
from typing import Any

# No simulation engine needed for simple demo
from hypersim.objects import Hypercube
from hypersim.visualization.renderers.pygame import PygameRenderer, Color


def main(argv: list[str] | None = None) -> None:
    """Entry point for `python -m hypersim.cli` or `hypersim` console script."""
    parser = argparse.ArgumentParser(description="Run hypersim demos")
    parser.add_argument(
        "--demo",
        choices=["tesseract", "menu", "sandbox", "app"],
        default="tesseract",
        help="Which built-in demo to run",
    )
    args = parser.parse_args(argv)

    if args.demo == "tesseract":
        _run_tesseract_demo()
    elif args.demo == "menu":
        from .demo_menu import run_demo_menu
        run_demo_menu()
    elif args.demo == "sandbox":
        from .sandbox import run_sandbox
        run_sandbox()
    elif args.demo == "app":
        from .app_menu import run_app_menu
        run_app_menu()
    else:
        parser.error(f"Unknown demo: {args.demo}")


def _run_tesseract_demo() -> None:
    """Run the basic tesseract visualization using the internal architecture."""
    cube = Hypercube(size=1.5)

    # Create renderer with custom settings
    renderer = PygameRenderer(
        width=1024,
        height=768,
        title="Tesseract Demo"
    )
    
    # Set background color
    renderer.scene.background_color = Color(10, 10, 20)
    
    # Add the hypercube to the scene
    renderer.add_object(cube)
    
    # Run the render loop
    renderer.run()

__all__ = ["main"]
