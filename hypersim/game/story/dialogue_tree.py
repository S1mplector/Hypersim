"""Dialogue tree system for branching conversations."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class DialogueConditionType(Enum):
    """Types of conditions for dialogue options."""
    NONE = "none"
    STORY_FLAG = "story_flag"
    AFFINITY = "affinity"
    ITEM = "item"
    DIMENSION = "dimension"
    EVOLUTION = "evolution"


@dataclass
class DialogueCondition:
    """A condition that must be met for a dialogue option."""
    type: DialogueConditionType = DialogueConditionType.NONE
    key: str = ""
    value: any = None
    comparison: str = "=="  # ==, !=, >, <, >=, <=


@dataclass
class DialogueEffect:
    """An effect triggered by selecting a dialogue option."""
    type: str  # "affinity", "flag", "item", "lore", "event"
    target: str
    value: any


@dataclass
class DialogueChoice:
    """A choice the player can make in dialogue."""
    id: str
    text: str
    next_node: Optional[str] = None
    conditions: List[DialogueCondition] = field(default_factory=list)
    effects: List[DialogueEffect] = field(default_factory=list)
    ends_dialogue: bool = False


@dataclass
class DialogueNode:
    """A single node in a dialogue tree."""
    id: str
    speaker: str = ""
    text: str = ""
    
    # Styling
    portrait: Optional[str] = None
    mood: str = "neutral"  # neutral, happy, sad, angry, mysterious
    
    # Flow
    choices: List[DialogueChoice] = field(default_factory=list)
    auto_next: Optional[str] = None  # Automatically continue to this node
    delay: float = 0.0  # Delay before showing (for dramatic effect)
    
    # Effects
    on_enter_effects: List[DialogueEffect] = field(default_factory=list)
    
    # Conditional display
    conditions: List[DialogueCondition] = field(default_factory=list)


class DialogueTree:
    """A complete dialogue tree with multiple nodes."""
    
    def __init__(self, id: str, title: str = ""):
        self.id = id
        self.title = title
        self.nodes: Dict[str, DialogueNode] = {}
        self.start_node: Optional[str] = None
        self.current_node: Optional[str] = None
        
        # Runtime
        self._context: Dict[str, any] = {}
        self._on_effect: Optional[Callable[[DialogueEffect], None]] = None
    
    def add_node(self, node: DialogueNode) -> None:
        """Add a node to the tree."""
        self.nodes[node.id] = node
        if self.start_node is None:
            self.start_node = node.id
    
    def start(self, context: Optional[Dict] = None) -> Optional[DialogueNode]:
        """Start the dialogue from the beginning."""
        self._context = context or {}
        self.current_node = self.start_node
        return self.get_current_node()
    
    def get_current_node(self) -> Optional[DialogueNode]:
        """Get the current dialogue node."""
        if not self.current_node:
            return None
        return self.nodes.get(self.current_node)
    
    def get_available_choices(self) -> List[DialogueChoice]:
        """Get choices available at the current node."""
        node = self.get_current_node()
        if not node:
            return []
        
        available = []
        for choice in node.choices:
            if self._check_conditions(choice.conditions):
                available.append(choice)
        
        return available
    
    def select_choice(self, choice_id: str) -> Optional[DialogueNode]:
        """Select a choice and advance the dialogue."""
        node = self.get_current_node()
        if not node:
            return None
        
        choice = None
        for c in node.choices:
            if c.id == choice_id:
                choice = c
                break
        
        if not choice:
            return None
        
        # Apply effects
        for effect in choice.effects:
            self._apply_effect(effect)
        
        # Check for end
        if choice.ends_dialogue:
            self.current_node = None
            return None
        
        # Move to next node
        self.current_node = choice.next_node
        
        next_node = self.get_current_node()
        if next_node:
            # Apply on_enter effects
            for effect in next_node.on_enter_effects:
                self._apply_effect(effect)
        
        return next_node
    
    def advance(self) -> Optional[DialogueNode]:
        """Advance dialogue (for nodes with auto_next)."""
        node = self.get_current_node()
        if not node or not node.auto_next:
            return None
        
        self.current_node = node.auto_next
        
        next_node = self.get_current_node()
        if next_node:
            for effect in next_node.on_enter_effects:
                self._apply_effect(effect)
        
        return next_node
    
    def _check_conditions(self, conditions: List[DialogueCondition]) -> bool:
        """Check if all conditions are met."""
        for cond in conditions:
            if not self._check_condition(cond):
                return False
        return True
    
    def _check_condition(self, cond: DialogueCondition) -> bool:
        """Check a single condition."""
        if cond.type == DialogueConditionType.NONE:
            return True
        
        value = self._context.get(cond.key)
        target = cond.value
        
        if cond.comparison == "==":
            return value == target
        elif cond.comparison == "!=":
            return value != target
        elif cond.comparison == ">":
            return value > target
        elif cond.comparison == "<":
            return value < target
        elif cond.comparison == ">=":
            return value >= target
        elif cond.comparison == "<=":
            return value <= target
        
        return False
    
    def _apply_effect(self, effect: DialogueEffect) -> None:
        """Apply a dialogue effect."""
        if self._on_effect:
            self._on_effect(effect)
        
        # Also update context
        if effect.type == "flag":
            self._context[effect.target] = effect.value
    
    def set_context(self, key: str, value: any) -> None:
        """Set a context value."""
        self._context[key] = value
    
    def on_effect(self, callback: Callable[[DialogueEffect], None]) -> None:
        """Set the effect callback."""
        self._on_effect = callback


# ============================================================================
# Pre-built dialogue trees for campaign
# ============================================================================

def create_echo_dialogues() -> Dict[str, DialogueTree]:
    """Create Echo's dialogue trees."""
    trees = {}
    
    # First meeting
    meet = DialogueTree("meet_echo", "Meeting Echo")
    meet.add_node(DialogueNode(
        id="start",
        speaker="???",
        text="...hello? Is someone there? I felt a vibration... different from the others.",
        auto_next="intro",
    ))
    meet.add_node(DialogueNode(
        id="intro",
        speaker="Echo",
        text="You're new here, aren't you? I can tell. Your resonance is... fresh. Unweathered by the endless line.",
        choices=[
            DialogueChoice(
                id="who",
                text="Who are you?",
                next_node="who_response",
            ),
            DialogueChoice(
                id="where",
                text="Where am I?",
                next_node="where_response",
            ),
            DialogueChoice(
                id="what",
                text="What do you mean by 'resonance'?",
                next_node="resonance_response",
            ),
        ],
    ))
    meet.add_node(DialogueNode(
        id="who_response",
        speaker="Echo",
        text="I am Echo. I've been here... well, I don't know how long. Time doesn't mean much when you can only move left and right. I've been bouncing between the same points, listening to the vibrations of others passing by.",
        auto_next="continue_1",
    ))
    meet.add_node(DialogueNode(
        id="where_response",
        speaker="Echo",
        text="This is the Line. The only reality I've ever known. An infinite stretch of existence where you can only go forward or backward. There is no 'up'. There is no 'side'. Just... the Line.",
        auto_next="continue_1",
    ))
    meet.add_node(DialogueNode(
        id="resonance_response",
        speaker="Echo",
        text="Everything on the Line vibrates. It's how we sense each other. When you move, you create ripples. I've learned to read those ripples. Yours are unique - like nothing I've ever felt before.",
        auto_next="continue_1",
    ))
    meet.add_node(DialogueNode(
        id="continue_1",
        speaker="Echo",
        text="I've heard stories... whispers in the vibrations... of beings who can move in TWO directions at once. Can you imagine? Being able to dodge a Blocker instead of just... hoping it passes.",
        choices=[
            DialogueChoice(
                id="blockers",
                text="What are Blockers?",
                next_node="blockers",
            ),
            DialogueChoice(
                id="two_directions",
                text="Two directions? Is that possible?",
                next_node="two_dirs",
            ),
            DialogueChoice(
                id="bye",
                text="I should go explore.",
                next_node="bye",
                effects=[
                    DialogueEffect("affinity", "echo", 5),
                    DialogueEffect("flag", "met_echo", True),
                ],
            ),
        ],
    ))
    meet.add_node(DialogueNode(
        id="blockers",
        speaker="Echo",
        text="Hostile entities. They patrol sections of the Line, destroying anything in their path. You can't go around them - there IS no around. You can only wait, or try to pass when they're moving away.",
        auto_next="continue_1",
    ))
    meet.add_node(DialogueNode(
        id="two_dirs",
        speaker="Echo",
        text="The stories say there are places where the Line... bends. Folds. Becomes something more. They call it a 'plane'. I don't fully understand it, but... I want to. I want to see it.",
        mood="hopeful",
        auto_next="continue_1",
    ))
    meet.add_node(DialogueNode(
        id="bye",
        speaker="Echo",
        text="Be careful out there. The Blockers are relentless. If you find anything... unusual... come tell me. I want to know. I NEED to know if there's more than this.",
        on_enter_effects=[
            DialogueEffect("flag", "met_echo", True),
        ],
    ))
    
    trees["meet_echo"] = meet
    
    # About dimensions
    dims = DialogueTree("echo_dimensions", "Echo Discusses Dimensions")
    dims.add_node(DialogueNode(
        id="start",
        speaker="Echo",
        text="I've been thinking about what those stories mean. If there really are beings who move in TWO directions... what does that even feel like?",
        choices=[
            DialogueChoice(
                id="explain",
                text="Tell me more about what you've heard.",
                next_node="explain",
            ),
            DialogueChoice(
                id="portal",
                text="Have you ever seen one of these 'planes'?",
                next_node="portal",
            ),
        ],
    ))
    dims.add_node(DialogueNode(
        id="explain",
        speaker="Echo",
        text="The vibrations speak of 'perpendicular' motion. A direction that is... at right angles to our Line. I can't picture it. My mind wasn't built to picture it. But the mathematics... the mathematics suggest it's real.",
        auto_next="math",
    ))
    dims.add_node(DialogueNode(
        id="math",
        speaker="Echo",
        text="Think about it. We have one number - our position on the Line. But what if there were TWO numbers? What if you could be at position (5, 3) instead of just position 5?",
        mood="excited",
        choices=[
            DialogueChoice(
                id="understand",
                text="That would mean infinite positions...",
                next_node="infinite",
                effects=[DialogueEffect("affinity", "echo", 10)],
            ),
            DialogueChoice(
                id="confused",
                text="I don't understand.",
                next_node="confused",
            ),
        ],
    ))
    dims.add_node(DialogueNode(
        id="infinite",
        speaker="Echo",
        text="YES! You understand! Not just infinite along one axis, but infinite in EVERY direction! The stories say there are beings who live in such a space. They call it... Flatland.",
        mood="excited",
        on_enter_effects=[
            DialogueEffect("lore", "lore_dimensions_intro", True),
        ],
    ))
    dims.add_node(DialogueNode(
        id="confused",
        speaker="Echo",
        text="Neither do I, fully. But I know this: there is more to existence than left and right. And I intend to find it.",
    ))
    dims.add_node(DialogueNode(
        id="portal",
        speaker="Echo",
        text="No. But I've HEARD one. At the far end of the Line, there's a strange vibration. Different from Blockers. Different from anything. It pulses... like it's breathing.",
        mood="mysterious",
        auto_next="portal_2",
    ))
    dims.add_node(DialogueNode(
        id="portal_2",
        speaker="Echo",
        text="I've been too afraid to approach it. The vibration is... overwhelming. But maybe together... maybe we could see what it is?",
        choices=[
            DialogueChoice(
                id="yes",
                text="Let's investigate it.",
                next_node="yes",
                effects=[
                    DialogueEffect("flag", "echo_portal_quest", True),
                    DialogueEffect("affinity", "echo", 15),
                ],
            ),
            DialogueChoice(
                id="no",
                text="Not yet. I'm not ready.",
                next_node="no",
            ),
        ],
    ))
    dims.add_node(DialogueNode(
        id="yes",
        speaker="Echo",
        text="Really? You'd do that? I... thank you. Head toward the positive end of the Line. I'll follow your resonance. Together, we can face whatever it is.",
        mood="happy",
    ))
    dims.add_node(DialogueNode(
        id="no",
        speaker="Echo",
        text="I understand. It's terrifying. But when you're ready... I'll be here. Bouncing between the same two points. Waiting.",
        mood="sad",
    ))
    
    trees["echo_dimensions"] = dims
    
    return trees


def create_all_campaign_dialogues() -> Dict[str, DialogueTree]:
    """Create all campaign dialogue trees."""
    all_trees = {}
    
    all_trees.update(create_echo_dialogues())
    # Add more NPC dialogues here...
    
    return all_trees
