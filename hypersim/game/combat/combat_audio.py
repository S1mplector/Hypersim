"""Combat Audio System - Music and SFX for dimensional combat.

Handles:
- Battle music with looping
- Combat SFX (attacks, hits, menu sounds, etc.)
- Perception shift sounds
- Victory/defeat jingles
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Optional, Callable

import pygame


class CombatSFX(Enum):
    """Combat sound effect types."""
    # Menu sounds
    MENU_MOVE = auto()
    MENU_SELECT = auto()
    MENU_BACK = auto()
    
    # Combat actions
    ATTACK_CHARGE = auto()
    ATTACK_HIT = auto()
    ATTACK_MISS = auto()
    ATTACK_CRITICAL = auto()
    
    # Player sounds
    PLAYER_DAMAGE = auto()
    PLAYER_DODGE = auto()
    PLAYER_GRAZE = auto()
    PLAYER_HEAL = auto()
    
    # Enemy sounds
    ENEMY_ATTACK = auto()
    ENEMY_DAMAGE = auto()
    ENEMY_DEFEAT = auto()
    
    # Perception sounds
    PERCEPTION_SHIFT = auto()
    TRANSCENDENCE_ACTIVATE = auto()
    TRANSCENDENCE_END = auto()
    
    # Battle flow
    ENCOUNTER_START = auto()
    VICTORY = auto()
    DEFEAT = auto()
    SPARE = auto()
    FLEE = auto()
    
    # Dimensional
    DIMENSION_PULSE = auto()


@dataclass
class SFXConfig:
    """Configuration for a sound effect."""
    sfx_type: CombatSFX
    filename: str
    volume: float = 0.7
    pitch_variance: float = 0.0  # Random pitch variation


# Default SFX configurations (will use generated/placeholder sounds if files don't exist)
DEFAULT_COMBAT_SFX: Dict[CombatSFX, SFXConfig] = {
    CombatSFX.MENU_MOVE: SFXConfig(CombatSFX.MENU_MOVE, "menu_move.wav", 0.4),
    CombatSFX.MENU_SELECT: SFXConfig(CombatSFX.MENU_SELECT, "menu_select.wav", 0.5),
    CombatSFX.MENU_BACK: SFXConfig(CombatSFX.MENU_BACK, "menu_back.wav", 0.4),
    
    CombatSFX.ATTACK_CHARGE: SFXConfig(CombatSFX.ATTACK_CHARGE, "attack_charge.wav", 0.6),
    CombatSFX.ATTACK_HIT: SFXConfig(CombatSFX.ATTACK_HIT, "attack_hit.wav", 0.7),
    CombatSFX.ATTACK_MISS: SFXConfig(CombatSFX.ATTACK_MISS, "attack_miss.wav", 0.5),
    CombatSFX.ATTACK_CRITICAL: SFXConfig(CombatSFX.ATTACK_CRITICAL, "attack_crit.wav", 0.8),
    
    CombatSFX.PLAYER_DAMAGE: SFXConfig(CombatSFX.PLAYER_DAMAGE, "player_damage.wav", 0.8),
    CombatSFX.PLAYER_DODGE: SFXConfig(CombatSFX.PLAYER_DODGE, "dodge.wav", 0.5),
    CombatSFX.PLAYER_GRAZE: SFXConfig(CombatSFX.PLAYER_GRAZE, "graze.wav", 0.3, 0.1),
    CombatSFX.PLAYER_HEAL: SFXConfig(CombatSFX.PLAYER_HEAL, "heal.wav", 0.6),
    
    CombatSFX.ENEMY_ATTACK: SFXConfig(CombatSFX.ENEMY_ATTACK, "enemy_attack.wav", 0.6),
    CombatSFX.ENEMY_DAMAGE: SFXConfig(CombatSFX.ENEMY_DAMAGE, "enemy_damage.wav", 0.6),
    CombatSFX.ENEMY_DEFEAT: SFXConfig(CombatSFX.ENEMY_DEFEAT, "enemy_defeat.wav", 0.7),
    
    CombatSFX.PERCEPTION_SHIFT: SFXConfig(CombatSFX.PERCEPTION_SHIFT, "perception_shift.wav", 0.6),
    CombatSFX.TRANSCENDENCE_ACTIVATE: SFXConfig(CombatSFX.TRANSCENDENCE_ACTIVATE, "transcend.wav", 0.8),
    CombatSFX.TRANSCENDENCE_END: SFXConfig(CombatSFX.TRANSCENDENCE_END, "transcend_end.wav", 0.5),
    
    CombatSFX.ENCOUNTER_START: SFXConfig(CombatSFX.ENCOUNTER_START, "encounter.wav", 0.7),
    CombatSFX.VICTORY: SFXConfig(CombatSFX.VICTORY, "victory.wav", 0.8),
    CombatSFX.DEFEAT: SFXConfig(CombatSFX.DEFEAT, "defeat.wav", 0.8),
    CombatSFX.SPARE: SFXConfig(CombatSFX.SPARE, "spare.wav", 0.7),
    CombatSFX.FLEE: SFXConfig(CombatSFX.FLEE, "flee.wav", 0.6),
    
    CombatSFX.DIMENSION_PULSE: SFXConfig(CombatSFX.DIMENSION_PULSE, "dimension_pulse.wav", 0.4),
}


class CombatAudioManager:
    """Manages combat-specific audio."""
    
    def __init__(self):
        self._initialized = False
        self._sounds: Dict[CombatSFX, pygame.mixer.Sound] = {}
        self._music_playing = False
        self._current_music: Optional[str] = None
        
        # Volume settings
        self._master_volume = 1.0
        self._music_volume = 0.5
        self._sfx_volume = 0.7
        self._muted = False
        
        # Paths
        self._assets_path = Path(__file__).parent.parent / "assets"
        self._bgm_path = self._assets_path / "bgm"
        self._sfx_path = self._assets_path / "sounds" / "combat"
        
        # Battle music tracks
        self._battle_tracks = {
            "default": "battle_music_1.mp3",
            "boss": "battle_music_1.mp3",  # Can add boss music later
            "1d": "battle_music_1.mp3",
            "2d": "battle_music_1.mp3",
            "3d": "battle_music_1.mp3",
            "4d": "battle_music_1.mp3",
        }
        
        self._try_init()
    
    def _try_init(self) -> bool:
        """Initialize pygame mixer if not already done."""
        if self._initialized:
            return True
        
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._initialized = True
            self._load_sounds()
            return True
        except pygame.error as e:
            print(f"Combat audio init failed: {e}")
            return False
    
    def _load_sounds(self) -> None:
        """Load all combat sound effects."""
        if not self._sfx_path.exists():
            self._sfx_path.mkdir(parents=True, exist_ok=True)
        
        for sfx_type, config in DEFAULT_COMBAT_SFX.items():
            sound_path = self._sfx_path / config.filename
            if sound_path.exists():
                try:
                    sound = pygame.mixer.Sound(str(sound_path))
                    sound.set_volume(config.volume * self._sfx_volume * self._master_volume)
                    self._sounds[sfx_type] = sound
                except pygame.error:
                    pass  # Sound file couldn't be loaded
    
    def play_sfx(self, sfx_type: CombatSFX, volume_mult: float = 1.0) -> bool:
        """Play a combat sound effect."""
        if not self._initialized or self._muted:
            return False
        
        if sfx_type not in self._sounds:
            return False
        
        sound = self._sounds[sfx_type]
        config = DEFAULT_COMBAT_SFX.get(sfx_type)
        
        if config:
            vol = config.volume * self._sfx_volume * self._master_volume * volume_mult
            sound.set_volume(min(1.0, vol))
        
        sound.play()
        return True
    
    def start_battle_music(self, track_key: str = "default", fade_ms: int = 1000) -> bool:
        """Start playing battle music with optional fade-in."""
        if not self._initialized or self._muted:
            return False
        
        track_file = self._battle_tracks.get(track_key, self._battle_tracks["default"])
        music_path = self._bgm_path / track_file
        
        if not music_path.exists():
            print(f"Battle music not found: {music_path}")
            return False
        
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(self._music_volume * self._master_volume)
            pygame.mixer.music.play(loops=-1, fade_ms=fade_ms)
            self._music_playing = True
            self._current_music = track_key
            return True
        except pygame.error as e:
            print(f"Failed to play battle music: {e}")
            return False
    
    def stop_battle_music(self, fade_ms: int = 500) -> None:
        """Stop battle music with optional fade-out."""
        if not self._initialized:
            return
        
        if fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
        
        self._music_playing = False
        self._current_music = None
    
    def pause_music(self) -> None:
        """Pause battle music."""
        if self._initialized and self._music_playing:
            pygame.mixer.music.pause()
    
    def resume_music(self) -> None:
        """Resume paused battle music."""
        if self._initialized and self._music_playing:
            pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 - 1.0)."""
        self._music_volume = max(0.0, min(1.0, volume))
        if self._initialized:
            pygame.mixer.music.set_volume(self._music_volume * self._master_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume (0.0 - 1.0)."""
        self._sfx_volume = max(0.0, min(1.0, volume))
        self._update_sound_volumes()
    
    def set_master_volume(self, volume: float) -> None:
        """Set master volume (0.0 - 1.0)."""
        self._master_volume = max(0.0, min(1.0, volume))
        self._update_sound_volumes()
        if self._initialized:
            pygame.mixer.music.set_volume(self._music_volume * self._master_volume)
    
    def _update_sound_volumes(self) -> None:
        """Update all loaded sound volumes."""
        for sfx_type, sound in self._sounds.items():
            config = DEFAULT_COMBAT_SFX.get(sfx_type)
            if config:
                sound.set_volume(config.volume * self._sfx_volume * self._master_volume)
    
    def set_muted(self, muted: bool) -> None:
        """Mute or unmute all combat audio."""
        self._muted = muted
        if muted:
            self.pause_music()
        else:
            self.resume_music()
    
    @property
    def is_music_playing(self) -> bool:
        """Check if battle music is currently playing."""
        return self._music_playing and pygame.mixer.music.get_busy()
    
    # === Convenience methods for common combat events ===
    
    def on_menu_move(self) -> None:
        """Play menu navigation sound."""
        self.play_sfx(CombatSFX.MENU_MOVE)
    
    def on_menu_select(self) -> None:
        """Play menu selection sound."""
        self.play_sfx(CombatSFX.MENU_SELECT)
    
    def on_menu_back(self) -> None:
        """Play menu back sound."""
        self.play_sfx(CombatSFX.MENU_BACK)
    
    def on_player_attack(self, damage: int, is_critical: bool = False) -> None:
        """Play attack sound based on result."""
        if is_critical:
            self.play_sfx(CombatSFX.ATTACK_CRITICAL)
        elif damage > 0:
            self.play_sfx(CombatSFX.ATTACK_HIT)
        else:
            self.play_sfx(CombatSFX.ATTACK_MISS)
    
    def on_player_damage(self, damage: int) -> None:
        """Play player damage sound."""
        self.play_sfx(CombatSFX.PLAYER_DAMAGE)
    
    def on_graze(self) -> None:
        """Play graze sound (near miss)."""
        self.play_sfx(CombatSFX.PLAYER_GRAZE, volume_mult=0.5)
    
    def on_perception_shift(self) -> None:
        """Play perception shift sound."""
        self.play_sfx(CombatSFX.PERCEPTION_SHIFT)
    
    def on_transcendence(self, activate: bool = True) -> None:
        """Play transcendence sound."""
        if activate:
            self.play_sfx(CombatSFX.TRANSCENDENCE_ACTIVATE)
        else:
            self.play_sfx(CombatSFX.TRANSCENDENCE_END)
    
    def on_enemy_attack(self) -> None:
        """Play enemy attack sound."""
        self.play_sfx(CombatSFX.ENEMY_ATTACK)
    
    def on_enemy_damage(self, damage: int) -> None:
        """Play enemy damage sound."""
        self.play_sfx(CombatSFX.ENEMY_DAMAGE)
    
    def on_battle_start(self, dimension: str = "default") -> None:
        """Start battle with appropriate music."""
        self.play_sfx(CombatSFX.ENCOUNTER_START)
        self.start_battle_music(dimension)
    
    def on_battle_end(self, result: str) -> None:
        """Play battle end sound and stop music."""
        self.stop_battle_music(fade_ms=1000)
        
        if result == "victory":
            self.play_sfx(CombatSFX.VICTORY)
        elif result == "spare":
            self.play_sfx(CombatSFX.SPARE)
        elif result == "defeat":
            self.play_sfx(CombatSFX.DEFEAT)
        elif result == "flee":
            self.play_sfx(CombatSFX.FLEE)


# Singleton instance
_combat_audio: Optional[CombatAudioManager] = None


def get_combat_audio() -> CombatAudioManager:
    """Get or create the combat audio manager."""
    global _combat_audio
    if _combat_audio is None:
        _combat_audio = CombatAudioManager()
    return _combat_audio
