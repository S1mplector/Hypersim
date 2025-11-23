"""Main Hypersim application menu with gallery and sandbox modes."""
from __future__ import annotations

import math
from typing import List, Tuple

import numpy as np
import pygame

from hypersim.visualization.renderers.pygame import Color
from hypersim.core.math_4d import perspective_projection_4d_to_3d
from hypersim.cli.demo_menu import run_demo_menu, get_demo_entries
from hypersim.cli.sandbox import run_sandbox


class Card:
    def __init__(self, rect: pygame.Rect, index: int):
        self.rect = rect
        self.index = index
        self.hover = False


def _project_point(v4: np.ndarray, distance: float = 4.0, scale: float = 80.0, w2d: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
    proj3 = perspective_projection_4d_to_3d(v4[np.newaxis, :], distance)[0]
    x = int(proj3[0] * scale + w2d[0])
    y = int(-proj3[1] * scale + w2d[1])
    return x, y


def _render_preview(surface: pygame.Surface, shape, bg: Color) -> None:
    surface.fill(bg.to_tuple())
    center = (surface.get_width() // 2, surface.get_height() // 2)
    verts = shape.get_transformed_vertices()
    for a, b in getattr(shape, "edges", []):
        pa = _project_point(verts[a], distance=5.0, scale=70.0, w2d=center)
        pb = _project_point(verts[b], distance=5.0, scale=70.0, w2d=center)
        pygame.draw.line(surface, shape.color.to_tuple(), pa, pb, getattr(shape, "line_width", 2))


def _build_cards(area: pygame.Rect, card_w: int, card_h: int, count: int, cols: int = 3, gutter: int = 20) -> List[Card]:
    cards: List[Card] = []
    x0, y0 = area.topleft
    col = 0
    row = 0
    for idx in range(count):
        x = x0 + col * (card_w + gutter)
        y = y0 + row * (card_h + gutter)
        cards.append(Card(pygame.Rect(x, y, card_w, card_h), idx))
        col += 1
        if col >= cols:
            col = 0
            row += 1
    return cards


def run_app_menu() -> None:
    pygame.init()
    width, height = 1280, 900
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Hypersim")
    clock = pygame.time.Clock()

    demos = get_demo_entries()
    # Pre-create preview shapes
    preview_shapes = []
    for entry in demos:
        shape = entry.factory()
        setattr(shape, "color", entry.color)
        setattr(shape, "line_width", entry.line_width)
        preview_shapes.append(shape)

    cards = _build_cards(pygame.Rect(40, 140, width - 80, height - 240), 360, 220, len(demos), cols=3, gutter=24)
    bg_color = Color(12, 12, 22)
    heading_font = pygame.font.SysFont("Arial", 32, bold=True)
    sub_font = pygame.font.SysFont("Arial", 20)
    card_title = pygame.font.SysFont("Arial", 18, bold=True)
    card_desc = pygame.font.SysFont("Arial", 15)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Sandbox button
                if sandbox_btn.collidepoint(pos):
                    pygame.display.set_caption("Hypersim - Sandbox")
                    run_sandbox()
                    pygame.init()
                    screen = pygame.display.set_mode((width, height))
                    pygame.display.set_caption("Hypersim")
                    clock = pygame.time.Clock()
                # Card clicks
                for card in cards:
                    if card.rect.collidepoint(pos):
                        pygame.display.set_caption("Hypersim - Gallery")
                        run_demo_menu(start_index=card.index)
                        pygame.init()
                        screen = pygame.display.set_mode((width, height))
                        pygame.display.set_caption("Hypersim")
                        clock = pygame.time.Clock()
                        break

        mouse_pos = pygame.mouse.get_pos()
        screen.fill(bg_color.to_tuple())

        # Header
        screen.blit(heading_font.render("Hypersim", True, (230, 230, 240)), (40, 40))
        screen.blit(sub_font.render("Choose a demo card or launch the sandbox.", True, (200, 200, 210)), (40, 80))

        # Sandbox button
        sandbox_btn = pygame.Rect(width - 220, 50, 160, 50)
        pygame.draw.rect(screen, (40, 120, 220), sandbox_btn, border_radius=8)
        screen.blit(card_title.render("Open Sandbox", True, (255, 255, 255)), (sandbox_btn.x + 16, sandbox_btn.y + 14))

        # Update hover
        for card in cards:
            card.hover = card.rect.collidepoint(mouse_pos)

        # Update and render previews
        for card in cards:
            # spin preview shapes lightly
            shape = preview_shapes[card.index]
            if hasattr(shape, "rotate"):
                shape.rotate(xy=dt * 0.4, xw=dt * 0.35, yw=dt * 0.3, zw=dt * 0.25)

            bg = (24, 24, 36) if card.hover else (16, 16, 26)
            pygame.draw.rect(screen, bg, card.rect, border_radius=10)
            pygame.draw.rect(screen, (60, 160, 255) if card.hover else (60, 60, 80), card.rect, 2, border_radius=10)

            preview_surface = pygame.Surface((card.rect.width, card.rect.height - 60), pygame.SRCALPHA)
            _render_preview(preview_surface, shape, Color(bg[0], bg[1], bg[2]))
            screen.blit(preview_surface, (card.rect.x, card.rect.y))

            # Title/description
            text_y = card.rect.y + card.rect.height - 56
            screen.blit(card_title.render(demos[card.index].name, True, (230, 230, 240)), (card.rect.x + 10, text_y))
            text_y += 20
            desc = card_desc.render(demos[card.index].description[:60], True, (200, 200, 210))
            screen.blit(desc, (card.rect.x + 10, text_y))

        pygame.display.flip()

    pygame.quit()
