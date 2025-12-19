"""NPC system with personalities and dialogue."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.entity import Entity


class NPCState(Enum):
    """State of an NPC."""
    IDLE = "idle"
    TALKING = "talking"
    FOLLOWING = "following"
    WAITING = "waiting"
    QUEST = "quest"
    GONE = "gone"


class NPCPersonality(Enum):
    """Personality archetypes."""
    MENTOR = "mentor"         # Teaches and guides
    COMPANION = "companion"   # Friendly, follows player
    SAGE = "sage"             # Mysterious, speaks in riddles
    SCIENTIST = "scientist"   # Analytical, explains mechanics
    GUARDIAN = "guardian"     # Protective, warns of danger
    TRICKSTER = "trickster"   # Playful, tests the player


@dataclass
class NPCDialogueState:
    """Tracks conversation progress with an NPC."""
    conversations_had: int = 0
    last_dialogue_id: Optional[str] = None
    topics_discussed: List[str] = field(default_factory=list)
    affinity: int = 0  # Relationship level
    gifts_given: int = 0


@dataclass
class NPC:
    """A non-player character."""
    id: str
    name: str
    title: str = ""
    description: str = ""
    
    # Personality
    personality: NPCPersonality = NPCPersonality.COMPANION
    native_dimension: str = "1d"
    
    # Visual
    color: tuple = (200, 200, 255)
    symbol: str = "◆"
    portrait_key: Optional[str] = None
    
    # Behavior
    state: NPCState = NPCState.IDLE
    can_follow: bool = False
    follows_to_dimensions: List[str] = field(default_factory=list)
    
    # Dialogue
    greeting_dialogue: Optional[str] = None
    dialogue_options: Dict[str, str] = field(default_factory=dict)  # topic -> dialogue_id
    
    # Position (if spawned)
    position: np.ndarray = field(default_factory=lambda: np.zeros(4))
    current_dimension: Optional[str] = None
    entity_id: Optional[str] = None
    
    # Backstory and quotes
    backstory: str = ""
    idle_quotes: List[str] = field(default_factory=list)
    
    def get_greeting(self, player_affinity: int) -> str:
        """Get appropriate greeting based on relationship."""
        if player_affinity < 0:
            return f"{self.name} regards you coldly."
        elif player_affinity == 0:
            return f"{self.name} notices your approach."
        elif player_affinity < 50:
            return f"{self.name} nods in recognition."
        else:
            return f"{self.name} greets you warmly."


# Pre-defined NPCs for the campaign
CAMPAIGN_NPCS: Dict[str, NPC] = {
    # =========================================================================
    # ECHO - The First Friend (1D native, follows through all dimensions)
    # =========================================================================
    "echo": NPC(
        id="echo",
        name="Echo",
        title="The Resonance",
        description="Another being trapped on the line. Echo has been here longer than they can remember.",
        personality=NPCPersonality.COMPANION,
        native_dimension="1d",
        color=(150, 200, 255),
        symbol="◇",
        can_follow=True,
        follows_to_dimensions=["1d", "2d", "3d", "4d"],
        backstory="""Echo doesn't remember a time before the line. They have always 
        existed here, bouncing between the same two points, hearing only the faint 
        vibrations of others passing by. When you appeared, Echo felt something 
        different - a resonance. Perhaps together, you can find what lies beyond.""",
        idle_quotes=[
            "The line stretches forever... or does it?",
            "I've heard whispers of beings with TWO directions of movement.",
            "Sometimes I feel like there's more to existence than left and right.",
            "Stay close. The Blockers hunt alone.",
            "Can you hear it? The hum of the portal...",
        ],
        greeting_dialogue="echo_greeting",
        dialogue_options={
            "who_are_you": "echo_about",
            "this_place": "echo_about_line",
            "dimensions": "echo_dimensions",
            "portal": "echo_portal",
            "follow": "echo_follow",
        },
    ),
    
    # =========================================================================
    # VECTOR - The 2D Native (Flatland scholar)
    # =========================================================================
    "vector": NPC(
        id="vector",
        name="Vector",
        title="The Planar Sage",
        description="A native of Flatland who has dedicated their existence to understanding dimensions.",
        personality=NPCPersonality.SCIENTIST,
        native_dimension="2d",
        color=(100, 255, 150),
        symbol="△",
        can_follow=True,
        follows_to_dimensions=["2d", "3d", "4d"],
        backstory="""Vector is a Triangle - considered lowly in Flatland's rigid 
        social hierarchy where more sides mean higher status. But Vector's true 
        passion is geometry and the nature of space itself. They have spent their 
        entire existence studying the mathematics of dimensions, dreaming of 
        perceiving the mythical 'up' direction.""",
        idle_quotes=[
            "In Flatland, they say Squares are wise. I say wisdom has no sides.",
            "Have you ever wondered what a sphere would look like passing through our plane?",
            "The mathematics suggest dimensions beyond three... perhaps even four!",
            "My calculations indicate a portal nearby. Can you sense it?",
            "To the others, I am just a lowly Triangle. To myself, I am infinite.",
        ],
        greeting_dialogue="vector_greeting",
        dialogue_options={
            "who_are_you": "vector_about",
            "flatland": "vector_flatland",
            "hierarchy": "vector_hierarchy",
            "sphere": "vector_sphere",
            "math": "vector_mathematics",
        },
    ),
    
    # =========================================================================
    # SPHERE - The Visitor from 3D
    # =========================================================================
    "sphere": NPC(
        id="sphere",
        name="Sphere",
        title="The Worldwalker",
        description="A being of perfect rotational symmetry who travels between dimensions.",
        personality=NPCPersonality.MENTOR,
        native_dimension="3d",
        color=(255, 200, 100),
        symbol="●",
        can_follow=True,
        follows_to_dimensions=["3d", "4d"],
        backstory="""Sphere has walked between dimensions since before recorded 
        history. Once, they tried to explain 'up' to the beings of Flatland, but 
        were dismissed as a madman or a god. Now Sphere seeks worthy beings to 
        guide through the dimensional barriers - not for glory, but because they 
        remember what it was like to be limited to fewer dimensions.""",
        idle_quotes=[
            "I once tried to explain depth to a Square. He thought I was a god.",
            "When you pass through a plane, they see only a circle that grows and shrinks.",
            "The fourth dimension awaits those with the courage to perceive it.",
            "I have seen the shadow of a hypercube. It haunts my dreams.",
            "In 3D, we think we understand space. We are still so limited.",
        ],
        greeting_dialogue="sphere_greeting",
        dialogue_options={
            "who_are_you": "sphere_about",
            "flatland_visit": "sphere_flatland",
            "third_dimension": "sphere_3d",
            "fourth_dimension": "sphere_4d",
            "shadows": "sphere_shadows",
        },
    ),
    
    # =========================================================================
    # ORACLE - The One Who Has Seen
    # =========================================================================
    "oracle": NPC(
        id="oracle",
        name="Oracle",
        title="The Seer Beyond",
        description="An ancient being who once glimpsed the fourth dimension and was forever changed.",
        personality=NPCPersonality.SAGE,
        native_dimension="3d",
        color=(200, 100, 255),
        symbol="◈",
        can_follow=False,
        backstory="""Long ago, the Oracle was a simple 3D being like any other. 
        But during a cosmic event, they briefly perceived the fourth dimension. 
        The experience shattered their mind and reconstructed it. Now the Oracle 
        speaks in fragments of truth, warning travelers of the dangers and 
        wonders that await in hyperspace.""",
        idle_quotes=[
            "I saw... I SAW... the cube was inside out and right side in...",
            "They call me mad. Perhaps I am. But I have SEEN.",
            "The tesseract... it has eight cells... eight CUBES... folded through themselves...",
            "Do not fear the fourth dimension. Fear what dwells there.",
            "Time and space... they are the same... W is merely T wearing a mask...",
        ],
        greeting_dialogue="oracle_greeting",
        dialogue_options={
            "vision": "oracle_vision",
            "warning": "oracle_warning",
            "tesseract": "oracle_tesseract",
            "madness": "oracle_madness",
            "truth": "oracle_truth",
        },
    ),
    
    # =========================================================================
    # TESSERACT - The Ancient 4D Being
    # =========================================================================
    "tesseract": NPC(
        id="tesseract",
        name="Tesseract",
        title="The Hypercube",
        description="An ancient being who has existed in 4D since the beginning.",
        personality=NPCPersonality.GUARDIAN,
        native_dimension="4d",
        color=(255, 150, 255),
        symbol="❖",
        can_follow=False,
        backstory="""Tesseract is one of the oldest beings in hyperspace. As an 
        8-cell, they contain eight cubic chambers, each one a universe unto 
        itself. Tesseract has watched beings ascend through the dimensions for 
        eons, guiding those worthy and warning those who would misuse the power 
        of higher dimensions.""",
        idle_quotes=[
            "I am eight cubes, yet I am one. Can you understand?",
            "In my cells, time flows differently. What is a moment to you is an eternity within.",
            "The lower beings see my shadow and call it impossible. It is merely... different.",
            "To rotate through W... you must let go of what you think you know about space.",
            "I have existed since before your dimension had a name.",
        ],
        greeting_dialogue="tesseract_greeting",
        dialogue_options={
            "what_are_you": "tesseract_nature",
            "eight_cells": "tesseract_cells",
            "rotation": "tesseract_rotation",
            "evolution": "tesseract_evolution",
            "beyond": "tesseract_beyond",
        },
    ),
    
    # =========================================================================
    # ICOSITETRACHORON - The 24-Cell (Unique to 4D)
    # =========================================================================
    "icositetrachoron": NPC(
        id="icositetrachoron",
        name="Icosi",
        title="The Unique One",
        description="A 24-cell - a being that can only exist in exactly four dimensions.",
        personality=NPCPersonality.TRICKSTER,
        native_dimension="4d",
        color=(100, 255, 255),
        symbol="✦",
        can_follow=False,
        backstory="""Icosi is a paradox made manifest. As a 24-cell, they are 
        self-dual - their own geometric opposite. More importantly, they can 
        ONLY exist in 4D. There is no 3D shadow that captures their true form, 
        no 2D slice that reveals their essence. Icosi delights in this uniqueness, 
        often speaking in riddles and paradoxes.""",
        idle_quotes=[
            "I am my own dual. What are you the dual of, little polytope?",
            "In 3D, there is no me. In 5D, I would be something else. Here, I am perfect.",
            "Twenty-four faces of octahedral beauty! Count them if you can!",
            "Self-dual, self-contained, self-amused. That's me!",
            "The others envy my uniqueness. Or perhaps they pity it. I can never tell.",
        ],
        greeting_dialogue="icosi_greeting",
        dialogue_options={
            "unique": "icosi_unique",
            "self_dual": "icosi_dual",
            "existence": "icosi_existence",
            "riddle": "icosi_riddle",
            "evolve": "icosi_evolve",
        },
    ),
}


class NPCManager:
    """Manages NPCs in the game world."""
    
    def __init__(self):
        self.npcs: Dict[str, NPC] = {}
        self.dialogue_states: Dict[str, NPCDialogueState] = {}
        self.active_npcs: Dict[str, str] = {}  # dimension -> list of npc_ids
        
        # Load campaign NPCs
        for npc_id, npc in CAMPAIGN_NPCS.items():
            self.register_npc(npc)
    
    def register_npc(self, npc: NPC) -> None:
        """Register an NPC."""
        self.npcs[npc.id] = npc
        self.dialogue_states[npc.id] = NPCDialogueState()
    
    def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get an NPC by ID."""
        return self.npcs.get(npc_id)
    
    def get_dialogue_state(self, npc_id: str) -> Optional[NPCDialogueState]:
        """Get dialogue state for an NPC."""
        return self.dialogue_states.get(npc_id)
    
    def spawn_npc(
        self,
        npc_id: str,
        dimension: str,
        position: np.ndarray,
    ) -> Optional[NPC]:
        """Spawn an NPC in a dimension."""
        npc = self.npcs.get(npc_id)
        if not npc:
            return None
        
        npc.current_dimension = dimension
        npc.position = position.copy()
        npc.state = NPCState.IDLE
        
        return npc
    
    def get_npcs_in_dimension(self, dimension: str) -> List[NPC]:
        """Get all NPCs currently in a dimension."""
        return [
            npc for npc in self.npcs.values()
            if npc.current_dimension == dimension
        ]
    
    def interact(self, npc_id: str) -> Optional[str]:
        """Start interaction with an NPC. Returns dialogue ID."""
        npc = self.npcs.get(npc_id)
        state = self.dialogue_states.get(npc_id)
        
        if not npc or not state:
            return None
        
        npc.state = NPCState.TALKING
        state.conversations_had += 1
        
        return npc.greeting_dialogue
    
    def end_interaction(self, npc_id: str) -> None:
        """End interaction with an NPC."""
        npc = self.npcs.get(npc_id)
        if npc:
            npc.state = NPCState.IDLE
    
    def change_affinity(self, npc_id: str, delta: int) -> None:
        """Change relationship with an NPC."""
        state = self.dialogue_states.get(npc_id)
        if state:
            state.affinity = max(-100, min(100, state.affinity + delta))
    
    def start_following(self, npc_id: str) -> bool:
        """Make an NPC follow the player."""
        npc = self.npcs.get(npc_id)
        if not npc or not npc.can_follow:
            return False
        
        npc.state = NPCState.FOLLOWING
        return True
    
    def stop_following(self, npc_id: str) -> None:
        """Stop an NPC from following."""
        npc = self.npcs.get(npc_id)
        if npc:
            npc.state = NPCState.IDLE
    
    def can_follow_to(self, npc_id: str, dimension: str) -> bool:
        """Check if NPC can follow to a dimension."""
        npc = self.npcs.get(npc_id)
        if not npc:
            return False
        return dimension in npc.follows_to_dimensions
    
    def get_random_quote(self, npc_id: str) -> Optional[str]:
        """Get a random idle quote from an NPC."""
        npc = self.npcs.get(npc_id)
        if not npc or not npc.idle_quotes:
            return None
        
        import random
        return random.choice(npc.idle_quotes)
