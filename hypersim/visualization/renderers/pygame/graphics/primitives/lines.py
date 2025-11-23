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
        zbuffer: Z-buffer for depth testing (optional)
    """
    if camera is None:
        raise ValueError("Camera instance is required for 4D projection")
    
    # Project 4D points to 2D screen space
    try:
        x1, y1, z1 = camera.project_4d_to_2d(start)
        x2, y2, z2 = camera.project_4d_to_2d(end)
    except Exception:
        # Skip if projection fails
        return

    # Skip if projection returned non-finite values
    if not np.isfinite([x1, y1, z1, x2, y2, z2]).all():
        return
    
    # Skip drawing if both points are behind the camera
    near_plane = 0.1
    far_plane = 100.0
    if camera is not None and hasattr(camera, "distance"):
        near_plane = max(0.05, float(camera.distance) * 0.05)
        far_plane = float(camera.distance) * 40.0
    
    # Clip line against near and far planes
    if z1 < near_plane and z2 < near_plane:
        return  # Both points behind near plane
    if z1 > far_plane and z2 > far_plane:
        return  # Both points beyond far plane
    
    # Clip line against near plane
    if z2 != z1:
        if z1 < near_plane:
            t = (near_plane - z1) / (z2 - z1)
            x1 = x1 + t * (x2 - x1)
            y1 = y1 + t * (y2 - y1)
            z1 = near_plane
        elif z2 < near_plane:
            t = (near_plane - z2) / (z1 - z2)
            x2 = x2 + t * (x1 - x2)
            y2 = y2 + t * (y1 - y2)
            z2 = near_plane
    
    # Skip if line is completely outside the viewport with some padding
    viewport_padding = 100  # pixels
    surface_width, surface_height = surface.get_size()
    min_x = -viewport_padding
    max_x = surface_width + viewport_padding
    min_y = -viewport_padding
    max_y = surface_height + viewport_padding
    
    # Cohen-Sutherland line clipping
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
        if not (outcode1 | outcode2):  # Both points inside viewport
            accept = True
            break
        elif outcode1 & outcode2:  # Both points outside viewport on same side
            return
        else:
            # Calculate intersection
            x, y = 0, 0
            outcode = outcode1 if outcode1 else outcode2
            
            # Calculate intersection with viewport edges
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
            
            # Update the point outside the viewport
            if outcode == outcode1:
                x1, y1 = x, y
                outcode1 = compute_outcode(x1, y1)
            else:
                x2, y2 = x, y
                outcode2 = compute_outcode(x2, y2)
    
    if not accept:
        return
    
    # Simple z-buffering (if provided)
    if zbuffer is not None:
        # Use the closer of the two z-values for z-buffering
        z = min(z1, z2)
        # Sample multiple points along the line for better z-buffering
        num_samples = 5
        for i in range(num_samples):
            t = i / (num_samples - 1)
            x = int(x1 * (1 - t) + x2 * t)
            y = int(y1 * (1 - t) + y2 * t)
            
            if 0 <= x < zbuffer.shape[0] and 0 <= y < zbuffer.shape[1]:
                if z < zbuffer[x, y]:
                    zbuffer[x, y] = z
                else:
                    # Optional: early exit if we hit an occluding surface
                    continue
    
    # Draw the line with anti-aliasing
    try:
        pygame.draw.aaline(
            surface,
            color.to_tuple(),
            (int(round(x1)), int(round(y1))),
            (int(round(x2)), int(round(y2))),
            True  # Blend with the existing pixels
        )
    except:
        # Fall back to regular line if aaline fails
        pygame.draw.line(
            surface,
            color.to_tuple(),
            (int(round(x1)), int(round(y1))),
            (int(round(x2)), int(round(y2))),
            width
        )
    
