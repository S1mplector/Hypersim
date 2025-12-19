"""Dramatic intro sequence for new game - Dimensional Descent.

Shows the 4D shape descending through dimensions with philosophical dialogue
about existence, dimensions, and transcendence.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame
import numpy as np


class IntroPhase(Enum):
    """Phases of the intro sequence."""
    FADE_UI = auto()           # Fade out menu UI, leave shape
    SHAPE_4D = auto()          # Show 4D with dialogue
    TRANSITION_4D_3D = auto()  # Morph to 3D
    SHAPE_3D = auto()          # Show 3D with dialogue
    TRANSITION_3D_2D = auto()  # Morph to 2D
    SHAPE_2D = auto()          # Show 2D with dialogue
    TRANSITION_2D_1D = auto()  # Morph to 1D
    SHAPE_1D = auto()          # Show 1D with dialogue
    FINAL_DIALOGUE = auto()    # Final philosophical text
    FADE_OUT = auto()          # Fade to black, start game
    COMPLETE = auto()


@dataclass
class DialogueLine:
    """A line of intro dialogue."""
    text: str
    duration: float = 0.0  # 0 = wait for input
    speaker: str = ""
    typing_speed: float = 40.0


# The philosophical intro dialogue
INTRO_DIALOGUES: Dict[IntroPhase, List[DialogueLine]] = {
    IntroPhase.SHAPE_4D: [
        DialogueLine("", duration=1.0),
        DialogueLine("What you see before you is a tesseract.", speaker="???"),
        DialogueLine("A four-dimensional hypercube.", speaker="???"),
        DialogueLine("To beings of three dimensions, it appears impossible.", speaker="???"),
        DialogueLine("Edges that shouldn't connect. Faces that fold through themselves.", speaker="???"),
        DialogueLine("Yet it exists. As real as anything else.", speaker="???"),
        DialogueLine("This is the FOURTH DIMENSION.", speaker="The Voice"),
    ],
    IntroPhase.SHAPE_3D: [
        DialogueLine("", duration=0.5),
        DialogueLine("Strip away the fourth axis...", speaker="The Voice"),
        DialogueLine("And you have a cube. Familiar. Comforting.", speaker="The Voice"),
        DialogueLine("Length, width, and depth. The world you know.", speaker="The Voice"),
        DialogueLine("But to a being of two dimensions...", speaker="The Voice"),
        DialogueLine("Even this would be incomprehensible.", speaker="The Voice"),
    ],
    IntroPhase.SHAPE_2D: [
        DialogueLine("", duration=0.5),
        DialogueLine("A square. Four equal sides. Four right angles.", speaker="The Voice"),
        DialogueLine("To a Flatlander, this is the peak of existence.", speaker="The Voice"),
        DialogueLine("They cannot conceive of 'above' or 'below'.", speaker="The Voice"),
        DialogueLine("Their entire universe is a single plane.", speaker="The Voice"),
        DialogueLine("Yet even they look down upon...", speaker="The Voice"),
    ],
    IntroPhase.SHAPE_1D: [
        DialogueLine("", duration=0.5),
        DialogueLine("A line.", speaker="The Voice"),
        DialogueLine("Forward. Backward. Nothing else.", speaker="The Voice"),
        DialogueLine("No width. No height. No depth. No... beyond.", speaker="The Voice"),
        DialogueLine("The simplest form of spatial existence.", speaker="The Voice"),
        DialogueLine("And yet...", speaker="The Voice"),
    ],
    IntroPhase.FINAL_DIALOGUE: [
        DialogueLine("", duration=1.0),
        DialogueLine("Before the line, there was a point.", speaker="The Voice"),
        DialogueLine("Before the point, there was nothing.", speaker="The Voice"),
        DialogueLine("And from nothing... you emerged.", speaker="The Voice"),
        DialogueLine("A consciousness. A spark of awareness.", speaker="The Voice"),
        DialogueLine("You will learn what it means to EXIST.", speaker="The Voice"),
        DialogueLine("To grow. To perceive. To transcend.", speaker="The Voice"),
        DialogueLine("Your journey begins... at the beginning.", speaker="The Voice"),
        DialogueLine("In ONE DIMENSION.", speaker="The Voice", duration=2.0),
    ],
}


class DimensionalShape:
    """Renders shapes that can morph between dimensions."""
    
    def __init__(self):
        self.time = 0.0
        self.dimension = 4  # Current dimension (4, 3, 2, 1)
        self.morph_progress = 0.0  # 0-1 progress during transitions
        
        # Rotation angles
        self.angle_xy = 0.0
        self.angle_xz = 0.0
        self.angle_xw = 0.0
        self.angle_yz = 0.0
        self.angle_yw = 0.0
        self.angle_zw = 0.0
        
        # Colors per dimension
        self.colors = {
            4: (150, 100, 255),   # Purple for 4D
            3: (100, 180, 255),   # Blue for 3D
            2: (100, 255, 180),   # Cyan for 2D
            1: (255, 200, 100),   # Gold for 1D
        }
        
        # Glow effect
        self.glow_intensity = 0.5
    
    def update(self, dt: float) -> None:
        """Update shape animation."""
        self.time += dt
        
        # Rotate based on dimension
        speed_mult = 1.0 + (4 - self.dimension) * 0.3
        
        if self.dimension >= 4:
            self.angle_xw += 0.5 * dt * speed_mult
            self.angle_yw += 0.4 * dt * speed_mult
            self.angle_zw += 0.35 * dt * speed_mult
        
        if self.dimension >= 3:
            self.angle_xz += 0.3 * dt * speed_mult
            self.angle_yz += 0.25 * dt * speed_mult
        
        if self.dimension >= 2:
            self.angle_xy += 0.4 * dt * speed_mult
        
        # Pulsing glow
        self.glow_intensity = 0.5 + 0.3 * math.sin(self.time * 2)
    
    def set_dimension(self, dim: int, morph: float = 0.0) -> None:
        """Set current dimension and morph progress."""
        self.dimension = dim
        self.morph_progress = morph
    
    def _rotate_point(self, point: np.ndarray) -> np.ndarray:
        """Apply rotations to a point."""
        x, y, z, w = point
        
        # 4D rotations (only if showing 4D)
        if self.dimension >= 4 or self.morph_progress > 0:
            cos_xw, sin_xw = math.cos(self.angle_xw), math.sin(self.angle_xw)
            x, w = x * cos_xw - w * sin_xw, x * sin_xw + w * cos_xw
            
            cos_yw, sin_yw = math.cos(self.angle_yw), math.sin(self.angle_yw)
            y, w = y * cos_yw - w * sin_yw, y * sin_yw + w * cos_yw
            
            cos_zw, sin_zw = math.cos(self.angle_zw), math.sin(self.angle_zw)
            z, w = z * cos_zw - w * sin_zw, z * sin_zw + w * cos_zw
        
        # 3D rotations
        if self.dimension >= 3 or self.morph_progress > 0:
            cos_xz, sin_xz = math.cos(self.angle_xz), math.sin(self.angle_xz)
            x, z = x * cos_xz - z * sin_xz, x * sin_xz + z * cos_xz
            
            cos_yz, sin_yz = math.cos(self.angle_yz), math.sin(self.angle_yz)
            y, z = y * cos_yz - z * sin_yz, y * sin_yz + z * cos_yz
        
        # 2D rotation
        cos_xy, sin_xy = math.cos(self.angle_xy), math.sin(self.angle_xy)
        x, y = x * cos_xy - y * sin_xy, x * sin_xy + y * cos_xy
        
        return np.array([x, y, z, w])
    
    def _project_to_screen(self, point: np.ndarray, center: Tuple[int, int], 
                          scale: float) -> Tuple[int, int, float]:
        """Project point to screen coordinates."""
        x, y, z, w = point
        
        # Collapse higher dimensions based on current state
        if self.dimension < 4:
            w = w * (1 - self.morph_progress) if self.morph_progress < 1 else 0
        if self.dimension < 3:
            z = z * (1 - self.morph_progress) if self.morph_progress < 1 else 0
        if self.dimension < 2:
            y = y * (1 - self.morph_progress) if self.morph_progress < 1 else 0
        
        # 4D to 3D projection
        dist_4d = 3.0
        factor_4d = dist_4d / (dist_4d - w) if abs(dist_4d - w) > 0.01 else 1
        x3d = x * factor_4d
        y3d = y * factor_4d
        z3d = z * factor_4d
        
        # 3D to 2D projection
        dist_3d = 4.0
        factor_3d = dist_3d / (dist_3d - z3d) if abs(dist_3d - z3d) > 0.01 else 1
        x2d = x3d * factor_3d
        y2d = y3d * factor_3d
        
        screen_x = int(center[0] + x2d * scale)
        screen_y = int(center[1] - y2d * scale)
        depth = w + z3d
        
        return (screen_x, screen_y, depth)
    
    def draw(self, screen: pygame.Surface, center: Tuple[int, int], 
             scale: float = 150) -> None:
        """Draw the current dimensional shape."""
        # Get vertices and edges based on dimension
        if self.dimension == 4:
            vertices, edges = self._get_tesseract()
        elif self.dimension == 3:
            vertices, edges = self._get_cube()
        elif self.dimension == 2:
            vertices, edges = self._get_square()
        else:  # 1D
            vertices, edges = self._get_line()
        
        # Get color (interpolate during transitions)
        color = self.colors.get(self.dimension, (255, 255, 255))
        
        # Rotate and project all vertices
        projected = []
        for v in vertices:
            rotated = self._rotate_point(v)
            proj = self._project_to_screen(rotated, center, scale)
            projected.append(proj)
        
        # Draw glow effect
        glow_surf = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        glow_color = (*color, int(30 * self.glow_intensity))
        
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            pygame.draw.line(glow_surf, glow_color, (p1[0], p1[1]), (p2[0], p2[1]), 8)
        
        screen.blit(glow_surf, (0, 0))
        
        # Draw edges
        for i, j in edges:
            p1, p2 = projected[i], projected[j]
            avg_depth = (p1[2] + p2[2]) / 2
            depth_factor = (avg_depth + 2) / 4
            depth_factor = max(0.3, min(1.0, depth_factor))
            
            edge_color = tuple(int(c * depth_factor) for c in color)
            width = max(1, int(3 * depth_factor))
            pygame.draw.line(screen, edge_color, (p1[0], p1[1]), (p2[0], p2[1]), width)
        
        # Draw vertices
        for p in projected:
            depth_factor = (p[2] + 2) / 4
            depth_factor = max(0.4, min(1.0, depth_factor))
            vertex_color = tuple(int(c * depth_factor) for c in color)
            radius = max(3, int(5 * depth_factor))
            pygame.draw.circle(screen, vertex_color, (p[0], p[1]), radius)
    
    def _get_tesseract(self) -> Tuple[List[np.ndarray], List[Tuple[int, int]]]:
        """Get tesseract (4D hypercube) vertices and edges."""
        vertices = []
        for w in [-1, 1]:
            for z in [-1, 1]:
                for y in [-1, 1]:
                    for x in [-1, 1]:
                        vertices.append(np.array([x, y, z, w], dtype=float))
        
        edges = []
        for i in range(16):
            for j in range(i + 1, 16):
                if bin(i ^ j).count('1') == 1:
                    edges.append((i, j))
        
        return vertices, edges
    
    def _get_cube(self) -> Tuple[List[np.ndarray], List[Tuple[int, int]]]:
        """Get cube (3D) vertices and edges."""
        vertices = []
        for z in [-1, 1]:
            for y in [-1, 1]:
                for x in [-1, 1]:
                    vertices.append(np.array([x, y, z, 0], dtype=float))
        
        edges = []
        for i in range(8):
            for j in range(i + 1, 8):
                if bin(i ^ j).count('1') == 1:
                    edges.append((i, j))
        
        return vertices, edges
    
    def _get_square(self) -> Tuple[List[np.ndarray], List[Tuple[int, int]]]:
        """Get square (2D) vertices and edges."""
        vertices = [
            np.array([-1, -1, 0, 0], dtype=float),
            np.array([1, -1, 0, 0], dtype=float),
            np.array([1, 1, 0, 0], dtype=float),
            np.array([-1, 1, 0, 0], dtype=float),
        ]
        edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
        return vertices, edges
    
    def _get_line(self) -> Tuple[List[np.ndarray], List[Tuple[int, int]]]:
        """Get line (1D) vertices and edges."""
        vertices = [
            np.array([-1.5, 0, 0, 0], dtype=float),
            np.array([1.5, 0, 0, 0], dtype=float),
        ]
        edges = [(0, 1)]
        return vertices, edges


class IntroTextBox:
    """Text display for intro sequence."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.current_text = ""
        self.displayed_text = ""
        self.speaker = ""
        self.char_index = 0
        self.typing_speed = 40.0
        self.char_timer = 0.0
        self.complete = False
        self.waiting = False
        self.auto_duration = 0.0
        self.auto_timer = 0.0
        
        self.alpha = 0.0
        
        self._font_text = pygame.font.Font(None, 32)
        self._font_speaker = pygame.font.Font(None, 28)
    
    def show(self, line: DialogueLine) -> None:
        """Show a dialogue line."""
        self.current_text = line.text
        self.speaker = line.speaker
        self.displayed_text = ""
        self.char_index = 0
        self.typing_speed = line.typing_speed
        self.char_timer = 0.0
        self.complete = False
        self.waiting = False
        self.auto_duration = line.duration
        self.auto_timer = 0.0
        self.alpha = 1.0
    
    def update(self, dt: float) -> bool:
        """Update textbox. Returns True when line is done."""
        if not self.current_text:
            # Empty line - just wait for duration
            self.auto_timer += dt
            return self.auto_timer >= self.auto_duration if self.auto_duration > 0 else False
        
        if not self.complete:
            self.char_timer += dt
            chars_to_add = int(self.char_timer * self.typing_speed)
            
            if chars_to_add > 0:
                self.char_timer = 0
                new_index = min(self.char_index + chars_to_add, len(self.current_text))
                self.displayed_text = self.current_text[:new_index]
                self.char_index = new_index
                
                if self.char_index >= len(self.current_text):
                    self.complete = True
                    if self.auto_duration > 0:
                        self.auto_timer = 0.0
                    else:
                        self.waiting = True
        elif self.auto_duration > 0:
            self.auto_timer += dt
            if self.auto_timer >= self.auto_duration:
                return True
        
        return False
    
    def skip(self) -> bool:
        """Skip typing or advance. Returns True if should proceed to next line."""
        if not self.complete:
            self.displayed_text = self.current_text
            self.char_index = len(self.current_text)
            self.complete = True
            if self.auto_duration == 0:
                self.waiting = True
            return False
        elif self.waiting:
            return True
        return False
    
    def draw(self) -> None:
        """Draw the textbox."""
        if not self.current_text and not self.waiting:
            return
        
        # Box dimensions
        box_width = int(self.width * 0.7)
        box_height = 120
        box_x = (self.width - box_width) // 2
        box_y = self.height - box_height - 60
        
        # Background
        bg_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        bg_surf.fill((10, 10, 20, int(200 * self.alpha)))
        self.screen.blit(bg_surf, (box_x, box_y))
        
        # Border
        border_color = (100, 120, 180, int(255 * self.alpha))
        pygame.draw.rect(self.screen, border_color[:3], 
                        (box_x, box_y, box_width, box_height), 2)
        
        # Speaker
        y_offset = box_y + 15
        if self.speaker:
            speaker_color = (180, 150, 255) if "Voice" in self.speaker else (150, 200, 255)
            speaker_surf = self._font_speaker.render(self.speaker, True, speaker_color)
            self.screen.blit(speaker_surf, (box_x + 20, y_offset))
            y_offset += 30
        
        # Text (with word wrap)
        if self.displayed_text:
            words = self.displayed_text.split(' ')
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if self._font_text.size(test_line)[0] <= box_width - 40:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            for line in lines:
                text_surf = self._font_text.render(line, True, (220, 220, 240))
                self.screen.blit(text_surf, (box_x + 20, y_offset))
                y_offset += 28
        
        # Continue indicator
        if self.waiting:
            blink = int(pygame.time.get_ticks() / 500) % 2 == 0
            if blink:
                indicator = self._font_speaker.render("▼", True, (150, 150, 180))
                self.screen.blit(indicator, (box_x + box_width - 30, box_y + box_height - 25))


