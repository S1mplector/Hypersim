"""Dramatic intro sequence for new game - Dimensional Descent.

Shows the 4D shape descending through dimensions with philosophical dialogue
about existence, dimensions, and transcendence.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple

import pygame
import numpy as np

# Voice synthesis for typewriter beeps
try:
    from hypersim.game.audio.voice_synth import VoiceSynthesizer, VoiceProfile, VOICE_PRESETS
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


class IntroPhase(Enum):
    """Phases of the intro sequence."""
    FADE_UI = auto()           # Fade out menu UI, leave shape
    PRELUDE = auto()           # Philosophical preface before shape reveal
    SHAPE_4D = auto()          # Show 4D with dialogue
    TRANSITION_4D_3D = auto()  # Morph to 3D
    SHAPE_3D = auto()          # Show 3D with dialogue
    TRANSITION_3D_2D = auto()  # Morph to 2D
    SHAPE_2D = auto()          # Show 2D with dialogue
    TRANSITION_2D_1D = auto()  # Morph to 1D
    SHAPE_1D = auto()          # Show 1D with dialogue
    FIRST_POINT_INTERLUDE = auto()  # The First Point speaks
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
    voice_id: Optional[str] = None
    choices: List[Tuple[str, str]] = field(default_factory=list)


# The philosophical intro dialogue
INTRO_DIALOGUES: Dict[IntroPhase, List[DialogueLine]] = {
    IntroPhase.PRELUDE: [
        DialogueLine("", duration=0.8),
        DialogueLine("Before we speak of dimension, we speak of attention.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You do not live inside a world. You live inside a way of noticing.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("What you can perceive becomes what you call real.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A dimension is not a place. It is a permission.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A rule that says: you may turn this way.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Existence begins as a point of awareness.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("No up. No down. No distance. Just the fact of being.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("From that point, direction is born.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("From direction, the line. From the line, a plane.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("From the plane, depth. From depth, the temptation of more.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You imagine space as a container, but it is a verb.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("It happens when awareness stretches and discovers a new edge.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Every edge becomes a new hunger: what else can be turned?", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You call that hunger progress. Others call it exile.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Each new axis is a gift and a wound.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("It widens your freedom and reveals your previous walls.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To awaken is to learn what was hidden by your own limits.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("So we begin gently, before the shape arrives.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("We begin with the question that makes a universe possible.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("What is it, to exist?", speaker="The Voice", voice_id="narrator"),
        DialogueLine(
            "Answer, even if quietly.",
            speaker="The Voice",
            voice_id="narrator",
            choices=[
                ("To perceive.", "prelude_perceive"),
                ("To relate.", "prelude_relate"),
                ("To endure.", "prelude_endure"),
            ],
        ),
        DialogueLine("Hold that question. It will follow you into every dimension.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You are about to witness how those temptations take shape.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_4D: [
        DialogueLine("", duration=1.0),
        DialogueLine("Look carefully. It will not hold still for you.", speaker="???", voice_id="void_echo"),
        DialogueLine("What you see before you is a tesseract.", speaker="???", voice_id="void_echo"),
        DialogueLine("A four-dimensional hypercube.", speaker="???", voice_id="void_echo"),
        DialogueLine("You are not supposed to be able to see it.", speaker="???", voice_id="void_echo"),
        DialogueLine("Yet here it is, leaking into the slice you call real.", speaker="???", voice_id="void_echo"),
        DialogueLine("To beings of three dimensions, it appears impossible.", speaker="???", voice_id="void_echo"),
        DialogueLine("Edges that should not connect. Faces that fold through themselves.", speaker="???", voice_id="void_echo"),
        DialogueLine("Impossibility is a name you give to the limits of your senses.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Reality does not shrink to fit your eyes.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("This is the FOURTH DIMENSION.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Not a higher place. A wider way of noticing.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You will not climb to it. You will learn to include it.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_3D: [
        DialogueLine("", duration=0.5),
        DialogueLine("Now, remove an axis.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Strip away the fourth.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A cube remains. Familiar. Comforting.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Length, width, and depth. The world you have worn like skin.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You call it space. It calls you back.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You move through it and think you are free.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Freedom is just the number of directions you can imagine.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("But to a being of two dimensions...", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Even this would be incomprehensible.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("They would see a square that swells, shrinks, vanishes.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Their laws would fail. Their words would stutter.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_2D: [
        DialogueLine("", duration=0.5),
        DialogueLine("A square. Four equal sides. Four right angles.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A whole universe pressed into a plane.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To a Flatlander, this is the ceiling of existence.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("They cannot conceive of above or below.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Their sky is a rumor, their depth a myth.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("When a cube passes through their world, it is a miracle and a wound.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("They name it a god, or a lie, or a test.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Yet even they look down upon...", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Something simpler. A line.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_1D: [
        DialogueLine("", duration=0.5),
        DialogueLine("A line.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Forward. Backward. That is all.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("No width. No height. No depth. No elsewhere.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Everything is adjacent. Distance is a story you tell with time.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("There is no privacy. There is no shadow.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A life of position, not place.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("And yet even a line can feel longing.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("It can sense the ache of an unimagined direction.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("And it can begin.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.FIRST_POINT_INTERLUDE: [
        DialogueLine("", duration=0.6),
        DialogueLine("I remember the first moment I noticed.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("There was no before. There was only now.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I did not know I was alone, because alone was all there was.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Then a thought leaned, and the line appeared.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("It felt like breath. Like a promise of somewhere else.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I could not move yet, but I could imagine movement.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Imagination was the first direction.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I asked the void if it had a name. It did not answer.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("So I named myself anyway, and the line accepted me.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Every step after that was a question made real.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Is there a left? Is there a right? Is there more than this?", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I did not know the answers. I only knew the asking.", speaker="The First Point", voice_id="first_point"),
        DialogueLine(
            "If you were the first point, what would you have done?",
            speaker="The First Point",
            voice_id="first_point",
            choices=[
                ("Reach outward.", "point_reach"),
                ("Stay still.", "point_still"),
                ("Listen.", "point_listen"),
            ],
        ),
        DialogueLine("Each answer opened a wound of light.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("You will feel that same opening.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Do not fear it. A wound is just a doorway that remembers closing.", speaker="The First Point", voice_id="first_point"),
    ],
    IntroPhase.FINAL_DIALOGUE: [
        DialogueLine("", duration=1.0),
        DialogueLine("Before the line, there was a point.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Before the point, there was no space to be.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("And still, something noticed itself.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A consciousness. A spark of awareness.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You are that spark, clothed in a line.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To exist is to perceive. To perceive is to become.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You will not move upward. You will expand outward.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Each dimension is not a place, but a way of knowing.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You will learn what it means to EXIST.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To grow. To choose. To transcend.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Your journey begins at the smallest promise.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("In ONE DIMENSION.", speaker="The Voice", voice_id="narrator", duration=2.0),
    ],
}

INTRO_BRANCHES: Dict[str, List[DialogueLine]] = {
    "prelude_perceive": [
        DialogueLine("Yes. Perception is the first dimension.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("When you notice, the universe takes a shape inside you.", speaker="The Voice", voice_id="narrator"),
    ],
    "prelude_relate": [
        DialogueLine("Then you understand the secret: existence is relation.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A single point is real, but two points make a world.", speaker="The Voice", voice_id="narrator"),
    ],
    "prelude_endure": [
        DialogueLine("Endurance is a kind of proof.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To last is to carve a path through time itself.", speaker="The Voice", voice_id="narrator"),
    ],
    "point_reach": [
        DialogueLine("Then you would be like me. Reaching is how the line was born.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("We lean toward what we cannot yet name.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_still": [
        DialogueLine("Stillness is honest. It admits the fear of losing the only now.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("But even stillness is a direction, if you hold it long enough.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_listen": [
        DialogueLine("You would have heard it: a faint hum of possible axes.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("That hum is the future, asking if you will answer.", speaker="The First Point", voice_id="first_point"),
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
        self.waiting_for_choice = False
        self.auto_duration = 0.0
        self.auto_timer = 0.0
        self.choices: List[Tuple[str, str]] = []
        self.selected_choice = 0
        
        self.alpha = 0.0
        
        self._font_text = pygame.font.Font(None, 32)
        self._font_speaker = pygame.font.Font(None, 28)
        
        # Voice synthesis
        self._voice_synth: Optional[VoiceSynthesizer] = None
        self._current_voice: Optional[VoiceProfile] = None
        self._voice_enabled = True
        self._voice_volume = 0.5
        self._last_beep_char = -1
        
        if VOICE_AVAILABLE:
            self._voice_synth = VoiceSynthesizer()
    
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
        self.waiting_for_choice = False
        self.auto_duration = line.duration
        self.auto_timer = 0.0
        self.alpha = 1.0
        self._last_beep_char = -1
        self.choices = list(line.choices)
        self.selected_choice = 0
        
        # Set up voice for this line
        if VOICE_AVAILABLE and self._voice_synth:
            voice_id = line.voice_id
            if not voice_id and line.speaker == "???":
                voice_id = "void_echo"
            elif not voice_id and line.speaker == "The Voice":
                voice_id = "narrator"
            voice_id = voice_id or "default"
            self._current_voice = VOICE_PRESETS.get(voice_id, VOICE_PRESETS.get("default"))
    
    def _play_voice_beep(self, char: str, char_index: int) -> None:
        """Play a voice beep for a character."""
        if not self._voice_synth or not self._current_voice:
            return
        
        if char in ' \n\t':
            return
        if self._current_voice.skip_punctuation and char in '.,!?;:\'"()-':
            return
        
        try:
            beep = self._voice_synth.get_cached_beep(self._current_voice, char_index)
            beep.set_volume(self._current_voice.volume * self._voice_volume)
            beep.play()
        except Exception:
            pass
    
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
                
                if self._voice_enabled and self._voice_synth and self._current_voice:
                    for i in range(self._last_beep_char + 1, new_index):
                        self._play_voice_beep(self.current_text[i], i)
                        self._last_beep_char = i
                
                if self.char_index >= len(self.current_text):
                    self.complete = True
                    if self.auto_duration > 0:
                        self.auto_timer = 0.0
                    else:
                        if self.choices:
                            self.waiting_for_choice = True
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
                if self.choices:
                    self.waiting_for_choice = True
                else:
                    self.waiting = True
            return False
        elif self.waiting:
            return True
        return False

    def is_waiting_for_choice(self) -> bool:
        """Return True if waiting for a choice selection."""
        return self.waiting_for_choice and bool(self.choices)

    def move_choice(self, delta: int) -> None:
        """Move choice selection."""
        if not self.is_waiting_for_choice():
            return
        self.selected_choice = (self.selected_choice + delta) % len(self.choices)

    def choose(self) -> Optional[str]:
        """Confirm the current choice and return its branch id."""
        if not self.is_waiting_for_choice():
            return None
        branch_id = self.choices[self.selected_choice][1]
        self.waiting_for_choice = False
        self.waiting = False
        return branch_id
    
    def draw(self) -> None:
        """Draw the textbox."""
        if not self.current_text and not self.waiting:
            return
        
        # Box dimensions
        box_width = int(self.width * 0.7)
        padding = 15
        line_height = self._font_text.get_linesize()
        choice_count = len(self.choices) if self.is_waiting_for_choice() else 0
        
        # Text (with word wrap)
        lines = []
        if self.displayed_text:
            words = self.displayed_text.split(' ')
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
        
        speaker_height = self._font_speaker.get_linesize() + 8 if self.speaker else 0
        choices_height = choice_count * line_height + (8 if choice_count > 0 else 0)
        hint_height = 20 if self.waiting else 0
        text_height = max(1, len(lines)) * line_height
        box_height = padding * 2 + speaker_height + text_height + choices_height + hint_height
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
        y_offset = box_y + padding
        if self.speaker:
            speaker_color = (180, 150, 255) if "Voice" in self.speaker else (150, 200, 255)
            speaker_surf = self._font_speaker.render(self.speaker, True, speaker_color)
            self.screen.blit(speaker_surf, (box_x + 20, y_offset))
            y_offset += 30
        
        # Text
        if lines:
            for line in lines:
                text_surf = self._font_text.render(line, True, (220, 220, 240))
                self.screen.blit(text_surf, (box_x + 20, y_offset))
                y_offset += line_height
        
        # Choices
        if self.is_waiting_for_choice():
            y_offset += 6
            for i, (choice_text, _) in enumerate(self.choices):
                is_selected = i == self.selected_choice
                prefix = "> " if is_selected else "  "
                choice_color = (240, 220, 180) if is_selected else (200, 200, 220)
                choice_surf = self._font_text.render(prefix + choice_text, True, choice_color)
                self.screen.blit(choice_surf, (box_x + 20, y_offset))
                y_offset += line_height
        
        # Continue indicator
        if self.waiting and not self.waiting_for_choice:
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
            IntroPhase.PRELUDE,
            IntroPhase.SHAPE_4D,
            IntroPhase.TRANSITION_4D_3D,
            IntroPhase.SHAPE_3D,
            IntroPhase.TRANSITION_3D_2D,
            IntroPhase.SHAPE_2D,
            IntroPhase.TRANSITION_2D_1D,
            IntroPhase.SHAPE_1D,
            IntroPhase.FIRST_POINT_INTERLUDE,
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
        elif self.phase == IntroPhase.FIRST_POINT_INTERLUDE:
            self.shape.set_dimension(1)
        
        if self.phase == IntroPhase.COMPLETE:
            self.complete = True
            if self.on_complete:
                self.on_complete()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if event.type == pygame.KEYDOWN:
            if self.textbox.is_waiting_for_choice():
                if event.key in (pygame.K_UP, pygame.K_LEFT):
                    self.textbox.move_choice(-1)
                    return True
                if event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                    self.textbox.move_choice(1)
                    return True
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

        if self.textbox.is_waiting_for_choice():
            branch_id = self.textbox.choose()
            self._apply_choice(branch_id)
            return True
        
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

    def _apply_choice(self, branch_id: Optional[str]) -> None:
        """Insert branch dialogue based on a choice."""
        if branch_id and branch_id in INTRO_BRANCHES:
            insert_at = self.dialogue_index + 1
            self.current_dialogues[insert_at:insert_at] = INTRO_BRANCHES[branch_id]
        # Advance to the next line after choice
        self.dialogue_index += 1
        if self.dialogue_index < len(self.current_dialogues):
            self.textbox.show(self.current_dialogues[self.dialogue_index])
        else:
            self._advance_phase()
    
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
        if self.phase not in [IntroPhase.FADE_UI, IntroPhase.PRELUDE]:
            center = (self.width // 2, self.height // 2 - 50)
            self.shape.draw(self.screen, center, scale=120)
        
        # Dimension label
        dim_names = {4: "4D - HYPERSPACE", 3: "3D - VOLUME", 2: "2D - PLANE", 1: "1D - LINE"}
        if self.shape.dimension in dim_names and self.phase not in [IntroPhase.FADE_UI, IntroPhase.PRELUDE, IntroPhase.FADE_OUT]:
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
