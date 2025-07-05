#!/usr/bin/env python3
"""
Enhanced OoT Romhack Training Data Generator with Strict Authenticity Validation + Real Decompilation Data

This merges:
1. Strict authenticity validation (rejects mixed patterns)
2. Comprehensive real function signatures from OoT decompilation  
3. Multi-pass validation with architectural enforcement
4. Real struct definitions and authentic examples
5. Dynamic source code analysis and integration
"""

import json
import re
import random
import time
import os
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import anthropic

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Use pip install python-dotenv")

# Snippet cache for real headers/macros
from support.oot_context_cache import get_snippet, get_macro_pack, get_example


class DynamicSourceAnalyzer:
    """Analyzes and extracts information from real OoT decompilation source files"""
    
    def __init__(self, oot_root_path: str = "oot"):
        self.oot_root = Path(oot_root_path)
        self.source_cache = {}
        self.analyzed_files = set()
        
        # Source file categories
        self.source_categories = {
            "actors": self.oot_root / "src" / "overlays" / "actors",
            "core": self.oot_root / "src" / "code", 
            "effects": self.oot_root / "src" / "overlays" / "effects",
            "gamestates": self.oot_root / "src" / "overlays" / "gamestates",
            "misc": self.oot_root / "src" / "overlays" / "misc",
            "headers": self.oot_root / "include",
            "assets": self.oot_root / "assets",
        }
        
        # Real function signatures extracted from source
        self.real_functions = {}
        self.real_structs = {}
        self.real_enums = {}
        self.real_constants = {}
        self.real_examples = {}
        
        # Initialize analysis
        self._analyze_source_files()
    
    def _analyze_source_files(self):
        """Analyze all source files and extract patterns"""
        print("🔍 Analyzing OoT decompilation source files...")
        
        # Analyze core files first
        core_files = list(self.source_categories["core"].glob("*.c"))
        for file_path in core_files:
            self._analyze_c_file(file_path, "core")
        
        # Analyze actor files
        actor_dirs = list(self.source_categories["actors"].glob("ovl_*"))
        for actor_dir in actor_dirs:
            c_files = list(actor_dir.glob("*.c"))
            for file_path in c_files:
                self._analyze_c_file(file_path, "actor")
        
        # Analyze header files
        header_files = list(self.source_categories["headers"].glob("*.h"))
        for file_path in header_files:
            self._analyze_h_file(file_path)
        
        print(f"✅ Analyzed {len(self.analyzed_files)} files")
        print(f"   📊 Found {len(self.real_functions)} functions")
        print(f"   📊 Found {len(self.real_structs)} structs")
        print(f"   📊 Found {len(self.real_enums)} enums")
        print(f"   📊 Found {len(self.real_constants)} constants")
    
    def _analyze_c_file(self, file_path: Path, category: str):
        """Analyze a C source file for patterns"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.analyzed_files.add(str(file_path))
            
            # Extract function signatures
            self._extract_function_signatures(content, file_path, category)
            
            # Extract struct definitions
            self._extract_struct_definitions(content, file_path, category)
            
            # Extract enum definitions
            self._extract_enum_definitions(content, file_path, category)
            
            # Extract constants and macros
            self._extract_constants(content, file_path, category)
            
            # Extract complete examples for specific patterns
            self._extract_examples(content, file_path, category)
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _analyze_h_file(self, file_path: Path):
        """Analyze a header file for definitions"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.analyzed_files.add(str(file_path))
            
            # Extract typedefs and struct definitions
            self._extract_struct_definitions(content, file_path, "header")
            self._extract_enum_definitions(content, file_path, "header")
            self._extract_constants(content, file_path, "header")
            
        except Exception as e:
            print(f"⚠️  Error analyzing {file_path}: {e}")
    
    def _extract_function_signatures(self, content: str, file_path: Path, category: str):
        """Extract function signatures from C source"""
        # Pattern for function definitions
        func_pattern = r'(?:^|\n)\s*(\w+(?:\s+\w+)*)\s+(\w+)\s*\([^)]*\)\s*\{'
        
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            return_type = match.group(1).strip()
            func_name = match.group(2)
            
            # Get the full function signature
            start = match.start()
            func_line = content[start:match.end()].strip()
            
            self.real_functions[func_name] = {
                "signature": func_line,
                "return_type": return_type,
                "file": str(file_path),
                "category": category,
            }
    
    def _extract_struct_definitions(self, content: str, file_path: Path, category: str):
        """Extract struct definitions"""
        # Pattern for struct definitions with memory comments
        struct_pattern = r'typedef\s+struct\s*\w*\s*\{([^}]+)\}\s*(\w+);'
        
        for match in re.finditer(struct_pattern, content, re.DOTALL):
            struct_body = match.group(1)
            struct_name = match.group(2)
            
            # Parse struct fields
            fields = []
            for line in struct_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    fields.append(line)
            
            self.real_structs[struct_name] = {
                "fields": fields,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_enum_definitions(self, content: str, file_path: Path, category: str):
        """Extract enum definitions"""
        enum_pattern = r'typedef\s+enum\s*\w*\s*\{([^}]+)\}\s*(\w+);'
        
        for match in re.finditer(enum_pattern, content, re.DOTALL):
            enum_body = match.group(1)
            enum_name = match.group(2)
            
            # Parse enum values
            values = []
            for line in enum_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    values.append(line.rstrip(','))
            
            self.real_enums[enum_name] = {
                "values": values,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_constants(self, content: str, file_path: Path, category: str):
        """Extract #define constants and macros"""
        define_pattern = r'#define\s+(\w+)\s+([^\n]+)'
        
        for match in re.finditer(define_pattern, content):
            const_name = match.group(1)
            const_value = match.group(2).strip()
            
            self.real_constants[const_name] = {
                "value": const_value,
                "file": str(file_path),
                "category": category,
                "full_definition": match.group(0)
            }
    
    def _extract_examples(self, content: str, file_path: Path, category: str):
        """Extract complete code examples for specific patterns"""
        # Extract actor initialization patterns
        if "Init" in str(file_path) or "_Init(" in content:
            init_pattern = r'void\s+\w+_Init\s*\([^)]+\)\s*\{[^}]+\}'
            for match in re.finditer(init_pattern, content, re.DOTALL):
                example_key = f"{file_path.stem}_init"
                self.real_examples[example_key] = {
                    "code": match.group(0),
                    "type": "actor_init",
                    "file": str(file_path),
                    "category": category
                }
        
        # Extract collision setup patterns
        if "Collider" in content:
            collider_pattern = r'static\s+Collider\w+Init\s+\w+\s*=\s*\{[^}]+\};'
            for match in re.finditer(collider_pattern, content, re.DOTALL):
                example_key = f"{file_path.stem}_collider"
                self.real_examples[example_key] = {
                    "code": match.group(0),
                    "type": "collider_init",
                    "file": str(file_path),
                    "category": category
                }
    
    def get_real_function_signature(self, func_name: str) -> Optional[str]:
        """Get the real function signature from source code"""
        if func_name in self.real_functions:
            return self.real_functions[func_name]["signature"]
        return None
    
    def get_real_struct_definition(self, struct_name: str) -> Optional[str]:
        """Get the real struct definition from source code"""
        if struct_name in self.real_structs:
            return self.real_structs[struct_name]["full_definition"]
        return None
    
    def get_similar_actors(self, actor_type: str, limit: int = 5) -> List[str]:
        """Get similar actors for reference"""
        actor_files = []
        for func_name, func_info in self.real_functions.items():
            if func_info["category"] == "actor" and actor_type.lower() in func_info["file"].lower():
                actor_files.append(func_info["file"])
        
        return list(set(actor_files))[:limit]
    
    def get_authentic_example(self, example_type: str) -> Optional[Dict]:
        """Get an authentic code example of the specified type"""
        matching_examples = [
            example for key, example in self.real_examples.items()
            if example["type"] == example_type
        ]
        
        if matching_examples:
            return random.choice(matching_examples)
        return None
    
    def get_real_constants_by_prefix(self, prefix: str) -> Dict[str, str]:
        """Get real constants starting with a prefix"""
        return {
            name: info["value"] for name, info in self.real_constants.items()
            if name.startswith(prefix)
        }
    
    def validate_against_real_source(self, code: str) -> List[str]:
        """Validate code against real source patterns"""
        issues = []
        
        # Check if functions used exist in real source
        func_pattern = r'(\w+)\s*\('
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and
                len(func_name) > 3 and func_name not in self.real_functions):
                issues.append(f"Function '{func_name}' not found in real OoT source")
        
        # Check if structs used exist
        struct_pattern = r'(\w+)\s*\*?\s+\w+\s*='
        for match in re.finditer(struct_pattern, code):
            struct_name = match.group(1)
            if (struct_name not in ['int', 'char', 'float', 'double', 'void', 'u8', 'u16', 'u32', 's8', 's16', 's32', 'f32'] and
                struct_name not in self.real_structs):
                issues.append(f"Struct '{struct_name}' not found in real OoT source")
        
        return issues

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

class StrictAuthenticityValidator:
    """Enhanced validator with strict authenticity enforcement + real OoT function data"""
    
    def __init__(self, source_analyzer: Optional[DynamicSourceAnalyzer] = None):
        # Use dynamic source analyzer if provided, otherwise use hardcoded data
        self.source_analyzer = source_analyzer
        
        if source_analyzer:
            # Real function signatures from actual OoT decompilation
            self.authentic_function_signatures = set(source_analyzer.real_functions.keys())
            
            # Real OoT types from decompilation
            self.authentic_types = set(source_analyzer.real_structs.keys())
        else:
            # Fallback to hardcoded data
            self.authentic_function_signatures = self._load_real_oot_functions()
            self.authentic_types = self._load_real_oot_types()
        
        # Mandatory corrections for authenticity
        self.mandatory_corrections = {
            # Function signature corrections
            "GlobalContext": "PlayState",
            "globalCtx": "play",
            "void ActorName_Init(PlayState* play, Actor* thisx)": "void ActorName_Init(Actor* thisx, PlayState* play)",
            "void ActorName_Update(PlayState* play, Actor* thisx)": "void ActorName_Update(Actor* thisx, PlayState* play)",
            "void ActorName_Destroy(PlayState* play, Actor* thisx)": "void ActorName_Destroy(Actor* thisx, PlayState* play)",
            "void ActorName_Draw(PlayState* play, Actor* thisx)": "void ActorName_Draw(Actor* thisx, PlayState* play)",
            
            # Position access corrections (from real decompilation)
            "this->actor.pos": "this->actor.world.pos",
            "this->actor.rot": "this->actor.world.rot", 
            "player->actor.pos": "player->actor.world.pos",
            
            # Structure corrections
            "ActorInit": "ActorProfile",
            "const ActorInit": "const ActorProfile",
        }
        
        # Forbidden patterns that indicate non-authenticity (STRICT)
        self.forbidden_patterns = [
            r"GlobalContext\*\s+\w+",  # Any GlobalContext usage
            r"void\s+\w+_Init\(PlayState\*.*?Actor\*",  # Wrong parameter order
            r"void\s+\w+_Update\(PlayState\*.*?Actor\*",  # Wrong parameter order
            r"ACTOR_HEART_PIECE",  # Custom heart piece actors (should use EN_ITEM00)
            r"HeartPieceActor",  # Custom heart piece structs
            r"\.pos\.",  # Direct pos access instead of world.pos
            r"gPlayState",  # Global state variables
            r"gGlobalCtx",  # Global context variables
        ]
        
        # Required authentic patterns for quality code
        self.required_patterns = [
            r"PlayState\*\s+play",  # Modern PlayState usage
            r"Actor\*\s+thisx",  # Authentic actor parameter
            r"world\.pos",  # Proper position access
            r"ACTORCAT_\w+",  # Actor categories
            r"Collider_\w+",  # Collision functions
        ]
        
        # Real architectural patterns from OoT decompilation
        self.architectural_guidance = {
            "heart_piece": "Use EnItem00 with ITEM00_HEART_PIECE parameter (from z_en_item00.c)",
            "rupees": "Use EnItem00 with ITEM00_RUPEE_* parameters (from z_en_item00.c)", 
            "keys": "Use EnItem00 with ITEM00_SMALL_KEY parameter (from z_en_item00.c)",
            "collectibles": "Most collectibles use EnItem00 with different parameters (see z_en_item00.c)",
            "switches": "Use existing switch actors with parameters, rarely create new ones",
        }

    def _load_real_oot_functions(self) -> Set[str]:
        """Load real function names from OoT decompilation"""
        return {
            # Core Actor functions from z_actor.c
            "ActorShape_Init", "ActorShadow_DrawCircle", "ActorShadow_DrawWhiteCircle", "ActorShadow_DrawHorse", 
            "ActorShadow_DrawFeet", "Actor_SetFeetPos", "Actor_ProjectPos", "Actor_Kill", "Actor_SetWorldToHome",
            "Actor_SetFocus", "Actor_SetWorldRotToShape", "Actor_SetShapeRotToWorld", "Actor_SetScale", 
            "Actor_SetObjectDependency", "Actor_Init", "Actor_Destroy", "Actor_UpdatePos", "Actor_UpdateVelocityXZGravity",
            "Actor_MoveXZGravity", "Actor_UpdateVelocityXYZ", "Actor_MoveXYZ", "Actor_SetProjectileSpeed",
            "Actor_UpdatePosByAnimation", "Actor_WorldYawTowardActor", "Actor_FocusYawTowardActor", "Actor_WorldYawTowardPoint",
            "Actor_WorldPitchTowardActor", "Actor_FocusPitchTowardActor", "Actor_WorldPitchTowardPoint", 
            "Actor_WorldDistXYZToActor", "Actor_WorldDistXYZToPoint", "Actor_WorldDistXZToActor", "Actor_WorldDistXZToPoint",
            "Actor_WorldToActorCoords", "Actor_HeightDiff", "Actor_UpdateBgCheckInfo", "Actor_GetFocus", "Actor_GetWorld",
            "Actor_GetWorldPosShapeRot", "Actor_Spawn", "Actor_SpawnAsChild", "Actor_SpawnTransitionActors",
            
            # Collision system functions from z_collision_check.c
            "Collider_InitBase", "Collider_DestroyBase", "Collider_SetBaseToActor", "Collider_SetBaseType1", "Collider_SetBase",
            "Collider_ResetATBase", "Collider_ResetACBase", "Collider_ResetOCBase", "Collider_InitElement", "Collider_DestroyElement",
            "Collider_SetElement", "Collider_ResetATElement", "Collider_ResetACElement", "Collider_ResetOCElement",
            "Collider_InitCylinder", "Collider_DestroyCylinder", "Collider_SetCylinderToActor", "Collider_SetCylinderType1",
            "Collider_SetCylinder", "Collider_ResetCylinderAT", "Collider_ResetCylinderAC", "Collider_ResetCylinderOC",
            "Collider_UpdateCylinder", "Collider_SetCylinderPosition", "Collider_InitJntSph", "Collider_FreeJntSph",
            "Collider_DestroyJntSph", "Collider_SetJntSphToActor", "Collider_SetJntSphAllocType1", "Collider_SetJntSphAlloc",
            "Collider_SetJntSph", "Collider_ResetJntSphAT", "Collider_ResetJntSphAC", "Collider_ResetJntSphOC",
            "Collider_UpdateSpheres", "CollisionCheck_InitContext", "CollisionCheck_DestroyContext", "CollisionCheck_ClearContext",
            "CollisionCheck_SetAT", "CollisionCheck_SetAC", "CollisionCheck_SetOC", "CollisionCheck_SetOCLine",
            
            # Interaction functions from z_actor.c
            "Actor_TalkOfferAccepted", "Actor_OfferTalkExchange", "Actor_OfferTalkExchangeEquiCylinder", "Actor_OfferTalk",
            "Actor_OfferTalkNearColChkInfoCylinder", "Actor_TextboxIsClosing", "Actor_GetPlayerExchangeItemId", 
            "Actor_GetScreenPos", "Actor_HasParent", "Actor_OfferGetItem", "Actor_OfferGetItemNearby", "Actor_OfferCarry",
            "Actor_HasNoParent", "Actor_IsFacingPlayer", "Actor_ActorAIsFacingActorB", "Actor_IsFacingAndNearPlayer",
            "Actor_ActorAIsFacingAndNearActorB", "Player_IsFacingActor", "Actor_ActorBIsFacingActorA", "Actor_IsLockedOn",
            "Actor_OtherIsLockedOn", "Npc_UpdateTalking", "Npc_GetTrackingPresetMaxPlayerYaw", "Npc_TrackPoint",
            
            # Flag system functions from z_actor.c
            "Flags_GetSwitch", "Flags_SetSwitch", "Flags_UnsetSwitch", "Flags_GetUnknown", "Flags_SetUnknown",
            "Flags_UnsetUnknown", "Flags_GetTreasure", "Flags_SetTreasure", "Flags_GetClear", "Flags_SetClear",
            "Flags_UnsetClear", "Flags_GetTempClear", "Flags_SetTempClear", "Flags_UnsetTempClear", "Flags_GetCollectible",
            "Flags_SetCollectible", "Flags_GetEventChkInf", "Flags_SetEventChkInf", "Flags_GetInfTable", "Flags_SetInfTable",
            
            # Math and utility functions
            "Math_SinS", "Math_CosS", "Math_ApproachF", "Math_ApproachS", "Math_Vec3f_Copy", "Math_Vec3f_DistXZ",
            "Math_Vec3f_DistXYZ", "Rand_CenteredFloat", "Rand_ZeroFloat", "Player_GetHeight", "Player_PlaySfx",
            "Player_SetCsAction", "Player_SetCsActionWithHaltedActors", "Matrix_Translate", "Matrix_Scale", "Matrix_RotateX",
            "Matrix_RotateY", "Matrix_RotateZ", "Matrix_Push", "Matrix_Pop", "Matrix_NewMtx", "Matrix_Put", "Matrix_Get",
            
            # Audio functions from z_actor.c
            "Actor_PlaySfx", "Actor_PlaySfx_SurfaceBomb", "Actor_PlaySfx_Flagged2", "Actor_PlaySfx_FlaggedCentered1",
            "Actor_PlaySfx_FlaggedCentered2", "Actor_PlaySfx_Flagged", "Actor_PlaySfx_FlaggedTimer", "Audio_PlayActorSound2",
            
            # Item functions from z_en_item00.c
            "EnItem00_SetupAction", "EnItem00_Init", "EnItem00_Destroy", "EnItem00_Update", "EnItem00_Draw",
            "EnItem00_DrawRupee", "EnItem00_DrawCollectible", "EnItem00_DrawHeartContainer", "EnItem00_DrawHeartPiece",
            "Item_DropCollectible", "Item_DropCollectible2", "Item_DropCollectibleRandom", "func_8001F404",
            
            # Effect functions
            "Effect_Add", "EffectBlure_AddVertex", "EffectBlure_AddSpace", "Actor_SpawnFloorDustRing",
            
            # Initialization functions
            "Actor_ProcessInitChain", "Object_GetSlot", "Object_LoadAll", "Object_IsLoaded",
            
            # Attention system functions
            "Attention_Init", "Attention_SetNaviState", "Attention_InitReticle", "Attention_SetReticlePos", 
            "Attention_Draw", "Attention_FindActor", "Attention_ShouldReleaseLockOn",
            
            # Animation functions
            "SkelAnime_Update", "SkelAnime_Init", "Animation_Change", "Animation_GetLastFrame",
            
            # Graphics functions
            "Gfx_DrawDListOpa", "Gfx_DrawDListXlu", "Gfx_SetupDL", "func_80034BA0", "func_80034CC4", 
            "Actor_UpdateAlphaByDistance", "Actor_SetColorFilter", "Actor_DrawDoorLock",
            
            # Memory functions
            "ZELDA_ARENA_MALLOC", "ZELDA_ARENA_FREE", "THA_GetRemaining",
            
            # Background collision functions
            "func_800BFCB8", "func_8002F9EC", "func_80038A28",
        }

    def _load_real_oot_types(self) -> Set[str]:
        """Load real type names from OoT decompilation"""
        return {
            # Core OoT types from actor.h and other headers
            "Actor", "PlayState", "Vec3f", "Vec3s", "PosRot", "s16", "u16", "s32", "u32", "s8", "u8", "f32",
            
            # Actor system types
            "ActorShape", "ActorFunc", "ActorShadowFunc", "ActorProfile", "ActorEntry", "ActorOverlay", "ActorContext",
            "ActorListEntry", "ActorContextSceneFlags", "EnItem00", "EnItem00ActionFunc", "DynaPolyActor",
            
            # Collision types
            "ColliderCylinder", "ColliderJntSph", "ColliderTris", "ColliderQuad", "ColliderElement", "CollisionCheckInfo",
            "CollisionCheckContext", "ColliderCylinderInit", "ColliderJntSphInit", "ColliderElementInit", 
            "ColliderElementDamageInfoAT", "ColliderElementDamageInfoAC", "ColliderJntSphElement", "ColliderJntSphElementDim",
            "ColliderInit", "ColliderInitToActor", "ColliderInitType1", "Collider", "CollisionPoly", "BgCheckFlags", "OcLine",
            
            # Animation types
            "SkelAnime", "AnimationHeader", "OverrideLimbDraw", "PostLimbDraw", "AnimationInfo",
            
            # Graphics types
            "Gfx", "GraphicsContext", "Color_RGBA8", "Color_RGB8", "Color_RGBAf", "MtxF", "Mtx", "Lights", "Light",
            "BodyBreak", "Hilite", "Vtx",
            
            # Player and NPC types
            "Player", "NpcInteractInfo", "NpcGetTextIdFunc", "NpcUpdateTalkStateFunc", "NpcTrackingMode", "NpcTalkState",
            
            # Attention system types
            "Attention", "LockOnReticle", "AttentionColor", "AttentionRangeType",
            
            # Context types
            "ObjectContext", "GameState", "TitleCardContext", "InitChainEntry",
        }

    def validate_function_signatures(self, code: str) -> List[str]:
        """Strict validation against real OoT function signatures"""
        issues = []
        
        # Check for wrong parameter order in actor lifecycle functions
        wrong_order_patterns = [
            r"void\s+\w+_Init\(PlayState\*[^,]*,\s*Actor\*",
            r"void\s+\w+_Update\(PlayState\*[^,]*,\s*Actor\*", 
            r"void\s+\w+_Destroy\(PlayState\*[^,]*,\s*Actor\*",
            r"void\s+\w+_Draw\(PlayState\*[^,]*,\s*Actor\*",
        ]
        
        for pattern in wrong_order_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong parameter order - should be (Actor* thisx, PlayState* play)")
        
        # Check for GlobalContext usage
        if re.search(r"GlobalContext", code):
            issues.append("CRITICAL: Uses outdated GlobalContext instead of PlayState")
            
        # Check for forbidden architectural patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                issues.append(f"FORBIDDEN: Found non-authentic pattern: {pattern}")
        
        # Use dynamic source analyzer if available
        if self.source_analyzer:
            dynamic_issues = self.source_analyzer.validate_against_real_source(code)
            issues.extend(dynamic_issues)
        else:
            # Fallback to hardcoded validation
            func_pattern = r'(\w+)\s*\('
            unknown_functions = []
            for match in re.finditer(func_pattern, code):
                func_name = match.group(1)
                if (func_name not in self.authentic_function_signatures and 
                    func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                    not func_name.startswith('g') and  # Skip display lists
                    not func_name.isupper() and  # Skip macros
                    len(func_name) > 3):  # Skip short names
                    unknown_functions.append(func_name)
                    
            if unknown_functions:
                issues.append(f"NON-AUTHENTIC: Unknown functions: {', '.join(unknown_functions[:5])}")
        
        return issues

    def validate_architectural_authenticity(self, code: str, instruction: str) -> List[str]:
        """Validate against authentic OoT architectural patterns"""
        issues = []
        
        # Check for custom heart piece actors (should use EnItem00)
        if "heart piece" in instruction.lower() and "ACTOR_HEART_PIECE" in code:
            issues.append("ARCHITECTURAL: Heart pieces should use EnItem00 with ITEM00_HEART_PIECE parameter")
            
        # Check for custom collectible actors
        collectible_keywords = ["rupee", "key", "magic jar", "arrow bundle"]
        if any(keyword in instruction.lower() for keyword in collectible_keywords):
            if "EnItem00" not in code and "ACTOR_EN_ITEM00" not in code:
                issues.append("ARCHITECTURAL: Collectibles should typically use EnItem00 (see z_en_item00.c)")
        
        # Check for proper ActorProfile usage
        if "ActorInit" in code:
            issues.append("NAMING: Should use ActorProfile, not ActorInit")
            
        return issues

    def apply_mandatory_corrections(self, code: str) -> str:
        """Apply mandatory corrections for authenticity"""
        corrected = code
        
        for old_pattern, new_pattern in self.mandatory_corrections.items():
            corrected = corrected.replace(old_pattern, new_pattern)
        
        # Fix parameter order with regex
        parameter_fixes = [
            (r"void\s+(\w+)_Init\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Init(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Update\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Update(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Destroy\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Destroy(Actor* \3, PlayState* \2)"),
            (r"void\s+(\w+)_Draw\(PlayState\*\s+(\w+),\s*Actor\*\s+(\w+)\)",
             r"void \1_Draw(Actor* \3, PlayState* \2)"),
        ]
        
        for old_regex, new_format in parameter_fixes:
            corrected = re.sub(old_regex, new_format, corrected)
            
        return corrected

    def calculate_authenticity_score(self, code: str) -> float:
        """Calculate authenticity score based on real OoT patterns"""
        score = 10.0  # Start with perfect score
        
        # Major penalties for forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, code):
                score -= 2.0
                
        # Check function authenticity
        func_pattern = r'(\w+)\s*\('
        total_functions = 0
        authentic_functions = 0
        
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and len(func_name) > 3):
                total_functions += 1
                if func_name in self.authentic_function_signatures:
                    authentic_functions += 1
                    
        if total_functions > 0:
            func_authenticity = authentic_functions / total_functions
            score = score * func_authenticity + (score * 0.1)  # Blend score based on function authenticity
        
        # Bonus for required patterns
        required_found = sum(1 for pattern in self.required_patterns if re.search(pattern, code))
        if required_found >= len(self.required_patterns) * 0.8:
            score += 1.0
            
        return max(0.0, min(10.0, score))


