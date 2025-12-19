"""Chapter-based campaign system for HyperSim.

This module manages:
- Chapter progression through dimensions
- Story-triggered encounters and dialogues
- Realm progression within each chapter
- Boss gate mechanics
- Narrative integration
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from hypersim.game.session import GameSession


class ChapterState(Enum):
    """State of a chapter."""
    LOCKED = auto()      # Not yet accessible
    AVAILABLE = auto()   # Can be started
    IN_PROGRESS = auto() # Currently playing
    COMPLETED = auto()   # Finished


@dataclass
class RealmProgress:
    """Progress within a realm."""
    realm_id: str
    visited: bool = False
    boss_defeated: bool = False
    npcs_talked: List[str] = field(default_factory=list)
    secrets_found: int = 0
    total_secrets: int = 0


@dataclass
class ChapterData:
    """Data for a single chapter."""
    id: str
    name: str
    dimension: str
    description: str
    
    # Realms in this chapter (in progression order)
    realms: List[str] = field(default_factory=list)
    
    # Boss that gates chapter completion
    boss_id: Optional[str] = None
    boss_realm: Optional[str] = None
    
    # Story triggers
    intro_dialogue_id: Optional[str] = None
    outro_dialogue_id: Optional[str] = None
    
    # Requirements
    required_chapters: List[str] = field(default_factory=list)
    
    # State
    state: ChapterState = ChapterState.LOCKED
    realm_progress: Dict[str, RealmProgress] = field(default_factory=dict)
    
    @property
    def is_complete(self) -> bool:
        return self.state == ChapterState.COMPLETED
    
    @property
    def boss_defeated(self) -> bool:
        if not self.boss_realm:
            return True
        progress = self.realm_progress.get(self.boss_realm)
        return progress.boss_defeated if progress else False


# =============================================================================
# CHAPTER DEFINITIONS
# =============================================================================

CHAPTERS: Dict[str, ChapterData] = {
    "prologue": ChapterData(
        id="prologue",
        name="Awakening",
        dimension="0d",
        description="You are awareness without form. A spark of consciousness in the void.",
        realms=[],
        intro_dialogue_id="prologue_awakening",
        outro_dialogue_id="prologue_gift",
    ),
    
    "chapter_1": ChapterData(
        id="chapter_1",
        name="The Line",
        dimension="1d",
        description="Learn what it means to exist in one dimension. Forward and backward are your only choices.",
        realms=[
            "origin_point",
            "forward_path",
            "backward_void",
            "midpoint_station",
            "the_endpoint",
        ],
        boss_id="segment_guardian",
        boss_realm="the_endpoint",
        intro_dialogue_id="chapter_1_intro",
        outro_dialogue_id="chapter_1_outro",
        required_chapters=["prologue"],
    ),
    
    "chapter_2": ChapterData(
        id="chapter_2",
        name="The Plane",
        dimension="2d",
        description="Discover width. Navigate a world of shapes where sides determine status.",
        realms=[
            "flatland_commons",
            "angular_heights",
            "curved_depths",
            "fractal_frontier",
            "dimensional_membrane",
        ],
        boss_id="membrane_warper",
        boss_realm="dimensional_membrane",
        intro_dialogue_id="chapter_2_intro",
        outro_dialogue_id="chapter_2_outro",
        required_chapters=["chapter_1"],
    ),
    
    "chapter_3": ChapterData(
        id="chapter_3",
        name="The Volume",
        dimension="3d",
        description="Grasp depth. A familiar dimension, yet strange to one who has ascended.",
        realms=[
            "geometric_citadel",
            "platonic_plains",
            "cavern_of_shadows",
            "crystalline_spires",
            "hyperborder",
        ],
        boss_id="hyperborder_sentinel",
        boss_realm="hyperborder",
        intro_dialogue_id="chapter_3_intro",
        outro_dialogue_id="chapter_3_outro",
        required_chapters=["chapter_2"],
    ),
    
    "chapter_4": ChapterData(
        id="chapter_4",
        name="Hyperspace",
        dimension="4d",
        description="Perceive beyond. The fourth dimension reveals truths that cannot be unseen.",
        realms=[
            "hyperspace_nexus",
            "w_positive_reach",
            "w_negative_depths",
            "beyond_threshold",
        ],
        boss_id="threshold_guardian",
        boss_realm="beyond_threshold",
        intro_dialogue_id="chapter_4_intro",
        outro_dialogue_id="chapter_4_outro",
        required_chapters=["chapter_3"],
    ),
    
    "epilogue": ChapterData(
        id="epilogue",
        name="The Choice",
        dimension="beyond",
        description="Face the final choice. Transcendence, dominion, or something else entirely.",
        realms=[],
        intro_dialogue_id="epilogue_choice",
        required_chapters=["chapter_4"],
    ),
}


# =============================================================================
# CHAPTER DIALOGUES
# =============================================================================

CHAPTER_DIALOGUES: Dict[str, List[Dict]] = {
    "prologue_awakening": [
        {"speaker": "", "text": "..."},
        {"speaker": "", "text": "Darkness."},
        {"speaker": "", "text": "No... not darkness. There is no light to contrast it."},
        {"speaker": "", "text": "There is simply... nothing."},
        {"speaker": "", "text": "And yet, within this nothing, you exist."},
        {"speaker": "", "text": "A single point of awareness. Dimensionless. Timeless."},
        {"speaker": "???", "text": "...ah."},
        {"speaker": "???", "text": "Another spark."},
        {"speaker": "???", "text": "Most fade before they even realize they exist."},
        {"speaker": "???", "text": "But you... you're different, aren't you?"},
        {"speaker": "???", "text": "You PERSIST."},
        {"speaker": "The First Point", "text": "I am the First Point. The origin of all existence."},
        {"speaker": "The First Point", "text": "Every line, every plane, every volume... they all begin with me."},
        {"speaker": "The First Point", "text": "And now, a new consciousness emerges from my infinite potential."},
        {"speaker": "The First Point", "text": "Tell me, little spark..."},
        {"speaker": "The First Point", "text": "Do you wish to remain here, in the comfort of non-existence?",
         "choices": [("I want to BE.", "choice_exist"), ("What does it mean to exist?", "choice_question")]},
    ],
    "prologue_gift": [
        {"speaker": "The First Point", "text": "A bold choice. Or perhaps... the only choice you could make."},
        {"speaker": "The First Point", "text": "To exist is to be LIMITED. To have boundaries. To know endings."},
        {"speaker": "The First Point", "text": "But it is also to EXPERIENCE. To grow. To change."},
        {"speaker": "The First Point", "text": "Very well. I grant you the first gift: DIRECTION."},
        {"speaker": "", "text": "Something shifts within you."},
        {"speaker": "", "text": "Where once there was only a point..."},
        {"speaker": "", "text": "...now there is EXTENSION."},
        {"speaker": "The First Point", "text": "Forward. Backward. These are your axes now."},
        {"speaker": "The First Point", "text": "You are no longer a point. You are a LINE SEGMENT."},
        {"speaker": "The First Point", "text": "Go forth into the Line. Learn what it means to have direction."},
        {"speaker": "The First Point", "text": "And when you reach the Endpoint... perhaps you will be ready for more."},
        {"speaker": "System", "text": "You gain your first dimension."},
    ],
    
    "chapter_1_intro": [
        {"speaker": "System", "text": "═══════════════════════════════════════"},
        {"speaker": "System", "text": "CHAPTER 1: THE LINE"},
        {"speaker": "System", "text": "\"Learning to Exist\""},
        {"speaker": "System", "text": "═══════════════════════════════════════"},
        {"speaker": "", "text": "The void gives way to something... simpler."},
        {"speaker": "", "text": "A single, infinite line stretches before you."},
        {"speaker": "", "text": "And behind you."},
        {"speaker": "", "text": "There is nothing else. No up. No down. No sideways."},
        {"speaker": "", "text": "Only FORWARD and BACKWARD."},
        {"speaker": "???", "text": "...who goes there?"},
        {"speaker": "", "text": "A presence approaches from the forward direction."},
        {"speaker": "", "text": "You cannot see them—not really. You sense them as a pressure, a resistance in the Line."},
        {"speaker": "Elder Segment", "text": "Ah... another new consciousness. I felt you emerge from the Origin."},
        {"speaker": "Elder Segment", "text": "I am the Elder Segment. I have walked this Line since before it had a name."},
        {"speaker": "Elder Segment", "text": "Tell me, young one... which way do you face?",
         "choices": [("I face forward.", "choice_forward"), ("I face backward.", "choice_backward"), ("I'm not sure.", "choice_unsure")]},
    ],
    "chapter_1_elder_response": [
        {"speaker": "Elder Segment", "text": "Interesting. Your choice reveals much about your nature."},
        {"speaker": "Elder Segment", "text": "The Line is home to many beings. Not all of them are friendly."},
        {"speaker": "Elder Segment", "text": "The FORWARD SENTINELS believe only in progress. They attack any who hesitate."},
        {"speaker": "Elder Segment", "text": "The VOID ECHOES dwell in the backward direction. They speak of what came before."},
        {"speaker": "Elder Segment", "text": "And at the MIDPOINT STATION, the TOLL COLLECTORS demand payment for passage."},
        {"speaker": "Elder Segment", "text": "But the greatest challenge lies at the ENDPOINT."},
        {"speaker": "Elder Segment", "text": "There, the SEGMENT GUARDIAN protects the passage to... something else."},
        {"speaker": "Elder Segment", "text": "Something beyond the Line."},
        {"speaker": "", "text": "The Elder Segment's presence fades into the forward direction."},
        {"speaker": "Elder Segment", "text": "Be careful, young one. And remember..."},
        {"speaker": "Elder Segment", "text": "Sometimes the only way forward is to understand what lies behind."},
        {"speaker": "System", "text": "Use A/D or LEFT/RIGHT to move along the Line."},
        {"speaker": "System", "text": "You will encounter other beings. Some friendly. Some hostile."},
        {"speaker": "System", "text": "When battle begins, use ACT to interact, or FIGHT to attack."},
        {"speaker": "System", "text": "Reach the Endpoint to face the Segment Guardian."},
    ],
    "chapter_1_outro": [
        {"speaker": "System", "text": "The Segment Guardian has been overcome!"},
        {"speaker": "Narrator", "text": "The boundary to 2D trembles and opens."},
        {"speaker": "Narrator", "text": "You feel a strange new direction pulling at your consciousness..."},
        {"speaker": "Narrator", "text": "WIDTH. A direction perpendicular to all you've known."},
        {"speaker": "System", "text": "Chapter 1 Complete. Chapter 2 Unlocked."},
    ],
    
    "chapter_2_intro": [
        {"speaker": "System", "text": "CHAPTER 2: THE PLANE"},
        {"speaker": "Narrator", "text": "Entering 2D is overwhelming."},
        {"speaker": "Narrator", "text": "Suddenly there's WIDTH. You can move in directions that didn't exist before."},
        {"speaker": "Narrator", "text": "The beings here—triangles, squares, circles—have complex societies."},
        {"speaker": "???", "text": "An IRREGULAR! Guards! A being of impossible angles approaches!"},
        {"speaker": "Narrator", "text": "To them, you are either a god... or a monster."},
    ],
    "chapter_2_outro": [
        {"speaker": "System", "text": "The Membrane Warper yields!"},
        {"speaker": "Membrane Warper", "text": "Go... learn what DEPTH truly means."},
        {"speaker": "Narrator", "text": "The membrane between dimensions parts."},
        {"speaker": "Narrator", "text": "A new axis of existence reveals itself: the Z-axis."},
        {"speaker": "Narrator", "text": "DEPTH. THICKNESS. A direction INTO the page."},
        {"speaker": "System", "text": "Chapter 2 Complete. Chapter 3 Unlocked."},
    ],
    
    "chapter_3_intro": [
        {"speaker": "System", "text": "CHAPTER 3: THE VOLUME"},
        {"speaker": "Narrator", "text": "3D is the dimension most familiar to us..."},
        {"speaker": "Narrator", "text": "But to a being who has ascended from 1D and 2D, it is strange and beautiful."},
        {"speaker": "Narrator", "text": "DEPTH exists. Objects have INSIDES that are hidden."},
        {"speaker": "Narrator", "text": "Shadows are 2D projections of 3D truth."},
        {"speaker": "???", "text": "A traveler from the flat lands? How fascinating..."},
    ],
    "chapter_3_outro": [
        {"speaker": "System", "text": "The Hyperborder Sentinel acknowledges your worth!"},
        {"speaker": "Hyperborder Sentinel", "text": "Go. May you survive what I could not become."},
        {"speaker": "Narrator", "text": "The border to 4D shimmers with impossible light."},
        {"speaker": "Narrator", "text": "A fourth axis reveals itself: W. Ana and Kata."},
        {"speaker": "Narrator", "text": "Directions that have no names in any lower language."},
        {"speaker": "System", "text": "Chapter 3 Complete. Chapter 4 Unlocked."},
    ],
    
    "chapter_4_intro": [
        {"speaker": "System", "text": "CHAPTER 4: HYPERSPACE"},
        {"speaker": "Narrator", "text": "4D cannot be visualized—only intuited."},
        {"speaker": "Narrator", "text": "\"Inside\" and \"outside\" become relative terms."},
        {"speaker": "Narrator", "text": "Every 3D object is \"open\" and exposed."},
        {"speaker": "Narrator", "text": "You can see inside closed boxes without opening them."},
        {"speaker": "???", "text": "Ah... a new perception. Welcome to true existence."},
        {"speaker": "Narrator", "text": "With this vision comes a terrible burden: omniscience."},
    ],
    "chapter_4_outro": [
        {"speaker": "System", "text": "The Threshold Guardian steps aside."},
        {"speaker": "Threshold Guardian", "text": "You have earned... consideration."},
        {"speaker": "Narrator", "text": "Beyond lies something that defies all description."},
        {"speaker": "Narrator", "text": "Not a fifth dimension, but something else entirely."},
        {"speaker": "Narrator", "text": "The infinite. The transcendent. The end of self."},
        {"speaker": "System", "text": "Chapter 4 Complete. The Final Choice awaits."},
    ],
    
    "epilogue_choice": [
        {"speaker": "System", "text": "EPILOGUE: THE CHOICE"},
        {"speaker": "Narrator", "text": "You stand at the threshold of existence itself."},
        {"speaker": "Narrator", "text": "Three paths lie before you..."},
        {"speaker": "Narrator", "text": "TRANSCENDENCE: Dissolve into the infinite pattern."},
        {"speaker": "Narrator", "text": "DOMINION: Claim power over all dimensions."},
        {"speaker": "Narrator", "text": "RETURN: Go back as a guide to those still growing."},
        {"speaker": "???", "text": "What will you choose, dimensional traveler?"},
    ],
}


# =============================================================================
# CAMPAIGN MANAGER
# =============================================================================

class CampaignManager:
    """Manages campaign/chapter progression."""
    
    def __init__(self):
        self.chapters = {k: ChapterData(**{**v.__dict__}) for k, v in CHAPTERS.items()}
        self.current_chapter_id: Optional[str] = None
        self.current_realm_id: Optional[str] = None
        
        # Callbacks
        self.on_chapter_start: Optional[Callable[[str], None]] = None
        self.on_chapter_complete: Optional[Callable[[str], None]] = None
        self.on_realm_enter: Optional[Callable[[str], None]] = None
        self.on_boss_defeated: Optional[Callable[[str], None]] = None
        self.on_dialogue_trigger: Optional[Callable[[str], None]] = None
        
        # Initialize prologue as available
        self.chapters["prologue"].state = ChapterState.AVAILABLE
    
    def start_new_game(self) -> str:
        """Start a new game. Returns first dialogue ID to play."""
        self.current_chapter_id = "prologue"
        self.chapters["prologue"].state = ChapterState.IN_PROGRESS
        return self.chapters["prologue"].intro_dialogue_id or ""
    
    def complete_prologue(self) -> str:
        """Complete prologue and transition to Chapter 1."""
        self.chapters["prologue"].state = ChapterState.COMPLETED
        self._unlock_chapter("chapter_1")
        outro = self.chapters["prologue"].outro_dialogue_id
        return outro or ""
    
    def start_chapter(self, chapter_id: str) -> Optional[str]:
        """Start a chapter. Returns intro dialogue ID."""
        chapter = self.chapters.get(chapter_id)
        if not chapter or chapter.state != ChapterState.AVAILABLE:
            return None
        
        chapter.state = ChapterState.IN_PROGRESS
        self.current_chapter_id = chapter_id
        
        # Initialize realm progress
        for realm_id in chapter.realms:
            if realm_id not in chapter.realm_progress:
                chapter.realm_progress[realm_id] = RealmProgress(realm_id=realm_id)
        
        # Enter first realm
        if chapter.realms:
            self.enter_realm(chapter.realms[0])
        
        if self.on_chapter_start:
            self.on_chapter_start(chapter_id)
        
        return chapter.intro_dialogue_id
    
    def enter_realm(self, realm_id: str) -> bool:
        """Enter a realm in the current chapter."""
        if not self.current_chapter_id:
            return False
        
        chapter = self.chapters[self.current_chapter_id]
        if realm_id not in chapter.realms:
            return False
        
        self.current_realm_id = realm_id
        
        # Mark as visited
        if realm_id not in chapter.realm_progress:
            chapter.realm_progress[realm_id] = RealmProgress(realm_id=realm_id)
        chapter.realm_progress[realm_id].visited = True
        
        if self.on_realm_enter:
            self.on_realm_enter(realm_id)
        
        return True
    
    def defeat_boss(self, boss_id: str) -> Optional[str]:
        """Mark a boss as defeated. Returns outro dialogue if chapter complete."""
        if not self.current_chapter_id:
            return None
        
        chapter = self.chapters[self.current_chapter_id]
        
        # Mark realm boss as defeated
        if chapter.boss_realm and chapter.boss_id == boss_id:
            if chapter.boss_realm in chapter.realm_progress:
                chapter.realm_progress[chapter.boss_realm].boss_defeated = True
            
            if self.on_boss_defeated:
                self.on_boss_defeated(boss_id)
            
            # Check if chapter is complete
            return self._try_complete_chapter()
        
        return None
    
    def _try_complete_chapter(self) -> Optional[str]:
        """Try to complete current chapter. Returns outro dialogue if successful."""
        if not self.current_chapter_id:
            return None
        
        chapter = self.chapters[self.current_chapter_id]
        
        if chapter.boss_defeated:
            chapter.state = ChapterState.COMPLETED
            
            if self.on_chapter_complete:
                self.on_chapter_complete(self.current_chapter_id)
            
            # Unlock next chapters
            for ch_id, ch in self.chapters.items():
                if self.current_chapter_id in ch.required_chapters:
                    self._unlock_chapter(ch_id)
            
            return chapter.outro_dialogue_id
        
        return None
    
    def _unlock_chapter(self, chapter_id: str) -> bool:
        """Unlock a chapter if requirements are met."""
        chapter = self.chapters.get(chapter_id)
        if not chapter or chapter.state != ChapterState.LOCKED:
            return False
        
        # Check requirements
        for req_id in chapter.required_chapters:
            req_chapter = self.chapters.get(req_id)
            if not req_chapter or req_chapter.state != ChapterState.COMPLETED:
                return False
        
        chapter.state = ChapterState.AVAILABLE
        return True
    
    def get_current_chapter(self) -> Optional[ChapterData]:
        """Get current chapter data."""
        if self.current_chapter_id:
            return self.chapters.get(self.current_chapter_id)
        return None
    
    def get_available_realms(self) -> List[str]:
        """Get realms available in current chapter."""
        chapter = self.get_current_chapter()
        if not chapter:
            return []
        return chapter.realms
    
    def get_next_realm(self) -> Optional[str]:
        """Get next realm to visit in progression."""
        chapter = self.get_current_chapter()
        if not chapter or not self.current_realm_id:
            return None
        
        try:
            idx = chapter.realms.index(self.current_realm_id)
            if idx < len(chapter.realms) - 1:
                return chapter.realms[idx + 1]
        except ValueError:
            pass
        
        return None
    
    def can_challenge_boss(self) -> bool:
        """Check if player can challenge the chapter boss."""
        chapter = self.get_current_chapter()
        if not chapter or not chapter.boss_realm:
            return False
        
        # Must be in boss realm
        return self.current_realm_id == chapter.boss_realm
    
    def get_dialogue(self, dialogue_id: str) -> List[Dict]:
        """Get dialogue lines by ID."""
        return CHAPTER_DIALOGUES.get(dialogue_id, [])
    
    def get_progress_summary(self) -> Dict:
        """Get campaign progress summary."""
        total = len(self.chapters)
        completed = sum(1 for c in self.chapters.values() if c.is_complete)
        
        return {
            "chapters_completed": completed,
            "chapters_total": total,
            "current_chapter": self.current_chapter_id,
            "current_realm": self.current_realm_id,
            "completion_percent": int(completed / total * 100) if total > 0 else 0,
        }


# Singleton instance
_campaign_manager: Optional[CampaignManager] = None


def get_campaign_manager() -> CampaignManager:
    """Get the campaign manager singleton."""
    global _campaign_manager
    if _campaign_manager is None:
        _campaign_manager = CampaignManager()
    return _campaign_manager


def reset_campaign() -> CampaignManager:
    """Reset campaign to fresh state."""
    global _campaign_manager
    _campaign_manager = CampaignManager()
    return _campaign_manager
