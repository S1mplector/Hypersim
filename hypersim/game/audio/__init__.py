"""Audio subsystem - voice synthesis and sound effects.

This package contains:
- voice_synth.py: Undertale-style typewriter voice beeps
"""
from .voice_synth import (
    VoiceSynthesizer,
    VoiceProfile,
    WaveformType,
    TypewriterTextSystem,
    TypewriterState,
    VOICE_PRESETS,
    get_typewriter,
    get_voice_profile,
    create_custom_voice,
    register_voice,
)

__all__ = [
    "VoiceSynthesizer",
    "VoiceProfile", 
    "WaveformType",
    "TypewriterTextSystem",
    "TypewriterState",
    "VOICE_PRESETS",
    "get_typewriter",
    "get_voice_profile",
    "create_custom_voice",
    "register_voice",
]
