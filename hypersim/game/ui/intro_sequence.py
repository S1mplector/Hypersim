"""Dramatic intro sequence for new game - Dimensional Descent.

Shows the 4D shape descending through dimensions with philosophical dialogue
about existence, dimensions, and transcendence.
"""
from __future__ import annotations

import math
import random
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
    MEMORY_FLASH = auto()      # Memory cutaway about Monodia/First Point
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


@dataclass
class IntroStar:
    """Ambient background star for the intro sequence."""
    x: float
    y: float
    drift_x: float
    drift_y: float
    size: float
    twinkle_phase: float
    twinkle_speed: float
    depth: float


@dataclass
class SignalRing:
    """Expanding ring used during dimensional pulses and transitions."""
    radius: float
    speed: float
    alpha: float
    fade_speed: float
    color: Tuple[int, int, int]
    width: int = 2


@dataclass
class MemoryShard:
    """Transient shard used during the memory flash phase."""
    x: float
    y: float
    vx: float
    vy: float
    length: float
    angle: float
    rotation_speed: float
    alpha: float
    fade_speed: float
    color: Tuple[int, int, int]


# The philosophical intro dialogue
INTRO_DIALOGUES: Dict[IntroPhase, List[DialogueLine]] = {
    IntroPhase.PRELUDE: [
        DialogueLine("", duration=0.6),
        DialogueLine("Before we speak of dimension, we need to speak of attention.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A world does not arrive all at once. It arrives in the exact shape your notice can bear.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("What do you notice?", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A dimension is not a place. It is a permission.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("The right to turn where, a moment ago, turning was impossible.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Every new permission feels like freedom.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Every new freedom reveals an older prison.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("So answer carefully.", speaker="The Voice", voice_id="narrator"),
        DialogueLine(
            "When do you think a world becomes real?",
            speaker="The Voice",
            voice_id="narrator",
            choices=[
                ("When it can be perceived.", "prelude_perceive"),
                ("When it can be related to.", "prelude_relate"),
                ("When it can endure...?", "prelude_endure"),
            ],
        ),
        DialogueLine("Good. Keep that answer near.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.MEMORY_FLASH: [
        DialogueLine("", duration=0.4),
        DialogueLine("A memory not yours strikes the dark and holds.", speaker="???", voice_id="void_echo"),
        DialogueLine("Monodia. The Line of One. Sparks colliding until one spark refuses to vanish.", speaker="???", voice_id="void_echo"),
        DialogueLine("That refusal becomes a witness. The witness becomes a point. The point becomes a beginning.", speaker="???", voice_id="void_echo"),
        DialogueLine("Before you inherit its hunger, answer this:", speaker="The Voice", voice_id="narrator"),
        DialogueLine(
            "When the unknown calls, what is your first answer?",
            speaker="The Voice",
            voice_id="narrator",
            choices=[
                ("Lean toward it.", "impulse_lean"),
                ("Listen before moving.", "impulse_listen"),
                ("Hesitate and observe.", "impulse_hesitate"),
            ],
        ),
        DialogueLine("Then let that first instinct name the shape of your opening step.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_4D: [
        DialogueLine("", duration=1.0),
        DialogueLine("Look carefully. It will not hold still for lower habits.", speaker="???", voice_id="void_echo"),
        DialogueLine("A tesseract. A four-dimensional body leaking through a thinner reality.", speaker="???", voice_id="void_echo"),
        DialogueLine("To three-dimensional sight, it appears impossible because your sight keeps slicing it into survivable pieces.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Impossibility is often just perception arriving late.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("This is the FOURTH DIMENSION.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Not a higher place. A wider way of being wrong before you become right.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_3D: [
        DialogueLine("", duration=0.5),
        DialogueLine("Remove one permission.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Volume remains. Depth. Shelter. Hidden interiors.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To you, perhaps familiar.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("To a flat being, a cube would arrive as revelation and violence at once.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Every dimension mistakes itself for the whole until a larger one interrupts.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_2D: [
        DialogueLine("", duration=0.5),
        DialogueLine("Remove depth and a plane survives.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Edges can enclose. Nothing can hide.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A flat civilization could spend ages arguing about angles and never imagine above.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("When a greater body crosses their world, theology and panic become the same motion.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("And still, even they would pity the Line.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.SHAPE_1D: [
        DialogueLine("", duration=0.5),
        DialogueLine("Now strip the world to its barest promise.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("A line.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Forward. Backward. No sideways mercy. No hidden room to become someone else.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Everything is adjacency. Distance is just time learning to ache.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("And still, even this smallest world can long for more.", speaker="The Voice", voice_id="narrator"),
    ],
    IntroPhase.FIRST_POINT_INTERLUDE: [
        DialogueLine("", duration=0.6),
        DialogueLine("I remember the first impossible thought.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I wondered whether stillness was truly all there was.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("That question wounded the void. Direction entered through the opening.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("I became first not by age, but by refusing to remain unshaped.", speaker="The First Point", voice_id="first_point"),
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
        DialogueLine("Good. Then you already understand how axes begin.", speaker="The First Point", voice_id="first_point"),
        DialogueLine("Not with power. With preference. With a tiny disobedience against nothing.", speaker="The First Point", voice_id="first_point"),
    ],
    IntroPhase.FINAL_DIALOGUE: [
        DialogueLine("", duration=1.0),
        DialogueLine("Now the greater shape closes, and you are left with the smallest promise.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("You will begin below your own future.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Two directions. A narrow world. A question that will not leave you alone.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("The Line will teach you cost before it teaches you wonder.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Wonder arrives anyway.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Go.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("Exist.", speaker="The Voice", voice_id="narrator"),
        DialogueLine("In ONE DIMENSION.", speaker="The Voice", voice_id="narrator", duration=2.0),
    ],
}

INTRO_BRANCHES: Dict[str, List[DialogueLine]] = {
    "prelude_perceive": [
        DialogueLine("Then you understand the first mercy: the unseen cannot claim you until it is noticed.", speaker="The Voice", voice_id="narrator"),
    ],
    "prelude_relate": [
        DialogueLine("Then you understand the first law: one point can exist, but relation is what turns existence into world.", speaker="The Voice", voice_id="narrator"),
    ],
    "prelude_endure": [
        DialogueLine("Then you understand the first burden: to endure is to let time carve a name into you.", speaker="The Voice", voice_id="narrator"),
    ],
    "point_reach": [
        DialogueLine("Then you would have done what I did. Reaching is how the first line tore itself free.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_still": [
        DialogueLine("Stillness is not emptiness. It is the last defense before becoming more than you were.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_listen": [
        DialogueLine("Then you would have heard it too: the faint hum of directions not yet born.", speaker="The First Point", voice_id="first_point"),
    ],
    "impulse_lean": [
        DialogueLine("Leaning breaks stasis. Sometimes clumsily. Always honestly.", speaker="The Voice", voice_id="narrator"),
    ],
    "impulse_listen": [
        DialogueLine("Listening is patience. It lets the future announce its shape before you enter it.", speaker="The Voice", voice_id="narrator"),
    ],
    "impulse_hesitate": [
        DialogueLine("Hesitation is data. You let uncertainty confess itself before you move.", speaker="The Voice", voice_id="narrator"),
    ],
}

FINAL_IMPULSE_ECHOS: Dict[str, List[DialogueLine]] = {
    "lean": [
        DialogueLine("You leaned before you understood. Keep that courage. Learn its cost.", speaker="The Voice", voice_id="narrator"),
    ],
    "listen": [
        DialogueLine("You listened before you moved. Keep that patience. Not every silence is kind.", speaker="The Voice", voice_id="narrator"),
    ],
    "hesitate": [
        DialogueLine("You measured the dark before stepping. Keep that caution. It will not always save you.", speaker="The Voice", voice_id="narrator"),
    ],
}

FINAL_POINT_ECHOS: Dict[str, List[DialogueLine]] = {
    "point_reach": [
        DialogueLine("When the world narrows, you will try the edge first.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_still": [
        DialogueLine("When the world trembles, you will know how to hold still without disappearing.", speaker="The First Point", voice_id="first_point"),
    ],
    "point_listen": [
        DialogueLine("When the world whispers, you will hear the next axis before others do.", speaker="The First Point", voice_id="first_point"),
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

    def _speaker_palette(self) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """Return accent and text colors for the active speaker."""
        if self.speaker == "The First Point":
            return (212, 164, 255), (238, 228, 255)
        if self.speaker == "The Voice":
            return (152, 186, 255), (226, 236, 255)
        if self.speaker == "???":
            return (118, 208, 196), (218, 245, 240)
        return (150, 160, 188), (224, 228, 240)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap textbox text to fit within the available width."""
        if not text:
            return []

        words = text.split(" ")
        lines: List[str] = []
        current_line = ""
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self._font_text.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines
    
    def draw(self) -> None:
        """Draw the textbox."""
        if not self.current_text and not self.waiting:
            return
        
        # Box dimensions
        box_width = int(self.width * 0.72)
        padding = 18
        line_height = self._font_text.get_linesize()
        choice_count = len(self.choices) if self.is_waiting_for_choice() else 0
        accent_color, text_color = self._speaker_palette()
        lines = self._wrap_text(self.displayed_text, box_width - 64)

        speaker_height = 36 if self.speaker else 0
        choices_height = choice_count * (line_height + 8) + (10 if choice_count > 0 else 0)
        hint_height = 28 if (self.waiting or self.waiting_for_choice) else 0
        text_height = max(1, len(lines)) * line_height
        box_height = padding * 2 + speaker_height + text_height + choices_height + hint_height
        box_x = (self.width - box_width) // 2
        box_y = self.height - box_height - 60
        
        # Background
        bg_surf = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (8, 10, 18, int(224 * self.alpha)), bg_surf.get_rect(), border_radius=18)
        pygame.draw.rect(bg_surf, (*accent_color, int(92 * self.alpha)), bg_surf.get_rect(), width=1, border_radius=18)
        pygame.draw.line(bg_surf, (*accent_color, int(210 * self.alpha)), (28, 24), (126, 24), 2)
        self.screen.blit(bg_surf, (box_x, box_y))
        
        # Speaker
        y_offset = box_y + padding
        if self.speaker:
            pill_text = self._font_speaker.render(self.speaker.upper(), True, accent_color)
            pill_rect = pygame.Rect(box_x + 22, y_offset - 2, pill_text.get_width() + 18, 28)
            pill_surf = pygame.Surface((pill_rect.width, pill_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(pill_surf, (18, 22, 34, int(220 * self.alpha)), pill_surf.get_rect(), border_radius=14)
            pygame.draw.rect(pill_surf, (*accent_color, int(110 * self.alpha)), pill_surf.get_rect(), width=1, border_radius=14)
            self.screen.blit(pill_surf, pill_rect.topleft)
            self.screen.blit(pill_text, (pill_rect.x + 9, pill_rect.y + 3))
            y_offset += 34
        
        # Text
        if lines:
            for line in lines:
                text_surf = self._font_text.render(line, True, text_color)
                self.screen.blit(text_surf, (box_x + 20, y_offset))
                y_offset += line_height
        
        # Choices
        if self.is_waiting_for_choice():
            y_offset += 6
            for i, (choice_text, _) in enumerate(self.choices):
                is_selected = i == self.selected_choice
                choice_rect = pygame.Rect(box_x + 18, y_offset - 2, box_width - 36, line_height + 10)
                if is_selected:
                    choice_bg = pygame.Surface((choice_rect.width, choice_rect.height), pygame.SRCALPHA)
                    pygame.draw.rect(choice_bg, (*accent_color, 42), choice_bg.get_rect(), border_radius=12)
                    pygame.draw.rect(choice_bg, (*accent_color, 90), choice_bg.get_rect(), width=1, border_radius=12)
                    self.screen.blit(choice_bg, choice_rect.topleft)

                prefix = "› " if is_selected else "  "
                choice_color = (248, 236, 214) if is_selected else (198, 204, 220)
                choice_surf = self._font_text.render(prefix + choice_text, True, choice_color)
                self.screen.blit(choice_surf, (choice_rect.x + 12, choice_rect.y + 4))
                y_offset += line_height + 8
        
        # Continue indicator
        if self.waiting_for_choice:
            hint = self._font_speaker.render("ARROWS TO CHOOSE  •  ENTER TO COMMIT", True, (142, 154, 176))
            self.screen.blit(hint, (box_x + box_width - hint.get_width() - 20, box_y + box_height - 28))
        elif self.waiting:
            blink = int(pygame.time.get_ticks() / 500) % 2 == 0
            hint = self._font_speaker.render("ENTER OR CLICK TO CONTINUE", True, (142, 154, 176))
            self.screen.blit(hint, (box_x + box_width - hint.get_width() - 48, box_y + box_height - 28))
            if blink:
                indicator = self._font_speaker.render("▼", True, (156, 166, 188))
                self.screen.blit(indicator, (box_x + box_width - 28, box_y + box_height - 31))


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
        self.impulse_choice: str = ""
        self.point_choice: str = ""
        
        self.bg_color = (5, 5, 15)
        self._phase_colors: Dict[IntroPhase, Tuple[int, int, int]] = {
            IntroPhase.FADE_UI: (28, 34, 52),
            IntroPhase.PRELUDE: (62, 78, 126),
            IntroPhase.MEMORY_FLASH: (104, 88, 142),
            IntroPhase.SHAPE_4D: (150, 100, 255),
            IntroPhase.TRANSITION_4D_3D: (136, 112, 240),
            IntroPhase.SHAPE_3D: (100, 180, 255),
            IntroPhase.TRANSITION_3D_2D: (96, 198, 226),
            IntroPhase.SHAPE_2D: (100, 255, 180),
            IntroPhase.TRANSITION_2D_1D: (180, 220, 140),
            IntroPhase.SHAPE_1D: (255, 200, 100),
            IntroPhase.FIRST_POINT_INTERLUDE: (214, 158, 255),
            IntroPhase.FINAL_DIALOGUE: (172, 182, 255),
            IntroPhase.FADE_OUT: (80, 90, 120),
            IntroPhase.COMPLETE: (0, 0, 0),
        }
        self._stars = self._build_stars(96)
        self._rings: List[SignalRing] = []
        self._memory_shards: List[MemoryShard] = []
        self._pulse_timer = 0.0
        self._memory_timer = 0.0
        self._flash_alpha = 0.0
        self._flash_color = (255, 255, 255)
        self._camera_shake = 0.0
    
    def start(self) -> None:
        """Start the intro sequence."""
        self.phase = IntroPhase.FADE_UI
        self.phase_timer = 0.0
        self.ui_alpha = 1.0
        self.overlay_alpha = 0.0
        self.impulse_choice = ""
        self.point_choice = ""
        self.complete = False
        self._rings.clear()
        self._memory_shards.clear()
        self._flash_alpha = 0.0
        self._camera_shake = 0.0
        self._pulse_timer = 0.0
        self._memory_timer = 0.0

    def _build_stars(self, count: int) -> List[IntroStar]:
        """Build the intro starfield."""
        stars: List[IntroStar] = []
        for _ in range(count):
            stars.append(
                IntroStar(
                    x=random.uniform(0, self.width),
                    y=random.uniform(0, self.height),
                    drift_x=random.uniform(-3.0, 3.0),
                    drift_y=random.uniform(-6.0, 6.0),
                    size=random.uniform(0.8, 2.4),
                    twinkle_phase=random.uniform(0.0, math.tau),
                    twinkle_speed=random.uniform(0.6, 2.4),
                    depth=random.uniform(0.25, 1.0),
                )
            )
        return stars

    def _phase_color(self) -> Tuple[int, int, int]:
        """Return the primary accent color for the current phase."""
        return self._phase_colors.get(self.phase, self.bg_color)

    def _build_phase_dialogues(self, phase: IntroPhase) -> List[DialogueLine]:
        """Build dialogue list for a phase, including final echoes."""
        base_dialogues = list(INTRO_DIALOGUES.get(phase, []))
        if phase != IntroPhase.FINAL_DIALOGUE:
            return base_dialogues

        insert_at = max(1, len(base_dialogues) - 3)
        echoes: List[DialogueLine] = []
        if self.impulse_choice:
            echoes.extend(FINAL_IMPULSE_ECHOS.get(self.impulse_choice, []))
        if self.point_choice:
            echoes.extend(FINAL_POINT_ECHOS.get(self.point_choice, []))
        base_dialogues[insert_at:insert_at] = echoes
        return base_dialogues

    def _spawn_ring(
        self,
        color: Tuple[int, int, int],
        radius: float = 40.0,
        speed: float = 120.0,
        alpha: float = 0.42,
        fade_speed: float = 0.22,
        width: int = 2,
    ) -> None:
        """Spawn a dimensional pulse ring."""
        self._rings.append(
            SignalRing(
                radius=radius,
                speed=speed,
                alpha=alpha,
                fade_speed=fade_speed,
                color=color,
                width=width,
            )
        )

    def _spawn_memory_shard(self) -> None:
        """Spawn a shard for the memory flash phase."""
        color_choices = [
            (118, 208, 196),
            (166, 144, 232),
            (216, 188, 255),
        ]
        self._memory_shards.append(
            MemoryShard(
                x=random.uniform(self.width * 0.16, self.width * 0.84),
                y=random.uniform(self.height * 0.16, self.height * 0.72),
                vx=random.uniform(-28.0, 28.0),
                vy=random.uniform(-18.0, 18.0),
                length=random.uniform(26.0, 82.0),
                angle=random.uniform(0.0, math.tau),
                rotation_speed=random.uniform(-1.2, 1.2),
                alpha=random.uniform(0.25, 0.7),
                fade_speed=random.uniform(0.16, 0.34),
                color=random.choice(color_choices),
            )
        )

    def _trigger_flash(self, color: Tuple[int, int, int], alpha: float, shake: float) -> None:
        """Trigger a brief screen flash and camera shake."""
        self._flash_color = color
        self._flash_alpha = max(self._flash_alpha, alpha)
        self._camera_shake = max(self._camera_shake, shake)
    
    def _advance_phase(self) -> None:
        """Advance to the next phase."""
        phase_order = [
            IntroPhase.FADE_UI,
            IntroPhase.PRELUDE,
            IntroPhase.MEMORY_FLASH,
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
            self.current_dialogues = self._build_phase_dialogues(self.phase)
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

        color = self._phase_color()
        self._spawn_ring(color, radius=36, speed=160, alpha=0.4, fade_speed=0.24, width=2)
        if self.phase in (
            IntroPhase.MEMORY_FLASH,
            IntroPhase.TRANSITION_4D_3D,
            IntroPhase.TRANSITION_3D_2D,
            IntroPhase.TRANSITION_2D_1D,
            IntroPhase.FINAL_DIALOGUE,
        ):
            self._spawn_ring(color, radius=24, speed=210, alpha=0.28, fade_speed=0.26, width=3)
            self._trigger_flash(color, alpha=0.18, shake=7.0)
        elif self.phase in (
            IntroPhase.SHAPE_4D,
            IntroPhase.SHAPE_3D,
            IntroPhase.SHAPE_2D,
            IntroPhase.SHAPE_1D,
            IntroPhase.FIRST_POINT_INTERLUDE,
        ):
            self._trigger_flash(color, alpha=0.08, shake=3.0)
        
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
            self.current_dialogues[insert_at:insert_at] = list(INTRO_BRANCHES[branch_id])
        # Capture intro impulse choice
        impulse_map = {
            "impulse_lean": "lean",
            "impulse_listen": "listen",
            "impulse_hesitate": "hesitate",
        }
        if branch_id in impulse_map:
            self.impulse_choice = impulse_map[branch_id]
        if branch_id in ("point_reach", "point_still", "point_listen"):
            self.point_choice = branch_id
        self._spawn_ring(self._phase_color(), radius=32, speed=185, alpha=0.35, fade_speed=0.3, width=3)
        self._trigger_flash(self._phase_color(), alpha=0.12, shake=4.0)
        # Advance to the next line after choice
        self.dialogue_index += 1
        if self.dialogue_index < len(self.current_dialogues):
            self.textbox.show(self.current_dialogues[self.dialogue_index])
        else:
            self._advance_phase()

    def _update_ambient(self, dt: float) -> None:
        """Update stars, rings, shards, and camera effects."""
        for star in self._stars:
            star.x += star.drift_x * star.depth * dt
            star.y += star.drift_y * star.depth * dt
            star.twinkle_phase += star.twinkle_speed * dt

            if star.x < -4:
                star.x = self.width + 4
            elif star.x > self.width + 4:
                star.x = -4
            if star.y < -4:
                star.y = self.height + 4
            elif star.y > self.height + 4:
                star.y = -4

        for ring in self._rings[:]:
            ring.radius += ring.speed * dt
            ring.alpha = max(0.0, ring.alpha - ring.fade_speed * dt)
            if ring.alpha <= 0.01:
                self._rings.remove(ring)

        if self.phase == IntroPhase.MEMORY_FLASH:
            self._memory_timer += dt
            if self._memory_timer >= 0.08:
                self._spawn_memory_shard()
                self._memory_timer = 0.0

        for shard in self._memory_shards[:]:
            shard.x += shard.vx * dt
            shard.y += shard.vy * dt
            shard.angle += shard.rotation_speed * dt
            shard.alpha = max(0.0, shard.alpha - shard.fade_speed * dt)
            if shard.alpha <= 0.02:
                self._memory_shards.remove(shard)

        pulsing_phase = self.phase in (
            IntroPhase.PRELUDE,
            IntroPhase.MEMORY_FLASH,
            IntroPhase.SHAPE_4D,
            IntroPhase.SHAPE_3D,
            IntroPhase.SHAPE_2D,
            IntroPhase.SHAPE_1D,
            IntroPhase.FIRST_POINT_INTERLUDE,
            IntroPhase.FINAL_DIALOGUE,
        )
        if pulsing_phase:
            self._pulse_timer += dt
            pulse_interval = 1.0 if self.phase in (IntroPhase.MEMORY_FLASH, IntroPhase.FINAL_DIALOGUE) else 1.45
            if self._pulse_timer >= pulse_interval:
                self._spawn_ring(self._phase_color(), radius=44, speed=120, alpha=0.24, fade_speed=0.16, width=2)
                self._pulse_timer = 0.0

        self._flash_alpha = max(0.0, self._flash_alpha - dt * 0.34)
        self._camera_shake = max(0.0, self._camera_shake - dt * 7.0)

    def _camera_offset(self) -> Tuple[int, int]:
        """Return camera drift and shake offset."""
        drift_x = int(math.sin(self.phase_timer * 0.55) * 14)
        drift_y = int(math.cos(self.phase_timer * 0.38) * 8)
        if self._camera_shake <= 0.0:
            return drift_x, drift_y

        shake_x = random.uniform(-self._camera_shake, self._camera_shake)
        shake_y = random.uniform(-self._camera_shake, self._camera_shake)
        return int(drift_x + shake_x), int(drift_y + shake_y)
    
    def update(self, dt: float) -> None:
        """Update the intro sequence."""
        self.phase_timer += dt
        self.shape.update(dt)
        self._update_ambient(dt)
        
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

    def _draw_background(self) -> None:
        """Draw the intro gradient and starfield."""
        accent = self._phase_color()
        top = tuple(int(6 + c * 0.12) for c in accent)
        bottom = tuple(int(2 + c * 0.03) for c in accent)

        for y in range(self.height):
            t = y / max(1, self.height - 1)
            color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))

        for star in self._stars:
            twinkle = 0.45 + 0.55 * math.sin(star.twinkle_phase)
            brightness = max(0.15, twinkle * star.depth)
            color = (
                int(170 + accent[0] * 0.18 * brightness),
                int(178 + accent[1] * 0.14 * brightness),
                int(198 + accent[2] * 0.16 * brightness),
            )
            pygame.draw.circle(
                self.screen,
                color,
                (int(star.x), int(star.y)),
                max(1, int(star.size * (0.8 + 0.2 * twinkle))),
            )

    def _draw_ambient_fx(self) -> None:
        """Draw rings, memory shards, and the pre-shape aura."""
        fx = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        center_x = self.width // 2
        center_y = self.height // 2 - 44

        if self.phase in (IntroPhase.PRELUDE, IntroPhase.MEMORY_FLASH, IntroPhase.FINAL_DIALOGUE):
            pulse = 1.0 + 0.08 * math.sin(self.phase_timer * 2.4)
            radius = int(54 * pulse)
            for layer in range(4, 0, -1):
                layer_radius = radius + layer * 18
                alpha = int((22 - layer * 4) * (0.8 + 0.2 * math.sin(self.phase_timer * 1.2)))
                pygame.draw.circle(fx, (*self._phase_color(), max(0, alpha)), (center_x, center_y), layer_radius)
            pygame.draw.circle(fx, (255, 255, 255, 240), (center_x, center_y), max(4, int(7 * pulse)))

        for ring in self._rings:
            radius = int(ring.radius)
            if radius <= 0:
                continue
            pygame.draw.circle(
                fx,
                (*ring.color, int(255 * ring.alpha)),
                (center_x, center_y),
                radius,
                ring.width,
            )

        for shard in self._memory_shards:
            dx = math.cos(shard.angle) * shard.length * 0.5
            dy = math.sin(shard.angle) * shard.length * 0.5
            start = (int(shard.x - dx), int(shard.y - dy))
            end = (int(shard.x + dx), int(shard.y + dy))
            pygame.draw.line(fx, (*shard.color, int(255 * shard.alpha)), start, end, 2)

        self.screen.blit(fx, (0, 0))

    def _draw_phase_title(self) -> None:
        """Draw a small phase title at the top."""
        titles = {
            IntroPhase.PRELUDE: ("ATTENTION", "before geometry"),
            IntroPhase.MEMORY_FLASH: ("MONODIA", "a memory from the Line of One"),
            IntroPhase.SHAPE_4D: ("4D", "a wider wound"),
            IntroPhase.SHAPE_3D: ("3D", "volume, shelter, hidden interiors"),
            IntroPhase.SHAPE_2D: ("2D", "a plane that mistakes itself for all"),
            IntroPhase.SHAPE_1D: ("1D", "the narrow mercy of direction"),
            IntroPhase.FIRST_POINT_INTERLUDE: ("THE FIRST POINT", "where preference first became an axis"),
            IntroPhase.FINAL_DIALOGUE: ("DESCENT", "the smallest promise remains"),
        }
        if self.phase not in titles:
            return

        title, subtitle = titles[self.phase]
        color = self._phase_color()
        font_title = pygame.font.Font(None, 38)
        font_sub = pygame.font.Font(None, 24)
        title_surf = font_title.render(title, True, color)
        subtitle_surf = font_sub.render(subtitle, True, (176, 186, 206))
        title_rect = title_surf.get_rect(center=(self.width // 2, 76))
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, 102))
        self.screen.blit(title_surf, title_rect)
        self.screen.blit(subtitle_surf, subtitle_rect)
    
    def draw(self) -> None:
        """Draw the intro sequence."""
        self._draw_background()
        self._draw_ambient_fx()
        
        # Shape
        if self.phase not in [IntroPhase.FADE_UI, IntroPhase.PRELUDE, IntroPhase.MEMORY_FLASH]:
            camera_x, camera_y = self._camera_offset()
            center = (self.width // 2 + camera_x, self.height // 2 - 50 + camera_y)
            scale = 128 + int(6 * math.sin(self.phase_timer * 1.4))
            self.shape.draw(self.screen, center, scale=scale)

        self._draw_phase_title()
        
        # Textbox
        self.textbox.draw()
        
        # Fade overlay
        if self.overlay_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(int(255 * self.overlay_alpha))
            self.screen.blit(overlay, (0, 0))

        if self._flash_alpha > 0:
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash.fill((*self._flash_color, int(255 * self._flash_alpha)))
            self.screen.blit(flash, (0, 0), special_flags=pygame.BLEND_ADD)
    
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
