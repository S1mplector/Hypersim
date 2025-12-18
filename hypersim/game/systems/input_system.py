"""Input system - processes player input and updates controllers."""
from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

from hypersim.game.ecs.system import System
from hypersim.game.ecs.component import Controller, Velocity, Transform
from hypersim.game.controllers.base import InputHandler, BaseController
from hypersim.game.controllers.line_controller import LineController
from hypersim.game.controllers.plane_controller import PlaneController

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World
    from hypersim.game.ecs.entity import Entity


class InputSystem(System):
    """System that processes input and updates entity velocities."""
    
    priority = 0  # Run first
    required_components = (Controller, Velocity)
    
    def __init__(self, input_handler: InputHandler):
        self.input_handler = input_handler
        self._controllers: Dict[str, BaseController] = {
            "line": LineController(),
            "1d": LineController(),
            "plane": PlaneController(),
            "2d": PlaneController(),
        }
        self._active_dimension: str = "1d"
    
    def set_dimension(self, dimension_id: str) -> None:
        """Set the active dimension for input mapping."""
        self._active_dimension = dimension_id
    
    def get_controller(self, controller_type: str) -> Optional[BaseController]:
        """Get controller by type."""
        return self._controllers.get(controller_type)
    
    def register_controller(self, controller_type: str, controller: BaseController) -> None:
        """Register a custom controller."""
        self._controllers[controller_type] = controller
    
    def update(self, world: "World", dt: float) -> None:
        """Process input for all controllable entities."""
        for entity in self.query(world):
            controller_comp = entity.get(Controller)
            velocity = entity.get(Velocity)
            
            if not controller_comp.enabled:
                continue
            
            # Get the appropriate controller
            ctrl = self._controllers.get(controller_comp.controller_type)
            if not ctrl:
                continue
            
            # Compute movement from input
            movement = ctrl.compute_movement(self.input_handler)
            controller_comp.input_vector = movement
            
            # Apply to velocity (scaled by speed)
            velocity.linear[:len(movement)] = movement[:len(velocity.linear)] * controller_comp.speed
            
            # Check for action inputs
            self._process_actions(entity, ctrl, world)
    
    def _process_actions(self, entity: "Entity", ctrl: BaseController, world: "World") -> None:
        """Process action button presses."""
        if ctrl.get_action("interact", self.input_handler):
            world.emit("player_interact", source_entity_id=entity.id)
        
        if ctrl.get_action("ability1", self.input_handler):
            world.emit("ability_use", source_entity_id=entity.id, ability_slot=1)
        
        if ctrl.get_action("ability2", self.input_handler):
            world.emit("ability_use", source_entity_id=entity.id, ability_slot=2)