class EnhancedOoTTrainingGenerator:
    """Enhanced generator with strict authenticity + real OoT decompilation data + diversity injection"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", 
                 oot_path: str = "oot", use_dynamic_analysis: bool = True):
        # Try to get API key from environment first, then parameter
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY in .env file or pass as parameter")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        
        # Initialize dynamic source analyzer if enabled
        self.source_analyzer = None
        if use_dynamic_analysis:
            try:
                print(f"🔍 Initializing dynamic source analysis from {oot_path}...")
                self.source_analyzer = DynamicSourceAnalyzer(oot_path)
                print("✅ Dynamic source analysis initialized successfully")
            except Exception as e:
                print(f"⚠️  Dynamic source analysis failed: {e}")
                print("   Falling back to hardcoded validation...")
        
        self.validator = StrictAuthenticityValidator(self.source_analyzer)
        
        # Initialize diversity injector
        self.diversity_injector = DiversityInjector()
        
        # Initialize dynamic temperature manager
        self.temperature_manager = DynamicTemperatureManager()
        
        # Initialize validation and context system
        try:
            from support.validate_and_enhance_scenarios import OoTPatternValidator
            from support.complete_context_generator import CompleteOoTContextGenerator
            self.pattern_validator = OoTPatternValidator(oot_path)
            self.context_generator = CompleteOoTContextGenerator(oot_path)
            self.use_validation = True
            print("✅ Enhanced validation and context generation enabled")
        except ImportError:
            print("⚠️  Enhanced validation not available, using basic validation")
            self.use_validation = False
        
        # Load authentic reference patterns from real decompilation
        self.authentic_examples = self._load_real_oot_examples()
        self.context_templates = self._load_enhanced_contexts()
        
        # Track generation statistics
        self.generation_stats = {
            "total_generated": 0,
            "total_accepted": 0,
            "total_rejected": 0,
            "category_distribution": {cat.value: 0 for cat in ActorCategory},
            "type_distribution": {t.value: 0 for t in ExampleType},
            "complexity_distribution": {"basic": 0, "intermediate": 0, "advanced": 0}
        }

    def _load_real_oot_examples(self) -> Dict[str, str]:
        """Load reference examples from authentic decompilation"""
        return {
            "basic_actor_authentic": """
