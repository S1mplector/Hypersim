"""Leaderboard system for competitive rankings."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from heapq import nlargest


class LeaderboardType(Enum):
    """Types of leaderboards."""
    # Overall
    LEVEL = "level"
    RANK_POINTS = "rank_points"
    TOTAL_XP = "total_xp"
    
    # PvP
    PVP_WINS = "pvp_wins"
    PVP_WINRATE = "pvp_winrate"
    PVP_STREAK = "pvp_streak"
    
    # Co-op
    COOP_MISSIONS = "coop_missions"
    PLAYERS_HELPED = "players_helped"
    
    # Combat
    ENEMIES_DEFEATED = "enemies_defeated"
    DAMAGE_DEALT = "damage_dealt"
    
    # Shape-specific
    SHAPE_MASTERY = "shape_mastery"
    EVOLUTIONS = "evolutions"
    
    # Seasonal
    SEASON_LEVEL = "season_level"
    SEASON_WINS = "season_wins"
    
    # Guild
    GUILD_LEVEL = "guild_level"
    GUILD_XP = "guild_xp"


class LeaderboardScope(Enum):
    """Scope of leaderboard."""
    GLOBAL = "global"
    FRIENDS = "friends"
    GUILD = "guild"
    FACTION = "faction"
    REGION = "region"


@dataclass
class RankEntry:
    """A single entry in a leaderboard."""
    player_id: str
    username: str
    value: float
    rank: int = 0
    
    # Optional metadata
    guild_tag: Optional[str] = None
    shape: Optional[str] = None
    badge: str = "🔷"
    
    # Change tracking
    previous_rank: Optional[int] = None
    
    @property
    def rank_change(self) -> Optional[int]:
        if self.previous_rank is None:
            return None
        return self.previous_rank - self.rank  # Positive = moved up


@dataclass
class LeaderboardSnapshot:
    """A snapshot of leaderboard at a point in time."""
    leaderboard_type: LeaderboardType
    scope: LeaderboardScope
    entries: List[RankEntry]
    updated_at: float = field(default_factory=time.time)
    total_participants: int = 0


class Leaderboard:
    """Manages a single leaderboard."""
    
    def __init__(
        self,
        lb_type: LeaderboardType,
        scope: LeaderboardScope = LeaderboardScope.GLOBAL,
        max_entries: int = 1000,
    ):
        self.lb_type = lb_type
        self.scope = scope
        self.max_entries = max_entries
        
        self._entries: Dict[str, RankEntry] = {}
        self._sorted_cache: List[RankEntry] = []
        self._cache_valid = False
        self._last_update = time.time()
    
    def update_score(
        self,
        player_id: str,
        username: str,
        value: float,
        guild_tag: Optional[str] = None,
        shape: Optional[str] = None,
        badge: str = "🔷",
    ) -> RankEntry:
        """Update a player's score."""
        existing = self._entries.get(player_id)
        previous_rank = existing.rank if existing else None
        
        entry = RankEntry(
            player_id=player_id,
            username=username,
            value=value,
            guild_tag=guild_tag,
            shape=shape,
            badge=badge,
            previous_rank=previous_rank,
        )
        
        self._entries[player_id] = entry
        self._cache_valid = False
        self._last_update = time.time()
        
        return entry
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from leaderboard."""
        if player_id in self._entries:
            del self._entries[player_id]
            self._cache_valid = False
            return True
        return False
    
    def get_rank(self, player_id: str) -> Optional[int]:
        """Get a player's rank."""
        self._ensure_cache()
        
        for i, entry in enumerate(self._sorted_cache):
            if entry.player_id == player_id:
                return i + 1
        return None
    
    def get_entry(self, player_id: str) -> Optional[RankEntry]:
        """Get a player's entry."""
        self._ensure_cache()
        return self._entries.get(player_id)
    
    def get_top(self, n: int = 100) -> List[RankEntry]:
        """Get top N entries."""
        self._ensure_cache()
        return self._sorted_cache[:n]
    
    def get_around_player(
        self,
        player_id: str,
        context: int = 5
    ) -> List[RankEntry]:
        """Get entries around a player."""
        self._ensure_cache()
        
        player_index = None
        for i, entry in enumerate(self._sorted_cache):
            if entry.player_id == player_id:
                player_index = i
                break
        
        if player_index is None:
            return []
        
        start = max(0, player_index - context)
        end = min(len(self._sorted_cache), player_index + context + 1)
        
        return self._sorted_cache[start:end]
    
    def get_snapshot(self, limit: int = 100) -> LeaderboardSnapshot:
        """Get a snapshot of the leaderboard."""
        return LeaderboardSnapshot(
            leaderboard_type=self.lb_type,
            scope=self.scope,
            entries=self.get_top(limit),
            updated_at=self._last_update,
            total_participants=len(self._entries),
        )
    
    def _ensure_cache(self) -> None:
        """Ensure sorted cache is valid."""
        if self._cache_valid:
            return
        
        # Sort by value descending
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: e.value,
            reverse=True
        )
        
        # Assign ranks and limit
        for i, entry in enumerate(sorted_entries[:self.max_entries]):
            entry.rank = i + 1
        
        self._sorted_cache = sorted_entries[:self.max_entries]
        self._cache_valid = True


