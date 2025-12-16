"""4D Physics simulation module.

Provides physics simulation capabilities for 4D objects including:
- Collision detection
- Rigid body dynamics
- Particle systems
"""

from .collision import (
    BoundingHypersphere,
    BoundingHyperbox,
    CollisionDetector,
    CollisionInfo,
    check_sphere_sphere,
    check_box_box,
)
from .dynamics import (
    RigidBody4D,
    PhysicsWorld,
    Force,
    Gravity4D,
    Spring4D,
)
from .particles import (
    Particle4D,
    ParticleEmitter,
    ParticleSystem,
    ParticleConfig,
)

__all__ = [
    # Collision
    "BoundingHypersphere",
    "BoundingHyperbox",
    "CollisionDetector",
    "CollisionInfo",
    "check_sphere_sphere",
    "check_box_box",
    # Dynamics
    "RigidBody4D",
    "PhysicsWorld",
    "Force",
    "Gravity4D",
    "Spring4D",
    # Particles
    "Particle4D",
    "ParticleEmitter",
    "ParticleSystem",
    "ParticleConfig",
]
