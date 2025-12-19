"""Core combat system data structures and mechanics."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable

import numpy as np


class CombatPhase(Enum):
    """Phases of combat turn."""
    INTRO = auto()           # Enemy appears, intro text
    PLAYER_MENU = auto()     # Player chooses action
    PLAYER_FIGHT = auto()    # Player attack timing minigame
    PLAYER_ACT = auto()      # Player ACT submenu
    PLAYER_ITEM = auto()     # Player item submenu
    PLAYER_MERCY = auto()    # Player mercy submenu
    ENEMY_DIALOGUE = auto()  # Enemy response/dialogue
    ENEMY_ATTACK = auto()    # Bullet hell dodge phase
    RESOLUTION = auto()      # Check win/lose/spare conditions
    VICTORY = auto()         # Player wins
    DEFEAT = auto()          # Player loses
    SPARE = auto()           # Enemy spared
    FLEE = auto()            # Player fled


class CombatResult(Enum):
    """Result of combat encounter."""
    ONGOING = auto()
    VICTORY = auto()      # Enemy HP reached 0
    SPARE = auto()        # Enemy was spared
    DEFEAT = auto()       # Player HP reached 0
    FLEE = auto()         # Player escaped
    SPECIAL = auto()      # Special ending (story events)


class SoulMode(Enum):
    """Soul modes affect movement in the battle box."""
    RED = "red"           # Normal - free movement
    BLUE = "blue"         # Gravity - affected by gravity, can jump
    ORANGE = "orange"     # Must keep moving or take damage
    CYAN = "cyan"         # Must stay still to avoid damage
    GREEN = "green"       # Shield mode - can block but not move freely
    PURPLE = "purple"     # Rail mode - moves on set paths
    YELLOW = "yellow"     # Shooter mode - can shoot projectiles


@dataclass
class CombatStats:
    """Combat statistics for player or enemy."""
    hp: int = 20
    max_hp: int = 20
    attack: int = 10
    defense: int = 10
    speed: float = 1.0
    
    # Combat-specific
    invincibility_frames: int = 0
    karma: int = 0  # Poison damage over time
    
    @property
    def hp_ratio(self) -> float:
        return self.hp / self.max_hp if self.max_hp > 0 else 0
    
    @property
    def is_alive(self) -> bool:
        return self.hp > 0
    
    def take_damage(self, amount: int, ignore_defense: bool = False) -> int:
        """Apply damage. Returns actual damage taken."""
        if self.invincibility_frames > 0:
            return 0
        
        actual = amount
        if not ignore_defense:
            actual = max(1, amount - self.defense)
        
        actual = min(actual, self.hp)
        self.hp -= actual
        return actual
    
    def heal(self, amount: int) -> int:
        """Heal HP. Returns actual healing."""
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual


class CombatAction(Enum):
    """Player combat actions."""
    FIGHT = auto()
    ACT = auto()
    ITEM = auto()
    MERCY = auto()


@dataclass
class PlayerSoul:
    """The player's soul in the battle box."""
    x: float = 0.0
    y: float = 0.0
    
    # Movement
    speed: float = 200.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    
    # Soul mode
    mode: SoulMode = SoulMode.RED
    
    # Blue soul physics
    grounded: bool = False
    jump_power: float = 400.0
    gravity: float = 800.0
    
    # Green soul shield
    shield_angle: float = 0.0  # Direction shield faces
    
    # Yellow soul shooting
    can_shoot: bool = False
    shoot_cooldown: float = 0.0
    
    # Collision
    radius: float = 8.0
    
    # State
    invincible: bool = False
    invincible_timer: float = 0.0
    invincible_duration: float = 1.0
    
    def update(self, dt: float, input_x: float, input_y: float, 
               box_bounds: Tuple[float, float, float, float]) -> None:
        """Update soul position based on mode and input."""
        min_x, min_y, max_x, max_y = box_bounds
        
        # Update invincibility
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Shooting cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        if self.mode == SoulMode.RED:
            # Free movement
            self.x += input_x * self.speed * dt
            self.y += input_y * self.speed * dt
        
        elif self.mode == SoulMode.BLUE:
            # Gravity mode
            self.velocity_x = input_x * self.speed
            self.velocity_y += self.gravity * dt
            
            # Jump
            if input_y < 0 and self.grounded:
                self.velocity_y = -self.jump_power
                self.grounded = False
            
            self.x += self.velocity_x * dt
            self.y += self.velocity_y * dt
            
            # Ground check
            if self.y >= max_y - self.radius:
                self.y = max_y - self.radius
                self.velocity_y = 0
                self.grounded = True
        
        elif self.mode == SoulMode.GREEN:
            # Shield mode - rotate shield with input
            self.shield_angle += input_x * 3.0 * dt
            # Limited movement
            self.x += input_x * self.speed * 0.3 * dt
            self.y += input_y * self.speed * 0.3 * dt
        
        elif self.mode == SoulMode.PURPLE:
            # Rail mode - move along horizontal or vertical rails
            # Input determines which direction on the rail
            self.x += input_x * self.speed * dt
            # Y is locked to current rail (simplified)
        
        elif self.mode == SoulMode.YELLOW:
            # Shooter mode - can shoot but slower movement
            self.x += input_x * self.speed * 0.7 * dt
            self.y += input_y * self.speed * 0.7 * dt
            self.can_shoot = self.shoot_cooldown <= 0
        
        elif self.mode == SoulMode.ORANGE:
            # Must keep moving
            self.x += input_x * self.speed * dt
            self.y += input_y * self.speed * dt
        
        elif self.mode == SoulMode.CYAN:
            # Movement same as red, damage logic handled elsewhere
            self.x += input_x * self.speed * dt
            self.y += input_y * self.speed * dt
        
        # Clamp to bounds
        self.x = max(min_x + self.radius, min(max_x - self.radius, self.x))
        self.y = max(min_y + self.radius, min(max_y - self.radius, self.y))
    
    def make_invincible(self, duration: Optional[float] = None) -> None:
        """Make soul invincible for a duration."""
        self.invincible = True
        self.invincible_timer = duration or self.invincible_duration
    
    def check_collision(self, bullet_x: float, bullet_y: float, bullet_radius: float) -> bool:
        """Check collision with a bullet."""
        if self.invincible:
            return False
        
        dist = math.sqrt((self.x - bullet_x) ** 2 + (self.y - bullet_y) ** 2)
        return dist < (self.radius + bullet_radius)
    
    def set_mode(self, mode: SoulMode) -> None:
        """Change soul mode."""
        self.mode = mode
        
        # Reset mode-specific state
        if mode == SoulMode.BLUE:
            self.velocity_y = 0
            self.grounded = True
        elif mode == SoulMode.GREEN:
            self.shield_angle = 0
        elif mode == SoulMode.YELLOW:
            self.shoot_cooldown = 0


