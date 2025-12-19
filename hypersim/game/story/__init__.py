"""Story and campaign system for HyperSim.

Features:
- Rich narrative exploring dimensional concepts
- NPCs with dialogue trees and personalities
- Multiple worlds/chapters with unique themes
- Lore collectibles and codex entries
- Story-driven progression
"""

from .campaign import Campaign, Chapter, StoryBeat
from .npc import NPC, NPCState, NPCManager
from .lore import LoreEntry, LoreCategory, Codex
from .dialogue_tree import DialogueNode, DialogueTree, DialogueChoice
from .cosmology import COSMIC_LORE, CosmicLoreEntry, CosmicEra, get_lore_for_dimension
from .dimensional_evolution import (
    DimensionalForm, DimensionTier, 
    FORMS_1D, FORMS_2D, FORMS_3D, ALL_DIMENSIONAL_FORMS,
    get_forms_for_dimension, get_starting_form, get_transcendent_form,
    get_available_forms
)

__all__ = [
    # Campaign
    "Campaign",
    "Chapter",
    "StoryBeat",
    # NPCs
    "NPC",
    "NPCState",
    "NPCManager",
    # Lore
    "LoreEntry",
    "LoreCategory",
    "Codex",
    # Dialogue
    "DialogueNode",
    "DialogueTree",
    "DialogueChoice",
    # Cosmology
    "COSMIC_LORE",
    "CosmicLoreEntry",
    "CosmicEra",
    "get_lore_for_dimension",
    # Dimensional Evolution
    "DimensionalForm",
    "DimensionTier",
    "FORMS_1D",
    "FORMS_2D",
    "FORMS_3D",
    "ALL_DIMENSIONAL_FORMS",
    "get_forms_for_dimension",
    "get_starting_form",
    "get_transcendent_form",
    "get_available_forms",
]
