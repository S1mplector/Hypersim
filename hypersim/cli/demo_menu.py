"""Interactive Pygame menu to browse built-in 4D object demos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

import pygame

from hypersim.objects import Hypercube, Simplex4D, SixteenCell
from hypersim.visualization.renderers.pygame import Color, PygameRenderer


@dataclass
class DemoEntry:
    name: str
    description: str
    factory: Callable[[], object]
    color: Color
    line_width: int = 2


def run_demo_menu() -> None:
    """Launch a simple menu for cycling through the built-in 4D shapes."""
    demos: List[DemoEntry] = [
        DemoEntry(
            name="Hypercube (Tesseract)",
            description="16 vertices, 32 edges. Classic wireframe cube-in-cube.",
            factory=lambda: Hypercube(size=1.3),
            color=Color(90, 200, 255),
        ),
        DemoEntry(
            name="4D Simplex (5-cell)",
            description="5 vertices fully connected, smooth rotation.",
            factory=lambda: Simplex4D(size=1.3),
            color=Color(255, 150, 90),
        ),
        DemoEntry(
            name="16-cell (Hyperoctahedron)",
            description="8 vertices on axes, 24 edges.",
            factory=lambda: SixteenCell(size=1.1),
            color=Color(140, 255, 160),
        ),
    ]

    renderer = PygameRenderer(
        width=1100,
        height=800,
        title="HyperSim Demo Menu",
        background_color=Color(12, 12, 22),
        distance=5.0,
    )

    state = {"index": 0, "active": None}

    def load_demo(new_index: int) -> None:
        """Instantiate and display the selected demo."""
        state["index"] = new_index % len(demos)
        demo = demos[state["index"]]
        renderer.clear_scene()
        shape = demo.factory()
        # Attach display hints
        setattr(shape, "color", demo.color)
        setattr(shape, "line_width", demo.line_width)
        # Gentle initial orientation
        if hasattr(shape, "rotate"):
            shape.rotate(xy=0.35, xw=0.28, yw=0.22, zw=0.18)
        state["active"] = shape
        renderer.add_object(shape)

    def next_demo() -> None:
        load_demo(state["index"] + 1)

    def prev_demo() -> None:
        load_demo(state["index"] - 1)

    def reset_demo() -> None:
        load_demo(state["index"])

    # Bind menu controls before entering the loop
    renderer.input_handler.register_key_handler(pygame.K_RIGHT, next_demo)
    renderer.input_handler.register_key_handler(pygame.K_LEFT, prev_demo)
    renderer.input_handler.register_key_handler(pygame.K_SPACE, reset_demo)

    load_demo(0)

    font_title = pygame.font.SysFont("Arial", 26)
    font_body = pygame.font.SysFont("Arial", 18)
    clock = renderer.clock
    target_fps = 60
    last_time = pygame.time.get_ticks() / 1000.0

    def draw_overlay() -> None:
        """Draw menu text and stats over the scene."""
        screen = renderer.screen
        overlay = pygame.Surface((screen.get_width(), 140), pygame.SRCALPHA)
        overlay.fill((8, 8, 16, 190))
        screen.blit(overlay, (0, 0))

        demo = demos[state["index"]]
        color = demo.color.to_tuple()[:3]
        text_y = 16
        screen.blit(font_title.render("HyperSim Demo Menu", True, (220, 220, 245)), (18, text_y))
        text_y += 34
        screen.blit(font_body.render(f"[{state['index'] + 1}/{len(demos)}] {demo.name}", True, color), (18, text_y))
        text_y += 26
        screen.blit(font_body.render(demo.description, True, (200, 200, 210)), (18, text_y))
        text_y += 30

        # Stats if available
        shape = state["active"]
        if shape is not None:
            stats = [
                f"Vertices: {getattr(shape, 'get_vertex_count', lambda: len(getattr(shape, 'vertices', [])))()}",
                f"Edges: {getattr(shape, 'get_edge_count', lambda: len(getattr(shape, 'edges', [])))()}",
            ]
            if hasattr(shape, "get_face_count"):
                stats.append(f"Faces: {shape.get_face_count()}")
            if hasattr(shape, "get_cell_count"):
                stats.append(f"Cells: {shape.get_cell_count()}")
            stats_text = " | ".join(stats)
            screen.blit(font_body.render(stats_text, True, (180, 200, 220)), (18, text_y))
        text_y += 26

        controls = "Left/Right: cycle demos   Space: reset demo   Drag + LMB: orbit camera   +/-: zoom   Esc: quit"
        screen.blit(font_body.render(controls, True, (170, 180, 200)), (18, text_y))

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        last_time = now

        running = renderer.input_handler.handle_events()

        # Mild idle rotation for visual interest
        obj = state["active"]
        if obj is not None and hasattr(obj, "rotate"):
            obj.rotate(xy=dt * 0.6, xw=dt * 0.4, yw=dt * 0.35, zw=dt * 0.3)

        renderer.update(dt)
        renderer.scene.render(renderer)
        draw_overlay()
        pygame.display.flip()
        clock.tick(target_fps)

    pygame.quit()
