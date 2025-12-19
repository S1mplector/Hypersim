"""Matchmaking system for online play."""
from __future__ import annotations

import time
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable
from queue import PriorityQueue

from .player_profile import PlayerProfile, PlayerRank


class MatchType(Enum):
    """Types of matches."""
    COOP_CAMPAIGN = "coop_campaign"      # 2-4 players story
    COOP_DUNGEON = "coop_dungeon"        # 2-4 players procedural
    PVP_DUEL = "pvp_duel"                # 1v1 arena
    PVP_TEAM = "pvp_team"                # 2v2 or 3v3
    PVP_FFA = "pvp_ffa"                  # Free for all (4-8)
    DIMENSIONAL_WAR = "dimensional_war"  # Large scale faction battle


class MatchState(Enum):
    """State of a match."""
    WAITING = "waiting"      # Waiting for players
    STARTING = "starting"    # Countdown
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


@dataclass
class QueueEntry:
    """A player waiting in matchmaking queue."""
    player_id: str
    profile: PlayerProfile
    match_type: MatchType
    queued_at: float = field(default_factory=time.time)
    preferred_dimension: Optional[str] = None
    party_ids: List[str] = field(default_factory=list)  # Pre-made party
    
    @property
    def wait_time(self) -> float:
        return time.time() - self.queued_at
    
    @property
    def skill_rating(self) -> int:
        """Estimate skill rating for matchmaking."""
        return self.profile.rank_points + (self.profile.level * 10)
    
    def __lt__(self, other: "QueueEntry") -> bool:
        """Priority queue comparison - longer wait = higher priority."""
        return self.queued_at < other.queued_at


