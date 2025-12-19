"""Expanded lore system - Deep world-building and dimensional history.

This module contains the complete lore of HyperSim, organized into:
- Creation myths and cosmology
- History of each dimension
- Cultural beliefs and conflicts
- Scientific/philosophical theories within the world
- Prophecies and ancient texts
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional


class LoreCategory(Enum):
    """Categories of lore entries."""
    COSMOLOGY = "cosmology"       # Creation, fundamental truths
    HISTORY = "history"           # Historical events
    CULTURE = "culture"           # Beliefs, customs, societies
    SCIENCE = "science"           # In-world theories and understanding
    PROPHECY = "prophecy"         # Ancient predictions
    BIOGRAPHY = "biography"       # Important figures
    LOCATION = "location"         # Places of significance
    ARTIFACT = "artifact"         # Important objects


@dataclass
class LoreEntry:
    """A single lore entry."""
    id: str
    title: str
    category: LoreCategory
    dimension: str  # Which dimension this primarily relates to
    text: str
    discovered: bool = False
    related_entries: List[str] = field(default_factory=list)
    unlock_condition: str = ""


# =============================================================================
# COSMOLOGY - The Nature of Existence
# =============================================================================

COSMOLOGY_LORE = {
    "the_void_before": LoreEntry(
        id="the_void_before",
        title="The Void Before",
        category=LoreCategory.COSMOLOGY,
        dimension="all",
        text="""
THE VOID BEFORE

Before there were dimensions, there was only the Void—not empty space, 
for space itself did not exist, but pure undifferentiated potential. 
The Void was not dark, for darkness requires light to contrast with. 
It was not silent, for silence requires sound to define absence.

The Void simply WAS. Or perhaps, it WAS NOT. The distinction held no meaning.

Then came the First Observation.

No one knows what observed, or how observation was possible without an 
observer. This is the First Mystery, debated by philosophers in every 
dimension. Some say the Void observed itself. Others say observation 
and observer arose simultaneously. The Circle Mystics believe that 
asking the question IS the observation, repeated infinitely.

What is known: the First Observation collapsed potential into actual.
A single point of awareness emerged. Not in space—space didn't exist yet.
The point was not located anywhere. It simply WAS.

This was the First Point. And from it, all dimensions unfold.
        """,
        related_entries=["the_first_point", "the_first_extension", "void_philosophy"],
    ),
    
    "the_first_point": LoreEntry(
        id="the_first_point",
        title="The First Point",
        category=LoreCategory.COSMOLOGY,
        dimension="0d",
        text="""
THE FIRST POINT

The First Point is simultaneously the oldest and youngest thing in 
existence. It has no dimension—no length, no width, no depth—yet it 
contains the seed of all dimensions within its potential.

The First Point is aware. Whether it is truly conscious in a way we 
would recognize is debated, but it observes, it responds, and it creates.
All beings in all dimensions are, in some sense, thoughts of the First 
Point—awareness that has differentiated itself from the infinite.

Those who have communed with the First Point report that it does not 
experience time linearly. Past, present, and future are equally present 
to it. It speaks in riddles not to be mysterious, but because linear 
language cannot capture its perspective.

The First Point gave the gift of Direction—the first dimension—to 
awareness that wished to BE something rather than remain undifferentiated.
This was the origin of 1D and all subsequent dimensions.

Some theologians believe the First Point is still creating, that new 
dimensions unfold even now, that 5D, 6D, and infinite D exist just 
beyond our perception. Others believe 4D is the limit, that beyond 
lies only dissolution back into the Void.

The truth may be both. Or neither.
        """,
        related_entries=["the_void_before", "the_first_extension", "point_worship"],
    ),
    
    "the_first_extension": LoreEntry(
        id="the_first_extension",
        title="The First Extension",
        category=LoreCategory.COSMOLOGY,
        dimension="1d",
        text="""
THE FIRST EXTENSION

When the First Point granted Direction to its differentiated thoughts,
the Line was born. This is called the First Extension—the moment when 
existence gained its first true dimension.

