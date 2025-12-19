"""NPCs for each dimensional realm with rich dialogue and lore.

NPCs provide:
- World-building and lore exposition
- Quest/objective information
- Shop/healing services
- Combat tips and hints
- Emotional connections to the world
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple


class NPCRole(Enum):
    """Roles NPCs can serve."""
    ELDER = auto()      # Provides wisdom and lore
    MERCHANT = auto()   # Sells items
    HEALER = auto()     # Restores HP
    GUIDE = auto()      # Gives directions and hints
    QUESTGIVER = auto() # Assigns objectives
    CITIZEN = auto()    # General inhabitant
    SAGE = auto()       # Deep philosophical insights
    GUARDIAN = auto()   # Warns about dangers ahead


@dataclass
class DialogueLine:
    """A single line of NPC dialogue."""
    text: str
    condition: Optional[str] = None  # Condition to show this line
    response_options: List[str] = field(default_factory=list)
    triggers_event: Optional[str] = None
    gives_item: Optional[str] = None


@dataclass
class NPCDialogue:
    """Complete dialogue tree for an NPC."""
    greeting: str
    lines: Dict[str, DialogueLine] = field(default_factory=dict)
    farewell: str = "..."
    
    # Special dialogues
    first_meeting: Optional[str] = None
    low_hp_dialogue: Optional[str] = None
    post_boss_dialogue: Optional[str] = None


@dataclass
class NPC:
    """A non-player character."""
    id: str
    name: str
    dimension: str
    realm_id: str
    role: NPCRole
    
    # Appearance
    color: Tuple[int, int, int] = (200, 200, 200)
    shape: str = "circle"  # For rendering
    
    # Dialogue
    dialogue: NPCDialogue = field(default_factory=lambda: NPCDialogue("..."))
    
    # Services
    heals: bool = False
    heal_cost: int = 0
    sells_items: List[str] = field(default_factory=list)
    
    # State
    met_before: bool = False
    conversations: int = 0


# =============================================================================
# 1D NPCs
# =============================================================================

NPCS_1D: Dict[str, NPC] = {
    "the_first_point": NPC(
        id="the_first_point",
        name="The First Point",
        dimension="1d",
        realm_id="origin_point",
        role=NPCRole.SAGE,
        color=(255, 255, 200),
        dialogue=NPCDialogue(
            greeting="* A dimensionless presence regards you.",
            first_meeting="""* ...
* Before there was forward or backward...
* Before there was the Line...
* There was only awareness.
* I am that awareness. The First Point.
* And you... you came from me.
* All beings did.""",
            lines={
                "origin": DialogueLine(
                    text="""* The Void knew itself, and I was born.
* From nothing, everything.
* From potential, actual.
* This is the truth of existence:
* To observe is to create.""",
                ),
                "purpose": DialogueLine(
                    text="""* Why do you seek higher dimensions?
* Is the Line not enough?
* ...I see. You seek to understand.
* Then go. Expand your perception.
* But remember: I am still here.
* At the center of all things.""",
                ),
                "wisdom": DialogueLine(
                    text="""* Each dimension you gain...
* Is another way to see the same truth.
* More complex? Yes.
* More true? No.
* The Point contains everything the Tesseract does.
* Just... differently.""",
                ),
            },
            farewell="* The First Point watches you go. It will always watch.",
        ),
    ),
    
    "elder_segment": NPC(
        id="elder_segment",
        name="Elder Segment",
        dimension="1d",
        realm_id="origin_point",
        role=NPCRole.ELDER,
        color=(150, 200, 255),
        dialogue=NPCDialogue(
            greeting="* Elder Segment stretches to acknowledge you.",
            first_meeting="""* Ah, a fellow traveler on the Line!
