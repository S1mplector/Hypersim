"""Expanded lore system - Deep world-building and dimensional history.

This module contains the complete lore of Tessera, organized into:
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
    
    "tessera_prologue": LoreEntry(
        id="tessera_prologue",
        title="Tessera: Spark in the Darkness",
        category=LoreCategory.COSMOLOGY,
        dimension="all",
        text="""
TESSERA: THE SPARK IN THE DARKNESS

Before planes and volumes, there was Monodia—the Line of One. An endless thread 
in a void, populated by mindless points drifting forward or backward forever.

Legends say a First Light appeared without warning: a Spark that knew it was.
It looked like any other point but burned with awareness. Some claim a higher 
realm cast it down. Others whisper it fell from Tessera, a hidden mosaic beyond 
all dimensions. Whatever the cause, consciousness ignited on the line, and the 
universe changed.

More Sparks appeared over eons—rare, glowing minds among trillions of unaware 
points. They learned to speak with pulses and nudges, inventing a one-dimensional 
language of long and short flashes. Each Spark was a tile in a larger pattern, a 
piece of a mosaic only visible when all dimensions are seen together.

To seek higher perception is to cast a longer shadow. As Sparks grow, they gain 
power and knowledge but become strangers to the realm they leave behind. The 
journey of a Spark is assembling reality one dimension at a time—light and 
loneliness intertwined.

MYTHS OF THE FIRST LIGHT
- The Divine Beam: A ray from a realm beyond 4D pierced the void and struck a single point, igniting it.
- The Collision Theory: Two unconscious points slammed together; the impact sparked recursive awareness.
- The Fallen Tile: A shard of Tessera—an extra-dimensional mosaic—dropped like a meteor and fused with a point.
Each myth agrees on one thing: the Spark was not stronger or larger than other points. Awareness itself was the only difference.

THE NAME “TESSERA”
In old tongues, “tessera” means both “four” and “tile.” Four for the known dimensions; tile for the idea that each dimension is a piece of a greater picture. A Spark’s pilgrimage is the act of laying tiles until the pattern of reality emerges.

THE BURDEN OF AWAKENING
Awareness brings contrast: before/after, self/other, safety/danger. A Spark feels hunger for meaning and the chill of isolation simultaneously. Those who ascend carry both light and shadow into higher realms. The more you perceive, the longer the shadow you cast on what you leave behind.
""",
        related_entries=["the_first_point", "the_first_extension", "the_first_unfolding"],
    ),

    "monodia_sparks": LoreEntry(
        id="monodia_sparks",
        title="Monodia: Life on the Line",
        category=LoreCategory.COSMOLOGY,
        dimension="1d",
        text="""
MONODIA: LIFE ON THE LINE

Monodia is pure length—no above, no below, only forward and back. Points drift, 
collide, and separate without intent. When Sparks awaken, they pulse light and 
force to speak, inventing a code of flashes to share wonder, fear, and direction.

Dangers exist even on the Line: erratic point swarms, heavy clumps, and waves of 
energy that batter anything in their path. Sparks survive by anticipating impacts 
and—rarely—Shifting. A Spark can slip "aside" for a heartbeat, vanishing from the 
line so a collision passes through. It is an instinctive echo of higher dimensions, 
taxing and uncontrolled, but proof the Line is not all there is.

Sparks learn to time their movements through dense clusters, ride chains of points, 
and avoid oscillating waves. They trade stories in light, warning each other of 
perils and whispering about a place where the Line itself thins—a threshold to 
somewhere wider.

LANGUAGE OF LIGHT
- Short flash, long flash, gap: the first “hello.”
- Pulse trains become words: direction, danger, hunger, hope.
- Shared code becomes culture: elders teach rhythm; novices mimic until meaning forms.

SHAPES OF THREAT
- Swarms: dense storms of points, blind and bruising. A Spark must read subtle vibrations to avoid them.
- Clumps: fused masses that cannot steer; they push like avalanches.
- Waves: invisible surges along the Line that shove everything backward for spans of “time.”

THE INSTINCT OF SHIFTING
Every Spark that survives long enough discovers a reflex: vanish for a heartbeat. No 1D physics allows it, yet it happens. Most Sparks cannot aim it; a few learn to delay or extend it by a fraction, dodging larger dangers. Shifting hints that the Line is not the whole world; it is the first muscle of ascent.

