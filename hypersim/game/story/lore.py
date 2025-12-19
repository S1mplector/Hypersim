"""Lore and codex system for world-building."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class LoreCategory(Enum):
    """Categories of lore entries."""
    DIMENSIONS = "dimensions"       # About dimensional theory
    BEINGS = "beings"               # About creatures and NPCs
    HISTORY = "history"             # Historical events
    LOCATIONS = "locations"         # Places in the multiverse
    SCIENCE = "science"             # Mathematical/scientific concepts
    PHILOSOPHY = "philosophy"       # Existential musings
    ARTIFACTS = "artifacts"         # Special items and objects


@dataclass
class LoreEntry:
    """A single lore/codex entry."""
    id: str
    title: str
    category: LoreCategory
    content: str
    short_description: str = ""
    
    # Discovery
    discovered: bool = False
    discovery_dimension: Optional[str] = None
    discovery_source: Optional[str] = None  # NPC, location, or item
    
    # Related entries
    related_entries: List[str] = field(default_factory=list)
    
    # Visual
    icon: str = "📜"
    image_key: Optional[str] = None


# All lore entries for the campaign
CAMPAIGN_LORE: Dict[str, LoreEntry] = {
    # =========================================================================
    # DIMENSIONS
    # =========================================================================
    "lore_1d_perception": LoreEntry(
        id="lore_1d_perception",
        title="Perception in One Dimension",
        category=LoreCategory.DIMENSIONS,
        short_description="How beings perceive reality on a line.",
        content="""In one dimension, perception is fundamentally limited. A 1D being 
can only sense in two directions: forward and backward along the line. They cannot 
see past another being - if something is between them and their target, that target 
is completely hidden.

Sound, or rather vibration, becomes the primary sense. Beings learn to interpret 
the reverberations that travel along the line. With practice, one can distinguish 
between different entities by their unique vibrational signatures.

This is why the 'Ping' ability is so valuable - it sends out a pulse that returns 
information about nearby entities, revealing what would otherwise be invisible.""",
        icon="👁️",
        related_entries=["lore_dimensions_intro", "lore_flatland"],
    ),
    
    "lore_dimensions_intro": LoreEntry(
        id="lore_dimensions_intro",
        title="The Nature of Dimensions",
        category=LoreCategory.DIMENSIONS,
        short_description="A primer on dimensional existence.",
        content="""Dimensions are not merely different places - they are fundamentally 
different ways of existing. Each dimension adds a new axis of freedom, a new 
direction in which movement and perception become possible.

In 1D, existence is a line. There is only forward and backward.
In 2D, existence is a plane. Left and right join forward and backward.
In 3D, existence is volume. Up and down complete the familiar space.
In 4D, existence transcends space. The W-axis defies simple description.

Moving between dimensions is not like walking through a door. It requires a 
fundamental restructuring of one's being. The mind must learn to perceive in new 
ways, and the body (such as it is) must learn to move in directions that previously 
did not exist.

Some say there are dimensions beyond the fourth. If so, they remain beyond the 
comprehension of most beings.""",
        icon="🌌",
        related_entries=["lore_1d_perception", "lore_flatland", "lore_w_axis"],
    ),
    
    "lore_flatland": LoreEntry(
        id="lore_flatland",
        title="Flatland: The 2D Realm",
        category=LoreCategory.DIMENSIONS,
        short_description="The society of the plane.",
        content="""Flatland is the common name for the 2D realm - an infinite plane 
where beings exist as geometric shapes. Unlike the simplicity of the line, Flatland 
has developed complex societies.

In Flatland, social status is determined by the number of sides one possesses:
- Triangles are the lowest class, often soldiers or workers
- Squares and Pentagons form the professional class
- Hexagons and above are nobility
- Circles (or many-sided polygons) are priests

This hierarchy is maintained through strict laws. Irregulars - beings with unequal 
sides - are considered dangerous and are often executed at birth.

The concept of 'up' is considered heretical in Flatland. Those who speak of a third 
dimension are thought mad. Yet some, like the being called Vector, quietly study 
the mathematics that suggest dimensions beyond their plane.""",
        icon="🔷",
        related_entries=["lore_dimensions_intro", "lore_polygon_wars", "lore_sphere_visit"],
    ),
    
    "lore_w_axis": LoreEntry(
        id="lore_w_axis",
        title="The W-Axis: Fourth Spatial Dimension",
        category=LoreCategory.DIMENSIONS,
        short_description="Understanding the fourth spatial axis.",
        content="""The W-axis is perpendicular to all three familiar spatial dimensions. 
