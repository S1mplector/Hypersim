"""Textbox and dialogue system for campaign storytelling.

Features:
- Typewriter text effect with adjustable speed
- Undertale-style voice beeps (unique per character)
- Multiple visual styles
- Choice selection
- Portrait support
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from hypersim.game.story.cinematics import get_first_point_dialogue

# Voice synthesis for typewriter beeps
try:
    from hypersim.game.audio.voice_synth import (
        VoiceSynthesizer, VoiceProfile, VOICE_PRESETS, get_typewriter
    )
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False


class TextBoxStyle(Enum):
    """Visual style presets for textboxes."""
    NARRATOR = "narrator"      # Centered, ethereal
    CHARACTER = "character"    # Bottom, with portrait space
    SYSTEM = "system"          # Top, minimal
    TUTORIAL = "tutorial"      # Highlighted, with icon
    DIMENSION = "dimension"    # Special style per dimension


@dataclass
class DialogueLine:
    """A single line of dialogue."""
    text: str
    speaker: str = ""
    style: TextBoxStyle = TextBoxStyle.NARRATOR
    duration: float = 0.0  # 0 = wait for input
    typing_speed: float = 30.0  # Characters per second
    voice_id: Optional[str] = None  # For audio
    portrait: Optional[str] = None  # Portrait image key
    choices: List[Tuple[str, str]] = field(default_factory=list)  # (text, callback_id)
    on_complete: Optional[str] = None  # Event to fire when done


@dataclass
class DialogueSequence:
    """A sequence of dialogue lines."""
    id: str
    lines: List[DialogueLine]
    on_start: Optional[str] = None
    on_end: Optional[str] = None
    can_skip: bool = True
    pause_game: bool = True


class TextBox:
    """Renders a textbox with typewriter effect."""
    
    # Style configurations
    STYLES: Dict[TextBoxStyle, Dict] = {
        TextBoxStyle.NARRATOR: {
            "bg_color": (10, 10, 20, 220),
            "border_color": (100, 120, 180),
            "text_color": (220, 220, 240),
            "speaker_color": (180, 200, 255),
            "position": "center",
            "width_ratio": 0.7,
            "padding": 30,
            "border_width": 2,
        },
        TextBoxStyle.CHARACTER: {
            "bg_color": (15, 15, 25, 230),
            "border_color": (80, 100, 160),
            "text_color": (240, 240, 240),
            "speaker_color": (100, 200, 255),
            "position": "bottom",
            "width_ratio": 0.85,
            "padding": 25,
            "border_width": 2,
        },
        TextBoxStyle.SYSTEM: {
            "bg_color": (5, 5, 15, 200),
            "border_color": (60, 60, 80),
            "text_color": (180, 180, 200),
            "speaker_color": (150, 150, 180),
            "position": "top",
            "width_ratio": 0.6,
            "padding": 15,
            "border_width": 1,
        },
        TextBoxStyle.TUTORIAL: {
            "bg_color": (20, 30, 40, 230),
            "border_color": (100, 180, 255),
            "text_color": (255, 255, 255),
            "speaker_color": (100, 200, 255),
            "position": "bottom",
            "width_ratio": 0.75,
            "padding": 25,
            "border_width": 3,
        },
        TextBoxStyle.DIMENSION: {
            "bg_color": (15, 10, 25, 220),
            "border_color": (150, 100, 200),
            "text_color": (230, 220, 255),
            "speaker_color": (200, 150, 255),
            "position": "center",
            "width_ratio": 0.65,
            "padding": 30,
            "border_width": 2,
        },
    }
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Current state
        self.active = False
        self.current_line: Optional[DialogueLine] = None
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0.0
        self.complete = False
        self.waiting_for_input = False
        self.selected_choice = 0
        
        # Animation
        self.fade_alpha = 0.0
        self.fade_speed = 5.0
        
        # Voice synthesis
        self._voice_synth: Optional[VoiceSynthesizer] = None
        self._current_voice: Optional[VoiceProfile] = None
        self._voice_enabled = True
        self._voice_volume = 0.5
        self._last_beep_char = -1  # Track last character that beeped
        
        if VOICE_AVAILABLE:
            self._voice_synth = VoiceSynthesizer()
        
        # Callbacks
        self._on_complete: Optional[Callable] = None
        self._on_choice: Optional[Callable[[str], None]] = None
    
    def show(
        self,
        line: DialogueLine,
        on_complete: Optional[Callable] = None,
        on_choice: Optional[Callable[[str], None]] = None
    ) -> None:
        """Show a dialogue line."""
        self.active = True
        self.current_line = line
        self.displayed_text = ""
        self.char_index = 0
        self.char_timer = 0.0
        self.complete = False
        self.waiting_for_input = False
        self.selected_choice = 0
        self._on_complete = on_complete
        self._on_choice = on_choice
        self._last_beep_char = -1
        
        # Set up voice for this line
        if VOICE_AVAILABLE and self._voice_synth:
            voice_id = line.voice_id or "default"
            self._current_voice = VOICE_PRESETS.get(voice_id, VOICE_PRESETS.get("default"))
    
    def hide(self) -> None:
        """Hide the textbox."""
        self.active = False
        self.current_line = None
    
    def _play_voice_beep(self, char: str, char_index: int) -> None:
        """Play a voice beep for a character."""
        if not self._voice_synth or not self._current_voice:
            return
        
        # Skip spaces and some punctuation
        if char in ' \n\t':
            return
        if self._current_voice.skip_punctuation and char in '.,!?;:\'"()-':
            return
        
        # Generate and play beep
        try:
            beep = self._voice_synth.get_cached_beep(self._current_voice, char_index)
            beep.set_volume(self._current_voice.volume * self._voice_volume)
            beep.play()
        except Exception:
            pass  # Silently fail if audio not available
    
    def set_voice_enabled(self, enabled: bool) -> None:
        """Enable or disable voice beeps."""
        self._voice_enabled = enabled
    
    def set_voice_volume(self, volume: float) -> None:
        """Set voice volume (0.0 to 1.0)."""
        self._voice_volume = max(0.0, min(1.0, volume))
    
    def skip_typing(self) -> None:
        """Skip to fully displayed text."""
        if self.current_line and not self.complete:
            self.displayed_text = self.current_line.text
            self.char_index = len(self.current_line.text)
            self.complete = True
            self.waiting_for_input = self.current_line.duration == 0
    
    def advance(self) -> bool:
        """Advance dialogue (on input). Returns True if should continue."""
        if not self.active or not self.current_line:
            return False
        
        if not self.complete:
            self.skip_typing()
            return True
        
        if self.current_line.choices and self._on_choice:
            choice_id = self.current_line.choices[self.selected_choice][1]
            self._on_choice(choice_id)
        
        if self._on_complete:
            self._on_complete()
        
        return True
    
    def select_choice(self, delta: int) -> None:
        """Change selected choice."""
        if self.current_line and self.current_line.choices:
            num_choices = len(self.current_line.choices)
            self.selected_choice = (self.selected_choice + delta) % num_choices
    
    def update(self, dt: float) -> None:
        """Update textbox state."""
        if not self.active or not self.current_line:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed * dt)
            return
        
        # Fade in
        self.fade_alpha = min(1.0, self.fade_alpha + self.fade_speed * dt)
        
        # Typewriter effect
        if not self.complete:
            self.char_timer += dt
            chars_to_add = int(self.char_timer * self.current_line.typing_speed)
            
            if chars_to_add > 0:
                self.char_timer = 0
                old_index = self.char_index
                new_index = min(
                    self.char_index + chars_to_add,
                    len(self.current_line.text)
                )
                self.displayed_text = self.current_line.text[:new_index]
                self.char_index = new_index
                
                # Play voice beeps for new characters
                if self._voice_enabled and self._voice_synth and self._current_voice:
                    for i in range(old_index, new_index):
                        if i > self._last_beep_char:
                            self._play_voice_beep(self.current_line.text[i], i)
                            self._last_beep_char = i
                
                if self.char_index >= len(self.current_line.text):
                    self.complete = True
                    if self.current_line.duration == 0:
                        self.waiting_for_input = True
        
        # Auto-advance if duration set
        elif self.current_line.duration > 0:
            self.char_timer += dt
            if self.char_timer >= self.current_line.duration:
                self.advance()
    
    def draw(self) -> None:
        """Draw the textbox."""
        if self.fade_alpha <= 0 or not self.current_line:
            return
        
        style = self.STYLES.get(self.current_line.style, self.STYLES[TextBoxStyle.NARRATOR])
        
        # Calculate box dimensions
        box_width = int(self.width * style["width_ratio"])
        padding = style["padding"]
        
        # Prepare fonts
        font_text = pygame.font.Font(None, 28)
        font_speaker = pygame.font.Font(None, 24)
        font_hint = pygame.font.Font(None, 20)
        
        # Wrap text
        wrapped_lines = self._wrap_text(self.displayed_text, font_text, box_width - padding * 2)
        
        # Calculate height
        line_height = font_text.get_linesize()
        text_height = len(wrapped_lines) * line_height
        
        speaker_height = font_speaker.get_linesize() + 10 if self.current_line.speaker else 0
        choices_height = len(self.current_line.choices) * 30 if self.current_line.choices else 0
        hint_height = 25 if self.waiting_for_input else 0
        
        box_height = padding * 2 + speaker_height + text_height + choices_height + hint_height
        
        # Position
        if style["position"] == "center":
            box_x = (self.width - box_width) // 2
            box_y = (self.height - box_height) // 2
        elif style["position"] == "bottom":
            box_x = (self.width - box_width) // 2
            box_y = self.height - box_height - 40
        else:  # top
            box_x = (self.width - box_width) // 2
            box_y = 40
        
        # Draw background
        bg_color = style["bg_color"]
        bg_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        bg_surface.fill((bg_color[0], bg_color[1], bg_color[2], int(bg_color[3] * self.fade_alpha)))
        self.screen.blit(bg_surface, (box_x, box_y))
        
        # Draw border
        border_color = tuple(int(c * self.fade_alpha) for c in style["border_color"])
        pygame.draw.rect(
            self.screen, border_color,
            (box_x, box_y, box_width, box_height),
            style["border_width"]
        )
        
        # Draw speaker name
        y_offset = box_y + padding
        if self.current_line.speaker:
            speaker_color = tuple(int(c * self.fade_alpha) for c in style["speaker_color"])
            speaker_text = font_speaker.render(self.current_line.speaker, True, speaker_color)
            self.screen.blit(speaker_text, (box_x + padding, y_offset))
            y_offset += speaker_height
        
        # Draw text
        text_color = tuple(int(c * self.fade_alpha) for c in style["text_color"])
        for line in wrapped_lines:
            text_surface = font_text.render(line, True, text_color)
            self.screen.blit(text_surface, (box_x + padding, y_offset))
            y_offset += line_height
        
        # Draw choices
        if self.current_line.choices and self.complete:
            y_offset += 10
            for i, (choice_text, _) in enumerate(self.current_line.choices):
                is_selected = i == self.selected_choice
                prefix = "▸ " if is_selected else "  "
                choice_color = (255, 255, 100) if is_selected else (180, 180, 200)
                choice_color = tuple(int(c * self.fade_alpha) for c in choice_color)
                
                choice_surface = font_text.render(prefix + choice_text, True, choice_color)
                self.screen.blit(choice_surface, (box_x + padding + 20, y_offset))
                y_offset += 30
        
        # Draw input hint
        if self.waiting_for_input and not self.current_line.choices:
            hint_color = tuple(int(c * self.fade_alpha * 0.6) for c in style["text_color"])
            blink = int(pygame.time.get_ticks() / 500) % 2 == 0
            if blink:
                hint_text = font_hint.render("▼ Press SPACE or ENTER to continue", True, hint_color)
                hint_rect = hint_text.get_rect(center=(box_x + box_width // 2, box_y + box_height - 15))
                self.screen.blit(hint_text, hint_rect)
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]


class DialogueSystem:
    """Manages dialogue sequences and triggers."""
    
    def __init__(self, screen: pygame.Surface):
        self.textbox = TextBox(screen)
        self._sequences: Dict[str, DialogueSequence] = {}
        self._current_sequence: Optional[DialogueSequence] = None
        self._current_line_index = 0
        self._event_callbacks: Dict[str, Callable] = {}
        self._paused = False
    
    def register_sequence(self, sequence: DialogueSequence) -> None:
        """Register a dialogue sequence."""
        self._sequences[sequence.id] = sequence
    
    def register_event(self, event_id: str, callback: Callable) -> None:
        """Register an event callback."""
        self._event_callbacks[event_id] = callback
    
    def start_sequence(self, sequence_id: str) -> bool:
        """Start a dialogue sequence."""
        sequence = self._sequences.get(sequence_id)
        if not sequence or not sequence.lines:
            return False
        
        self._current_sequence = sequence
        self._current_line_index = 0
        self._paused = sequence.pause_game
        
        if sequence.on_start:
            self._fire_event(sequence.on_start)
        
        self._show_current_line()
        return True
    
    def stop(self) -> None:
        """Stop current dialogue."""
        if self._current_sequence and self._current_sequence.on_end:
            self._fire_event(self._current_sequence.on_end)
        
        self._current_sequence = None
        self.textbox.hide()
        self._paused = False
    
    def _show_current_line(self) -> None:
        """Show the current line in the sequence."""
        if not self._current_sequence:
            return
        
        if self._current_line_index >= len(self._current_sequence.lines):
            self.stop()
            return
        
        line = self._current_sequence.lines[self._current_line_index]
        self.textbox.show(
            line,
            on_complete=self._on_line_complete,
            on_choice=self._on_choice_selected
        )
    
    def _on_line_complete(self) -> None:
        """Called when a line is complete."""
        if not self._current_sequence:
            return
        
        line = self._current_sequence.lines[self._current_line_index]
        if line.on_complete:
            self._fire_event(line.on_complete)
        
        self._current_line_index += 1
        self._show_current_line()
    
    def _on_choice_selected(self, choice_id: str) -> None:
        """Called when a choice is selected."""
        self._fire_event(choice_id)
    
    def _fire_event(self, event_id: str) -> None:
        """Fire an event callback."""
        callback = self._event_callbacks.get(event_id)
        if callback:
            callback()
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """Handle input. Returns True if consumed."""
        if not self.textbox.active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                self.textbox.advance()
                return True
            elif event.key == pygame.K_UP:
                self.textbox.select_choice(-1)
                return True
            elif event.key == pygame.K_DOWN:
                self.textbox.select_choice(1)
                return True
            elif event.key == pygame.K_ESCAPE:
                if self._current_sequence and self._current_sequence.can_skip:
                    self.stop()
                    return True
        
        return False
    
    def update(self, dt: float) -> None:
        """Update dialogue system."""
        self.textbox.update(dt)
    
    def draw(self) -> None:
        """Draw dialogue."""
        self.textbox.draw()
    
    @property
    def is_active(self) -> bool:
        return self.textbox.active
    
    @property
    def should_pause_game(self) -> bool:
        return self._paused and self.textbox.active


# Pre-built dialogue for campaign intro
def create_campaign_dialogues() -> List[DialogueSequence]:
    """Create campaign story dialogues."""
    return [
        DialogueSequence(
            id="intro_1d",
            lines=[
                DialogueLine(
                    text="...",
                    style=TextBoxStyle.DIMENSION,
                    duration=1.5,
                ),
                DialogueLine(
                    text="You awaken.",
                    style=TextBoxStyle.NARRATOR,
                    duration=2.0,
                ),
                DialogueLine(
                    text="But something is... wrong. Limited. You can sense only a single direction.",
                    speaker="???",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="Left. Right. That is all that exists in your universe.",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="You are a being of ONE DIMENSION.",
                    speaker="The Voice",
                    style=TextBoxStyle.DIMENSION,
                ),
                DialogueLine(
                    text="Use A and D (or arrow keys) to move along the line. Press E near the portal when you're ready to ascend.",
                    style=TextBoxStyle.TUTORIAL,
                ),
            ],
            pause_game=True,
        ),
        DialogueSequence(
            id="intro_2d",
            lines=[
                DialogueLine(
                    text="The portal tears open reality itself...",
                    style=TextBoxStyle.NARRATOR,
                    duration=2.0,
                ),
                DialogueLine(
                    text="A new axis unfolds before you. Up. Down. The world expands!",
                    speaker="The Voice",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="Welcome to the SECOND DIMENSION.",
                    style=TextBoxStyle.DIMENSION,
                ),
                DialogueLine(
                    text="You are now a planar being. Move freely with WASD.",
                    style=TextBoxStyle.TUTORIAL,
                ),
            ],
            pause_game=True,
        ),
        DialogueSequence(
            id="intro_3d",
            lines=[
                DialogueLine(
                    text="Space itself bends around you...",
                    style=TextBoxStyle.NARRATOR,
                    duration=2.0,
                ),
                DialogueLine(
                    text="Depth. Volume. You can now perceive what flat beings could never imagine.",
                    speaker="The Voice",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="The THIRD DIMENSION. Home to most physical beings.",
                    style=TextBoxStyle.DIMENSION,
                ),
                DialogueLine(
                    text="Move with WASD. Look with the mouse. Space to rise, Ctrl to descend.",
                    style=TextBoxStyle.TUTORIAL,
                ),
            ],
            pause_game=True,
        ),
        DialogueSequence(
            id="intro_4d",
            lines=[
                DialogueLine(
                    text="Reality fractures. Time and space become one.",
                    style=TextBoxStyle.NARRATOR,
                    duration=2.5,
                ),
                DialogueLine(
                    text="You have transcended. The fourth axis - W - unfolds before your consciousness.",
                    speaker="The Voice",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="THE FOURTH DIMENSION. Few mortals ever perceive this realm.",
                    style=TextBoxStyle.DIMENSION,
                ),
                DialogueLine(
                    text="You begin as a 5-Cell - the simplest 4D form. Collect XP to evolve into more complex polytopes.",
                    speaker="The Voice",
                    style=TextBoxStyle.NARRATOR,
                ),
                DialogueLine(
                    text="Use Q and E to move along the W axis. Your form determines your power.",
                    style=TextBoxStyle.TUTORIAL,
                ),
            ],
            pause_game=True,
        ),
        DialogueSequence(
            id="evolution_unlocked",
            lines=[
                DialogueLine(
                    text="Your form is changing...",
                    style=TextBoxStyle.NARRATOR,
                    duration=1.5,
                ),
                DialogueLine(
                    text="You have accumulated enough dimensional energy to EVOLVE.",
                    speaker="The Voice",
                    style=TextBoxStyle.DIMENSION,
                ),
                DialogueLine(
                    text="Each polytope form grants unique abilities and enhanced perception of the fourth dimension.",
                    style=TextBoxStyle.NARRATOR,
                ),
            ],
            pause_game=True,
        ),
        # Chapter 1: First Point Introduction (warm, guiding tone)
        DialogueSequence(
            id="chapter_1_first_point_intro",
            lines=_create_first_point_dialogue_lines(),
            pause_game=True,
            can_skip=False,
        ),
    ]


def _create_first_point_dialogue_lines() -> List[DialogueLine]:
    """Create dialogue lines for the First Point introduction."""
    first_point_data = get_first_point_dialogue()
    lines = []
    
    for item in first_point_data:
        speaker = item.get("speaker", "")
        text = item.get("text", "")
        
        # Determine style based on speaker
        if speaker == "System":
            style = TextBoxStyle.TUTORIAL
        elif speaker == "The First Point":
            style = TextBoxStyle.DIMENSION
        else:
            style = TextBoxStyle.NARRATOR
        
        # Slower typing for atmospheric moments
        typing_speed = 25.0 if speaker == "" else 30.0
        
        # Auto-advance for "..." lines
        duration = 1.5 if text == "..." else 0.0
        
        lines.append(DialogueLine(
            speaker=speaker,
            text=text,
            style=style,
            typing_speed=typing_speed,
            duration=duration,
        ))
    
    return lines