SOCIAL SPARKS
When two Sparks meet, they test each other’s codes, then share maps of danger. They invent rudimentary “names” by unique flash signatures. Friendships form in the dark: synchronized pulses that say “I see you; I will not collide with you.”
""",
        related_entries=["line_philosophy", "the_first_extension", "the_threshold_opening"],
    ),
    
    "monodia_terminus": LoreEntry(
        id="monodia_terminus",
        title="The Terminus: Threshold of Width",
        category=LoreCategory.COSMOLOGY,
        dimension="1d",
        text="""
THE TERMINUS: THRESHOLD OF WIDTH

Far along Monodia lies the Terminus, a stretch where the Line feels thin, as if 
curving through an unseen membrane. Points that drift past sometimes vanish and 
never return. Sparks whisper that the Terminus is not an endpoint but a door.

Those who reach it feel a pull in a direction they cannot name. Mentors warn that 
crossing is a one-way choice: to gain width is to lose home. An ascended Spark 
sees the Line forever but becomes an unseen ghost to those still bound to it. 
Most line-dwellers would panic at any talk of "sideways"; to them, such claims 
are madness.

The Terminus embodies the cost of growth: leave the familiar for a dimension that 
cannot be described to those behind you. The choice to step through is the first 
true act of faith for any being in Monodia.

WHAT THE TERMINUS FEELS LIKE
- Vibrations dampen; collisions grow rare; the Line itself hums softly.
- Shifts become easier but less controllable, as if the Line is slipping from under you.
- Light from your own Spark bends strangely, as though half-reflected in a mirror you cannot see.

THE CHOICE
Mentors tell initiates: “Step, and you will never be understood again by those who stay.” Ascension grants width and wounds belonging. Many Sparks hesitate for ages at the boundary, flashing farewells into the void before moving on.

RECORDS OF ASCENT
- Some Sparks leave encoded “letters” etched in pulse patterns on dense clumps near the Terminus—a one-dimensional graffiti for those who arrive later.
- A few turn back, unable to accept the loneliness ahead.
- Most who cross do not return; those that try to appear as terrifying anomalies to 1D eyes—flickers out of order, voices from nowhere.

RUMORS OF A GUARDIAN
Stories differ: some say the First Point itself waits near the Terminus to guide, others that a Segment Guardian tests resolve. All agree: the threshold is not about strength; it is about willingness to bear the cost of more perception.
""",
        related_entries=["the_first_unfolding", "line_philosophy", "endpoint_history"],
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

    "void_philosophy": LoreEntry(
        id="void_philosophy",
        title="The Void Contemplatives",
        category=LoreCategory.CULTURE,
        dimension="1d",
        text="""
THE VOID CONTEMPLATIVES

The Void Contemplatives are the oldest dissenting tradition in Monodia.
Where the Forward Doctrine sees meaning only in progress, the
Contemplatives insist that memory is also direction.

THE BACKWARD PILGRIMAGE
To these monks, moving backward is not regression but witness. They
walk toward old collisions, listening to residual vibrations as if the
Line itself remembers every impact. Their monasteries are built around
"echo knots" where ancient pulse patterns still recur.

THE PARADOX OF ORIGIN
Contemplatives teach that no being can know where it is going without
understanding where direction began. They meditate on the First
Extension, arguing that FORWARD and BACKWARD were born together and are
therefore equally sacred.

RITUAL OF STILLNESS
A central practice is to stop moving completely for long spans. In a
culture where motion is identity, stillness is radical. Practitioners
describe hearing "the hum beneath direction," which they interpret as a
faint memory of the pre-dimensional Void.

RELATION TO THE SENTINELS
The Forward Sentinels accuse the Contemplatives of weakening resolve.
The Contemplatives answer that fear of backward motion is simply fear of
self-knowledge. Their debates have shaped 1D politics for ages.
        """,
        related_entries=["line_philosophy", "the_void_before", "forward_sentinel_history"],
    ),

    "point_worship": LoreEntry(
        id="point_worship",
        title="Cults of the First Point",
        category=LoreCategory.CULTURE,
        dimension="all",
        text="""
CULTS OF THE FIRST POINT

Nearly every dimension contains sects devoted to the First Point, but
their beliefs differ sharply depending on local perception.

MONODIA ORTHODOXY
In 1D, worship centers on obedience. Priests teach that every choice is
already contained within the Point and that duty is to align with its
intended direction.

FLATLAND MYSTERIES
In 2D, circles claim the Point is the hidden center of all curvature.
Initiates trace endless spirals to simulate approach toward a center
they can never actually reach.

