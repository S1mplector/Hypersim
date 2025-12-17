"""Improved interactive demo menu for HyperSim.

A completely rewritten demo browser with modern UI, categories,
search, settings, and many quality-of-life improvements.
"""
from __future__ import annotations

import os
import math
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Optional, Tuple, Any
from datetime import datetime

import pygame
import numpy as np

from hypersim.objects import (
    Hypercube, Simplex4D, SixteenCell, TwentyFourCell, Duoprism,
    HypercubeGrid, CliffordTorus, SimplexPrism, RectifiedTesseract,
    CubePrism, Spherinder, Mobius4D, IcosaPrism, PenteractFrame,
    DodecaPrism, SixHundredCell, TetraPrism, OctaPrism, TorusKnot4D,
    HopfLink4D, OneHundredTwentyCell, GrandAntiprism, RuncinatedTesseract,
    TruncatedTesseract, CantellatedTesseract, BitruncatedTesseract,
    Snub24Cell, OmnitruncatedTesseract, Tesseractihexadecachoron,
    KleinBottle4D, Pentachoron,
)

from .ui_components import (
    Colors, Button, Slider, Panel, TabBar, SearchBox, Toggle, Toast,
    Animation, lerp, lerp_color, ease_out_cubic,
)

# Import new features
from hypersim.visualization.materials import Material, Gradient, GradientType, Materials
from hypersim.visualization.recorder import Recorder, RecordingConfig
from hypersim.visualization.effects import MotionBlur, MotionBlurConfig, Glow, GlowConfig
from hypersim.core.morphing import ShapeMorpher, MorphStrategy, EasingType
from hypersim.physics.particles import ParticleSystem, ParticleConfig, ParticleEmitter, EmitterShape


@dataclass
class DemoObject:
    """Definition of a demo object."""
    name: str
    description: str
    factory: Callable[[], Any]
    category: str
    color: Tuple[int, int, int] = (100, 200, 255)
    line_width: int = 2
    vertices: int = 0
    edges: int = 0
    faces: int = 0
    cells: int = 0
    math_info: str = ""
    tags: List[str] = field(default_factory=list)