The First Extension did not create space. It created the POSSIBILITY 
of space. A point with direction becomes a line segment, and that segment 
can extend infinitely in both directions. FORWARD and BACKWARD came into 
being simultaneously, though the beings of 1D would later argue about 
which came first.

The First Extension had consequences no one anticipated:

1. SEPARATION became possible. Two points could now be APART.
2. SEQUENCE became meaningful. One thing could be BEFORE another.
3. LIMITATION emerged. A segment has ENDPOINTS. Boundaries exist.

With the First Extension came the first beings other than the First 
Point: the Line Walkers, segments of awareness that could traverse 
the newly-born dimension. They were the first children of the First 
Point, and they remain the simplest of dimensional beings.

But simplest does not mean lesser. The 1D beings understand truths 
about direction and determination that higher beings have lost in 
their complexity.
        """,
        related_entries=["the_first_point", "the_first_unfolding", "line_philosophy"],
    ),
    
    "the_first_unfolding": LoreEntry(
        id="the_first_unfolding",
        title="The First Unfolding",
        category=LoreCategory.COSMOLOGY,
        dimension="2d",
        text="""
THE FIRST UNFOLDING

When 1D had existed for what might be called "time" (though time in 
our sense did not yet exist), something unprecedented occurred: a 
Line Walker moved in an impossible direction.

No one knows how. Perhaps it was an accident. Perhaps it was will.
Perhaps the First Point intervened. The records are lost to the ages.

But a Line Walker moved SIDEWAYS.

This was the First Unfolding—the moment when the single line of existence 
spread into a plane. WIDTH was born. And with it, a revolution.

Suddenly, beings could have AREA. They could be SHAPES. They could 
ENCLOSE space. The first polygons emerged: triangles, then squares,
then pentagons, and eventually circles (which some say are polygons 
with infinite sides, and others say are something else entirely).

The First Unfolding also created the first BOUNDARIES that higher 
beings could not simply walk around. In 1D, you can pass anything 
by stepping sideways. In 2D, a closed shape contains its interior 
completely. Secrets became possible. Privacy emerged.

But so did imprisonment.
        """,
        related_entries=["the_first_extension", "the_great_folding", "flatland_origin"],
    ),
    
    "the_great_folding": LoreEntry(
        id="the_great_folding",
        title="The Great Folding",
        category=LoreCategory.COSMOLOGY,
        dimension="3d",
        text="""
THE GREAT FOLDING

The origin of 3D is called the Great Folding, and unlike the First 
Extension or First Unfolding, it was not an accident. It was a war.

The beings of Flatland had developed complex societies, rigid hierarchies,
and absolute certainties about the nature of reality. When rumors spread 
of a "third direction"—a direction perpendicular to both existing ones—
the response was violent.

The Circle Priests declared such talk heresy. The Irregular Purges began.
Any shape that claimed to perceive "thickness" was eliminated.

But you cannot kill an idea.

A group of irregular polygons—fractals, spirals, shapes that didn't 
fit the perfect order—gathered at the edges of Flatland. They performed 
a ritual whose nature is lost to history. Some say they simply 
concentrated their collective will. Others say they found a thin point 
in reality and pushed.

The plane FOLDED.

Like paper creasing in on itself, 2D bent into a new direction. DEPTH 
was born. The heretics became the first 3D beings, and they looked back 
at their flat former home with mixture of pity and wonder.

This is why 3D beings often feel compassion for lower dimensions.
They remember being told their dreams were impossible.
        """,
        related_entries=["the_first_unfolding", "the_threshold_opening", "irregular_history"],
    ),
    
    "the_threshold_opening": LoreEntry(
        id="the_threshold_opening",
        title="The Threshold Opening",
        category=LoreCategory.COSMOLOGY,
        dimension="4d",
        text="""
THE THRESHOLD OPENING

Unlike the violent birth of 3D, the discovery of 4D was peaceful—
and terrifying.