// AUTHENTIC PATTERN from OoT decompilation (z_en_item00.c style)
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ f32 scale;
    /* 0x154 */ ColliderCylinder collider;
} EnExample; // size = 0x1A0

void EnExample_Init(Actor* thisx, PlayState* play) {
    EnExample* this = (EnExample*)thisx;
    
    // Authentic collision initialization pattern
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    // Authentic actor setup
    Actor_SetScale(&this->actor, 0.01f);
    Actor_SetFocus(&this->actor, 50.0f);
    
    this->timer = 0;
    this->actionState = 0;
}

void EnExample_Update(Actor* thisx, PlayState* play) {
    EnExample* this = (EnExample*)thisx;
    
    // Authentic collision update pattern
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, BGCHECKFLAG_GROUND);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Authentic movement pattern
    Actor_MoveXZGravity(&this->actor);
}

// AUTHENTIC ActorProfile from decompilation
const ActorProfile En_Example_Profile = {
    /**/ ACTOR_EN_EXAMPLE,
    /**/ ACTORCAT_MISC,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnExample),
    /**/ EnExample_Init,
    /**/ EnExample_Destroy,
    /**/ EnExample_Update,
    /**/ EnExample_Draw,
};
""",
            
            "collectible_authentic_item00": """
// AUTHENTIC COLLECTIBLE PATTERN - Use EnItem00 from z_en_item00.c
// Heart pieces use ITEM00_HEART_PIECE (0x06)
// Blue rupees use ITEM00_RUPEE_BLUE (0x01) 
// Small keys use ITEM00_SMALL_KEY (0x0B)

void SpawnHeartPiece(PlayState* play, Vec3f* pos) {
    // Authentic pattern from z_en_item00.c
    Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00, 
                pos->x, pos->y, pos->z, 0, 0, 0, ITEM00_HEART_PIECE);
}

void SpawnBlueRupee(PlayState* play, Vec3f* pos) {
    Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00,
                pos->x, pos->y, pos->z, 0, 0, 0, ITEM00_RUPEE_BLUE);
}
""",
            
            "real_collision_patterns": """
// AUTHENTIC COLLISION PATTERNS from z_collision_check.c

static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEM_MATERIAL_UNK0,
        { 0x00000000, HIT_SPECIAL_EFFECT_NONE, 0x00 },
        { 0x00000010, HIT_BACKLASH_NONE, 0x00 },
        ATELEM_NONE,
        ACELEM_ON,
        OCELEM_ON,
    },
    { 15, 25, 0, { 0, 0, 0 } },
};

// Authentic initialization sequence
Collider_InitCylinder(play, &this->collider);
Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);

// Authentic update sequence  
Collider_UpdateCylinder(&this->actor, &this->collider);
CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
""",
        }

    def _load_enhanced_contexts(self) -> Dict[str, str]:
        """Load contexts with strict requirements + real examples"""
        
        # Get dynamic function list if available
        if self.source_analyzer:
            function_list = list(self.source_analyzer.real_functions.keys())[:20]
            function_count = len(self.source_analyzer.real_functions)
            additional_info = f"""
REAL SOURCE DATA AVAILABLE:
   📁 Analyzed {len(self.source_analyzer.analyzed_files)} source files
   🔧 Found {len(self.source_analyzer.real_functions)} functions
   📊 Found {len(self.source_analyzer.real_structs)} structs
   📋 Found {len(self.source_analyzer.real_enums)} enums
   🔧 Found {len(self.source_analyzer.real_constants)} constants
"""
        else:
            function_list = list(self.validator.authentic_function_signatures)[:20]
            function_count = len(self.validator.authentic_function_signatures)
            additional_info = "\n⚠️  Using hardcoded validation (dynamic analysis not available)\n"
        
        return {
            "strict_requirements": f"""
CRITICAL AUTHENTICITY REQUIREMENTS (ENFORCED BY VALIDATION):
{additional_info}
1. FUNCTION SIGNATURES (MANDATORY):
   ✓ Actor lifecycle MUST use: FuncName(Actor* thisx, PlayState* play)
   ✗ NEVER use: FuncName(PlayState* play, Actor* thisx) 
   ✓ ALWAYS use PlayState*, NEVER GlobalContext*

2. ARCHITECTURAL ACCURACY (MANDATORY):
   ✓ Heart pieces: Use EnItem00 with ITEM00_HEART_PIECE parameter
   ✓ Rupees: Use EnItem00 with ITEM00_RUPEE_* parameters  
   ✓ Most collectibles: Use EnItem00, not custom actors
   ✓ Reference z_en_item00.c for collectible patterns

3. POSITION ACCESS (MANDATORY):
   ✓ Use actor.world.pos, NEVER actor.pos
   ✓ Use actor.world.rot, NEVER actor.rot

4. REAL FUNCTION USAGE (MANDATORY):
   Must use ONLY functions from actual OoT decompilation:
   {', '.join(function_list)}...
   (and {function_count} more real functions)

5. COLLISION PATTERNS (MANDATORY):
   ✓ Use Collider_InitCylinder(play, &collider)
   ✓ Use Collider_SetCylinder(play, &collider, &actor, &init)
   ✓ Follow patterns from z_collision_check.c

VALIDATION WILL REJECT ANY EXAMPLE VIOLATING THESE REQUIREMENTS.
""",
            
            "authentic_actor_context": f"""
AUTHENTIC ACTOR SYSTEM (FROM REAL OoT DECOMPILATION):

