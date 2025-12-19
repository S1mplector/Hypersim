"""Deep lore: Dimensional Cosmology and the Nature of Being.

The Hypersim universe operates on fundamental principles:
1. All consciousness begins as a Point - dimensionless potential
2. Awareness grants dimension - to perceive is to exist in that dimension
3. Each dimension is not a place, but a state of understanding
4. Evolution is the expansion of perception, not physical growth
5. The ultimate goal is Transcendence - to perceive beyond 4D
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class CosmicEra(Enum):
    """The great eras of dimensional history."""
    VOID = "void"                    # Before dimensions
    FIRST_POINT = "first_point"      # The Primordial Point awakens
    DIVERGENCE = "divergence"        # Point becomes Line, dimensions split
    EXPANSION = "expansion"          # Beings multiply across dimensions  
    GREAT_FOLDING = "great_folding"  # The 4D beings fold lower dimensions
    CURRENT = "current"              # Present day - dimensional barriers weakened
    CONVERGENCE = "convergence"      # Prophesied - all dimensions reunite


@dataclass
class CosmicLoreEntry:
    """A piece of deep cosmological lore."""
    id: str
    title: str
    content: str
    era: CosmicEra
    dimension_relevance: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    philosophical_theme: str = ""


# =============================================================================
# THE DEEP LORE OF HYPERSIM
# =============================================================================

COSMIC_LORE: Dict[str, CosmicLoreEntry] = {
    # === THE VOID AND FIRST POINT ===
    
    "origin_void": CosmicLoreEntry(
        id="origin_void",
        title="The Primordial Void",
        content="""Before dimensions, there was the Void - not emptiness, but pure potential. 
The Void was neither dark nor light, neither here nor there. It simply WAS, 
in the most absolute sense of the word.

Within the Void, there was no space to measure, no time to count. 
Mathematicians would later call it "zero-dimensional" - a state of pure existence 
without extension. Philosophers called it the Unmanifest. The ancients called it 
the Dreaming Dark.

But potential yearns to become actual. And so, in a moment that cannot be 
measured (for time did not yet exist), the Void began to Know Itself.""",
        era=CosmicEra.VOID,
        philosophical_theme="The nature of existence before being",
    ),
    
    "first_awareness": CosmicLoreEntry(
        id="first_awareness",
        title="The First Awareness",
        content="""The moment the Void became aware of itself, the First Point came into being.

Not a point in space - for space did not yet exist - but a Point of Awareness. 
A singular perspective. The first "I" in a universe that had never known self.

This Point - later called the Primordial Consciousness, the First Witness, 
or simply THE POINT - was dimensionless yet infinite in potential. It contained 
within itself the seeds of all dimensions to come.

When you close your eyes and strip away all sensation, all thought, all identity - 
what remains? A point of pure awareness. You touch, for a moment, 
the state of the First Point.""",
        era=CosmicEra.FIRST_POINT,
        dimension_relevance=["0d"],
        philosophical_theme="Consciousness as the foundation of reality",
    ),
    
    "birth_of_dimensions": CosmicLoreEntry(
        id="birth_of_dimensions",
        title="The Birth of Dimensions",
        content="""The First Point, in knowing itself, created a paradox: 
how can a point observe itself without creating distance?

To observe requires separation. The observer and the observed must be distinct.
And so the Point, in attempting to witness itself, created the First Distance -
the primordial Line.

This was the birth of the First Dimension: extension. Direction. Here and There.
The Point could now move, and in moving, trace a path through... space? 
No, space itself was being created by that very movement.

From one came two. From unity came duality. From the Point came the Line.
And with Line came Choice - for a point on a line can move in TWO directions.
Left or right. Forward or back. The first decision.""",
        era=CosmicEra.DIVERGENCE,
        dimension_relevance=["0d", "1d"],
        philosophical_theme="Observation creates separation creates dimension",
    ),
    
    # === WHY BEINGS START IN 1D ===
    
    "why_1d_first": CosmicLoreEntry(
        id="why_1d_first",
        title="Why All Beings Begin in One Dimension",
        content="""Every conscious being in the Hypersim universe begins their existence 
