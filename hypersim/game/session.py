"""Session wrapper tying dimension progression to the simulation loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from hypersim.engine.scene import Scene
from hypersim.engine.simulation import Simulation

from .abilities import AbilityState
from .dimensions import DEFAULT_DIMENSIONS, DimensionSpec, DimensionTrack
from .objectives import MissionTracker
from .progression import CampaignState, ProgressionState


SessionHook = Callable[[DimensionSpec, Scene], None]


@dataclass
class GameSession:
    """Manage a player's session, dimension state, and simulation runtime."""

    dimensions: DimensionTrack = None
    progression: ProgressionState = None
    campaign: Optional[CampaignState] = None
    scene: Scene = None
    simulation: Simulation = None
    abilities: AbilityState = None
    on_dimension_changed: Optional[SessionHook] = None

    def __post_init__(self) -> None:
        if self.dimensions is None:
            self.dimensions = DimensionTrack(DEFAULT_DIMENSIONS)
        if self.progression is None:
            start_dim = self.dimensions.first().id
            self.progression = ProgressionState(
                current_dimension=start_dim,
                unlocked_dimensions=[start_dim],
            )
        if self.scene is None:
            self.scene = Scene()
        if self.simulation is None:
            self.simulation = Simulation(self.scene)
        self._active_dimension: DimensionSpec = self.dimensions.get(self.progression.current_dimension)
        if self.abilities is None:
            self.abilities = AbilityState()
        if self.progression.unlocked_abilities:
            self.abilities.grant_many(self.progression.unlocked_abilities)
        self._grant_all_unlocked_dimensions()

        self.mission_tracker: Optional[MissionTracker] = MissionTracker(self.campaign) if self.campaign else None
        if self.mission_tracker and self.progression.active_node_id:
            snapshot = self.progression.mission_progress.get(self.progression.active_node_id, {})
            self.mission_tracker.activate(self.progression.active_node_id, snapshot)
        elif self.mission_tracker:
            self.auto_select_mission()
        # Register initial dimension for objectives
        if self.mission_tracker:
            self.record_event("dimension_changed", dimension_id=self._active_dimension.id)

    @property
    def active_dimension(self) -> DimensionSpec:
        return self._active_dimension

    def set_dimension(self, dimension_id: str) -> DimensionSpec:
        """Jump to a specific dimension (respecting unlock state)."""
        self.progression.advance_to(dimension_id)
        self._active_dimension = self.dimensions.get(dimension_id)
        self._grant_dimension_abilities(self._active_dimension)
        self.record_event("dimension_changed", dimension_id=dimension_id)
        if self.on_dimension_changed:
            self.on_dimension_changed(self._active_dimension, self.scene)
        return self._active_dimension

    def ascend(self) -> Optional[DimensionSpec]:
        """Ascend to the next dimension on the track (if it exists)."""
        next_dim = self.dimensions.next(self._active_dimension.id)
        if not next_dim:
            return None
        return self.set_dimension(next_dim.id)

    def ascend_if_ready(self) -> bool:
        """Ascend if the next dimension is already unlocked."""
        next_dim = self.dimensions.next(self._active_dimension.id)
        if not next_dim:
            return False
        if not self.progression.is_unlocked(next_dim.id):
            return False
        self.set_dimension(next_dim.id)
        return True

    def run_for(self, duration: float | None = None) -> None:
        """Run the underlying simulation."""
        self.simulation.run(duration)

    def control_scope(self) -> list[str]:
        """Return ids of dimensions the active one can control."""
        return [
            spec.id
            for spec in self.dimensions.all()
            if self._active_dimension.dominates(spec)
        ]

    # ------------------------------------------------------------------
    # Abilities
    # ------------------------------------------------------------------
    def _grant_dimension_abilities(self, spec: DimensionSpec) -> None:
        """Grant abilities tied to the provided dimension."""
        if spec.abilities:
            self.abilities.grant_many(spec.abilities)
            self.progression.grant_abilities(spec.abilities)

    def _grant_all_unlocked_dimensions(self) -> None:
        """Sync abilities for all unlocked dimensions (useful on load)."""
        for dim_id in self.progression.unlocked_dimensions:
            spec = self.dimensions.get(dim_id)
            self._grant_dimension_abilities(spec)

    # ------------------------------------------------------------------
    # Missions / Objectives
    # ------------------------------------------------------------------
    def auto_select_mission(self) -> None:
        """Choose the first available mission, preferring current dimension."""
        if not self.mission_tracker:
            return
        available = self.campaign.available(self.progression) if self.campaign else []
        if not available:
            self.progression.set_active_node(None)
            self.mission_tracker.clear()
            return
        same_dim = [n for n in available if n.dimension_id == self._active_dimension.id]
        chosen = same_dim[0] if same_dim else available[0]
        self.set_active_mission(chosen.id)

    def set_active_mission(self, node_id: str) -> None:
        """Activate a mission by id."""
        if not self.mission_tracker:
            return
        snapshot = self.progression.mission_progress.get(node_id, {})
        self.mission_tracker.activate(node_id, snapshot)
        self.progression.set_active_node(node_id)

    def record_event(self, event_type: str, **data) -> None:
        """Record a gameplay event for mission tracking."""
        if not self.mission_tracker or not self.mission_tracker.active:
            return
        changed, completed = self.mission_tracker.record_event(event_type, data)
        if changed:
            self._persist_mission_progress()
        if completed:
            self._complete_active_mission()

    def _persist_mission_progress(self) -> None:
        if not self.mission_tracker or not self.mission_tracker.active:
            return
        node_id = self.mission_tracker.active.node_id
        self.progression.mission_progress[node_id] = self.mission_tracker.active.snapshot()

    def _complete_active_mission(self) -> None:
        """Handle mission completion bookkeeping."""
        if not self.mission_tracker or not self.mission_tracker.active:
            return
        node_id = self.mission_tracker.active.node_id
        if self.campaign:
            node = self.campaign.complete(node_id, self.progression)
            # Apply rewards (abilities or simple xp tokens)
            for reward in node.rewards:
                if reward.startswith("ability:"):
                    ability_name = reward.split("ability:", 1)[1]
                    self.abilities.grant(ability_name)
                    self.progression.grant_abilities([ability_name])
                elif reward.startswith("xp:"):
                    try:
                        self.progression.xp += int(reward.split("xp:", 1)[1])
                    except ValueError:
                        pass
        self.progression.set_active_node(None)
        self.mission_tracker.clear()
        # Grant abilities for newly unlocked dimensions (if any)
        self._grant_all_unlocked_dimensions()
        # Auto-select next mission if available
        self.auto_select_mission()

    def describe(self) -> dict:
        """Return a snapshot of the session state (for UI or saves)."""
        return {
            "dimension": self._active_dimension.id,
            "unlocked": list(self.progression.unlocked_dimensions),
            "completed_nodes": list(self.progression.completed_nodes),
            "control_scope": self.control_scope(),
            "xp": self.progression.xp,
            "abilities": list(self.abilities.unlocked),
            "active_mission": self.progression.active_node_id,
        }
