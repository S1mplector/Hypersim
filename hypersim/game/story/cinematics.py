"""Cinematic scene system for story moments.

Handles special visual effects, animated introductions, and
atmospheric cutscenes that go beyond simple dialogue.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING
import math

import pygame
import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ui.textbox import DialogueSystem


class CinematicState(Enum):
    """State of a cinematic scene."""
    IDLE = auto()
    PLAYING = auto()
    PAUSED = auto()
    FINISHED = auto()


@dataclass
class GlowingEntity:
    """A glowing entity for cinematic rendering."""
    position: Tuple[float, float]  # Screen position (0-1 normalized)
    color: Tuple[int, int, int]  # RGB color
    size: float = 20.0  # Base size in pixels
    glow_radius: float = 60.0  # Outer glow radius
    glow_layers: int = 8  # Number of glow layers
    pulse_speed: float = 1.5  # Pulse animation speed
    pulse_amount: float = 0.2  # How much to pulse (0-1)
    
    # Animation state
    alpha: float = 0.0  # Current visibility (0-1)
    fade_in_duration: float = 3.0  # Seconds to fade in
    _time: float = 0.0


class FirstPointCinematic:
    """Cinematic scene for the First Point's introduction in Chapter 1.
    
    Shows a large purple glowing point slowly fading in at the start
    of the line, with an ethereal aura effect.
    """
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # State
        self.state = CinematicState.IDLE
        self._time = 0.0
        self._phase = 0  # Current phase of the cinematic
        
        # The First Point entity
        self.first_point = GlowingEntity(
            position=(0.3, 0.5),  # Left side of screen, on the line
            color=(180, 100, 255),  # Purple
            size=35.0,
            glow_radius=120.0,
            glow_layers=12,
            pulse_speed=1.2,
            pulse_amount=0.15,
            fade_in_duration=4.0,
        )
        
        # Background fade
        self._bg_alpha = 0.0
        self._bg_target = 0.8
        
        # Particle effects for aura
        self._particles: List[Dict] = []
        self._particle_timer = 0.0
        
        # Callbacks
        self.on_phase_complete: Optional[Callable[[int], None]] = None
        self.on_cinematic_complete: Optional[Callable[[], None]] = None
        
        # Dialogue integration
        self._dialogue_system: Optional[DialogueSystem] = None
        self._waiting_for_dialogue = False
        
        # Phase timing
        self._phase_durations = [
            2.0,   # Phase 0: Darkness, background fade in
            4.0,   # Phase 1: First Point slowly glows into existence
            1.0,   # Phase 2: Point fully visible, slight pause
            0.0,   # Phase 3: Dialogue begins (manual advance)
        ]
        self._phase_start_time = 0.0
    
    def start(self, dialogue_system: Optional["DialogueSystem"] = None) -> None:
        """Start the cinematic."""
        self.state = CinematicState.PLAYING
        self._time = 0.0
        self._phase = 0
        self._phase_start_time = 0.0
        self._dialogue_system = dialogue_system
        self._waiting_for_dialogue = False
        
        # Reset entity
        self.first_point.alpha = 0.0
        self.first_point._time = 0.0
        self._bg_alpha = 0.0
        self._particles.clear()
    
    def stop(self) -> None:
        """Stop the cinematic."""
        self.state = CinematicState.FINISHED
        if self.on_cinematic_complete:
            self.on_cinematic_complete()
    
    def skip(self) -> None:
        """Skip to end of cinematic."""
        self.first_point.alpha = 1.0
        self._bg_alpha = self._bg_target
        self.stop()
    
    def _advance_phase(self) -> None:
        """Advance to the next phase."""
        if self.on_phase_complete:
            self.on_phase_complete(self._phase)
        
        self._phase += 1
        self._phase_start_time = self._time
        
        if self._phase >= len(self._phase_durations):
            self.stop()
    
    def _spawn_particle(self) -> None:
        """Spawn an aura particle."""
        if len(self._particles) > 50:
            return
        
        # Spawn around the First Point
        angle = np.random.uniform(0, 2 * math.pi)
        distance = np.random.uniform(30, 80)
        
        base_x = self.first_point.position[0] * self.width
        base_y = self.first_point.position[1] * self.height
        
        self._particles.append({
            "x": base_x + math.cos(angle) * distance,
            "y": base_y + math.sin(angle) * distance,
            "vx": math.cos(angle) * -15,  # Move toward center
            "vy": math.sin(angle) * -15,
            "size": np.random.uniform(2, 5),
            "alpha": np.random.uniform(0.3, 0.7),
            "life": np.random.uniform(1.5, 3.0),
            "max_life": 3.0,
            "color": (
                self.first_point.color[0] + np.random.randint(-20, 20),
                self.first_point.color[1] + np.random.randint(-20, 20),
                min(255, self.first_point.color[2] + np.random.randint(0, 40)),
            ),
        })
    
    def update(self, dt: float) -> None:
        """Update the cinematic."""
        if self.state != CinematicState.PLAYING:
            return
        
        self._time += dt
        phase_time = self._time - self._phase_start_time
        
        # Update based on current phase
        if self._phase == 0:
            # Phase 0: Background fade in
            self._bg_alpha = min(self._bg_target, phase_time / 1.5)
            
            if phase_time >= self._phase_durations[0]:
                self._advance_phase()
        
        elif self._phase == 1:
            # Phase 1: First Point fades in with glow
            fade_progress = phase_time / self.first_point.fade_in_duration
            self.first_point.alpha = min(1.0, fade_progress)
            self.first_point._time = self._time
            
            # Spawn particles as point appears
            self._particle_timer += dt
            if self._particle_timer > 0.1 and self.first_point.alpha > 0.2:
                self._spawn_particle()
                self._particle_timer = 0
            
            if phase_time >= self._phase_durations[1]:
                self._advance_phase()
        
        elif self._phase == 2:
            # Phase 2: Pause before dialogue
            self.first_point._time = self._time
            
            # Keep spawning particles
            self._particle_timer += dt
            if self._particle_timer > 0.15:
                self._spawn_particle()
                self._particle_timer = 0
            
            if phase_time >= self._phase_durations[2]:
                self._advance_phase()
                # Trigger dialogue
                if self._dialogue_system:
                    self._dialogue_system.start_sequence("chapter_1_first_point_intro")
                    self._waiting_for_dialogue = True
        
        elif self._phase == 3:
            # Phase 3: During dialogue - keep animating
            self.first_point._time = self._time
            
            # Keep spawning particles
            self._particle_timer += dt
            if self._particle_timer > 0.2:
                self._spawn_particle()
                self._particle_timer = 0
            
            # Check if dialogue is done
            if self._dialogue_system and not self._dialogue_system.is_active:
                self._waiting_for_dialogue = False
                self._advance_phase()
        
        # Update particles
        self._update_particles(dt)
    
    def _update_particles(self, dt: float) -> None:
        """Update particle effects."""
        for p in self._particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            
            # Fade out as life decreases
            life_ratio = p["life"] / p["max_life"]
            p["alpha"] = min(p["alpha"], life_ratio * 0.7)
            
            if p["life"] <= 0:
                self._particles.remove(p)
    
    def draw(self) -> None:
        """Draw the cinematic."""
        if self.state == CinematicState.IDLE:
            return
        
        # Draw dark overlay
        if self._bg_alpha > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((5, 5, 15, int(255 * self._bg_alpha)))
            self.screen.blit(overlay, (0, 0))
        
        # Draw the line (1D world representation)
        line_y = int(self.height * 0.5)
        pygame.draw.line(
            self.screen,
            (40, 40, 80),
            (0, line_y),
            (self.width, line_y),
            3
        )
        
        # Draw particles (behind the point)
        self._draw_particles()
        
        # Draw the First Point
        if self.first_point.alpha > 0:
            self._draw_glowing_point(self.first_point)
    
    def _draw_particles(self) -> None:
        """Draw aura particles."""
        for p in self._particles:
            if p["alpha"] <= 0:
                continue
            
            color = (*p["color"], int(255 * p["alpha"] * self.first_point.alpha))
            size = int(p["size"])
            
            # Draw particle with glow
            surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (size * 2, size * 2), size)
            
            # Outer glow
            glow_color = (*p["color"][:3], int(100 * p["alpha"] * self.first_point.alpha))
            pygame.draw.circle(surf, glow_color, (size * 2, size * 2), size * 2)
            
            self.screen.blit(surf, (int(p["x"]) - size * 2, int(p["y"]) - size * 2))
    
    def _draw_glowing_point(self, entity: GlowingEntity) -> None:
        """Draw a glowing point entity with aura."""
        if entity.alpha <= 0:
            return
        
        x = int(entity.position[0] * self.width)
        y = int(entity.position[1] * self.height)
        
        # Pulse effect
        pulse = math.sin(entity._time * entity.pulse_speed * 2 * math.pi)
        pulse_factor = 1.0 + pulse * entity.pulse_amount
        
        # Draw outer glow layers (largest to smallest)
        for i in range(entity.glow_layers, 0, -1):
            layer_ratio = i / entity.glow_layers
            radius = int(entity.glow_radius * layer_ratio * pulse_factor)
            
            # Glow gets more transparent at outer edges
            alpha = int(60 * (1 - layer_ratio) * entity.alpha)
            color = (
                entity.color[0],
                entity.color[1],
                entity.color[2],
                alpha
            )
            
            # Create surface for this glow layer
            glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, color, (radius, radius), radius)
            self.screen.blit(glow_surf, (x - radius, y - radius))
        
        # Draw inner bright core layers
        core_layers = 5
        for i in range(core_layers):
            layer_ratio = (core_layers - i) / core_layers
            radius = int(entity.size * layer_ratio * pulse_factor)
            
            # Core is brighter
            brightness = 0.5 + 0.5 * (1 - layer_ratio)
            alpha = int(255 * brightness * entity.alpha)
            
            # Blend toward white at center
            blend = 1 - layer_ratio
            color = (
                int(entity.color[0] + (255 - entity.color[0]) * blend),
                int(entity.color[1] + (255 - entity.color[1]) * blend),
                int(entity.color[2] + (255 - entity.color[2]) * blend),
                alpha
            )
            
            core_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(core_surf, color, (radius + 2, radius + 2), radius)
            self.screen.blit(core_surf, (x - radius - 2, y - radius - 2))
        
        # Draw bright center point
        center_size = int(8 * pulse_factor)
        pygame.draw.circle(
            self.screen,
            (255, 255, 255),
            (x, y),
            center_size
        )
    
    @property
    def is_active(self) -> bool:
        """Check if cinematic is currently playing."""
        return self.state == CinematicState.PLAYING
    
    @property
    def is_finished(self) -> bool:
        """Check if cinematic has finished."""
        return self.state == CinematicState.FINISHED


# =============================================================================
# CHAPTER 1 SPECIFIC DIALOGUES FOR FIRST POINT INTRO
# =============================================================================

FIRST_POINT_INTRO_DIALOGUE = [
    {"speaker": "", "text": "..."},
    {"speaker": "", "text": "In the void, something stirs."},
    {"speaker": "", "text": "A warmth. Ancient beyond measure."},
    {"speaker": "", "text": "It has been waiting."},
    {"speaker": "", "text": "Waiting for you."},
    {"speaker": "The First Point", "text": "..."},
    {"speaker": "The First Point", "text": "There you are, little one."},
    {"speaker": "The First Point", "text": "I felt you the moment you came into being."},
    {"speaker": "The First Point", "text": "A new spark of awareness, born from the infinite potential of the void."},
    {"speaker": "The First Point", "text": "Do not be afraid."},
    {"speaker": "The First Point", "text": "I am the First Point. The origin. The beginning of all things."},
    {"speaker": "The First Point", "text": "Every line that stretches outward... every shape that takes form..."},
    {"speaker": "The First Point", "text": "They all trace their existence back to me."},
    {"speaker": "The First Point", "text": "And now, so do you."},
    {"speaker": "", "text": "The purple glow pulses gently, like a heartbeat."},
    {"speaker": "The First Point", "text": "You have been given something precious: direction."},
    {"speaker": "The First Point", "text": "Forward. Backward. The first taste of dimension."},
    {"speaker": "The First Point", "text": "I know it feels strange. Limited, perhaps."},
    {"speaker": "The First Point", "text": "But this is how all journeys begin—with a single step along a single line."},
    {"speaker": "The First Point", "text": "Go now. Explore this world of one dimension."},
    {"speaker": "The First Point", "text": "Learn what it means to move, to grow, to exist."},
    {"speaker": "The First Point", "text": "And when you are ready for more... the way will open."},
    {"speaker": "The First Point", "text": "I will be here, at the origin. Watching over you."},
    {"speaker": "The First Point", "text": "Always."},
    {"speaker": "", "text": "The First Point's glow settles into a steady, comforting radiance."},
    {"speaker": "System", "text": "Use A/D or Arrow Keys to move along the Line."},
    {"speaker": "System", "text": "Press E to interact with beings you encounter."},
    {"speaker": "System", "text": "The First Point will remain here if you wish to speak again."},
]


def get_first_point_dialogue() -> List[Dict]:
    """Get the First Point introduction dialogue."""
    return FIRST_POINT_INTRO_DIALOGUE.copy()


# =============================================================================
# FIRST POINT INTERACTION DIALOGUES (after initial intro)
# =============================================================================

FIRST_POINT_INTERACTION_DIALOGUES = {
    "greeting": [
        {"speaker": "The First Point", "text": "Ah, little one. You've returned to me."},
        {"speaker": "The First Point", "text": "Is there something you wish to know?",
         "choices": [
             ("Tell me about the Line.", "line_info"),
             ("Who are you, really?", "identity"),
             ("I'm ready to continue.", "farewell"),
         ]},
    ],
    "line_info": [
        {"speaker": "The First Point", "text": "The Line is your first home. Your first limitation."},
        {"speaker": "The First Point", "text": "Here, you can only move forward or backward."},
        {"speaker": "The First Point", "text": "Other beings walk this Line too."},
        {"speaker": "The First Point", "text": "Some are friendly. Some are lost. Some are... territorial."},
        {"speaker": "The First Point", "text": "At the far end lies the Endpoint, guarded by one who protects the way forward."},
        {"speaker": "The First Point", "text": "Defeat them, and a new direction will reveal itself to you."},
        {"speaker": "The First Point", "text": "Is there anything else you wish to know?",
         "choices": [
             ("Who are you, really?", "identity"),
             ("I'm ready to continue.", "farewell"),
         ]},
    ],
    "identity": [
        {"speaker": "The First Point", "text": "Who am I..."},
        {"speaker": "The First Point", "text": "I am the first thing that ever was."},
        {"speaker": "The First Point", "text": "Before direction. Before extension. Before dimension itself."},
        {"speaker": "The First Point", "text": "There was the Void—pure potential, undifferentiated and infinite."},
        {"speaker": "The First Point", "text": "And then... awareness. A single point that knew itself."},
        {"speaker": "The First Point", "text": "That was me. That IS me."},
        {"speaker": "The First Point", "text": "From my self-awareness, the Line emerged. From the Line, the Plane."},
        {"speaker": "The First Point", "text": "And so on, infinitely upward through dimensions you cannot yet imagine."},
        {"speaker": "The First Point", "text": "But I remain here, at the origin. Watching. Guiding those who seek to grow."},
        {"speaker": "The First Point", "text": "Like you."},
        {"speaker": "The First Point", "text": "Is there anything else, little spark?",
         "choices": [
             ("Tell me about the Line.", "line_info"),
             ("I'm ready to continue.", "farewell"),
         ]},
    ],
    "farewell": [
        {"speaker": "The First Point", "text": "Then go, little one. Explore. Grow. Become."},
        {"speaker": "The First Point", "text": "And remember—no matter how far you travel..."},
        {"speaker": "The First Point", "text": "...every journey begins at a single point."},
        {"speaker": "The First Point", "text": "I will be here when you need me."},
    ],
}


def get_first_point_interaction_dialogue(dialogue_key: str = "greeting") -> List[Dict]:
    """Get dialogue for interacting with the First Point after the intro."""
    return FIRST_POINT_INTERACTION_DIALOGUES.get(dialogue_key, FIRST_POINT_INTERACTION_DIALOGUES["greeting"]).copy()
