"""Example: Display multiple 4D objects in the same scene.

This example shows how to create and render multiple different
4D geometric objects simultaneously with different colors.

Controls:
    - Mouse drag: Orbit camera
    - +/-: Zoom in/out
    - ESC: Quit
"""
import pygame
from hypersim.objects import Hypercube, Simplex4D, SixteenCell
from hypersim.visualization.renderers.pygame import PygameRenderer, Color


def main():
    renderer = PygameRenderer(
        width=1200,
        height=800,
        title="HyperSim - Multiple Objects",
        background_color=Color(5, 5, 15),
        distance=6.0,
    )

    # Create multiple objects at different positions
    cube = Hypercube(size=0.8)
    cube.set_position([-2.5, 0, 0, 0])

    simplex = Simplex4D(size=1.0)
    simplex.set_position([0, 0, 0, 0])

    cell16 = SixteenCell(size=1.0)
    cell16.set_position([2.5, 0, 0, 0])

    objects = [
        (cube, Color(80, 200, 255)),      # Cyan
        (simplex, Color(255, 150, 80)),   # Orange
        (cell16, Color(150, 255, 150)),   # Green
    ]

    running = True
    clock = pygame.time.Clock()
    last_time = pygame.time.get_ticks() / 1000.0

    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Rotate each object differently
        cube.rotate(xy=dt * 0.4, xw=dt * 0.3)
        simplex.rotate(xz=dt * 0.5, yw=dt * 0.4)
        cell16.rotate(yz=dt * 0.3, zw=dt * 0.5)

        renderer.clear()
        for obj, color in objects:
            renderer.render_4d_object(obj, color, 2)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
