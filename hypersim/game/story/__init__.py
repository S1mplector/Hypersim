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
]
