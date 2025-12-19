"""4D Shape-based skill system for HyperSim.

Skills are derived from actual 4D mathematical properties:
- Symmetry → Defensive abilities
- Vertex count → Attack multipliers
- Cell structure → Special effects
- Rotations → Movement abilities
- Duality → Counter abilities
- Topology → Unique manipulations
"""

from .skill_system import (
    Skill, SkillType, SkillTarget, SkillEffect,
    SkillInstance, SkillSystem, get_skill_system
)
from .shape_skills import (
    SHAPE_SKILLS, get_skills_for_shape, get_skill_by_id
)
from .math_advantages import (
    ShapeAdvantage, calculate_advantage, SHAPE_MATCHUPS
)

__all__ = [
    # Core
    "Skill",
    "SkillType",
    "SkillTarget",
    "SkillEffect",
    "SkillInstance",
    "SkillSystem",
    "get_skill_system",
    # Shape skills
    "SHAPE_SKILLS",
    "get_skills_for_shape",
    "get_skill_by_id",
    # Advantages
    "ShapeAdvantage",
    "calculate_advantage",
    "SHAPE_MATCHUPS",
]