* I have walked forward for countless cycles.
* Sometimes, I even walk backward!
* (Don't tell the Sentinels I said that.)
* Welcome to the Origin Point, young one.""",
            lines={
                "advice": DialogueLine(
                    text="""* If you're heading to the Endpoint...
* Be respectful to the Guardian.
* It guards the way to something called "2D."
* I don't know what that is, but...
* Those who pass never come back the same.""",
                ),
                "history": DialogueLine(
                    text="""* In the old days, we didn't even have direction.
* Just existence. Just the Point.
* Then came forward. Then came backward.
* Now there are rumors of... sideways?
* Sideways! Can you imagine?!""",
                ),
                "combat_tip": DialogueLine(
                    text="""* If you find yourself in conflict...
* Remember: the Line is simple.
* Attacks can only come from two directions.
* But I hear in higher dimensions...
* Things can attack from anywhere!""",
                ),
            },
            farewell="* May the Line extend ever forward for you!",
        ),
    ),
    
    "tired_traveler": NPC(
        id="tired_traveler",
        name="Tired Traveler",
        dimension="1d",
        realm_id="forward_path",
        role=NPCRole.CITIZEN,
        color=(180, 180, 200),
        heals=True,
        heal_cost=0,
        dialogue=NPCDialogue(
            greeting="* A weary segment rests on the Line.",
            first_meeting="""* Oh! Another traveler!
* I've been walking forward for so long...
* But I refuse to turn back.
* Backward is... no. I won't go backward.
* Here, rest with me a moment.""",
            lines={
                "rest": DialogueLine(
                    text="""* Just... catch your breath.
* The Forward Path is long.
* But we'll make it. We have to.
* (Your HP is restored.)""",
                    triggers_event="heal_player",
                ),
                "story": DialogueLine(
                    text="""* I've heard tales of the Endpoint.
* Where the Line meets something... bigger.
* Some say if you reach it...
* You gain the ability to move... SIDEWAYS.
* Imagine! A whole new direction!""",
                ),
            },
            farewell="* Rest when you need to. The Line will wait.",
            low_hp_dialogue="* Oh dear, you look hurt! Let me help. (HP restored)",
        ),
    ),
    
    "innkeeper_segment": NPC(
        id="innkeeper_segment",
        name="Innkeeper Segment",
        dimension="1d",
        realm_id="midpoint_station",
        role=NPCRole.MERCHANT,
        color=(200, 180, 100),
        heals=True,
        heal_cost=5,
        sells_items=["dimensional_candy", "line_tonic", "segment_shield"],
        dialogue=NPCDialogue(
            greeting="* Welcome to the Midpoint Inn!",
            first_meeting="""* A newcomer! Welcome, welcome!
* This is the Midpoint Station - exactly
* halfway along the Line.
* Travelers rest here before the final push.
* What can I get for you?""",
            lines={
                "shop": DialogueLine(
                    text="""* I've got Line Tonics for 10G - heals you right up!
* Dimensional Candies for 15G - tastes different to everyone!
* And Segment Shields for 25G - blocks one hit!
* What'll it be?""",
                ),
                "rest": DialogueLine(
                    text="""* A full rest costs 5G.
* You'll wake up fully refreshed!
* The bed's not much to look at...
* Being one-dimensional and all.
* But it's comfortable!""",
                ),
                "rumors": DialogueLine(
                    text="""* Heard an interesting rumor recently.
* Some travelers who went to the Endpoint...
* They came back talking about "width."
* As if there's more than forward and back!
* Crazy talk, if you ask me.""",
                ),
            },
            farewell="* Come back anytime! The Midpoint's always here!",
        ),
    ),
    
    "the_philosopher": NPC(
        id="the_philosopher",
        name="The Philosopher",
        dimension="1d",
        realm_id="backward_void",
        role=NPCRole.SAGE,
        color=(100, 100, 150),
        dialogue=NPCDialogue(
            greeting="* A figure contemplates the void behind.",
            first_meeting="""* Ah... you came backward.
* Most don't. Most fear what's behind the origin.
* But you... you wonder.
* What was before the beginning?
* I've been asking that question for eons.""",
            lines={
                "void": DialogueLine(
                    text="""* The Void behind the Origin...
* It's not nothing. It's not something.
* It's... potential. Undifferentiated potential.
* Before the First Point knew itself.
* We came from that. We can never return.""",
                ),
                "existence": DialogueLine(
                    text="""* Why does anything exist at all?
* The Void didn't have to become aware.
* But it did. And here we are.
* One-dimensional beings pondering infinity.
* The universe has a sense of humor.""",
                ),
                "higher": DialogueLine(
                    text="""* They say there are dimensions beyond 4D.
* Five, six, ten, infinite...
* I wonder if even THOSE beings...
* Look at THEIR void and wonder
* what came before.""",
                ),
            },
            farewell="* Ponder well, traveler. Questions are more valuable than answers.",
        ),
    ),
}

# =============================================================================
# 2D NPCs  
# =============================================================================

