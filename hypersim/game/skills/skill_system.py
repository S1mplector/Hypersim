"""Core skill system for 4D shape combat."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
import time

import numpy as np

if TYPE_CHECKING:
    from hypersim.game.ecs.entity import Entity
    from hypersim.game.ecs.world import World


class SkillType(Enum):
    """Categories of skills."""
    ATTACK = "attack"           # Damage dealing
    DEFENSE = "defense"         # Damage reduction/blocking
    MOVEMENT = "movement"       # Mobility skills
    MANIPULATION = "manipulation"  # Alter space/enemies
    UTILITY = "utility"         # Buffs, vision, etc.
    ULTIMATE = "ultimate"       # Powerful, long cooldown


class SkillTarget(Enum):
    """What a skill can target."""
    SELF = "self"
    SINGLE_ENEMY = "single_enemy"
    ALL_ENEMIES = "all_enemies"
    AREA = "area"
    DIRECTION = "direction"
    DIMENSION = "dimension"     # Affects entire dimension slice


class SkillEffect(Enum):
    """Types of effects skills can apply."""
    DAMAGE = "damage"
    HEAL = "heal"
    SHIELD = "shield"
    STUN = "stun"
    SLOW = "slow"
    KNOCKBACK = "knockback"
    TELEPORT = "teleport"
    PHASE = "phase"             # Pass through objects
    ROTATE = "rotate"           # 4D rotation
    SLICE = "slice"             # Dimensional slice
    FOLD = "fold"               # Fold space
    INVERT = "invert"           # Invert inside/out
    DUPLICATE = "duplicate"     # Create copy
    ABSORB = "absorb"           # Absorb enemy properties


@dataclass
class Skill:
    """Definition of a skill."""
    id: str
    name: str
    description: str
    skill_type: SkillType
    target: SkillTarget
    
    # Costs and cooldowns
    cooldown: float = 5.0       # Seconds
    energy_cost: float = 0.0    # If energy system exists
    
    # Effects
    effects: List[SkillEffect] = field(default_factory=list)
    damage: float = 0.0
    heal: float = 0.0
    duration: float = 0.0       # For buffs/debuffs
    
    # Range and area
    range: float = 10.0
    area_radius: float = 0.0    # 0 = single target
    
    # Requirements
    requires_shape: Optional[str] = None
    requires_family: Optional[str] = None
    min_vertices: int = 0
    
    # Visual/Audio
    color: tuple = (255, 255, 255)
    particle_effect: Optional[str] = None
    sound_effect: Optional[str] = None
    
    # Mathematical basis
    math_basis: str = ""        # Explanation of 4D math behind skill


@dataclass
class SkillInstance:
    """Runtime state of a skill for an entity."""
    skill: Skill
    last_used: float = 0.0
    level: int = 1
    
    @property
    def is_ready(self) -> bool:
        return time.time() - self.last_used >= self.skill.cooldown
    
    @property
    def remaining_cooldown(self) -> float:
        elapsed = time.time() - self.last_used
        return max(0, self.skill.cooldown - elapsed)
    
    def use(self) -> bool:
        """Attempt to use the skill. Returns True if successful."""
        if not self.is_ready:
            return False
        self.last_used = time.time()
        return True
    
    def get_damage(self) -> float:
        """Get damage scaled by level."""
        return self.skill.damage * (1 + (self.level - 1) * 0.15)


class SkillSystem:
    """Manages skills for all entities."""
    
    def __init__(self):
        self._entity_skills: Dict[str, Dict[str, SkillInstance]] = {}
        self._skill_definitions: Dict[str, Skill] = {}
        self._effect_handlers: Dict[SkillEffect, Callable] = {}
        
        self._setup_effect_handlers()
    
    def _setup_effect_handlers(self) -> None:
        """Set up handlers for each effect type."""
        self._effect_handlers = {
            SkillEffect.DAMAGE: self._apply_damage,
            SkillEffect.HEAL: self._apply_heal,
            SkillEffect.SHIELD: self._apply_shield,
            SkillEffect.STUN: self._apply_stun,
            SkillEffect.KNOCKBACK: self._apply_knockback,
            SkillEffect.TELEPORT: self._apply_teleport,
            SkillEffect.PHASE: self._apply_phase,
            SkillEffect.ROTATE: self._apply_rotate,
            SkillEffect.SLICE: self._apply_slice,
            SkillEffect.FOLD: self._apply_fold,
        }
    
    def register_skill(self, skill: Skill) -> None:
        """Register a skill definition."""
        self._skill_definitions[skill.id] = skill
    
    def grant_skill(self, entity_id: str, skill_id: str, level: int = 1) -> bool:
        """Grant a skill to an entity."""
        skill = self._skill_definitions.get(skill_id)
        if not skill:
            return False
        
        if entity_id not in self._entity_skills:
            self._entity_skills[entity_id] = {}
        
        self._entity_skills[entity_id][skill_id] = SkillInstance(
            skill=skill,
            level=level
        )
        return True
    
    def get_skills(self, entity_id: str) -> List[SkillInstance]:
        """Get all skills for an entity."""
        return list(self._entity_skills.get(entity_id, {}).values())
    
    def get_skill(self, entity_id: str, skill_id: str) -> Optional[SkillInstance]:
        """Get a specific skill for an entity."""
        return self._entity_skills.get(entity_id, {}).get(skill_id)
    
    def use_skill(
        self,
        world: "World",
        caster_id: str,
        skill_id: str,
        target_pos: Optional[np.ndarray] = None,
        target_entity_id: Optional[str] = None,
    ) -> bool:
        """Use a skill. Returns True if successful."""
        instance = self.get_skill(caster_id, skill_id)
        if not instance or not instance.use():
            return False
        
        skill = instance.skill
        caster = world.get(caster_id)
        if not caster:
            return False
        
        # Find targets
        targets = self._find_targets(
            world, caster, skill, target_pos, target_entity_id
        )
        
        # Apply effects to each target
        for target in targets:
            for effect in skill.effects:
                handler = self._effect_handlers.get(effect)
                if handler:
                    handler(world, caster, target, instance)
        
        # Emit event
        world.emit("skill_used", 
            caster_id=caster_id,
            skill_id=skill_id,
            targets=[t.id for t in targets]
        )
        
        return True
    
    def _find_targets(
        self,
        world: "World",
        caster: "Entity",
        skill: Skill,
        target_pos: Optional[np.ndarray],
        target_entity_id: Optional[str],
    ) -> List["Entity"]:
        """Find valid targets for a skill."""
        from hypersim.game.ecs.component import Transform
        
        targets = []
        caster_transform = caster.get(Transform)
        if not caster_transform:
            return targets
        
        if skill.target == SkillTarget.SELF:
            return [caster]
        
        if skill.target == SkillTarget.SINGLE_ENEMY and target_entity_id:
            target = world.get(target_entity_id)
            if target and target.has_tag("enemy"):
                targets.append(target)
        
        elif skill.target in (SkillTarget.ALL_ENEMIES, SkillTarget.AREA):
            center = target_pos if target_pos is not None else caster_transform.position
            
            for entity in world.entities.values():
                if entity.id == caster.id:
                    continue
                if skill.target == SkillTarget.ALL_ENEMIES and not entity.has_tag("enemy"):
                    continue
                
                entity_transform = entity.get(Transform)
                if not entity_transform:
                    continue
                
                dist = np.linalg.norm(entity_transform.position - center)
                
                if skill.area_radius > 0:
                    if dist <= skill.area_radius:
                        targets.append(entity)
                elif dist <= skill.range:
                    targets.append(entity)
        
        return targets
    
    # === EFFECT HANDLERS ===
    
    def _apply_damage(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply damage effect."""
        from hypersim.game.ecs.component import Health
        
        health = target.get(Health)
        if health:
            damage = instance.get_damage()
            health.current = max(0, health.current - damage)
            world.emit("damage_dealt", 
                source=caster.id, 
                target=target.id, 
                amount=damage
            )
    
    def _apply_heal(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply healing effect."""
        from hypersim.game.ecs.component import Health
        
        health = target.get(Health)
        if health:
            heal = instance.skill.heal * (1 + (instance.level - 1) * 0.1)
            health.current = min(health.max, health.current + heal)
    
    def _apply_shield(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply shield effect."""
        # Would add a Shield component or buff
        world.emit("shield_applied", 
            target=target.id,
            amount=instance.skill.damage,  # Shield amount
            duration=instance.skill.duration
        )
    
    def _apply_stun(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply stun effect."""
        from hypersim.game.ecs.component import AIBrain
        
        brain = target.get(AIBrain)
        if brain:
            brain.state["stunned"] = True
            brain.state["stun_end"] = time.time() + instance.skill.duration
    
    def _apply_knockback(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply knockback effect."""
        from hypersim.game.ecs.component import Transform, Velocity
        
        caster_t = caster.get(Transform)
        target_t = target.get(Transform)
        target_v = target.get(Velocity)
        
        if caster_t and target_t and target_v:
            direction = target_t.position - caster_t.position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction = direction / norm
                knockback_force = 20.0 * instance.level
                target_v.linear += direction * knockback_force
    
    def _apply_teleport(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply teleport effect."""
        from hypersim.game.ecs.component import Transform
        
        # Teleport target a short distance in random direction
        transform = target.get(Transform)
        if transform:
            offset = np.random.randn(4) * instance.skill.range * 0.5
            transform.position += offset
    
    def _apply_phase(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply phase (intangibility) effect."""
        from hypersim.game.ecs.component import Collider
        
        collider = target.get(Collider)
        if collider:
            collider.is_trigger = True
            # Would need to track when to restore
    
    def _apply_rotate(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply 4D rotation to target."""
        from hypersim.game.ecs.component import Transform
        
        transform = target.get(Transform)
        if transform:
            # Apply XW rotation (4D specific!)
            angle = 0.5 * instance.level
            x, w = transform.position[0], transform.position[3]
            transform.position[0] = x * np.cos(angle) - w * np.sin(angle)
            transform.position[3] = x * np.sin(angle) + w * np.cos(angle)
    
    def _apply_slice(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Apply dimensional slice - damage based on W position."""
        from hypersim.game.ecs.component import Transform, Health
        
        transform = target.get(Transform)
        health = target.get(Health)
        
        if transform and health:
            # More damage the further from W=0
            w_factor = abs(transform.position[3])
            damage = instance.get_damage() * (1 + w_factor)
            health.current = max(0, health.current - damage)
    
    def _apply_fold(
        self,
        world: "World",
        caster: "Entity",
        target: "Entity",
        instance: SkillInstance
    ) -> None:
        """Fold space to bring target closer."""
        from hypersim.game.ecs.component import Transform
        
        caster_t = caster.get(Transform)
        target_t = target.get(Transform)
        
        if caster_t and target_t:
            # Move target 50% closer
            direction = caster_t.position - target_t.position
            target_t.position += direction * 0.5


# Global instance
_skill_system: Optional[SkillSystem] = None

def get_skill_system() -> SkillSystem:
    """Get the global skill system instance."""
    global _skill_system
    if _skill_system is None:
        _skill_system = SkillSystem()
    return _skill_system
