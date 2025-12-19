"""Typewriter voice synthesis system - Undertale-style character voice beeps.

Each character/NPC can have a unique "voice" defined by:
- Base pitch (frequency)
- Pitch variance (how much it varies per character)
- Speed (characters per second)
- Volume
- Waveform type (sine, square, saw, noise)

The system generates beeps procedurally, no audio files needed.
"""
from __future__ import annotations

import math
import random
import struct
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable

import pygame


class WaveformType(Enum):
    """Types of waveforms for voice synthesis."""
    SINE = "sine"           # Smooth, gentle (like Toriel)
    SQUARE = "square"       # Sharp, robotic (like Papyrus)
    SAW = "saw"             # Buzzy, energetic
    TRIANGLE = "triangle"   # Soft but present
    NOISE = "noise"         # Static-y, mysterious
    PULSE = "pulse"         # Variable duty cycle square


@dataclass
class VoiceProfile:
    """Defines a character's unique voice."""
    id: str
    name: str
    
    # Pitch settings (in Hz)
    base_pitch: float = 260.0       # Base frequency (middle C = 261.6)
    pitch_variance: float = 30.0    # Random variance per beep
    pitch_pattern: str = "random"   # "random", "rising", "falling", "sine"
    
    # Timing
    chars_per_second: float = 25.0  # Text speed
    beep_duration: float = 0.05     # How long each beep lasts
    beep_gap: float = 0.02          # Gap between beeps
    
    # Sound
    waveform: WaveformType = WaveformType.SINE
    volume: float = 0.3             # 0.0 to 1.0
    
    # Pulse wave specific
    pulse_duty: float = 0.5         # Duty cycle for pulse wave
    
    # Effects
    vibrato_speed: float = 0.0      # Vibrato oscillation speed
    vibrato_depth: float = 0.0      # Vibrato pitch range
    attack: float = 0.005           # Attack time (fade in)
    decay: float = 0.01             # Decay time (fade out)
    
    # Special
    skip_spaces: bool = True        # Don't beep on spaces
    skip_punctuation: bool = False  # Don't beep on punctuation
    punctuation_pause: float = 0.1  # Extra pause after punctuation


# =============================================================================
# PRESET VOICE PROFILES
# =============================================================================