# All demo objects organized by category
DEMO_OBJECTS: List[DemoObject] = [
    # Regular Polytopes
    DemoObject(
        name="Pentachoron (5-cell)",
        description="Simplest regular 4-polytope, 4D tetrahedron",
        factory=lambda: Pentachoron(size=1.3),
        category="Regular Polytopes",
        color=(255, 180, 100),
        vertices=5, edges=10, faces=10, cells=5,
        math_info="Schläfli: {3,3,3}. Self-dual. Complete graph K₅.",
        tags=["regular", "simplex", "self-dual"],
    ),
    DemoObject(
        name="Tesseract (Hypercube)",
        description="4D cube with 16 vertices, 32 edges",
        factory=lambda: Hypercube(size=1.3),
        category="Regular Polytopes",
        color=(90, 200, 255),
        vertices=16, edges=32, faces=24, cells=8,
        math_info="Schläfli: {4,3,3}. Dual of 16-cell. Vertices at (±1,±1,±1,±1).",
        tags=["regular", "cube", "hypercube"],
    ),
    DemoObject(
        name="16-cell",
        description="Hyperoctahedron, dual of tesseract",
        factory=lambda: SixteenCell(size=1.1),
        category="Regular Polytopes",
        color=(140, 255, 160),
        vertices=8, edges=24, faces=32, cells=16,
        math_info="Schläfli: {3,3,4}. Dual of tesseract. Vertices on axes.",
        tags=["regular", "octahedron", "dual"],
    ),
    DemoObject(
        name="24-cell",
        description="Self-dual regular polytope, unique to 4D",
        factory=lambda: TwentyFourCell(size=1.1),
        category="Regular Polytopes",
        color=(200, 130, 255),
        vertices=24, edges=96, faces=96, cells=24,
        math_info="Schläfli: {3,4,3}. Self-dual. Only regular polytope unique to 4D.",
        tags=["regular", "self-dual", "unique"],
    ),
    DemoObject(
        name="120-cell",
        description="600 vertices, largest regular polytope",
        factory=lambda: OneHundredTwentyCell(size=1.0),
        category="Regular Polytopes",
        color=(255, 220, 150),
        line_width=1,
        vertices=600, edges=1200, faces=720, cells=120,
        math_info="Schläfli: {5,3,3}. Contains golden ratio. 120 dodecahedral cells.",
        tags=["regular", "golden", "complex"],
    ),
    DemoObject(
        name="600-cell",
        description="120 vertices, 600 tetrahedral cells",
        factory=lambda: SixHundredCell(size=1.0),
        category="Regular Polytopes",
        color=(255, 200, 120),
        line_width=1,
        vertices=120, edges=720, faces=1200, cells=600,
        math_info="Schläfli: {3,3,5}. Dual of 120-cell. Golden ratio coordinates.",
        tags=["regular", "golden", "dual"],
    ),
    
    # Uniform Polytopes
    DemoObject(
        name="Rectified Tesseract",
        description="Rectified hypercube with 24 vertices",
        factory=lambda: RectifiedTesseract(size=1.2),
        category="Uniform Polytopes",
        color=(180, 220, 255),
        vertices=24, edges=96, faces=64, cells=24,
        math_info="Vertices at edge midpoints of tesseract. r{4,3,3}.",
        tags=["uniform", "rectified"],
    ),
    DemoObject(
        name="Truncated Tesseract",
        description="Tesseract with truncated vertices",
        factory=lambda: TruncatedTesseract(size=1.0),
        category="Uniform Polytopes",
        color=(150, 200, 255),
        vertices=64, edges=128, faces=88, cells=24,
        math_info="t{4,3,3}. Truncation creates octagonal faces.",
        tags=["uniform", "truncated"],
    ),
    DemoObject(
        name="Cantellated Tesseract",
        description="Edge-beveled hypercube",
        factory=lambda: CantellatedTesseract(size=1.0),
        category="Uniform Polytopes",
        color=(120, 180, 255),
        vertices=96, edges=288, faces=272, cells=80,
        math_info="rr{4,3,3}. Cantellation bevels all edges.",
        tags=["uniform", "cantellated"],
    ),
    DemoObject(
        name="Bitruncated Tesseract",
        description="Bitruncation of tesseract and 16-cell",
        factory=lambda: BitruncatedTesseract(size=1.0),
        category="Uniform Polytopes",
        color=(100, 160, 255),
        vertices=96, edges=240, faces=200, cells=56,
        math_info="2t{4,3,3}. Sits between tesseract and 16-cell.",
        tags=["uniform", "bitruncated"],
    ),
    DemoObject(
        name="Runcinated Tesseract",
        description="Expanded hypercube",
        factory=lambda: RuncinatedTesseract(size=1.0),
        category="Uniform Polytopes",
        color=(80, 140, 255),
        vertices=64, edges=192, faces=192, cells=80,
        math_info="Runcination expands cells outward.",
        tags=["uniform", "runcinated"],
    ),
    DemoObject(
        name="Omnitruncated Tesseract",
        description="Maximum truncation, 768 vertices",
        factory=lambda: OmnitruncatedTesseract(size=0.8),
        category="Uniform Polytopes",
        color=(60, 120, 255),
        line_width=1,
        vertices=768, edges=1536, faces=1040, cells=272,
        math_info="tr{4,3,3}. Most complex in tesseract family.",
        tags=["uniform", "omnitruncated", "complex"],
    ),
    DemoObject(
        name="Rectified 24-cell",
        description="Self-dual, edge-transitive",
        factory=lambda: Tesseractihexadecachoron(size=1.0),
        category="Uniform Polytopes",
        color=(180, 140, 255),
        vertices=96, edges=288, faces=288, cells=96,
        math_info="r{3,4,3}. Self-dual and isotoxal.",
        tags=["uniform", "rectified", "self-dual"],
    ),
    DemoObject(
        name="Snub 24-cell",
        description="Chiral polytope with icosahedral cells",
        factory=lambda: Snub24Cell(size=1.0, chirality='right'),
        category="Uniform Polytopes",
        color=(255, 160, 200),
        vertices=96, edges=432, faces=480, cells=144,
        math_info="Chiral (left/right forms). 24 icosahedra + 120 tetrahedra.",
        tags=["uniform", "snub", "chiral", "golden"],
    ),
    DemoObject(
        name="Grand Antiprism",
        description="Unique uniform polytope with 100 vertices",
        factory=lambda: GrandAntiprism(size=1.0),
        category="Uniform Polytopes",
        color=(255, 140, 180),
        vertices=100, edges=500, faces=720, cells=320,
        math_info="Non-Wythoffian. Two rings of 10 antiprisms each.",
        tags=["uniform", "antiprism", "unique"],
    ),
    
    # Prisms
    DemoObject(
        name="Duoprism (5×6)",
        description="Pentagon × hexagon product",
        factory=lambda: Duoprism(m=5, n=6, size=1.1),
        category="Prisms & Products",
        color=(255, 220, 120),
        vertices=30, edges=60, faces=41, cells=11,
        math_info="Cartesian product of two polygons on a 4D torus.",
        tags=["prism", "product", "torus"],
    ),
    DemoObject(
        name="Cube Prism",
        description="Cube extruded along W",
        factory=lambda: CubePrism(size=1.2, height=1.0),
        category="Prisms & Products",
        color=(200, 255, 140),
        vertices=16, edges=32, faces=24, cells=10,
        math_info="Cube × interval. Two cubes connected in W.",
        tags=["prism", "cube"],
    ),
    DemoObject(
        name="Tetrahedron Prism",
        description="Tetrahedron extruded along W",
        factory=lambda: TetraPrism(size=1.1, height=0.75),
        category="Prisms & Products",
        color=(255, 200, 160),
        vertices=8, edges=16, faces=14, cells=6,
        math_info="Tetrahedron × interval.",
        tags=["prism", "tetrahedron"],
    ),
    DemoObject(
        name="Octahedron Prism",
        description="Octahedron extruded along W",
        factory=lambda: OctaPrism(size=1.1, height=0.8),
        category="Prisms & Products",
        color=(190, 230, 255),
        vertices=12, edges=24, faces=20, cells=8,
        math_info="Octahedron × interval.",
        tags=["prism", "octahedron"],
    ),
    DemoObject(
        name="Simplex Prism",
        description="5-cell prism",
        factory=lambda: SimplexPrism(size=1.1, height=0.75),
        category="Prisms & Products",
        color=(255, 180, 120),
        vertices=10, edges=25, faces=20, cells=7,
        math_info="Two 5-cells connected along W.",
        tags=["prism", "simplex"],
    ),
    DemoObject(
        name="Icosahedron Prism",
        description="Icosahedron extruded along W",
        factory=lambda: IcosaPrism(size=1.0, height=1.0),
        category="Prisms & Products",
        color=(255, 210, 150),
        line_width=1,
        vertices=24, edges=54, faces=42, cells=22,
        math_info="Icosahedron × interval.",
        tags=["prism", "icosahedron"],
    ),
    DemoObject(
        name="Dodecahedron Prism",
        description="Dodecahedron extruded along W",
        factory=lambda: DodecaPrism(size=1.0, height=1.0),
        category="Prisms & Products",
        color=(255, 235, 180),
        vertices=40, edges=80, faces=54, cells=14,
        math_info="Dodecahedron × interval.",
        tags=["prism", "dodecahedron", "golden"],
    ),
    
    # Manifolds & Surfaces
    DemoObject(
        name="Clifford Torus",
        description="Flat torus in S³, product of circles",
        factory=lambda: CliffordTorus(segments_u=32, segments_v=20, size=1.0),
        category="Manifolds",
        color=(255, 160, 200),
        line_width=1,
        math_info="S¹ × S¹ embedded in S³. Intrinsically flat.",
        tags=["manifold", "torus", "flat"],
    ),
    DemoObject(
        name="Spherinder",
        description="Sphere × interval, 4D cylinder",
        factory=lambda: Spherinder(radius=1.0, height=1.0, segments=24, stacks=12),
        category="Manifolds",
        color=(200, 255, 200),
        line_width=1,
        math_info="Sphere extruded along W. Spherical cross-sections.",
        tags=["manifold", "sphere", "cylinder"],
    ),
    DemoObject(
        name="Klein Bottle (4D)",
        description="Non-orientable surface embedded in 4D",
        factory=lambda: KleinBottle4D(radius=1.0, segments_u=40, segments_v=20),
        category="Manifolds",
        color=(180, 220, 255),
        line_width=1,
        math_info="Figure-8 parametrization. Cannot embed in 3D without self-intersection.",
        tags=["manifold", "non-orientable", "topology"],
    ),
    DemoObject(
        name="Möbius Strip (4D)",
        description="Non-orientable surface in 4D",
        factory=lambda: Mobius4D(radius=1.0, width=0.5, segments_u=72, segments_v=14),
        category="Manifolds",
        color=(255, 220, 160),
        line_width=1,
        math_info="Möbius band embedded in 4D to avoid self-intersection.",
        tags=["manifold", "non-orientable", "mobius"],
    ),
    DemoObject(
        name="Torus Knot (3,5)",
        description="Trefoil-like knot on torus",
        factory=lambda: TorusKnot4D(p=3, q=5, segments=200, radius=1.0),
        category="Manifolds",
        color=(255, 180, 220),
        math_info="(3,5) torus knot on Clifford torus.",
        tags=["manifold", "knot", "torus"],
    ),
    DemoObject(
        name="Hopf Link",
        description="Two linked circles in orthogonal planes",
        factory=lambda: HopfLink4D(radius=1.0, segments=160),
        category="Manifolds",
        color=(180, 220, 255),
        math_info="Circles in XY and ZW planes. Classic topological link.",
        tags=["manifold", "link", "topology"],
    ),
    
    # Lattices & Procedural
    DemoObject(
        name="Hypercube Grid (3³)",
        description="Regular 4D lattice",
        factory=lambda: HypercubeGrid(divisions=3, size=1.0),
        category="Lattices",
        color=(120, 200, 255),
        line_width=1,
        math_info="Regular grid in 4D. Vertices = divisions⁴.",
        tags=["lattice", "grid", "procedural"],
    ),
    DemoObject(
        name="Penteract Frame",
        description="5D hypercube projected to 4D",
        factory=lambda: PenteractFrame(size=1.0),
        category="Lattices",
        color=(180, 255, 255),
        math_info="5D cube skeleton projected to 4D. 80 edges.",
        tags=["higher-dim", "projection", "5d"],
    ),
]