@dataclass
class CombatState:
    """Complete state of a combat encounter."""
    phase: CombatPhase = CombatPhase.INTRO
    result: CombatResult = CombatResult.ONGOING
    
    # Turn tracking
    turn_number: int = 0
    
    # Player state
    player_stats: CombatStats = field(default_factory=CombatStats)
    player_soul: PlayerSoul = field(default_factory=PlayerSoul)
    
    # Selected actions
    current_action: Optional[CombatAction] = None
    selected_act: Optional[str] = None
    selected_item: Optional[str] = None
    
    # Attack state
    attack_timer: float = 0.0
    attack_duration: float = 0.0
    
    # Fight minigame
    fight_bar_position: float = 0.0
    fight_bar_speed: float = 1.0
    fight_damage_calculated: bool = False
    
    # Dialogue
    current_dialogue: str = ""
    dialogue_timer: float = 0.0
    
    # Flee
    flee_attempts: int = 0
    can_flee: bool = True
    
    # Items
    inventory: List[str] = field(default_factory=list)
    
    def advance_turn(self) -> None:
        """Advance to next turn."""
        self.turn_number += 1
        self.current_action = None
        self.selected_act = None
        self.selected_item = None
        self.fight_damage_calculated = False
    
    def start_attack_phase(self, duration: float) -> None:
        """Start enemy attack phase."""
        self.phase = CombatPhase.ENEMY_ATTACK
        self.attack_timer = 0.0
        self.attack_duration = duration
    
    def is_attack_finished(self) -> bool:
        """Check if current attack phase is done."""
        return self.attack_timer >= self.attack_duration


@dataclass
class InventoryItem:
    """An item usable in combat."""
    id: str
    name: str
    description: str
    heal_amount: int = 0
    effect: Optional[str] = None  # Special effect ID
    consumable: bool = True
    

# Default inventory items
DEFAULT_ITEMS: Dict[str, InventoryItem] = {
    "monster_candy": InventoryItem(
        id="monster_candy",
        name="Monster Candy",
        description="Has a distinct, non-licorice flavor.",
        heal_amount=10,
    ),
    "spider_donut": InventoryItem(
        id="spider_donut",
        name="Spider Donut",
        description="A donut made with Spider Cider.",
        heal_amount=12,
    ),
    "butterscotch_pie": InventoryItem(
        id="butterscotch_pie",
        name="Butterscotch Pie",
        description="Butterscotch-cinnamon pie, one slice.",
        heal_amount=99,
    ),
    "dimensional_candy": InventoryItem(
        id="dimensional_candy",
        name="Dimensional Candy",
        description="Tastes different in each dimension.",
        heal_amount=15,
    ),
    "hyper_crystal": InventoryItem(
        id="hyper_crystal",
        name="Hyper Crystal",
        description="4D energy in crystallized form.",
        heal_amount=25,
    ),
    "instant_noodles": InventoryItem(
        id="instant_noodles",
        name="Instant Noodles",
        description="Comes with everything you need!",
        heal_amount=4,  # Heals 4 then 90 after long animation
    ),
}
