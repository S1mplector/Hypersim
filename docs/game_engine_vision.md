# HyperSim Game Engine Vision

High-level direction for evolving HyperSim from a visualization toolkit into a playable, cross-dimensional game engine and game.

## Pillars
- Cross-dimensional play: Start as a 1D being and ascend through 2D -> 3D -> 4D. Higher-dimensional beings can observe/influence lower dimensions.
- Shared engine core: One runtime that can downshift rendering/physics/input per dimension instead of four separate games.
- Campaign + multiplayer: Story/campaign progression plus systemic sandbox with drop-in co-op/PvP. Same content should be hostable locally or over the network.
- Extensibility: Data-driven content (levels, abilities, objectives) and plugin-friendly systems for adding new dimensions, biomes, and modes.

## Dimension Track (v1 draft)
- 1D Line World: Movement on a line; visibility limited to neighbors; puzzles around ordering/phase.
- 2D Plane: Classic top-down side; pathing, simple combat; can "fold" the 1D line.
- 3D Space: FPS/third-person traversal; volume-based puzzles; interact with 2D as holograms/overlays.
- 4D Space: Existing HyperSim strengths; perceive/manipulate lower dimensions (e.g., freeze 2D time, rotate 3D slices, spawn 4D objects that project into 3D).

## Systems to Build
- Dimension system: Descriptors for rules (movement axes, input mapping, rendering projection, physics model, available abilities) and factories that build a scene for each dimension.
- Entity/Component runtime: Lightweight ECS or entity + component bag to share logic across dimensions while swapping render/physics representations.
- Simulation loop: Layer on top of `engine.Simulation`, with frame phases (input → simulation → authority/network → render).
- Campaign/progression: Nodes (missions), unlock conditions, rewards; persistent profile; difficulty scaling by dimension.
- Multiplayer: Transport-agnostic netcode surface (authoritative host, prediction/interp hooks), session lifecycle, replication filters per dimension.
- Content data: YAML/JSON (or Python) definitions for dimensions, biomes, abilities, NPC behaviors, and objectives. Versioned and hot-reloadable.
- Tooling: Editor panes for scenes/dimensions, profiling overlays, replay/ghosts.

## Incremental Milestones
1) Scaffolding (this PR): Dimension descriptors + progression state; starter session bootstrap.
2) 1D/2D prototypes: Movement controllers, minimal enemies/goals, render in Pygame UI; persist profile between runs.
3) 3D/4D bridge: Reuse existing 4D rendering; add portals/slices between dimensions; difficulty/AI that escalates across dimensions.
4) Multiplayer slice: Deterministic simulation surface, snapshot/rollback hooks, lobby/host APIs; start with 2D/3D co-op.
5) Campaign authoring: Data-driven missions, branching unlocks, encounter scripting, save/load.

## Next Steps (suggested)
- Finalize dimension spec schema and controllers for 1D/2D movement.
- Wire a `GameSession` wrapper around `Simulation` with pluggable dimension controllers.
- Add content stubs (abilities, objectives) and a simple save file for progression.
- Introduce a minimal networking surface (loopback host + client) once single-player loops are stable.

---

# Technical Implementation Specification

## Entity Component System (ECS)

Lightweight ECS to share logic across dimensions while swapping render/physics representations.

### Core Architecture

```
hypersim/game/ecs/
├── __init__.py
├── entity.py        # Entity class with component bag
├── component.py     # Base Component, built-in components
├── system.py        # System base class and registry
└── world.py         # World container managing entities/systems
```

### Entity
```python
@dataclass
class Entity:
    id: str                              # Unique identifier (UUID or slug)
    components: Dict[Type[Component], Component]
    tags: Set[str]                       # Fast filtering ("player", "enemy", "pickup")
    active: bool = True
```

### Core Components

| Component | Purpose | Fields |
|-----------|---------|--------|
| `Transform` | Position in N-D space | `position: NDArray`, `rotation: NDArray`, `scale: float` |
| `Velocity` | Movement state | `linear: NDArray`, `angular: NDArray` |
| `Renderable` | Visual representation | `mesh_id: str`, `color: Color`, `layer: int` |
| `Collider` | Collision shape | `shape: ColliderShape`, `is_trigger: bool` |
| `Health` | Damageable entities | `current: float`, `max: float`, `invuln_timer: float` |
| `Controller` | Input-driven movement | `controller_type: str`, `speed: float`, `dimension_id: str` |
| `AIBrain` | NPC behavior | `behavior_tree: str`, `state: Dict` |
| `DimensionAnchor` | Which dimension entity exists in | `dimension_id: str`, `visible_from: List[str]` |

### Systems (execution order)