NPCS_2D: Dict[str, NPC] = {
    "mayor_hexagon": NPC(
        id="mayor_hexagon",
        name="Mayor Hexagon",
        dimension="2d",
        realm_id="flatland_commons",
        role=NPCRole.ELDER,
        color=(200, 150, 100),
        dialogue=NPCDialogue(
            greeting="* The six-sided Mayor regards you with dignity.",
            first_meeting="""* Ah! A visitor from... elsewhere!
* Welcome to Flatland Commons!
* I am Mayor Hexagon, keeper of order.
* Six sides, six responsibilities:
* Justice, Commerce, Safety, Culture, Health, Progress!""",
            lines={
                "society": DialogueLine(
                    text="""* In Flatland, sides matter.
* Triangles are workers. Squares are merchants.
* Pentagons are professionals. Hexagons govern.
* And Circles... Circles are priests.
* It's been this way since the Flat Beginning.""",
                ),
                "visitor": DialogueLine(
                    text="""* You're from 1D originally, yes?
* I can tell - you still move like you're on a line.
* Don't worry. You'll learn to appreciate WIDTH.
* It changes everything. Trust me.""",
                ),
                "warning": DialogueLine(
                    text="""* Be careful in the Angular Heights.
* The Triangles are... proud.
* And in the Curved Depths, the Circles can be...
* Let's say "philosophically intense."
* Stick to the Commons until you find your footing.""",
                ),
            },
            farewell="* May your angles be regular and your area maximized!",
        ),
    ),
    
    "young_triangle": NPC(
        id="young_triangle",
        name="Young Triangle",
        dimension="2d",
        realm_id="flatland_commons",
        role=NPCRole.CITIZEN,
        color=(255, 150, 150),
        dialogue=NPCDialogue(
            greeting="* An excited young triangle bounces over.",
            first_meeting="""* Ooh! You're from another dimension, right?!
* Is it true you used to be a LINE?!
* What's it like having only ONE direction?!
* Did you feel squished?!
* This is so COOL!""",
            lines={
                "questions": DialogueLine(
                    text="""* Is 1D really just forward and backward?!
* Can you show me what it was like?!
* No wait, I probably can't perceive it anyway...
* Ugh! Being 2D is so LIMITING!
* I wanna be a CUBE someday!""",
                ),
                "dreams": DialogueLine(
                    text="""* My parents say Triangles can't be Cubes.
* But I don't believe them!
* If a Line can become a Triangle...
* Then a Triangle can become a Tetrahedron!
* I'll find a way!""",
                ),
            },
            farewell="* Come back and tell me about 3D when you get there!",
        ),
    ),
    
    "high_priest_circle": NPC(
        id="high_priest_circle",
        name="High Priest Circle",
        dimension="2d",
        realm_id="curved_depths",
        role=NPCRole.SAGE,
        color=(200, 100, 255),
        dialogue=NPCDialogue(
            greeting="* Perfect roundness greets you.",
            first_meeting="""* Welcome, ascending one.
* We Circles have meditated on π for eons.
* An infinite number, never repeating.
* In it, we see the truth of existence:
* Patterns without patterns. Order in chaos.""",
            lines={
                "pi": DialogueLine(
                    text="""* 3.14159265358979323846...
* Every digit holds meaning.
* Somewhere in π, your entire life is written.
* As is mine. As is everyone's.
* The circle contains all things.""",
                ),
                "transcendence": DialogueLine(
                    text="""* You seek 3D. Then 4D.
* But know this: dimension is not progress.
* A Circle in 2D has infinite sides.
* A Sphere in 3D is but a stack of Circles.
* The truth is the same at every level.""",
                ),
                "wisdom": DialogueLine(
                    text="""* The path to higher dimensions...
* Is not through complexity.
* It is through simplicity pushed to infinity.
* A Circle is a polygon with infinite sides.
* Become infinite in your current form first.""",
                ),
            },
            farewell="* May your circumference encircle truth.",
        ),
    ),
    
    "fractal_hermit": NPC(
        id="fractal_hermit",
        name="Fractal Hermit",
        dimension="2d",
        realm_id="fractal_frontier",
        role=NPCRole.SAGE,
        color=(100, 200, 150),
        dialogue=NPCDialogue(
            greeting="* An infinitely complex shape acknowledges you.",
            first_meeting="""* You... can see me?
* Most beings can't. I'm too detailed.
* They see a smudge, a blur.
* But you... you see the recursion.
* Welcome to the Fractal Frontier.""",
            lines={
                "self": DialogueLine(
                    text="""* I am the same at every scale.
* Zoom in: still me. Zoom out: still me.
* Is that not beautiful?
* To be equally complex everywhere?
* The simple shapes think it's madness.""",
                ),
                "dimensions": DialogueLine(
                    text="""* Here's a secret the regulars don't know:
* I'm not quite 2D.
* My dimension is... fractional.
* 1.26, 1.58, 2.73...
* Dimensions aren't just integers, you see.""",
                ),
                "advice": DialogueLine(
                    text="""* The Dimensional Membrane is near.
* Beyond it, 3D awaits.
* But be warned: in 3D, fractals become...
* Even more complex. More beautiful.
* And more dangerous.""",
                ),
            },
            farewell="* May your coastline be infinite.",
        ),
    ),
}