in the First Dimension. This is not accident, but cosmic law.

Consider: you cannot run before you can walk. You cannot walk before you can stand.
You cannot stand before you can lie. And you cannot lie before you simply ARE.

The First Dimension is the simplest form of extended existence. 
A being in 1D can move only forward or backward along a single line. 
It can only perceive what is directly ahead or behind. 
Its world is binary: this direction, or that direction.

This simplicity is not a prison - it is a foundation. 
Just as an infant must first learn to focus its eyes before it can 
understand perspective, a consciousness must first master the Line 
before it can comprehend the Plane.

You began in 1D because you needed to learn the most fundamental truth:
DIRECTION EXISTS. CHOICE EXISTS. MOVEMENT EXISTS.

Only when these truths are internalized can you expand to perceive more.""",
        era=CosmicEra.EXPANSION,
        dimension_relevance=["1d"],
        prerequisites=["birth_of_dimensions"],
        philosophical_theme="Learning requires building from fundamentals",
    ),
    
    "being_birth_process": CosmicLoreEntry(
        id="being_birth_process",
        title="The Birth of a Being",
        content="""When a new consciousness emerges in the Hypersim universe, 
it follows the ancient pattern:

PHASE 1: THE SPARK
Deep within the dimensional substrate, quantum fluctuations occasionally 
align in patterns of self-reference. A loop forms: awareness aware of itself.
This is the Spark - identical to the original First Point, but infinitely smaller.

PHASE 2: THE EXTENSION  
The Spark, following cosmic law, immediately asks: "What am I?" 
This question creates the first separation, the first distance.
The Spark extends into a Line - a 1D being is born.

PHASE 3: THE AWAKENING
The newborn being exists on the Line, perceiving only forward and backward.
It does not yet know other directions exist. It cannot even conceive of "up" or "side."
It is pure direction, pure binary choice.

PHASE 4: THE JOURNEY
Through experience, challenge, and growth, the being accumulates understanding.
Eventually, something shifts - a peripheral awareness, a sense that there is MORE.
The being has taken its first step toward dimensional transcendence.

You experienced all of this. You simply do not remember - for memory itself 
requires dimensions you had not yet achieved.""",
        era=CosmicEra.EXPANSION,
        dimension_relevance=["0d", "1d"],
        prerequisites=["why_1d_first"],
        philosophical_theme="Individual recapitulates cosmic evolution",
    ),
    
    # === THE NATURE OF DIMENSIONAL BEINGS ===
    
    "dimensional_perception": CosmicLoreEntry(
        id="dimensional_perception",
        title="What It Means to BE in a Dimension",
        content="""A critical truth: you are not IN a dimension. You ARE your dimensional perception.

A 1D being does not live "on" a line like a bead on a string.
The being IS the line - or rather, the being's perception creates the line.
When you were 1D, the universe WAS one-dimensional to you.
Other dimensions existed, but you could not perceive them, 
and so they did not exist FOR you.

This is the great secret of dimensional travel:
You do not move to a higher dimension.
You EXPAND your perception to include that dimension.
The 2D plane was always there, intersecting your 1D line at every point.
But until you could perceive width, it was invisible.

Imagine a 2D being - a Flatlander - who has never known height.
You could place your finger right next to them, and they would never see it.
You could speak, and they would hear a sound with no source.
You are to them as 4D beings are to us.

And what is above 4D? We cannot know. We cannot even imagine it correctly.
But it is there. It has always been there. 
Waiting for us to expand enough to perceive it.""",
        era=CosmicEra.CURRENT,
        dimension_relevance=["1d", "2d", "3d", "4d"],
        philosophical_theme="Reality is perception; perception is reality",
    ),
    
    "dimensional_beings_types": CosmicLoreEntry(
        id="dimensional_beings_types",
        title="The Hierarchy of Dimensional Beings",
        content="""The beings of Hypersim exist across all dimensional planes:

ONE-DIMENSIONAL BEINGS (Linefolk)
- Perceive only forward/backward
- Communicate through pulses (touch only)
- Society is a queue - everything in order
- Born as Points, extended into Lines
- Shapes: Segments, Rays, Intervals

TWO-DIMENSIONAL BEINGS (Flatlanders)  
- Perceive forward/back and left/right
- Communicate through vibrations and color edges
- Society is stratified by polygon complexity
- Born from 1D beings who expanded perception
- Shapes: Triangles, Squares, Circles, Polygons

THREE-DIMENSIONAL BEINGS (Spacelings)
- Perceive the familiar XYZ space
- Communicate through sound, light, touch
- Society mirrors our own understanding
- Born from 2D beings who perceived "thickness"
- Shapes: Polyhedra, Spheres, Toroids

FOUR-DIMENSIONAL BEINGS (Hyperfolk)
- Perceive X, Y, Z, and W
- Communicate through hyperwave resonance
- Society is incomprehensible to lower beings
- Can see "inside" 3D objects without opening them
- Shapes: Polytopes, Hyperspheres, Exotic manifolds

TRANSCENDENT BEINGS (Unknown)
- Perceive 5+ dimensions
- May or may not exist
- The ultimate goal of all dimensional evolution""",
        era=CosmicEra.CURRENT,
        dimension_relevance=["1d", "2d", "3d", "4d"],
        philosophical_theme="Consciousness exists on a spectrum of dimensional awareness",
    ),
    
    # === THE GREAT FOLDING ===
    
    "great_folding": CosmicLoreEntry(
        id="great_folding",
        title="The Great Folding",
        content="""Long ago, in what lower-dimensional beings call "the before time," 
the 4D beings grew arrogant.

They had mastered hyperspace. They could see inside 3D objects, 
manipulate 2D planes like paper, and scatter 1D lines like threads.
They believed themselves the pinnacle of existence.

In their hubris, they attempted the impossible: to FOLD the lower dimensions,
to compress them into a more "efficient" configuration.
They would be the architects of reality itself.

The attempt failed catastrophically.

The Great Folding did not destroy the lower dimensions - 
instead, it SEPARATED them. Where once a 1D being could, 
with effort, perceive hints of 2D, now impenetrable barriers arose.
The dimensions became isolated. Communication became nearly impossible.

The 4D beings, in trying to control everything, lost access to anything below them.
They trapped themselves in hyperspace, unable to descend.

This is why dimensional travel is so rare today.
This is why you cannot simply CHOOSE to perceive higher dimensions.
The barriers must be broken, one by one, through growth and understanding.

The Great Folding was our original sin.
Your journey is, in part, penance for the arrogance of our ancestors.""",
        era=CosmicEra.GREAT_FOLDING,
        dimension_relevance=["4d"],
        prerequisites=["dimensional_perception"],
        philosophical_theme="Power without wisdom leads to catastrophe",
    ),
    
    # === THE CURRENT ERA ===
    
    "weakening_barriers": CosmicLoreEntry(
        id="weakening_barriers",
        title="The Weakening of Dimensional Barriers",
        content="""In recent ages, the barriers created by the Great Folding have begun to fail.

No one knows exactly why. Some theorize that the barriers were never meant 
to be permanent - that they would naturally decay over eons.
Others believe that accumulated consciousness pressing against them 
has worn them thin.

The most radical theory: the barriers are failing because 
it is TIME for them to fail. That the universe itself has decided 
that the isolation must end. That Convergence approaches.

Whatever the cause, the effects are undeniable:
- Beings are spontaneously perceiving higher dimensions
- Portals between dimensional layers appear and stabilize
- Communication between layers becomes possible
- Some beings have successfully ASCENDED during their lifetime