class LeaderboardManager:
    """Manages all leaderboards."""
    
    def __init__(self):
        self._leaderboards: Dict[str, Leaderboard] = {}
        self._init_default_leaderboards()
    
    def _init_default_leaderboards(self) -> None:
        """Initialize default leaderboards."""
        for lb_type in LeaderboardType:
            key = f"{lb_type.value}_global"
            self._leaderboards[key] = Leaderboard(
                lb_type=lb_type,
                scope=LeaderboardScope.GLOBAL,
            )
    
    def get_leaderboard(
        self,
        lb_type: LeaderboardType,
        scope: LeaderboardScope = LeaderboardScope.GLOBAL,
    ) -> Optional[Leaderboard]:
        """Get a leaderboard."""
        key = f"{lb_type.value}_{scope.value}"
        return self._leaderboards.get(key)
    
    def update_player_stats(
        self,
        player_id: str,
        username: str,
        stats: Dict[str, float],
        guild_tag: Optional[str] = None,
        shape: Optional[str] = None,
    ) -> None:
        """Update all leaderboards for a player."""
        stat_to_lb = {
            "level": LeaderboardType.LEVEL,
            "rank_points": LeaderboardType.RANK_POINTS,
            "total_xp": LeaderboardType.TOTAL_XP,
            "pvp_wins": LeaderboardType.PVP_WINS,
            "pvp_winrate": LeaderboardType.PVP_WINRATE,
            "coop_missions": LeaderboardType.COOP_MISSIONS,
            "enemies_defeated": LeaderboardType.ENEMIES_DEFEATED,
            "damage_dealt": LeaderboardType.DAMAGE_DEALT,
            "season_level": LeaderboardType.SEASON_LEVEL,
        }
        
        for stat_name, value in stats.items():
            lb_type = stat_to_lb.get(stat_name)
            if lb_type:
                lb = self.get_leaderboard(lb_type)
                if lb:
                    lb.update_score(
                        player_id=player_id,
                        username=username,
                        value=value,
                        guild_tag=guild_tag,
                        shape=shape,
                    )
    
    def get_player_ranks(self, player_id: str) -> Dict[LeaderboardType, int]:
        """Get all ranks for a player."""
        ranks = {}
        
        for key, lb in self._leaderboards.items():
            rank = lb.get_rank(player_id)
            if rank:
                ranks[lb.lb_type] = rank
        
        return ranks


# Seasonal leaderboards
@dataclass
class Season:
    """A competitive season."""
    season_id: str
    name: str
    start_time: float
    end_time: float
    
    # Rewards per rank
    rewards: Dict[str, Dict] = field(default_factory=dict)  # rank_range -> rewards
    
    # Leaderboards for this season
    leaderboards: Dict[LeaderboardType, Leaderboard] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        now = time.time()
        return self.start_time <= now <= self.end_time
    
    @property
    def time_remaining(self) -> float:
        return max(0, self.end_time - time.time())
    
    @property
    def days_remaining(self) -> int:
        return int(self.time_remaining / 86400)


class SeasonManager:
    """Manages competitive seasons."""
    
    def __init__(self):
        self._seasons: Dict[str, Season] = {}
        self._current_season_id: Optional[str] = None
    
    def create_season(
        self,
        name: str,
        duration_days: int = 90,
        rewards: Optional[Dict] = None,
    ) -> Season:
        """Create a new season."""
        season_id = f"season_{len(self._seasons) + 1}"
        
        season = Season(
            season_id=season_id,
            name=name,
            start_time=time.time(),
            end_time=time.time() + (duration_days * 86400),
            rewards=rewards or {},
        )
        
        # Create season-specific leaderboards
        for lb_type in [LeaderboardType.SEASON_LEVEL, LeaderboardType.SEASON_WINS]:
            season.leaderboards[lb_type] = Leaderboard(lb_type)
        
        self._seasons[season_id] = season
        self._current_season_id = season_id
        
        return season
    
    def get_current_season(self) -> Optional[Season]:
        """Get the current active season."""
        if self._current_season_id:
            return self._seasons.get(self._current_season_id)
        return None
    
    def end_season(self) -> Optional[Dict[str, Dict]]:
        """End the current season and calculate rewards."""
        season = self.get_current_season()
        if not season:
            return None
        
        # Calculate rewards for all participants
        rewards_to_distribute = {}
        
        for lb_type, lb in season.leaderboards.items():
            for entry in lb.get_top(1000):
                if entry.player_id not in rewards_to_distribute:
                    rewards_to_distribute[entry.player_id] = {}
                
                # Determine reward tier based on rank
                reward_tier = self._get_reward_tier(entry.rank)
                if reward_tier in season.rewards:
                    rewards_to_distribute[entry.player_id].update(
                        season.rewards[reward_tier]
                    )
        
        self._current_season_id = None
        return rewards_to_distribute
    
    def _get_reward_tier(self, rank: int) -> str:
        """Get reward tier for a rank."""
        if rank <= 10:
            return "top_10"
        elif rank <= 100:
            return "top_100"
        elif rank <= 500:
            return "top_500"
        elif rank <= 1000:
            return "top_1000"
        return "participant"