VOICE_PRESETS: Dict[str, VoiceProfile] = {
    # DEFAULT VOICES
    "default": VoiceProfile(
        id="default",
        name="Default",
        base_pitch=260.0,
        waveform=WaveformType.SINE,
    ),
    
    "narrator": VoiceProfile(
        id="narrator",
        name="Narrator",
        base_pitch=200.0,
        pitch_variance=10.0,
        waveform=WaveformType.TRIANGLE,
        volume=0.25,
        chars_per_second=30.0,
    ),
    
    # 1D VOICES
    "first_point": VoiceProfile(
        id="first_point",
        name="The First Point",
        base_pitch=440.0,  # High, ethereal
        pitch_variance=100.0,
        pitch_pattern="sine",
        waveform=WaveformType.SINE,
        volume=0.2,
        vibrato_speed=5.0,
        vibrato_depth=20.0,
        chars_per_second=15.0,  # Slow, contemplative
    ),
    
    "line_walker": VoiceProfile(
        id="line_walker",
        name="Line Walker",
        base_pitch=300.0,
        pitch_variance=20.0,
        waveform=WaveformType.SQUARE,
        volume=0.25,
        chars_per_second=28.0,
    ),
    
    "segment_guardian": VoiceProfile(
        id="segment_guardian",
        name="Segment Guardian",
        base_pitch=180.0,  # Deep, authoritative
        pitch_variance=15.0,
        waveform=WaveformType.SAW,
        volume=0.35,
        chars_per_second=22.0,
    ),
    
    "void_echo": VoiceProfile(
        id="void_echo",
        name="Void Echo",
        base_pitch=150.0,
        pitch_variance=80.0,
        pitch_pattern="random",
        waveform=WaveformType.NOISE,
        volume=0.2,
        chars_per_second=18.0,
    ),
    
    # 2D VOICES
    "triangle_scout": VoiceProfile(
        id="triangle_scout",
        name="Triangle Scout",
        base_pitch=380.0,  # Higher, aggressive
        pitch_variance=40.0,
        waveform=WaveformType.SQUARE,
        volume=0.3,
        chars_per_second=35.0,  # Fast, energetic
    ),
    
    "square_citizen": VoiceProfile(
        id="square_citizen",
        name="Square Citizen",
        base_pitch=280.0,
        pitch_variance=15.0,
        waveform=WaveformType.SQUARE,
        volume=0.25,
        chars_per_second=25.0,
    ),
    
    "circle_mystic": VoiceProfile(
        id="circle_mystic",
        name="Circle Mystic",
        base_pitch=320.0,
        pitch_variance=50.0,
        pitch_pattern="sine",
        waveform=WaveformType.SINE,
        volume=0.25,
        vibrato_speed=3.0,
        vibrato_depth=15.0,
        chars_per_second=20.0,
    ),
    
    "high_priest_circle": VoiceProfile(
        id="high_priest_circle",
        name="High Priest Circle",
        base_pitch=250.0,
        pitch_variance=30.0,
        pitch_pattern="sine",
        waveform=WaveformType.SINE,
        volume=0.3,
        vibrato_speed=2.0,
        vibrato_depth=10.0,
        chars_per_second=18.0,
    ),
    
    # 3D VOICES
    "cube_guard": VoiceProfile(
        id="cube_guard",
        name="Cube Guard",
        base_pitch=200.0,
        pitch_variance=10.0,
        waveform=WaveformType.SQUARE,
        volume=0.35,
        chars_per_second=28.0,
    ),
    
    "sphere_wanderer": VoiceProfile(
        id="sphere_wanderer",
        name="Sphere Wanderer",
        base_pitch=340.0,
        pitch_variance=60.0,
        pitch_pattern="random",
        waveform=WaveformType.SINE,
        volume=0.25,
        chars_per_second=22.0,
    ),
    
    "crystal_guardian": VoiceProfile(
        id="crystal_guardian",
        name="Crystal Guardian",
        base_pitch=500.0,  # High, crystalline
        pitch_variance=100.0,
        waveform=WaveformType.TRIANGLE,
        volume=0.2,
        chars_per_second=24.0,
    ),
    
    # 4D VOICES
    "tesseract_guardian": VoiceProfile(
        id="tesseract_guardian",
        name="Tesseract Guardian",
        base_pitch=160.0,
        pitch_variance=120.0,
        pitch_pattern="random",
        waveform=WaveformType.SAW,
        volume=0.35,
        vibrato_speed=8.0,
        vibrato_depth=30.0,
        chars_per_second=20.0,
    ),
    
    "hypersphere_wanderer": VoiceProfile(
        id="hypersphere_wanderer",
        name="Hypersphere Wanderer",
        base_pitch=300.0,
        pitch_variance=80.0,
        pitch_pattern="sine",
        waveform=WaveformType.SINE,
        volume=0.25,
        vibrato_speed=4.0,
        vibrato_depth=40.0,
        chars_per_second=18.0,
    ),
    
    "threshold_guardian": VoiceProfile(
        id="threshold_guardian",
        name="Threshold Guardian",
        base_pitch=100.0,  # Very deep
        pitch_variance=150.0,
        pitch_pattern="random",
        waveform=WaveformType.NOISE,
        volume=0.3,
        chars_per_second=15.0,
    ),
    
    "the_transcended": VoiceProfile(
        id="the_transcended",
        name="The Transcended",
        base_pitch=400.0,
        pitch_variance=200.0,
        pitch_pattern="sine",
        waveform=WaveformType.SINE,
        volume=0.15,
        vibrato_speed=10.0,
        vibrato_depth=50.0,
        chars_per_second=12.0,  # Very slow, otherworldly
    ),
}


# =============================================================================
# VOICE SYNTHESIZER
# =============================================================================

