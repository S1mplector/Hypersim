"""Interactive 4D sandbox for spawning shapes of varying sizes."""
from __future__ import annotations

import random
from typing import Callable, Dict, List

import numpy as np
import pygame

from hypersim.visualization.renderers.pygame import Color, PygameRenderer
from hypersim.objects import (
    Hypercube,
    Simplex4D,
    SixteenCell,
    TwentyFourCell,
    RectifiedTesseract,
    CubePrism,
    IcosaPrism,
    PenteractFrame,
    Spherinder,
    Mobius4D,
    HypercubeGrid,
    Duoprism,
    SimplexPrism,
)

SpawnFn = Callable[[float], object]


def _palette() -> List[Color]:
    return [
        Color(120, 200, 255),
        Color(255, 180, 140),
        Color(180, 255, 180),
        Color(255, 220, 160),
        Color(190, 160, 255),
        Color(255, 140, 200),
    ]


def _rand_color() -> Color:
    return random.choice(_palette())


def _spawn_map() -> Dict[int, SpawnFn]:
    return {
        pygame.K_1: lambda s: Hypercube(size=s),
        pygame.K_2: lambda s: Simplex4D(size=s),
        pygame.K_3: lambda s: SixteenCell(size=s),
        pygame.K_4: lambda s: TwentyFourCell(size=s),
        pygame.K_5: lambda s: RectifiedTesseract(size=s),
        pygame.K_6: lambda s: Duoprism(m=3, n=4, size=s),
        pygame.K_7: lambda s: CubePrism(size=s, height=s * 0.8),
        pygame.K_8: lambda s: IcosaPrism(size=s, height=s * 0.8),
        pygame.K_9: lambda s: SimplexPrism(size=s, height=s * 0.6),
        pygame.K_0: lambda s: PenteractFrame(size=s),
        pygame.K_q: lambda s: Spherinder(radius=s * 0.8, height=s * 0.8),
        pygame.K_w: lambda s: Mobius4D(radius=s, width=s * 0.4),
        pygame.K_e: lambda s: HypercubeGrid(divisions=3, size=s * 0.7),
    }


def _set_shape_defaults(shape: object, size: float) -> None:
    # Random small offset in XYZ and a forward bias in W for visibility
    if hasattr(shape, "set_position"):
        offset = np.array(
            [
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5),
                random.uniform(-0.5, 0.5),
                random.uniform(0.3, 1.0),
            ],
            dtype=np.float32,
        )
        shape.set_position(offset)
    if hasattr(shape, "line_width"):
        shape.line_width = getattr(shape, "line_width", 2) + 0  # keep if preset


def run_sandbox() -> None:
    renderer = PygameRenderer(
        width=1280,
        height=900,
        title="HyperSim 4D Sandbox",
        background_color=Color(12, 12, 22),
        distance=7.0,
        auto_spin=False,
    )
    clock = renderer.clock
    target_fps = 60
    spawn_size = 1.2
    shapes: List[object] = []
    spawners = _spawn_map()

    font = pygame.font.SysFont("Arial", 18)
    heading_font = pygame.font.SysFont("Arial", 24, bold=True)

    def spawn(key: int) -> None:
        if key not in spawners:
            return
        shape = spawners[key](spawn_size)
        shape.color = _rand_color()
        _set_shape_defaults(shape, spawn_size)
        renderer.add_object(shape)
        shapes.append(shape)

    def clear() -> None:
        shapes.clear()
        renderer.clear_scene()

    running = True
    last_time = pygame.time.get_ticks() / 1000.0
    rotating = False
    last_mouse = (0, 0)

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
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    spawn_size = max(0.2, spawn_size - 0.1)
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    spawn_size = min(3.0, spawn_size + 0.1)
                elif event.key == pygame.K_c:
                    clear()
                elif event.key in spawners:
                    spawn(event.key)
                else:
                    renderer.camera.handle_key_press(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rotating = True
                last_mouse = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                rotating = False
            elif event.type == pygame.MOUSEMOTION and rotating:
                dx = event.pos[0] - last_mouse[0]
                dy = event.pos[1] - last_mouse[1]
                renderer.camera.handle_mouse_motion(dx, dy)
                last_mouse = event.pos

        renderer.update(dt)
        renderer.render()

        # HUD
        overlay = pygame.Surface((400, 160), pygame.SRCALPHA)
        overlay.fill((10, 10, 20, 180))
        renderer.screen.blit(overlay, (10, 10))
        y = 18
        renderer.screen.blit(
            heading_font.render("Sandbox Controls", True, (230, 230, 240)), (20, y)
        )
        y += 28
        lines = [
            f"Spawn size: {spawn_size:.2f}   +/- to adjust",
            "1-0,q,w,e: spawn shapes; C: clear",
            "WASD/QE: move XYZ, Z/X: move W",
            "Drag+LMB: orbit camera   Esc: quit",
        ]
        for line in lines:
            renderer.screen.blit(font.render(line, True, (200, 200, 210)), (20, y))
            y += 22
        count_line = f"Objects: {len(shapes)}"
        renderer.screen.blit(font.render(count_line, True, (180, 200, 200)), (20, y))

        pygame.display.flip()
        clock.tick(target_fps)

    pygame.quit()