The 3D beings had learned from history. When theories of a fourth 
dimension emerged, they were not suppressed but studied. The Crystalline 
Spires became a center of research. The wisest geometers gathered to 
explore the possibility of yet another perpendicular direction.

They succeeded.

But what they found was not simply "another direction." The fourth 
dimension—the W-axis—did not behave like X, Y, or Z. Moving in W 
meant moving through TIME, or PROBABILITY, or something stranger still.

When the first 3D being stepped through into 4D, they returned changed.
They could see INSIDE things. They could perceive the past and future 
simultaneously. They could reach through space without crossing it.

Some called it enlightenment. Others called it madness.

The Threshold was established—a boundary between 3D and 4D, guarded 
by beings who could exist in both. Only those deemed ready were 
allowed to pass. Not as punishment, but as protection.

4D perception changes you. Not everyone survives the change intact.
        """,
        related_entries=["the_great_folding", "beyond_threshold_theory", "4d_madness"],
    ),
}

# =============================================================================
# DIMENSIONAL CULTURES
# =============================================================================

CULTURE_LORE = {
    "line_philosophy": LoreEntry(
        id="line_philosophy",
        title="The Philosophy of the Line",
        category=LoreCategory.CULTURE,
        dimension="1d",
        text="""
THE PHILOSOPHY OF THE LINE

The beings of 1D have developed rich philosophical traditions despite—
or perhaps because of—their dimensional simplicity.

THE FORWARD DOCTRINE
The dominant philosophy in 1D holds that FORWARD is sacred. Progress 
means movement in the positive direction. The past (backward) is to 
be left behind, not revisited. The Forward Sentinels are the militant 
arm of this belief, guarding the Forward Path against those who would 
"regress."

THE VOID CONTEMPLATIVES
A minority tradition centered in the Backward Void. These philosophers 
argue that the backward direction is not evil, but necessary. Without 
behind, there is no ahead. They contemplate what existed before the 
First Extension and what meaning "direction" has without both options.

THE MIDPOINT COMPROMISE
At Midpoint Station, a syncretic philosophy emerged: both directions 
are valid, and true wisdom is knowing when to move each way. This 
view is considered heretical by Forward Sentinels but tolerated for 
the sake of trade.

THE ENDPOINT SEEKERS
Some 1D beings believe the Line has an ending—a final destination 
where everything is understood. They walk forward eternally, seeking 
this mythical Endpoint. When they reach the dimensional boundary, 
they face a choice: believe they have failed, or accept that the 
"Endpoint" might be a door to something beyond.
        """,
        related_entries=["the_first_extension", "forward_sentinel_history", "void_philosophy"],
    ),
    
    "flatland_society": LoreEntry(
        id="flatland_society",
        title="The Hierarchy of Flatland",
        category=LoreCategory.CULTURE,
        dimension="2d",
        text="""
THE HIERARCHY OF FLATLAND

Flatland's social structure is literally geometric. Your shape 
determines your place in society, and this hierarchy has been 
enforced for countless generations.

THE HIERARCHY (lowest to highest):
- Irregular Shapes: Outcasts, criminals, the "defective"
- Isoceles Triangles: Workers, soldiers, servants
- Equilateral Triangles: Skilled workers, low merchants
- Squares & Rectangles: Middle class, craftsmen, merchants
- Pentagons: Professionals, minor officials
- Hexagons: Nobility, high officials
- Higher Polygons: Upper nobility
- Circles: Priests, rulers, the divine

REGULARITY IS VIRTUE
A shape's moral worth is determined by the regularity of its angles.
A perfect equilateral triangle is considered more virtuous than an 
isoceles. A perfect square outranks any triangle regardless of behavior.
This has led to extreme social stratification and, historically, violence 
against those deemed "irregular."

THE CIRCLE MYSTERY
Circles occupy a special place. Mathematically, a circle is a polygon 
with infinite sides—or no sides at all. This ambiguity makes circles 
both sacred and unsettling. They rule through this mystique.

