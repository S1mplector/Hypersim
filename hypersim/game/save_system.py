"""Comprehensive save/load system for Tessera campaign.

Features:
- Multiple save slots (manual saves)
- Auto-save functionality
- Save state snapshots (quick save/load)
- Cloud-ready serialization
- Save file validation and versioning
"""
from __future__ import annotations

import json
import gzip
import hashlib
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import base64


# =============================================================================
# SAVE DATA STRUCTURES
# =============================================================================

SAVE_VERSION = "1.0.0"
SAVE_MAGIC = "TESSERA_SAVE"


class SaveType(Enum):
    """Types of saves."""
    MANUAL = "manual"       # Player-initiated save
    AUTO = "auto"           # Automatic checkpoint
    QUICKSAVE = "quicksave" # Quick save slot
    CLOUD = "cloud"         # Cloud sync save


@dataclass
class PlayerState:
    """Player-specific save data."""
    # Position
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])
    dimension: str = "1d"
    
    # Stats
    health: float = 100.0
    max_health: float = 100.0
    
    # Progression
    level: int = 1
    xp: int = 0
    
    # Evolution (per dimension)
    evolution_1d: str = "point_awakened"
    evolution_2d: str = "newborn_flat"
    evolution_3d: str = "newborn_solid"
    evolution_4d: str = "pentachoron"
    
    evolution_xp_1d: int = 0
    evolution_xp_2d: int = 0
    evolution_xp_3d: int = 0
    evolution_xp_4d: int = 0
    
    # Unlocked forms per dimension
    unlocked_forms_1d: List[str] = field(default_factory=lambda: ["point_awakened"])
    unlocked_forms_2d: List[str] = field(default_factory=lambda: ["newborn_flat"])
    unlocked_forms_3d: List[str] = field(default_factory=lambda: ["newborn_solid"])
    unlocked_forms_4d: List[str] = field(default_factory=lambda: ["pentachoron"])
    
    # Abilities
    unlocked_abilities: List[str] = field(default_factory=list)
    equipped_abilities: List[str] = field(default_factory=list)
    ability_cooldowns: Dict[str, float] = field(default_factory=dict)
    
    # Inventory
    inventory: Dict[str, int] = field(default_factory=dict)


@dataclass
class WorldState:
    """World/level state data."""
    # Current location
    current_world: str = "tutorial_1d"
    current_chapter: int = 1
    current_mission: str = ""
    
    # Completed content
    completed_worlds: List[str] = field(default_factory=list)
    completed_missions: List[str] = field(default_factory=list)
    completed_objectives: List[str] = field(default_factory=list)
    
    # Unlocked content
    unlocked_dimensions: List[str] = field(default_factory=lambda: ["1d"])
    unlocked_worlds: List[str] = field(default_factory=lambda: ["tutorial_1d"])
    unlocked_portals: List[str] = field(default_factory=list)
    
    # World-specific state (entities, pickups collected, etc.)
    world_states: Dict[str, Dict] = field(default_factory=dict)
    
    # NPCs
    npc_states: Dict[str, Dict] = field(default_factory=dict)
    npc_relationships: Dict[str, int] = field(default_factory=dict)


@dataclass
class StoryState:
    """Story/narrative state data."""
    # Campaign progress
    story_chapter: int = 1
    story_beat: int = 0
    
    # Dialogue
    seen_dialogues: List[str] = field(default_factory=list)
    dialogue_choices: Dict[str, str] = field(default_factory=dict)
    
    # Lore
    discovered_lore: List[str] = field(default_factory=list)
    codex_entries: List[str] = field(default_factory=list)
    
    # Flags
    story_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Achievements
    achievements: List[str] = field(default_factory=list)


@dataclass
class SettingsState:
    """Player settings (saved with game)."""
    master_volume: float = 0.8
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    
    mouse_sensitivity: float = 1.0
    invert_y: bool = False
    
    show_tutorials: bool = True
    show_hints: bool = True
    
    difficulty: str = "normal"


@dataclass
class SaveMetadata:
    """Metadata about a save file."""
    save_id: str = ""
    save_type: str = "manual"
    save_name: str = "Unnamed Save"
    
    # Timestamps
    created_at: float = 0.0
    updated_at: float = 0.0
    playtime_seconds: int = 0
    
    # Quick info for display
    player_level: int = 1
    current_dimension: str = "1d"
    current_chapter: int = 1
    completion_percent: float = 0.0
    
    # Technical
    save_version: str = SAVE_VERSION
    checksum: str = ""