class DemoMenu:
    """Improved demo menu with modern UI."""
    
    def __init__(self, width: int = 1400, height: int = 900):
        pygame.init()
        pygame.display.set_caption("HyperSim - 4D Object Explorer")
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        
        # State
        self.running = True
        self.selected_index = 0
        self.filtered_objects = list(DEMO_OBJECTS)
        self.current_object: Any = None
        self.auto_spin = True
        self.show_info = False
        self.show_help = False
        self.show_settings = False
        
        # Settings
        self.spin_speed = 1.0
        self.projection_scale = 150.0
        self.w_factor = 0.3
        self.line_width_multiplier = 1.0
        self.bg_brightness = 0.05
        
        # New features
        self.use_gradient = False
        self.gradient_type = "depth"  # depth, radial, w_axis, rainbow
        self.show_particles = False
        self.motion_blur_enabled = False
        self.is_recording = False
        self.morph_mode = False
        
        # Recording
        self.recorder = Recorder(RecordingConfig(fps=30))
        
        # Effects
        self.motion_blur = MotionBlur(MotionBlurConfig(samples=6, decay=0.6, enabled=False))
        self.glow = Glow(GlowConfig(radius=3, intensity=0.3, enabled=False))
        
        # Morphing
        self.morpher = ShapeMorpher(strategy=MorphStrategy.DISTRIBUTE, easing=EasingType.EASE_IN_OUT)
        self.morph_target_idx: Optional[int] = None
        
        # Particles
        self.particle_system = ParticleSystem()
        self._setup_ambient_particles()
        
        # Categories
        self.categories = self._get_categories()
        self.selected_category = "All"
        
        # Animations
        self._transition_anim = Animation(1, 1, 0)
        self._info_anim = Animation(0, 0, 0)
        
        # UI Components
        self._init_ui()
        
        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 20)
        self.font_body = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_mono = pygame.font.SysFont("Consolas", 14)
        
        # Toasts
        self.toasts: List[Toast] = []
        
        # Load first object
        self._load_object(0)
    
    def _init_from_app(self) -> None:
        """Initialize when launched from the master app (screen already set)."""
        pygame.display.set_caption("HyperSim - 4D Object Explorer")
        
        # State
        self.running = True
        self.selected_index = 0
        self.filtered_objects = list(DEMO_OBJECTS)
        self.current_object: Any = None
        self.auto_spin = True
        self.show_info = False
        self.show_help = False
        self.show_settings = False
        
        # Settings
        self.spin_speed = 1.0
        self.projection_scale = 150.0
        self.w_factor = 0.3
        self.line_width_multiplier = 1.0
        self.bg_brightness = 0.05
        
        # New features
        self.use_gradient = False
        self.gradient_type = "depth"
        self.show_particles = False
        self.motion_blur_enabled = False
        self.is_recording = False
        self.morph_mode = False
        
        # Recording
        self.recorder = Recorder(RecordingConfig(fps=30))
        
        # Effects
        self.motion_blur = MotionBlur(MotionBlurConfig(samples=6, decay=0.6, enabled=False))
        self.glow = Glow(GlowConfig(radius=3, intensity=0.3, enabled=False))
        
        # Morphing
        self.morpher = ShapeMorpher(strategy=MorphStrategy.DISTRIBUTE, easing=EasingType.EASE_IN_OUT)
        self.morph_target_idx: Optional[int] = None
        
        # Particles
        self.particle_system = ParticleSystem()
        self._setup_ambient_particles()
        
        # Categories
        self.categories = self._get_categories()
        self.selected_category = "All"
        
        # Animations
        self._transition_anim = Animation(1, 1, 0)
        self._info_anim = Animation(0, 0, 0)
        
        # UI Components
        self._init_ui()
        
        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_subtitle = pygame.font.SysFont("Arial", 20)
        self.font_body = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_mono = pygame.font.SysFont("Consolas", 14)
        
        # Toasts
        self.toasts: List[Toast] = []
        
        # Load first object
        self._load_object(0)
    
    def _setup_ambient_particles(self) -> None:
        """Setup ambient particle effect."""
        config = ParticleConfig(
            lifetime_min=3.0,
            lifetime_max=5.0,
            speed_min=0.05,
            speed_max=0.15,
            size_start=2,
            size_end=1,
            color_start=(100, 150, 255),
            color_end=(50, 80, 150),
            alpha_start=80,
            alpha_end=0,
            gravity_scale=0.0,
        )
        emitter = self.particle_system.create_emitter(
            np.array([0, 0, 0, 0], dtype=np.float32),
            config,
            shape=EmitterShape.HYPERSPHERE,
            shape_size=3.0,
            emission_rate=3,
            max_particles=50,
        )
        emitter.enabled = False  # Start disabled
    
    def _get_categories(self) -> List[str]:
        """Get unique categories."""
        cats = ["All"]
        for obj in DEMO_OBJECTS:
            if obj.category not in cats:
                cats.append(obj.category)
        return cats
    
    def _init_ui(self) -> None:
        """Initialize UI components."""
        # Search box
        self.search_box = SearchBox(
            pygame.Rect(20, 70, 280, 36),
            placeholder="Search objects...",
            on_change=self._on_search,
        )
        
        # Category tabs
        self.category_tabs = TabBar(
            pygame.Rect(20, 120, 280, 32),
            tabs=["All", "Regular", "Uniform", "Prisms", "More"],
            on_change=self._on_category_change,
        )
        
        # Control toggles
        self.spin_toggle = Toggle(
            (self.width - 280, 80),
            label="Auto-spin",
            value=True,
            on_change=lambda v: setattr(self, 'auto_spin', v),
        )
        
        # Settings sliders
        self.speed_slider = Slider(
            pygame.Rect(self.width - 280, 140, 200, 24),
            min_value=0.0, max_value=3.0, value=1.0,
            label="Spin Speed",
            on_change=lambda v: setattr(self, 'spin_speed', v),
        )
        
        self.scale_slider = Slider(
            pygame.Rect(self.width - 280, 200, 200, 24),
            min_value=50.0, max_value=300.0, value=150.0,
            label="Projection Scale",
            on_change=lambda v: setattr(self, 'projection_scale', v),
        )
        
        self.w_slider = Slider(
            pygame.Rect(self.width - 280, 260, 200, 24),
            min_value=0.0, max_value=1.0, value=0.3,
            label="W Perspective",
            on_change=lambda v: setattr(self, 'w_factor', v),
        )
        
        # Feature toggles
        self.gradient_toggle = Toggle(
            (self.width - 280, 320),
            label="Color Gradient",
            value=False,
            on_change=lambda v: setattr(self, 'use_gradient', v),
        )
        
        self.particles_toggle = Toggle(
            (self.width - 280, 355),
            label="Particles",
            value=False,
            on_change=self._toggle_particles,
        )
        
        self.blur_toggle = Toggle(
            (self.width - 280, 390),
            label="Motion Blur",
            value=False,
            on_change=self._toggle_motion_blur,
        )
        
        # Buttons
        self.screenshot_btn = Button(
            pygame.Rect(self.width - 280, self.height - 110, 120, 36),
            text="Screenshot",
            on_click=self._take_screenshot,
            color=Colors.ACCENT_GREEN,
        )
        
        self.record_btn = Button(
            pygame.Rect(self.width - 150, self.height - 110, 120, 36),
            text="Record",
            on_click=self._toggle_recording,
            color=Colors.ACCENT_ORANGE,
        )
        
        self.morph_btn = Button(
            pygame.Rect(self.width - 280, self.height - 60, 120, 36),
            text="Morph Next",
            on_click=self._start_morph,
            color=Colors.ACCENT_PURPLE,
        )
        
        self.reset_btn = Button(
            pygame.Rect(self.width - 150, self.height - 60, 120, 36),
            text="Reset",
            on_click=self._reset_view,
            color=Colors.ACCENT_CYAN,
        )
    
    def _on_search(self, query: str) -> None:
        """Filter objects by search query."""
        query = query.lower().strip()
        if not query:
            self.filtered_objects = self._filter_by_category(self.selected_category)
        else:
            self.filtered_objects = [
                obj for obj in self._filter_by_category(self.selected_category)
                if query in obj.name.lower() 
                or query in obj.description.lower()
                or any(query in tag for tag in obj.tags)
            ]
        
        if self.filtered_objects:
            self._load_object(0)
    
    def _filter_by_category(self, category: str) -> List[DemoObject]:
        """Filter objects by category."""
        if category == "All":
            return list(DEMO_OBJECTS)
        
        # Map tab names to actual categories
        cat_map = {
            "Regular": "Regular Polytopes",
            "Uniform": "Uniform Polytopes",
            "Prisms": "Prisms & Products",
            "More": None,  # Everything else
        }
        
        target = cat_map.get(category, category)
        if target is None:
            return [obj for obj in DEMO_OBJECTS 
                    if obj.category not in ["Regular Polytopes", "Uniform Polytopes", "Prisms & Products"]]
        return [obj for obj in DEMO_OBJECTS if obj.category == target]
    
    def _on_category_change(self, index: int) -> None:
        """Handle category tab change."""
        tabs = ["All", "Regular", "Uniform", "Prisms", "More"]
        self.selected_category = tabs[index]
        self.filtered_objects = self._filter_by_category(self.selected_category)
        self.search_box.text = ""
        if self.filtered_objects:
            self._load_object(0)
    
    def _load_object(self, index: int) -> None:
        """Load a demo object."""
        if not self.filtered_objects:
            self.current_object = None
            return
        
        self.selected_index = index % len(self.filtered_objects)
        demo = self.filtered_objects[self.selected_index]
        
        try:
            self.current_object = demo.factory()
            # Apply initial rotation for visual interest
            if hasattr(self.current_object, 'rotate'):
                self.current_object.rotate(xy=0.35, xw=0.28, yw=0.22, zw=0.18)
            
            self._transition_anim.reset(0, 1, 0.3)
        except Exception as e:
            self.current_object = None
            self._add_toast(f"Failed to load: {e}", Colors.ERROR)
    
    def _add_toast(self, message: str, color: Tuple[int, int, int] = Colors.ACCENT_BLUE) -> None:
        """Add a toast notification."""
        self.toasts.append(Toast(message, duration=3.0, color=color))
    
    def _take_screenshot(self) -> None:
        """Save a screenshot."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hypersim_screenshot_{timestamp}.png"
        
        try:
            pygame.image.save(self.screen, filename)
            self._add_toast(f"Saved: {filename}", Colors.SUCCESS)
        except Exception as e:
            self._add_toast(f"Screenshot failed: {e}", Colors.ERROR)
    
    def _reset_view(self) -> None:
        """Reset the current object."""
        self._load_object(self.selected_index)
        self._add_toast("View reset", Colors.ACCENT_BLUE)
    
    def _toggle_particles(self, enabled: bool) -> None:
        """Toggle particle effects."""
        self.show_particles = enabled
        if self.particle_system.emitters:
            self.particle_system.emitters[0].enabled = enabled
        status = "enabled" if enabled else "disabled"
        self._add_toast(f"Particles {status}", Colors.ACCENT_CYAN)
    
    def _toggle_motion_blur(self, enabled: bool) -> None:
        """Toggle motion blur effect."""
        self.motion_blur_enabled = enabled
        self.motion_blur.set_enabled(enabled)
        status = "enabled" if enabled else "disabled"
        self._add_toast(f"Motion blur {status}", Colors.ACCENT_PURPLE)
    
    def _toggle_recording(self) -> None:
        """Toggle GIF recording."""
        if self.is_recording:
            self.recorder.stop()
            self.is_recording = False
            # Save the recording
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hypersim_recording_{timestamp}.gif"
            self._add_toast(f"Saving {filename}...", Colors.ACCENT_ORANGE)
            if self.recorder.save(filename):
                self._add_toast(f"Saved: {filename} ({self.recorder.frame_count} frames)", Colors.SUCCESS)
            else:
                self._add_toast("Recording save failed", Colors.ERROR)
            self.record_btn.text = "Record"
            self.record_btn.color = Colors.ACCENT_ORANGE
        else:
            self.recorder.start()
            self.is_recording = True
            self.record_btn.text = "Stop"
            self.record_btn.color = Colors.ERROR
            self._add_toast("Recording started...", Colors.ACCENT_ORANGE)
    
    def _start_morph(self) -> None:
        """Start morphing to next object."""
        if self.morpher.is_morphing:
            self._add_toast("Morph in progress...", Colors.WARNING)
            return
        
        if not self.filtered_objects or len(self.filtered_objects) < 2:
            self._add_toast("Need at least 2 objects to morph", Colors.WARNING)
            return
        
        # Get next object
        next_idx = (self.selected_index + 1) % len(self.filtered_objects)
        next_demo = self.filtered_objects[next_idx]
        
        try:
            next_obj = next_demo.factory()
            if hasattr(next_obj, 'rotate'):
                next_obj.rotate(xy=0.35, xw=0.28, yw=0.22, zw=0.18)
            
            self.morpher.start_morph(self.current_object, next_obj, duration=1.5)
            self.morph_target_idx = next_idx
            self._add_toast(f"Morphing to {next_demo.name}...", Colors.ACCENT_PURPLE)
        except Exception as e:
            self._add_toast(f"Morph failed: {e}", Colors.ERROR)
    
    def _project_vertex(self, v: np.ndarray) -> Tuple[int, int, float]:
        """Project a 4D vertex to 2D screen coordinates."""
        x, y, z, w = v
        
        # W-based scaling
        w_scale = 1.0 / (1.0 + abs(w) * self.w_factor)
        
        # Apply scaling
        proj_x = x * w_scale * self.projection_scale
        proj_y = -y * w_scale * self.projection_scale
        depth = z * w_scale
        
        # Center on render area (between sidebars)
        center_x = 320 + (self.width - 620) // 2
        center_y = self.height // 2
        
        return int(proj_x + center_x), int(proj_y + center_y), depth
    
    def _render_object(self) -> None:
        """Render the current 4D object."""
        if self.current_object is None and not self.morpher.is_morphing:
            return
        
        demo = self.filtered_objects[self.selected_index]
        
        # Get vertices - from morpher if morphing, otherwise from object
        if self.morpher.is_morphing:
            vertices = self.morpher.vertices
            edges = self.morpher.edges
            # Interpolate color during morph
            if self.morph_target_idx is not None:
                target_demo = self.filtered_objects[self.morph_target_idx]
                t = self.morpher.progress
                base_color = tuple(
                    int(demo.color[i] + (target_demo.color[i] - demo.color[i]) * t)
                    for i in range(3)
                )
            else:
                base_color = demo.color
        else:
            vertices = self.current_object.get_transformed_vertices()
            edges = self.current_object.edges
            base_color = demo.color
        
        # Project all vertices
        projected = [self._project_vertex(np.array(v)) for v in vertices]
        
        # Sort edges by depth (back to front)
        edge_data = []
        for a, b in edges:
            if a < len(projected) and b < len(projected):
                avg_depth = (projected[a][2] + projected[b][2]) / 2
                edge_data.append((avg_depth, a, b, vertices[a], vertices[b]))
        edge_data.sort(reverse=True)
        
        # Apply transition animation
        alpha = int(255 * self._transition_anim.value)
        
        # Draw edges with depth-based or gradient coloring
        for depth, a, b, v1, v2 in edge_data:
            p1 = (projected[a][0], projected[a][1])
            p2 = (projected[b][0], projected[b][1])
            
            # Depth-based color variation
            t = (depth + 2) / 4  # Normalize depth
            t = max(0, min(1, t))
            
            if self.use_gradient:
                # Use gradient coloring
                if self.gradient_type == "rainbow":
                    # Rainbow based on W coordinate
                    w_val = (v1[3] + v2[3]) / 2
                    hue = (w_val + 1.5) / 3.0  # Map to 0-1
                    color = self._hsv_to_rgb(hue % 1.0, 0.8, 1.0 - t * 0.4)
                elif self.gradient_type == "radial":
                    # Radial gradient
                    dist = (np.linalg.norm(v1) + np.linalg.norm(v2)) / 2
                    r_t = min(1, dist / 2)
                    color = (
                        int(255 * (1 - r_t) + 80 * r_t),
                        int(200 * (1 - r_t) + 255 * r_t),
                        int(255 * (1 - r_t) + 150 * r_t),
                    )
                    color = tuple(int(c * (0.5 + 0.5 * (1 - t))) for c in color)
                else:  # depth gradient (default)
                    near_color = (255, 255, 255)
                    far_color = (50, 80, 150)
                    color = tuple(
                        int(near_color[i] * (1 - t) + far_color[i] * t)
                        for i in range(3)
                    )
            else:
                color = tuple(int(c * (0.4 + 0.6 * (1 - t))) for c in base_color)
            
            width = max(1, int(demo.line_width * self.line_width_multiplier * (1 - t * 0.3)))
            
            # Draw with alpha
            if alpha < 255:
                surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.line(surf, (*color, alpha), p1, p2, width)
                self.screen.blit(surf, (0, 0))
            else:
                pygame.draw.line(self.screen, color, p1, p2, width)
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)
    
    def _render_particles(self) -> None:
        """Render particle effects."""
        if not self.show_particles:
            return
        
        for particle in self.particle_system.get_all_particles():
            px, py, depth = self._project_vertex(particle.position)
            size = int(particle.current_size)
            
            if 0 < px < self.width and 0 < py < self.height and size > 0:
                color = (*particle.current_color, particle.current_alpha)
                surf = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (size + 1, size + 1), size)
                self.screen.blit(surf, (px - size - 1, py - size - 1))
    
    def _draw_object_list(self) -> None:
        """Draw the object list sidebar."""
        # Background
        sidebar_rect = pygame.Rect(0, 0, 320, self.height)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, sidebar_rect)
        pygame.draw.line(self.screen, Colors.BORDER, (320, 0), (320, self.height), 1)
        
        # Title
        title_surf = self.font_title.render("4D Objects", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title_surf, (20, 20))
        
        # Search and tabs
        self.search_box.draw(self.screen)
        self.category_tabs.draw(self.screen)
        
        # Object list
        list_y = 170
        visible_height = self.height - 190
        
        for i, obj in enumerate(self.filtered_objects):
            if list_y > self.height - 20:
                break
            
            item_rect = pygame.Rect(10, list_y, 300, 60)
            
            # Highlight selected
            if i == self.selected_index:
                pygame.draw.rect(self.screen, Colors.BG_ACTIVE, item_rect, border_radius=6)
                pygame.draw.rect(self.screen, obj.color, 
                               pygame.Rect(item_rect.x, item_rect.y, 3, item_rect.height),
                               border_radius=2)
            
            # Name
            name_color = Colors.TEXT_PRIMARY if i == self.selected_index else Colors.TEXT_SECONDARY
            name_surf = self.font_body.render(obj.name, True, name_color)
            self.screen.blit(name_surf, (item_rect.x + 12, item_rect.y + 8))
            
            # Description
            desc_surf = self.font_small.render(obj.description[:40] + "..." if len(obj.description) > 40 else obj.description, 
                                               True, Colors.TEXT_MUTED)
            self.screen.blit(desc_surf, (item_rect.x + 12, item_rect.y + 28))
            
            # Stats
            if obj.vertices > 0:
                stats = f"V:{obj.vertices} E:{obj.edges}"
                stats_surf = self.font_small.render(stats, True, Colors.TEXT_MUTED)
                self.screen.blit(stats_surf, (item_rect.x + 12, item_rect.y + 44))
            
            list_y += 65
    
    def _draw_info_panel(self) -> None:
        """Draw the info panel on the right."""
        if not self.filtered_objects:
            return
        
        demo = self.filtered_objects[self.selected_index]
        
        # Background
        panel_x = self.width - 300
        panel_rect = pygame.Rect(panel_x, 0, 300, self.height)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, panel_rect)
        pygame.draw.line(self.screen, Colors.BORDER, (panel_x, 0), (panel_x, self.height), 1)
        
        # Object name
        name_surf = self.font_subtitle.render(demo.name, True, demo.color)
        self.screen.blit(name_surf, (panel_x + 15, 20))
        
        # Category badge
        cat_surf = self.font_small.render(demo.category, True, Colors.TEXT_MUTED)
        self.screen.blit(cat_surf, (panel_x + 15, 48))
        
        # Toggles and sliders
        self.spin_toggle.draw(self.screen)
        self.speed_slider.draw(self.screen)
        self.scale_slider.draw(self.screen)
        self.w_slider.draw(self.screen)
        
        # Feature toggles
        self.gradient_toggle.draw(self.screen)
        self.particles_toggle.draw(self.screen)
        self.blur_toggle.draw(self.screen)
        
        # Stats panel
        stats_y = 440
        pygame.draw.line(self.screen, Colors.BORDER, (panel_x + 15, stats_y), (self.width - 15, stats_y), 1)
        
        stats_title = self.font_body.render("Geometry", True, Colors.TEXT_PRIMARY)
        self.screen.blit(stats_title, (panel_x + 15, stats_y + 10))
        
        stats_y += 40
        stats = [
            ("Vertices", demo.vertices),
            ("Edges", demo.edges),
            ("Faces", demo.faces),
            ("Cells", demo.cells),
        ]
        
        for label, value in stats:
            if value > 0:
                label_surf = self.font_small.render(label, True, Colors.TEXT_MUTED)
                value_surf = self.font_mono.render(str(value), True, Colors.TEXT_PRIMARY)
                self.screen.blit(label_surf, (panel_x + 15, stats_y))
                self.screen.blit(value_surf, (panel_x + 100, stats_y))
                stats_y += 22
        
        # Math info
        if demo.math_info:
            stats_y += 10
            pygame.draw.line(self.screen, Colors.BORDER, (panel_x + 15, stats_y), (self.width - 15, stats_y), 1)
            stats_y += 15
            
            info_title = self.font_body.render("Math", True, Colors.TEXT_PRIMARY)
            self.screen.blit(info_title, (panel_x + 15, stats_y))
            stats_y += 25
            
            # Word wrap math info
            words = demo.math_info.split()
            line = ""
            for word in words:
                test_line = line + word + " "
                if self.font_small.size(test_line)[0] < 270:
                    line = test_line
                else:
                    info_surf = self.font_small.render(line, True, Colors.TEXT_SECONDARY)
                    self.screen.blit(info_surf, (panel_x + 15, stats_y))
                    stats_y += 18
                    line = word + " "
            if line:
                info_surf = self.font_small.render(line, True, Colors.TEXT_SECONDARY)
                self.screen.blit(info_surf, (panel_x + 15, stats_y))
        
        # Buttons
        self.screenshot_btn.draw(self.screen)
        self.record_btn.draw(self.screen)
        self.morph_btn.draw(self.screen)
        self.reset_btn.draw(self.screen)
        
        # Recording indicator
        if self.is_recording:
            rec_color = (255, 80, 80) if int(pygame.time.get_ticks() / 500) % 2 else (180, 50, 50)
            pygame.draw.circle(self.screen, rec_color, (panel_x + 270, 25), 8)
            rec_text = self.font_small.render(f"REC {self.recorder.frame_count}", True, rec_color)
            self.screen.blit(rec_text, (panel_x + 200, 18))
        
        # Morph progress
        if self.morpher.is_morphing:
            progress_y = self.height - 140
            pygame.draw.rect(self.screen, Colors.BG_ACTIVE, 
                           (panel_x + 15, progress_y, 270, 20), border_radius=4)
            progress_width = int(260 * self.morpher.progress)
            pygame.draw.rect(self.screen, Colors.ACCENT_PURPLE,
                           (panel_x + 20, progress_y + 3, progress_width, 14), border_radius=3)
            morph_text = self.font_small.render(f"Morphing... {int(self.morpher.progress * 100)}%", True, Colors.TEXT_PRIMARY)
            self.screen.blit(morph_text, (panel_x + 15, progress_y - 18))
    
    def _draw_help_overlay(self) -> None:
        """Draw the help overlay."""
        if not self.show_help:
            return
        
        # Dim background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Help panel
        panel_width, panel_height = 500, 400
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        
        pygame.draw.rect(self.screen, Colors.BG_PANEL, 
                        (panel_x, panel_y, panel_width, panel_height), border_radius=12)
        pygame.draw.rect(self.screen, Colors.BORDER,
                        (panel_x, panel_y, panel_width, panel_height), width=1, border_radius=12)
        
        # Title
        title = self.font_title.render("Keyboard Shortcuts", True, Colors.TEXT_PRIMARY)
        self.screen.blit(title, (panel_x + 20, panel_y + 20))
        
        # Shortcuts
        shortcuts = [
            ("↑/↓/←/→", "Navigate objects"),
            ("Space", "Toggle auto-spin"),
            ("G", "Cycle gradient modes"),
            ("P", "Toggle particles"),
            ("B", "Toggle motion blur"),
            ("M", "Morph to next object"),
            ("F5", "Start/stop recording"),
            ("F12", "Take screenshot"),
            ("R", "Reset view"),
            ("+/-", "Adjust scale"),
            ("H", "Toggle help"),
            ("Esc", "Quit"),
        ]
        
        y = panel_y + 70
        for key, desc in shortcuts:
            key_surf = self.font_mono.render(key, True, Colors.ACCENT_BLUE)
            desc_surf = self.font_body.render(desc, True, Colors.TEXT_SECONDARY)
            self.screen.blit(key_surf, (panel_x + 30, y))
            self.screen.blit(desc_surf, (panel_x + 180, y))
            y += 28
        
        # Close hint
        hint = self.font_small.render("Press H or Esc to close", True, Colors.TEXT_MUTED)
        self.screen.blit(hint, (panel_x + panel_width // 2 - hint.get_width() // 2, panel_y + panel_height - 40))
    
    def _draw_toasts(self) -> None:
        """Draw toast notifications."""
        toast_y = self.height - 100
        for toast in self.toasts[::-1]:  # Bottom to top
            toast.draw(self.screen, (self.width // 2, toast_y))
            toast_y -= 50
    
    def _draw_status_bar(self) -> None:
        """Draw bottom status bar."""
        bar_height = 30
        bar_rect = pygame.Rect(320, self.height - bar_height, self.width - 620, bar_height)
        pygame.draw.rect(self.screen, Colors.BG_PANEL, bar_rect)
        
        # FPS
        fps = self.clock.get_fps()
        fps_surf = self.font_small.render(f"FPS: {fps:.0f}", True, Colors.TEXT_MUTED)
        self.screen.blit(fps_surf, (bar_rect.x + 10, bar_rect.y + 8))
        
        # Object count
        count_text = f"{self.selected_index + 1}/{len(self.filtered_objects)} objects"
        count_surf = self.font_small.render(count_text, True, Colors.TEXT_MUTED)
        self.screen.blit(count_surf, (bar_rect.right - count_surf.get_width() - 10, bar_rect.y + 8))
        
        # Help hint
        help_surf = self.font_small.render("Press H for help", True, Colors.TEXT_MUTED)
        self.screen.blit(help_surf, (bar_rect.centerx - help_surf.get_width() // 2, bar_rect.y + 8))
    
    def handle_events(self) -> None:
        """Process input events."""
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # UI components
            if self.search_box.handle_event(event):
                continue
            if self.category_tabs.handle_event(event):
                continue
            if self.spin_toggle.handle_event(event):
                continue
            if self.speed_slider.handle_event(event):
                continue
            if self.scale_slider.handle_event(event):
                continue
            if self.w_slider.handle_event(event):
                continue
            if self.screenshot_btn.handle_event(event):
                continue
            if self.record_btn.handle_event(event):
                continue
            if self.morph_btn.handle_event(event):
                continue
            if self.reset_btn.handle_event(event):
                continue
            if self.gradient_toggle.handle_event(event):
                continue
            if self.particles_toggle.handle_event(event):
                continue
            if self.blur_toggle.handle_event(event):
                continue
            
            # Keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_help:
                        self.show_help = False
                    else:
                        self.running = False
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_SPACE:
                    self.auto_spin = not self.auto_spin
                    self.spin_toggle.value = self.auto_spin
                elif event.key == pygame.K_r:
                    self._reset_view()
                elif event.key == pygame.K_g:
                    # Cycle gradient types
                    self.use_gradient = True
                    self.gradient_toggle.value = True
                    types = ["depth", "radial", "rainbow"]
                    idx = types.index(self.gradient_type) if self.gradient_type in types else 0
                    self.gradient_type = types[(idx + 1) % len(types)]
                    self._add_toast(f"Gradient: {self.gradient_type}", Colors.ACCENT_CYAN)
                elif event.key == pygame.K_p:
                    self.show_particles = not self.show_particles
                    self.particles_toggle.value = self.show_particles
                    self._toggle_particles(self.show_particles)
                elif event.key == pygame.K_b:
                    self.motion_blur_enabled = not self.motion_blur_enabled
                    self.blur_toggle.value = self.motion_blur_enabled
                    self._toggle_motion_blur(self.motion_blur_enabled)
                elif event.key == pygame.K_m:
                    self._start_morph()
                elif event.key == pygame.K_F5:
                    self._toggle_recording()
                elif event.key == pygame.K_F12:
                    self._take_screenshot()
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._load_object(self.selected_index - 1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._load_object(self.selected_index + 1)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._load_object(self.selected_index - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._load_object(self.selected_index + 1)
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.projection_scale = min(300, self.projection_scale + 10)
                    self.scale_slider.value = self.projection_scale
                elif event.key == pygame.K_MINUS:
                    self.projection_scale = max(50, self.projection_scale - 10)
                    self.scale_slider.value = self.projection_scale
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                    if idx < len(self.filtered_objects):
                        self._load_object(idx)
            
            # Mouse click on object list
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if 10 <= event.pos[0] <= 310 and 170 <= event.pos[1] < self.height:
                    clicked_idx = (event.pos[1] - 170) // 65
                    if 0 <= clicked_idx < len(self.filtered_objects):
                        self._load_object(clicked_idx)
            
            # Mouse wheel for scrolling
            if event.type == pygame.MOUSEWHEEL:
                mx, my = pygame.mouse.get_pos()
                if mx < 320:  # In object list
                    if event.y > 0:
                        self._load_object(self.selected_index - 1)
                    else:
                        self._load_object(self.selected_index + 1)
    
    def update(self, dt: float) -> None:
        """Update animations and object rotation."""
        mouse_pos = pygame.mouse.get_pos()
        
        # Update UI
        self.search_box.update(dt, mouse_pos)
        self.category_tabs.update(dt)
        self.spin_toggle.update(dt)
        self.speed_slider.update(dt, mouse_pos)
        self.scale_slider.update(dt, mouse_pos)
        self.w_slider.update(dt, mouse_pos)
        self.gradient_toggle.update(dt)
        self.particles_toggle.update(dt)
        self.blur_toggle.update(dt)
        self.screenshot_btn.update(dt, mouse_pos)
        self.record_btn.update(dt, mouse_pos)
        self.morph_btn.update(dt, mouse_pos)
        self.reset_btn.update(dt, mouse_pos)
        
        # Update animations
        self._transition_anim.update(dt)
        
        # Update toasts
        for toast in self.toasts:
            toast.update(dt)
        self.toasts = [t for t in self.toasts if not t.finished]
        
        # Update morphing
        if self.morpher.is_morphing:
            still_morphing = self.morpher.update(dt)
            if not still_morphing:
                # Morph complete - switch to target object
                if self.morph_target_idx is not None:
                    self.selected_index = self.morph_target_idx
                    demo = self.filtered_objects[self.selected_index]
                    self.current_object = demo.factory()
                    if hasattr(self.current_object, 'rotate'):
                        self.current_object.rotate(xy=0.35, xw=0.28, yw=0.22, zw=0.18)
                    self._add_toast(f"Now showing: {demo.name}", Colors.SUCCESS)
                self.morph_target_idx = None
        
        # Update particles
        if self.show_particles:
            self.particle_system.update(dt)
        
        # Rotate object
        if self.auto_spin and self.current_object and hasattr(self.current_object, 'rotate'):
            speed = self.spin_speed * dt
            self.current_object.rotate(
                xy=speed * 0.6,
                xw=speed * 0.4,
                yw=speed * 0.35,
                zw=speed * 0.3,
            )
    
    def render(self) -> None:
        """Render the entire UI."""
        # Background
        bg_val = int(self.bg_brightness * 255)
        self.screen.fill((bg_val, bg_val + 2, bg_val + 8))
        
        # Render 4D object
        self._render_object()
        
        # Render particles
        self._render_particles()
        
        # UI
        self._draw_object_list()
        self._draw_info_panel()
        self._draw_status_bar()
        
        # Overlays
        self._draw_help_overlay()
        self._draw_toasts()
        
        # Capture frame if recording
        if self.is_recording:
            self.recorder.capture_frame(self.screen)
        
        pygame.display.flip()
    
    def run(self) -> None:
        """Main loop."""
        last_time = pygame.time.get_ticks() / 1000.0
        
        while self.running:
            now = pygame.time.get_ticks() / 1000.0
            dt = min(now - last_time, 0.1)
            last_time = now
            
            self.handle_events()
            self.update(dt)
            self.render()
            
            self.clock.tick(60)
        
        pygame.quit()


def run_demo_menu_v2() -> None:
    """Launch the improved demo menu."""
    menu = DemoMenu()
    menu.run()


if __name__ == "__main__":
    run_demo_menu_v2()
