"""Story Encounters - Scripted combat encounters tied to story progression.

This module defines story-driven combat encounters that:
1. Trigger at specific story beats
2. Have pre/post-battle dialogue
3. Affect story route based on outcome
4. Unlock progression rewards
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable

from .dimensional_combat import CombatDimension
from .dimensional_integration import DimensionalEncounterConfig
from .core import CombatResult


class StoryEncounterType(Enum):
    """Types of story encounters."""
    TUTORIAL = auto()      # Teaching mechanic
    STORY_BEAT = auto()    # Part of main story
    BOSS = auto()          # Chapter boss
    OPTIONAL = auto()      # Side content
    SECRET = auto()        # Hidden encounter


@dataclass
class StoryEncounter:
    """A story-driven combat encounter."""
    id: str
    enemy_id: str
    dimension: CombatDimension
    encounter_type: StoryEncounterType
    
    # Story context
    title: str = ""
    description: str = ""
    chapter: str = "1d"
    
    # Dialogue
    pre_battle_dialogue: List[str] = field(default_factory=list)
    victory_dialogue: List[str] = field(default_factory=list)
    spare_dialogue: List[str] = field(default_factory=list)
    defeat_dialogue: List[str] = field(default_factory=list)
    
    # Requirements
    requires_flags: List[str] = field(default_factory=list)
    requires_encounters: List[str] = field(default_factory=list)
    
    # Rewards and effects
    sets_flags: List[str] = field(default_factory=list)
    xp_bonus: int = 0
    gold_bonus: int = 0
    unlocks_area: Optional[str] = None
    unlocks_dimension: Optional[str] = None
    
    # Combat modifiers
    difficulty_modifier: float = 1.0
    can_flee: bool = True
    
    def to_encounter_config(self) -> DimensionalEncounterConfig:
        """Convert to encounter config."""
        return DimensionalEncounterConfig(
            enemy_id=self.enemy_id,
            dimension=self.dimension,
            can_flee=self.can_flee,
            is_boss=self.encounter_type == StoryEncounterType.BOSS,
            is_scripted=True,
            xp_bonus=self.xp_bonus,
            gold_bonus=self.gold_bonus,
            unlocks_dimension=self.unlocks_dimension,
        )


# ============================================================================
# 1D STORY ENCOUNTERS - THE LINE
# ============================================================================

ENCOUNTERS_1D: Dict[str, StoryEncounter] = {
    # === TUTORIAL: First encounter ===
    "1d_tutorial_point": StoryEncounter(
        id="1d_tutorial_point",
        enemy_id="point_spirit",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.TUTORIAL,
        title="First Contact",
        description="Your first encounter with a being of pure existence.",
        chapter="1d",
        pre_battle_dialogue=[
            "* Something flickers in the infinite line before you.",
            "* A Point Spirit - a consciousness without extension.",
            "* It seems curious about your presence.",
            "* [TUTORIAL: Use [1-4] to shift your perception during combat!]",
        ],
        victory_dialogue=[
            "* The Point Spirit fades away.",
            "* You feel its essence disperse into the line.",
            "* There's a strange weight to this victory...",
        ],
        spare_dialogue=[
            "* The Point Spirit glows with gratitude.",
            "* \"You... saw me. That's all I ever wanted.\"",
            "* It fades peacefully, leaving behind a warm light.",
            "* [You gained more G from sparing!]",
        ],
        sets_flags=["first_encounter_complete"],
        xp_bonus=2,
        difficulty_modifier=0.6,
    ),
    
    # === STORY: The confused traveler ===
    "1d_line_walker_first": StoryEncounter(
        id="1d_line_walker_first",
        enemy_id="line_walker",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.STORY_BEAT,
        title="The Walker's Confusion",
        description="A being that knows only forward and backward.",
        chapter="1d",
        requires_flags=["first_encounter_complete"],
        pre_battle_dialogue=[
            "* A Line Walker blocks your path!",
            "* It stares at you with confusion.",
            "* \"You... you're not from the Line, are you?\"",
            "* \"How do you have... WIDTH?\"",
        ],
        victory_dialogue=[
            "* The Line Walker collapses.",
            "* Its last thought: wondering about dimensions it could never perceive.",
        ],
        spare_dialogue=[
            "* The Line Walker steps aside, amazed.",
            "* \"Maybe... there IS more than forward and back.\"",
            "* \"Will you... show me someday?\"",
            "* [The Line Walker might remember this kindness...]",
        ],
        sets_flags=["met_line_walker"],
    ),
    
    # === STORY: The forward zealot ===
    "1d_sentinel_encounter": StoryEncounter(
        id="1d_sentinel_encounter",
        enemy_id="forward_sentinel",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.STORY_BEAT,
        title="Guardian of Forward",
        description="A zealot who believes only in progress.",
        chapter="1d",
        requires_flags=["met_line_walker"],
        pre_battle_dialogue=[
            "* \"HALT!\"",
            "* A Forward Sentinel blocks your path aggressively.",
            "* \"You reek of... backward. Of hesitation.\"",
            "* \"FORWARD IS THE ONLY WAY!\"",
        ],
        victory_dialogue=[
            "* The Sentinel falls... forward.",
            "* Even in defeat, it refused to look back.",
        ],
        spare_dialogue=[
            "* The Sentinel pauses, considering.",
            "* \"Perhaps... some paths do fork.\"",
            "* \"Go, then. Find your own forward.\"",
        ],
        sets_flags=["passed_sentinel"],
        difficulty_modifier=1.1,
    ),
    
    # === STORY: The void philosopher ===
    "1d_void_echo_encounter": StoryEncounter(
        id="1d_void_echo_encounter",
        enemy_id="void_echo",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.STORY_BEAT,
        title="Echoes from Nothing",
        description="A being from the backward void speaks in riddles.",
        chapter="1d",
        pre_battle_dialogue=[
            "* Something resonates from the darkness behind you.",
            "* A Void Echo manifests - a memory of what came before.",
            "* \"Before the Line... there was no Line.\"",
            "* \"Before forward... was there backward?\"",
            "* \"Before existence... was there... you?\"",
        ],
        victory_dialogue=[
            "* The Echo dissipates into silence.",
            "* Its questions hang in the void, unanswered.",
        ],
        spare_dialogue=[
            "* The Echo smiles - somehow, without a face.",
            "* \"You understand. Nothing is the canvas.\"",
            "* \"On nothing, anything can be drawn.\"",
            "* \"Even you.\"",
        ],
        sets_flags=["understood_void"],
    ),
    
    # === STORY: The toll keeper ===
    "1d_toll_collector_encounter": StoryEncounter(
        id="1d_toll_collector_encounter",
        enemy_id="toll_collector",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.STORY_BEAT,
        title="Toll of the Midpoint",
        description="A playful gatekeeper demands payment.",
        chapter="1d",
        requires_flags=["passed_sentinel"],
        pre_battle_dialogue=[
            "* You've reached the Midpoint Station.",
            "* A Toll Collector blocks the way, grinning.",
            "* \"Toll for passage! One riddle, one fight, or one fortune!\"",
            "* \"What'll it be, traveler from beyond?\"",
        ],
        victory_dialogue=[
            "* The Toll Collector's coins scatter.",
            "* \"Ow! Okay, okay, you pass! Cheapskate...\"",
        ],
        spare_dialogue=[
            "* The Toll Collector bows with a flourish.",
            "* \"A customer who GETS it! Please, pass freely!\"",
            "* \"Come back anytime! I have MORE riddles!\"",
        ],
        sets_flags=["passed_midpoint"],
        gold_bonus=5,
    ),
    
    # === BOSS: Segment Guardian ===
    "1d_boss_segment_guardian": StoryEncounter(
        id="1d_boss_segment_guardian",
        enemy_id="segment_guardian",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.BOSS,
        title="The Boundary Keeper",
        description="The guardian of the passage to 2D.",
        chapter="1d",
        requires_flags=["passed_midpoint"],
        pre_battle_dialogue=[
            "* You've reached the Endpoint.",
            "* A massive presence blocks the way to the second dimension.",
            "* The SEGMENT GUARDIAN stands before you!",
            "* \"So. You seek to perceive WIDTH.\"",
            "* \"To expand beyond the sacred Line.\"",
            "* \"Only the WORTHY may pass!\"",
            "* \"PROVE YOUR UNDERSTANDING OF DIMENSION!\"",
        ],
        victory_dialogue=[
            "* The Segment Guardian crumbles.",
            "* \"You... have the strength... but do you have... the vision?\"",
            "* The boundary weakens. The way to 2D opens.",
            "* But something feels hollow about this victory...",
        ],
        spare_dialogue=[
            "* The Segment Guardian nods with respect.",
            "* \"You understand. Force is not the only dimension of power.\"",
            "* \"Wisdom. Patience. These are higher dimensions of the soul.\"",
            "* \"Go forth. Learn what WIDTH truly means.\"",
            "* \"And remember: every dimension builds on the last.\"",
            "* The way to 2D opens with the Guardian's blessing!",
        ],
        defeat_dialogue=[
            "* You fall before the Guardian's might.",
            "* \"Not yet. You are not ready for more dimensions.\"",
            "* \"Return when you understand the LINE.\"",
        ],
        sets_flags=["defeated_segment_guardian", "1d_complete"],
        xp_bonus=20,
        gold_bonus=15,
        unlocks_dimension="2d",
        unlocks_area="the_plane",
        can_flee=False,
        difficulty_modifier=1.3,
    ),
    
    # === SECRET: The origin point ===
    "1d_secret_origin": StoryEncounter(
        id="1d_secret_origin",
        enemy_id="point_spirit",
        dimension=CombatDimension.ONE_D,
        encounter_type=StoryEncounterType.SECRET,
        title="The Origin Point",
        description="A secret encounter at the very beginning of the Line.",
        chapter="1d",
        pre_battle_dialogue=[
            "* You've traveled all the way back to the Origin.",
            "* Here, where the Line began...",
            "* An ancient Point Spirit awakens.",
            "* \"You... returned. To the beginning.\"",
            "* \"Most only look forward. You looked back.\"",
            "* \"Let me show you... what was before.\"",
        ],
        spare_dialogue=[
            "* The ancient Spirit shares its memory.",
            "* You see: before the Line, there was a Point.",
            "* Before the Point, there was Nothing.",
            "* And from Nothing... came Everything.",
            "* \"Remember this. It will matter... later.\"",
            "* [You gained secret knowledge!]",
        ],
        sets_flags=["secret_origin_knowledge"],
        xp_bonus=10,
        gold_bonus=20,
        difficulty_modifier=0.8,
    ),
}


# ============================================================================
# ENCOUNTER MANAGER
# ============================================================================

class StoryEncounterManager:
    """Manages story encounters and their progression."""
    
    def __init__(self):
        self.encounters: Dict[str, StoryEncounter] = {}
        self.completed_encounters: set = set()
        self.story_flags: set = set()
        
        # Load all encounters
        self.encounters.update(ENCOUNTERS_1D)
        # Add more dimensions here as they're implemented
    
    def can_trigger(self, encounter_id: str) -> bool:
        """Check if an encounter can be triggered."""
        if encounter_id not in self.encounters:
            return False
        
        encounter = self.encounters[encounter_id]
        
        # Check required flags
        for flag in encounter.requires_flags:
            if flag not in self.story_flags:
                return False
        
        # Check required encounters
        for req_enc in encounter.requires_encounters:
            if req_enc not in self.completed_encounters:
                return False
        
        return True
    
    def get_encounter(self, encounter_id: str) -> Optional[StoryEncounter]:
        """Get an encounter by ID."""
        return self.encounters.get(encounter_id)
    
    def complete_encounter(self, encounter_id: str, result: CombatResult) -> List[str]:
        """Mark an encounter as complete and apply effects.
        
        Returns list of newly set flags.
        """
        if encounter_id not in self.encounters:
            return []
        
        encounter = self.encounters[encounter_id]
        self.completed_encounters.add(encounter_id)
        
        # Set flags based on outcome
        new_flags = []
        for flag in encounter.sets_flags:
            if flag not in self.story_flags:
                self.story_flags.add(flag)
                new_flags.append(flag)
        
        # Add outcome-specific flags
        if result == CombatResult.SPARE:
            spare_flag = f"{encounter_id}_spared"
            self.story_flags.add(spare_flag)
            new_flags.append(spare_flag)
        elif result == CombatResult.VICTORY:
            kill_flag = f"{encounter_id}_killed"
            self.story_flags.add(kill_flag)
            new_flags.append(kill_flag)
        
        return new_flags
    
    def get_available_encounters(self, chapter: str) -> List[StoryEncounter]:
        """Get all available encounters for a chapter."""
        available = []
        for enc in self.encounters.values():
            if enc.chapter == chapter and self.can_trigger(enc.id):
                if enc.id not in self.completed_encounters:
                    available.append(enc)
        return available
    
    def get_next_story_encounter(self, chapter: str) -> Optional[StoryEncounter]:
        """Get the next story encounter for a chapter."""
        available = self.get_available_encounters(chapter)
        
        # Prioritize by type
        for enc_type in [StoryEncounterType.TUTORIAL, StoryEncounterType.STORY_BEAT, StoryEncounterType.BOSS]:
            for enc in available:
                if enc.encounter_type == enc_type:
                    return enc
        
        return available[0] if available else None
    
    def has_flag(self, flag: str) -> bool:
        """Check if a story flag is set."""
        return flag in self.story_flags
    
    def set_flag(self, flag: str) -> None:
        """Set a story flag."""
        self.story_flags.add(flag)
    
    def get_chapter_progress(self, chapter: str) -> float:
        """Get completion percentage for a chapter (0-1)."""
        chapter_encounters = [e for e in self.encounters.values() if e.chapter == chapter]
        if not chapter_encounters:
            return 0.0
        
        completed = sum(1 for e in chapter_encounters if e.id in self.completed_encounters)
        return completed / len(chapter_encounters)


# Singleton instance
_encounter_manager: Optional[StoryEncounterManager] = None


def get_encounter_manager() -> StoryEncounterManager:
    """Get or create the story encounter manager."""
    global _encounter_manager
    if _encounter_manager is None:
        _encounter_manager = StoryEncounterManager()
    return _encounter_manager