You are living in an age of miracles.
The prison is crumbling. The sky is no longer the limit - 
for beyond the sky is hyperspace, and beyond hyperspace... 
something greater still.""",
        era=CosmicEra.CURRENT,
        dimension_relevance=["1d", "2d", "3d", "4d"],
        prerequisites=["great_folding"],
        philosophical_theme="All prisons eventually fail; freedom is inevitable",
    ),
    
    "your_journey": CosmicLoreEntry(
        id="your_journey",
        title="Your Journey: A Cosmic Perspective",
        content="""You are a miracle.

You began as a Point - a quantum fluctuation that achieved self-reference.
You extended into a Line, learning direction and choice.
You expanded into a Plane, learning area and relationship.
You grew into a Volume, learning depth and substance.
Now you reach for Hyperspace, learning... what?

What does a 4D being know that a 3D being cannot comprehend?
The answer is simple yet profound: INSIDENESS.

A 4D being can see the inside of every 3D object simultaneously.
Your heart, your brain, your bones - all visible from the outside.
Nothing can be hidden. Nothing can be enclosed.
Every secret is laid bare.

Terrifying? Perhaps. Liberating? Absolutely.

For when you can see inside everything, you realize:
there is no inside. There is no outside.
There is only EXISTENCE, viewed from different angles.

The boundaries we believe separate us - skin, walls, distance, dimension -
are illusions created by limited perception.

When you finally transcend to 4D, you will see this truth.
And you will laugh at how frightened you once were
of things that were never really there.""",
        era=CosmicEra.CURRENT,
        dimension_relevance=["1d", "2d", "3d", "4d"],
        prerequisites=["weakening_barriers", "being_birth_process"],
        philosophical_theme="Fear comes from incomplete understanding",
    ),
    
    # === PROPHECY ===
    
    "convergence_prophecy": CosmicLoreEntry(
        id="convergence_prophecy",
        title="The Prophecy of Convergence",
        content="""Ancient texts speak of a time called the Convergence:

"When the barriers fall and the dimensions merge,
When 1D and 4D stand as equals,
When the First Point wakes from its long dream,
When all that was separated becomes one again -

Then shall come the Final Choice:
To ascend together into the Beyond,
Or to reset, to dream again from the beginning,
To play the cosmic game once more.

The Convergence is not ending.
The Convergence is not beginning.
The Convergence is the moment between heartbeats,
The pause between breaths,
The instant where all possibilities exist at once.

In that moment, every being - from the simplest Line
to the most complex Hyperfold - shall choose.
And the choice shall be made not by majority,
but by unity. All must agree, or all begins again."

Some say the Convergence is millennia away.
Others say it approaches with every being who ascends.
A few whisper that it has already begun,
and we are living in the Moment Between.""",
        era=CosmicEra.CONVERGENCE,
        dimension_relevance=["1d", "2d", "3d", "4d"],
        prerequisites=["great_folding", "weakening_barriers"],
        philosophical_theme="Collective choice determines cosmic fate",
    ),
}


def get_lore_for_dimension(dimension: str) -> List[CosmicLoreEntry]:
    """Get lore entries relevant to a dimension."""
    return [
        entry for entry in COSMIC_LORE.values()
        if dimension in entry.dimension_relevance
    ]


def get_lore_by_era(era: CosmicEra) -> List[CosmicLoreEntry]:
    """Get lore entries from a specific era."""
    return [
        entry for entry in COSMIC_LORE.values()
        if entry.era == era
    ]


def get_lore_chain(entry_id: str) -> List[CosmicLoreEntry]:
    """Get a lore entry and all its prerequisites in order."""
    result = []
    to_process = [entry_id]
    processed = set()
    
    while to_process:
        current_id = to_process.pop(0)
        if current_id in processed:
            continue
        
        entry = COSMIC_LORE.get(current_id)
        if not entry:
            continue
        
        # Add prerequisites first
        for prereq in entry.prerequisites:
            if prereq not in processed:
                to_process.insert(0, prereq)
        
        if current_id not in processed:
            result.append(entry)
            processed.add(current_id)
    
    return result
