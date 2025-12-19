"""Online multiplayer infrastructure for HyperSim MMO-lite.

Features:
- Player profiles with persistent progression
- Matchmaking for co-op and PvP
- Guild/faction system based on shape families
- Leaderboards and rankings
- Seasonal events and rewards
"""

from .player_profile import PlayerProfile, ProfileManager, PlayerRank, PlayerStats
from .matchmaking import MatchmakingQueue, MatchType, Match, MatchState
from .guilds import Guild, GuildManager, ShapeFaction, GuildRank
from .leaderboards import Leaderboard, LeaderboardType, RankEntry, LeaderboardManager
from .server import GameServer, ServerConfig

__all__ = [
    # Profiles
    "PlayerProfile",
    "ProfileManager",
    # Matchmaking
    "MatchmakingQueue",
    "MatchType",
    "Match",
    # Guilds
    "Guild",
    "GuildManager",
    "ShapeFaction",
    # Leaderboards
    "Leaderboard",
    "LeaderboardType",
    "RankEntry",
    # Server
    "GameServer",
    "ServerConfig",
]