# =============================================================================
# 3D NPCs
# =============================================================================

NPCS_3D: Dict[str, NPC] = {
    "king_dodecahedron": NPC(
        id="king_dodecahedron",
        name="King Dodecahedron",
        dimension="3d",
        realm_id="geometric_citadel",
        role=NPCRole.ELDER,
        color=(255, 200, 100),
        dialogue=NPCDialogue(
            greeting="* Twelve pentagonal faces turn to regard you.",
            first_meeting="""* A visitor from the lower dimensions!
* I am King Dodecahedron, ruler of the Citadel.
* Twelve faces, thirty edges, twenty vertices.
* The most noble of Platonic solids!
* Welcome to true, volumetric existence!""",
            lines={
                "kingdom": DialogueLine(
                    text="""* The Geometric Citadel has stood for ages.
* Here, all polyhedra live in harmony.
* Cubes build our walls. Spheres light our halls.
* Pyramids guard our gates. Tetrahedra scout ahead.
* And we Dodecahedra? We rule with wisdom.""",
                ),
                "platonic": DialogueLine(
                    text="""* There are only five Platonic solids.
* Tetrahedron, Cube, Octahedron, Dodecahedron, Icosahedron.
* Each is perfect. Each is regular.
* Why only five? A mystery of 3D.
* Perhaps in 4D there are more...""",
                ),
                "hyperspace": DialogueLine(
                    text="""* Beyond the Citadel lies the Hyperborder.
* There, 3D meets 4D.
* The Tesseract Guardian waits.
* It will test you. Harshly.
* But if you pass... you'll see TRUE depth.""",
                ),
            },
            farewell="* May all your faces be regular!",
        ),
    ),
    
    "sphere_oracle": NPC(
        id="sphere_oracle",
        name="Sphere Oracle",
        dimension="3d",
        realm_id="geometric_citadel",
        role=NPCRole.SAGE,
        color=(200, 200, 255),
        dialogue=NPCDialogue(
            greeting="* A perfect sphere hovers, reflecting everything.",
            first_meeting="""* I see you. All of you.
* Every angle. Every surface.
* I am the Sphere Oracle.
* I reflect truth.
* What do you wish to see?""",
            lines={
                "prophecy": DialogueLine(
                    text="""* I see your path.
* Through 3D, into 4D.
* And beyond? ...
* Beyond is cloudy. Even I cannot see.
* But the journey will change you.""",
                ),
                "self": DialogueLine(
                    text="""* Why is the sphere considered perfect?
* Because it is the same in every direction.
* No vertices to favor. No edges to walk.
* Pure, continuous surface.
* The circle's 3D truth.""",
                ),
                "warning": DialogueLine(
                    text="""* Beware the Cavern of Shadows.
* In darkness, your 3D nature casts 2D shadows.
* Some shadows... remember being flat.
* They are jealous of your depth.
* They may try to flatten you.""",
                ),
            },
            farewell="* Reflect on what you've learned.",
        ),
    ),
    
    "shadow_sage": NPC(
        id="shadow_sage",
        name="Shadow Sage",
        dimension="3d",
        realm_id="cavern_of_shadows",
        role=NPCRole.SAGE,
        color=(80, 80, 100),
        dialogue=NPCDialogue(
            greeting="* A shadow moves independently of any source.",
            first_meeting="""* Don't be alarmed.
* I am a shadow that remembers.
* Remembers being 2D. Being flat.
* Before I was cast by something 3D.
* Now I'm... between.""",
            lines={
                "between": DialogueLine(
                    text="""* I'm not truly 3D. Not truly 2D.
* I'm a projection. A memory.
* But in that in-between space...
* I see truths that pure dimensions miss.
* Every 3D being casts a 2D shadow.""",
                ),
                "truth": DialogueLine(
                    text="""* You cast a shadow too.
* Your 3D form projects onto 2D surfaces.
* And your 4D... potential? 
* It casts YOU. You are someone's shadow.
* Think about that.""",
                ),
            },
            farewell="* May your shadow walk with purpose.",
        ),
    ),
    
    "light_keeper": NPC(
        id="light_keeper",
        name="Light Keeper",
        dimension="3d",
        realm_id="crystalline_spires",
        role=NPCRole.GUARDIAN,
        color=(255, 255, 200),
        heals=True,
        heal_cost=10,
        dialogue=NPCDialogue(
            greeting="* Light bends around a crystalline form.",
            first_meeting="""* Welcome to the Crystalline Spires.
* I am the Light Keeper.
* Here, light reveals truth.
* Let me cleanse your wounds with pure spectrum.
* (HP fully restored)""",
            lines={
                "light": DialogueLine(
                    text="""* Light is the key to perception.
* In 1D, light travels only forward and back.
* In 2D, it spreads across planes.
* In 3D, it fills volumes.
* In 4D... it does things we can't describe.""",
                ),
                "healing": DialogueLine(
                    text="""* The light here heals because it's TRUE light.
* Not scattered or filtered.
* Pure spectral energy.
* It aligns your form with geometric perfection.
* ...There. You're restored.""",
                ),
            },
            farewell="* Walk in light, traveler.",
            low_hp_dialogue="* You're wounded. Let my light heal you. (HP restored)",
        ),
    ),
}

