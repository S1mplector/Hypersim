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
