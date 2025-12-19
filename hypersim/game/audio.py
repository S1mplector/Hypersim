"""Audio system for sound effects and music."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


@dataclass
class SoundConfig:
    """Configuration for a sound effect."""
    id: str
    path: str
    volume: float = 1.0
    max_instances: int = 3  # Max concurrent plays


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
        else:
            self.sounds_path = Path(__file__).parent / "assets" / "sounds"
        
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
            print("Warning: Audio system could not be initialized")
            return False
    
    def register_sound(self, config: SoundConfig) -> bool:
        """Register a sound effect."""
        if not self._initialized:
            return False
        
        self._sound_configs[config.id] = config
        
        # Try to load the sound file
        sound_path = self.sounds_path / config.path
        if sound_path.exists():
            try:
                sound = pygame.mixer.Sound(str(sound_path))
                sound.set_volume(config.volume * self._sfx_volume)
                self._sounds[config.id] = sound
                self._playing_counts[config.id] = 0
                return True
            except pygame.error as e:
                print(f"Warning: Could not load sound '{config.id}': {e}")
        
        return False
    
    def register_defaults(self) -> None:
        """Register default game sounds (placeholders if files don't exist)."""
        defaults = [
            SoundConfig("pickup", "pickup.wav", volume=0.6),
            SoundConfig("damage", "damage.wav", volume=0.8),
            SoundConfig("death", "death.wav", volume=0.9),
            SoundConfig("portal", "portal.wav", volume=0.7),
            SoundConfig("ability", "ability.wav", volume=0.6),
            SoundConfig("dash", "dash.wav", volume=0.5),
            SoundConfig("enemy_attack", "enemy_attack.wav", volume=0.7),
            SoundConfig("dimension_shift", "dimension_shift.wav", volume=0.8),
            SoundConfig("menu_select", "menu_select.wav", volume=0.5),
            SoundConfig("menu_back", "menu_back.wav", volume=0.4),
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
        
        full_path = self.sounds_path / music_path
        if not full_path.exists():
            return False
        
        try:
            pygame.mixer.music.load(str(full_path))
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops)
            return True
        except pygame.error:
            return False
    
    def stop_music(self) -> None:
        """Stop background music."""
        if self._initialized:
            pygame.mixer.music.stop()
    
    def pause_music(self) -> None:
        """Pause background music."""
        if self._initialized:
            pygame.mixer.music.pause()
    
    def unpause_music(self) -> None:
        """Unpause background music."""
        if self._initialized:
            pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self._music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set sound effects volume (0.0 to 1.0)."""
        self._sfx_volume = max(0.0, min(1.0, volume))
        
        # Update all loaded sounds
        for sound_id, sound in self._sounds.items():
            config = self._sound_configs.get(sound_id)
            if config:
                sound.set_volume(config.volume * self._sfx_volume)
    
    def set_muted(self, muted: bool) -> None:
        """Mute or unmute all audio."""
        self._muted = muted
        if muted:
            self.stop_all()
            self.pause_music()
        else:
            self.unpause_music()
    
    def toggle_mute(self) -> bool:
        """Toggle mute state. Returns new mute state."""
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
        
        def on_dimension_change(event):
            self.audio.play("dimension_shift")
        
        def on_enemy_attack(event):
            self.audio.play("enemy_attack", volume_override=0.5)
        
        self.world.on_event("pickup_collected", on_pickup)
        self.world.on_event("damage_taken", on_damage)
        self.world.on_event("entity_died", on_death)
        self.world.on_event("portal_entered", on_portal)
        self.world.on_event("ability_used", on_ability)
        self.world.on_event("dimension_changed", on_dimension_change)
        self.world.on_event("enemy_attack", on_enemy_attack)


# Global audio system instance
_audio_system: Optional[AudioSystem] = None


def get_audio_system() -> AudioSystem:
    """Get or create the global audio system."""
    global _audio_system
    if _audio_system is None:
        _audio_system = AudioSystem()
        _audio_system.register_defaults()
    return _audio_system