Just as 'up' is perpendicular to both 'forward' and 'left', W is perpendicular to 
up, forward, AND left simultaneously.

This is impossible to visualize directly - our minds evolved in 3D and cannot 
truly picture a fourth perpendicular direction. Instead, we must understand it 
mathematically and experience it intuitively.

Movement along W allows:
- Passing through 3D barriers (as they have no extent in W)
- Seeing the inside of closed 3D objects
- Existing in multiple 3D 'slices' at once

For a 4D being, all of 3D is visible at once - including the interiors of objects 
and the 'other side' of surfaces. This is comparable to how a 3D being can see 
the entire interior of a 2D shape at once.

The W-axis is sometimes confused with time. While they share mathematical 
similarities, spatial W and temporal T are distinct.""",
        icon="⟁",
        related_entries=["lore_dimensions_intro", "lore_tesseract", "lore_omnivision"],
    ),
    
    "lore_portals": LoreEntry(
        id="lore_portals",
        title="Dimensional Portals",
        category=LoreCategory.SCIENCE,
        short_description="How beings transcend between dimensions.",
        content="""Portals are tears in the fabric of dimensional space. They occur 
naturally at points where dimensional boundaries grow thin, but can also be created 
artificially by beings of sufficient power.

A portal does not simply transport - it TRANSFORMS. When a 1D being enters a portal 
to 2D, their entire existence is restructured. They gain the ability to perceive 
and move in a new direction. This process is not without risk - some beings are 
unable to handle the expanded perception and lose their minds.

Natural portals are unstable and temporary. They pulse in and out of existence, 
sometimes appearing for mere moments. Artificial portals can be stabilized, but 
require enormous energy to maintain.

The energy signature of a portal is distinctive - even a 1D being can sense its 
vibration from a great distance. This 'portal hum' has been described as the most 
beautiful and terrifying sound in existence.""",
        icon="🌀",
        related_entries=["lore_dimensions_intro"],
    ),
    
    "lore_shadows": LoreEntry(
        id="lore_shadows",
        title="Dimensional Shadows",
        category=LoreCategory.SCIENCE,
        short_description="How higher dimensions cast lower-dimensional shadows.",
        content="""Just as a 3D object casts a 2D shadow, a 4D object casts a 3D shadow.

Consider: when light shines on a cube, it casts a shadow that is a 2D shape - 
perhaps a square, perhaps a hexagon, depending on the angle. The shadow is a 
'projection' of the cube onto a lower dimension.

Similarly, when a 4D object exists near 3D space, it casts a 3D 'shadow'. A tesseract's 
shadow appears as a cube within a cube, connected at the vertices. But this is 
merely a shadow - the true tesseract is eight cubes arranged in ways that 3D space 
cannot contain.

Understanding shadows is key to perceiving higher dimensions. When a 3D being sees 
a 4D object's shadow, they are glimpsing something beyond their reality - incomplete, 
distorted, but real nonetheless.

The Oracle speaks of the day they saw a tesseract's shadow dance across the sky. 
That moment changed them forever.""",
        icon="🔮",
        related_entries=["lore_tesseract", "lore_w_axis"],
    ),
    
    "lore_tesseract": LoreEntry(
        id="lore_tesseract",
        title="The Tesseract: Hypercube",
        category=LoreCategory.BEINGS,
        short_description="The 8-cell, most iconic 4D shape.",
        content="""The tesseract, or 8-cell, is to 4D what the cube is to 3D. It is 
composed of eight cubic cells, arranged so that each cube shares its faces with 
six others.

Geometrically:
- 16 vertices
- 32 edges
- 24 square faces
- 8 cubic cells

When a tesseract rotates through the W-axis, its 3D shadow appears to turn itself 
inside out - the inner cube becomes the outer, and vice versa. This effect has 
driven observers mad, as it suggests impossible geometry.

As a being, Tesseract has existed since the dawn of hyperspace. They serve as 
guardian and guide to those who ascend to 4D, though their motives remain 
mysterious. Each of their eight cubic chambers is said to contain different 
aspects of hyperspace itself.

Some theorize that Tesseract is not a being at all, but a living piece of 4D 
geometry - consciousness emerging from pure mathematical truth.""",
        icon="❖",
        related_entries=["lore_polytopes", "lore_shadows", "lore_w_axis"],
    ),
    
    "lore_polytopes": LoreEntry(
        id="lore_polytopes",
        title="The Six Regular 4-Polytopes",
        category=LoreCategory.SCIENCE,
        short_description="The only regular shapes in 4D.",
        content="""In 4D, there are exactly six regular convex polytopes - the analogs 