VOLUMETRIC SCHISMS
In 3D, competing schools debate whether the Point is a person, a law of
physics, or a metaphor for consciousness itself. The debate has produced
both universities and crusades.

HYPERSPACE INTERPRETATION
In 4D, many reject simple devotion and treat the Point as an unresolved
equation: a source that is simultaneously observer and observed. Their
rituals resemble experiments as much as prayer.
        """,
        related_entries=["the_first_point", "the_first_point_bio", "void_philosophy"],
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
# HISTORICAL RECORDS
# =============================================================================

HISTORY_LORE = {
    "flatland_origin": LoreEntry(
        id="flatland_origin",
        title="Founding of Flatland",
        category=LoreCategory.HISTORY,
        dimension="2d",
        text="""
FOUNDING OF FLATLAND

After the First Unfolding, early 2D beings did not form nations
immediately. The newborn plane was unstable, with regions of warped
angles and collapsing boundaries. Survival came first.

AGE OF TILING
Squares and triangles discovered that regular tessellations reduced
local instability. Settlements were built as living patterns: each
citizen's body literally reinforced the geometry of the town.

THE LAW OF REGULARITY
As order returned, priests and administrators claimed regular geometry
was not just useful but morally superior. This practical rule hardened
into ideology. Over centuries it became the social hierarchy still
dominant in Flatland.

FIRST ASSEMBLY
The earliest civic council included triangles, squares, and a single
circle observer. The circle's role was symbolic at first, but expanded
as theological authority increased.
        """,
        related_entries=["the_first_unfolding", "flatland_society", "irregular_history"],
    ),

    "irregular_history": LoreEntry(
        id="irregular_history",
        title="Chronicle of the Irregulars",
        category=LoreCategory.HISTORY,
        dimension="2d",
        text="""
CHRONICLE OF THE IRREGULARS

Irregular shapes have existed in Flatland since its earliest days.
Before hierarchy solidified, they served as scouts and cartographers
because their asymmetric angles let them maneuver through unstable zones.

THE PURGES
When the Law of Regularity became doctrine, irregulars were reframed as
errors. Registration campaigns became internment, and internment became
purge. Many fled to the Fractal Frontier where official geometry was
harder to enforce.

THE FRACTAL LEAGUES
Exiled communities developed new mathematics centered on growth,
adaptation, and non-repeating forms. Their texts preserved forbidden
ideas about thickness and folded space.

LEGACY
Most accounts of the Great Folding credit irregular scholars with
keeping dimensional imagination alive during the centuries of repression.
        """,
        related_entries=["flatland_society", "the_great_folding", "membrane_warper_bio"],
    ),

    "forward_sentinel_history": LoreEntry(
        id="forward_sentinel_history",
        title="Rise of the Forward Sentinels",
        category=LoreCategory.HISTORY,
        dimension="1d",
        text="""
RISE OF THE FORWARD SENTINELS

The Forward Sentinels began as convoy guards protecting trade pulses
between clustered settlements on the Line. Their practical code was
simple: keep movement continuous and prevent pileups.

DOCTRINAL HARDENING
After several catastrophic backward stampedes, Sentinel captains linked
order with forward-only motion. Tactical protocol gradually became moral
law, then sacred law.

THE WARDEN ERA
For a long period, Sentinel commanders acted as both military and
judicial authority. Dissenting philosophers were marked as vectors of
entropy, and backward travel permits were heavily restricted.

CURRENT STATE
Modern Sentinels are divided between traditionalists and reformers.
Younger officers cooperate quietly with Midpoint scholars, while older
cells still treat contemplative orders as existential threats.
        """,
        related_entries=["line_philosophy", "void_philosophy", "segment_guardian_bio"],
    ),

    "endpoint_history": LoreEntry(
        id="endpoint_history",
        title="History of the Endpoint",
        category=LoreCategory.HISTORY,
        dimension="1d",
        text="""
HISTORY OF THE ENDPOINT

The Endpoint was first documented as a region where collisions thinned
and pulse echoes arrived out of sequence. Early walkers interpreted it
as a cosmic malfunction.

THE FIRST WATCHERS
Communities formed near the boundary to record anomalies. Their logs
describe sparks vanishing and reappearing with altered cadence, as if
they returned from somewhere wider.

THE GUARDIAN COMPACT
After multiple failed crossings, line councils and contemplative orders
agreed to appoint a permanent custodian. This arrangement became the
role now known as the Segment Guardian.