class VoiceSynthesizer:
    """Generates voice beeps for typewriter text."""
    
    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate
        self._initialized = False
        self._beep_cache: Dict[str, pygame.mixer.Sound] = {}
        self._current_char_index = 0
        
    def init(self) -> None:
        """Initialize pygame mixer if needed."""
        if not self._initialized:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1)
            self._initialized = True
    
    def _generate_waveform(self, frequency: float, duration: float, 
                           waveform: WaveformType, profile: VoiceProfile) -> bytes:
        """Generate raw waveform samples."""
        num_samples = int(self.sample_rate * duration)
        samples = []
        
        for i in range(num_samples):
            t = i / self.sample_rate
            
            # Apply vibrato
            if profile.vibrato_speed > 0:
                vibrato = math.sin(2 * math.pi * profile.vibrato_speed * t) * profile.vibrato_depth
                freq = frequency + vibrato
            else:
                freq = frequency
            
            # Generate base waveform
            phase = 2 * math.pi * freq * t
            
            if waveform == WaveformType.SINE:
                sample = math.sin(phase)
            
            elif waveform == WaveformType.SQUARE:
                sample = 1.0 if math.sin(phase) > 0 else -1.0
            
            elif waveform == WaveformType.SAW:
                sample = 2.0 * (t * freq - math.floor(t * freq + 0.5))
            
            elif waveform == WaveformType.TRIANGLE:
                sample = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
            
            elif waveform == WaveformType.NOISE:
                sample = random.uniform(-1, 1) * math.sin(phase * 0.5)
            
            elif waveform == WaveformType.PULSE:
                phase_normalized = (phase % (2 * math.pi)) / (2 * math.pi)
                sample = 1.0 if phase_normalized < profile.pulse_duty else -1.0
            
            else:
                sample = math.sin(phase)
            
            # Apply envelope (attack/decay)
            envelope = 1.0
            attack_samples = int(profile.attack * self.sample_rate)
            decay_samples = int(profile.decay * self.sample_rate)
            
            if i < attack_samples:
                envelope = i / attack_samples
            elif i > num_samples - decay_samples:
                envelope = (num_samples - i) / decay_samples
            
            sample *= envelope * profile.volume
            
            # Convert to 16-bit integer
            sample_int = int(sample * 32767)
            sample_int = max(-32768, min(32767, sample_int))
            samples.append(sample_int)
        
        # Pack as bytes
        return struct.pack(f'{len(samples)}h', *samples)
    
    def generate_beep(self, profile: VoiceProfile, char_index: int = 0) -> pygame.mixer.Sound:
        """Generate a single beep for the given voice profile."""
        self.init()
        
        # Calculate pitch based on pattern
        if profile.pitch_pattern == "random":
            pitch = profile.base_pitch + random.uniform(-profile.pitch_variance, profile.pitch_variance)
        elif profile.pitch_pattern == "rising":
            pitch = profile.base_pitch + (char_index % 10) * (profile.pitch_variance / 5)
        elif profile.pitch_pattern == "falling":
            pitch = profile.base_pitch - (char_index % 10) * (profile.pitch_variance / 5)
        elif profile.pitch_pattern == "sine":
            pitch = profile.base_pitch + math.sin(char_index * 0.5) * profile.pitch_variance
        else:
            pitch = profile.base_pitch
        
        # Generate waveform
        samples = self._generate_waveform(
            frequency=pitch,
            duration=profile.beep_duration,
            waveform=profile.waveform,
            profile=profile
        )
        
        # Create Sound object
        sound = pygame.mixer.Sound(buffer=samples)
        return sound
    
    def get_cached_beep(self, profile: VoiceProfile, char_index: int) -> pygame.mixer.Sound:
        """Get a beep, using cache when possible for non-random patterns."""
        if profile.pitch_pattern == "random":
            # Always generate new for random
            return self.generate_beep(profile, char_index)
        
        # Cache key includes profile and char index for pattern-based voices
        cache_key = f"{profile.id}_{char_index % 20}"  # Cycle every 20 chars
        
        if cache_key not in self._beep_cache:
            self._beep_cache[cache_key] = self.generate_beep(profile, char_index)
        
        return self._beep_cache[cache_key]
    
    def clear_cache(self) -> None:
        """Clear the beep cache."""
        self._beep_cache.clear()


# =============================================================================
# TYPEWRITER TEXT SYSTEM
# =============================================================================

@dataclass
class TypewriterState:
    """State of a typewriter text animation."""
    full_text: str
    current_index: int = 0
    time_accumulator: float = 0.0
    finished: bool = False
    paused: bool = False
    
    # Current voice
    voice_profile: VoiceProfile = field(default_factory=lambda: VOICE_PRESETS["default"])
    
    # Settings
    speed_multiplier: float = 1.0
    skip_animation: bool = False
    
    @property
    def visible_text(self) -> str:
        """Get currently visible text."""
        return self.full_text[:self.current_index]
    
    @property
    def progress(self) -> float:
        """Get progress as 0.0 to 1.0."""
        if len(self.full_text) == 0:
            return 1.0
        return self.current_index / len(self.full_text)


