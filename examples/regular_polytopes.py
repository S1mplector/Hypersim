"""Example: Showcase all regular 4D polytopes (convex regular 4-polytopes).

There are exactly six regular convex 4-polytopes:
1. 5-cell (simplex) - 5 vertices
2. 8-cell (tesseract/hypercube) - 16 vertices  
3. 16-cell (hyperoctahedron) - 8 vertices
4. 24-cell - 24 vertices
5. 120-cell - 600 vertices
6. 600-cell - 120 vertices

This example cycles through them with information display.
"""
import pygame
from hypersim.objects import (
    Simplex4D,
    Hypercube,
    SixteenCell,
    TwentyFourCell,
    SixHundredCell,
)
from hypersim.visualization.renderers.pygame import PygameRenderer, Color


POLYTOPES = [
    {
        "name": "5-Cell (Simplex)",
        "factory": lambda: Simplex4D(size=1.3),
        "color": Color(255, 150, 90),
        "info": "5 vertices, 10 edges, 10 faces, 5 cells",
    },
    {
        "name": "8-Cell (Tesseract)",
        "factory": lambda: Hypercube(size=1.2),
        "color": Color(90, 200, 255),
        "info": "16 vertices, 32 edges, 24 faces, 8 cells",
    },
    {
        "name": "16-Cell (Hyperoctahedron)",
        "factory": lambda: SixteenCell(size=1.2),
        "color": Color(150, 255, 150),
        "info": "8 vertices, 24 edges, 32 faces, 16 cells",
    },
    {
        "name": "24-Cell",
        "factory": lambda: TwentyFourCell(size=1.1),
        "color": Color(200, 130, 255),
        "info": "24 vertices, 96 edges, 96 faces, 24 cells",
    },
    {
        "name": "600-Cell",
        "factory": lambda: SixHundredCell(size=1.0),
        "color": Color(255, 200, 120),
        "info": "120 vertices, 720 edges, 1200 faces, 600 cells",
    },
]


def main():
    renderer = PygameRenderer(
        width=1024,
        height=768,
        title="HyperSim - Regular 4-Polytopes",
        background_color=Color(8, 8, 18),
        distance=5.0,
    )

    current_index = 0
    current_obj = POLYTOPES[0]["factory"]()
    font = pygame.font.SysFont("Arial", 24)
    small_font = pygame.font.SysFont("Arial", 18)

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
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
                    current_index = (current_index + 1) % len(POLYTOPES)
                    current_obj = POLYTOPES[current_index]["factory"]()
                elif event.key == pygame.K_LEFT:
                    current_index = (current_index - 1) % len(POLYTOPES)
                    current_obj = POLYTOPES[current_index]["factory"]()

        current_obj.rotate(xy=dt * 0.5, xw=dt * 0.35, yw=dt * 0.3, zw=dt * 0.25)

        renderer.clear()
        polytope = POLYTOPES[current_index]
        renderer.render_4d_object(current_obj, polytope["color"], 2)

        # Draw info overlay
        screen = renderer.screen
        title = font.render(f"{polytope['name']} ({current_index + 1}/{len(POLYTOPES)})", True, (220, 220, 240))
        info = small_font.render(polytope["info"], True, (180, 180, 200))
        controls = small_font.render("Left/Right: Change polytope | ESC: Quit", True, (140, 140, 160))
        screen.blit(title, (20, 20))
        screen.blit(info, (20, 50))
        screen.blit(controls, (20, screen.get_height() - 30))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