# =============================================================================
# 4D NPCs
# =============================================================================

NPCS_4D: Dict[str, NPC] = {
    "tesseract_sage": NPC(
        id="tesseract_sage",
        name="Tesseract Sage",
        dimension="4d",
        realm_id="hyperspace_nexus",
        role=NPCRole.SAGE,
        color=(255, 150, 255),
        dialogue=NPCDialogue(
            greeting="* An impossible shape speaks from all directions.",
            first_meeting="""* Ah... a newcomer to hyperspace.
* Welcome. You must be disoriented.
* In 4D, 'inside' and 'outside' blur.
* I can see your internal organs.
* Don't worry - we all can. It's normal here.""",
            lines={
                "4d_nature": DialogueLine(
                    text="""* The W-axis is perpendicular to X, Y, and Z.
* You cannot visualize it. Not truly.
* But you can learn to FEEL it.
* Move ana (W+) or kata (W-).
* With practice, it becomes natural.""",
                ),
                "perception": DialogueLine(
                    text="""* In 3D, you could hide inside a box.
* In 4D, there is no inside.
* I can reach into your 'closed' body
* without breaking your skin.
* Privacy is a lower-dimensional concept.""",
                ),
                "beyond": DialogueLine(
                    text="""* Some say 4D is the end.
* It is not.
* Beyond the Threshold lies 5D, 6D, infinity.
* But to go further...
* You must be willing to lose what you are.""",
                ),
            },
            farewell="* May your W-axis extend forever.",
        ),
    ),
    
    "w_axis_guide": NPC(
        id="w_axis_guide",
        name="W-Axis Guide",
        dimension="4d",
        realm_id="hyperspace_nexus",
        role=NPCRole.GUIDE,
        color=(200, 255, 200),
        dialogue=NPCDialogue(
            greeting="* A helpful presence orients you in hyperspace.",
            first_meeting="""* Lost? Everyone is at first.
* I'm the W-Axis Guide.
* Think of W as a fourth direction.
* Not up, down, left, right, forward, or back.
* Something else entirely.""",
            lines={
                "directions": DialogueLine(
                    text="""* In 4D, we use special words:
* 'Ana' means movement in positive W.
* 'Kata' means movement in negative W.
* Just as 'up' and 'down' describe Y...
* 'Ana' and 'kata' describe W.""",
                ),
                "navigation": DialogueLine(
                    text="""* To navigate hyperspace:
* The W+ Reach is ana from here.
* The W- Depths are kata from here.
* The Ana-Kata Corridor connects them.
* Probability Gardens are... sideways? In 4D?""",
                ),
                "tips": DialogueLine(
                    text="""* Combat tip for 4D:
* Enemies can attack from W directions.
* Your 3D instincts will betray you.
* Learn to dodge ana and kata.
* It could save your life.""",
                ),
            },
            farewell="* Safe travels through hyperspace!",
        ),
    ),
    
    "seer_of_futures": NPC(
        id="seer_of_futures",
        name="Seer of Futures",
        dimension="4d",
        realm_id="w_positive_reach",
        role=NPCRole.SAGE,
        color=(255, 255, 150),
        dialogue=NPCDialogue(
            greeting="* Something that already knows you're here.",
            first_meeting="""* You were going to come here.
* I saw it. In the W+ direction.
* Future-echoes are clearer there.
* Welcome, [Name I already knew].
* ...You're surprised? You'll get used to it.""",
            lines={
                "future": DialogueLine(
                    text="""* W+ holds possibility.
* Every choice branches into futures.
* In W+ space, I can see those branches.
* Not all of them. But many.
* You're in several right now.""",
                ),
                "your_path": DialogueLine(
                    text="""* I see you reaching the Threshold.
* I see you facing the Guardian.
* Beyond that... the branches blur.
* Either you transcend, or you don't.
* Both futures exist until you choose.""",
                ),
            },
            farewell="* We'll meet again. I've seen it.",
        ),
    ),
    
    "keeper_of_memories": NPC(
        id="keeper_of_memories",
        name="Keeper of Memories",
        dimension="4d",
        realm_id="w_negative_depths",
        role=NPCRole.SAGE,
        color=(100, 100, 150),
        dialogue=NPCDialogue(
            greeting="* Something ancient and sad acknowledges you.",
            first_meeting="""* You've come to the depths.
* Where the past never fades.
* I keep the memories of all who've passed.
* Your 1D origins. Your 2D growth.
* Your 3D struggles. All preserved.""",
            lines={
                "past": DialogueLine(
                    text="""* In W- space, nothing is forgotten.
* Every moment you've lived echoes here.
* That's why it feels heavy.
* The weight of all that was.
* Some beings drown in their own past.""",
                ),
                "warning": DialogueLine(
                    text="""* Don't stay in W- too long.
* The Memory Specters will find you.
* They're not evil. Just... hungry.
* Hungry for the warmth of present-moment being.
* Something they've lost.""",
                ),
            },
            farewell="* Remember, but don't be trapped by remembering.",
        ),
    ),
    
    "the_transcended": NPC(
        id="the_transcended",
        name="The Transcended",
        dimension="4d",
        realm_id="beyond_threshold",
        role=NPCRole.SAGE,
        color=(255, 255, 255),
        dialogue=NPCDialogue(
            greeting="* Something both present and absent speaks.",
            first_meeting="""* ...
* You can perceive me?
* Interesting. Most 4D beings cannot.
* I have gone Beyond. And returned.
* Partially.
* Parts of me are still... there.""",
            lines={
                "beyond": DialogueLine(
                    text="""* What is beyond 4D?
* I cannot say. Not won't - cannot.
* The words don't exist.
* Your mind would fold.
* It's beautiful. And terrifying. And neither.""",
                ),
                "choice": DialogueLine(
                    text="""* To transcend is to choose dissolution.
* You stop being 'you' in any recognizable way.
* You become... part of something larger.
* The pattern continues. But the individual...
* The individual becomes the pattern.""",
                ),
                "advice": DialogueLine(
                    text="""* If you seek transcendence...
* Face the Threshold Guardian.
* Prove you understand all dimensions.
* And accept the price.
* Only then... will the way open.""",
                ),
            },
            farewell="* I'll be here. And there. And everywhere. And nowhere.",
        ),
    ),
}

# Combined NPC registry
ALL_NPCS: Dict[str, NPC] = {}
ALL_NPCS.update(NPCS_1D)
ALL_NPCS.update(NPCS_2D)
ALL_NPCS.update(NPCS_3D)
ALL_NPCS.update(NPCS_4D)


def get_npc(npc_id: str) -> NPC:
    """Get an NPC by ID."""
    return ALL_NPCS.get(npc_id)


def get_npcs_for_realm(realm_id: str) -> List[NPC]:
    """Get all NPCs in a realm."""
    return [npc for npc in ALL_NPCS.values() if npc.realm_id == realm_id]


def get_npcs_for_dimension(dimension: str) -> List[NPC]:
    """Get all NPCs in a dimension."""
    return [npc for npc in ALL_NPCS.values() if npc.dimension == dimension]
