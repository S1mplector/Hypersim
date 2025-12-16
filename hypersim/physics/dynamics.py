"""4D Rigid body dynamics simulation.

Provides physics simulation for 4D objects including forces,
velocities, and collision response.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hypersim.core.shape_4d import Shape4D

from .collision import CollisionDetector, CollisionInfo, BoundingHypersphere


@dataclass
class RigidBody4D:
    """A rigid body in 4D space.
    
    Handles physics simulation for a 4D object including
    linear and angular motion.
    """
    
    shape: "Shape4D"
    mass: float = 1.0
    
    # Linear motion
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=np.float32))
    acceleration: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=np.float32))
    
    # Angular motion (6 rotation planes in 4D: xy, xz, xw, yz, yw, zw)
    angular_velocity: Dict[str, float] = field(default_factory=lambda: {
        'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0
    })
    angular_acceleration: Dict[str, float] = field(default_factory=lambda: {
        'xy': 0.0, 'xz': 0.0, 'xw': 0.0, 'yz': 0.0, 'yw': 0.0, 'zw': 0.0
    })
    
    # Physical properties
    restitution: float = 0.5  # Bounciness (0-1)
    friction: float = 0.3
    drag: float = 0.01  # Linear drag
    angular_drag: float = 0.02  # Angular drag
    
    # Flags
    is_static: bool = False  # Static objects don't move
    is_kinematic: bool = False  # Kinematic objects move but aren't affected by physics
    use_gravity: bool = True
    
    def __post_init__(self):
        self.velocity = np.array(self.velocity, dtype=np.float32)
        self.acceleration = np.array(self.acceleration, dtype=np.float32)
        self._force_accumulator = np.zeros(4, dtype=np.float32)
        self._torque_accumulator = {k: 0.0 for k in self.angular_velocity}
    
    @property
    def position(self) -> np.ndarray:
        """Get current position."""
        return np.array(self.shape.position, dtype=np.float32)
    
    @position.setter
    def position(self, value: np.ndarray) -> None:
        """Set position."""
        self.shape.set_position(value)
    
    @property
    def inverse_mass(self) -> float:
        """Get inverse mass (0 for infinite mass / static objects)."""
        if self.is_static or self.mass <= 0:
            return 0.0
        return 1.0 / self.mass
    
    def apply_force(self, force: np.ndarray) -> None:
        """Apply a force to the body's center of mass."""
        if not self.is_static and not self.is_kinematic:
            self._force_accumulator += force
    
    def apply_impulse(self, impulse: np.ndarray) -> None:
        """Apply an instantaneous impulse."""
        if not self.is_static and not self.is_kinematic:
            self.velocity += impulse * self.inverse_mass
    
    def apply_torque(self, plane: str, torque: float) -> None:
        """Apply torque in a rotation plane."""
        if plane in self._torque_accumulator:
            self._torque_accumulator[plane] += torque
    
    def integrate(self, dt: float) -> None:
        """Integrate physics for one time step.
        
        Args:
            dt: Time step in seconds
        """
        if self.is_static:
            return
        
        # Linear motion
        if not self.is_kinematic:
            # Apply accumulated forces
            self.acceleration = self._force_accumulator * self.inverse_mass
            
            # Update velocity
            self.velocity += self.acceleration * dt
            
            # Apply drag
            self.velocity *= (1 - self.drag)
        
        # Update position
        new_pos = self.position + self.velocity * dt
        self.position = new_pos
        
        # Angular motion
        if not self.is_kinematic:
            for plane in self.angular_velocity:
                # Apply accumulated torques
                self.angular_acceleration[plane] = self._torque_accumulator[plane] / self.mass
                
                # Update angular velocity
                self.angular_velocity[plane] += self.angular_acceleration[plane] * dt
                
                # Apply angular drag
                self.angular_velocity[plane] *= (1 - self.angular_drag)
        
        # Apply rotation
        if hasattr(self.shape, 'rotate'):
            rotation_delta = {k: v * dt for k, v in self.angular_velocity.items()}
            self.shape.rotate(**rotation_delta)
        
        # Clear accumulators
        self._force_accumulator.fill(0)
        self._torque_accumulator = {k: 0.0 for k in self.angular_velocity}
    
    def get_kinetic_energy(self) -> float:
        """Calculate kinetic energy."""
        linear = 0.5 * self.mass * np.dot(self.velocity, self.velocity)
        angular = 0.5 * self.mass * sum(v**2 for v in self.angular_velocity.values())
        return linear + angular


class Force(ABC):
    """Abstract base class for forces."""
    
    @abstractmethod
    def apply(self, body: RigidBody4D, dt: float) -> None:
        """Apply the force to a body."""
        pass


@dataclass
class Gravity4D(Force):
    """4D gravity force."""
    
    direction: np.ndarray = field(default_factory=lambda: np.array([0, -1, 0, 0], dtype=np.float32))
    strength: float = 9.81
    
    def apply(self, body: RigidBody4D, dt: float) -> None:
        if body.use_gravity and not body.is_static:
            force = self.direction * self.strength * body.mass
            body.apply_force(force)