REAL ACTOR STRUCTURE PATTERN (from actor.h):
```c
typedef struct {{
    /* 0x0000 */ Actor actor;  // Base actor (size 0x14C)
    /* 0x014C */ // Custom fields start here with proper offsets
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 actionState;
    /* 0x0150 */ f32 customScale;
    /* 0x0154 */ ColliderCylinder collider;  // If collision needed
}} ActorName; // size = calculated correctly

// MANDATORY: Exact parameter order from decompilation
void ActorName_Init(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    // Authentic patterns from z_actor.c and z_en_item00.c
}}

void ActorName_Update(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    // Authentic patterns from z_actor.c
}}

// MANDATORY: Exact ActorProfile format from real decompilation
const ActorProfile ActorName_Profile = {{
    /**/ ACTOR_ACTORNAME,
    /**/ ACTORCAT_MISC,
    /**/ FLAGS,
    /**/ OBJECT_ACTORNAME,
    /**/ sizeof(ActorName),
    /**/ ActorName_Init,
    /**/ ActorName_Destroy,
    /**/ ActorName_Update,
    /**/ ActorName_Draw,
}};
```

AUTHENTIC REFERENCE EXAMPLE:
{self.authentic_examples['basic_actor_authentic']}
""",
        }

    def generate_training_example(self, example_type: ExampleType, complexity: str = "intermediate") -> TrainingExample:
        """Generate with strict authenticity validation + diversity injection + refinement"""
        
        # Update generation stats
        self.generation_stats["total_generated"] += 1
        self.generation_stats["type_distribution"][example_type.value] += 1
        self.generation_stats["complexity_distribution"][complexity] += 1
        
        # Phase 1: Generate with diversity injection
        example = self._generate_with_diverse_prompt(example_type, complexity)
        
        if not example:
            print(f"[DEBUG] Generation failed - no example returned")
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Phase 2: Multi-pass validation and correction
        example = self._multi_pass_validation(example)
        
        # Phase 3: Refinement if quality is low but not terrible
        if example.quality_score < 7.0 and example.quality_score > 3.0:
            print(f"[REFINE] Attempting to refine example (quality: {example.quality_score:.1f})")
            refined_example = self._refine_example(example, example_type, complexity)
            if refined_example and refined_example.quality_score > example.quality_score:
                example = refined_example
                print(f"[REFINE] ✅ Refinement improved quality: {example.quality_score:.1f}")
            else:
                print(f"[REFINE] ❌ Refinement did not improve quality")
        
        # Phase 4: Final authenticity scoring
        example.authenticity_score = self.validator.calculate_authenticity_score(example.output)
        
        # More lenient rejection criteria
        quality_threshold = 6.0  # Reduced from 7.0
        authenticity_threshold = 6.0  # Reduced from 7.0
        
        if example.authenticity_score < authenticity_threshold or example.quality_score < quality_threshold:
            print(f"[REJECT] Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
            print(f"[DEBUG] Instruction: {example.instruction[:50]}...")
            print(f"[DEBUG] Output length: {len(example.output)}")
            print(f"[DEBUG] Validation notes: {example.validation_notes}")
            self.generation_stats["total_rejected"] += 1
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Update acceptance stats
        self.generation_stats["total_accepted"] += 1
            
        return example

    def _refine_example(self, example: TrainingExample, example_type: ExampleType, complexity: str) -> Optional[TrainingExample]:
        """Attempt to refine a low-quality example"""
        
        # Identify specific issues
        issues = []
        if len(example.output) < 500:
            issues.append("Output too short - needs more complete implementation")
        if "```c" not in example.output:
            issues.append("Missing proper code formatting")
        if "GlobalContext" in example.output:
            issues.append("Uses outdated GlobalContext instead of PlayState")
        if not re.search(r"Actor\*\s+thisx.*PlayState\*\s+play", example.output):
            issues.append("Incorrect function parameter order")
        
        if not issues:
            return None  # No obvious issues to fix
        
        # Create refinement prompt
        refinement_prompt = f"""
The following OoT code example has quality issues. Please fix them and provide a complete, authentic implementation:

ORIGINAL INSTRUCTION: {example.instruction}

ORIGINAL CODE:
{example.output}

ISSUES TO FIX:
{chr(10).join(f"- {issue}" for issue in issues)}

REQUIREMENTS FOR FIXED VERSION:
1. Use proper function signatures: FuncName(Actor* thisx, PlayState* play)
2. Include complete struct definition with memory offsets
3. Use authentic OoT function names and patterns
4. Provide at least 500 characters of meaningful code
5. Use world.pos not pos, PlayState* not GlobalContext*
6. Include proper collision setup and state management

