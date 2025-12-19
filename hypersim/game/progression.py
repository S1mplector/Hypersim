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
    completed_nodes: Set[str] = field(default_factory=set)
    xp: int = 0
    profile_name: str = "default"
    active_node_id: Optional[str] = None
    mission_progress: Dict[str, Dict[str, float]] = field(default_factory=dict)
    unlocked_abilities: Set[str] = field(default_factory=set)
    
    # 4D Evolution tracking
    evolution_form: int = 0  # PolytopeForm enum value
    evolution_xp: int = 0
    evolution_forms_unlocked: List[int] = field(default_factory=lambda: [0])

    def __post_init__(self) -> None:
        if self.current_dimension not in self.unlocked_dimensions:
            self.unlocked_dimensions.append(self.current_dimension)

    def is_unlocked(self, dimension_id: str) -> bool:
        return dimension_id in self.unlocked_dimensions

    def unlock_dimension(self, dimension_id: str) -> None:
        if dimension_id not in self.unlocked_dimensions:
            self.unlocked_dimensions.append(dimension_id)

    def advance_to(self, dimension_id: str) -> None:
        if not self.is_unlocked(dimension_id):
            self.unlock_dimension(dimension_id)
        self.current_dimension = dimension_id

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