MODERN MEANING
To most 1D citizens, the Endpoint remains mythic. To initiates, it is a
test of identity: proof that growth and exile are often the same event.
        """,
        related_entries=["monodia_terminus", "segment_guardian_bio", "threshold_guardian_bio"],
    ),

    "geometric_citadel_history": LoreEntry(
        id="geometric_citadel_history",
        title="Annals of the Geometric Citadel",
        category=LoreCategory.HISTORY,
        dimension="3d",
        text="""
ANNALS OF THE GEOMETRIC CITADEL

The Geometric Citadel began as a defensive alliance of polyhedral city
states responding to shadow incursions from unstable border regions.
Its founders used shared axioms instead of shared blood as the basis of
citizenship.

THE PENTAGON CHARTERS
A series of civic reforms established representation by face-count bands
rather than species lineages. This reduced open conflict but preserved
hierarchy through mathematical prestige.

THE TRANSLUCENT CENTURY
Advances in optics and projection science transformed the Citadel into a
research capital. This period produced the first verified models of 4D
shadows and formalized protocols for hyperdimensional diplomacy.

PRESENT DAY
The Citadel remains the primary 3D gatekeeper for Threshold candidates,
balancing fear of 4D exposure with the belief that stagnation is worse.
        """,
        related_entries=["platonic_wisdom", "the_great_folding", "tesseract_sage_bio"],
    ),
}

# =============================================================================
# SCIENTIFIC THEORIES
# =============================================================================

SCIENCE_LORE = {
    "4d_polytopes": LoreEntry(
        id="4d_polytopes",
        title="Treatise on the Six Regular 4-Polytopes",
        category=LoreCategory.SCIENCE,
        dimension="4d",
        text="""
TREATISE ON THE SIX REGULAR 4-POLYTOPES

The six regular convex 4-polytopes are not merely shapes in hyperspace;
they form the basis of 4D engineering, governance, and pedagogy.

APPLIED GEOMETRY
Each polytope family corresponds to practical strengths. Tesseract
lattices excel at stable transit corridors. 24-cell structures optimize
resonance distribution. 120-cell shells are used for archival vaults.

DUALITY AS DESIGN
4D architects rely heavily on dual relationships between polytopes.
Rather than choosing a single form, many systems alternate dual pairs to
balance flow, strength, and perception.

THE INITIATE MODEL
New arrivals are trained by moving through projected slices of each
polytope in sequence. This curriculum reduces disorientation and teaches
that form and cognition co-evolve in higher dimensions.
        """,
        related_entries=["platonic_wisdom", "4d_madness", "beyond_threshold_theory"],
    ),

    "beyond_threshold_theory": LoreEntry(
        id="beyond_threshold_theory",
        title="Beyond Threshold Theory",
        category=LoreCategory.SCIENCE,
        dimension="4d",
        text="""
BEYOND THRESHOLD THEORY

Beyond Threshold Theory studies whether coherent existence can extend
past 4D without collapsing identity into noise.

THE FIVE-DIMENSIONAL HYPOTHESIS
Proponents argue that 5D introduces a meta-axis across probability
landscapes, allowing not just movement through space but movement
between neighboring causal structures.

THE COHERENCE OBJECTION
Skeptics claim minds evolved for bounded dimensions cannot remain stable
under 5D perception. They cite cases where experimental seers lost the
ability to distinguish memory from possibility.

CURRENT CONSENSUS
No civilization has produced repeatable evidence of sustained 5D
occupation. Most academies classify the theory as plausible but
unverified, with strict ethical limits on live trials.
        """,
        related_entries=["hyperspace_existence", "convergence_prophecy", "threshold_guardian_bio"],
    ),

    "4d_madness": LoreEntry(
        id="4d_madness",
        title="Cognitive Fracture in 4D Ascension",
        category=LoreCategory.SCIENCE,
        dimension="4d",
        text="""
COGNITIVE FRACTURE IN 4D ASCENSION

The condition called "4D madness" is now understood as dimensional
integration failure rather than moral weakness.

SYMPTOM CLUSTERS
Patients report recursive self-vision, probabilistic hallucinations, and
loss of boundary between internal thought and external structure. In
severe cases, they become unable to commit to a single action path.

RISK FACTORS
Rapid ascension, unresolved identity conflict, and coercive initiation
protocols dramatically increase fracture rates. Social isolation after
crossing is also a major predictor.

