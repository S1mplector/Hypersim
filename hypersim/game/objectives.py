"""Objective specs and mission tracking."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple


class ObjectiveType(str, Enum):
    REACH_DIMENSION = "reach_dimension"
    COLLECT = "collect"
    DEFEAT = "defeat"
    TRAVEL = "travel"
    INTERACT = "interact"
    CUSTOM_EVENT = "custom_event"


@dataclass(frozen=True)
class ObjectiveSpec:
    """Static description of an objective."""

    id: str
    type: ObjectiveType
    target: float = 1.0
    description: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectiveState:
    """Runtime state for an objective."""

    spec: ObjectiveSpec
    progress: float = 0.0
    completed: bool = False

    def apply_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Update progress from an event. Returns True if state changed."""
        if self.completed:
            return False

        changed = False
        spec = self.spec

        if spec.type == ObjectiveType.REACH_DIMENSION:
            if event_type == "dimension_changed" and data.get("dimension_id") == spec.params.get("dimension_id"):
                self.progress = spec.target
                self.completed = True
                return True

        elif spec.type == ObjectiveType.COLLECT:
            if event_type == "collect":
                item = spec.params.get("item")
                if item is None or item == data.get("item"):
                    amount = float(data.get("count", 1))
                    self.progress = min(spec.target, self.progress + amount)
                    changed = True

        elif spec.type == ObjectiveType.DEFEAT:
            if event_type == "defeat":
                tag = spec.params.get("tag")
                if tag is None or tag == data.get("tag"):
                    amount = float(data.get("count", 1))
                    self.progress = min(spec.target, self.progress + amount)
                    changed = True

        elif spec.type == ObjectiveType.TRAVEL:
            if event_type == "travel":
                distance = float(data.get("distance", 0.0))
                if distance > 0:
                    self.progress = min(spec.target, self.progress + distance)
                    changed = True

        elif spec.type == ObjectiveType.INTERACT:
            if event_type == "interact":
                target = spec.params.get("target")
                if target is None or target == data.get("target"):
                    self.progress = spec.target
                    self.completed = True
                    return True

        elif spec.type == ObjectiveType.CUSTOM_EVENT:
            expected_event = spec.params.get("event_type")
            if event_type == expected_event:
                value = float(data.get("value", 1.0))
                self.progress = min(spec.target, self.progress + value)
                changed = True

        if not self.completed and self.progress >= spec.target:
            self.completed = True
            changed = True
        return changed


@dataclass
class MissionState:
    """Runtime mission with objective progress."""

    node_id: str
    objectives: Dict[str, ObjectiveState]
    completed: bool = False

    @classmethod
    def from_specs(cls, node_id: str, specs: Iterable[ObjectiveSpec], progress_snapshot: Optional[Dict[str, float]] = None) -> "MissionState":
        progress_snapshot = progress_snapshot or {}
        objectives: Dict[str, ObjectiveState] = {}
        for spec in specs:
            progress = float(progress_snapshot.get(spec.id, 0.0))
            completed = progress >= spec.target
            objectives[spec.id] = ObjectiveState(spec=spec, progress=progress, completed=completed)
        completed = objectives and all(o.completed for o in objectives.values())
        return cls(node_id=node_id, objectives=objectives, completed=completed)

    def apply_event(self, event_type: str, data: Dict[str, Any]) -> Tuple[bool, bool]:
        """Apply an event to objectives. Returns (changed, now_completed)."""
        if self.completed:
            return False, True
        changed = False
        for obj in self.objectives.values():
            if obj.apply_event(event_type, data):
                changed = True
        if not self.completed and self.objectives and all(o.completed for o in self.objectives.values()):
            self.completed = True
            changed = True
        return changed, self.completed

    def snapshot(self) -> Dict[str, float]:
        """Return progress snapshot for persistence."""
        return {oid: obj.progress for oid, obj in self.objectives.items()}


class MissionTracker:
    """Manage the currently active mission and objective updates."""

    def __init__(self, campaign) -> None:
        self.campaign = campaign
        self.active: Optional[MissionState] = None

    def activate(self, node_id: str, progress_snapshot: Optional[Dict[str, float]] = None) -> MissionState:
        node = self.campaign.node(node_id)
        self.active = MissionState.from_specs(node_id, node.objectives, progress_snapshot)
        return self.active

    def clear(self) -> None:
        self.active = None

    def record_event(self, event_type: str, data: Dict[str, Any]) -> Tuple[bool, bool]:
        """Send an event to the active mission. Returns (changed, completed)."""
        if not self.active:
            return False, False
        return self.active.apply_event(event_type, data)