@dataclass
class Spring4D(Force):
    """4D spring force between two bodies."""
    
    body_a: RigidBody4D
    body_b: RigidBody4D
    rest_length: float = 1.0
    stiffness: float = 10.0
    damping: float = 0.5
    
    def apply(self, body: RigidBody4D, dt: float) -> None:
        if body not in (self.body_a, self.body_b):
            return
        
        # Calculate spring vector
        diff = self.body_b.position - self.body_a.position
        distance = np.linalg.norm(diff)
        
        if distance < 0.0001:
            return
        
        # Normalize
        direction = diff / distance
        
        # Spring force (Hooke's law)
        extension = distance - self.rest_length
        spring_force = direction * extension * self.stiffness
        
        # Damping force
        relative_velocity = self.body_b.velocity - self.body_a.velocity
        damping_force = direction * np.dot(relative_velocity, direction) * self.damping
        
        # Total force
        total_force = spring_force + damping_force
        
        # Apply to bodies
        self.body_a.apply_force(total_force)
        self.body_b.apply_force(-total_force)


@dataclass
class AttractorForce(Force):
    """Attractive/repulsive force toward a point."""
    
    position: np.ndarray
    strength: float = 1.0
    falloff: float = 2.0  # Distance falloff exponent
    
    def apply(self, body: RigidBody4D, dt: float) -> None:
        if body.is_static:
            return
        
        diff = self.position - body.position
        distance = np.linalg.norm(diff)
        
        if distance < 0.01:
            return
        
        direction = diff / distance
        magnitude = self.strength / (distance ** self.falloff)
        
        body.apply_force(direction * magnitude * body.mass)


class PhysicsWorld:
    """Manages physics simulation for multiple bodies."""
    
    def __init__(self):
        self.bodies: List[RigidBody4D] = []
        self.forces: List[Force] = []
        self.collision_detector = CollisionDetector()
        
        # World settings
        self.gravity = Gravity4D()
        self.time_scale: float = 1.0
        self.substeps: int = 4
    
    def add_body(self, body: RigidBody4D) -> None:
        """Add a rigid body to the world."""
        self.bodies.append(body)
        self.collision_detector.add_object(body.shape)
    
    def remove_body(self, body: RigidBody4D) -> None:
        """Remove a body from the world."""
        if body in self.bodies:
            idx = self.bodies.index(body)
            self.bodies.remove(body)
            self.collision_detector.remove_object(idx)
    
    def add_force(self, force: Force) -> None:
        """Add a global force."""
        self.forces.append(force)
    
    def remove_force(self, force: Force) -> None:
        """Remove a force."""
        if force in self.forces:
            self.forces.remove(force)
    
    def step(self, dt: float) -> List[CollisionInfo]:
        """Advance simulation by dt seconds.
        
        Args:
            dt: Time step
            
        Returns:
            List of collisions that occurred
        """
        dt *= self.time_scale
        sub_dt = dt / self.substeps
        
        all_collisions = []
        
        for _ in range(self.substeps):
            # Apply forces
            for body in self.bodies:
                # Gravity
                self.gravity.apply(body, sub_dt)
                
                # Other forces
                for force in self.forces:
                    force.apply(body, sub_dt)
            
            # Integrate
            for body in self.bodies:
                body.integrate(sub_dt)
            
            # Update collision bounds
            self.collision_detector.update_bounds()
            
            # Detect and resolve collisions
            collisions = self.collision_detector.detect_collisions()
            self._resolve_collisions(collisions)
            all_collisions.extend(collisions)
        
        return all_collisions
    
    def _resolve_collisions(self, collisions: List[CollisionInfo]) -> None:
        """Resolve collision responses."""
        for info in collisions:
            if info.object_a is None or info.object_b is None:
                continue
            
            # Find corresponding bodies
            body_a = None
            body_b = None
            for body in self.bodies:
                if body.shape is info.object_a:
                    body_a = body
                if body.shape is info.object_b:
                    body_b = body
            
            if body_a is None or body_b is None:
                continue
            
            # Skip if both static
            if body_a.is_static and body_b.is_static:
                continue
            
            self._resolve_collision_pair(body_a, body_b, info)
    
    def _resolve_collision_pair(
        self,
        body_a: RigidBody4D,
        body_b: RigidBody4D,
        info: CollisionInfo,
    ) -> None:
        """Resolve collision between two bodies."""
        # Relative velocity
        rel_vel = body_b.velocity - body_a.velocity
        vel_along_normal = np.dot(rel_vel, info.normal)
        
        # Don't resolve if velocities are separating
        if vel_along_normal > 0:
            return
        
        # Calculate restitution
        e = min(body_a.restitution, body_b.restitution)
        
        # Calculate impulse magnitude
        inv_mass_sum = body_a.inverse_mass + body_b.inverse_mass
        if inv_mass_sum == 0:
            return
        
        j = -(1 + e) * vel_along_normal / inv_mass_sum
        
        # Apply impulse
        impulse = info.normal * j
        body_a.apply_impulse(-impulse)
        body_b.apply_impulse(impulse)
        
        # Position correction (prevent sinking)
        percent = 0.2  # Penetration percentage to correct
        slop = 0.01  # Allowable penetration
        correction = info.normal * max(info.depth - slop, 0) * percent / inv_mass_sum
        
        if not body_a.is_static:
            body_a.position = body_a.position - correction * body_a.inverse_mass
        if not body_b.is_static:
            body_b.position = body_b.position + correction * body_b.inverse_mass
    
    def get_total_energy(self) -> float:
        """Calculate total kinetic energy in the system."""
        return sum(body.get_kinetic_energy() for body in self.bodies)
    
    def clear(self) -> None:
        """Remove all bodies and forces."""
        self.bodies.clear()
        self.forces.clear()
        self.collision_detector = CollisionDetector()