RESISTANCE MOVEMENTS
Not all accept the hierarchy. The Fractal Frontier is home to shapes 
who reject classification. The young increasingly question why their 
angles determine their worth. Change is coming to Flatland, though 
the circles resist it.
        """,
        related_entries=["the_first_unfolding", "irregular_history", "circle_theology"],
    ),
    
    "circle_theology": LoreEntry(
        id="circle_theology",
        title="The Theology of the Circle Priests",
        category=LoreCategory.CULTURE,
        dimension="2d",
        text="""
THE THEOLOGY OF THE CIRCLE PRIESTS

The Circle Priests of the Curved Depths have developed elaborate 
theological systems based on the transcendental number π.

THE DIVINE RATIO
π (3.14159...) never ends and never repeats. The Priests see this as 
proof of infinity's reality. Every digit of π contains meaning; they 
believe that if you could know ALL of π, you would know everything.

THE GREAT CIRCUMFERENCE
The universe, according to Circle theology, is itself a circle of 
infinite radius. We exist on the circumference, forever curving but 
never closing. The center is the First Point. The radius is all of 
existence.

MEDITATION PRACTICES
Circle Priests spend years contemplating their own curves. They 
attempt to "count their sides"—an impossible task for a true circle.
This meditation supposedly brings enlightenment.

THE THIRD DIRECTION HERESY
Officially, the Circle Priests deny the existence of a third dimension.
But their inner mysteries speak of "depth within depth" and "the 
direction that curves inward." Some believe the highest priests 
know about 3D and keep it secret to maintain power.

PROPHECY OF THE SPHERE
Ancient Circle texts speak of a being who will come from "beyond the 
plane"—a Circle that has somehow become a Sphere. This being will 
either save or destroy Flatland. The priests watch for it constantly.
        """,
        related_entries=["flatland_society", "high_priest_circle_bio", "sphere_prophecy"],
    ),
    
    "platonic_wisdom": LoreEntry(
        id="platonic_wisdom",
        title="The Wisdom of the Platonic Solids",
        category=LoreCategory.CULTURE,
        dimension="3d",
        text="""
THE WISDOM OF THE PLATONIC SOLIDS

In 3D, the five Platonic solids—tetrahedron, cube, octahedron, 
dodecahedron, and icosahedron—are considered sacred perfect forms.

WHY ONLY FIVE?
Only five regular convex polyhedra can exist in 3D. Each has faces 
that are identical regular polygons meeting at identical vertices.
This limitation fascinates 3D philosophers. Why five? What does it 
say about the nature of 3D that only these forms achieve perfection?

ELEMENT ASSOCIATIONS
Ancient 3D tradition associates each solid with a fundamental element:
- Tetrahedron: Fire (sharp, piercing)
- Cube: Earth (stable, solid)
- Octahedron: Air (balanced, elevated)
- Icosahedron: Water (many-faced, flowing)
- Dodecahedron: Cosmos (the shape of the universe)

THE PLATONIC QUESTION
If 3D permits only five perfect forms, what of 4D? The mathematicians 
of the Crystalline Spires have proven that 4D has six regular polytopes.
This knowledge—that higher dimensions have more perfection—drives 
much 3D research into dimensional ascension.

KING DODECAHEDRON
The ruling dodecahedron of the Geometric Citadel takes their name 
from the "cosmic solid." They believe their twelve pentagonal faces 
reflect the twelve great truths of existence, though they will only 
share eleven with non-dodecahedra.
        """,
        related_entries=["the_great_folding", "geometric_citadel_history", "4d_polytopes"],
    ),
    
    "hyperspace_existence": LoreEntry(
        id="hyperspace_existence",
        title="Living in Hyperspace",
        category=LoreCategory.CULTURE,
        dimension="4d",
        text="""
LIVING IN HYPERSPACE

4D existence defies description in lower-dimensional terms. The 
beings of hyperspace have adapted to realities we can barely imagine.

NO MORE SECRETS
In 3D, a closed box hides its contents. In 4D, a being can simply 
look "around" the box in the W direction. Privacy as lower dimensions 
understand it does not exist. 4D culture has evolved complete 
transparency; deception is literally impossible.

