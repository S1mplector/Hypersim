"""Basic example: Display a rotating hypercube (tesseract).

This example demonstrates the simplest usage of hypersim to create
and visualize a 4D hypercube with interactive controls.

Controls:
    - Mouse drag: Orbit camera
    - +/-: Zoom in/out
    - Z/X: Move along W axis
    - WASD: Move camera
    - ESC: Quit
"""
import pygame
from hypersim.objects import Hypercube
from hypersim.visualization.renderers.pygame import PygameRenderer, Color


def main():
    # Create a renderer window
    renderer = PygameRenderer(
        width=1024,
        height=768,
        title="HyperSim - Basic Hypercube",
        background_color=Color(10, 10, 20),
        distance=5.0,
    )

    # Create a hypercube (tesseract)
    cube = Hypercube(size=1.5)
    cube.set_position([0, 0, 0, 1.0])
    cube.rotate(xy=0.3, xw=0.2, zw=0.1)

    # Render loop
    running = True
    clock = pygame.time.Clock()
    last_time = pygame.time.get_ticks() / 1000.0

    while running:
        # Calculate delta time
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Update rotation
        cube.rotate(xy=dt * 0.5, xw=dt * 0.3, zw=dt * 0.2)

        # Render
        renderer.clear()
        renderer.render_4d_object(cube, Color(80, 200, 255), 2)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
