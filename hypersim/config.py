"""Configuration file support for HyperSim.

This module provides utilities for loading and saving configuration
from YAML or JSON files.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import os


@dataclass
class WindowConfig:
    """Window and display configuration."""
    width: int = 1024
    height: int = 768
    title: str = "HyperSim"
    fullscreen: bool = False
    vsync: bool = True
    target_fps: int = 60


@dataclass
class RenderConfig:
    """Rendering configuration."""
    background_color: Tuple[int, int, int] = (10, 10, 20)
    default_line_width: int = 2
    projection_distance: float = 5.0
    projection_scale: float = 120.0
    w_scale_factor: float = 0.3
    depth_sort: bool = False
    antialiasing: bool = True


@dataclass
class CameraConfig:
    """Camera configuration."""
    position: Tuple[float, float, float, float] = (0.0, 0.0, -10.0, 0.0)
    target: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    up: Tuple[float, float, float, float] = (0.0, 1.0, 0.0, 0.0)
    move_speed: float = 0.1
    rotation_speed: float = 0.02
    zoom_speed: float = 1.1


@dataclass
class ControlsConfig:
    """Keyboard and mouse controls configuration."""
    move_forward: str = "w"
    move_backward: str = "s"
    move_left: str = "a"
    move_right: str = "d"
    move_up: str = "q"
    move_down: str = "e"
    move_w_positive: str = "z"
    move_w_negative: str = "x"
    zoom_in: str = "="
    zoom_out: str = "-"
    toggle_spin: str = "t"
    reset_view: str = "r"
    quit: str = "escape"


@dataclass
class AnimationConfig:
    """Animation configuration."""
    auto_spin: bool = True
    spin_speed_xy: float = 0.4
    spin_speed_xw: float = 0.6
    spin_speed_yw: float = 0.5
    spin_speed_zw: float = 0.3


@dataclass
class HypersimConfig:
    """Main configuration container for HyperSim."""
    window: WindowConfig = field(default_factory=WindowConfig)
    render: RenderConfig = field(default_factory=RenderConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    controls: ControlsConfig = field(default_factory=ControlsConfig)
    animation: AnimationConfig = field(default_factory=AnimationConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HypersimConfig":
        """Create configuration from dictionary."""
        return cls(
            window=WindowConfig(**data.get("window", {})),
            render=RenderConfig(**data.get("render", {})),
            camera=CameraConfig(**data.get("camera", {})),
            controls=ControlsConfig(**data.get("controls", {})),
            animation=AnimationConfig(**data.get("animation", {})),
        )
    
    def save(self, path: str | Path) -> None:
        """Save configuration to a JSON file.
        
        Args:
            path: Path to save the configuration file
        """
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: str | Path) -> "HypersimConfig":
        """Load configuration from a JSON file.
        
        Args:
            path: Path to the configuration file
            
        Returns:
            Loaded configuration
        """
        path = Path(path)
        if not path.exists():
            return cls()  # Return default config
        
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


def get_default_config_path() -> Path:
    """Get the default configuration file path.
    
    Returns platform-appropriate config directory:
    - Linux/Mac: ~/.config/hypersim/config.json
    - Windows: %APPDATA%/hypersim/config.json
    """
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", "~"))
    else:  # Unix-like
        base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))
    
    return base.expanduser() / "hypersim" / "config.json"


def load_config(path: Optional[str | Path] = None) -> HypersimConfig:
    """Load configuration from file, falling back to defaults.
    
    Args:
        path: Optional path to config file. If None, uses default location.
        
    Returns:
        Loaded or default configuration
    """
    if path is None:
        path = get_default_config_path()
    return HypersimConfig.load(path)


def save_config(config: HypersimConfig, path: Optional[str | Path] = None) -> None:
    """Save configuration to file.
    
    Args:
        config: Configuration to save
        path: Optional path. If None, uses default location.
    """
    if path is None:
        path = get_default_config_path()
    
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    config.save(path)


# Default configuration instance
DEFAULT_CONFIG = HypersimConfig()