class IntroSequence:
    """The dramatic intro sequence showing dimensional descent."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.phase = IntroPhase.FADE_UI
        self.phase_timer = 0.0
        self.ui_alpha = 1.0  # For fading menu elements
        self.overlay_alpha = 0.0  # For transitions
        
        self.shape = DimensionalShape()
        self.textbox = IntroTextBox(screen)
        
        self.dialogue_index = 0
        self.current_dialogues: List[DialogueLine] = []
        
        self.complete = False
        self.on_complete: Optional[Callable] = None
        
        # Background
        self.bg_color = (5, 5, 15)
    
    def start(self) -> None:
        """Start the intro sequence."""
        self.phase = IntroPhase.FADE_UI
        self.phase_timer = 0.0
        self.ui_alpha = 1.0
    
    def _advance_phase(self) -> None:
        """Advance to the next phase."""
        phase_order = [
            IntroPhase.FADE_UI,
            IntroPhase.SHAPE_4D,
            IntroPhase.TRANSITION_4D_3D,
            IntroPhase.SHAPE_3D,
            IntroPhase.TRANSITION_3D_2D,
            IntroPhase.SHAPE_2D,
            IntroPhase.TRANSITION_2D_1D,
            IntroPhase.SHAPE_1D,
            IntroPhase.FINAL_DIALOGUE,
            IntroPhase.FADE_OUT,
            IntroPhase.COMPLETE,
        ]
        
        current_idx = phase_order.index(self.phase)
        if current_idx < len(phase_order) - 1:
            self.phase = phase_order[current_idx + 1]
            self.phase_timer = 0.0
            self._on_phase_enter()
    
    def _on_phase_enter(self) -> None:
        """Handle entering a new phase."""
        # Set up dialogues for dialogue phases
        if self.phase in INTRO_DIALOGUES:
            self.current_dialogues = INTRO_DIALOGUES[self.phase]
            self.dialogue_index = 0
            if self.current_dialogues:
                self.textbox.show(self.current_dialogues[0])
        
        # Set shape dimension for shape phases
        if self.phase == IntroPhase.SHAPE_4D:
            self.shape.set_dimension(4)
        elif self.phase == IntroPhase.SHAPE_3D:
            self.shape.set_dimension(3)
        elif self.phase == IntroPhase.SHAPE_2D:
            self.shape.set_dimension(2)
        elif self.phase == IntroPhase.SHAPE_1D:
            self.shape.set_dimension(1)
        
        if self.phase == IntroPhase.COMPLETE:
            self.complete = True
            if self.on_complete:
                self.on_complete()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                return self._advance_dialogue()
            elif event.key == pygame.K_ESCAPE:
                # Skip entire intro
                self.phase = IntroPhase.FADE_OUT
                self.phase_timer = 0.0
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._advance_dialogue()
        return False
    
    def _advance_dialogue(self) -> bool:
        """Advance dialogue. Returns True if consumed."""
        if self.phase in [IntroPhase.FADE_UI, IntroPhase.FADE_OUT, IntroPhase.COMPLETE]:
            return False
        
        if self.phase.name.startswith("TRANSITION"):
            return False
        
        # Try to skip/advance textbox
        if self.textbox.skip():
            # Move to next dialogue line
            self.dialogue_index += 1
            if self.dialogue_index < len(self.current_dialogues):
                self.textbox.show(self.current_dialogues[self.dialogue_index])
            else:
                # All dialogues done, advance phase
                self._advance_phase()
        
        return True
    
    def update(self, dt: float) -> None:
        """Update the intro sequence."""
        self.phase_timer += dt
        self.shape.update(dt)
        
        # Phase-specific updates
        if self.phase == IntroPhase.FADE_UI:
            self.ui_alpha = max(0, 1 - self.phase_timer / 1.5)
            if self.phase_timer >= 2.0:
                self._advance_phase()
        
        elif self.phase == IntroPhase.TRANSITION_4D_3D:
            progress = min(1, self.phase_timer / 2.0)
            self.shape.set_dimension(4 if progress < 0.5 else 3, 
                                    progress * 2 if progress < 0.5 else (progress - 0.5) * 2)
            if self.phase_timer >= 2.0:
                self._advance_phase()
        
        elif self.phase == IntroPhase.TRANSITION_3D_2D:
            progress = min(1, self.phase_timer / 2.0)
            self.shape.set_dimension(3 if progress < 0.5 else 2,
                                    progress * 2 if progress < 0.5 else (progress - 0.5) * 2)
            if self.phase_timer >= 2.0:
                self._advance_phase()
        
        elif self.phase == IntroPhase.TRANSITION_2D_1D:
            progress = min(1, self.phase_timer / 2.0)
            self.shape.set_dimension(2 if progress < 0.5 else 1,
                                    progress * 2 if progress < 0.5 else (progress - 0.5) * 2)
            if self.phase_timer >= 2.0:
                self._advance_phase()
        
        elif self.phase == IntroPhase.FADE_OUT:
            self.overlay_alpha = min(1, self.phase_timer / 2.0)
            if self.phase_timer >= 2.5:
                self._advance_phase()
        
        elif self.phase in INTRO_DIALOGUES:
            # Update textbox for auto-advance lines
            if self.textbox.update(dt):
                self.dialogue_index += 1
                if self.dialogue_index < len(self.current_dialogues):
                    self.textbox.show(self.current_dialogues[self.dialogue_index])
                else:
                    self._advance_phase()
    
    def draw(self) -> None:
        """Draw the intro sequence."""
        # Background
        self.screen.fill(self.bg_color)
        
        # Shape
        center = (self.width // 2, self.height // 2 - 50)
        self.shape.draw(self.screen, center, scale=120)
        
        # Dimension label
        dim_names = {4: "4D - HYPERSPACE", 3: "3D - VOLUME", 2: "2D - PLANE", 1: "1D - LINE"}
        if self.shape.dimension in dim_names and self.phase not in [IntroPhase.FADE_UI, IntroPhase.FADE_OUT]:
            font = pygame.font.Font(None, 36)
            label = font.render(dim_names[self.shape.dimension], True, self.shape.colors[self.shape.dimension])
            label_rect = label.get_rect(center=(self.width // 2, 80))
            self.screen.blit(label, label_rect)
        
        # Textbox
        self.textbox.draw()
        
        # Fade overlay
        if self.overlay_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int(255 * self.overlay_alpha))
            self.screen.blit(overlay, (0, 0))
    
    @property
    def is_complete(self) -> bool:
        return self.complete


def run_intro_sequence(screen: pygame.Surface) -> bool:
    """Run the intro sequence standalone. Returns True if completed, False if skipped."""
    clock = pygame.time.Clock()
    intro = IntroSequence(screen)
    intro.start()
    
    while not intro.is_complete:
        dt = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            intro.handle_event(event)
        
        intro.update(dt)
        intro.draw()
        pygame.display.flip()
    
    return True