of the five Platonic solids of 3D. Each represents a different form of geometric 
perfection.

**5-Cell (Pentachoron)**: The simplest, composed of 5 tetrahedra. The starting 
form of newly-ascended 4D beings.

**16-Cell (Hexadecachoron)**: The 4D cross-polytope, 8 vertices forming a 4D 
'plus sign'. Sharp and precise.

**8-Cell (Tesseract)**: The hypercube, most famous and studied. 16 vertices, 
8 cubic cells. The iconic 4D shape.

**24-Cell (Icositetrachoron)**: UNIQUE TO 4D. This self-dual polytope has no 
analog in any other dimension. 24 octahedral cells in perfect symmetry.

**120-Cell (Hecatonicosachoron)**: 600 vertices, 120 dodecahedral cells. 
Approaching the complexity of hyperspheres.

**600-Cell (Hexacosichoron)**: The ultimate form. 600 tetrahedral cells in 
harmony. Said to be the final evolution of a 4D being.

Each form grants different abilities and perceptions. Evolving between them 
requires enormous dimensional energy.""",
        icon="✧",
        related_entries=["lore_tesseract", "lore_24cell"],
    ),
    
    "lore_24cell": LoreEntry(
        id="lore_24cell",
        title="The 24-Cell: Unique to 4D",
        category=LoreCategory.BEINGS,
        short_description="A shape that can only exist in four dimensions.",
        content="""The 24-cell (Icositetrachoron) is perhaps the most remarkable of 
all polytopes. It exists ONLY in 4D - there is no 3D equivalent, no 5D version. 
It is perfectly unique to the fourth dimension.

This uniqueness manifests in its geometry:
- 24 vertices
- 96 edges  
- 96 triangular faces
- 24 octahedral cells

The 24-cell is SELF-DUAL, meaning its dual polytope is another 24-cell. This 
property of being its own geometric opposite gives it a strange metaphysical 
significance.

Beings who achieve 24-cell form report experiences of profound self-reflection. 
They can perceive themselves from outside themselves. Some describe it as 
'being the mirror and the reflection simultaneously'.

