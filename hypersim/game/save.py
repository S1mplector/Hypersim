"""Persistence helpers for progression state."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .progression import ProgressionState


DEFAULT_SAVE_PATH = Path("game_save.json")


def save_progression(prog: ProgressionState, path: Path | str = DEFAULT_SAVE_PATH) -> None:
    """Persist progression to disk as JSON."""
    data = {
        "current_dimension": prog.current_dimension,
        "unlocked_dimensions": list(prog.unlocked_dimensions),
        "current_world_id": prog.current_world_id,
        "unlocked_worlds": list(prog.unlocked_worlds),
        "completed_worlds": list(prog.completed_worlds),
        "completed_nodes": list(prog.completed_nodes),
        "xp": prog.xp,
        "profile_name": prog.profile_name,
        "active_node_id": prog.active_node_id,
        "mission_progress": prog.mission_progress,
        "world_objective_progress": prog.world_objective_progress,
        "unlocked_abilities": list(prog.unlocked_abilities),
        "intro_impulse": prog.intro_impulse,
        "lineage_ritual_state": prog.lineage_ritual_state,
        "lineage_direction": prog.lineage_direction,
        "terminus_seen": prog.terminus_seen,
        "shift_tutorial_done": prog.shift_tutorial_done,
        "outsider_cutscene_played": prog.outsider_cutscene_played,
        "shown_dimension_vignettes": list(prog.shown_dimension_vignettes),
        # 4D Evolution
        "evolution_form": prog.evolution_form,
        "evolution_xp": prog.evolution_xp,
        "evolution_forms_unlocked": list(prog.evolution_forms_unlocked),
    }
    path = Path(path)
    path.write_text(json.dumps(data, indent=2))


def load_progression(path: Path | str = DEFAULT_SAVE_PATH) -> Optional[ProgressionState]:
    """Load progression from JSON if the file exists."""
    path = Path(path)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return ProgressionState(
        current_dimension=data.get("current_dimension", "1d"),
        unlocked_dimensions=data.get("unlocked_dimensions", ["1d"]),
        current_world_id=data.get("current_world_id", "tutorial_1d"),
        unlocked_worlds=data.get("unlocked_worlds", ["tutorial_1d"]),
        completed_worlds=set(data.get("completed_worlds", [])),
        completed_nodes=set(data.get("completed_nodes", [])),
        xp=int(data.get("xp", 0)),
        profile_name=data.get("profile_name", "default"),
        active_node_id=data.get("active_node_id"),
        mission_progress=data.get("mission_progress", {}),
        world_objective_progress=data.get("world_objective_progress", {}),
        unlocked_abilities=set(data.get("unlocked_abilities", [])),
        intro_impulse=data.get("intro_impulse", ""),
        lineage_ritual_state=data.get("lineage_ritual_state", "complete"),
        lineage_direction=data.get("lineage_direction", ""),
        terminus_seen=data.get("terminus_seen", False),
        shift_tutorial_done=data.get("shift_tutorial_done", False),
        outsider_cutscene_played=data.get("outsider_cutscene_played", False),
        shown_dimension_vignettes=set(data.get("shown_dimension_vignettes", [])),
        # 4D Evolution
        evolution_form=data.get("evolution_form", 0),
        evolution_xp=data.get("evolution_xp", 0),
        evolution_forms_unlocked=data.get("evolution_forms_unlocked", [0]),
    )
