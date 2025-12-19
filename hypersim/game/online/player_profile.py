"""Player profile system for persistent online progression."""
from __future__ import annotations

import json
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum


class PlayerRank(Enum):
    """Competitive ranks for players."""
    UNRANKED = 0
    POINT = 1          # 1D - just starting
    LINE = 2           # Learning the basics
    TRIANGLE = 3       # 2D understanding
    SQUARE = 4
    PENTAGON = 5
    HEXAGON = 6
    CUBE = 7           # 3D mastery
    TESSERACT = 8      # 4D competence
    HYPERSPHERE = 9    # Top tier
    TRANSCENDENT = 10  # Elite


@dataclass
class PlayerStats:
    """Tracked statistics for a player."""
    # Playtime
    total_playtime_seconds: int = 0
    sessions_played: int = 0
    
    # Combat
    enemies_defeated: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    deaths: int = 0
    
    # Progression
    dimensions_unlocked: int = 1
    shapes_unlocked: int = 1
    skills_unlocked: int = 0
    max_evolution_reached: str = "pentachoron"
    
    # Multiplayer
    pvp_wins: int = 0
    pvp_losses: int = 0
    coop_missions_completed: int = 0
    players_helped: int = 0
    
    # Collection
    lore_entries_found: int = 0
    achievements_earned: int = 0
    
    @property
    def pvp_winrate(self) -> float:
        total = self.pvp_wins + self.pvp_losses
        return self.pvp_wins / total if total > 0 else 0.0
    
    @property
    def kd_ratio(self) -> float:
        return self.enemies_defeated / max(1, self.deaths)


@dataclass
class PlayerProfile:
    """Complete player profile for online play."""
    # Identity
    player_id: str
    username: str
    display_name: str = ""
    created_at: float = field(default_factory=time.time)
    last_online: float = field(default_factory=time.time)
    
    # Progression
    level: int = 1
    xp: int = 0
    rank: PlayerRank = PlayerRank.UNRANKED
    rank_points: int = 0
    
    # Current state
    current_shape: str = "pentachoron"
    unlocked_shapes: Set[str] = field(default_factory=lambda: {"pentachoron"})
    unlocked_skills: Set[str] = field(default_factory=set)
    unlocked_dimensions: Set[str] = field(default_factory=lambda: {"1d"})
    
    # Social
    guild_id: Optional[str] = None
    friends: Set[str] = field(default_factory=set)
    blocked: Set[str] = field(default_factory=set)
    
    # Stats
    stats: PlayerStats = field(default_factory=PlayerStats)
    
    # Customization
    title: str = "Newcomer"
    badge: str = "🔷"
    color: tuple = (100, 200, 255)
    
    # Achievements
    achievements: Set[str] = field(default_factory=set)
    
    # Season progress
    season_pass_level: int = 0
    season_xp: int = 0
    
    def __post_init__(self):
        if not self.display_name:
            self.display_name = self.username
    
    @property
    def xp_for_next_level(self) -> int:
        """XP required to reach next level."""
        return 100 + (self.level * 50)
    
    @property
    def level_progress(self) -> float:
        """Progress to next level (0-1)."""
        return self.xp / self.xp_for_next_level
    
    def add_xp(self, amount: int) -> bool:
        """Add XP and check for level up. Returns True if leveled up."""
        self.xp += amount
        leveled_up = False
        
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            leveled_up = True
        
        return leveled_up
    
    def update_rank(self, won: bool) -> Optional[PlayerRank]:
        """Update rank after a match. Returns new rank if changed."""
        old_rank = self.rank
        
        if won:
            self.rank_points += 25
        else:
            self.rank_points = max(0, self.rank_points - 15)
        
        # Rank thresholds
        thresholds = [
            (0, PlayerRank.UNRANKED),
            (100, PlayerRank.POINT),
            (250, PlayerRank.LINE),
            (500, PlayerRank.TRIANGLE),
            (800, PlayerRank.SQUARE),
            (1200, PlayerRank.PENTAGON),
            (1700, PlayerRank.HEXAGON),
            (2300, PlayerRank.CUBE),
            (3000, PlayerRank.TESSERACT),
            (4000, PlayerRank.HYPERSPHERE),
            (5500, PlayerRank.TRANSCENDENT),
        ]
        
        for threshold, rank in reversed(thresholds):
            if self.rank_points >= threshold:
                self.rank = rank
                break
        
        return self.rank if self.rank != old_rank else None
    
    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "player_id": self.player_id,
            "username": self.username,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "last_online": self.last_online,
            "level": self.level,
            "xp": self.xp,
            "rank": self.rank.value,
            "rank_points": self.rank_points,
            "current_shape": self.current_shape,
            "unlocked_shapes": list(self.unlocked_shapes),
            "unlocked_skills": list(self.unlocked_skills),
            "unlocked_dimensions": list(self.unlocked_dimensions),
            "guild_id": self.guild_id,
            "friends": list(self.friends),
            "stats": {
                "total_playtime_seconds": self.stats.total_playtime_seconds,
                "sessions_played": self.stats.sessions_played,
                "enemies_defeated": self.stats.enemies_defeated,
                "pvp_wins": self.stats.pvp_wins,
                "pvp_losses": self.stats.pvp_losses,
                "coop_missions_completed": self.stats.coop_missions_completed,
            },
            "title": self.title,
            "badge": self.badge,
            "achievements": list(self.achievements),
            "season_pass_level": self.season_pass_level,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "PlayerProfile":
        """Deserialize from dictionary."""
        stats = PlayerStats(
            total_playtime_seconds=data.get("stats", {}).get("total_playtime_seconds", 0),
            sessions_played=data.get("stats", {}).get("sessions_played", 0),
            enemies_defeated=data.get("stats", {}).get("enemies_defeated", 0),
            pvp_wins=data.get("stats", {}).get("pvp_wins", 0),
            pvp_losses=data.get("stats", {}).get("pvp_losses", 0),
            coop_missions_completed=data.get("stats", {}).get("coop_missions_completed", 0),
        )
        
        return cls(
            player_id=data["player_id"],
            username=data["username"],
            display_name=data.get("display_name", data["username"]),
            created_at=data.get("created_at", time.time()),
            last_online=data.get("last_online", time.time()),
            level=data.get("level", 1),
            xp=data.get("xp", 0),
            rank=PlayerRank(data.get("rank", 0)),
            rank_points=data.get("rank_points", 0),
            current_shape=data.get("current_shape", "pentachoron"),
            unlocked_shapes=set(data.get("unlocked_shapes", ["pentachoron"])),
            unlocked_skills=set(data.get("unlocked_skills", [])),
            unlocked_dimensions=set(data.get("unlocked_dimensions", ["1d"])),
            guild_id=data.get("guild_id"),
            friends=set(data.get("friends", [])),
            stats=stats,
            title=data.get("title", "Newcomer"),
            badge=data.get("badge", "🔷"),
            achievements=set(data.get("achievements", [])),
            season_pass_level=data.get("season_pass_level", 0),
        )


