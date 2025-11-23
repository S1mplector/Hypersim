"""Interactive Pygame menu to browse built-in 4D object demos."""

from __future__ import annotations

import math
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
    SimplexPrism,
    RectifiedTesseract,
    CubePrism,
    Spherinder,
    Mobius4D,
    IcosaPrism,
)
from hypersim.visualization.renderers.pygame import Color, PygameRenderer


@dataclass
class DemoEntry:
    name: str
    description: str
    factory: Callable[[], object]
    color: Color
    line_width: int = 2
    category: str = "General"
    info: str = ""


def run_demo_menu() -> None:
    """Launch a simple menu for cycling through the built-in 4D shapes."""
    demos: List[DemoEntry] = [
        DemoEntry(
            name="Hypercube (Tesseract)",
            description="16 vertices, 32 edges. Classic wireframe cube-in-cube.",
            factory=lambda: Hypercube(size=1.3),
            color=Color(90, 200, 255),
            category="Regular polytopes",
            info="Vertices: (±1, ±1, ±1, ±1). 16 vertices, 32 edges, 24 square faces, 8 cubic cells. Dual of the 16-cell; cartesian product of two squares.",
        ),
        DemoEntry(
            name="4D Simplex (5-cell)",
            description="5 vertices fully connected, smooth rotation.",
            factory=lambda: Simplex4D(size=1.3),
            color=Color(255, 150, 90),
            category="Regular polytopes",
            info="Regular simplex in 4D: 5 vertices, 10 edges, 10 triangular faces, 5 tetrahedral cells. Vertices form a basis with equal pairwise distances.",
        ),
        DemoEntry(
            name="16-cell (Hyperoctahedron)",
            description="8 vertices on axes, 24 edges.",
            factory=lambda: SixteenCell(size=1.1),
            color=Color(140, 255, 160),
            category="Regular polytopes",
            info="Vertices at ±axes: (±1,0,0,0), etc. 8 vertices, 24 edges, 32 triangular faces, 16 tetrahedral cells. Dual of the tesseract; edge length tuned to size.",
        ),
        DemoEntry(
            name="24-cell (Icositetrachoron)",
            description="Self-dual regular polytope with 24 vertices, 96 edges.",
            factory=lambda: TwentyFourCell(size=1.1),
            color=Color(200, 130, 255),
            line_width=2,
            category="Regular polytopes",
            info="Self-dual regular 4-polytope. 24 vertices: 8 axis points ±1 and 16 half-points (±1/2,±1/2,±1/2,±1/2). 96 edges; cells are octahedra.",
        ),
        DemoEntry(
            name="Rectified Tesseract",
            description="Cuboctachoron: rectified hypercube with 24 vertices.",
            factory=lambda: RectifiedTesseract(size=1.2),
            color=Color(180, 220, 255),
            category="Regular polytopes",
            line_width=2,
            info="Vertices are midpoints of tesseract edges: permutations of (±1, ±1, 0, 0). 24 vertices, 96 edges; faces are triangles and squares.",
        ),
        DemoEntry(
            name="Duoprism (3x4)",
            description="Cartesian product of triangle and square; 12 vertices on a 4D torus.",
            factory=lambda: Duoprism(m=3, n=4, size=1.1),
            color=Color(255, 220, 120),
            line_width=2,
            category="Products / prisms",
            info="Vertices at (cos 2πi/3, sin 2πi/3, cos 2πj/4, sin 2πj/4). 12 vertices. Edges wrap along both polygon rings; topology is a flat 2-torus embedded in 4D.",
        ),
        DemoEntry(
            name="Simplex Prism",
            description="Prism over a 5-cell (two simplexes connected along W).",
            factory=lambda: SimplexPrism(size=1.1, height=0.75),
            color=Color(255, 180, 120),
            line_width=2,
            category="Products / prisms",
            info="Two 5-cells separated in W and joined vertex-to-vertex. 10 vertices. Edges: 10 + 10 within each simplex + 5 vertical links.",
        ),
        DemoEntry(
            name="Cube Prism",
            description="3D cube extruded along W; 16 vertices.",
            factory=lambda: CubePrism(size=1.2, height=1.0),
            color=Color(200, 255, 140),
            line_width=2,
            category="Products / prisms",
            info="Cartesian product of a cube and a segment in W. Two cubes linked vertex-to-vertex along W. 16 vertices, 48 edges.",
        ),
        DemoEntry(
            name="Icosahedron Prism",
            description="Regular icosahedron duplicated and linked along W.",
            factory=lambda: IcosaPrism(size=1.0, height=1.0),
            color=Color(255, 210, 150),
            line_width=1,
            category="Products / prisms",
            info="Two icosahedra offset in W and connected vertex-to-vertex. Base layer: 12 vertices, 30 edges; doubled to 24 verts plus 12 vertical links (90 edges total).",
        ),
        DemoEntry(
            name="Hypercube Grid (3x3x3x3)",
            description="Regular lattice in 4D; edges connect immediate neighbors.",
            factory=lambda: HypercubeGrid(divisions=3, size=1.0),
            color=Color(120, 200, 255),
            line_width=1,
            category="Lattices / procedural",
            info="Grid on [-size, size]^4 with nearest-neighbor edges in each axis direction. Vertices = divisions^4; edges = 4*(divisions-1)*divisions^3.",
        ),
        DemoEntry(
            name="Clifford Torus",
            description="S1 x S1 embedded in S3; a 4D torus wireframe.",
            factory=lambda: CliffordTorus(segments_u=28, segments_v=16, size=1.0),
            color=Color(255, 160, 200),
            line_width=1,
            category="Tori / manifolds",
            info="Parameterized by angles (u,v): (cos u, sin u, cos v, sin v)/√2. Flat torus embedded in S3; edges wrap along both angular directions.",
        ),
        DemoEntry(
            name="Spherinder",
            description="Sphere extruded along W; think '4D cylinder with spherical cross-sections'.",
            factory=lambda: Spherinder(radius=1.0, height=1.0, segments=24, stacks=12),
            color=Color(200, 255, 200),
            line_width=1,
            category="Manifolds / surfaces",
            info="Parametric surface: (r cosθ sinφ, r sinθ sinφ, r cosφ, w) with w∈{-h/2,+h/2}. Two spherical skins connected across W approximate the spherinder hull.",
        ),
        DemoEntry(
            name="Möbius Band (4D)",
            description="A Möbius strip embedded in 4D to resolve self-intersection.",
            factory=lambda: Mobius4D(radius=1.0, width=0.5, segments_u=72, segments_v=14),
            color=Color(255, 220, 160),
            line_width=1,
            category="Manifolds / surfaces",
            info="Embedded Möbius band: ( (R+v cos u/2)cos u, (R+v cos u/2)sin u, v sin u/2, 0.8 v sin(u/2+π/4) ), with v∈[-w/2,w/2], u∈[0,2π). Wrap connects v reversed to create the single-sided strip.",
        ),
    ]

    renderer = PygameRenderer(
        width=1100,
        height=800,
        title="HyperSim Demo Menu",
        background_color=Color(12, 12, 22),
        distance=5.0,
        auto_spin=False,
    )

    # Flatten and group demos by category for navigation/display
    categories: List[str] = []
    for entry in demos:
        if entry.category not in categories:
            categories.append(entry.category)
    state = {
        "index": 0,
        "active": None,
        "mode": "preview",
        "show_info": False,
        "info_hover": False,
    }  # modes: preview | viewer

    info_center = (1100 - 40, 40)
    info_radius = 16

    def is_over_info(pos: tuple[int, int]) -> bool:
        dx = pos[0] - info_center[0]
        dy = pos[1] - info_center[1]
        return dx * dx + dy * dy <= (info_radius + 6) ** 2

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

        # Info badge (top-right)
        badge_color = (120, 210, 255) if state["info_hover"] else (80, 180, 255)
        if state["show_info"]:
            badge_color = (255, 210, 120)
        pygame.draw.circle(screen, badge_color, info_center, info_radius, width=2)
        pygame.draw.line(screen, badge_color, (info_center[0], info_center[1] - 6), (info_center[0], info_center[1] + 6), 2)
        pygame.draw.circle(screen, badge_color, (info_center[0], info_center[1] - 10), 2)

        if state["show_info"] and demo.info:
            info_overlay = pygame.Surface((screen.get_width(), 200), pygame.SRCALPHA)
            info_overlay.fill((12, 12, 24, 220))
            screen.blit(info_overlay, (0, screen.get_height() - 220))
            lines = demo.info.split(". ")
            info_y = screen.get_height() - 200
            screen.blit(font_title.render("Info", True, (220, 220, 245)), (18, info_y))
            info_y += 28
            for line in lines:
                if not line.endswith("."):
                    line += "."
                screen.blit(font_body.render(line.strip(), True, (200, 200, 210)), (24, info_y))
                info_y += 22

        if state["mode"] == "preview":
            controls = "Enter/Space: start viewer   Up/Down/Left/Right: choose demo   Esc: quit"
        else:
            controls = "Left/Right: cycle demos   Space: reset demo   M: back to menu   Drag+LMB: orbit   +/-: zoom   Z/X: move W   Esc: quit"
        screen.blit(font_body.render(controls, True, (170, 180, 200)), (18, text_y))

        # On preview, show a scrollable list on the right for quick reference
        if state["mode"] == "preview":
            list_overlay = pygame.Surface((360, screen.get_height()), pygame.SRCALPHA)
            list_overlay.fill((6, 6, 12, 190))
            list_x = screen.get_width() - 370
            screen.blit(list_overlay, (list_x, 0))
            list_y = 24
            current_category = None
            for idx, entry in enumerate(demos):
                if entry.category != current_category:
                    current_category = entry.category
                    list_y += 6
                    screen.blit(font_title.render(current_category, True, (220, 220, 245)), (list_x + 16, list_y))
                    list_y += 30
                highlight = idx == state["index"]
                name_color = (255, 220, 160) if highlight else (190, 190, 200)
                desc_color = (180, 180, 190)
                screen.blit(font_body.render(f"{idx+1}. {entry.name}", True, name_color), (list_x + 16, list_y))
                list_y += 22
                screen.blit(font_body.render(f"   {entry.description}", True, desc_color), (list_x + 16, list_y))
                list_y += 26

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0
        dt = now - last_time
        if dt > 0.5:
            dt = 0.0  # Skip huge jumps when tabbed out
        last_time = now

        # Event handling with mode awareness
        events = pygame.event.get()
        if state["mode"] == "preview":
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    state["info_hover"] = is_over_info(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if is_over_info(event.pos):
                        state["show_info"] = not state["show_info"]
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_i:
                        state["show_info"] = not state["show_info"]
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
            # Viewer mode: handle info button + delegate to input handler
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEMOTION:
                    state["info_hover"] = is_over_info(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if is_over_info(event.pos):
                        state["show_info"] = not state["show_info"]
                        continue
                if not running:
                    break
                # Delegate to input handler logic
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        continue
                    if event.key == pygame.K_i:
                        state["show_info"] = not state["show_info"]
                        continue
                    handler = renderer.input_handler._key_handlers.get(event.key)
                    if handler:
                        handler()
                    else:
                        renderer.input_handler.camera.handle_key_press(event.key)
                elif event.type in renderer.input_handler._mouse_handlers:
                    renderer.input_handler._mouse_handlers[event.type](event)

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
