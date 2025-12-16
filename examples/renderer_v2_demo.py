"""Example: Improved Pygame renderer demonstration.

Showcases the new renderer features including:
- Multiple render modes
- Proper camera controls
- HUD system
- Depth-based coloring
"""
import pygame
from hypersim.objects import Hypercube, TwentyFourCell, SixteenCell
from hypersim.visualization.renderers.pygame.renderer_v2 import (
    Renderer,
    RendererConfig,
    RenderMode,
)
from hypersim.visualization.renderers.pygame.render_pipeline import RenderStyle


def main():
    # Create renderer with custom config
    config = RendererConfig(
        width=1280,
        height=900,
        title="HyperSim - Improved Renderer Demo",
        background_color=(5, 5, 15),
        target_fps=60,
        default_render_mode=RenderMode.DEPTH_COLORED,
        default_line_width=2,
        auto_spin=True,
        show_fps=True,
        show_stats=True,
    )
    
    renderer = Renderer(config)
    
    # Create objects with different styles
    cube = Hypercube(size=1.0)
    cube.set_position(-2.0, 0, 0, 0)
    
    cell24 = TwentyFourCell(size=0.8)
    
    cell16 = SixteenCell(size=1.0)
    cell16.set_position(2.0, 0, 0, 0)
    
    # Add objects with custom styles
    renderer.add_object(cube, RenderStyle(
        mode=RenderMode.DEPTH_COLORED,
        near_color=(100, 255, 200),
        far_color=(20, 60, 80),
        line_width=2,
    ))
    
    renderer.add_object(cell24, RenderStyle(
        mode=RenderMode.DEPTH_COLORED,
        near_color=(255, 200, 100),
        far_color=(80, 40, 20),
        line_width=2,
    ))
    
    renderer.add_object(cell16, RenderStyle(
        mode=RenderMode.DEPTH_COLORED,
        near_color=(200, 100, 255),
        far_color=(40, 20, 80),
        line_width=2,
    ))
    
    # Add instructions to HUD
    from hypersim.visualization.renderers.pygame.hud import Anchor, HUDStyle
    renderer.hud.add_element(
        "title",
        "Improved Renderer Demo",
        anchor=Anchor.TOP_LEFT,
        style=HUDStyle(font_size=24, color=(255, 255, 255), background_color=None),
    )
    
    renderer.hud.add_element(
        "controls",
        "F: Cycle modes | T: Toggle spin | H: Help | Tab: Stats",
        anchor=Anchor.BOTTOM_CENTER,
        style=HUDStyle(font_size=16, color=(150, 150, 170), background_color=None),
    )
    
    print("\nImproved Renderer Demo")
    print("=" * 40)
    print("Controls:")
    print("  Mouse drag: Orbit camera")
    print("  Scroll: Zoom")
    print("  F: Cycle render modes")
    print("  T: Toggle auto-spin")
    print("  Tab: Toggle stats")
    print("  H: Toggle help")
    print("  R: Reset view")
    print("  ESC: Quit")
    print()
    
    # Run the renderer
    renderer.run()


if __name__ == "__main__":
    main()
