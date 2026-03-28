"""Audio subsystem - sound effects, music, and voice synthesis.

This package contains:
- Core audio system (AudioSystem, GameAudioHandler)
- voice_synth.py: Undertale-style typewriter voice beeps
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

import pygame
import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World

# Voice synthesis
from .voice_synth import (
    VoiceSynthesizer,
    VoiceProfile,
    WaveformType,
    TypewriterTextSystem,
    TypewriterState,
    VOICE_PRESETS,
    get_typewriter,
    get_voice_profile,
    create_custom_voice,
    register_voice,
)


# =============================================================================
# CORE AUDIO SYSTEM (moved from audio.py)
# =============================================================================

@dataclass
class SoundConfig:
    """Configuration for a sound effect."""
    id: str
    path: str
    volume: float = 1.0
    max_instances: int = 3


class AudioSystem:
    """Manages sound effects and background music."""
    
    def __init__(self, sounds_path: Optional[Path] = None):
        self._initialized = False
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._sound_configs: Dict[str, SoundConfig] = {}
        self._playing_counts: Dict[str, int] = {}
        self._music_volume = 0.5
        self._sfx_volume = 0.7
        self._muted = False
        
        if sounds_path:
            self.sounds_path = Path(sounds_path)
            self.assets_path = self.sounds_path.parent
        else:
            self.assets_path = Path(__file__).parent.parent / "assets"
            self.sounds_path = self.assets_path / "sounds"
        self.bgm_path = self.assets_path / "bgm"
        
        self._try_init()
    
    def _try_init(self) -> bool:
        """Try to initialize pygame mixer."""
        if self._initialized:
            return True
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
            return True
        except pygame.error:
            return False
    
    def register_sound(self, config: SoundConfig) -> bool:
        """Register a sound effect."""
        if not self._initialized:
            return False
        self._sound_configs[config.id] = config
        sound_path = self.sounds_path / config.path
        if sound_path.exists():
            try:
                sound = pygame.mixer.Sound(str(sound_path))
                sound.set_volume(config.volume * self._sfx_volume)
                self._sounds[config.id] = sound
                self._playing_counts[config.id] = 0
                return True
            except pygame.error:
                pass
        fallback = self._build_procedural_sound(config.id)
        if fallback is not None:
            fallback.set_volume(config.volume * self._sfx_volume)
            self._sounds[config.id] = fallback
            self._playing_counts[config.id] = 0
            return True
        return False

    def _build_procedural_sound(self, sound_id: str) -> Optional[pygame.mixer.Sound]:
        """Generate a small synthetic fallback for key gameplay sounds."""
        if not self._initialized:
            return None

        sample_rate = 44100
        if sound_id == "line_strain":
            duration = 0.62
            t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False, dtype=np.float32)
            sweep = np.linspace(190.0, 76.0, t.size, dtype=np.float32)
            phase = np.cumsum((2.0 * np.pi * sweep) / sample_rate)
            body = np.sin(phase) * 0.42
            rasp = np.sign(np.sin(2.0 * np.pi * 34.0 * t + 0.7 * np.sin(2.0 * np.pi * 2.7 * t))) * 0.08
            whine = np.sin(2.0 * np.pi * (320.0 + 24.0 * np.sin(2.0 * np.pi * 5.0 * t)) * t) * 0.06
            envelope = np.minimum(1.0, t / 0.03) * np.exp(-t * 2.35)
            signal = (body + rasp + whine) * envelope
        elif sound_id == "guardian_judgment":
            duration = 1.35
            t = np.linspace(0.0, duration, int(sample_rate * duration), endpoint=False, dtype=np.float32)
            sweep = np.linspace(158.0, 44.0, t.size, dtype=np.float32)
            phase = np.cumsum((2.0 * np.pi * sweep) / sample_rate)
            body = np.sin(phase) * 0.34 + np.sin(phase * 0.51) * 0.18
            lattice = np.sign(np.sin(2.0 * np.pi * 22.0 * t)) * 0.08
            shear = np.sin(2.0 * np.pi * (520.0 - 180.0 * (t / duration)) * t) * 0.05
            envelope = np.minimum(1.0, t / 0.05) * np.exp(-t * 1.05)
            signal = (body + lattice + shear) * envelope
        else:
            return None

        stereo = np.column_stack((signal, signal * 0.96))
        pcm = np.clip(stereo * 32767, -32767, 32767).astype(np.int16)
        try:
            return pygame.sndarray.make_sound(pcm)
        except pygame.error:
            return None
    
    def register_defaults(self) -> None:
        """Register default game sounds."""
        defaults = [
            SoundConfig("pickup", "pickup.wav", volume=0.6),
            SoundConfig("damage", "damage.wav", volume=0.8),
            SoundConfig("death", "death.wav", volume=0.9),
            SoundConfig("portal", "portal.wav", volume=0.7),
            SoundConfig("ability", "ability.wav", volume=0.6),
            SoundConfig("dash", "dash.wav", volume=0.5),
            SoundConfig("encounter", "encounter.wav", volume=0.7),
            SoundConfig("victory", "victory.wav", volume=0.8),
            SoundConfig("spare", "spare.wav", volume=0.7),
            SoundConfig("boss_defeated", "boss_defeated.wav", volume=0.9),
            SoundConfig("line_strain", "line_strain.wav", volume=0.72, max_instances=12),
            SoundConfig("guardian_judgment", "guardian_judgment.wav", volume=0.9, max_instances=3),
        ]
        for config in defaults:
            self.register_sound(config)
    
    def play(self, sound_id: str, volume_override: Optional[float] = None) -> bool:
        """Play a sound effect."""
        if not self._initialized or self._muted:
            return False
        if sound_id not in self._sounds:
            return False
        config = self._sound_configs.get(sound_id)
        if config and self._playing_counts.get(sound_id, 0) >= config.max_instances:
            return False
        sound = self._sounds[sound_id]
        if volume_override is not None:
            sound.set_volume(volume_override * self._sfx_volume)
        sound.play()
        if config:
            self._playing_counts[sound_id] = self._playing_counts.get(sound_id, 0) + 1
        return True
    
    def stop(self, sound_id: str) -> None:
        """Stop a sound effect."""
        if sound_id in self._sounds:
            self._sounds[sound_id].stop()
            self._playing_counts[sound_id] = 0
    
    def stop_all(self) -> None:
        """Stop all sound effects."""
        if self._initialized:
            pygame.mixer.stop()
            for sound_id in self._playing_counts:
                self._playing_counts[sound_id] = 0
    
    def play_music(self, music_path: str, loops: int = -1) -> bool:
        """Play background music."""
        if not self._initialized or self._muted:
            return False
        full_path = self._resolve_music_path(music_path)
        if full_path is None:
            return False
        try:
            pygame.mixer.music.load(str(full_path))
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops)
            return True
        except pygame.error:
            return False

    def _resolve_music_path(self, music_path: str) -> Optional[Path]:
        """Resolve a music file against known asset roots."""
        candidate = Path(music_path)
        if candidate.is_absolute():
            return candidate if candidate.exists() else None

        search_roots = [
            self.sounds_path,
            self.bgm_path,
            self.assets_path,
        ]
        for root in search_roots:
            full_path = root / candidate
            if full_path.exists():
                return full_path

        return None
    
    def stop_music(self) -> None:
        if self._initialized:
            pygame.mixer.music.stop()
    
    def pause_music(self) -> None:
        if self._initialized:
            pygame.mixer.music.pause()
    
    def unpause_music(self) -> None:
        if self._initialized:
            pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float) -> None:
        self._music_volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self._music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        self._sfx_volume = max(0.0, min(1.0, volume))
        for sound_id, sound in self._sounds.items():
            config = self._sound_configs.get(sound_id)
            if config:
                sound.set_volume(config.volume * self._sfx_volume)
    
    def set_muted(self, muted: bool) -> None:
        self._muted = muted
        if muted:
            self.stop_all()
            self.pause_music()
        else:
            self.unpause_music()
    
    def toggle_mute(self) -> bool:
        self.set_muted(not self._muted)
        return self._muted
    
    @property
    def is_muted(self) -> bool:
        return self._muted


class GameAudioHandler:
    """Connects game events to audio playback."""
    
    def __init__(self, audio: AudioSystem, world: "World"):
        self.audio = audio
        self.world = world
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Wire up game events to sounds."""
        def on_pickup(event):
            self.audio.play("pickup")
        def on_damage(event):
            self.audio.play("damage")
        def on_death(event):
            entity_id = event.data.get("entity_id")
            entity = self.world.get(entity_id) if entity_id else None
            if entity and entity.has_tag("player"):
                self.audio.play("death")
        def on_portal(event):
            self.audio.play("portal")
        def on_ability(event):
            ability_id = event.data.get("ability_id", "")
            if ability_id == "dash":
                self.audio.play("dash")
            else:
                self.audio.play("ability")
        
        self.world.on_event("pickup_collected", on_pickup)
        self.world.on_event("damage_taken", on_damage)
        self.world.on_event("entity_died", on_death)
        self.world.on_event("portal_entered", on_portal)
        self.world.on_event("ability_used", on_ability)


# Global audio system instance
_audio_system: Optional[AudioSystem] = None


def get_audio_system() -> AudioSystem:
    """Get or create the global audio system."""
    global _audio_system
    if _audio_system is None:
        _audio_system = AudioSystem()
        _audio_system.register_defaults()
    return _audio_system


__all__ = [
    # Core audio
    "AudioSystem",
    "GameAudioHandler",
    "SoundConfig",
    "get_audio_system",
    # Voice synthesis
    "VoiceSynthesizer",
    "VoiceProfile", 
    "WaveformType",
    "TypewriterTextSystem",
    "TypewriterState",
    "VOICE_PRESETS",
    "get_typewriter",
    "get_voice_profile",
    "create_custom_voice",
    "register_voice",
]