@dataclass
class GameSaveData:
    """Complete save data structure."""
    metadata: SaveMetadata = field(default_factory=SaveMetadata)
    player: PlayerState = field(default_factory=PlayerState)
    world: WorldState = field(default_factory=WorldState)
    story: StoryState = field(default_factory=StoryState)
    settings: SettingsState = field(default_factory=SettingsState)
    
    # Additional custom data
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "magic": SAVE_MAGIC,
            "version": SAVE_VERSION,
            "metadata": asdict(self.metadata),
            "player": asdict(self.player),
            "world": asdict(self.world),
            "story": asdict(self.story),
            "settings": asdict(self.settings),
            "custom_data": self.custom_data,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "GameSaveData":
        """Create from dictionary."""
        return cls(
            metadata=SaveMetadata(**data.get("metadata", {})),
            player=PlayerState(**data.get("player", {})),
            world=WorldState(**data.get("world", {})),
            story=StoryState(**data.get("story", {})),
            settings=SettingsState(**data.get("settings", {})),
            custom_data=data.get("custom_data", {}),
        )
    
    def update_metadata(self) -> None:
        """Update metadata from current state."""
        self.metadata.updated_at = time.time()
        self.metadata.player_level = self.player.level
        self.metadata.current_dimension = self.player.dimension
        self.metadata.current_chapter = self.world.current_chapter
        self.metadata.save_version = SAVE_VERSION
        
        # Calculate completion
        total_missions = 35  # From campaign
        completed = len(self.world.completed_missions)
        self.metadata.completion_percent = (completed / total_missions) * 100


# =============================================================================
# SAVE SLOT SYSTEM
# =============================================================================

@dataclass
class SaveSlot:
    """A save slot that can hold save data."""
    slot_id: int
    slot_type: SaveType
    is_empty: bool = True
    metadata: Optional[SaveMetadata] = None
    file_path: Optional[Path] = None
    
    @property
    def display_name(self) -> str:
        if self.is_empty:
            return f"Slot {self.slot_id} - Empty"
        if self.metadata:
            return f"Slot {self.slot_id} - {self.metadata.save_name}"
        return f"Slot {self.slot_id}"
    
    @property
    def last_played(self) -> str:
        if self.is_empty or not self.metadata:
            return "Never"
        dt = datetime.fromtimestamp(self.metadata.updated_at)
        return dt.strftime("%Y-%m-%d %H:%M")
    
    @property
    def playtime_display(self) -> str:
        if self.is_empty or not self.metadata:
            return "0:00"
        seconds = self.metadata.playtime_seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}:{minutes:02d}"


