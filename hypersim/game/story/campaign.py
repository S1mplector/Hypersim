"""Campaign and story structure."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class StoryBeatType(Enum):
    """Types of story moments."""
    DIALOGUE = "dialogue"           # Conversation/narration
    CUTSCENE = "cutscene"           # Visual sequence
    DISCOVERY = "discovery"         # Player finds something
    BOSS = "boss"                   # Boss encounter
    PUZZLE = "puzzle"               # Dimensional puzzle
    CHOICE = "choice"               # Player decision
    TRANSITION = "transition"       # Dimension/world change
    LORE = "lore"                   # Lore unlocked


@dataclass
class StoryBeat:
    """A single story moment in the campaign."""
    id: str
    type: StoryBeatType
    title: str = ""
    description: str = ""
    
    # Content
    dialogue_id: Optional[str] = None  # Reference to dialogue sequence
    npc_id: Optional[str] = None       # NPC involved
    lore_id: Optional[str] = None      # Lore to unlock
    
    # Requirements
    requires_dimension: Optional[str] = None
    requires_items: List[str] = field(default_factory=list)
    requires_story_beats: List[str] = field(default_factory=list)
    requires_evolution: Optional[int] = None  # Polytope form level
    
    # Triggers
    trigger_on_enter: bool = False     # Trigger when entering area
    trigger_on_interact: bool = False  # Trigger on NPC/object interact
    trigger_position: Optional[List[float]] = None
    trigger_radius: float = 3.0
    
    # Results
    unlocks_dimension: Optional[str] = None
    grants_ability: Optional[str] = None
    grants_xp: int = 0
    next_beat: Optional[str] = None
    
    # Flags
    repeatable: bool = False
    skippable: bool = True
    pauses_game: bool = True


@dataclass
class Chapter:
    """A chapter/act of the campaign."""
    id: str
    title: str
    description: str = ""
    dimension: str = "1d"           # Primary dimension
    theme: str = ""                 # Visual/audio theme
    
    # Structure
    story_beats: List[StoryBeat] = field(default_factory=list)
    side_quests: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)
    
    # Worlds in this chapter
    worlds: List[str] = field(default_factory=list)
    hub_world: Optional[str] = None
    
    # Requirements to unlock
    requires_chapters: List[str] = field(default_factory=list)
    
    # Rewards
    completion_rewards: Dict[str, any] = field(default_factory=dict)


@dataclass
class CampaignState:
    """Tracks player's campaign progress."""
    current_chapter: str = "chapter_1"
    current_beat: Optional[str] = None
    completed_beats: List[str] = field(default_factory=list)
    unlocked_chapters: List[str] = field(default_factory=lambda: ["chapter_1"])
    npc_relationships: Dict[str, int] = field(default_factory=dict)  # npc_id -> affinity
    story_flags: Dict[str, bool] = field(default_factory=dict)
    choices_made: Dict[str, str] = field(default_factory=dict)  # choice_id -> option


