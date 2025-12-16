"""Line drawing primitives for the Pygame renderer.

This module provides functions for drawing various types of lines and curves.
"""

from __future__ import annotations

from typing import Any, Optional, Tuple

import numpy as np
import pygame

from hypersim.core.math_4d import Vector4D
from ...graphics.color import Color

__all__ = ["draw_line_4d"]


def draw_line_4d(
    surface: pygame.Surface,
    start: Vector4D,
    end: Vector4D,
    color: Color,
    width: int = 2,
    camera: Any = None,
    zbuffer: Optional[np.ndarray] = None
) -> None:
    """Draw a 4D line on the given surface with improved clipping and rendering.
    
    Args:
        surface: The surface to draw on
        start: Start point in 4D space
        end: End point in 4D space
        color: Color of the line
        width: Width of the line in pixels
        camera: Camera instance for projection (must have project_4d_to_2d method)
        zbuffer: Z-buffer for depth testing (optional, shape (height, width))
    """
    if camera is None:
        raise ValueError("Camera instance is required for 4D projection")

    def _clip_against_w(p0: np.ndarray, p1: np.ndarray, max_w: float):
        w0, w1 = p0[3], p1[3]
        if w0 >= max_w and w1 >= max_w:
            return None
        if w0 >= max_w:
            t = (max_w - w0) / (w1 - w0)
            p0 = p0 + t * (p1 - p0)
        elif w1 >= max_w:
            t = (max_w - w1) / (w0 - w1)
            p1 = p1 + t * (p0 - p1)
        return p0, p1

    # Work in view space to clip before projecting
    view_start = camera.world_to_view(start)
    view_end = camera.world_to_view(end)
    max_w = float(camera.distance) - 0.05
    clipped = _clip_against_w(view_start, view_end, max_w)
    if clipped is None:
        return
    view_start, view_end = clipped

    try:
        x1, y1, z1 = camera.project_view_point(view_start)
        x2, y2, z2 = camera.project_view_point(view_end)
    except Exception:
        return

    if not np.isfinite([x1, y1, z1, x2, y2, z2]).all():
        return

    near_plane = max(0.05, float(camera.distance) * 0.05)
    far_plane = float(camera.distance) * 40.0
    if z1 < near_plane and z2 < near_plane:
        return
    if z1 > far_plane and z2 > far_plane:
        return

    viewport_padding = 100  # pixels
    surface_width, surface_height = surface.get_size()
    min_x = -viewport_padding
    max_x = surface_width + viewport_padding
    min_y = -viewport_padding
    max_y = surface_height + viewport_padding

    # Cohen-Sutherland line clipping in screen space
    def compute_outcode(x, y):
        code = 0
        if x < min_x: code |= 1
        if x > max_x: code |= 2
        if y < min_y: code |= 4
        if y > max_y: code |= 8
        return code

    outcode1 = compute_outcode(x1, y1)
    outcode2 = compute_outcode(x2, y2)
    accept = False

    while True:
        if not (outcode1 | outcode2):
            accept = True
            break
        if outcode1 & outcode2:
            return
        # Calculate intersection
        x, y = 0.0, 0.0
        outcode = outcode1 if outcode1 else outcode2

        if outcode & 8:  # Top
            x = x1 + (x2 - x1) * (max_y - y1) / (y2 - y1)
            y = max_y
        elif outcode & 4:  # Bottom
            x = x1 + (x2 - x1) * (min_y - y1) / (y2 - y1)
            y = min_y
        elif outcode & 2:  # Right
            y = y1 + (y2 - y1) * (max_x - x1) / (x2 - x1)
            x = max_x
        elif outcode & 1:  # Left
            y = y1 + (y2 - y1) * (min_x - x1) / (x2 - x1)
            x = min_x

        if outcode == outcode1:
            x1, y1 = x, y
            outcode1 = compute_outcode(x1, y1)
        else:
            x2, y2 = x, y
            outcode2 = compute_outcode(x2, y2)

    if not accept:
        return

    if zbuffer is not None:
        steps = int(max(abs(x2 - x1), abs(y2 - y1), 1))
        for i in range(steps + 1):
            t = 0.0 if steps == 0 else i / steps
            x = int(round(x1 + t * (x2 - x1)))
            y = int(round(y1 + t * (y2 - y1)))
            if 0 <= y < zbuffer.shape[0] and 0 <= x < zbuffer.shape[1]:
                depth = z1 + t * (z2 - z1)
                if depth < zbuffer[y, x]:
                    zbuffer[y, x] = depth

    # Draw the line with anti-aliasing
    try:
        pygame.draw.aaline(
            surface,
            color.to_tuple(),
            (int(round(x1)), int(round(y1))),
            (int(round(x2)), int(round(y2))),
            True,
        )
    except Exception:
        pygame.draw.line(
            surface,
            color.to_tuple(),
            (int(round(x1)), int(round(y1))),
            (int(round(x2)), int(round(y2))),
            width,
        )
    
