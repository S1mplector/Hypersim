"""Game server for online multiplayer."""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any
import threading

from .player_profile import PlayerProfile, ProfileManager
from .matchmaking import MatchmakingQueue, MatchType, Match
from .guilds import GuildManager, ShapeFaction
from .leaderboards import LeaderboardManager, SeasonManager


class ServerState(Enum):
    """State of the game server."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"


@dataclass
class ServerConfig:
    """Configuration for the game server."""
    name: str = "HyperSim Server"
    host: str = "0.0.0.0"
    port: int = 7777
    max_players: int = 1000
    tick_rate: int = 20  # Updates per second
    
    # Features
    enable_pvp: bool = True
    enable_guilds: bool = True
    enable_seasons: bool = True
    
    # Limits
    max_guilds: int = 100
    max_matches: int = 50
    
    # Timeouts
    connection_timeout: float = 30.0
    afk_timeout: float = 300.0


@dataclass
class ConnectedClient:
    """A connected client."""
    client_id: str
    player_id: Optional[str] = None
    profile: Optional[PlayerProfile] = None
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    # Network info
    address: tuple = ("", 0)
    latency_ms: float = 0.0
    
    # State
    in_match: Optional[str] = None
    in_queue: Optional[MatchType] = None
    
    @property
    def is_authenticated(self) -> bool:
        return self.player_id is not None
    
    @property
    def idle_time(self) -> float:
        return time.time() - self.last_activity


class GameServer:
    """Main game server for HyperSim online."""
    
    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or ServerConfig()
        self.state = ServerState.STOPPED
        
        # Core systems
        self.profiles = ProfileManager()
        self.matchmaking = MatchmakingQueue()
        self.guilds = GuildManager()
        self.leaderboards = LeaderboardManager()
        self.seasons = SeasonManager()
        
        # Connected clients
        self._clients: Dict[str, ConnectedClient] = {}
        self._player_to_client: Dict[str, str] = {}
        
        # Server stats
        self._stats = {
            "players_online": 0,
            "matches_active": 0,
            "total_connections": 0,
            "uptime_start": 0.0,
        }
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Background tasks
        self._tick_task: Optional[asyncio.Task] = None
        self._matchmaking_task: Optional[asyncio.Task] = None
        
        # Setup matchmaking callbacks
        self._setup_matchmaking()
    
    def _setup_matchmaking(self) -> None:
        """Setup matchmaking callbacks."""
        def on_match_found(match: Match):
            self._emit("match_found", match=match)
            for player_id in match.players:
                self._notify_player(player_id, "match_found", {
                    "match_id": match.match_id,
                    "match_type": match.match_type.value,
                    "players": match.players,
                })
        
        def on_match_start(match: Match):
            self._stats["matches_active"] += 1
            self._emit("match_start", match=match)
        
        def on_match_end(match: Match):
            self._stats["matches_active"] -= 1
            self._emit("match_end", match=match)
            self._process_match_results(match)
        
        self.matchmaking.on_match_found = on_match_found
        self.matchmaking.on_match_start = on_match_start
        self.matchmaking.on_match_end = on_match_end
    
    async def start(self) -> None:
        """Start the server."""
        if self.state != ServerState.STOPPED:
            return
        
        self.state = ServerState.STARTING
        self._stats["uptime_start"] = time.time()
        
        # Start a season if none active
        if self.config.enable_seasons and not self.seasons.get_current_season():
            self.seasons.create_season("Season 1", duration_days=90)
        
        # Start background tasks
        self._tick_task = asyncio.create_task(self._tick_loop())
        self._matchmaking_task = asyncio.create_task(self._matchmaking_loop())
        
        self.state = ServerState.RUNNING
        self._emit("server_start")
        
        print(f"🎮 {self.config.name} started on {self.config.host}:{self.config.port}")
    
    async def stop(self) -> None:
        """Stop the server."""
        if self.state != ServerState.RUNNING:
            return
        
        self.state = ServerState.STOPPING
        
        # Cancel background tasks
        if self._tick_task:
            self._tick_task.cancel()
        if self._matchmaking_task:
            self._matchmaking_task.cancel()
        
        # Disconnect all clients
        for client_id in list(self._clients.keys()):
            self._disconnect_client(client_id, "server_shutdown")
        
        self.state = ServerState.STOPPED
        self._emit("server_stop")
        
        print("🛑 Server stopped")
    
    async def _tick_loop(self) -> None:
        """Main server tick loop."""
        tick_duration = 1.0 / self.config.tick_rate
        
        while self.state == ServerState.RUNNING:
            tick_start = time.time()
            
            # Process tick
            self._process_tick()
            
            # Wait for next tick
            elapsed = time.time() - tick_start
            if elapsed < tick_duration:
                await asyncio.sleep(tick_duration - elapsed)
    
    async def _matchmaking_loop(self) -> None:
        """Matchmaking processing loop."""
        while self.state == ServerState.RUNNING:
            # Process matchmaking queues
            new_matches = self.matchmaking.process_queues()
            
            # Auto-start matches that are ready
            for match in new_matches:
                if match.can_start:
                    self.matchmaking.start_match(match.match_id)
            
            await asyncio.sleep(1.0)  # Check every second
    
    def _process_tick(self) -> None:
        """Process a single server tick."""
        now = time.time()
        
        # Check for AFK players
        for client_id, client in list(self._clients.items()):
            if client.idle_time > self.config.afk_timeout:
                self._disconnect_client(client_id, "afk_timeout")
        
        # Update stats
        self._stats["players_online"] = len([
            c for c in self._clients.values() if c.is_authenticated
        ])
    
    # =========================================================================
    # Client Management
    # =========================================================================
    
    def connect_client(self, client_id: str, address: tuple) -> ConnectedClient:
        """Handle new client connection."""
        client = ConnectedClient(
            client_id=client_id,
            address=address,
        )
        
        self._clients[client_id] = client
        self._stats["total_connections"] += 1
        
        self._emit("client_connect", client=client)
        return client
    
    def authenticate_client(
        self,
        client_id: str,
        player_id: str,
    ) -> bool:
        """Authenticate a client with a player profile."""
        client = self._clients.get(client_id)
        if not client:
            return False
        
        profile = self.profiles.get_profile(player_id)
        if not profile:
            return False
        
        # Check if player already connected
        if player_id in self._player_to_client:
            old_client_id = self._player_to_client[player_id]
            self._disconnect_client(old_client_id, "duplicate_login")
        
        client.player_id = player_id
        client.profile = profile
        self._player_to_client[player_id] = client_id
        
        self.profiles.set_online(player_id)
        self._emit("player_login", player_id=player_id)
        
        return True
    
    def _disconnect_client(self, client_id: str, reason: str = "") -> None:
        """Disconnect a client."""
        client = self._clients.get(client_id)
        if not client:
            return
        
        # Clean up player associations
        if client.player_id:
            self._player_to_client.pop(client.player_id, None)
            self.profiles.set_offline(client.player_id)
            
            # Remove from queue
            self.matchmaking.dequeue(client.player_id)
            
            # Handle match abandonment
            if client.in_match:
                self._handle_match_abandon(client.player_id, client.in_match)
        
        del self._clients[client_id]
        self._emit("client_disconnect", client_id=client_id, reason=reason)
    
    # =========================================================================
    # Game Actions
    # =========================================================================
    
    def queue_for_match(
        self,
        player_id: str,
        match_type: MatchType,
        preferred_dimension: Optional[str] = None,
    ) -> bool:
        """Queue a player for matchmaking."""
        client_id = self._player_to_client.get(player_id)
        if not client_id:
            return False
        
        client = self._clients.get(client_id)
        if not client or not client.profile:
            return False
        
        if self.matchmaking.queue(
            profile=client.profile,
            match_type=match_type,
            preferred_dimension=preferred_dimension,
        ):
            client.in_queue = match_type
            return True
        
        return False
    
    def cancel_queue(self, player_id: str) -> bool:
        """Cancel matchmaking queue."""
        client_id = self._player_to_client.get(player_id)
        if client_id and client_id in self._clients:
            self._clients[client_id].in_queue = None
        
        return self.matchmaking.dequeue(player_id)
    
    def _handle_match_abandon(self, player_id: str, match_id: str) -> None:
        """Handle a player abandoning a match."""
        match = self.matchmaking.get_match(match_id)
        if not match:
            return
        
        # Remove from match
        match.remove_player(player_id)
        
        # Check if match should end
        if len(match.players) < match.min_players:
            # End match, remaining players win
            remaining = match.players[0] if match.players else None
            self.matchmaking.end_match(
                match_id,
                winner_player=remaining,
            )
    
    def _process_match_results(self, match: Match) -> None:
        """Process results of a completed match."""
        # Update player stats and rankings
        for player_id in match.players:
            profile = self.profiles.get_profile(player_id)
            if not profile:
                continue
            
            is_winner = (
                (match.winner_player == player_id) or
                (match.winner_team is not None and 
                 player_id in match.teams.get(match.winner_team, []))
            )
            
            # Update stats
            if match.match_type in (MatchType.PVP_DUEL, MatchType.PVP_TEAM, MatchType.PVP_FFA):
                if is_winner:
                    profile.stats.pvp_wins += 1
                else:
                    profile.stats.pvp_losses += 1
                
                # Update rank
                new_rank = profile.update_rank(is_winner)
                if new_rank:
                    self._notify_player(player_id, "rank_change", {
                        "new_rank": new_rank.name,
                        "rank_points": profile.rank_points,
                    })
            
            elif match.match_type in (MatchType.COOP_CAMPAIGN, MatchType.COOP_DUNGEON):
                profile.stats.coop_missions_completed += 1
            
            # Add XP
            xp_gain = 100 if is_winner else 50
            if profile.add_xp(xp_gain):
                self._notify_player(player_id, "level_up", {
                    "new_level": profile.level,
                })
            
            # Save profile
            self.profiles.save_profile(profile)
            
            # Update leaderboards
            self.leaderboards.update_player_stats(
                player_id=player_id,
                username=profile.username,
                stats={
                    "level": profile.level,
                    "rank_points": profile.rank_points,
                    "pvp_wins": profile.stats.pvp_wins,
                    "pvp_winrate": profile.stats.pvp_winrate,
                    "coop_missions": profile.stats.coop_missions_completed,
                },
                guild_tag=self._get_player_guild_tag(player_id),
                shape=profile.current_shape,
            )
    
    def _get_player_guild_tag(self, player_id: str) -> Optional[str]:
        """Get a player's guild tag."""
        guild = self.guilds.get_player_guild(player_id)
        return guild.tag if guild else None
    
    # =========================================================================
    # Notifications & Events
    # =========================================================================
    
    def _notify_player(self, player_id: str, event: str, data: Dict) -> None:
        """Send a notification to a player."""
        client_id = self._player_to_client.get(player_id)
        if not client_id:
            return
        
        # In real implementation, this would send over network
        self._emit(f"notify_{event}", player_id=player_id, data=data)
    
    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def _emit(self, event: str, **kwargs) -> None:
        """Emit an event."""
        handlers = self._event_handlers.get(event, [])
        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception as e:
                print(f"Error in event handler for {event}: {e}")
    
    # =========================================================================
    # Server Info
    # =========================================================================
    
    def get_status(self) -> Dict:
        """Get server status."""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "players_online": self._stats["players_online"],
            "matches_active": self._stats["matches_active"],
            "uptime": time.time() - self._stats["uptime_start"] if self._stats["uptime_start"] else 0,
            "season": self.seasons.get_current_season().name if self.seasons.get_current_season() else None,
        }
    
    def get_queue_stats(self) -> Dict[str, Dict]:
        """Get matchmaking queue statistics."""
        return {
            mt.value: self.matchmaking.get_queue_status(mt)
            for mt in MatchType
        }