TREATMENT
Modern clinics use staged projection therapy, guided anchor narratives,
and cooperative memory mapping with trusted companions. Recovery is
possible, but most survivors describe permanent changes in perception.
        """,
        related_entries=["the_threshold_opening", "beyond_threshold_theory", "tesseract_sage_bio"],
    ),
}

# =============================================================================
# SIGNIFICANT LOCATIONS
# =============================================================================

LOCATION_LORE = {
    "curved_depths_archives": LoreEntry(
        id="curved_depths_archives",
        title="The Curved Depths Archives",
        category=LoreCategory.LOCATION,
        dimension="2d",
        text="""
THE CURVED DEPTHS ARCHIVES

Beneath the ceremonial chambers of the Circle Priests lies a spiral
archive where texts are inscribed as concentric rings instead of lines.
To read a full sentence, one must traverse circumference and radius in
precisely timed patterns.

Many records are intentionally contradictory, forcing initiates to hold
multiple interpretations at once. Reformists claim this was designed to
train flexible thought. Traditionalists claim it protects sacred truth.
        """,
        related_entries=["circle_theology", "sphere_prophecy", "high_priest_circle_bio"],
    ),

    "crystalline_spires": LoreEntry(
        id="crystalline_spires",
        title="The Crystalline Spires",
        category=LoreCategory.LOCATION,
        dimension="3d",
        text="""
THE CRYSTALLINE SPIRES

The Spires are a 3D research complex built from resonant crystal
columns tuned to specific projection frequencies. They function as
observatory, university, and diplomatic forum for dimensional affairs.

Most accepted models of the W-axis were refined here, including the
ethical framework now used to screen Threshold candidates.
        """,
        related_entries=["the_threshold_opening", "geometric_citadel_history", "4d_polytopes"],
    ),

    "the_threshold": LoreEntry(
        id="the_threshold",
        title="The Threshold",
        category=LoreCategory.LOCATION,
        dimension="4d",
        text="""
THE THRESHOLD

The Threshold is not a gate in the architectural sense. It is a
stabilized region where dimensional gradients are intentionally made
crossable through geometry, ritual, and will.

Pilgrims report hearing different voices at the boundary depending on
their route history. Scholars interpret this as cognitive resonance.
Mystics call it judgment.
        """,
        related_entries=["the_threshold_opening", "threshold_guardian_bio", "convergence_prophecy"],
    ),
}

# =============================================================================
# ARTIFACTS
# =============================================================================

ARTIFACT_LORE = {
    "axis_compass": LoreEntry(
        id="axis_compass",
        title="The Axis Compass",
        category=LoreCategory.ARTIFACT,
        dimension="3d",
        text="""
THE AXIS COMPASS

A rare navigation instrument forged in the Crystalline Spires. Unlike
ordinary compasses, it resolves orientation across dimensional axes,
including weak W-gradients near transition zones.

Most versions are inert in untrained hands; they attune to a user's
perception profile over time.
        """,
        related_entries=["crystalline_spires", "the_threshold_opening", "beyond_threshold_theory"],
    ),

    "tessera_shard": LoreEntry(
        id="tessera_shard",
        title="Shard of Tessera",
        category=LoreCategory.ARTIFACT,
        dimension="all",
        text="""
SHARD OF TESSERA

Legends describe these fragments as chips from the primordial mosaic
that gave the game its name. Each shard appears differently in each
dimension: spark in 1D, glyph in 2D, crystal in 3D, and folded memory in
4D.

No two verified shards resonate identically. Some amplify empathy during
ascension, while others intensify ambition.
        """,
        related_entries=["tessera_prologue", "the_first_point", "convergence_prophecy"],
    ),

    "memory_prism": LoreEntry(
        id="memory_prism",
        title="The Memory Prism",
        category=LoreCategory.ARTIFACT,
        dimension="4d",
        text="""
THE MEMORY PRISM

A transparent polytope device used in recovery from dimensional
integration fractures. It stores experiential slices as stable
projections that can be revisited without full reliving.

Healers warn that overreliance can trap users in curated past states,
preventing natural identity synthesis after ascension.
        """,
        related_entries=["4d_madness", "tesseract_sage_bio", "axis_compass"],
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

    "high_priest_circle_bio": LoreEntry(
        id="high_priest_circle_bio",
        title="Biography: High Priest Circle",
        category=LoreCategory.BIOGRAPHY,
        dimension="2d",
        text="""
