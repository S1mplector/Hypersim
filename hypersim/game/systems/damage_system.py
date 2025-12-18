"""Damage system - processes collision damage and health updates."""
from __future__ import annotations

from typing import TYPE_CHECKING

from hypersim.game.ecs.system import System
from hypersim.game.ecs.component import Health

if TYPE_CHECKING:
    from hypersim.game.ecs.world import World


class DamageSystem(System):
    """Processes damage from collisions and updates health."""
    
    priority = 40  # After collision
    required_components = (Health,)
    
    def __init__(self):
        self._pending_damage: dict[str, float] = {}  # entity_id -> damage
    
    def queue_damage(self, entity_id: str, amount: float) -> None:
        """Queue damage to be applied this frame."""
        if entity_id in self._pending_damage:
            self._pending_damage[entity_id] += amount
        else:
            self._pending_damage[entity_id] = amount
    
    def update(self, world: "World", dt: float) -> None:
        """Update health timers and apply queued damage."""
        # Update invulnerability timers
        for entity in self.query(world):
            health = entity.get(Health)
            health.tick(dt)
        
        # Apply queued damage
        for entity_id, damage in self._pending_damage.items():
            entity = world.get(entity_id)
            if not entity:
                continue
            
            health = entity.get(Health)
            if not health:
                continue
            
            actual_damage = health.take_damage(damage)
            if actual_damage > 0:
                world.emit("damage_taken", entity_id=entity_id, amount=actual_damage)
                
                if not health.is_alive:
                    world.emit("entity_died", entity_id=entity_id)
                    
                    # Handle death based on entity type
                    if entity.has_tag("player"):
                        world.emit("player_died", entity_id=entity_id)
                    elif entity.has_tag("enemy"):
                        world.emit("defeat", tag="enemy", count=1)
                        entity.active = False
        
        self._pending_damage.clear()