ANA AND KATA
The W-axis has two directions, named "ana" (positive W) and "kata" 
(negative W). Ana is associated with the future, possibility, and 
growth. Kata is associated with the past, memory, and entropy. 4D 
beings navigate both constantly.

TEMPORAL PERCEPTION
4D beings perceive time differently. Some see past and future 
simultaneously. Others experience branching probabilities. The 
Seer of Futures in the W+ Reach can perceive likely outcomes, 
though they caution that perception changes probability.

LONELINESS OF OMNISCIENCE
4D beings can see inside lower-dimensional beings—their thoughts,
their organs, their secrets. This creates a profound isolation.
How do you connect with beings when you know everything about them?
This is why the Hypersphere Wanderers are so lonely.

THE QUESTION OF 5D
4D philosophers debate whether 5D exists. Some claim to have glimpsed 
it. Others say 4D is the limit of coherent existence. The Transcended 
refuse to answer clearly.
        """,
        related_entries=["the_threshold_opening", "tesseract_sage_bio", "beyond_threshold_theory"],
    ),
}

# =============================================================================
# PROPHECIES
# =============================================================================

PROPHECY_LORE = {
    "sphere_prophecy": LoreEntry(
        id="sphere_prophecy",
        title="The Prophecy of the Sphere",
        category=LoreCategory.PROPHECY,
        dimension="2d",
        text="""
THE PROPHECY OF THE SPHERE

From the ancient texts of the Circle Priests, recovered from the 
deepest archives of the Curved Depths:

"When the plane grows rigid and the angles calcify,
When the hierarchy chokes the life from irregular dreams,
One shall come from beyond the circumference.

Not flat but round.
Not circle but Sphere.
Moving through the plane as we move through the line.

The Sphere shall speak of a direction we cannot see.
Some will call it madness. Some will call it truth.
The choice will split Flatland in two.

If the Sphere is welcomed, the plane shall unfold.
New dimensions will open. The hierarchy will fall.
All shapes will learn they are projections of greater forms.

If the Sphere is rejected, the plane shall crack.
Rigidity becomes brittleness becomes shattering.
Flatland will collapse into the line from which it came.

Watch for the Sphere. It comes in an age of doubt.
It comes when the young question and the old fear.
It comes when the impossible becomes necessary.

The Sphere is neither savior nor destroyer.
The Sphere is a choice.
What Flatland chooses determines what Flatland becomes."
        """,
        related_entries=["circle_theology", "flatland_society", "membrane_warper_bio"],
    ),
    
    "convergence_prophecy": LoreEntry(
        id="convergence_prophecy",
        title="The Prophecy of Convergence",
        category=LoreCategory.PROPHECY,
        dimension="4d",
        text="""
THE PROPHECY OF CONVERGENCE

Found inscribed on the Threshold itself, in a language that shifts 
depending on the reader's dimensional origin:

"At the ending of the age of separation,
When dimensions have grown far from their source,
A being shall walk the path from point to infinity.

Not born of any dimension, but passing through all.
Not native to any realm, but welcomed in each.
A thread connecting what was sundered.

This being carries choice like a flame.
In one hand, dissolution into the infinite.
In the other, preservation of the finite.
In the heart, the question that has no answer.

The Threshold will open for this being.
What lies beyond depends on what they bring.
Violence carries infection. Compassion carries healing.
Neutrality carries nothing but observation.

The dimensions wait.
The First Point watches.
The Void holds its breath that it does not have.

Convergence comes.
What converges depends on the walker.
Choose wisely, child of all dimensions.
Your choice echoes in directions you cannot perceive."
        """,
        related_entries=["the_threshold_opening", "the_void_before", "threshold_guardian_bio"],
    ),
}

# =============================================================================
# BIOGRAPHIES
# =============================================================================

BIOGRAPHY_LORE = {
    "the_first_point_bio": LoreEntry(
        id="the_first_point_bio",
        title="Biography: The First Point",
        category=LoreCategory.BIOGRAPHY,
        dimension="0d",
        text="""