The being known as Icosi delights in this uniqueness. When asked about existence 
in other dimensions, they simply laugh and say 'Those places are not for me. 
I am exactly where I must be.'""",
        icon="✦",
        related_entries=["lore_polytopes", "lore_tesseract"],
    ),
    
    "lore_omnivision": LoreEntry(
        id="lore_omnivision",
        title="Omnivision: Seeing All",
        category=LoreCategory.PHILOSOPHY,
        short_description="How 4D beings perceive lower dimensions.",
        content="""From the fourth dimension, all of 3D is visible simultaneously. 
Not just the surface of objects, but their INSIDES. Not just one side of a wall, 
but BOTH sides at once. This is omnivision.

Consider: a 3D being looking at a 2D circle sees its entire interior at once. 
Nothing inside the circle is hidden - the 2D beings living there have no secrets 
from the 3D observer.

Similarly, a 4D being sees all of 3D. The contents of locked rooms, the organs 
inside bodies, the reverse side of every surface - all visible, all at once.

This raises profound questions:
- Do higher-dimensional beings watch us always?
- Is privacy an illusion of limited perception?
- What watches from 5D? From 6D? From infinity?

Some 4D beings become overwhelmed by omnivision and retreat to perceiving only 
one 3D 'slice' at a time. Others embrace the totality and lose their connection 
to individual moments and spaces.

The wise learn to filter - to see what is needed and ignore the rest.""",
        icon="👁️‍🗨️",
        related_entries=["lore_w_axis", "lore_dimensions_intro"],
    ),
    
    "lore_sphere_visit": LoreEntry(
        id="lore_sphere_visit",
        title="The Sphere's Visit to Flatland",
        category=LoreCategory.HISTORY,
        short_description="When a 3D being tried to teach 2D beings about depth.",
        content="""Long ago, the being known as Sphere descended into Flatland, hoping 
to enlighten its inhabitants about the third dimension.

The encounter is legendary. Sphere appeared to a Square (a respected member of 
Flatland society) and tried to explain 'up' - a direction perpendicular to their 
entire reality.

'Imagine,' said Sphere, 'a direction that is neither North, South, East, nor West. 
A direction that goes... UPWARD.'

The Square could not comprehend. When Sphere lifted the Square out of Flatland 
briefly, allowing them to see their world from above, the Square was forever 
changed - but none believed their tale.

The Square was imprisoned for heresy. Sphere was labeled a demon or a god, 
depending on who told the story.

Yet the seed was planted. Beings like Vector study the mathematics in secret, 
believing that what Sphere showed is real. They wait for another visitor from 
beyond their dimension.

They wait for beings like you.""",
        icon="📖",
        related_entries=["lore_flatland", "lore_dimensions_intro"],
    ),
    
    "lore_polygon_wars": LoreEntry(
        id="lore_polygon_wars",
        title="The Polygon Wars",
        category=LoreCategory.HISTORY,
        short_description="Conflicts in Flatland.",
        content="""Flatland's history is marked by brutal conflicts between the 
geometric classes. The most significant was the Color Rebellion, when lower 
polygons attempted to distinguish themselves through pigmentation rather than 
shape.

The ruling Circles crushed the rebellion mercilessly. Color was banned. The 
rigid hierarchy was reinforced with new laws:
- Irregular polygons to be destroyed at birth
- Speaking of higher dimensions is heresy
- Movement between classes is impossible

Yet conflict continues. Triangles form secret societies. Squares plot against 
Pentagons. And occasionally, an Irregular survives and grows powerful in the 
shadows.

The current state is tense peace. The Perfect Square who rules the local region 
maintains order through fear. But whispers of a 'being from above' who once 
visited spread among the lower classes.

Some say the next war will not be between shapes, but between dimensions.""",
        icon="⚔️",
        related_entries=["lore_flatland"],
    ),
    
    "lore_hyperspace_dangers": LoreEntry(
        id="lore_hyperspace_dangers",
        title="Dangers of Hyperspace",
        category=LoreCategory.PHILOSOPHY,
        short_description="Warnings for those who would ascend to 4D.",
        content="""The Oracle speaks of hyperspace with reverence and terror. Those 
who ascend unprepared face numerous dangers:

**PERCEPTION OVERLOAD**: The mind is not built for omnivision. Some beings who 
enter 4D cannot process the infinite information and simply... stop. Their minds 
freeze, unable to handle seeing everything at once.

**SPATIAL MADNESS**: The W-axis defies intuition. Some beings become convinced 
that they are simultaneously in all places. They lose the ability to focus on 
any single location and spread themselves thin across hyperspace until they 
dissipate entirely.

**THE WATCHERS**: Ancient beings dwell in 4D. Some are benevolent, like Tesseract. 
Others... are not. They hunger for the novelty of lower-dimensional minds.

**THE CALL OF 5D**: Once you perceive 4D, you become aware of 5D. And 6D. The 
temptation to keep ascending can consume a being until they attempt to transcend 
beyond what their consciousness can survive.

The Oracle concludes: 'Ascend with wisdom. Know your limits. And always, ALWAYS, 
remember your origin. The line that birthed you. The plane that nurtured you. 
The volume that shaped you. These are your anchors. Lose them, and you are lost.'""",
        icon="⚠️",
        related_entries=["lore_w_axis", "lore_omnivision"],
    ),
}


class Codex:
    """The player's collection of discovered lore."""
    
    def __init__(self):
        self.entries: Dict[str, LoreEntry] = {}
        self.discovered_ids: List[str] = []
        
        # Load all lore (but mark as undiscovered)
        for lore_id, entry in CAMPAIGN_LORE.items():
            self.entries[lore_id] = entry
    
    def discover(self, lore_id: str, source: Optional[str] = None) -> Optional[LoreEntry]:
        """Discover a lore entry."""
        entry = self.entries.get(lore_id)
        if not entry:
            return None
        
        if not entry.discovered:
            entry.discovered = True
            entry.discovery_source = source
            self.discovered_ids.append(lore_id)
        
        return entry
    
    def is_discovered(self, lore_id: str) -> bool:
        """Check if a lore entry has been discovered."""
        entry = self.entries.get(lore_id)
        return entry.discovered if entry else False
    
    def get_discovered(self) -> List[LoreEntry]:
        """Get all discovered lore entries."""
        return [self.entries[lid] for lid in self.discovered_ids]
    
    def get_by_category(self, category: LoreCategory) -> List[LoreEntry]:
        """Get discovered entries in a category."""
        return [
            e for e in self.get_discovered()
            if e.category == category
        ]
    
    def get_discovery_count(self) -> tuple:
        """Get (discovered, total) counts."""
        return len(self.discovered_ids), len(self.entries)
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage."""
        total = len(self.entries)
        if total == 0:
            return 100.0
        return (len(self.discovered_ids) / total) * 100
