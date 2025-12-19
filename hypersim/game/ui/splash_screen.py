"""Splash screens for Tessera."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Callable

import pygame
import numpy as np


class SplashPhase(Enum):
    """Phases of splash animation."""
    FADE_IN = auto()
    HOLD = auto()
    FADE_OUT = auto()
    DONE = auto()


@dataclass
class SplashConfig:
    """Configuration for a splash screen."""
    text_primary: str
    text_secondary: str = ""
    fade_in_duration: float = 0.8
    hold_duration: float = 1.5
    fade_out_duration: float = 0.6
    bg_color: tuple = (5, 5, 10)
    primary_color: tuple = (255, 255, 255)
    secondary_color: tuple = (150, 150, 180)
    logo_path: Optional[str] = None


class SplashScreen:
    """Animated splash screen with fade effects."""
    
    def __init__(self, screen: pygame.Surface, config: SplashConfig):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.config = config
        
        self.phase = SplashPhase.FADE_IN
        self.phase_time = 0.0
        self.alpha = 0.0
        self.finished = False
        
        # Fonts
        self._font_primary = pygame.font.Font(None, 64)
        self._font_secondary = pygame.font.Font(None, 32)
        
        # Particles for extra flair
        self._particles = []
        self._init_particles()
    
    def _init_particles(self) -> None:
        """Initialize subtle background particles."""
        import random
        for _ in range(30):
            self._particles.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "size": random.uniform(1, 3),
                "speed": random.uniform(0.2, 0.8),
                "alpha": random.uniform(0.1, 0.4),
            })
    
    def update(self, dt: float) -> bool:
        """Update splash animation. Returns True when finished."""
        if self.finished:
            return True
        
        self.phase_time += dt
        
        if self.phase == SplashPhase.FADE_IN:
            progress = min(1.0, self.phase_time / self.config.fade_in_duration)
            self.alpha = self._ease_out(progress)
            if progress >= 1.0:
                self.phase = SplashPhase.HOLD
                self.phase_time = 0.0
        
        elif self.phase == SplashPhase.HOLD:
            self.alpha = 1.0
            if self.phase_time >= self.config.hold_duration:
                self.phase = SplashPhase.FADE_OUT
                self.phase_time = 0.0
        
        elif self.phase == SplashPhase.FADE_OUT:
            progress = min(1.0, self.phase_time / self.config.fade_out_duration)
            self.alpha = 1.0 - self._ease_in(progress)
            if progress >= 1.0:
                self.phase = SplashPhase.DONE
                self.finished = True
        
        # Update particles
        for p in self._particles:
            p["y"] -= p["speed"] * dt * 30
            if p["y"] < -10:
                p["y"] = self.height + 10
        
        return self.finished
    
    def _ease_out(self, t: float) -> float:
        """Ease out cubic."""
        return 1 - (1 - t) ** 3
    
    def _ease_in(self, t: float) -> float:
        """Ease in cubic."""
        return t ** 3
    
    def draw(self) -> None:
        """Draw the splash screen."""
        # Background
        self.screen.fill(self.config.bg_color)
        
        # Particles
        for p in self._particles:
            alpha = int(p["alpha"] * self.alpha * 255)
            if alpha > 0:
                color = (alpha // 2, alpha // 2, alpha)
                pygame.draw.circle(
                    self.screen, color,
                    (int(p["x"]), int(p["y"])),
                    int(p["size"])
                )
        
        # Primary text
        text_alpha = int(self.alpha * 255)
        primary_surface = self._font_primary.render(
            self.config.text_primary, True, self.config.primary_color
        )
        primary_surface.set_alpha(text_alpha)
        primary_rect = primary_surface.get_rect(center=(self.width // 2, self.height // 2 - 20))
        self.screen.blit(primary_surface, primary_rect)
        
        # Secondary text
        if self.config.text_secondary:
            secondary_surface = self._font_secondary.render(
                self.config.text_secondary, True, self.config.secondary_color
            )
            secondary_surface.set_alpha(text_alpha)
            secondary_rect = secondary_surface.get_rect(center=(self.width // 2, self.height // 2 + 30))
            self.screen.blit(secondary_surface, secondary_rect)
    
    def skip(self) -> None:
        """Skip to end of splash."""
        self.finished = True
        self.phase = SplashPhase.DONE


class HypersimEngineSplash(SplashScreen):
    """Special splash screen with animated hypercube for Hypersim Engine."""
    
    def __init__(self, screen: pygame.Surface, config: SplashConfig):
        super().__init__(screen, config)
        
        # Hypercube rotation angles
        self.angle_xw = 0.0
        self.angle_yw = 0.0
        self.angle_zw = 0.0
        self.angle_xy = 0.0
        
        # Generate tesseract vertices and edges
        self._vertices = self._generate_tesseract_vertices()
        self._edges = self._generate_tesseract_edges()
    
    def _generate_tesseract_vertices(self):
        """Generate the 16 vertices of a tesseract."""
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append(np.array([x, y, z, w], dtype=float))
        return vertices
    
    def _generate_tesseract_edges(self):
        """Generate the 32 edges of a tesseract."""
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                diff = bin(i ^ j).count('1')
                if diff == 1:
                    edges.append((i, j))
        return edges
    
    def _rotate_4d(self, vertex):
        """Apply 4D rotations."""
        x, y, z, w = vertex
        
        # XW rotation
        cos_xw, sin_xw = math.cos(self.angle_xw), math.sin(self.angle_xw)
        x, w = x * cos_xw - w * sin_xw, x * sin_xw + w * cos_xw
        
        # YW rotation
        cos_yw, sin_yw = math.cos(self.angle_yw), math.sin(self.angle_yw)
        y, w = y * cos_yw - w * sin_yw, y * sin_yw + w * cos_yw
        
        # ZW rotation
        cos_zw, sin_zw = math.cos(self.angle_zw), math.sin(self.angle_zw)
        z, w = z * cos_zw - w * sin_zw, z * sin_zw + w * cos_zw
        
        # XY rotation
        cos_xy, sin_xy = math.cos(self.angle_xy), math.sin(self.angle_xy)
        x, y = x * cos_xy - y * sin_xy, x * sin_xy + y * cos_xy
        
        return np.array([x, y, z, w])
    
    def _project_4d_to_2d(self, vertex, scale, center):
        """Project 4D vertex to 2D screen coordinates."""
        x, y, z, w = vertex
        
        # 4D to 3D perspective
        distance_4d = 2.5
        factor_4d = distance_4d / (distance_4d - w)
        x3d = x * factor_4d
        y3d = y * factor_4d
        z3d = z * factor_4d
        
        # 3D to 2D perspective
        distance_3d = 3.5
        factor_3d = distance_3d / (distance_3d - z3d)
        x2d = x3d * factor_3d
        y2d = y3d * factor_3d
        
        screen_x = int(center[0] + x2d * scale)
        screen_y = int(center[1] - y2d * scale)
        depth = w + z3d
        
        return (screen_x, screen_y, depth)
    
    def update(self, dt: float) -> bool:
        """Update splash and hypercube animation."""
        result = super().update(dt)
        
        # Rotate hypercube
        self.angle_xw += dt * 0.8
        self.angle_yw += dt * 0.6
        self.angle_zw += dt * 0.5
        self.angle_xy += dt * 0.3
        
        return result
    
    def draw(self) -> None:
        """Draw splash with animated hypercube."""
        # Background
        self.screen.fill(self.config.bg_color)
        
        # Particles
        for p in self._particles:
            alpha = int(p["alpha"] * self.alpha * 255)
            if alpha > 0:
                color = (alpha // 2, alpha // 2, alpha)
                pygame.draw.circle(
                    self.screen, color,
                    (int(p["x"]), int(p["y"])),
                    int(p["size"])
                )
        
        # Draw animated hypercube to the left of text
        text_alpha = int(self.alpha * 255)
        cube_center = (self.width // 2 - 180, self.height // 2 - 10)
        cube_scale = 35
        cube_color = (100, 200, 255)
        
        # Rotate and project vertices
        projected = []
        for v in self._vertices:
            rotated = self._rotate_4d(v)
            proj = self._project_4d_to_2d(rotated, cube_scale, cube_center)
            projected.append(proj)
        
        # Draw edges with alpha
        for i, j in self._edges:
            p1, p2 = projected[i], projected[j]
            avg_depth = (p1[2] + p2[2]) / 2
            depth_factor = (avg_depth + 2) / 4
            depth_factor = max(0.3, min(1.0, depth_factor))
            
            edge_color = tuple(int(c * depth_factor * self.alpha) for c in cube_color)
            if edge_color[0] > 0:
                pygame.draw.line(self.screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1)
        
        # Draw vertices
        for p in projected:
            depth_factor = (p[2] + 2) / 4
            depth_factor = max(0.3, min(1.0, depth_factor))
            vertex_alpha = int(depth_factor * self.alpha * 255)
            if vertex_alpha > 0:
                vertex_color = tuple(int(c * depth_factor * self.alpha) for c in cube_color)
                pygame.draw.circle(self.screen, vertex_color, (p[0], p[1]), 2)
        
        # Primary text (shifted right to make room for cube)
        primary_surface = self._font_primary.render(
            self.config.text_primary, True, self.config.primary_color
        )
        primary_surface.set_alpha(text_alpha)
        primary_rect = primary_surface.get_rect(center=(self.width // 2 + 40, self.height // 2 - 20))
        self.screen.blit(primary_surface, primary_rect)
        
        # Secondary text
        if self.config.text_secondary:
            secondary_surface = self._font_secondary.render(
                self.config.text_secondary, True, self.config.secondary_color
            )
            secondary_surface.set_alpha(text_alpha)
            secondary_rect = secondary_surface.get_rect(center=(self.width // 2 + 40, self.height // 2 + 30))
            self.screen.blit(secondary_surface, secondary_rect)


class SplashSequence:
    """Sequence of multiple splash screens."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.splashes: list[SplashScreen] = []
        self.current_index = 0
        self.finished = False
        self.skippable = True
    
    def add_splash(self, config: SplashConfig) -> None:
        """Add a splash to the sequence."""
        self.splashes.append(SplashScreen(self.screen, config))
    
    def add_splash_instance(self, splash: SplashScreen) -> None:
        """Add a pre-created splash instance to the sequence."""
        self.splashes.append(splash)
    
    def update(self, dt: float) -> bool:
        """Update current splash. Returns True when all finished."""
        if self.finished or self.current_index >= len(self.splashes):
            self.finished = True
            return True
        
        current = self.splashes[self.current_index]
        if current.update(dt):
            self.current_index += 1
            if self.current_index >= len(self.splashes):
                self.finished = True
        
        return self.finished
    
    def draw(self) -> None:
        """Draw current splash."""
        if self.current_index < len(self.splashes):
            self.splashes[self.current_index].draw()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.skippable:
            return False
        
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            if self.current_index < len(self.splashes):
                # Skip current splash
                self.splashes[self.current_index].skip()
                return True
        
        return False
    
    def skip_all(self) -> None:
        """Skip all remaining splashes."""
        self.finished = True
        self.current_index = len(self.splashes)


def create_tessera_splash_sequence(screen: pygame.Surface) -> SplashSequence:
    """Create the standard Tessera splash sequence."""
    sequence = SplashSequence(screen)
    
    # Simplector splash
    sequence.add_splash(SplashConfig(
        text_primary="S I M P L E C T O R",
        text_secondary="presents",
        fade_in_duration=0.6,
        hold_duration=1.2,
        fade_out_duration=0.5,
        bg_color=(3, 3, 8),
        primary_color=(200, 180, 255),
        secondary_color=(120, 100, 150),
    ))
    
    # Hypersim Engine splash (with animated hypercube)
    hypersim_config = SplashConfig(
        text_primary="HYPERSIM ENGINE",
        text_secondary="Dimensional Rendering Technology",
        fade_in_duration=0.5,
        hold_duration=1.5,
        fade_out_duration=0.5,
        bg_color=(5, 8, 15),
        primary_color=(100, 200, 255),
        secondary_color=(80, 150, 200),
    )
    sequence.add_splash_instance(HypersimEngineSplash(screen, hypersim_config))
    
    return sequence