1. **InputSystem** – Poll input, update `Controller` components
2. **AISystem** – Tick behavior trees, update `Velocity`
3. **PhysicsSystem** – Apply velocity, resolve collisions
4. **DamageSystem** – Process collision triggers, apply damage
5. **AbilitySystem** – Handle ability activation/cooldowns
6. **DimensionSystem** – Cross-dimension interactions (higher dims affecting lower)
7. **RenderSystem** – Gather `Renderable` + `Transform`, dispatch to renderer

---

## Player Controller

Dimension-aware player controller that swaps input mapping and movement rules.

### Controller Types

| Dimension | Controller | Movement | View |
|-----------|------------|----------|------|
| 1D | `LineController` | Left/Right on X axis | Side view, limited visibility |
| 2D | `PlaneController` | WASD on XY plane | Top-down or side-scroller |
| 3D | `VolumeController` | WASD + Space/Ctrl, mouse look | FPS/TPS camera |
| 4D | `HyperController` | 3D controls + Q/E for W axis | 4D→3D projection |

### Input Mapping Schema
```python
@dataclass
class InputMapping:
    dimension_id: str
    move_positive: Dict[str, int]   # axis -> pygame key
    move_negative: Dict[str, int]
    actions: Dict[str, int]         # "jump", "interact", "ability1" -> key
    mouse_look: bool
    mouse_sensitivity: float
```

### Player Entity Template
```python
def create_player(dimension_id: str, spawn_pos: NDArray) -> Entity:
    return Entity(
        id="player",
        components={
            Transform: Transform(position=spawn_pos),
            Velocity: Velocity(),
            Renderable: Renderable(mesh_id=f"player_{dimension_id}"),
            Collider: Collider(shape=_player_shape(dimension_id)),
            Health: Health(current=100, max=100),
            Controller: Controller(controller_type=f"{dimension_id}_controller", speed=5.0),
            DimensionAnchor: DimensionAnchor(dimension_id=dimension_id),
        },
        tags={"player", "controllable"},
    )
```

---

## Dimension-Specific Rendering

Each dimension has a dedicated render pipeline.

### 1D Line Renderer
- **Canvas**: Horizontal strip (800×100 pixels)
- **Player**: Glowing point or short segment
- **Entities**: Points with varying brightness/size
- **Visibility**: Only neighbors within `visibility_radius` shown; fog beyond
- **UI Overlay**: Mini-map showing full line with player dot

### 2D Plane Renderer
- **Canvas**: Full window, top-down or platformer perspective
- **Sprites**: 2D shapes/textures for entities
- **Camera**: Follows player, smooth lerp
- **Layers**: Background, entities, foreground, UI
- **Effects**: Particle trails, dimension fold visualization

### 3D Volume Renderer
- **Engine**: Pygame + OpenGL or software rasterizer
- **Camera**: FPS/TPS with mouse look
- **Meshes**: 3D primitives, procedural geometry
- **Lighting**: Basic directional + point lights
- **Lower-dim overlays**: 2D planes rendered as semi-transparent billboards

### 4D Hyper Renderer (existing)
- **Projection**: 4D→3D perspective projection (existing `PygameRenderer`)
- **Slicing**: Real-time W-axis cross-sections
- **Lower-dim control**: Overlay UI showing 1D/2D/3D states

---

## Level / World Structure

### World Definition (YAML)
```yaml
world:
  id: "tutorial_1d"
  dimension: "1d"
  spawn: [0.0]
  bounds: [-50.0, 50.0]
  
entities:
  - type: "pickup"
    position: [10.0]
    params: { item: "key_alpha" }
  - type: "enemy"
    position: [25.0]
    params: { behavior: "patrol", patrol_range: 5.0 }
  - type: "portal"
    position: [45.0]
    params: { target_dimension: "2d", target_world: "tutorial_2d" }

objectives:
  - id: "collect_key"
    type: "collect"
    target: 1
    params: { item: "key_alpha" }
  - id: "reach_portal"
    type: "interact"
    params: { target: "portal" }
```

### World Loader
```python
class WorldLoader:
    def load(self, path: Path) -> Tuple[World, List[Entity], List[ObjectiveSpec]]:
        """Parse YAML, instantiate entities, return configured world."""
```

---

## Enemy / NPC System

### Behavior Trees (simplified)

```
Selector
├── Sequence [Attack]
│   ├── Condition: player_in_range(attack_range)
│   └── Action: attack_player()
├── Sequence [Chase]
│   ├── Condition: player_in_range(detect_range)
│   └── Action: move_toward_player()
└── Action: patrol()
```

### Enemy Types per Dimension

