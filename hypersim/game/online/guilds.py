"""Guild and faction system based on shape families."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from hypersim.game.evolution_expanded import ShapeFamily


class ShapeFaction(Enum):
    """Major factions based on shape families."""
    REGULARS = "regulars"          # Regular polytope purists
    UNIFORMISTS = "uniformists"    # Truncation enthusiasts  
    EXOTICS = "exotics"            # Topological rebels
    PRISMATICS = "prismatics"      # Extension advocates
    TRANSCENDENTS = "transcendents"  # 5D seekers
    NEUTRAL = "neutral"            # No faction


# Faction to shape family mapping
FACTION_FAMILIES = {
    ShapeFaction.REGULARS: [ShapeFamily.REGULAR],
    ShapeFaction.UNIFORMISTS: [ShapeFamily.UNIFORM, ShapeFamily.CELL_24],
    ShapeFaction.EXOTICS: [ShapeFamily.EXOTIC],
    ShapeFaction.PRISMATICS: [ShapeFamily.PRISM, ShapeFamily.DUOPRISM],
    ShapeFaction.TRANSCENDENTS: [ShapeFamily.TRANSCENDENT, ShapeFamily.SPECIAL],
}

# Faction relationships
FACTION_ALLIES = {
    ShapeFaction.REGULARS: [ShapeFaction.UNIFORMISTS],
    ShapeFaction.UNIFORMISTS: [ShapeFaction.REGULARS],
    ShapeFaction.EXOTICS: [ShapeFaction.TRANSCENDENTS],
    ShapeFaction.PRISMATICS: [],
    ShapeFaction.TRANSCENDENTS: [ShapeFaction.EXOTICS],
}

FACTION_RIVALS = {
    ShapeFaction.REGULARS: [ShapeFaction.EXOTICS],
    ShapeFaction.UNIFORMISTS: [ShapeFaction.PRISMATICS],
    ShapeFaction.EXOTICS: [ShapeFaction.REGULARS],
    ShapeFaction.PRISMATICS: [ShapeFaction.UNIFORMISTS],
    ShapeFaction.TRANSCENDENTS: [],
}


class GuildRank(Enum):
    """Ranks within a guild."""
    MEMBER = 0
    VETERAN = 1
    OFFICER = 2
    CO_LEADER = 3
    LEADER = 4


@dataclass
class GuildMember:
    """A member of a guild."""
    player_id: str
    rank: GuildRank = GuildRank.MEMBER
    joined_at: float = field(default_factory=time.time)
    contribution_points: int = 0
    last_active: float = field(default_factory=time.time)
    
    @property
    def days_in_guild(self) -> int:
        return int((time.time() - self.joined_at) / 86400)


@dataclass
class GuildStats:
    """Statistics for a guild."""
    total_xp_earned: int = 0
    pvp_wins: int = 0
    pvp_losses: int = 0
    coop_missions: int = 0
    dimensional_wars_won: int = 0
    members_all_time: int = 0


@dataclass
class Guild:
    """A player guild aligned with a shape faction."""
    guild_id: str
    name: str
    tag: str  # 3-4 character tag
    faction: ShapeFaction
    
    # Leadership
    leader_id: str
    created_at: float = field(default_factory=time.time)
    
    # Members
    members: Dict[str, GuildMember] = field(default_factory=dict)
    max_members: int = 50
    
    # Description
    description: str = ""
    motd: str = ""  # Message of the day
    emblem: str = "🔷"
    color: tuple = (100, 150, 255)
    
    # Stats
    level: int = 1
    xp: int = 0
    stats: GuildStats = field(default_factory=GuildStats)
    
    # Settings
    public: bool = True  # Can anyone join?
    min_level_to_join: int = 1
    
    # Buffs (unlocked at higher guild levels)
    active_buffs: List[str] = field(default_factory=list)
    
    @property
    def member_count(self) -> int:
        return len(self.members)
    
    @property
    def is_full(self) -> bool:
        return self.member_count >= self.max_members
    
    @property
    def xp_for_next_level(self) -> int:
        return 1000 + (self.level * 500)
    
    def add_member(
        self,
        player_id: str,
        rank: GuildRank = GuildRank.MEMBER
    ) -> bool:
        """Add a member to the guild."""
        if self.is_full or player_id in self.members:
            return False
        
        self.members[player_id] = GuildMember(
            player_id=player_id,
            rank=rank,
        )
        self.stats.members_all_time += 1
        return True
    
    def remove_member(self, player_id: str) -> bool:
        """Remove a member from the guild."""
        if player_id not in self.members:
            return False
        
        # Can't remove leader
        if player_id == self.leader_id:
            return False
        
        del self.members[player_id]
        return True
    
    def promote(self, player_id: str) -> bool:
        """Promote a member."""
        member = self.members.get(player_id)
        if not member or member.rank == GuildRank.CO_LEADER:
            return False
        
        if member.rank == GuildRank.LEADER:
            return False
        
        member.rank = GuildRank(member.rank.value + 1)
        return True
    
    def demote(self, player_id: str) -> bool:
        """Demote a member."""
        member = self.members.get(player_id)
        if not member or member.rank == GuildRank.MEMBER:
            return False
        
        if player_id == self.leader_id:
            return False
        
        member.rank = GuildRank(member.rank.value - 1)
        return True
    
    def transfer_leadership(self, new_leader_id: str) -> bool:
        """Transfer leadership to another member."""
        if new_leader_id not in self.members:
            return False
        
        # Demote old leader to co-leader
        old_leader = self.members.get(self.leader_id)
        if old_leader:
            old_leader.rank = GuildRank.CO_LEADER
        
        # Promote new leader
        self.members[new_leader_id].rank = GuildRank.LEADER
        self.leader_id = new_leader_id
        return True
    
    def add_xp(self, amount: int) -> bool:
        """Add XP to guild. Returns True if leveled up."""
        self.xp += amount
        self.stats.total_xp_earned += amount
        
        leveled = False
        while self.xp >= self.xp_for_next_level:
            self.xp -= self.xp_for_next_level
            self.level += 1
            self._unlock_level_rewards()
            leveled = True
        
        return leveled
    
    def _unlock_level_rewards(self) -> None:
        """Unlock rewards for reaching a new level."""
        # Increase max members
        if self.level % 5 == 0:
            self.max_members += 10
        
        # Unlock buffs at certain levels
        level_buffs = {
            5: "xp_boost_5",
            10: "damage_boost_3",
            15: "cooldown_reduction_5",
            20: "xp_boost_10",
            25: "faction_bonus",
        }
        
        if self.level in level_buffs:
            self.active_buffs.append(level_buffs[self.level])
    
    def get_officers(self) -> List[GuildMember]:
        """Get all officers and above."""
        return [
            m for m in self.members.values()
            if m.rank.value >= GuildRank.OFFICER.value
        ]


class GuildManager:
    """Manages all guilds."""
    
    def __init__(self):
        self._guilds: Dict[str, Guild] = {}
        self._player_to_guild: Dict[str, str] = {}
        self._guild_counter = 0
        
        # Faction standings (for dimensional wars)
        self._faction_points: Dict[ShapeFaction, int] = {
            f: 0 for f in ShapeFaction if f != ShapeFaction.NEUTRAL
        }
    
    def create_guild(
        self,
        name: str,
        tag: str,
        leader_id: str,
        faction: ShapeFaction = ShapeFaction.NEUTRAL,
        description: str = "",
    ) -> Optional[Guild]:
        """Create a new guild."""
        # Check if player already in a guild
        if leader_id in self._player_to_guild:
            return None
        
        # Check name/tag uniqueness
        for guild in self._guilds.values():
            if guild.name.lower() == name.lower():
                return None
            if guild.tag.upper() == tag.upper():
                return None
        
        self._guild_counter += 1
        guild_id = f"guild_{self._guild_counter}"
        
        guild = Guild(
            guild_id=guild_id,
            name=name,
            tag=tag.upper()[:4],
            faction=faction,
            leader_id=leader_id,
            description=description,
        )
        
        # Add leader as member
        guild.add_member(leader_id, GuildRank.LEADER)
        
        self._guilds[guild_id] = guild
        self._player_to_guild[leader_id] = guild_id
        
        return guild
    
    def disband_guild(self, guild_id: str, requester_id: str) -> bool:
        """Disband a guild (leader only)."""
        guild = self._guilds.get(guild_id)
        if not guild or guild.leader_id != requester_id:
            return False
        
        # Remove all player mappings
        for player_id in guild.members:
            self._player_to_guild.pop(player_id, None)
        
        del self._guilds[guild_id]
        return True
    
    def join_guild(self, guild_id: str, player_id: str) -> bool:
        """Join a guild."""
        guild = self._guilds.get(guild_id)
        if not guild or not guild.public:
            return False
        
        if player_id in self._player_to_guild:
            return False
        
        if guild.add_member(player_id):
            self._player_to_guild[player_id] = guild_id
            return True
        
        return False
    
    def leave_guild(self, player_id: str) -> bool:
        """Leave current guild."""
        guild_id = self._player_to_guild.get(player_id)
        if not guild_id:
            return False
        
        guild = self._guilds.get(guild_id)
        if not guild:
            return False
        
        if guild.remove_member(player_id):
            del self._player_to_guild[player_id]
            return True
        
        return False
    
    def get_guild(self, guild_id: str) -> Optional[Guild]:
        """Get a guild by ID."""
        return self._guilds.get(guild_id)
    
    def get_player_guild(self, player_id: str) -> Optional[Guild]:
        """Get the guild a player is in."""
        guild_id = self._player_to_guild.get(player_id)
        if guild_id:
            return self._guilds.get(guild_id)
        return None
    
    def search_guilds(
        self,
        faction: Optional[ShapeFaction] = None,
        min_level: int = 0,
        public_only: bool = True,
    ) -> List[Guild]:
        """Search for guilds."""
        results = []
        
        for guild in self._guilds.values():
            if public_only and not guild.public:
                continue
            if faction and guild.faction != faction:
                continue
            if guild.level < min_level:
                continue
            
            results.append(guild)
        
        # Sort by level descending
        results.sort(key=lambda g: g.level, reverse=True)
        return results
    
    def get_faction_standings(self) -> Dict[ShapeFaction, int]:
        """Get current faction standings."""
        return self._faction_points.copy()
    
    def add_faction_points(self, faction: ShapeFaction, points: int) -> None:
        """Add points to a faction."""
        if faction != ShapeFaction.NEUTRAL:
            self._faction_points[faction] += points
    
    def get_top_guilds(self, limit: int = 10) -> List[Guild]:
        """Get top guilds by level."""
        guilds = list(self._guilds.values())
        guilds.sort(key=lambda g: (g.level, g.stats.total_xp_earned), reverse=True)
        return guilds[:limit]
    
    def get_guilds_by_faction(self, faction: ShapeFaction) -> List[Guild]:
        """Get all guilds in a faction."""
        return [g for g in self._guilds.values() if g.faction == faction]
