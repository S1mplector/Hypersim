"""Evolution UI components for displaying polytope form and progress."""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

import pygame
import numpy as np

from hypersim.game.evolution import (
    EvolutionState, PolytopeForm, PolytopeFormDef, POLYTOPE_FORMS,
    generate_polytope_vertices, generate_polytope_edges
)

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


class EvolutionUI:
    """Renders evolution-related UI elements."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # UI positioning
        self.panel_x = 20
        self.panel_y = 60
        self.panel_width = 200
        
        # Animation state
        self._rotation_angle = 0.0
        self._evolution_flash = 0.0
        self._preview_form: Optional[PolytopeForm] = None
    
    def update(self, dt: float) -> None:
        """Update UI animations."""
        self._rotation_angle += dt * 0.5
        if self._evolution_flash > 0:
            self._evolution_flash = max(0, self._evolution_flash - dt)
    
    def trigger_evolution_flash(self) -> None:
        """Trigger the evolution animation."""
        self._evolution_flash = 1.5
    
    def draw(self, state: EvolutionState, show_details: bool = False) -> None:
        """Draw the evolution UI panel."""
        form_def = state.current_form_def
        
        # Draw panel background
        panel_rect = pygame.Rect(
            self.panel_x, self.panel_y,
            self.panel_width, 140 if show_details else 90
        )
        
        # Panel with slight transparency
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surface.fill((20, 20, 40, 200))
        self.screen.blit(panel_surface, panel_rect.topleft)
        
        # Border with form color
        border_color = form_def.color
        if self._evolution_flash > 0:
            # Flash effect during evolution
            flash_intensity = int(self._evolution_flash * 255)
            border_color = (
                min(255, border_color[0] + flash_intensity),
                min(255, border_color[1] + flash_intensity),
                min(255, border_color[2] + flash_intensity),
            )
        pygame.draw.rect(self.screen, border_color, panel_rect, 2)
        
        # Form name
        font_large = pygame.font.Font(None, 28)
        font_small = pygame.font.Font(None, 20)
        
        name_text = font_large.render(form_def.short_name, True, form_def.color)
        self.screen.blit(name_text, (self.panel_x + 10, self.panel_y + 8))
        
        # Vertices/Cells info
        info_text = font_small.render(
            f"{form_def.vertices}v / {form_def.cells}c",
            True, (150, 150, 180)
        )
        self.screen.blit(info_text, (self.panel_x + 10, self.panel_y + 32))
        
        # Evolution progress bar
        if state.next_form:
            next_def = state.next_form_def
            bar_x = self.panel_x + 10
            bar_y = self.panel_y + 55
            bar_width = self.panel_width - 20
            bar_height = 12
            
            # Background
            pygame.draw.rect(self.screen, (40, 40, 60), (bar_x, bar_y, bar_width, bar_height))
            
            # Progress
            progress = state.evolution_progress
            fill_width = int(bar_width * progress)
            if fill_width > 0:
                # Gradient from current to next color
                progress_color = self._lerp_color(form_def.color, next_def.color, progress)
                pygame.draw.rect(self.screen, progress_color, (bar_x, bar_y, fill_width, bar_height))
            
            # Border
            pygame.draw.rect(self.screen, (80, 80, 100), (bar_x, bar_y, bar_width, bar_height), 1)
            
            # XP text
            xp_text = font_small.render(
                f"{state.evolution_xp} / {next_def.xp_required} XP",
                True, (180, 180, 200)
            )
            self.screen.blit(xp_text, (bar_x, bar_y + 15))
            
            # Next form hint
            next_text = font_small.render(f"→ {next_def.short_name}", True, next_def.color)
            self.screen.blit(next_text, (bar_x + bar_width - 70, bar_y + 15))
        else:
            # Max evolution reached
            max_text = font_small.render("✦ TRANSCENDED ✦", True, (255, 220, 100))
            self.screen.blit(max_text, (self.panel_x + 10, self.panel_y + 55))
        
        # Detailed stats if requested
        if show_details:
            self._draw_stats(form_def, self.panel_y + 90)
    
    def _draw_stats(self, form_def: PolytopeFormDef, y_start: int) -> None:
        """Draw detailed stats for current form."""
        font = pygame.font.Font(None, 18)
        stats = form_def.stats
        
        stat_lines = [
            f"HP: +{int(stats.health_bonus)}",
            f"SPD: +{stats.speed_bonus:.1f}",
            f"W-View: {stats.w_perception:.1f}",
            f"DR: {int(stats.damage_reduction * 100)}%",
        ]
        
        x = self.panel_x + 10
        for i, line in enumerate(stat_lines):
            text = font.render(line, True, (140, 140, 160))
            self.screen.blit(text, (x + (i % 2) * 90, y_start + (i // 2) * 18))
    
    def draw_polytope_preview(
        self,
        form: PolytopeForm,
        center: Tuple[int, int],
        size: int = 60,
        rotation: Optional[float] = None
    ) -> None:
        """Draw a rotating 2D preview of a polytope form."""
        form_def = POLYTOPE_FORMS[form]
        
        # Generate vertices
        vertices = generate_polytope_vertices(form, scale=1.0)
        edges = generate_polytope_edges(form, vertices)
        
        # Use animated rotation or provided
        angle = rotation if rotation is not None else self._rotation_angle
        
        # Rotate in XW and YZ planes for interesting 4D projection
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        cos_b = np.cos(angle * 0.7)
        sin_b = np.sin(angle * 0.7)
        
        projected = []
        for v in vertices:
            # XW rotation
            x = v[0] * cos_a - v[3] * sin_a
            w = v[0] * sin_a + v[3] * cos_a
            
            # YZ rotation
            y = v[1] * cos_b - v[2] * sin_b
            z = v[1] * sin_b + v[2] * cos_b
            
            # 4D to 2D projection
            perspective = 2.0 / (2.0 + w * 0.3)
            px = int(center[0] + x * size * perspective)
            py = int(center[1] - y * size * perspective)
            
            projected.append((px, py, perspective))
        
        # Draw edges
        color = form_def.color
        for i, j in edges:
            p1 = projected[i]
            p2 = projected[j]
            # Fade based on depth
            alpha = min(1.0, (p1[2] + p2[2]) / 2)
            edge_color = tuple(int(c * alpha) for c in color)
            pygame.draw.line(self.screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), 1)
        
        # Draw vertices
        for px, py, depth in projected:
            radius = max(2, int(3 * depth))
            pygame.draw.circle(self.screen, color, (px, py), radius)
    
    def draw_evolution_menu(
        self,
        current_state: EvolutionState,
        screen_center: Tuple[int, int]
    ) -> None:
        """Draw a full evolution menu showing all forms."""
        # Darken background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.Font(None, 48)
        font_name = pygame.font.Font(None, 28)
        font_desc = pygame.font.Font(None, 20)
        
        # Title
        title = font_title.render("4D EVOLUTION", True, (200, 150, 255))
        title_rect = title.get_rect(center=(screen_center[0], 50))
        self.screen.blit(title, title_rect)
        
        # Draw each form
        forms = list(PolytopeForm)
        spacing = self.width // (len(forms) + 1)
        
        for i, form in enumerate(forms):
            form_def = POLYTOPE_FORMS[form]
            x = spacing * (i + 1)
            y = screen_center[1]
            
            # Highlight current form
            is_current = form == current_state.current_form
            is_unlocked = form in current_state.forms_unlocked
            is_next = form == current_state.next_form
            
            # Draw polytope preview
            preview_size = 50 if is_current else 35
            self.draw_polytope_preview(form, (x, y - 30), preview_size)
            
            # Form name
            name_color = form_def.color if is_unlocked else (80, 80, 80)
            if is_current:
                name_color = (255, 255, 255)
            
            name_text = font_name.render(form_def.short_name, True, name_color)
            name_rect = name_text.get_rect(center=(x, y + 40))
            self.screen.blit(name_text, name_rect)
            
            # Cell count
            cells_text = font_desc.render(f"{form_def.cells} cells", True, (120, 120, 140))
            cells_rect = cells_text.get_rect(center=(x, y + 60))
            self.screen.blit(cells_text, cells_rect)
            
            # XP requirement or status
            if is_current:
                status = "◆ CURRENT"
                status_color = (100, 255, 100)
            elif is_unlocked:
                status = "✓ UNLOCKED"
                status_color = (100, 200, 100)
            elif is_next and current_state.can_evolve():
                status = "★ READY!"
                status_color = (255, 220, 100)
            else:
                status = f"{form_def.xp_required} XP"
                status_color = (150, 150, 150)
            
            status_text = font_desc.render(status, True, status_color)
            status_rect = status_text.get_rect(center=(x, y + 80))
            self.screen.blit(status_text, status_rect)
            
            # Selection indicator
            if is_current:
                pygame.draw.rect(
                    self.screen, form_def.color,
                    (x - 45, y - 80, 90, 180), 2
                )
        
        # Instructions
        hint = font_desc.render(
            "Collect XP to evolve • Each form grants new abilities and stats",
            True, (150, 150, 180)
        )
        hint_rect = hint.get_rect(center=(screen_center[0], self.height - 50))
        self.screen.blit(hint, hint_rect)
    
    def _lerp_color(
        self,
        c1: Tuple[int, int, int],
        c2: Tuple[int, int, int],
        t: float
    ) -> Tuple[int, int, int]:
        """Linearly interpolate between two colors."""
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t),
        )
