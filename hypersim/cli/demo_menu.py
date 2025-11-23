"""Interactive Pygame menu to browse built-in 4D object demos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

import pygame

from hypersim.objects import (
    Hypercube,
    Simplex4D,
    SixteenCell,
    TwentyFourCell,
    Duoprism,
    HypercubeGrid,
    CliffordTorus,
)
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
        DemoEntry(
            name="24-cell (Icositetrachoron)",
            description="Self-dual regular polytope with 24 vertices, 96 edges.",
            factory=lambda: TwentyFourCell(size=1.1),
            color=Color(200, 130, 255),
            line_width=2,
        ),
        DemoEntry(
            name="Duoprism (3x4)",
            description="Cartesian product of triangle and square; 12 vertices on a 4D torus.",
            factory=lambda: Duoprism(m=3, n=4, size=1.1),
            color=Color(255, 220, 120),
            line_width=2,
        ),
        DemoEntry(
            name="Hypercube Grid (3x3x3x3)",
            description="Regular lattice in 4D; edges connect immediate neighbors.",
            factory=lambda: HypercubeGrid(divisions=3, size=1.0),
            color=Color(120, 200, 255),
            line_width=1,
        ),
        DemoEntry(
            name="Clifford Torus",
            description="S1 x S1 embedded in S3; a 4D torus wireframe.",
            factory=lambda: CliffordTorus(segments_u=28, segments_v=16, size=1.0),
            color=Color(255, 160, 200),
            line_width=1,
        ),
    ]

    renderer = PygameRenderer(
        width=1100,
        height=800,
        title="HyperSim Demo Menu",
        background_color=Color(12, 12, 22),
        distance=5.0,
    )

    state = {"index": 0, "active": None, "mode": "preview"}  # modes: preview | viewer

    def load_demo(new_index: int) -> None:
        """Instantiate and display the selected demo."""
        state["index"] = new_index % len(demos)
        demo = demos[state["index"]]
        renderer.clear_scene()
        try:
            shape = demo.factory()
        except Exception as exc:
            print(f"[demo_menu] Failed to create demo '{demo.name}': {exc}")
            state["active"] = None
            return

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

    def enter_viewer() -> None:
        state["mode"] = "viewer"

    def back_to_preview() -> None:
        state["mode"] = "preview"

    # Bind menu controls before entering the loop
    renderer.input_handler.register_key_handler(pygame.K_RIGHT, next_demo)
    renderer.input_handler.register_key_handler(pygame.K_LEFT, prev_demo)
    renderer.input_handler.register_key_handler(pygame.K_UP, prev_demo)
    renderer.input_handler.register_key_handler(pygame.K_DOWN, next_demo)
    renderer.input_handler.register_key_handler(pygame.K_SPACE, lambda: reset_demo() if state["mode"] == "viewer" else enter_viewer())
    renderer.input_handler.register_key_handler(pygame.K_RETURN, enter_viewer)
    renderer.input_handler.register_key_handler(pygame.K_m, back_to_preview)

    load_demo(0)

    font_title = pygame.font.SysFont("Arial", 26)
    font_body = pygame.font.SysFont("Arial", 18)
    clock = renderer.clock
    target_fps = 60
    last_time = pygame.time.get_ticks() / 1000.0

    def draw_overlay() -> None:
        """Draw overlay depending on mode (preview or viewer)."""
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

        if state["mode"] == "preview":
            controls = "Enter/Space: start viewer   Up/Down/Left/Right: choose demo   Esc: quit"
        else:
            controls = "Left/Right: cycle demos   Space: reset demo   M: back to menu   Drag+LMB: orbit   +/-: zoom   Esc: quit"
        screen.blit(font_body.render(controls, True, (170, 180, 200)), (18, text_y))

        # On preview, show a scrollable list on the right for quick reference
        if state["mode"] == "preview":
            list_overlay = pygame.Surface((320, screen.get_height()), pygame.SRCALPHA)
            list_overlay.fill((6, 6, 12, 180))
            list_x = screen.get_width() - 330
            screen.blit(list_overlay, (list_x, 0))
            list_y = 24
            for idx, entry in enumerate(demos):
                highlight = idx == state["index"]
                name_color = (255, 220, 160) if highlight else (190, 190, 200)
                desc_color = (180, 180, 190)
                screen.blit(font_body.render(f"{idx+1}. {entry.name}", True, name_color), (list_x + 16, list_y))
                list_y += 22
                desc_lines = [entry.description]
                for line in desc_lines:
                    screen.blit(font_body.render(f"   {line}", True, desc_color), (list_x + 16, list_y))
                    list_y += 20
                list_y += 6

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        if dt > 0.5:
            dt = 0.0  # Skip huge jumps when tabbed out
        last_time = now

        # Event handling with mode awareness
        if state["mode"] == "preview":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        enter_viewer()
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        prev_demo()
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        next_demo()
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        prev_demo()
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        next_demo()
        else:
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
