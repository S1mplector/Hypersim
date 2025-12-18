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
        "completed_nodes": list(prog.completed_nodes),
        "xp": prog.xp,
        "profile_name": prog.profile_name,
        "active_node_id": prog.active_node_id,
        "mission_progress": prog.mission_progress,
        "unlocked_abilities": list(prog.unlocked_abilities),
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
        completed_nodes=set(data.get("completed_nodes", [])),
        xp=int(data.get("xp", 0)),
        profile_name=data.get("profile_name", "default"),
        active_node_id=data.get("active_node_id"),
        mission_progress=data.get("mission_progress", {}),
        unlocked_abilities=set(data.get("unlocked_abilities", [])),
    )