class SaveManager:
    """Manages all save operations."""
    
    MAX_MANUAL_SLOTS = 10
    MAX_AUTO_SLOTS = 3
    
    def __init__(self, save_dir: Optional[Path] = None):
        self.save_dir = save_dir or Path("~/.tessera/saves").expanduser()
        self.save_dir.mkdir(parents=True, exist_ok=True)
        
        # Slot directories
        self.manual_dir = self.save_dir / "manual"
        self.auto_dir = self.save_dir / "auto"
        self.quicksave_dir = self.save_dir / "quicksave"
        
        for d in [self.manual_dir, self.auto_dir, self.quicksave_dir]:
            d.mkdir(exist_ok=True)
        
        # Current game state (for quick operations)
        self._current_save: Optional[GameSaveData] = None
        self._current_slot: Optional[SaveSlot] = None
        self._session_start: float = time.time()
        
        # Auto-save settings
        self.auto_save_enabled = True
        self.auto_save_interval = 300.0  # 5 minutes
        self._last_auto_save: float = 0.0
    
    # =========================================================================
    # SLOT MANAGEMENT
    # =========================================================================
    
    def get_manual_slots(self) -> List[SaveSlot]:
        """Get all manual save slots."""
        slots = []
        for i in range(1, self.MAX_MANUAL_SLOTS + 1):
            slot = self._load_slot_info(i, SaveType.MANUAL)
            slots.append(slot)
        return slots
    
    def get_auto_slots(self) -> List[SaveSlot]:
        """Get all auto-save slots."""
        slots = []
        for i in range(1, self.MAX_AUTO_SLOTS + 1):
            slot = self._load_slot_info(i, SaveType.AUTO)
            slots.append(slot)
        return slots
    
    def get_quicksave_slot(self) -> SaveSlot:
        """Get the quicksave slot."""
        return self._load_slot_info(1, SaveType.QUICKSAVE)
    
    def _load_slot_info(self, slot_id: int, slot_type: SaveType) -> SaveSlot:
        """Load slot metadata without full save data."""
        file_path = self._get_slot_path(slot_id, slot_type)
        
        slot = SaveSlot(
            slot_id=slot_id,
            slot_type=slot_type,
            file_path=file_path,
        )
        
        if file_path.exists():
            try:
                metadata = self._load_metadata_only(file_path)
                if metadata:
                    slot.is_empty = False
                    slot.metadata = metadata
            except Exception:
                pass
        
        return slot
    
    def _get_slot_path(self, slot_id: int, slot_type: SaveType) -> Path:
        """Get file path for a slot."""
        if slot_type == SaveType.MANUAL:
            return self.manual_dir / f"save_{slot_id}.tsr"
        elif slot_type == SaveType.AUTO:
            return self.auto_dir / f"auto_{slot_id}.tsr"
        elif slot_type == SaveType.QUICKSAVE:
            return self.quicksave_dir / "quicksave.tsr"
        else:
            return self.save_dir / f"save_{slot_id}.tsr"
    
    # =========================================================================
    # SAVE OPERATIONS
    # =========================================================================
    
    def save_to_slot(
        self,
        save_data: GameSaveData,
        slot_id: int,
        slot_type: SaveType = SaveType.MANUAL,
        save_name: str = "",
    ) -> bool:
        """Save game to a specific slot."""
        # Update metadata
        save_data.metadata.save_id = f"{slot_type.value}_{slot_id}"
        save_data.metadata.save_type = slot_type.value
        save_data.metadata.save_name = save_name or f"Save {slot_id}"
        save_data.metadata.updated_at = time.time()
        if save_data.metadata.created_at == 0:
            save_data.metadata.created_at = time.time()
        
        # Update playtime
        if self._current_save:
            elapsed = time.time() - self._session_start
            save_data.metadata.playtime_seconds += int(elapsed)
            self._session_start = time.time()
        
        save_data.update_metadata()
        
        # Serialize and save
        file_path = self._get_slot_path(slot_id, slot_type)
        return self._write_save_file(file_path, save_data)
    
    def load_from_slot(self, slot_id: int, slot_type: SaveType = SaveType.MANUAL) -> Optional[GameSaveData]:
        """Load game from a specific slot."""
        file_path = self._get_slot_path(slot_id, slot_type)
        
        if not file_path.exists():
            return None
        
        save_data = self._read_save_file(file_path)
        if save_data:
            self._current_save = save_data
            self._current_slot = self._load_slot_info(slot_id, slot_type)
            self._session_start = time.time()
        
        return save_data
    
    def delete_slot(self, slot_id: int, slot_type: SaveType = SaveType.MANUAL) -> bool:
        """Delete a save slot."""
        file_path = self._get_slot_path(slot_id, slot_type)
        
        if file_path.exists():
            try:
                # Create backup first
                backup_path = file_path.with_suffix(".tsr.bak")
                shutil.copy2(file_path, backup_path)
                file_path.unlink()
                return True
            except Exception:
                return False
        
        return False
    
    def copy_slot(
        self,
        from_slot: int,
        from_type: SaveType,
        to_slot: int,
        to_type: SaveType,
    ) -> bool:
        """Copy save from one slot to another."""
        save_data = self.load_from_slot(from_slot, from_type)
        if save_data:
            return self.save_to_slot(save_data, to_slot, to_type)
        return False
    
    # =========================================================================
    # QUICK SAVE / LOAD
    # =========================================================================
    
    def quicksave(self, save_data: GameSaveData) -> bool:
        """Quick save to dedicated slot."""
        return self.save_to_slot(save_data, 1, SaveType.QUICKSAVE, "Quick Save")
    
    def quickload(self) -> Optional[GameSaveData]:
        """Quick load from dedicated slot."""
        return self.load_from_slot(1, SaveType.QUICKSAVE)
    
    # =========================================================================
    # AUTO-SAVE
    # =========================================================================
    
    def auto_save(self, save_data: GameSaveData, force: bool = False) -> bool:
        """Auto-save if interval has passed."""
        if not self.auto_save_enabled and not force:
            return False
        
        now = time.time()
        if not force and (now - self._last_auto_save) < self.auto_save_interval:
            return False
        
        # Rotate auto-saves (keep last 3)
        self._rotate_auto_saves()
        
        success = self.save_to_slot(save_data, 1, SaveType.AUTO, "Auto Save")
        if success:
            self._last_auto_save = now
        
        return success
    
    def _rotate_auto_saves(self) -> None:
        """Rotate auto-save slots (1 <- 2 <- 3, new -> 1)."""
        for i in range(self.MAX_AUTO_SLOTS, 1, -1):
            old_path = self._get_slot_path(i - 1, SaveType.AUTO)
            new_path = self._get_slot_path(i, SaveType.AUTO)
            
            if old_path.exists():
                try:
                    shutil.move(str(old_path), str(new_path))
                except Exception:
                    pass
    
    def check_auto_save(self, save_data: GameSaveData) -> bool:
        """Check if auto-save should trigger. Call from game loop."""
        return self.auto_save(save_data, force=False)
    
    # =========================================================================
    # FILE I/O
    # =========================================================================
    
    def _write_save_file(self, path: Path, save_data: GameSaveData) -> bool:
        """Write save data to file with compression and checksum."""
        try:
            # Convert to JSON
            data_dict = save_data.to_dict()
            json_str = json.dumps(data_dict, separators=(',', ':'))
            
            # Calculate checksum
            checksum = hashlib.sha256(json_str.encode()).hexdigest()[:16]
            data_dict["metadata"]["checksum"] = checksum
            json_str = json.dumps(data_dict, separators=(',', ':'))
            
            # Compress
            compressed = gzip.compress(json_str.encode())
            
            # Write with temp file for safety
            temp_path = path.with_suffix(".tmp")
            temp_path.write_bytes(compressed)
            
            # Atomic rename
            temp_path.rename(path)
            
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False
    
    def _read_save_file(self, path: Path) -> Optional[GameSaveData]:
        """Read and validate save file."""
        try:
            # Read and decompress
            compressed = path.read_bytes()
            json_str = gzip.decompress(compressed).decode()
            
            # Parse JSON
            data_dict = json.loads(json_str)
            
            # Validate magic
            if data_dict.get("magic") != SAVE_MAGIC:
                print("Invalid save file magic")
                return None
            
            # Validate checksum
            stored_checksum = data_dict.get("metadata", {}).get("checksum", "")
            data_dict["metadata"]["checksum"] = ""
            verify_str = json.dumps(data_dict, separators=(',', ':'))
            calculated_checksum = hashlib.sha256(verify_str.encode()).hexdigest()[:16]
            
            if stored_checksum and stored_checksum != calculated_checksum:
                print("Save file checksum mismatch - file may be corrupted")
                # Continue anyway for now
            
            # Create save data
            return GameSaveData.from_dict(data_dict)
            
        except Exception as e:
            print(f"Load error: {e}")
            return None
    
    def _load_metadata_only(self, path: Path) -> Optional[SaveMetadata]:
        """Load only metadata from save file (faster)."""
        try:
            compressed = path.read_bytes()
            json_str = gzip.decompress(compressed).decode()
            data_dict = json.loads(json_str)
            
            if data_dict.get("magic") != SAVE_MAGIC:
                return None
            
            return SaveMetadata(**data_dict.get("metadata", {}))
        except Exception:
            return None
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_newest_save(self) -> Optional[Tuple[SaveSlot, GameSaveData]]:
        """Get the most recent save across all slots."""
        newest_slot = None
        newest_time = 0.0
        
        for slot in self.get_manual_slots() + self.get_auto_slots():
            if not slot.is_empty and slot.metadata:
                if slot.metadata.updated_at > newest_time:
                    newest_time = slot.metadata.updated_at
                    newest_slot = slot
        
        # Check quicksave
        qs = self.get_quicksave_slot()
        if not qs.is_empty and qs.metadata:
            if qs.metadata.updated_at > newest_time:
                newest_slot = qs
        
        if newest_slot:
            save_data = self.load_from_slot(newest_slot.slot_id, newest_slot.slot_type)
            if save_data:
                return (newest_slot, save_data)
        
        return None
    
    def has_any_saves(self) -> bool:
        """Check if any saves exist."""
        for slot in self.get_manual_slots():
            if not slot.is_empty:
                return True
        for slot in self.get_auto_slots():
            if not slot.is_empty:
                return True
        if not self.get_quicksave_slot().is_empty:
            return True
        return False
    
    def export_save(self, slot_id: int, slot_type: SaveType, export_path: Path) -> bool:
        """Export save to a portable format."""
        save_data = self.load_from_slot(slot_id, slot_type)
        if not save_data:
            return False
        
        try:
            # Write as readable JSON for export
            data_dict = save_data.to_dict()
            export_path.write_text(json.dumps(data_dict, indent=2))
            return True
        except Exception:
            return False
    
    def import_save(self, import_path: Path, slot_id: int, slot_type: SaveType = SaveType.MANUAL) -> bool:
        """Import save from exported file."""
        try:
            data_dict = json.loads(import_path.read_text())
            
            if data_dict.get("magic") != SAVE_MAGIC:
                return False
            
            save_data = GameSaveData.from_dict(data_dict)
            return self.save_to_slot(save_data, slot_id, slot_type)
        except Exception:
            return False
    
    def create_new_game(self) -> GameSaveData:
        """Create fresh save data for a new game."""
        save_data = GameSaveData()
        save_data.metadata.created_at = time.time()
        save_data.metadata.updated_at = time.time()
        return save_data


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_save_manager: Optional[SaveManager] = None


def get_save_manager() -> SaveManager:
    """Get the global save manager instance."""
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager
