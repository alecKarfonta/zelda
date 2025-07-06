#!/usr/bin/env python3
"""
OoT Generator Enums and Data Models
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any, Set


class ExampleType(Enum):
    CODE_EXPLANATION = "code_explanation"
    FEATURE_IMPLEMENTATION = "feature_implementation" 
    DEBUGGING_HELP = "debugging_help"
    ACTOR_CREATION = "actor_creation"
    ANIMATION_SYSTEM = "animation_system"
    COLLISION_SYSTEM = "collision_system"
    INTERACTION_SYSTEM = "interaction_system"
    EFFECT_SYSTEM = "effect_system"
    SOUND_SYSTEM = "sound_system"
    AI_BEHAVIOR = "ai_behavior"
    ENVIRONMENTAL = "environmental"
    COMBAT_SYSTEM = "combat_system"
    PUZZLE_SYSTEM = "puzzle_system"
    UI_SYSTEM = "ui_system"
    MEMORY_MANAGEMENT = "memory_management"
    OPTIMIZATION = "optimization"
    DEBUGGING_TOOLS = "debugging_tools"
    CUSTOM_MECHANICS = "custom_mechanics"


class ActorCategory(Enum):
    """Real OoT actor categories based on actual source code"""
    ENEMY = "enemy"           # En_* actors that are hostile (En_Dodongo, En_Karebaba, etc.)
    NPC = "npc"               # En_* actors that are friendly/interactive (En_Zo, En_Guest, etc.)
    ITEM = "item"             # Item_* actors and collectibles (Item_Shield, Item_Ocarina, etc.)
    OBJECT = "object"         # Obj_* actors (Obj_Switch, Obj_Lift, etc.)
    BACKGROUND = "background"  # Bg_* actors (Bg_*, environmental objects)
    EFFECT = "effect"         # Effect actors (Oceff_*, Magic_*, etc.)
    PLAYER = "player"         # Player-related actors
    MISC = "misc"            # Other En_* actors that don't fit above categories


@dataclass
class TrainingExample:
    example_type: ExampleType
    instruction: str
    input: Optional[str] = None
    output: str = ""
    metadata: Optional[Dict[str, Any]] = None
    quality_score: float = 0.0
    validation_notes: str = ""
    authenticity_score: float = 0.0 