| Dimension | Enemy | Behavior |
|-----------|-------|----------|
| 1D | `Blocker` | Oscillates on line segment, damages on contact |
| 1D | `Chaser` | Moves toward player when in range |
| 2D | `Patroller` | Walks set path, attacks if player crosses |
| 2D | `Shooter` | Stationary, fires projectiles |
| 3D | `Flyer` | 3D patrol, dive-bombs player |
| 4D | `Shifter` | Phase-shifts through W, unpredictable |

---

## Ability System

### Ability Definition
```python
@dataclass
class AbilityDef:
    id: str
    name: str
    dimension_req: Optional[str]      # None = usable anywhere
    cooldown: float                   # seconds
    cost: float                       # energy/mana (0 if none)
    effect: str                       # effect function name
    params: Dict[str, Any]
```

### Built-in Abilities

| Ability | Dimension | Effect |
|---------|-----------|--------|
| `ping_neighbors` | 1D | Reveal entities within radius for 2s |
| `fold_line` | 2D+ | Teleport a 1D entity to new position |
| `sketch_path` | 2D | Draw temporary wall/path |
| `slice_plane` | 3D+ | View cross-section of 3D at chosen Z |
| `carry_line` | 3D+ | Pick up 1D entity and reposition |
| `rotate_hyperplanes` | 4D | Rotate 4D object's projection into 3D |
| `spawn_slices` | 4D | Spawn 3D cross-sections as physical objects |
| `stabilize_lower` | 4D | Freeze time in a lower dimension |

---

## Game Loop Integration

```python
class GameLoop:
    def __init__(self, session: GameSession, renderer: DimensionRenderer):
        self.session = session
        self.renderer = renderer
        self.world = World()
        self.input_handler = InputHandler()
        self.systems = [
            InputSystem(self.input_handler),
            AISystem(),
            PhysicsSystem(),
            DamageSystem(),
            AbilitySystem(session.abilities),
            DimensionSystem(session),
            RenderSystem(self.renderer),
        ]
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            
            # Input phase
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                self.input_handler.process(event)
            
            # Update phase
            for system in self.systems:
                system.update(self.world, dt)
            
            # Event recording for objectives
            for event in self.world.drain_events():
                self.session.record_event(event.type, **event.data)
            
            # Render phase
            self.renderer.render(self.world, self.session.active_dimension)
            pygame.display.flip()
```

---

## File Structure (target)

```
hypersim/game/
├── __init__.py
├── abilities.py          # (existing)
├── dimensions.py         # (existing)
├── objectives.py         # (existing)
├── progression.py        # (existing)
├── save.py              # (existing)
├── session.py           # (existing)
├── ecs/
│   ├── __init__.py
│   ├── entity.py
│   ├── component.py
│   ├── system.py
│   └── world.py
├── controllers/
│   ├── __init__.py
│   ├── base.py
│   ├── line_controller.py
│   ├── plane_controller.py
│   ├── volume_controller.py
│   └── hyper_controller.py
├── enemies/
│   ├── __init__.py
│   ├── behaviors.py
│   └── spawner.py
├── rendering/
│   ├── __init__.py
│   ├── dimension_renderer.py
│   ├── line_renderer.py
│   ├── plane_renderer.py
│   └── volume_renderer.py
├── content/
│   ├── abilities.yaml
│   ├── enemies.yaml
│   └── worlds/
│       ├── tutorial_1d.yaml
│       ├── tutorial_2d.yaml
│       └── ...
└── loop.py              # Main game loop
```

---

## Implementation Priority

### Phase 1: Core Runtime (Current Sprint)
1. ✅ Dimension specs, progression, campaign nodes, objectives
2. 🔲 ECS foundation (`Entity`, `Component`, `World`)
3. 🔲 Core components (`Transform`, `Velocity`, `Controller`, `DimensionAnchor`)
4. 🔲 Input system + 1D controller
5. 🔲 1D line renderer (Pygame)

### Phase 2: 1D Playable Slice
6. 🔲 Player entity spawning
7. 🔲 1D enemy (Blocker)
8. 🔲 Collision detection (1D segment overlap)
9. 🔲 Health/damage system
10. 🔲 First playable 1D level with portal to 2D

### Phase 3: 2D Expansion
11. 🔲 2D plane renderer
12. 🔲 Plane controller
13. 🔲 2D enemies (Patroller, Shooter)
14. 🔲 2D collision (AABB / circle)
15. 🔲 Abilities: `fold_line`, `sketch_path`

### Phase 4: 3D/4D Bridge
16. 🔲 Wire existing 4D renderer into game loop
17. 🔲 Volume controller (FPS camera)
18. 🔲 Cross-dimension portals and observation
19. 🔲 Higher-dimension abilities affecting lower worlds

### Phase 5: Polish & Content
20. 🔲 Campaign mission graph (10+ missions)
21. 🔲 Audio system (sfx, ambient)
22. 🔲 Settings/options menu
23. 🔲 Multiplayer foundation (local first)