@dataclass
class Match:
    """An active or pending match."""
    match_id: str
    match_type: MatchType
    state: MatchState = MatchState.WAITING
    
    # Players
    players: List[str] = field(default_factory=list)
    teams: Dict[int, List[str]] = field(default_factory=dict)  # team_id -> player_ids
    
    # Settings
    dimension: str = "4d"
    map_id: Optional[str] = None
    max_players: int = 4
    min_players: int = 2
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    ended_at: Optional[float] = None
    
    # Results
    winner_team: Optional[int] = None
    winner_player: Optional[str] = None
    scores: Dict[str, int] = field(default_factory=dict)
    
    @property
    def is_full(self) -> bool:
        return len(self.players) >= self.max_players
    
    @property
    def can_start(self) -> bool:
        return len(self.players) >= self.min_players
    
    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.ended_at:
            return self.ended_at - self.started_at
        return None
    
    def add_player(self, player_id: str, team: int = 0) -> bool:
        """Add a player to the match."""
        if self.is_full or player_id in self.players:
            return False
        
        self.players.append(player_id)
        
        if team not in self.teams:
            self.teams[team] = []
        self.teams[team].append(player_id)
        
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the match."""
        if player_id not in self.players:
            return False
        
        self.players.remove(player_id)
        
        for team_players in self.teams.values():
            if player_id in team_players:
                team_players.remove(player_id)
        
        return True
    
    def start(self) -> bool:
        """Start the match."""
        if not self.can_start:
            return False
        
        self.state = MatchState.IN_PROGRESS
        self.started_at = time.time()
        return True
    
    def end(self, winner_team: Optional[int] = None, winner_player: Optional[str] = None) -> None:
        """End the match."""
        self.state = MatchState.FINISHED
        self.ended_at = time.time()
        self.winner_team = winner_team
        self.winner_player = winner_player


class MatchmakingQueue:
    """Handles matchmaking for all game modes."""
    
    # Match configuration
    MATCH_CONFIG = {
        MatchType.COOP_CAMPAIGN: {"min": 1, "max": 4, "teams": 1},
        MatchType.COOP_DUNGEON: {"min": 2, "max": 4, "teams": 1},
        MatchType.PVP_DUEL: {"min": 2, "max": 2, "teams": 2},
        MatchType.PVP_TEAM: {"min": 4, "max": 6, "teams": 2},
        MatchType.PVP_FFA: {"min": 4, "max": 8, "teams": 0},
        MatchType.DIMENSIONAL_WAR: {"min": 8, "max": 32, "teams": 4},
    }
    
    # Skill rating tolerance (expands over time)
    INITIAL_RATING_TOLERANCE = 200
    RATING_TOLERANCE_EXPANSION = 50  # Per 30 seconds
    MAX_RATING_TOLERANCE = 1000
    
    def __init__(self):
        self._queues: Dict[MatchType, List[QueueEntry]] = {
            mt: [] for mt in MatchType
        }
        self._active_matches: Dict[str, Match] = {}
        self._player_to_match: Dict[str, str] = {}
        self._match_counter = 0
        
        # Callbacks
        self.on_match_found: Optional[Callable[[Match], None]] = None
        self.on_match_start: Optional[Callable[[Match], None]] = None
        self.on_match_end: Optional[Callable[[Match], None]] = None
    
    def queue(
        self,
        profile: PlayerProfile,
        match_type: MatchType,
        preferred_dimension: Optional[str] = None,
        party_ids: Optional[List[str]] = None,
    ) -> bool:
        """Add a player to the matchmaking queue."""
        # Check if already in queue or match
        if self._is_player_busy(profile.player_id):
            return False
        
        entry = QueueEntry(
            player_id=profile.player_id,
            profile=profile,
            match_type=match_type,
            preferred_dimension=preferred_dimension,
            party_ids=party_ids or [],
        )
        
        self._queues[match_type].append(entry)
        return True
    
    def dequeue(self, player_id: str) -> bool:
        """Remove a player from all queues."""
        removed = False
        for queue in self._queues.values():
            for entry in queue[:]:
                if entry.player_id == player_id:
                    queue.remove(entry)
                    removed = True
        return removed
    
    def _is_player_busy(self, player_id: str) -> bool:
        """Check if player is already queued or in a match."""
        # Check queues
        for queue in self._queues.values():
            for entry in queue:
                if entry.player_id == player_id:
                    return True
        
        # Check active matches
        return player_id in self._player_to_match
    
    def process_queues(self) -> List[Match]:
        """Process all queues and create matches. Call periodically."""
        new_matches = []
        
        for match_type, queue in self._queues.items():
            if not queue:
                continue
            
            config = self.MATCH_CONFIG[match_type]
            
            # Sort by wait time (longest first)
            queue.sort(key=lambda e: e.queued_at)
            
            # Try to form matches
            matches = self._form_matches(queue, match_type, config)
            new_matches.extend(matches)
        
        return new_matches
    
    def _form_matches(
        self,
        queue: List[QueueEntry],
        match_type: MatchType,
        config: Dict
    ) -> List[Match]:
        """Try to form matches from a queue."""
        matches = []
        used_players = set()
        
        for anchor in queue:
            if anchor.player_id in used_players:
                continue
            
            # Calculate rating tolerance based on wait time
            tolerance = min(
                self.MAX_RATING_TOLERANCE,
                self.INITIAL_RATING_TOLERANCE + 
                (anchor.wait_time / 30) * self.RATING_TOLERANCE_EXPANSION
            )
            
            # Find compatible players
            compatible = [anchor]
            
            for entry in queue:
                if entry.player_id in used_players:
                    continue
                if entry.player_id == anchor.player_id:
                    continue
                
                # Check skill rating compatibility
                rating_diff = abs(entry.skill_rating - anchor.skill_rating)
                if rating_diff <= tolerance:
                    compatible.append(entry)
                
                if len(compatible) >= config["max"]:
                    break
            
            # Check if we have enough players
            if len(compatible) >= config["min"]:
                match = self._create_match(compatible, match_type, config)
                matches.append(match)
                
                for entry in compatible:
                    used_players.add(entry.player_id)
        
        # Remove matched players from queue
        queue[:] = [e for e in queue if e.player_id not in used_players]
        
        return matches
    
    def _create_match(
        self,
        entries: List[QueueEntry],
        match_type: MatchType,
        config: Dict
    ) -> Match:
        """Create a match from queue entries."""
        self._match_counter += 1
        match_id = f"match_{self._match_counter}_{int(time.time())}"
        
        match = Match(
            match_id=match_id,
            match_type=match_type,
            min_players=config["min"],
            max_players=config["max"],
        )
        
        # Assign teams
        num_teams = config["teams"]
        if num_teams > 1:
            # Distribute players across teams
            for i, entry in enumerate(entries):
                team = i % num_teams
                match.add_player(entry.player_id, team)
        else:
            # All on same team (co-op) or no teams (FFA)
            for entry in entries:
                match.add_player(entry.player_id, 0)
        
        # Set dimension (prefer anchor's preference)
        if entries[0].preferred_dimension:
            match.dimension = entries[0].preferred_dimension
        
        # Register match
        self._active_matches[match_id] = match
        for entry in entries:
            self._player_to_match[entry.player_id] = match_id
        
        # Callback
        if self.on_match_found:
            self.on_match_found(match)
        
        return match
    
    def get_match(self, match_id: str) -> Optional[Match]:
        """Get a match by ID."""
        return self._active_matches.get(match_id)
    
    def get_player_match(self, player_id: str) -> Optional[Match]:
        """Get the match a player is in."""
        match_id = self._player_to_match.get(player_id)
        if match_id:
            return self._active_matches.get(match_id)
        return None
    
    def start_match(self, match_id: str) -> bool:
        """Start a match."""
        match = self._active_matches.get(match_id)
        if not match or not match.start():
            return False
        
        if self.on_match_start:
            self.on_match_start(match)
        
        return True
    
    def end_match(
        self,
        match_id: str,
        winner_team: Optional[int] = None,
        winner_player: Optional[str] = None,
        scores: Optional[Dict[str, int]] = None
    ) -> bool:
        """End a match."""
        match = self._active_matches.get(match_id)
        if not match:
            return False
        
        match.end(winner_team, winner_player)
        if scores:
            match.scores = scores
        
        # Clean up player mappings
        for player_id in match.players:
            self._player_to_match.pop(player_id, None)
        
        if self.on_match_end:
            self.on_match_end(match)
        
        return True
    
    def get_queue_status(self, match_type: MatchType) -> Dict:
        """Get status of a queue."""
        queue = self._queues[match_type]
        config = self.MATCH_CONFIG[match_type]
        
        return {
            "players_queued": len(queue),
            "min_players": config["min"],
            "max_players": config["max"],
            "average_wait": sum(e.wait_time for e in queue) / len(queue) if queue else 0,
            "estimated_time": self._estimate_wait_time(match_type),
        }
    
    def _estimate_wait_time(self, match_type: MatchType) -> float:
        """Estimate wait time for a match type."""
        queue = self._queues[match_type]
        config = self.MATCH_CONFIG[match_type]
        
        if len(queue) >= config["min"]:
            return 5.0  # Almost instant
        
        needed = config["min"] - len(queue)
        # Estimate based on historical join rate (placeholder)
        return needed * 30.0  # 30 seconds per needed player
