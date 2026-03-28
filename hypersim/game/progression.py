"""Progression, campaign, and unlock tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set

from .dimensions import DimensionTrack, DimensionSpec


@dataclass
class ProgressionState:
    """Track player/campaign progression across dimensions and missions."""

    current_dimension: str = "1d"
    unlocked_dimensions: List[str] = field(default_factory=lambda: ["1d"])
    current_world_id: str = "tutorial_1d"
    unlocked_worlds: List[str] = field(default_factory=lambda: ["tutorial_1d"])
    completed_worlds: Set[str] = field(default_factory=set)
    completed_nodes: Set[str] = field(default_factory=set)
    xp: int = 0
    profile_name: str = "default"
    active_node_id: Optional[str] = None
    mission_progress: Dict[str, Dict[str, float]] = field(default_factory=dict)
    world_objective_progress: Dict[str, Dict[str, float]] = field(default_factory=dict)
    unlocked_abilities: Set[str] = field(default_factory=set)
    intro_impulse: str = ""              # Chosen impulse from intro (lean/listen/hesitate)
    lineage_ritual_state: str = "complete"  # complete for legacy saves; fresh games begin at "cohere"
    lineage_direction: str = ""         # First claimed direction on the Line (forward/backward)
    terminus_seen: bool = False          # Whether the 1D Terminus cutscene was seen
    shift_tutorial_done: bool = False    # Whether the 1D shift tutorial fired
    outsider_cutscene_played: bool = False  # First return-to-lower-dim vignette
    shown_dimension_vignettes: Set[str] = field(default_factory=set)  # Intro vignettes per dimension
    
    # 4D Evolution tracking
    evolution_form: int = 0  # PolytopeForm enum value
    evolution_xp: int = 0
    evolution_forms_unlocked: List[int] = field(default_factory=lambda: [0])

    def __post_init__(self) -> None:
        if self.current_dimension not in self.unlocked_dimensions:
            self.unlocked_dimensions.append(self.current_dimension)
        if self.current_world_id and self.current_world_id not in self.unlocked_worlds:
            self.unlocked_worlds.append(self.current_world_id)

    def is_unlocked(self, dimension_id: str) -> bool:
        return dimension_id in self.unlocked_dimensions

    def unlock_dimension(self, dimension_id: str) -> None:
        if dimension_id not in self.unlocked_dimensions:
            self.unlocked_dimensions.append(dimension_id)

    def advance_to(self, dimension_id: str) -> None:
        if not self.is_unlocked(dimension_id):
            self.unlock_dimension(dimension_id)
        self.current_dimension = dimension_id

    def is_world_unlocked(self, world_id: str) -> bool:
        return world_id in self.unlocked_worlds

    def unlock_world(self, world_id: str) -> None:
        if world_id not in self.unlocked_worlds:
            self.unlocked_worlds.append(world_id)

    def advance_to_world(self, world_id: str) -> None:
        if world_id:
            self.unlock_world(world_id)
            self.current_world_id = world_id

    def record_world_completion(self, world_id: str) -> bool:
        already_completed = world_id in self.completed_worlds
        self.completed_worlds.add(world_id)
        return not already_completed

    def record_completion(self, node_id: str) -> None:
        self.completed_nodes.add(node_id)
        if self.active_node_id == node_id:
            self.active_node_id = None
        self.mission_progress.pop(node_id, None)

    def highest_unlocked_order(self, track: DimensionTrack) -> int:
        return max(track.get(d).order for d in self.unlocked_dimensions)

    def set_active_node(self, node_id: Optional[str]) -> None:
        self.active_node_id = node_id

    def grant_abilities(self, abilities: Iterable[str]) -> None:
        for ability in abilities:
            self.unlocked_abilities.add(ability)

    def has_ability(self, ability: str) -> bool:
        return ability in self.unlocked_abilities


@dataclass(frozen=True)
class CampaignNode:
    """A mission or milestone in the campaign."""

    id: str
    dimension_id: str
    title: str
    description: str
    prerequisites: List[str] = field(default_factory=list)
    rewards: List[str] = field(default_factory=list)
    objectives: List["ObjectiveSpec"] = field(default_factory=list)


class CampaignState:
    """Simple campaign graph with prerequisite checking."""

    def __init__(self, nodes: Iterable[CampaignNode], track: DimensionTrack):
        self._nodes = {node.id: node for node in nodes}
        self.track = track

    def node(self, node_id: str) -> CampaignNode:
        if node_id not in self._nodes:
            raise KeyError(f"campaign node '{node_id}' not found")
        return self._nodes[node_id]

    def available(self, progression: ProgressionState) -> List[CampaignNode]:
        ready: List[CampaignNode] = []
        for node in self._nodes.values():
            if node.id in progression.completed_nodes:
                continue
            if not progression.is_unlocked(node.dimension_id):
                continue
            if any(req not in progression.completed_nodes for req in node.prerequisites):
                continue
            ready.append(node)
        return sorted(ready, key=lambda n: self.track.get(n.dimension_id).order)

    def complete(self, node_id: str, progression: ProgressionState) -> CampaignNode:
        node = self.node(node_id)
        if any(req not in progression.completed_nodes for req in node.prerequisites):
            raise ValueError(f"prerequisites not met for node '{node_id}'")
        progression.record_completion(node_id)
        # Auto-unlock the next dimension along the track when finishing a node.
        next_dim = self.track.next(node.dimension_id)
        if next_dim:
            progression.unlock_dimension(next_dim.id)
        return node

    def all_nodes(self) -> List[CampaignNode]:
        return list(self._nodes.values())
