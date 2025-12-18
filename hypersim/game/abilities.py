"""Ability state and gating."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Set


@dataclass
class AbilityState:
    """Track unlocked abilities."""

    unlocked: Set[str] = field(default_factory=set)

    def grant(self, ability: str) -> None:
        self.unlocked.add(ability)

    def grant_many(self, abilities: Iterable[str]) -> None:
        for ability in abilities:
            self.unlocked.add(ability)

    def has(self, ability: str) -> bool:
        return ability in self.unlocked

    def snapshot(self) -> Set[str]:
        """Return a copy for persistence."""
        return set(self.unlocked)
