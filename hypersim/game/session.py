"""Session wrapper tying dimension progression to the simulation loop."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from hypersim.engine.scene import Scene
from hypersim.engine.simulation import Simulation

from .dimensions import DEFAULT_DIMENSIONS, DimensionSpec, DimensionTrack
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

    @property
    def active_dimension(self) -> DimensionSpec:
        return self._active_dimension

    def set_dimension(self, dimension_id: str) -> DimensionSpec:
        """Jump to a specific dimension (respecting unlock state)."""
        self.progression.advance_to(dimension_id)
        self._active_dimension = self.dimensions.get(dimension_id)
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

    def describe(self) -> dict:
        """Return a snapshot of the session state (for UI or saves)."""
        return {
            "dimension": self._active_dimension.id,
            "unlocked": list(self.progression.unlocked_dimensions),
            "completed_nodes": list(self.progression.completed_nodes),
            "control_scope": self.control_scope(),
            "xp": self.progression.xp,
        }