Generate exactly this JSON format:
{{
    "instruction": "{example.instruction}",
    "input": null,
    "output": "Complete, fixed OoT code"
}}
"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,  # Lower temperature for refinement
                messages=[{"role": "user", "content": refinement_prompt}]
            )
            
            content_block = response.content[0]
            if content_block.type == 'text':
                raw_response = content_block.text
                refined_example = self._parse_response(raw_response, example_type)
                
                if refined_example:
                    # Validate the refined example
                    refined_example = self._multi_pass_validation(refined_example)
                    refined_example.metadata = {"generation_method": "refinement", "original_quality": example.quality_score}
                    return refined_example
                    
        except Exception as e:
            print(f"[REFINE] Error during refinement: {e}")
            
        return None

    def _generate_with_diverse_prompt(self, example_type: ExampleType, complexity: str) -> Optional[TrainingExample]:
        """Generate with diversity injection and enhanced prompts"""
        
        # Get diverse instruction from injector
        diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
        
        # Validate scenario if enhanced validation is available
        if self.use_validation:
            category = self._map_example_type_to_category(example_type)
            validation = self.pattern_validator.validate_scenario(diverse_instruction, category)
            
            if not validation.is_valid:
                print(f"⚠️  Scenario validation failed: {validation.issues}")
                # Try to get a better scenario
                for _ in range(3):  # Try up to 3 times
                    diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
                    validation = self.pattern_validator.validate_scenario(diverse_instruction, category)
                    if validation.is_valid:
                        break
                else:
                    print(f"❌ Could not generate valid scenario after 3 attempts")
                    return None
        
        # Get dynamic examples if available
        dynamic_examples = self._get_dynamic_examples(example_type)
        
        # Get dynamic temperature based on diversity needs
        diversity_metrics = {
            "actor_categories": {cat.value: 0 for cat in ActorCategory},
            "example_types": {t.value: 0 for t in ExampleType},
            "complexities": {"basic": 0, "intermediate": 0, "advanced": 0},
            "unique_scenarios": set()
        }
        dynamic_temperature = self.temperature_manager.get_dynamic_temperature(example_type, complexity, diversity_metrics)
        
        # Use enhanced context if available
        if self.use_validation and hasattr(self, 'context_generator'):
            category = self._map_example_type_to_category(example_type)
            validation_result = self.pattern_validator.validate_scenario(diverse_instruction, category)
            # -------- header / macro snippets --------
            header_block, macro_block, example_block = self._get_context_snippets(example_type)

            enhanced_prompt = (
                header_block + "\n" + macro_block + "\n" + example_block + "\n" +
                self.context_generator._create_complete_prompt(diverse_instruction, category, validation_result)
            )
        else:
            # Fallback to original enhanced prompt
            enhanced_prompt = f"""
+{self._get_context_snippets_raw(example_type)}
+
 You are generating diverse OoT romhacking training data. You MUST follow authentic decompilation patterns exactly while creating varied and interesting content.
@@
 """
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=dynamic_temperature,  # Use dynamic temperature
                messages=[{"role": "user", "content": enhanced_prompt}]
            )
            
            # Handle different types of content blocks
            content_block = response.content[0]
            if content_block.type == 'text':
                raw_response = content_block.text
            else:
                raw_response = str(content_block)
            return self._parse_response(raw_response, example_type)
            
        except Exception as e:
            print(f"Generation failed: {e}")
            return None
    
    def _get_real_oot_patterns(self, example_type: ExampleType) -> str:
        """Get real OoT patterns based on actual source code"""
        
        if example_type == ExampleType.ACTOR_CREATION:
            return """
REAL OoT ENEMY PATTERNS (from actual En_* files):
- Use Actor_WorldDistXYZToActor for distance checking (like En_Dodongo)
- Implement state machines with s16 actionState (like En_Karebaba)
- Use Collider_InitCylinder for collision detection (like En_Torch)
- Implement proper attack patterns and damage systems
- Use Actor_PlaySfx for sound effects

REAL OoT NPC PATTERNS (from actual En_* files):
- Use Actor_OfferTalk for dialogue interactions (like En_Zo)
- Implement NpcInteractInfo for complex interactions
- Use Actor_IsFacingPlayer for player detection
- Implement proper dialogue state management
- Use Player_GetHeight for player interaction

REAL OoT ITEM PATTERNS (from z_en_item00.h):
- Use EnItem00 for most collectibles (hearts, rupees, keys)
- Use ITEM00_* constants: ITEM00_HEART_PIECE, ITEM00_RUPEE_BLUE, etc.
- Implement proper item spawning with Actor_Spawn
- Use Item_DropCollectible for authentic item creation
- Implement proper item collection logic

REAL OoT OBJECT PATTERNS (from Obj_* files):
- Use proper door and switch systems (like Obj_Switch)
- Implement moving platforms with Vec3f paths
- Use collision detection for mechanical interactions
- Implement proper state management for mechanisms
- Use authentic mechanical sound effects

REAL OoT BACKGROUND PATTERNS (from Bg_* files):
- Use proper lighting and weather systems
- Implement day/night cycle effects
- Use environmental collision detection
- Implement proper environmental interactions
- Use authentic environmental sound effects
"""
        
        elif example_type == ExampleType.ANIMATION_SYSTEM:
            return """
REAL OoT ANIMATION PATTERNS (from z_actor.c):
- Use SkelAnime_Init for skeleton initialization
- Implement Animation_Change for animation transitions
- Use SkelAnime_Update for animation updates
- Implement proper animation state management
- Use authentic animation timing and blending
"""
        
        elif example_type == ExampleType.COLLISION_SYSTEM:
            return """
REAL OoT COLLISION PATTERNS (from z_collision_check.c):
- Use Collider_InitCylinder for cylinder collision
- Implement Collider_UpdateCylinder for updates
- Use CollisionCheck_SetAC/OC for collision detection
- Implement proper collision response systems
- Use authentic collision flags and materials
"""
        
        elif example_type == ExampleType.INTERACTION_SYSTEM:
            return """
REAL OoT INTERACTION PATTERNS (from z_actor.c):
- Use Actor_OfferTalk for dialogue systems
- Implement proper interaction state management
- Use Actor_IsFacingPlayer for player detection
- Implement proper interaction feedback
- Use authentic interaction sound effects
"""
        
        elif example_type == ExampleType.EFFECT_SYSTEM:
            return """
REAL OoT EFFECT PATTERNS (from Oceff_* files):
- Use Effect_Add for particle effects
- Implement proper effect lifecycle management
- Use authentic effect parameters and timing
- Implement proper effect cleanup
- Use authentic effect sound integration
"""
        
        else:
            return """
REAL OoT GENERAL PATTERNS (from actual decompilation):
- Use proper memory management with ZELDA_ARENA_MALLOC
- Implement authentic error handling patterns
- Use proper mathematical functions (Math_SinS, Math_CosS)
- Implement authentic timing and frame counting
- Use proper flag systems for state management
"""
    
    def _get_dynamic_examples(self, example_type: ExampleType) -> str:
        """Get real examples from the source code based on example type"""
        if not self.source_analyzer:
            return ""
        
        examples = []
        
        if example_type == ExampleType.ACTOR_CREATION:
            # Get real actor initialization examples
            actor_example = self.source_analyzer.get_authentic_example("actor_init")
            if actor_example:
                examples.append(f"""
REAL ACTOR INITIALIZATION EXAMPLE (from {actor_example['file']}):
```c
{actor_example['code']}
```
""")
            
            # Get real collision initialization examples
            collision_example = self.source_analyzer.get_authentic_example("collider_init") 
            if collision_example:
                examples.append(f"""
REAL COLLISION SETUP EXAMPLE (from {collision_example['file']}):
```c
{collision_example['code']}
```
""")
        
        elif example_type == ExampleType.CODE_EXPLANATION:
            # Get real struct definitions
            if self.source_analyzer.real_structs:
                struct_name = random.choice(list(self.source_analyzer.real_structs.keys()))
                struct_def = self.source_analyzer.real_structs[struct_name]
                examples.append(f"""
REAL STRUCT EXAMPLE (from {struct_def['file']}):
```c
{struct_def['full_definition']}
```
""")
        
        elif example_type == ExampleType.FEATURE_IMPLEMENTATION:
            # Get real constants for features
            item_constants = self.source_analyzer.get_real_constants_by_prefix("ITEM00_")
            if item_constants:
                const_list = list(item_constants.items())[:10]
                examples.append(f"""
REAL ITEM CONSTANTS (from source):
```c
{chr(10).join([f'#define {name} {value}' for name, value in const_list])}
```
""")
        
        return "\n".join(examples) if examples else ""
    
    def _enhance_with_real_patterns(self, example: TrainingExample) -> TrainingExample:
        """Enhance examples with real patterns from source code"""
        if not self.source_analyzer:
            return example
        
        # Replace placeholder function names with real ones
        if "FuncName" in example.output:
            real_funcs = list(self.source_analyzer.real_functions.keys())
            actor_funcs = [f for f in real_funcs if "_Init" in f or "_Update" in f]
            if actor_funcs:
                replacement_func = random.choice(actor_funcs)
                base_name = replacement_func.split("_")[0]
                example.output = example.output.replace("FuncName", base_name)
        
        # Replace placeholder struct names with real ones  
        if "StructName" in example.output:
            actor_structs = [s for s in self.source_analyzer.real_structs.keys() 
                           if s.startswith("En") and "Actor" not in s]
            if actor_structs:
                replacement_struct = random.choice(actor_structs)
                example.output = example.output.replace("StructName", replacement_struct)
        
        return example
    
    def _map_example_type_to_category(self, example_type: ExampleType) -> str:
        """Map ExampleType to validation category"""
        mapping = {
            ExampleType.ACTOR_CREATION: "enemy",  # Actor creation can be enemy, npc, or object
            ExampleType.ANIMATION_SYSTEM: "object",  # Animation systems are typically objects/mechanics
            ExampleType.COLLISION_SYSTEM: "object",  # Collision systems are mechanics
            ExampleType.INTERACTION_SYSTEM: "npc",   # Interaction systems are typically NPC-related
            ExampleType.EFFECT_SYSTEM: "object",     # Effect systems are mechanics
            ExampleType.SOUND_SYSTEM: "object",      # Sound systems are mechanics
            ExampleType.AI_BEHAVIOR: "enemy",        # AI behavior is typically enemy-related
            ExampleType.ENVIRONMENTAL: "object",     # Environmental systems are objects/mechanics
            ExampleType.COMBAT_SYSTEM: "enemy",      # Combat systems are enemy-related
            ExampleType.PUZZLE_SYSTEM: "object",     # Puzzle systems are objects/mechanics
            ExampleType.UI_SYSTEM: "object",         # UI systems are objects/mechanics
            ExampleType.MEMORY_MANAGEMENT: "object", # Memory management is mechanics
            ExampleType.OPTIMIZATION: "object",      # Optimization is mechanics
            ExampleType.DEBUGGING_TOOLS: "object",   # Debugging tools are mechanics
            ExampleType.CUSTOM_MECHANICS: "object",  # Custom mechanics are objects
            ExampleType.CODE_EXPLANATION: "object",  # Code explanations are generic
            ExampleType.FEATURE_IMPLEMENTATION: "object", # Feature implementations are objects
            ExampleType.DEBUGGING_HELP: "object"     # Debugging help is generic
        }
        return mapping.get(example_type, "object")
    
    def _parse_response(self, raw_response: str, example_type: ExampleType) -> Optional[TrainingExample]:
        """Parse Claude's response into a TrainingExample object using multiple robust parsing strategies"""
        
        # Strategy 1: Try standard JSON parsing first
        try:
            # Look for JSON block
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                return TrainingExample(
                    example_type=example_type,
                    instruction=data.get("instruction", ""),
                    input=data.get("input") if data.get("input") != "null" else None,
                    output=data.get("output", ""),
                    metadata={"generation_method": "json_block_parsing"},
                    quality_score=0.0
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 1.5: Try parsing as raw JSON (no code block)
        try:
            # Check if the response is just raw JSON
            stripped = raw_response.strip()
            if stripped.startswith('{') and stripped.endswith('}'):
                data = json.loads(stripped)
                print(f"[DEBUG] Raw JSON parsing successful - Output length: {len(data.get('output', ''))}")
                return TrainingExample(
                    example_type=example_type,
                    instruction=data.get("instruction", ""),
                    input=data.get("input") if data.get("input") != "null" else None,
                    output=data.get("output", ""),
                    metadata={"generation_method": "raw_json_parsing"},
                    quality_score=0.0
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Strategy 2: Try to extract fields using regex patterns that handle unescaped content
        print("[DEBUG] Attempting robust field extraction...")
        
        # More flexible regex patterns that can handle unescaped content
        instruction_patterns = [
            r'"instruction":\s*"([^"]+)"',  # Standard quoted string
            r'"instruction":\s*"([^"]*(?:\\.[^"]*)*)"',  # Handle escaped quotes  
        ]
        
        output_patterns = [
            # Handle code blocks properly - match everything until the closing quote
            r'"output":\s*"((?:[^"\\]|\\.)*)"\s*[,}]',  # Comprehensive pattern for quoted content with escapes
            r'"output":\s*"([^"]*(?:\\.[^"]*)*)"',  # Handle escaped quotes
            r'"output":\s*```([^`]+)```',  # Unescaped code block (fallback)
            r'"output":\s*```c\s*([^`]+)```',  # Specific C code block (fallback)
        ]
        
        input_patterns = [
            r'"input":\s*(null|"[^"]*")',  # null or quoted string
        ]
        
        # Try different extraction strategies
        instruction = None
        output = None
        input_text = None
        
        # Extract instruction
        for pattern in instruction_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                instruction = match.group(1).strip()
                break
        
        # Extract output - try multiple strategies
        for pattern in output_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                output = match.group(1).strip()
                # Decode escaped characters (like \n -> newlines)
                try:
                    output = output.encode().decode('unicode_escape')
                except:
                    pass  # If decoding fails, use as-is
                
                # If this was a code block, add proper formatting
                if not output.startswith('```') and ('void ' in output or '#include' in output or 'typedef' in output):
                    output = f"```c\n{output}\n```"
                break
        
        # Extract input
        for pattern in input_patterns:
            match = re.search(pattern, raw_response, re.DOTALL)
            if match:
                input_content = match.group(1).strip()
                if input_content != "null":
                    input_text = input_content.strip('"')
                break
        
        # Strategy 3: If structured extraction worked, create example
        if instruction and output:
            print(f"[DEBUG] Successfully extracted - Instruction: {len(instruction)} chars, Output: {len(output)} chars")
            print(f"[DEBUG] Output preview: {output[:100]}...")
            return TrainingExample(
                example_type=example_type,
                instruction=instruction,
                input=input_text,
                output=output,
                metadata={"extraction_method": "robust_regex"},
                quality_score=0.0
            )
        
        # Strategy 4: Manual parsing fallback for completely malformed responses
        print("[DEBUG] Attempting manual parsing fallback...")
        
        # Try to find JSON-like structure manually
        lines = raw_response.split('\n')
        current_field = None
        current_content = []
        parsed_data = {}
        
        for line in lines:
            line = line.strip()
            
            # Check for field start
            if line.startswith('"instruction":'):
                current_field = "instruction"
                content = line.split(':', 1)[1].strip().strip('"').strip(',')
                if content:
                    parsed_data[current_field] = content
                current_content = []
            elif line.startswith('"input":'):
                current_field = "input"
                content = line.split(':', 1)[1].strip().strip('"').strip(',')
                if content and content != "null":
                    parsed_data[current_field] = content
                current_content = []
            elif line.startswith('"output":'):
                current_field = "output"
                content = line.split(':', 1)[1].strip()
                if content.startswith('```'):
                    # This is a code block, start collecting
                    current_content = [content]
                else:
                    # Regular quoted content
                    content = content.strip('"').strip(',')
                    if content:
                        parsed_data[current_field] = content
                    current_content = []
            elif current_field and line:
                # Continue collecting multi-line content
                current_content.append(line)
            elif current_field and current_content:
                # End of field, finalize content
                if current_field == "output" and current_content:
                    parsed_data[current_field] = '\n'.join(current_content)
                current_field = None
                current_content = []
        
        # Finalize any remaining content
        if current_field and current_content:
            parsed_data[current_field] = '\n'.join(current_content)
        
        # Create example from manual parsing
        if parsed_data.get("instruction") and parsed_data.get("output"):
            print(f"[DEBUG] Manual parsing successful - {len(parsed_data)} fields extracted")
            return TrainingExample(
                example_type=example_type,
                instruction=parsed_data["instruction"],
                input=parsed_data.get("input"),
                output=parsed_data["output"],
                metadata={"extraction_method": "manual_parsing", "raw_response": raw_response[:500]},
                quality_score=0.0
            )
        
        # Strategy 5: Last resort - try to find any usable content
        print("[DEBUG] Last resort parsing...")
        
        # Look for any instruction-like content
        instruction_fallback = None
        output_fallback = None
        
        # Search for common patterns
        create_match = re.search(r'(Create|Implement|Explain|Debug).*?(?=\n|$)', raw_response, re.IGNORECASE)
        if create_match:
            instruction_fallback = create_match.group(0).strip()
        
        # Look for code blocks
        code_match = re.search(r'```c?\s*\n(.*?)\n```', raw_response, re.DOTALL)
        if code_match:
            output_fallback = f"```c\n{code_match.group(1).strip()}\n```"
        elif re.search(r'```', raw_response):
            # There's a code block but it's malformed
            start = raw_response.find('```')
            if start != -1:
                remaining = raw_response[start+3:]
                end = remaining.find('```')
                if end != -1:
                    code_content = remaining[:end].strip()
                    output_fallback = f"```c\n{code_content}\n```"
        
        if instruction_fallback and output_fallback:
            print(f"[DEBUG] Fallback extraction successful")
            return TrainingExample(
                example_type=example_type,
                instruction=instruction_fallback,
                input=None,
                output=output_fallback,
                metadata={"extraction_method": "fallback", "warning": "Extracted from malformed response"},
                quality_score=0.0
            )
        
        # Complete failure
        print(f"[DEBUG] Complete parsing failure. Raw response preview:\n{raw_response[:200]}...")
        return None

    def _multi_pass_validation(self, example: TrainingExample) -> TrainingExample:
        """Multi-pass validation with progressive correction"""
        
        # Pass 0: Enhance with real patterns from source code
        example = self._enhance_with_real_patterns(example)
        
        # Pass 1: Function signature validation against real functions
        signature_issues = self.validator.validate_function_signatures(example.output)
        if signature_issues:
            example.validation_notes += f"Signature issues: {len(signature_issues)}. "
            # Apply mandatory corrections
            example.output = self.validator.apply_mandatory_corrections(example.output)
        
        # Pass 2: Architectural validation against real patterns
        arch_issues = self.validator.validate_architectural_authenticity(example.output, example.instruction)
        if arch_issues:
            example.validation_notes += f"Architecture issues: {len(arch_issues)}. "
        
        # Pass 3: Additional source-based validation
        if self.source_analyzer:
            source_issues = self.source_analyzer.validate_against_real_source(example.output)
            if source_issues:
                example.validation_notes += f"Source validation issues: {len(source_issues)}. "
        
        # Pass 4: Final quality scoring
        example.quality_score = self._calculate_quality_score(example)
        
        return example

    def _calculate_quality_score(self, example: TrainingExample) -> float:
        """Enhanced quality scoring with authenticity focus"""
        score = 5.0
        
        # Basic content quality
        if len(example.instruction) > 20:
            score += 0.5
        if len(example.output) > 200:
            score += 1.0
        if "```c" in example.output:
            score += 1.0
            
        # Real function usage bonus
        func_pattern = r'(\w+)\s*\('
        total_functions = 0
        real_functions = 0
        
        for match in re.finditer(func_pattern, example.output):
            func_name = match.group(1)
            if (func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and not func_name.isupper() and len(func_name) > 3):
                total_functions += 1
                if func_name in self.validator.authentic_function_signatures:
                    real_functions += 1
                    
        if total_functions > 0:
            real_func_ratio = real_functions / total_functions
            score += real_func_ratio * 2.0  # Up to +2.0 for real functions
            
        # Authenticity pattern bonuses
        authentic_patterns = [
            "Actor* thisx, PlayState* play",
            "world.pos", 
            "ActorProfile",
            "Collider_InitCylinder",
            "ACTORCAT_",
            "EnItem00",  # For collectibles
        ]
        
        for pattern in authentic_patterns:
            if pattern in example.output:
                score += 0.3
                
        # Heavy penalties for non-authentic patterns
        if "GlobalContext" in example.output:
            score -= 3.0
        if "PlayState* play, Actor* thisx" in example.output:
            score -= 3.0
        if re.search(r"\.pos\.", example.output):  # Direct pos access
            score -= 1.0
            
        return max(0.0, min(10.0, score))

    def generate_dataset(self, num_examples: int = 50, output_file: str = "authentic_oot_training.jsonl") -> None:
        """Generate dataset with strict quality control + diversity injection"""
        
        examples = []
        example_types = list(ExampleType)
        rejected_count = 0
        
        # Enhanced example type distribution for better diversity
        type_weights = {
            ExampleType.ACTOR_CREATION: 0.25,      # Core actor creation
            ExampleType.ANIMATION_SYSTEM: 0.08,     # Animation systems
            ExampleType.COLLISION_SYSTEM: 0.08,     # Collision systems  
            ExampleType.INTERACTION_SYSTEM: 0.08,   # Interaction systems
            ExampleType.EFFECT_SYSTEM: 0.08,        # Effect systems
            ExampleType.SOUND_SYSTEM: 0.06,         # Sound systems
            ExampleType.AI_BEHAVIOR: 0.08,          # AI behavior systems
            ExampleType.ENVIRONMENTAL: 0.06,        # Environmental systems
            ExampleType.COMBAT_SYSTEM: 0.06,        # Combat systems
            ExampleType.PUZZLE_SYSTEM: 0.06,        # Puzzle systems
            ExampleType.CUSTOM_MECHANICS: 0.05,     # Custom mechanics
            ExampleType.CODE_EXPLANATION: 0.03,     # Code explanations
            ExampleType.FEATURE_IMPLEMENTATION: 0.03, # Feature implementations
            ExampleType.DEBUGGING_HELP: 0.02,       # Debugging help
            ExampleType.UI_SYSTEM: 0.02,            # UI systems
            ExampleType.MEMORY_MANAGEMENT: 0.02,    # Memory management
            ExampleType.OPTIMIZATION: 0.02,         # Optimization
            ExampleType.DEBUGGING_TOOLS: 0.02,      # Debugging tools
        }
        
        # Complexity distribution for better variety
        complexity_weights = {
            "basic": 0.2,
            "intermediate": 0.5, 
            "advanced": 0.3
        }
        
        print(f"Generating {num_examples} diverse authentic examples...")
        print(f"Using {len(self.validator.authentic_function_signatures)} real OoT functions for validation")
        print(f"Target distribution: {len(type_weights)} example types with weighted selection")
        
        # Track diversity metrics
        diversity_metrics = {
            "actor_categories": {cat.value: 0 for cat in ActorCategory},
            "example_types": {t.value: 0 for t in ExampleType},
            "complexities": {"basic": 0, "intermediate": 0, "advanced": 0},
            "unique_scenarios": set()
        }
        
        for i in range(num_examples * 3):  # Generate more to account for rejections and diversity
            if len(examples) >= num_examples:
                break
                
            # Weighted selection for example type
            available_types = [t for t in example_types if t in type_weights]
            type_weights_list = [type_weights.get(t, 0.01) for t in available_types]
            example_type = random.choices(available_types, weights=type_weights_list, k=1)[0]
            
            # Weighted selection for complexity
            complexity = random.choices(list(complexity_weights.keys()), 
                                     weights=list(complexity_weights.values()), k=1)[0]
            
            print(f"Generating example {len(examples)+1}/{num_examples}: {example_type.value} ({complexity})")
            
            try:
                example = self.generate_training_example(example_type, complexity)
                
                # Enhanced acceptance criteria with diversity bonus
                base_quality = example.quality_score >= 7.0
                base_authenticity = example.authenticity_score >= 7.0
                base_length = len(example.output) > 100
                
                # Diversity bonus: boost score for underrepresented categories
                diversity_bonus = self._calculate_diversity_bonus(example, diversity_metrics)
                
                if base_quality and base_authenticity and base_length:
                    # Apply diversity bonus
                    final_score = example.quality_score + diversity_bonus
                    
                    if final_score >= 7.0:
                        examples.append(example)
                        
                        # Update diversity metrics
                        self._update_diversity_metrics(example, diversity_metrics)
                        
                        # Update temperature manager
                        self.temperature_manager.update_usage(example, diversity_metrics)
                        
                        print(f"  ✓ ACCEPTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                    else:
                        rejected_count += 1
                        print(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                else:
                    rejected_count += 1
                    print(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
                    
            except Exception as e:
                print(f"  ✗ ERROR: {e}")
                rejected_count += 1
                
            time.sleep(0.5)  # Rate limiting
        
        # Save results with enhanced metadata
        self._save_dataset_with_diversity(examples, output_file, diversity_metrics)
        
        print(f"\nFINAL RESULTS:")
        print(f"✓ Accepted: {len(examples)} examples")
        print(f"✗ Rejected: {rejected_count} examples")
        print(f"📊 Acceptance rate: {len(examples)/(len(examples)+rejected_count)*100:.1f}%")
        print(f"🎯 Diversity achieved:")
        print(f"   - Actor categories: {len([c for c in diversity_metrics['actor_categories'].values() if c > 0])}/14")
        print(f"   - Example types: {len([t for t in diversity_metrics['example_types'].values() if t > 0])}/{len(ExampleType)}")
        print(f"   - Unique scenarios: {len(diversity_metrics['unique_scenarios'])}")
        print(f"💾 Saved to: {output_file}")

    def _calculate_diversity_bonus(self, example: TrainingExample, diversity_metrics: Dict) -> float:
        """Calculate diversity bonus for underrepresented categories"""
        bonus = 0.0
        
        # Check actor category diversity
        for category, keywords in {
            ActorCategory.ENEMY: ["enemy", "dodongo", "karebaba", "wallmaster", "stalfos"],
            ActorCategory.NPC: ["npc", "zora", "goron", "kokiri", "hylian", "gerudo"],
            ActorCategory.ITEM: ["item", "heart", "rupee", "bomb", "arrow", "bottle"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }.items():
            if any(keyword.lower() in example.instruction.lower() for keyword in keywords):
                category_count = diversity_metrics['actor_categories'][category.value]
                if category_count < 2:  # Boost underrepresented categories
                    bonus += 1.0
                break
        
        # Check example type diversity
        type_count = diversity_metrics['example_types'][example.example_type.value]
        if type_count < 2:  # Boost underrepresented types
            bonus += 0.5
        
        # Check scenario uniqueness
        if example.instruction not in diversity_metrics['unique_scenarios']:
            bonus += 0.3
        
        return bonus

    def _update_diversity_metrics(self, example: TrainingExample, diversity_metrics: Dict) -> None:
        """Update diversity tracking metrics"""
        
        # Update actor category counts
        for category, keywords in {
            ActorCategory.ENEMY: ["enemy", "dodongo", "karebaba", "wallmaster", "stalfos"],
            ActorCategory.NPC: ["npc", "zora", "goron", "kokiri", "hylian", "gerudo"],
            ActorCategory.ITEM: ["item", "heart", "rupee", "bomb", "arrow", "bottle"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }.items():
            if any(keyword.lower() in example.instruction.lower() for keyword in keywords):
                diversity_metrics['actor_categories'][category.value] += 1
                break
        
        # Update example type counts
        diversity_metrics['example_types'][example.example_type.value] += 1
        
        # Update unique scenarios
        diversity_metrics['unique_scenarios'].add(example.instruction)

    def _save_dataset_with_diversity(self, examples: List[TrainingExample], output_file: str, diversity_metrics: Dict) -> None:
        """Save dataset with enhanced diversity metadata"""
        
        # Training data format
        with open(output_file, 'w') as f:
            for example in examples:
                record = {"instruction": example.instruction, "output": example.output}
                if example.input:
                    record["input"] = example.input
                f.write(json.dumps(record) + '\n')
        
        # Enhanced analysis with diversity metrics
        metadata = {
            "total_examples": len(examples),
            "average_quality": sum(e.quality_score for e in examples) / len(examples) if examples else 0.0,
            "average_authenticity": sum(e.authenticity_score for e in examples) / len(examples) if examples else 0.0,
            "type_distribution": {t.value: sum(1 for e in examples if e.example_type == t) for t in ExampleType},
            "real_functions_used": len(self.validator.authentic_function_signatures),
            "diversity_metrics": {
                "actor_categories": diversity_metrics['actor_categories'],
                "example_types": diversity_metrics['example_types'],
                "unique_scenarios": len(diversity_metrics['unique_scenarios']),
                "category_coverage": len([c for c in diversity_metrics['actor_categories'].values() if c > 0]),
                "type_coverage": len([t for t in diversity_metrics['example_types'].values() if t > 0])
            },
            "generation_stats": self.generation_stats,
            "validation_summary": [
                {
                    "instruction": e.instruction[:100] + "..." if len(e.instruction) > 100 else e.instruction,
                    "type": e.example_type.value,
                    "quality_score": e.quality_score,
                    "authenticity_score": e.authenticity_score,
                    "validation_notes": e.validation_notes
                } for e in examples
            ]
        }
        
        metadata_file = output_file.replace('.jsonl', '_diversity_analysis.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _get_context_snippets(self, example_type: ExampleType) -> Tuple[str, str, str]:
        """Get header, macro, and example snippets from support.oot_context_cache"""
        
        # Get header snippet based on example type
        if example_type in [ExampleType.ACTOR_CREATION, ExampleType.AI_BEHAVIOR]:
            header_block = get_snippet("actor")
        elif example_type in [ExampleType.COLLISION_SYSTEM, ExampleType.INTERACTION_SYSTEM]:
            header_block = get_snippet("collision")
        elif example_type in [ExampleType.ANIMATION_SYSTEM]:
            header_block = get_snippet("animation")
        else:
            header_block = get_snippet("actor")  # Default to actor header
        
        # Get macro pack based on example type
        if example_type in [ExampleType.COLLISION_SYSTEM]:
            macro_block = get_macro_pack("collider")
        elif example_type in [ExampleType.ANIMATION_SYSTEM]:
            macro_block = get_macro_pack("animation")
        else:
            macro_block = get_macro_pack("collider")  # Default to collider macros
        
        # Get example based on category
        if example_type in [ExampleType.ACTOR_CREATION, ExampleType.AI_BEHAVIOR]:
            example_block = get_example("actor")
        else:
            example_block = get_example("actor")  # Default to actor example
        
        return header_block, macro_block, example_block
    
    def _get_context_snippets_raw(self, example_type: ExampleType) -> str:
        """Get raw context snippets as a single string"""
        header_block, macro_block, example_block = self._get_context_snippets(example_type)
        
        return f"""
AUTHENTIC OoT HEADER SNIPPETS:
{header_block}

AUTHENTIC OoT MACRO SNIPPETS:
{macro_block}

AUTHENTIC OoT EXAMPLE SNIPPETS:
{example_block}
"""

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

class RealOoTScenarioTemplate:
    """Improved OoT scenario templates with natural, diverse instructions"""
    
    def __init__(self):
        # Import the new scenario generator and validator
        try:
            from support.improved_scenario_generator import ImprovedOoTScenarioGenerator
            from support.validate_and_enhance_scenarios import OoTPatternValidator
            self.scenario_generator = ImprovedOoTScenarioGenerator()
            self.validator = OoTPatternValidator()
            self.use_improved_generator = True
            print("✅ Using improved scenario generator with validation")
        except ImportError:
            print("⚠️  Improved scenario generator not available, using fallback scenarios")
            self.use_improved_generator = False
    
    def get_enemy_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_enemy_scenarios(20)
        else:
            return self._get_fallback_enemy_scenarios()
    
    def _get_fallback_enemy_scenarios(self) -> List[str]:
        return [
            "Create a skeletal warrior that teleports behind the player for surprise attacks",
            "Design a fire-breathing dragon that creates defensive barriers when health is low",
            "Implement a crystal golem enemy with the ability to summon smaller minions to assist in battle",
            "Build a shadow assassin that changes attack patterns based on player actions when the player approaches",
            "Create a hostile ice elemental that uses environmental hazards as weapons as its main attack",
            "Design an enemy forest guardian that becomes more aggressive as the fight progresses",
            "How would you implement a stone gargoyle that can split into multiple smaller enemies when defeated?",
            "What's the best way to create a lightning spirit that absorbs elemental attacks to grow stronger?",
            "Explain how to build a poison spider with the ability to phase through walls to ambush the player",
            "Walk me through creating an armored knight that can mirror the player's equipped weapon and abilities",
            "Create a flying demon that has multiple phases with different abilities with state-based AI",
            "Design a water serpent that can only be damaged in specific ways using multiple attack patterns",
            "Implement a lava beast enemy with the ability to control the battlefield lighting and visibility",
            "Build a wind wraith that manipulates gravity in the surrounding area when the player approaches",
            "Create a hostile earth titan that creates illusions to confuse the player as its main attack",
            "Design an enemy void stalker that steals and uses the player's items temporarily",
            "How would you implement a crystal guardian that regenerates health by consuming nearby objects?",
            "What's the best way to create a shadow demon that coordinates attacks with other enemies?",
            "Explain how to build a flame spirit with the ability to adapt to the player's combat style",
            "Walk me through creating a stone beast that uses hit-and-run tactics to avoid damage"
        ]
    
    def get_npc_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_npc_scenarios(20)
        else:
            return self._get_fallback_npc_scenarios()
    
    def _get_fallback_npc_scenarios(self) -> List[str]:
        return [
            "Create a merchant NPC that provides hints about nearby secrets",
            "Design a blacksmith that can offer to upgrade the player's equipment",
            "I want to make a scholar that shares local legends and lore with the player",
            "How do I create a guard NPC that gives quests based on player progress?",
            "Build a farmer character that teaches new skills or abilities when approached",
            "Create a healer NPC that trades rare items for specific materials",
            "Design a sage that can provide temporary buffs or services",
            "I need a craftsman that can warns about upcoming dangers",
            "How would you implement a storyteller that offers transportation to other areas?",
            "Build a guide character that maintains a mini-game or challenge when approached",
            "Create a merchant NPC that provides item repair and enhancement services",
            "Design a innkeeper that can magical enchantments for equipment",
            "I want to make a collector that information about dungeon layouts with the player",
            "How do I create a trainer NPC that temporary companion assistance?",
            "Build a cook character that skill training and tutorials when approached",
            "Create a librarian NPC that rare item trading and exchange",
            "Design a musician that can quest coordination and tracking",
            "I need a sage that can fast travel between locations",
            "How would you implement a healer that inventory management and storage?",
            "Build a scholar character that character customization options when approached"
        ]
    
    def get_item_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_item_scenarios(15)
        else:
            return self._get_fallback_item_scenarios()
    
    def _get_fallback_item_scenarios(self) -> List[str]:
        return [
            "Build a magical sword item that reveals hidden passages and secrets when used",
            "Design a enchanted bow that can allows temporary flight or levitation",
            "I want to implement a crystal shield that creates protective barriers against attacks",
            "How do I create a power gauntlet with the ability to transforms the player's appearance or abilities?",
            "Build a stealth cloak item that provides enhanced vision in dark areas when used",
            "Create a healing potion that manipulates time flow in small areas",
            "Design a puzzle key that can controls elemental forces like fire or ice",
            "I need a transformation mask that grants telepathic communication with NPCs",
            "How would you implement an ancient relic that opens dimensional portals for fast travel?",
            "Build a utility tool item that amplifies the player's magical abilities when used",
            "Create a elemental stone that reveals hidden passages and secrets with simple effects",
            "Design a consumable scroll that can allows temporary flight or levitation using resource management",
            "I want to implement a magical sword that creates protective barriers against attacks for combat enhancement",
            "How do I create a enchanted bow with the ability to transforms the player's appearance or abilities?",
            "Build a crystal shield item that provides enhanced vision in dark areas when used with conditional effects"
        ]
    
    def get_object_scenarios(self) -> List[str]:
        if self.use_improved_generator:
            return self.scenario_generator.generate_object_scenarios(15)
        else:
            return self._get_fallback_object_scenarios()
    
    def _get_fallback_object_scenarios(self) -> List[str]:
        return [
            "Build a pressure switch object that activates when multiple conditions are met when activated",
            "Design a rotating platform mechanism that moves in complex patterns to create platforms",
            "I need a sliding door that can opens passages based on player inventory",
            "How would you implement a magical portal that responds to specific musical sequences?",
            "Build a crystal mechanism object that changes the room's layout dynamically when activated",
            "Create a ancient statue that creates temporary bridges across gaps",
            "Design a mechanical lift mechanism that manipulates light and shadow patterns",
            "I need a energy conduit that can generates force fields and barriers",
            "How would you implement a puzzle pedestal that controls water levels and flow?",
            "Build a temporal gate object that synchronizes with other mechanisms when activated",
            "Create a elemental altar that activates when multiple conditions are met with simple activation",
            "Design a gravity well mechanism that moves in complex patterns to create platforms using timing mechanisms",
            "I need a pressure switch that can opens passages based on player inventory",
            "How would you implement a rotating platform that responds to specific musical sequences?",
            "Build a sliding door object that changes the room's layout dynamically when activated with complex sequences"
        ]
    
    @staticmethod
    def get_background_scenarios() -> List[str]:
        return [
            "Create a Water Temple water level system",
            "Implement a Fire Temple lava flow mechanics",
            "Create a Forest Temple moving platforms",
            "Make a Shadow Temple darkness and light mechanics",
            "Create a Spirit Temple sand flow and time mechanics",
            "Implement a Deku Tree web and platform system",
            "Create a Jabu-Jabu's Belly water and bubble mechanics",
            "Make a Dodongo's Cavern rock and lava system",
            "Create a Inside the Deku Tree web and platform mechanics",
            "Implement a Ganon's Castle tower and barrier system"
        ]
    
    @staticmethod
    def get_effect_scenarios() -> List[str]:
        return [
            "Create a Sun Song effect that changes time of day",
            "Implement a Song of Storms effect that creates rain",
            "Create a Song of Time effect that advances time",
            "Make a Zelda's Lullaby effect that opens doors",
            "Create a Saria's Song effect that calls for help",
            "Implement a Epona's Song effect that calls the horse",
            "Create a Song of Healing effect that cures curses",
            "Make a Requiem of Spirit effect that warps to desert",
            "Create a Nocturne of Shadow effect that warps to shadow temple",
            "Implement a Prelude of Light effect that warps to temple of time"
        ]
    
    @staticmethod
    def get_player_scenarios() -> List[str]:
        return [
            "Create a Hookshot targeting and grappling system",
            "Implement a Boomerang throwing and returning mechanics",
            "Create a Bow and arrow aiming and shooting system",
            "Make a Bomb throwing and explosion mechanics",
            "Create a Magic spell casting and mana system",
            "Implement a Sword combat with different attack patterns",
            "Create a Shield blocking and deflection mechanics",
            "Make a Ocarina playing and song system",
            "Create a Transformation mask mechanics (Deku, Goron, Zora)",
            "Implement a Equipment and inventory management system"
        ]
    
    @staticmethod
    def get_misc_scenarios() -> List[str]:
        return [
            "Create a Fishing system with different fish types",
            "Implement a Horse riding and Epona mechanics",
            "Create a Owl Statue save point system",
            "Make a Gossip Stone hint system",
            "Create a Treasure Chest opening and item collection",
            "Implement a Rupee collection and wallet system",
            "Create a Heart Piece collection and health upgrade",
            "Make a Skulltula token collection system",
            "Create a Gold Skulltula reward system",
            "Implement a Trading sequence with various NPCs"
        ]

class DynamicTemperatureManager:
    """Manages dynamic temperature based on diversity needs"""
    
    def __init__(self):
        self.base_temperature = 0.7
        self.min_temperature = 0.3
        self.max_temperature = 0.9
        self.category_usage = {cat.value: 0 for cat in ActorCategory}
        self.recent_examples = []
        self.max_recent = 10
        
    def get_dynamic_temperature(self, example_type: ExampleType, complexity: str, 
                              diversity_metrics: Dict) -> float:
        """Calculate dynamic temperature based on diversity needs"""
        
        # Start with base temperature
        temp = self.base_temperature
        
        # Adjust based on category diversity
        category_coverage = len([c for c in diversity_metrics['actor_categories'].values() if c > 0])
        total_categories = len(ActorCategory)
        coverage_ratio = category_coverage / total_categories
        
        if coverage_ratio < 0.5:  # Low diversity - increase temperature
            temp += 0.2
        elif coverage_ratio > 0.8:  # High diversity - decrease temperature for consistency
            temp -= 0.1
        
        # Adjust based on recent repetition
        if len(self.recent_examples) >= 3:
            recent_types = [ex['type'] for ex in self.recent_examples[-3:]]
            if len(set(recent_types)) == 1:  # All same type - increase temperature
                temp += 0.15
        
        # Adjust based on complexity
        if complexity == "advanced":
            temp += 0.1  # More variety for complex examples
        elif complexity == "basic":
            temp -= 0.05  # Less variety for basic examples
        
        # Adjust based on example type
        if example_type in [ExampleType.ACTOR_CREATION, ExampleType.CUSTOM_MECHANICS]:
            temp += 0.1  # More variety for creative examples
        elif example_type in [ExampleType.CODE_EXPLANATION, ExampleType.DEBUGGING_HELP]:
            temp -= 0.05  # Less variety for explanatory examples
        
        # Clamp to valid range
        temp = max(self.min_temperature, min(self.max_temperature, temp))
        
        return temp
    
    def update_usage(self, example: TrainingExample, diversity_metrics: Dict):
        """Update usage tracking for dynamic temperature calculation"""
        
        # Update recent examples
        self.recent_examples.append({
            'type': example.example_type.value,
            'instruction': example.instruction[:50]
        })
        
        # Keep only recent examples
        if len(self.recent_examples) > self.max_recent:
            self.recent_examples.pop(0)
        
        # Update category usage
        for category, keywords in {
            ActorCategory.ENEMY: ["enemy", "dodongo", "karebaba", "wallmaster", "stalfos"],
            ActorCategory.NPC: ["npc", "zora", "goron", "kokiri", "hylian", "gerudo"],
            ActorCategory.ITEM: ["item", "heart", "rupee", "bomb", "arrow", "bottle"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }.items():
            if any(keyword.lower() in example.instruction.lower() for keyword in keywords):
                self.category_usage[category.value] += 1
                break

class DiversityInjector:
    """Injects diversity into training data generation"""
    
    def __init__(self):
        self.scenario_templates = RealOoTScenarioTemplate()
        self.used_scenarios = set()
        self.actor_category_counts = {cat: 0 for cat in ActorCategory}
        
    def get_diverse_instruction(self, example_type: ExampleType, complexity: str) -> str:
        """Generate diverse instructions based on example type"""
        
        # Get base scenarios for the example type
        if example_type == ExampleType.ACTOR_CREATION:
            scenarios = self._get_actor_creation_scenarios()
        elif example_type == ExampleType.ANIMATION_SYSTEM:
            scenarios = self._get_animation_scenarios()
        elif example_type == ExampleType.COLLISION_SYSTEM:
            scenarios = self._get_collision_scenarios()
        elif example_type == ExampleType.INTERACTION_SYSTEM:
            scenarios = self._get_interaction_scenarios()
        elif example_type == ExampleType.EFFECT_SYSTEM:
            scenarios = self.scenario_templates.get_effect_scenarios()
        elif example_type == ExampleType.SOUND_SYSTEM:
            scenarios = self._get_sound_scenarios()
        elif example_type == ExampleType.AI_BEHAVIOR:
            scenarios = self.scenario_templates.get_player_scenarios()  # Use player scenarios for AI behavior
        elif example_type == ExampleType.ENVIRONMENTAL:
            scenarios = self.scenario_templates.get_background_scenarios()
        elif example_type == ExampleType.COMBAT_SYSTEM:
            scenarios = self.scenario_templates.get_player_scenarios()  # Use player scenarios for combat
        elif example_type == ExampleType.PUZZLE_SYSTEM:
            scenarios = self.scenario_templates.get_object_scenarios()  # Use object scenarios for puzzles
        elif example_type == ExampleType.CUSTOM_MECHANICS:
            scenarios = self.scenario_templates.get_misc_scenarios()  # Use misc scenarios for custom mechanics
        else:
            scenarios = self._get_generic_scenarios(example_type)
        
        # Filter out used scenarios to avoid repetition
        available_scenarios = [s for s in scenarios if s not in self.used_scenarios]
        if not available_scenarios:
            # Reset if all scenarios used
            self.used_scenarios.clear()
            available_scenarios = scenarios
        
        # Select scenario with diversity bias
        selected_scenario = self._select_with_diversity_bias(available_scenarios, example_type)
        self.used_scenarios.add(selected_scenario)
        
        # Add complexity modifiers
        complexity_modifiers = self._get_complexity_modifiers(complexity)
        if complexity_modifiers:
            selected_scenario += f" {random.choice(complexity_modifiers)}"
        
        return selected_scenario
    
    def _get_actor_creation_scenarios(self) -> List[str]:
        """Get diverse actor creation scenarios"""
        scenarios = []
        
        # Enemy scenarios
        scenarios.extend(self.scenario_templates.get_enemy_scenarios())
        
        # NPC scenarios  
        scenarios.extend(self.scenario_templates.get_npc_scenarios())
        
        # Item scenarios
        scenarios.extend(self.scenario_templates.get_item_scenarios())
        
        # Object scenarios (mechanical)
        scenarios.extend(self.scenario_templates.get_object_scenarios())
        
        # Background scenarios (environmental)
        scenarios.extend(self.scenario_templates.get_background_scenarios())
        
        return scenarios
    
    def _get_animation_scenarios(self) -> List[str]:
        return [
            "Create a skeletal animation system for character movement",
            "Implement a procedural animation system for natural movement",
            "Create a blend tree system for smooth animation transitions",
            "Make an animation event system that triggers effects during animations",
            "Create a facial animation system for NPC expressions",
            "Implement a physics-based animation system for cloth and hair",
            "Create an animation state machine for complex character behaviors",
            "Make a keyframe animation system for custom animations",
            "Create an animation compression system for memory optimization",
            "Implement an animation blending system for smooth transitions"
        ]
    
    def _get_collision_scenarios(self) -> List[str]:
        return [
            "Create a dynamic collision detection system for moving objects",
            "Implement a collision response system with realistic physics",
            "Create a collision filtering system for different object types",
            "Make a collision optimization system for performance",
            "Create a collision debugging system for development",
            "Implement a collision event system for trigger responses",
            "Create a collision prediction system for AI pathfinding",
            "Make a collision memory system for persistent interactions",
            "Create a collision visualization system for debugging",
            "Implement a collision caching system for repeated checks"
        ]
    
    def _get_interaction_scenarios(self) -> List[str]:
        return [
            "Create a dialogue system with branching conversations",
            "Implement an inventory system with item management",
            "Create a trading system for buying and selling items",
            "Make a crafting system for creating new items",
            "Create a quest system with objectives and rewards",
            "Implement a reputation system that affects NPC interactions",
            "Create a relationship system between NPCs and the player",
            "Make a skill system that improves with use",
            "Create a faction system with different groups and allegiances",
            "Implement a reputation system that affects available options"
        ]
    
    def _get_sound_scenarios(self) -> List[str]:
        return [
            "Create a dynamic music system that adapts to gameplay",
            "Implement a 3D audio system for spatial sound effects",
            "Create a voice acting system for NPC dialogue",
            "Make an ambient sound system for environmental audio",
            "Create a sound effect system for actions and events",
            "Implement a music transition system for smooth audio changes",
            "Create a sound filtering system for different environments",
            "Make a voice modulation system for different character types",
            "Create a sound memory system for persistent audio cues",
            "Implement a sound optimization system for performance"
        ]
    
    def _get_generic_scenarios(self, example_type: ExampleType) -> List[str]:
        """Generic scenarios for other example types"""
        return [
            f"Create a {example_type.value.replace('_', ' ')} system with proper OoT patterns",
            f"Implement {example_type.value.replace('_', ' ')} functionality using authentic code",
            f"Make a {example_type.value.replace('_', ' ')} that follows OoT decompilation standards",
            f"Create an advanced {example_type.value.replace('_', ' ')} with multiple features",
            f"Implement a complex {example_type.value.replace('_', ' ')} system for enhanced gameplay"
        ]
    
    def _select_with_diversity_bias(self, scenarios: List[str], example_type: ExampleType) -> str:
        """Select scenario with bias towards less used categories"""
        
        # Determine actor category from scenario content
        category_keywords = {
            ActorCategory.ENEMY: ["enemy", "boss", "attack", "patrol", "stealth", "flying"],
            ActorCategory.NPC: ["npc", "shopkeeper", "quest", "dialogue", "wandering"],
            ActorCategory.ITEM: ["item", "weapon", "armor", "tool", "consumable", "magic"],
            ActorCategory.OBJECT: ["object", "switch", "lift", "door", "chest", "torch"],
            ActorCategory.BACKGROUND: ["background", "temple", "water", "fire", "forest"],
            ActorCategory.EFFECT: ["effect", "song", "magic", "spell", "ocarina"],
            ActorCategory.PLAYER: ["player", "sword", "fishing", "ocarina", "bottle", "mask", "magic"],
            ActorCategory.MISC: ["fishing", "horse", "owl", "gossip", "treasure"]
        }
        
        # Score scenarios based on category diversity
        scenario_scores = []
        for scenario in scenarios:
            score = 1.0
            for category, keywords in category_keywords.items():
                if any(keyword.lower() in scenario.lower() for keyword in keywords):
                    # Boost score for less used categories
                    usage_ratio = self.actor_category_counts[category] / max(sum(self.actor_category_counts.values()), 1)
                    score += (1.0 - usage_ratio) * 2.0
                    break
            scenario_scores.append((scenario, score))
        
        # Weighted random selection
        total_score = sum(score for _, score in scenario_scores)
        if total_score > 0:
            weights = [score / total_score for _, score in scenario_scores]
            selected = random.choices(scenarios, weights=weights, k=1)[0]
        else:
            selected = random.choice(scenarios)
        
        # Update category counts
        for category, keywords in category_keywords.items():
            if any(keyword.lower() in selected.lower() for keyword in keywords):
                self.actor_category_counts[category] += 1
                break
        
        return selected
    
    def _get_complexity_modifiers(self, complexity: str) -> List[str]:
        """Get complexity modifiers for instructions"""
        if complexity == "advanced":
            return [
                "with multiple states and transitions",
                "using advanced optimization techniques", 
                "with complex interaction patterns",
                "implementing sophisticated AI behaviors",
                "with extensive error handling and edge cases",
                "using advanced memory management",
                "with complex mathematical calculations",
                "implementing multiple subsystems",
                "with extensive debugging capabilities",
                "using advanced rendering techniques"
            ]
        elif complexity == "intermediate":
            return [
                "with proper error handling",
                "using efficient algorithms",
                "with good code organization",
                "implementing standard patterns",
                "with appropriate documentation",
                "using memory-safe practices",
                "with reasonable performance",
                "implementing common features",
                "with basic debugging support",
                "using established conventions"
            ]
        else:  # basic
            return [
                "with basic functionality",
                "using simple patterns",
                "with minimal features",
                "implementing core requirements",
                "with straightforward logic",
                "using standard approaches",
                "with basic error checking",
                "implementing essential features",
                "with simple documentation",
                "using common practices"
            ]

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate strictly authentic OoT training data with dynamic source analysis")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--num-examples", type=int, default=30, help="Number of examples to generate")
    parser.add_argument("--output", default="authentic_oot_training.jsonl", help="Output file")
    parser.add_argument("--oot-path", default="oot", help="Path to OoT decompilation directory")
    parser.add_argument("--no-dynamic", action="store_true", help="Disable dynamic source analysis")
    
    args = parser.parse_args()
    
    generator = EnhancedOoTTrainingGenerator(
        api_key=args.api_key,
        oot_path=args.oot_path, 
        use_dynamic_analysis=not args.no_dynamic
    )
    generator.generate_dataset(args.num_examples, args.output)

if __name__ == "__main__":
    main() 