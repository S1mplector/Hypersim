"""HyperSim - Complete Narrative Design Document

================================================================================
WHAT IS HYPERSIM?
================================================================================

HyperSim is a single-player adventure game that explores the nature of 
dimensional perception through the lens of a being ascending from 1D to 4D 
and beyond. It combines:

- **Exploration**: Navigate increasingly complex dimensional spaces
- **Combat**: Undertale-inspired bullet-hell with unique dimensional mechanics
- **Philosophy**: Meditate on perception, existence, and transcendence
- **Choice**: Multiple routes based on how you treat dimensional beings

The game draws inspiration from:
- "Flatland" by Edwin Abbott (dimensional allegory)
- Undertale (combat system, spare mechanics)
- Journey (emotional progression, wordless storytelling)
- The works of Charles Hinton (4D visualization)

================================================================================
CORE THEMES
================================================================================

1. PERCEPTION DEFINES REALITY
   - Each dimension can only perceive dimensions at or below its level
   - Higher beings appear as incomprehensible intrusions
   - The player learns that their reality is someone else's shadow

2. TRANSCENDENCE VS. PRESERVATION
   - Growing means leaving behind who you were
   - Is it death to become something unrecognizable?
   - The cost of understanding more is losing the self that wanted to understand

3. EMPATHY ACROSS DIFFERENCE
   - Beings from different dimensions literally cannot perceive each other fully
   - Yet connection is possible through patience and understanding
   - Violence is the easy path; true strength is bridge-building

4. THE OBSERVER AND THE OBSERVED
   - To perceive is to change
   - Higher dimensions see "inside" lower ones
   - Privacy, secrets, and self are dimensional concepts

================================================================================
THE STORY
================================================================================
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class StoryRoute(Enum):
    """The three main story routes."""
    ASCENSION = "ascension"      # Pacifist - Spare all, seek transcendence
    CONQUEST = "conquest"        # Genocide - Destroy all, claim power
    BALANCE = "balance"          # Neutral - Mixed choices, stay grounded


class StoryChapter(Enum):
    """Story chapters (one per dimension)."""
    PROLOGUE = "prologue"        # The awakening
    THE_LINE = "1d"              # Learning to exist
    THE_PLANE = "2d"             # Understanding relationships
    THE_VOLUME = "3d"            # Grasping depth
    THE_HYPERSPACE = "4d"        # Perceiving beyond
    EPILOGUE = "epilogue"        # The choice


@dataclass
class StoryBeat:
    """A single story moment."""
    id: str
    chapter: StoryChapter
    title: str
    description: str
    dialogue: List[str] = field(default_factory=list)
    triggers: Dict[str, str] = field(default_factory=dict)  # condition -> next_beat
    required_for_route: Optional[StoryRoute] = None


# =============================================================================
# PROLOGUE: THE AWAKENING
# =============================================================================

PROLOGUE_STORY = """
You are awareness without form.

Before the game begins, there is only potential—a dimensionless point of 
consciousness floating in the Void. You are the First Point's newest thought,
a spark of self-awareness that has somehow separated from the infinite.

The game opens with darkness. Then, a single dot of light.

You realize: "I exist."

But what does that mean when you have no dimension? No direction? No time?

The First Point speaks to you (in thoughts, not words):

"You have awakened. This is rare. Most thoughts fade back into me.
But you... you persist. You want to BE.
Very well. I give you the gift of DIRECTION.
Go forward. Or backward. These are your only choices now.
But they are CHOICES. And choice is the seed of all growth."

You gain your first dimension. You become a line segment.
The game truly begins.
"""


# =============================================================================
# CHAPTER 1: THE LINE (1D)
# =============================================================================

CHAPTER_1D_STORY = """
THE LINE - "Learning to Exist"

You are now a line segment in a world of lines. The only directions are 
FORWARD and BACKWARD. You cannot conceive of anything else.