class ProfileManager:
    """Manages player profiles."""
    
    def __init__(self, storage_path: Path = Path("~/.hypersim/profiles").expanduser()):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._profiles: Dict[str, PlayerProfile] = {}
        self._online_players: Set[str] = set()
    
    def create_profile(self, username: str, display_name: str = "") -> PlayerProfile:
        """Create a new player profile."""
        player_id = hashlib.sha256(
            f"{username}:{time.time()}".encode()
        ).hexdigest()[:16]
        
        profile = PlayerProfile(
            player_id=player_id,
            username=username,
            display_name=display_name or username,
        )
        
        self._profiles[player_id] = profile
        self.save_profile(profile)
        
        return profile
    
    def get_profile(self, player_id: str) -> Optional[PlayerProfile]:
        """Get a profile by ID."""
        if player_id in self._profiles:
            return self._profiles[player_id]
        
        # Try loading from disk
        return self.load_profile(player_id)
    
    def get_by_username(self, username: str) -> Optional[PlayerProfile]:
        """Find profile by username."""
        for profile in self._profiles.values():
            if profile.username == username:
                return profile
        
        # Search saved profiles
        for path in self.storage_path.glob("*.json"):
            data = json.loads(path.read_text())
            if data.get("username") == username:
                profile = PlayerProfile.from_dict(data)
                self._profiles[profile.player_id] = profile
                return profile
        
        return None
    
    def save_profile(self, profile: PlayerProfile) -> None:
        """Save profile to disk."""
        path = self.storage_path / f"{profile.player_id}.json"
        path.write_text(json.dumps(profile.to_dict(), indent=2))
    
    def load_profile(self, player_id: str) -> Optional[PlayerProfile]:
        """Load profile from disk."""
        path = self.storage_path / f"{player_id}.json"
        if not path.exists():
            return None
        
        data = json.loads(path.read_text())
        profile = PlayerProfile.from_dict(data)
        self._profiles[player_id] = profile
        return profile
    
    def set_online(self, player_id: str) -> None:
        """Mark player as online."""
        self._online_players.add(player_id)
        profile = self.get_profile(player_id)
        if profile:
            profile.last_online = time.time()
    
    def set_offline(self, player_id: str) -> None:
        """Mark player as offline."""
        self._online_players.discard(player_id)
        profile = self.get_profile(player_id)
        if profile:
            profile.last_online = time.time()
            self.save_profile(profile)
    
    def get_online_players(self) -> List[PlayerProfile]:
        """Get all online players."""
        return [
            self._profiles[pid] 
            for pid in self._online_players 
            if pid in self._profiles
        ]
    
    def get_friends_online(self, player_id: str) -> List[PlayerProfile]:
        """Get online friends for a player."""
        profile = self.get_profile(player_id)
        if not profile:
            return []
        
        return [
            self._profiles[fid]
            for fid in profile.friends
            if fid in self._online_players and fid in self._profiles
        ]