class Campaign:
    """The full game campaign."""
    
    def __init__(self):
        self.chapters: Dict[str, Chapter] = {}
        self.story_beats: Dict[str, StoryBeat] = {}
        self.state = CampaignState()
        
        # Callbacks
        self._on_beat_start: Optional[Callable[[StoryBeat], None]] = None
        self._on_beat_complete: Optional[Callable[[StoryBeat], None]] = None
        self._on_chapter_complete: Optional[Callable[[Chapter], None]] = None
        
        # Build campaign
        self._build_campaign()
    
    def _build_campaign(self) -> None:
        """Build the full campaign structure."""
        
        # =====================================================================
        # CHAPTER 1: THE LINE (1D)
        # =====================================================================
        ch1 = Chapter(
            id="chapter_1",
            title="Awakening on the Line",
            description="You exist as a single point on an infinite line. Learn the nature of one-dimensional existence.",
            dimension="1d",
            theme="minimal_pulse",
            worlds=["1d_void", "1d_corridor", "1d_nexus"],
            hub_world="1d_nexus",
            story_beats=[
                StoryBeat(
                    id="1d_awakening",
                    type=StoryBeatType.DIALOGUE,
                    title="Awakening",
                    dialogue_id="intro_1d_awakening",
                    trigger_on_enter=True,
                    pauses_game=True,
                ),
                StoryBeat(
                    id="1d_meet_echo",
                    type=StoryBeatType.DIALOGUE,
                    title="The Echo",
                    description="Meet Echo, another being trapped on the line.",
                    npc_id="echo",
                    dialogue_id="meet_echo",
                    trigger_on_interact=True,
                    requires_story_beats=["1d_awakening"],
                ),
                StoryBeat(
                    id="1d_learn_neighbors",
                    type=StoryBeatType.DISCOVERY,
                    title="Sensing Neighbors",
                    description="Learn to sense other beings on the line.",
                    lore_id="lore_1d_perception",
                    grants_ability="ping_neighbors",
                    grants_xp=50,
                ),
                StoryBeat(
                    id="1d_first_enemy",
                    type=StoryBeatType.DIALOGUE,
                    title="The Blocker",
                    description="Encounter hostile 1D entities.",
                    dialogue_id="first_enemy_1d",
                    requires_story_beats=["1d_learn_neighbors"],
                ),
                StoryBeat(
                    id="1d_echo_explains",
                    type=StoryBeatType.DIALOGUE,
                    title="Beyond the Line",
                    description="Echo speaks of dimensions beyond.",
                    npc_id="echo",
                    dialogue_id="echo_dimensions",
                    requires_story_beats=["1d_first_enemy"],
                    lore_id="lore_dimensions_intro",
                ),
                StoryBeat(
                    id="1d_find_portal",
                    type=StoryBeatType.DISCOVERY,
                    title="The Tear",
                    description="Discover a rift in reality.",
                    dialogue_id="discover_portal_1d",
                    lore_id="lore_portals",
                ),
                StoryBeat(
                    id="1d_portal_choice",
                    type=StoryBeatType.CHOICE,
                    title="The Choice",
                    description="Echo asks if you're ready to leave the only world you know.",
                    dialogue_id="portal_choice_1d",
                    npc_id="echo",
                ),
                StoryBeat(
                    id="1d_ascend",
                    type=StoryBeatType.TRANSITION,
                    title="Ascension",
                    description="Enter the portal and transcend to 2D.",
                    dialogue_id="ascend_to_2d",
                    unlocks_dimension="2d",
                    grants_xp=100,
                    next_beat="2d_arrival",
                ),
            ],
            npcs=["echo"],
        )
        
        # =====================================================================
        # CHAPTER 2: THE PLANE (2D)
        # =====================================================================
        ch2 = Chapter(
            id="chapter_2",
            title="Freedom of the Plane",
            description="A whole new axis of movement. The plane stretches infinitely in two directions.",
            dimension="2d",
            theme="geometric_ambient",
            worlds=["2d_flatlands", "2d_maze", "2d_citadel"],
            hub_world="2d_citadel",
            requires_chapters=["chapter_1"],
            story_beats=[
                StoryBeat(
                    id="2d_arrival",
                    type=StoryBeatType.DIALOGUE,
                    title="A New Dimension",
                    dialogue_id="intro_2d_arrival",
                    trigger_on_enter=True,
                    pauses_game=True,
                ),
                StoryBeat(
                    id="2d_meet_vector",
                    type=StoryBeatType.DIALOGUE,
                    title="Vector",
                    description="Meet Vector, a native 2D being.",
                    npc_id="vector",
                    dialogue_id="meet_vector",
                    trigger_on_interact=True,
                ),
                StoryBeat(
                    id="2d_flatland_philosophy",
                    type=StoryBeatType.LORE,
                    title="Flatland Philosophy",
                    description="Learn how 2D beings perceive reality.",
                    lore_id="lore_flatland",
                    dialogue_id="flatland_lecture",
                    npc_id="vector",
                ),
                StoryBeat(
                    id="2d_enemy_shapes",
                    type=StoryBeatType.DIALOGUE,
                    title="The Polygon Wars",
                    description="Learn about hostile polygon factions.",
                    dialogue_id="polygon_wars",
                    npc_id="vector",
                    lore_id="lore_polygon_wars",
                ),
                StoryBeat(
                    id="2d_boss_square",
                    type=StoryBeatType.BOSS,
                    title="The Perfect Square",
                    description="Face the tyrant of Flatland.",
                    dialogue_id="boss_square_intro",
                    grants_xp=200,
                ),
                StoryBeat(
                    id="2d_echo_returns",
                    type=StoryBeatType.DIALOGUE,
                    title="Echo's Journey",
                    description="Echo has followed you to 2D.",
                    npc_id="echo",
                    dialogue_id="echo_in_2d",
                    requires_story_beats=["2d_boss_square"],
                ),
                StoryBeat(
                    id="2d_sphere_vision",
                    type=StoryBeatType.CUTSCENE,
                    title="The Sphere's Visit",
                    description="A being from 3D passes through your plane.",
                    dialogue_id="sphere_vision",
                    lore_id="lore_sphere_visit",
                ),
                StoryBeat(
                    id="2d_ascend",
                    type=StoryBeatType.TRANSITION,
                    title="Into Volume",
                    description="Follow the Sphere into the third dimension.",
                    dialogue_id="ascend_to_3d",
                    unlocks_dimension="3d",
                    grants_xp=150,
                    next_beat="3d_arrival",
                ),
            ],
            npcs=["vector", "echo"],
        )
        
        # =====================================================================
        # CHAPTER 3: THE VOLUME (3D)
        # =====================================================================
        ch3 = Chapter(
            id="chapter_3",
            title="Depth and Shadow",
            description="Volume. Mass. Shadow. The world of three dimensions is the realm of most physical beings.",
            dimension="3d",
            theme="spatial_symphony",
            worlds=["3d_emergence", "3d_city", "3d_caverns", "3d_tower"],
            hub_world="3d_city",
            requires_chapters=["chapter_2"],
            story_beats=[
                StoryBeat(
                    id="3d_arrival",
                    type=StoryBeatType.DIALOGUE,
                    title="True Space",
                    dialogue_id="intro_3d_arrival",
                    trigger_on_enter=True,
                ),
                StoryBeat(
                    id="3d_meet_sphere",
                    type=StoryBeatType.DIALOGUE,
                    title="The Sphere",
                    description="Finally meet the being who showed you 3D.",
                    npc_id="sphere",
                    dialogue_id="meet_sphere",
                ),
                StoryBeat(
                    id="3d_shadow_lesson",
                    type=StoryBeatType.LORE,
                    title="Shadows of Higher Dimensions",
                    description="Learn how 4D objects cast 3D shadows.",
                    dialogue_id="shadow_lesson",
                    npc_id="sphere",
                    lore_id="lore_shadows",
                ),
                StoryBeat(
                    id="3d_tesseract_glimpse",
                    type=StoryBeatType.DISCOVERY,
                    title="Glimpse of the Tesseract",
                    description="See a hypercube's shadow for the first time.",
                    dialogue_id="tesseract_glimpse",
                    lore_id="lore_tesseract",
                ),
                StoryBeat(
                    id="3d_oracle",
                    type=StoryBeatType.DIALOGUE,
                    title="The Oracle",
                    description="Meet the Oracle who has seen 4D.",
                    npc_id="oracle",
                    dialogue_id="meet_oracle",
                ),
                StoryBeat(
                    id="3d_oracle_warning",
                    type=StoryBeatType.DIALOGUE,
                    title="The Warning",
                    description="The Oracle warns of dangers in hyperspace.",
                    npc_id="oracle",
                    dialogue_id="oracle_warning",
                    lore_id="lore_hyperspace_dangers",
                ),
                StoryBeat(
                    id="3d_boss_cube",
                    type=StoryBeatType.BOSS,
                    title="The Cubic Overlord",
                    description="A powerful 3D entity guards the path forward.",
                    dialogue_id="boss_cube_intro",
                    grants_xp=300,
                ),
                StoryBeat(
                    id="3d_final_choice",
                    type=StoryBeatType.CHOICE,
                    title="The Final Threshold",
                    description="Are you ready to transcend space itself?",
                    dialogue_id="final_3d_choice",
                    npc_id="sphere",
                ),
                StoryBeat(
                    id="3d_ascend",
                    type=StoryBeatType.TRANSITION,
                    title="Transcendence",
                    description="Break through to the fourth dimension.",
                    dialogue_id="ascend_to_4d",
                    unlocks_dimension="4d",
                    grants_xp=250,
                    next_beat="4d_arrival",
                ),
            ],
            npcs=["sphere", "oracle", "echo", "vector"],
        )
        
        # =====================================================================
        # CHAPTER 4: HYPERSPACE (4D)
        # =====================================================================
        ch4 = Chapter(
            id="chapter_4",
            title="Beyond Space",
            description="The fourth dimension. Time and space become one. Reality itself bends to your will.",
            dimension="4d",
            theme="hyperdimensional",
            worlds=["4d_threshold", "4d_tesseract_city", "4d_void_between", "4d_origin"],
            hub_world="4d_tesseract_city",
            requires_chapters=["chapter_3"],
            story_beats=[
                StoryBeat(
                    id="4d_arrival",
                    type=StoryBeatType.DIALOGUE,
                    title="Hyperspace",
                    dialogue_id="intro_4d_arrival",
                    trigger_on_enter=True,
                ),
                StoryBeat(
                    id="4d_evolution_begin",
                    type=StoryBeatType.DISCOVERY,
                    title="The Simplex Form",
                    description="You take shape as a 5-cell, the simplest 4D being.",
                    dialogue_id="evolution_begin",
                    lore_id="lore_polytopes",
                ),
                StoryBeat(
                    id="4d_meet_tesseract",
                    type=StoryBeatType.DIALOGUE,
                    title="The Tesseract",
                    description="Meet the ancient Tesseract being.",
                    npc_id="tesseract",
                    dialogue_id="meet_tesseract",
                ),
                StoryBeat(
                    id="4d_w_axis",
                    type=StoryBeatType.LORE,
                    title="The W Axis",
                    description="Learn to perceive and move in the fourth spatial axis.",
                    dialogue_id="w_axis_lesson",
                    npc_id="tesseract",
                    lore_id="lore_w_axis",
                    grants_ability="rotate_hyperplanes",
                ),
                StoryBeat(
                    id="4d_meet_24cell",
                    type=StoryBeatType.DIALOGUE,
                    title="The Unique One",
                    description="Meet the 24-Cell, a being that exists only in 4D.",
                    npc_id="icositetrachoron",
                    dialogue_id="meet_24cell",
                    lore_id="lore_24cell",
                ),
                StoryBeat(
                    id="4d_see_lower",
                    type=StoryBeatType.DISCOVERY,
                    title="Seeing All Dimensions",
                    description="From 4D, you can see all lower dimensions at once.",
                    dialogue_id="see_all_dimensions",
                    lore_id="lore_omnivision",
                ),
                StoryBeat(
                    id="4d_friends_return",
                    type=StoryBeatType.DIALOGUE,
                    title="Old Friends",
                    description="Echo, Vector, and Sphere join you in 4D.",
                    dialogue_id="friends_in_4d",
                ),
                StoryBeat(
                    id="4d_final_boss",
                    type=StoryBeatType.BOSS,
                    title="The 600-Cell",
                    description="Face the ultimate 4D entity.",
                    dialogue_id="boss_600cell",
                    grants_xp=500,
                ),
                StoryBeat(
                    id="4d_choice_ascend",
                    type=StoryBeatType.CHOICE,
                    title="Beyond 4D?",
                    description="The Tesseract offers a glimpse of 5D... but at what cost?",
                    dialogue_id="beyond_4d_choice",
                ),
                StoryBeat(
                    id="4d_ending",
                    type=StoryBeatType.CUTSCENE,
                    title="Transcendence Complete",
                    description="You have become a true hyperdimensional being.",
                    dialogue_id="game_ending",
                    grants_xp=1000,
                ),
            ],
            npcs=["tesseract", "icositetrachoron", "sphere", "oracle", "echo", "vector"],
        )
        
        # Register all chapters
        for chapter in [ch1, ch2, ch3, ch4]:
            self.chapters[chapter.id] = chapter
            for beat in chapter.story_beats:
                self.story_beats[beat.id] = beat
    
    def get_current_chapter(self) -> Optional[Chapter]:
        """Get the current chapter."""
        return self.chapters.get(self.state.current_chapter)
    
    def get_current_beat(self) -> Optional[StoryBeat]:
        """Get the current story beat."""
        if self.state.current_beat:
            return self.story_beats.get(self.state.current_beat)
        return None
    
    def can_trigger_beat(self, beat_id: str) -> bool:
        """Check if a story beat can be triggered."""
        beat = self.story_beats.get(beat_id)
        if not beat:
            return False
        
        # Already completed and not repeatable
        if beat_id in self.state.completed_beats and not beat.repeatable:
            return False
        
        # Check requirements
        for req in beat.requires_story_beats:
            if req not in self.state.completed_beats:
                return False
        
        return True
    
    def trigger_beat(self, beat_id: str) -> bool:
        """Trigger a story beat."""
        if not self.can_trigger_beat(beat_id):
            return False
        
        beat = self.story_beats[beat_id]
        self.state.current_beat = beat_id
        
        if self._on_beat_start:
            self._on_beat_start(beat)
        
        return True
    
    def complete_beat(self, beat_id: str) -> None:
        """Mark a story beat as complete."""
        beat = self.story_beats.get(beat_id)
        if not beat:
            return
        
        if beat_id not in self.state.completed_beats:
            self.state.completed_beats.append(beat_id)
        
        if self.state.current_beat == beat_id:
            self.state.current_beat = beat.next_beat
        
        if self._on_beat_complete:
            self._on_beat_complete(beat)
    
    def set_story_flag(self, flag: str, value: bool = True) -> None:
        """Set a story flag."""
        self.state.story_flags[flag] = value
    
    def get_story_flag(self, flag: str) -> bool:
        """Get a story flag."""
        return self.state.story_flags.get(flag, False)
    
    def record_choice(self, choice_id: str, option: str) -> None:
        """Record a player choice."""
        self.state.choices_made[choice_id] = option