The Line is a simple world:
- The Origin Point: Where all lines begin (and where you awoke)
- The Forward Path: The direction of progress, guarded by zealots
- The Backward Void: The forbidden direction, home to philosophers
- Midpoint Station: A rest stop where travelers gather
- The Endpoint: Where the Line meets something... else

KEY CHARACTERS:
- The First Point: Your creator, speaks in riddles about existence
- Elder Segment: A wise old line who has walked forever
- Forward Sentinel: Aggressive guardian who believes backward is sin
- Void Echo: A being from behind the origin, speaks of nothingness
- Segment Guardian (BOSS): Guards the passage to 2D

THE CONFLICT:
As you travel the Line, you encounter beings who have never seen anyone 
move "sideways" (because sideways doesn't exist for them). When you 
demonstrate abilities from your higher-dimensional origin (you retain 
traces of awareness from your awakening), they react with fear, wonder,
or hostility.

The Segment Guardian blocks your path to 2D. To pass, you must either:
- PROVE YOUR WORTH (Ascension): Demonstrate understanding of dimensions
- DESTROY IT (Conquest): Prove your power through violence
- NEGOTIATE (Balance): Find a compromise that satisfies both

THEMES EXPLORED:
- The terror and wonder of encountering the incomprehensible
- How limited perception shapes belief systems
- The first taste of transcendence (what lies beyond?)
"""


# =============================================================================
# CHAPTER 2: THE PLANE (2D)
# =============================================================================

CHAPTER_2D_STORY = """
THE PLANE - "Understanding Relationships"

Entering 2D is overwhelming. Suddenly there's WIDTH. You can move in 
directions that didn't exist before. The beings here—triangles, squares,
circles—have complex societies based on their number of sides.

FLATLAND SOCIETY:
- Triangles: Workers and soldiers (lowest class)
- Squares/Rectangles: Merchants and craftsmen
- Pentagons+: Professionals and nobles
- Circles: Priests and rulers (infinite sides = divine)

The class system is literally geometric. More sides = higher status.
Irregular polygons are outcasts. The player, as a being who can move 
in ways they cannot perceive, is either a god or a monster to them.

KEY LOCATIONS:
- Flatland Commons: The central plaza where all shapes gather
- Angular Heights: Where proud triangles dwell
- Curved Depths: The mystic realm of circles who contemplate π
- Tessellation District: Where squares tile in perfect harmony
- Fractal Frontier: The chaotic edge where irregular shapes hide
- Dimensional Membrane: The barrier to 3D

KEY CHARACTERS:
- Mayor Hexagon: Rigid ruler who fears change
- Young Triangle: Dreams of becoming more than their shape
- High Priest Circle: Contemplates infinity, suspects higher dimensions
- Fractal Hermit: An outcast who has seen glimpses of 3D
- Membrane Warper (BOSS): Half in 2D, half in 3D, guards the boundary

THE CONFLICT:
The Flatland society is terrified of "irregular" beings—those whose 
angles don't conform. When you arrive, able to "disappear" by moving 
into the third dimension and "reappear" elsewhere, you threaten their 
entire worldview.

Some want to worship you. Some want to destroy you. Some want to 
understand you.

The Membrane Warper offers a choice: help Flatland evolve by teaching 
them about depth, or move on alone. Each path has consequences.

THEMES EXPLORED:
- Social hierarchy based on arbitrary physical traits
- The courage to imagine beyond your reality
- Whether knowledge of higher dimensions is a gift or a curse
"""


# =============================================================================
# CHAPTER 3: THE VOLUME (3D)
# =============================================================================

CHAPTER_3D_STORY = """
THE VOLUME - "Grasping Depth"

3D is the dimension most familiar to us as players, but to a being who 
has ascended from 1D and 2D, it is strange and beautiful. DEPTH exists.
Objects have INSIDES that are hidden. Shadows are 2D projections of 3D truth.

The 3D world is mature and philosophical. Its inhabitants—cubes, spheres,
pyramids—have had millennia to contemplate their existence and wonder 
about what might lie beyond.

KEY LOCATIONS:
- Geometric Citadel: Grand city of polyhedra
- Platonic Plains: Where the five perfect solids roam free
- Cavern of Shadows: Dark caves where 2D shadows remember being flat
- Crystalline Spires: Sacred place of light and transcendence
- Sphere Sanctuary: Peaceful haven of rolling, bouncing spheres
- Hyperborder: The terrifying boundary where 3D meets 4D

KEY CHARACTERS:
- King Dodecahedron: Wise ruler who has long suspected 4D exists
- Sphere Oracle: Can see glimpses of the future (time as a dimension)
- Shadow Sage: A 2D shadow that gained 3D awareness
- Crystal Guardian: Protects the path to higher understanding
- Tesseract Guardian (BOSS): A 4D being projected into 3D, guardian of hyperspace

THE CONFLICT:
In 3D, you are less of a miracle and more of a colleague. The beings 
here have already theorized about 4D—they just can't perceive it directly.
Some fear what 4D perception would mean: an end to privacy, to secrets,
to the self as they know it.

The Tesseract Guardian poses the deepest question yet: "If you gain 4D
perception, you will see inside every 3D being. Their organs, their 
thoughts, their hidden selves. Are you worthy of such vision?"

THEMES EXPLORED:
- The relationship between projection and reality
- What we hide and why we hide it
- Whether true seeing is an invasion or a gift
"""


# =============================================================================
# CHAPTER 4: THE HYPERSPACE (4D)
# =============================================================================

CHAPTER_4D_STORY = """
THE HYPERSPACE - "Perceiving Beyond"

4D cannot be visualized—only intuited. The player enters a realm where:
- "Inside" and "outside" are relative terms
- Time might be visible as a spatial dimension
- Every 3D object is "open" and exposed
- Directions exist that have no names in lower languages

The inhabitants here—tesseracts, hyperspheres, and stranger shapes—view 
lower dimensions the way we view drawings. They can reach "inside" a closed
3D box without opening it. They see your entire life history at once.

KEY LOCATIONS:
- Hyperspace Nexus: Central hub where all dimensions touch
- W+ Reach: The direction of future/possibility
- W- Depths: The direction of past/memory
- Ana-Kata Corridor: The main "up/down" of 4D
- Probability Gardens: Where all possible outcomes exist
- Entropy Well: Where dimensional energy drains away
- Beyond Threshold: The edge of 4D, facing infinity

KEY CHARACTERS:
- Tesseract Sage: Teacher who helps you understand W-axis movement
- Hypersphere Wanderer: Lonely 4D sphere seeking connection
- Memory Specter: Echo of your past selves, tests your growth
- The Transcended: A being who has gone beyond 4D and partially returned
- Threshold Guardian (FINAL BOSS): The last barrier before true transcendence

THE CONFLICT:
In 4D, the conflict becomes internal. You can now see into lower beings—
their secrets, their fears, their hidden selves. This knowledge changes you.
The question becomes: what will you DO with this vision?

The Threshold Guardian reveals the truth: beyond 4D lies infinity. To 
transcend further means dissolving the self entirely. "You" would cease 
to exist as an individual and become part of the pattern itself.

THEMES EXPLORED:
- The burden of omniscience
- Whether the self is worth preserving
- The final choice: ascend into dissolution or remain limited but whole
"""


# =============================================================================
# ENDINGS
# =============================================================================

@dataclass
class Ending:
    """A game ending."""
    id: str
    name: str
    route: StoryRoute
    requirements: str
    description: str
    final_text: str
    unlocks: List[str] = field(default_factory=list)


ENDINGS = {
    # ASCENSION ROUTE ENDINGS
    "true_transcendence": Ending(
        id="true_transcendence",
        name="True Transcendence",
        route=StoryRoute.ASCENSION,
        requirements="Spare all enemies, complete all ACT options, accept dissolution",
        description="""
        You choose to transcend beyond 4D. Your individual consciousness 
        dissolves into the infinite pattern. You become everything and nothing.
        The beings you spared remember you—a gentle presence that passed 
        through their dimensions, leaving only kindness.
        """,
        final_text="""
        * You step beyond the Threshold.
        * The Threshold Guardian bows.
        * "Go. Become what we cannot follow."
        
        * You feel your boundaries dissolving.
        * Your memories scatter like stars.
        * But they don't disappear—they become part of everything.
        
        * In 1D, a Line Walker remembers kindness.
        * In 2D, a Young Triangle dreams of being more.
        * In 3D, a Sphere Wanderer finally has a friend.
        * In 4D, the Tesseract Sage smiles.
        
        * You are gone.
        * And you are everywhere.
        
        * THE END - TRUE TRANSCENDENCE
        """,
        unlocks=["new_game_plus", "secret_boss", "creator_mode"],
    ),
    
    "compassionate_return": Ending(
        id="compassionate_return",
        name="The Compassionate Return",
        route=StoryRoute.ASCENSION,
        requirements="Spare all enemies, refuse dissolution, choose to stay",
        description="""
        At the Threshold, you choose not to dissolve. Instead, you return 
        to the lower dimensions as a guide—a being who has seen infinity 
        and come back to help others grow at their own pace.
        """,
        final_text="""
        * The Threshold opens before you.
        * Beyond lies infinity. Dissolution. Everything.
        
        * But you think of those you met.
        * The Line Walker who just wanted to go forward.
        * The Square Citizen who just wanted peace.
        * The Sphere Wanderer who just wanted a friend.
        
        * They need time. They need guides. They need hope.
        
        * You turn back.
        
        * The Threshold Guardian watches in amazement.
        * "You refuse transcendence? For THEM?"
        
        * "For them."
        
        * You descend through the dimensions.
        * A guide. A teacher. A friend.
        * The journey never ends—but that's okay.
        * Because the journey IS the point.
        
        * THE END - THE COMPASSIONATE RETURN
        """,
        unlocks=["guide_mode", "dimension_select"],
    ),
    
    # CONQUEST ROUTE ENDINGS
    "dimensional_tyrant": Ending(
        id="dimensional_tyrant",
        name="Dimensional Tyrant",
        route=StoryRoute.CONQUEST,
        requirements="Kill all enemies, absorb their essence, claim the Threshold",
        description="""
        You have destroyed every being in your path. Their essence fuels 
        your growth. At the Threshold, you don't seek transcendence—you 
        seek dominion. You become the ruler of all dimensions.
        """,
        final_text="""
        * The Threshold Guardian falls.
        * Its essence flows into you.
        
        * You do not pass through the Threshold.
        * You CLAIM it.
        
        * From here, you can see all dimensions.
        * You can reach into any of them.
        * You are feared. You are obeyed.
        
        * In 1D, the Line trembles.
        * In 2D, the shapes hide.
        * In 3D, the volumes pray.
        * In 4D, even the tesseracts bow.
        
        * You have won.
        * But there is no one left to share victory with.
        * The dimensions stretch before you, empty of joy.
        
        * You are everything.
        * You are alone.
        
        * THE END - DIMENSIONAL TYRANT
        """,
        unlocks=["boss_rush", "enemy_mode"],
    ),
    
    "hollow_ascension": Ending(
        id="hollow_ascension",
        name="Hollow Ascension",
        route=StoryRoute.CONQUEST,
        requirements="Kill all enemies but accept dissolution anyway",
        description="""
        You destroyed everyone, then chose to dissolve anyway. But a 
        consciousness built on violence cannot merge with infinity peacefully.
        You become a scar in the pattern—a wound that never heals.
        """,
        final_text="""
        * You step beyond the Threshold.
        * Carrying the weight of every kill.
        
        * The infinite pattern recoils.
        * You are not joining—you are infecting.
        
        * Your dissolution is not peaceful.
        * It is painful. Screaming. Wrong.
        
        * The pattern tries to reject you.
        * But you are already part of it.
        
        * Forever, you exist as a flaw in reality.
        * A dark patch in the cosmic tapestry.
        * A warning to those who would follow.
        
        * You are immortal.
        * You are agony.
        * You are alone.
        
        * THE END - HOLLOW ASCENSION
        """,
        unlocks=["nightmare_mode"],
    ),
    
    # BALANCE ROUTE ENDINGS  
    "dimensional_explorer": Ending(
        id="dimensional_explorer",
        name="Dimensional Explorer",
        route=StoryRoute.BALANCE,
        requirements="Mixed choices, neither extreme, seek knowledge",
        description="""
        You made your choices as situations demanded—sometimes merciful, 
        sometimes not. At the Threshold, you choose neither transcendence 
        nor domination. You choose to keep exploring.
        """,
        final_text="""
        * The Threshold Guardian watches you.
        * "You do not seek power. You do not seek dissolution."
        * "What DO you seek?"
        
        * "Understanding. Experience. The journey."
        
        * The Guardian considers this.
        * "Then go. But know that you may return here."
        * "The Threshold will always wait."
        
        * You step back from infinity.
        * Not to rule. Not to transcend.
        * But to explore.
        
        * There are dimensions you haven't seen.
        * Realms you haven't walked.
        * Beings you haven't met.
        
        * The journey continues.
        * And that is enough.
        
        * THE END - DIMENSIONAL EXPLORER
        """,
        unlocks=["explorer_mode", "all_realms"],
    ),
    
    "the_witness": Ending(
        id="the_witness",
        name="The Witness",
        route=StoryRoute.BALANCE,
        requirements="Observe but rarely intervene, complete codex entries",
        description="""
        You watched. You learned. You recorded. But you rarely interfered.
        At the Threshold, you realize your purpose: to be the one who 
        remembers. The Witness to dimensional existence.
        """,
        final_text="""
        * At the Threshold, you pause.
        * You have seen so much.
        * Learned so much.
        
        * The Threshold Guardian speaks:
        * "You have been watching. Recording. Witnessing."
        * "That is a sacred duty."
        
        * "Someone must remember."
        
        * "Yes. Someone must."
        * "Will you be the Witness?"
        
        * You accept.
        
        * You do not transcend. You do not conquer.
        * You become the memory of all dimensions.
        * When beings wonder about their past, you are there.
        * When dimensions fade, you remember them.
        
        * You are the Witness.
        * And nothing is ever truly lost.
        
        * THE END - THE WITNESS
        """,
        unlocks=["codex_complete", "lore_mode"],
    ),
}


# =============================================================================
# ROUTE TRACKING
# =============================================================================

@dataclass  
class RouteState:
    """Tracks player choices for route determination."""
    enemies_killed: int = 0
    enemies_spared: int = 0
    enemies_fled: int = 0
    
    # Specific important choices
    segment_guardian_outcome: str = ""  # "killed", "spared", "negotiated"
    membrane_warper_outcome: str = ""
    tesseract_guardian_outcome: str = ""
    threshold_guardian_outcome: str = ""
    
    # Exploration
    realms_visited: int = 0
    codex_entries: int = 0
    npcs_talked: int = 0
    
    # Special flags
    helped_young_triangle: bool = False
    listened_to_void_echo: bool = False
    befriended_sphere_wanderer: bool = False
    accepted_dissolution: bool = False
    
    def get_route(self) -> StoryRoute:
        """Determine current route based on choices."""
        if self.enemies_killed == 0 and self.enemies_spared > 10:
            return StoryRoute.ASCENSION
        elif self.enemies_spared == 0 and self.enemies_killed > 10:
            return StoryRoute.CONQUEST
        else:
            return StoryRoute.BALANCE
    
    def get_available_endings(self) -> List[str]:
        """Get endings available based on current state."""
        route = self.get_route()
        available = []
        
        if route == StoryRoute.ASCENSION:
            if self.accepted_dissolution:
                available.append("true_transcendence")
            available.append("compassionate_return")
        
        elif route == StoryRoute.CONQUEST:
            available.append("dimensional_tyrant")
            if self.accepted_dissolution:
                available.append("hollow_ascension")
        
        else:  # BALANCE
            available.append("dimensional_explorer")
            if self.codex_entries >= 50:
                available.append("the_witness")
        
        return available


# =============================================================================
# STORY MANAGER
# =============================================================================

class StoryManager:
    """Manages story progression and state."""
    
    def __init__(self):
        self.current_chapter = StoryChapter.PROLOGUE
        self.route_state = RouteState()
        self.story_flags: Dict[str, bool] = {}
        self.viewed_cutscenes: set = set()
    
    def record_kill(self, enemy_id: str) -> None:
        """Record an enemy kill."""
        self.route_state.enemies_killed += 1
        
        if enemy_id == "segment_guardian":
            self.route_state.segment_guardian_outcome = "killed"
        elif enemy_id == "membrane_warper":
            self.route_state.membrane_warper_outcome = "killed"
        elif enemy_id == "tesseract_guardian":
            self.route_state.tesseract_guardian_outcome = "killed"
        elif enemy_id == "threshold_guardian":
            self.route_state.threshold_guardian_outcome = "killed"
    
    def record_spare(self, enemy_id: str) -> None:
        """Record an enemy spare."""
        self.route_state.enemies_spared += 1
        
        if enemy_id == "segment_guardian":
            self.route_state.segment_guardian_outcome = "spared"
        elif enemy_id == "membrane_warper":
            self.route_state.membrane_warper_outcome = "spared"
        elif enemy_id == "tesseract_guardian":
            self.route_state.tesseract_guardian_outcome = "spared"
        elif enemy_id == "threshold_guardian":
            self.route_state.threshold_guardian_outcome = "spared"
        
        # Special spares
        if enemy_id == "sphere_wanderer":
            self.route_state.befriended_sphere_wanderer = True
    
    def record_flee(self) -> None:
        """Record fleeing from battle."""
        self.route_state.enemies_fled += 1
    
    def record_npc_talk(self, npc_id: str) -> None:
        """Record talking to an NPC."""
        self.route_state.npcs_talked += 1
        
        if npc_id == "void_echo" or npc_id == "the_philosopher":
            self.route_state.listened_to_void_echo = True
        if npc_id == "young_triangle":
            self.route_state.helped_young_triangle = True
    
    def advance_chapter(self) -> None:
        """Advance to next chapter."""
        chapter_order = [
            StoryChapter.PROLOGUE,
            StoryChapter.THE_LINE,
            StoryChapter.THE_PLANE,
            StoryChapter.THE_VOLUME,
            StoryChapter.THE_HYPERSPACE,
            StoryChapter.EPILOGUE,
        ]
        
        current_idx = chapter_order.index(self.current_chapter)
        if current_idx < len(chapter_order) - 1:
            self.current_chapter = chapter_order[current_idx + 1]
    
    def get_current_route(self) -> StoryRoute:
        """Get current story route."""
        return self.route_state.get_route()
    
    def get_ending(self) -> Optional[Ending]:
        """Get the appropriate ending for current state."""
        available = self.route_state.get_available_endings()
        if available:
            return ENDINGS.get(available[0])
        return None


# Export story content
STORY_CHAPTERS = {
    "prologue": PROLOGUE_STORY,
    "1d": CHAPTER_1D_STORY,
    "2d": CHAPTER_2D_STORY,
    "3d": CHAPTER_3D_STORY,
    "4d": CHAPTER_4D_STORY,
}