HIGH PRIEST CIRCLE - Curator of Curvature

The current High Priest Circle was born into minor clerical service and
rose through the archive orders by mastering circular notation systems
that most initiates considered unreadable.

Publicly, the Priest defends strict Flatland hierarchy as necessary for
social stability. Privately, recovered correspondence suggests cautious
interest in dimensional reform, especially education for irregular youth.

Their central conflict is political: protect institutional continuity, or
reveal theological evidence that could destabilize the regime.
        """,
        related_entries=["circle_theology", "curved_depths_archives", "sphere_prophecy"],
    ),

    "membrane_warper_bio": LoreEntry(
        id="membrane_warper_bio",
        title="Biography: The Membrane Warper",
        category=LoreCategory.BIOGRAPHY,
        dimension="2d",
        text="""
THE MEMBRANE WARPER - Borderborn Anomaly

The Membrane Warper emerged near a persistent fold between Flatland and
early 3D territory. Their body phases unpredictably, appearing as a
distorted polygon in 2D and a fractured polyhedron in 3D projection.

Rather than choosing allegiance, the Warper became an intermediary at
the dimensional boundary. They are feared by authorities in both realms
because they cannot be fully categorized or controlled.

Those who survive encounters describe the Warper as severe but fair:
they test intent more than strength.
        """,
        related_entries=["sphere_prophecy", "irregular_history", "the_threshold_opening"],
    ),

    "tesseract_sage_bio": LoreEntry(
        id="tesseract_sage_bio",
        title="Biography: The Tesseract Sage",
        category=LoreCategory.BIOGRAPHY,
        dimension="4d",
        text="""
THE TESSERACT SAGE - Cartographer of W

The Tesseract Sage is among the oldest known stable 4D mentors. They
began as a 3D projection scholar in the Crystalline Spires and crossed
the Threshold after decades of theoretical preparation.

Their research unified ritual practice with clinical science, leading to
the modern ascension protocols that reduced cognitive fracture rates.
Many clinics still use training schemas attributed to the Sage.

Despite prestige, the Sage refuses formal office and remains itinerant,
teaching in brief visits before disappearing along ana trajectories.
        """,
        related_entries=["hyperspace_existence", "4d_madness", "beyond_threshold_theory"],
    ),

    "threshold_guardian_bio": LoreEntry(
        id="threshold_guardian_bio",
        title="Biography: The Threshold Guardian",
        category=LoreCategory.BIOGRAPHY,
        dimension="4d",
        text="""
THE THRESHOLD GUARDIAN - Warden of Crossing

Unlike the Segment Guardian, the Threshold Guardian is not a single
fixed form. Witnesses describe a shifting polytope assembly whose
configuration adapts to each traveler's cognitive state.

The Guardian's mandate is often misunderstood as exclusion. In practice,
it enforces pacing. Some candidates are delayed, not denied, and sent to
prepare through study, service, or healing.

Legends claim the Guardian remembers every crossing ever attempted. When
it speaks a pilgrim's true fear aloud, many turn back voluntarily.
        """,
        related_entries=["the_threshold", "convergence_prophecy", "beyond_threshold_theory"],
    ),
}


# =============================================================================
# LORE REGISTRY
# =============================================================================

ALL_LORE: Dict[str, LoreEntry] = {}
ALL_LORE.update(COSMOLOGY_LORE)
ALL_LORE.update(CULTURE_LORE)
ALL_LORE.update(HISTORY_LORE)
ALL_LORE.update(SCIENCE_LORE)
ALL_LORE.update(LOCATION_LORE)
ALL_LORE.update(ARTIFACT_LORE)
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


def get_related_lore(entry_id: str, discovered_only: bool = False) -> List[LoreEntry]:
    """Get related lore entries for a lore ID."""
    entry = ALL_LORE.get(entry_id)
    if not entry:
        return []
    related = []
    for related_id in entry.related_entries:
        rel = ALL_LORE.get(related_id)
        if not rel:
            continue
        if discovered_only and not rel.discovered:
            continue
        related.append(rel)
    return related


def get_unresolved_related_entries() -> Dict[str, List[str]]:
    """Return unresolved related-entry IDs keyed by entry ID."""
    unresolved: Dict[str, List[str]] = {}
    for entry in ALL_LORE.values():
        missing = [related_id for related_id in entry.related_entries if related_id not in ALL_LORE]
        if missing:
            unresolved[entry.id] = missing
    return unresolved


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