class TypewriterTextSystem:
    """Manages typewriter text display with voice synthesis."""
    
    def __init__(self):
        self.synth = VoiceSynthesizer()
        self.current_state: Optional[TypewriterState] = None
        
        # Global settings
        self.master_volume: float = 1.0
        self.voice_enabled: bool = True
        self.default_speed: float = 1.0
        
        # Voice overrides per speaker
        self.voice_overrides: Dict[str, VoiceProfile] = {}
    
    def start_text(self, text: str, voice_id: str = "default", 
                   speed_multiplier: float = 1.0) -> TypewriterState:
        """Start a new typewriter text animation."""
        # Get voice profile
        if voice_id in self.voice_overrides:
            voice = self.voice_overrides[voice_id]
        elif voice_id in VOICE_PRESETS:
            voice = VOICE_PRESETS[voice_id]
        else:
            voice = VOICE_PRESETS["default"]
        
        self.current_state = TypewriterState(
            full_text=text,
            voice_profile=voice,
            speed_multiplier=speed_multiplier * self.default_speed,
        )
        
        return self.current_state
    
    def update(self, dt: float) -> Optional[str]:
        """Update typewriter animation. Returns visible text."""
        if not self.current_state or self.current_state.finished:
            return self.current_state.full_text if self.current_state else None
        
        if self.current_state.paused:
            return self.current_state.visible_text
        
        if self.current_state.skip_animation:
            self.current_state.current_index = len(self.current_state.full_text)
            self.current_state.finished = True
            return self.current_state.full_text
        
        state = self.current_state
        profile = state.voice_profile
        
        # Calculate time per character
        base_cps = profile.chars_per_second * state.speed_multiplier
        char_time = 1.0 / base_cps if base_cps > 0 else 0.05
        
        state.time_accumulator += dt
        
        # Advance characters
        while state.time_accumulator >= char_time and state.current_index < len(state.full_text):
            char = state.full_text[state.current_index]
            
            # Play beep (maybe)
            should_beep = True
            extra_pause = 0.0
            
            if char == ' ' and profile.skip_spaces:
                should_beep = False
            elif char in '.,!?;:' and profile.skip_punctuation:
                should_beep = False
                extra_pause = profile.punctuation_pause
            elif char in '.,!?':
                extra_pause = profile.punctuation_pause
            elif char == '\n':
                should_beep = False
                extra_pause = profile.punctuation_pause * 2
            
            if should_beep and self.voice_enabled:
                beep = self.synth.get_cached_beep(profile, state.current_index)
                beep.set_volume(profile.volume * self.master_volume)
                beep.play()
            
            state.current_index += 1
            state.time_accumulator -= char_time
            state.time_accumulator -= extra_pause
        
        # Check if finished
        if state.current_index >= len(state.full_text):
            state.finished = True
        
        return state.visible_text
    
    def skip(self) -> None:
        """Skip to end of current text."""
        if self.current_state:
            self.current_state.skip_animation = True
    
    def is_finished(self) -> bool:
        """Check if current text is finished."""
        return self.current_state is None or self.current_state.finished
    
    def set_voice(self, speaker_id: str, profile: VoiceProfile) -> None:
        """Set a custom voice profile for a speaker."""
        self.voice_overrides[speaker_id] = profile
    
    def set_master_volume(self, volume: float) -> None:
        """Set master volume (0.0 to 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def set_voice_enabled(self, enabled: bool) -> None:
        """Enable or disable voice beeps."""
        self.voice_enabled = enabled
    
    def set_default_speed(self, speed: float) -> None:
        """Set default text speed multiplier."""
        self.default_speed = max(0.1, min(5.0, speed))


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global typewriter instance
_typewriter: Optional[TypewriterTextSystem] = None


def get_typewriter() -> TypewriterTextSystem:
    """Get the global typewriter instance."""
    global _typewriter
    if _typewriter is None:
        _typewriter = TypewriterTextSystem()
    return _typewriter


def get_voice_profile(voice_id: str) -> Optional[VoiceProfile]:
    """Get a voice profile by ID."""
    return VOICE_PRESETS.get(voice_id)


def create_custom_voice(
    voice_id: str,
    name: str,
    base_pitch: float = 260.0,
    pitch_variance: float = 30.0,
    waveform: WaveformType = WaveformType.SINE,
    volume: float = 0.3,
    chars_per_second: float = 25.0,
    **kwargs
) -> VoiceProfile:
    """Create a custom voice profile."""
    return VoiceProfile(
        id=voice_id,
        name=name,
        base_pitch=base_pitch,
        pitch_variance=pitch_variance,
        waveform=waveform,
        volume=volume,
        chars_per_second=chars_per_second,
        **kwargs
    )


def register_voice(profile: VoiceProfile) -> None:
    """Register a custom voice profile globally."""
    VOICE_PRESETS[profile.id] = profile