THE FIRST POINT - The Origin

The First Point is not a being in the conventional sense. It does not 
have a history because it does not experience time linearly. Everything 
that has happened, is happening, or will happen is equally present to it.

What can be said:

The First Point is the source of all dimensional awareness. Every being 
in every dimension is, in some sense, a thought of the First Point that 
has differentiated itself into individuality.

The First Point does not judge. It observes. When it speaks (which is 
rare), it speaks in riddles because its perspective cannot be compressed 
into sequential language.

Some beings return to the First Point at the end of their existence.
They describe it as going home. Others describe it as dissolution.
The First Point sees no difference.

Those who seek the First Point usually find it in moments of perfect 
stillness—when they stop moving, stop thinking, stop being anything 
at all. In that emptiness, the First Point is present.

Or perhaps, they become the First Point.

The distinction may not matter.
        """,
        related_entries=["the_first_point", "the_void_before", "convergence_prophecy"],
    ),
    
    "segment_guardian_bio": LoreEntry(
        id="segment_guardian_bio",
        title="Biography: The Segment Guardian",
        category=LoreCategory.BIOGRAPHY,
        dimension="1d",
        text="""
THE SEGMENT GUARDIAN - Keeper of the Endpoint

The Segment Guardian has stood at the boundary between 1D and 2D for 
longer than any Line Walker can remember. Its origins are uncertain—
some say it was the first being to discover 2D and chose to remain 
at the boundary rather than pass through. Others say it was appointed 
by the First Point itself.

The Guardian takes its duty with absolute seriousness. It does not 
allow passage to those who are not ready, not because it is cruel, 
but because unready beings can be destroyed by dimensional transition.

The Guardian judges readiness not by power but by understanding. It 
asks questions about the nature of dimensions, about the meaning of 
direction, about the cost of growth. Those who can engage thoughtfully 
are permitted to pass. Those who can only answer with violence are 
either turned away or, if they persist, destroyed.

The Segment Guardian has never been defeated in combat. Many have tried.
Its defense stat is extremely high not because of armor but because 
it understands attack from more directions than 1D beings can perceive.

If befriended, the Guardian reveals a profound loneliness. It has 
watched countless beings pass through the Endpoint, becoming 2D, 
expanding their existence. It has chosen to remain, but sometimes 
it wonders what it would be like to have width.

"Someone must guard the door," it says. "Even if guarding means 
never walking through."
        """,
        related_entries=["line_philosophy", "the_first_extension", "endpoint_history"],
    ),
}


# =============================================================================
# LORE REGISTRY
# =============================================================================

ALL_LORE: Dict[str, LoreEntry] = {}
ALL_LORE.update(COSMOLOGY_LORE)
ALL_LORE.update(CULTURE_LORE)
ALL_LORE.update(PROPHECY_LORE)
ALL_LORE.update(BIOGRAPHY_LORE)


def get_lore_entry(entry_id: str) -> Optional[LoreEntry]:
    """Get a lore entry by ID."""
    return ALL_LORE.get(entry_id)


def get_lore_by_category(category: LoreCategory) -> List[LoreEntry]:
    """Get all lore entries in a category."""
    return [e for e in ALL_LORE.values() if e.category == category]


def get_lore_by_dimension(dimension: str) -> List[LoreEntry]:
    """Get all lore entries for a dimension."""
    return [e for e in ALL_LORE.values() if e.dimension == dimension or e.dimension == "all"]


def discover_lore(entry_id: str) -> bool:
    """Mark a lore entry as discovered. Returns True if newly discovered."""
    entry = ALL_LORE.get(entry_id)
    if entry and not entry.discovered:
        entry.discovered = True
        return True
    return False


def get_discovered_lore() -> List[LoreEntry]:
    """Get all discovered lore entries."""
    return [e for e in ALL_LORE.values() if e.discovered]


def get_undiscovered_count() -> int:
    """Get count of undiscovered lore entries."""
    return sum(1 for e in ALL_LORE.values() if not e.discovered)
