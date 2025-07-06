#!/usr/bin/env python3
"""
Strict Authenticity Validator for OoT Training Data
"""

import re
import os
import json
from typing import List, Optional, Tuple
from dataclasses import dataclass

from src.core.logger import logger
from src.analyzers.source_analyzer import DynamicSourceAnalyzer
from .function_signature_validator import FunctionSignatureValidator
from src.compilation.c_code_compiler import CCodeExtractor, CompilationResult


@dataclass
class ValidationResult:
    """Result of authenticity validation"""
    is_authentic: bool
    score: float
    issues: List[str]
    suggestions: List[str]
    compilation_result: Optional[CompilationResult] = None


class StrictAuthenticityValidator:
    """Validates authenticity of generated OoT code against real codebase"""
    
    def __init__(self, source_analyzer: Optional[DynamicSourceAnalyzer] = None):
        # Use dynamic source analyzer if provided, otherwise use OoTAuthenticPatterns data
        self.source_analyzer = source_analyzer
        
        if source_analyzer:
            # Real function signatures from actual OoT decompilation
            self.authentic_function_signatures = set(source_analyzer.real_functions.keys())
            
            # Real OoT types from decompilation
            self.authentic_types = set(source_analyzer.real_structs.keys())
        else:
            # Use OoTAuthenticPatterns data instead of hardcoded lists
            from helpers.validate_and_enhance_scenarios import OoTAuthenticPatterns
            patterns = OoTAuthenticPatterns()
            self.authentic_function_signatures = patterns.AUTHENTIC_FUNCTIONS
            self.authentic_types = patterns.AUTHENTIC_CONSTANTS  # Use constants as types too
        
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
            
            # NEW: Feedback-based corrections
            "play->state.input[0].press.button": "input->press.button",  # Will be used with Input* input = &play->state.input[0]
            "Actor_DrawScale": "SkelAnime_DrawOpa",  # Replace non-existent drawing functions
            "Actor_DrawModel": "SkelAnime_DrawOpa",
            "Actor_DrawMesh": "Gfx_DrawDListOpa",
            "Actor_RenderModel": "Gfx_DrawDListOpa",
            "LightContext_InsertLight": "Lights_PointGlowSetInfo",  # Correct lighting function
            
            # NEW: Additional feedback-based corrections
            "SkelAnime_BlendFrames": "Animation_MorphToLoop",  # Replace non-existent animation blending
            "ANIM_BLEND_MAX_JOINTS": "PLAYER_LIMB_MAX",  # Replace with authentic constant
            "PLAYER_MASK_13": "PLAYER_MASK_OCARINA",  # Replace with authentic mask
            "Player_Action_80846978": "Player_UpdateOcarina",  # Replace with authentic function
            "ENTR_TEMPLE_OF_TIME_0": "ENTR_TEMPLE_OF_TIME",  # Replace with authentic entrance
            "TRANS_TYPE_FADE_WHITE": "TRANS_TYPE_FADE_BLACK",  # Replace with authentic transition
            "TRANS_TRIGGER_START": "TRANS_TRIGGER_START",  # Keep but verify usage
            
            # NEW: Additional feedback-based corrections
            "Lights_PointGlowSetInfo": "LightContext_InsertLight",  # Replace with authentic lighting function
            "Lights_PointNoGlowSetInfo": "LightContext_InsertLight",  # Replace with authentic lighting function
            "Math_Vec3f_DistXZ": "sqrtf(SQ(dx) + SQ(dz))",  # Replace with manual calculation
            "BGCHECKFLAG_GROUND": "UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2",  # Replace with authentic flags
            
            # NEW: Updated corrections based on compilation testing
            "COLTYPE_NONE": "COL_MATERIAL_NONE",
            "COLTYPE_HIT0": "COL_MATERIAL_HIT0", 
            "COLTYPE_HIT1": "COL_MATERIAL_HIT1",
            "COLTYPE_HIT2": "COL_MATERIAL_HIT2",
            "COLTYPE_HIT3": "COL_MATERIAL_HIT3",
            "COLTYPE_METAL": "COL_MATERIAL_METAL",
            "COLTYPE_WOOD": "COL_MATERIAL_WOOD",
            "COLTYPE_HARD": "COL_MATERIAL_HARD",
            "COLTYPE_TREE": "COL_MATERIAL_TREE",
            "ELEMTYPE_UNK0": "ELEM_MATERIAL_UNK0",
            "ELEMTYPE_UNK1": "ELEM_MATERIAL_UNK1",
            "ELEMTYPE_UNK2": "ELEM_MATERIAL_UNK2",
            "ELEMTYPE_UNK3": "ELEM_MATERIAL_UNK3",
            "ELEMTYPE_UNK4": "ELEM_MATERIAL_UNK4",
            "ELEMTYPE_UNK5": "ELEM_MATERIAL_UNK5",
            "ELEMTYPE_UNK6": "ELEM_MATERIAL_UNK6",
            "ELEMTYPE_UNK7": "ELEM_MATERIAL_UNK7",
            "OPEN_DISPS(play->state.gfxCtx)": "OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__)",
            "CLOSE_DISPS(play->state.gfxCtx)": "CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__)",
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
            
            # NEW: Feedback-based forbidden patterns
            r"play->state\.input\[0\]\.press\.button",  # Incorrect input handling pattern
            r"Actor_DrawScale",  # Non-existent drawing function
            r"Actor_DrawModel",  # Non-existent drawing function
            r"Actor_DrawMesh",  # Non-existent drawing function
            r"Actor_RenderModel",  # Non-existent drawing function
            r"play->msgCtx\.choiceIndex",  # Incorrect message system usage
            r"Message_GetState.*TEXT_STATE_CHOICE",  # Incorrect message state checking
            r"LightContext_InsertLight",  # Incorrect lighting implementation
            r"player->actor\.world\.pos\.[xyz]\s*=",  # Direct player position manipulation (CRITICAL)
            
            # NEW: Additional feedback-based forbidden patterns
            r"SkelAnime_BlendFrames",  # Non-existent animation blending function
            r"ANIM_BLEND_MAX_JOINTS",  # Non-existent animation constant
            r"PLAYER_MASK_13",  # Non-existent player mask constant
            r"Player_Action_80846978",  # Non-existent player action function
            r"ENTR_TEMPLE_OF_TIME_0",  # Non-existent entrance constant
            r"TRANS_TYPE_FADE_WHITE",  # Non-existent transition type
            r"TRANS_TRIGGER_START",  # Non-existent transition trigger
            
            # NEW: Additional feedback-based forbidden patterns
            r"Lights_PointGlowSetInfo",  # Non-existent lighting function signature
            r"Lights_PointNoGlowSetInfo",  # Non-existent lighting function signature
            r"Math_Vec3f_DistXZ",  # Non-existent math function
            r"BGCHECKFLAG_GROUND",  # Non-existent collision flag
            r"\"\"\"[^\"]+\"\"\"",  # Triple-quoted strings in C code
            
            # NEW: Updated forbidden patterns based on compilation testing
            r"COLTYPE_[A-Z_]+",  # Wrong collision type constants (use COL_MATERIAL_*)
            r"ELEMTYPE_[A-Z_]+",  # Wrong element type constants (use ELEM_MATERIAL_*)
            r"OPEN_DISPS\(play->state\.gfxCtx\)(?!\s*,\s*__FILE__)",  # Missing file/line parameters
            r"CLOSE_DISPS\(play->state\.gfxCtx\)(?!\s*,\s*__FILE__)",  # Missing file/line parameters
            r"func_8002F71C",  # Non-existent function
            r"sCylinderInit(?!\s*=)",  # Using sCylinderInit without declaring it
            r"SkelAnime_InitFlex\([^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,\s*0\)",  # Wrong parameters
            r"player->actor\.id\s*!=\s*ACTOR_PLAYER",  # Wrong player ID check
            r"gSaveContext\.inventory\.questItems\s*&\s*0x3F",  # Wrong quest item check
            r"play->colCtx\.waterLevel\s*=",  # Direct water level manipulation
            r"play->msgCtx\.ocarinaMode\s*==\s*OCARINA_MODE_04",  # Wrong ocarina mode check
            r"player->health",  # Wrong player health access
            r"player->healthCapacity",  # Wrong player health capacity access
            r"player->currentShield",  # Non-existent player shield access
            r"player->swordState",  # Non-existent player sword state access
            r"PLAYER_SHIELD_MAX",  # Non-existent constant
            r"PLAYER_SWORD_MAX",  # Non-existent constant
            r"LIMB_COUNT",  # Non-existent constant
            r"ACTOR_FLAG_[8-9]|ACTOR_FLAG_1[0-9]",  # Non-existent actor flags
            r"INV_CONTENT",  # Non-existent inventory function
            r"Actor_DrawOpa",  # Non-existent drawing function
            r"SkelAnime_DrawOpa\([^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*\)",  # Wrong signature
            r"ZeldaArena_MallocDebug",  # Non-existent debug function
            r"ZeldaArena_FreeDebug",  # Non-existent debug function
        ]
        
        # Required authentic patterns for quality code
        self.required_patterns = [
            r"PlayState\*\s+play",  # Modern PlayState usage
            r"Actor\*\s+thisx",  # Authentic actor parameter
            r"world\.pos",  # Proper position access
            r"ACTORCAT_\w+",  # Actor categories
            r"Collider_\w+",  # Collision functions
            r"COL_MATERIAL_\w+",  # Correct collision material constants
            r"ELEM_MATERIAL_\w+",  # Correct element material constants
            r"OPEN_DISPS\(play->state\.gfxCtx,\s*__FILE__,\s*__LINE__\)",  # Correct OPEN_DISPS usage
            r"CLOSE_DISPS\(play->state\.gfxCtx,\s*__FILE__,\s*__LINE__\)",  # Correct CLOSE_DISPS usage
            r"static\s+ColliderCylinderInit\s+sCylinderInit",  # Proper collision initialization
            r"UPDBGCHECKINFO_FLAG_\d+",  # Correct background check flags
        ]
        
        # Real architectural patterns from OoT decompilation
        self.architectural_guidance = {
            "heart_piece": "Use EnItem00 with ITEM00_HEART_PIECE parameter (from z_en_item00.c)",
            "rupees": "Use EnItem00 with ITEM00_RUPEE_* parameters (from z_en_item00.c)", 
            "keys": "Use EnItem00 with ITEM00_SMALL_KEY parameter (from z_en_item00.c)",
            "collectibles": "Most collectibles use EnItem00 with different parameters (see z_en_item00.c)",
            "switches": "Use existing switch actors with parameters, rarely create new ones",
            "ocarina": "Ocarina handling is done through player actor's state machine, not separate actors. Use Player_UpdateOcarina() and built-in song recognition",
            "animation_blending": "Use Animation_MorphToLoop() or Animation_Change() with morph parameters, not dedicated blending functions",
            "transitions": "Use authentic entrance constants and transition types from OoT decompilation",
            "lighting": "Use LightContext_InsertLight() with proper LightInfo structure, not Lights_PointGlowSetInfo()",
            "matrix_strings": "Use __FILE__, __LINE__ for Matrix_NewMtx(), not triple-quoted strings",
            "background_collision": "Use UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2 for Actor_UpdateBgCheckInfo()",
            "math_functions": "Use sqrtf(SQ(dx) + SQ(dz)) for distance calculations, not Math_Vec3f_DistXZ()",
            "collision_materials": "Use COL_MATERIAL_* constants (COL_MATERIAL_NONE, COL_MATERIAL_HIT0, etc.) instead of COLTYPE_*",
            "element_materials": "Use ELEM_MATERIAL_* constants (ELEM_MATERIAL_UNK0, ELEM_MATERIAL_UNK1, etc.) instead of ELEMTYPE_*",
            "graphics_macros": "Use OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__) and CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__)",
            "collision_init": "Declare static ColliderCylinderInit sCylinderInit = { ... }; for collision initialization",
            "skeleton_init": "Use SkelAnime_InitFlex(play, &skelAnime, skeleton, animation, jointTable, morphTable, limbCount)",
            "player_access": "Use gSaveContext.health and gSaveContext.healthCapacity for player health, gSaveContext.equips.buttonItems for equipment",
            "actor_flags": "Use ACTOR_FLAG_0 through ACTOR_FLAG_15 for actor flags",
            "memory_management": "Use ZeldaArena_Malloc(size) and ZeldaArena_Free(ptr) for memory management",
            "drawing_functions": "Use SkelAnime_DrawFlexOpa(play, skeleton, jointTable, dListCount, NULL, NULL, this) for skeleton drawing",
        }

        self.function_validator = FunctionSignatureValidator()
        self.code_extractor = CCodeExtractor()
        self.compiler = None  # Will be initialized when needed

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
                
        # NEW: Extra penalties for critical feedback patterns
        critical_patterns = [
            r"player->actor\.world\.pos\.[xyz]\s*=",  # Direct player position manipulation
            r"play->state\.input\[0\]\.press\.button",  # Incorrect input handling
            r"Actor_DrawScale|Actor_DrawModel|Actor_DrawMesh|Actor_RenderModel",  # Non-existent drawing functions
            r"play->msgCtx\.choiceIndex",  # Incorrect message system
            r"LightContext_InsertLight",  # Incorrect lighting
            r"SkelAnime_BlendFrames",  # Non-existent animation blending function
            r"ANIM_BLEND_MAX_JOINTS",  # Non-existent animation constant
            r"PLAYER_MASK_13",  # Non-existent player mask constant
            r"Player_Action_80846978",  # Non-existent player action function
            r"ENTR_TEMPLE_OF_TIME_0",  # Non-existent entrance constant
            r"TRANS_TYPE_FADE_WHITE",  # Non-existent transition type
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, code):
                score -= 3.0  # Extra penalty for critical issues
                
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

    def validate_feedback_patterns(self, code: str) -> List[str]:
        """Validate against feedback patterns from previous runs"""
        issues = []
        
        # Check for Majora's Mask contamination
        mm_patterns = [
            r'TRANSFORM_STATE_DEKU', r'TRANSFORM_STATE_GORON', r'TRANSFORM_STATE_ZORA',
            r'transformState', r'transformTimer', r'transformation',
            r'Deku\s+form', r'Goron\s+form', r'Zora\s+form'
        ]
        
        for pattern in mm_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("Majora's Mask contamination detected")
                break
        
        # Check for fabricated functions
        fabricated_patterns = [
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_DrawOpa\s*\(\s*play,\s*[^)]+\s*\)',
            r'func_80093D18\s*\(',
            r'ZeldaArena_MallocDebug\s*\(',
            r'ZeldaArena_FreeDebug\s*\('
        ]
        
        for pattern in fabricated_patterns:
            if re.search(pattern, code):
                issues.append("Fabricated function detected")
                break
        
        # Check for wrong player struct access
        wrong_player_patterns = [
            r'player->currentShield', r'player->swordState', r'player->health',
            r'player->equippedShield', r'player->equippedSword'
        ]
        
        for pattern in wrong_player_patterns:
            if re.search(pattern, code):
                issues.append("Wrong player struct access - use gSaveContext instead")
                break
        
        # Check for non-existent constants
        non_existent_constants = [
            r'PLAYER_SHIELD_MAX', r'PLAYER_SWORD_MAX', r'LIMB_COUNT',
            r'ACTOR_PLAYER', r'PLAYER_WEAPON_MAX'
        ]
        
        for pattern in non_existent_constants:
            if re.search(pattern, code):
                issues.append("Non-existent constant detected")
                break
        
        # Check for wrong Matrix_NewMtx usage
        if re.search(r'Matrix_NewMtx\s*\(\s*[^,]+,\s*"[^"]+"\s*\)', code):
            issues.append("Wrong Matrix_NewMtx parameters - use __FILE__, __LINE__")
        
        # Check for wrong OPEN_DISPS usage
        if re.search(r'OPEN_DISPS\s*\(\s*[^,]+,\s*"[^"]+",\s*[^)]+\)', code):
            issues.append("Wrong OPEN_DISPS usage - don't use file/line parameters")
        
        # Check for missing struct members
        if re.search(r'this->jointTable|this->morphTable', code):
            struct_pattern = r'typedef\s+struct\s*\{[^}]*\}'
            struct_matches = re.finditer(struct_pattern, code, re.DOTALL)
            
            found_declaration = False
            for struct_match in struct_matches:
                struct_content = struct_match.group(0)
                if "jointTable" in struct_content and "morphTable" in struct_content:
                    found_declaration = True
                    break
            
            if not found_declaration:
                issues.append("Missing struct members - declare jointTable and morphTable")
        
        # Check for dynamic memory allocation
        memory_patterns = [
            r'ZeldaArena_Malloc\s*\(',
            r'malloc\s*\(',
            r'dynamic\s+memory\s+allocation',
            r'memory\s+manager'
        ]
        
        for pattern in memory_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("Dynamic memory allocation not allowed in actors")
                break
        
        # Check for wrong Math_SmoothStepToF usage
        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*Math_SmoothStepToF\s*\(', code):
            issues.append("Wrong Math_SmoothStepToF usage - function returns bool, not float")
        
        return issues

    def validate_code(self, code: str, category: str = "general") -> ValidationResult:
        """Validate code authenticity and compile it if possible"""
        issues = []
        suggestions = []
        
        # Extract C code if present
        extracted_snippets = self.code_extractor.extract_c_code(code)
        
        # Initialize compiler if we have C code to test
        compilation_result = None
        if extracted_snippets:
            if self.compiler is None:
                from src.compilation.c_code_compiler import OoTCompiler
                self.compiler = OoTCompiler()
            
            # Try to compile the first (largest) code snippet
            largest_snippet = max(extracted_snippets, key=len) if extracted_snippets else ""
            
            try:
                compilation_result = self.compiler.compile_code(largest_snippet)
            except Exception as e:
                logger.warning(f"Compilation test failed: {e}")
                compilation_result = CompilationResult(
                    success=False,
                    error_messages=[f"Compilation test error: {e}"],
                    warnings=[],
                    compilation_time=0.0,
                    extracted_code=largest_snippet
                )
        
        # Perform authenticity validation
        auth_score, auth_issues, auth_suggestions = self._validate_authenticity(code, category)
        
        # Combine issues and suggestions
        all_issues = auth_issues.copy()
        all_suggestions = auth_suggestions.copy()
        
        # Add compilation issues if compilation failed
        if compilation_result and not compilation_result.success:
            all_issues.append("Compilation failed - code contains syntax errors or missing dependencies")
            if compilation_result.error_messages:
                # Add first few compilation errors as specific issues
                for error in compilation_result.error_messages[:3]:
                    all_issues.append(f"Compilation error: {error}")
            
            # Add compilation-specific suggestions
            if "unknown type name" in str(compilation_result.error_messages):
                all_suggestions.append("Include proper OoT header files (z_actor.h, z_play.h, etc.)")
            if "implicit declaration" in str(compilation_result.error_messages):
                all_suggestions.append("Add proper function declarations or include required headers")
            if "undefined reference" in str(compilation_result.error_messages):
                all_suggestions.append("Ensure all referenced functions are properly declared")
        
        # Calculate overall score (authenticity + compilation success)
        overall_score = auth_score
        if compilation_result and compilation_result.success:
            overall_score += 0.2  # Bonus for successful compilation
        elif compilation_result and not compilation_result.success:
            overall_score -= 0.3  # Penalty for compilation failure
        
        overall_score = max(0.0, min(10.0, overall_score))  # Clamp to 0-10
        
        return ValidationResult(
            is_authentic=overall_score >= 7.0,
            score=overall_score,
            issues=all_issues,
            suggestions=all_suggestions,
            compilation_result=compilation_result
        )
    
    def _validate_authenticity(self, code: str, category: str) -> Tuple[float, List[str], List[str]]:
        """Core authenticity validation logic"""
        issues = []
        suggestions = []
        score = 8.0  # Start with good score
        
        # Check for common inauthentic patterns
        if "printf" in code or "scanf" in code:
            issues.append("Uses standard C I/O functions not available in OoT")
            suggestions.append("Use OoT's message system or debug functions instead")
            score -= 2.0
        
        if "malloc" in code or "free" in code:
            issues.append("Uses dynamic memory allocation not available in OoT")
            suggestions.append("Use static allocation or OoT's memory management")
            score -= 2.0
        
        if "fopen" in code or "fclose" in code:
            issues.append("Uses file I/O not available in OoT")
            suggestions.append("Use OoT's save system or data structures")
            score -= 2.0
        
        # Check for OoT-specific patterns
        if "Actor" in code and "PlayState" in code:
            score += 0.5  # Bonus for proper OoT actor structure
        
        if "Collider" in code and "CollisionCheck" in code:
            score += 0.5  # Bonus for proper collision system usage
        
        if "SkelAnime" in code:
            score += 0.5  # Bonus for skeleton animation usage
        
        # Check for missing OoT patterns
        if "Actor" in code and "Actor_UpdateBgCheckInfo" not in code:
            issues.append("Missing background collision check")
            suggestions.append("Add Actor_UpdateBgCheckInfo call in Update function")
            score -= 1.0
        
        if "Collider" in code and "Collider_UpdateCylinder" not in code:
            issues.append("Missing collider update")
            suggestions.append("Add Collider_UpdateCylinder call in Update function")
            score -= 1.0
        
        return score, issues, suggestions

    def _check_nonexistent_player_health_access(self, code: str) -> List[str]:
        """Check for incorrect player health access patterns."""
        issues = []
        
        # Check for wrong player health access
        wrong_health_patterns = [
            r'player->health',
            r'player->healthCapacity',
            r'player->maxHealth',
            r'player->currentHealth'
        ]
        
        for pattern in wrong_health_patterns:
            if re.search(pattern, code):
                issues.append("❌ CRITICAL: Wrong player health access - player->health doesn't exist in OoT")
                break
        
        return issues

    def _check_direct_player_position_manipulation(self, code: str) -> List[str]:
        """Check for direct manipulation of player position from other actors."""
        issues = []
        
        # Check for direct player position manipulation
        player_pos_patterns = [
            r'player->actor\.world\.pos\.x\s*[+\-]?=',
            r'player->actor\.world\.pos\.y\s*[+\-]?=',
            r'player->actor\.world\.pos\.z\s*[+\-]?=',
            r'player->actor\.world\.pos\s*[+\-]?=',
            r'player->actor\.world\.rot\.',
            r'player->actor\.velocity\.',
            r'player->actor\.speed'
        ]
        
        for pattern in player_pos_patterns:
            if re.search(pattern, code):
                issues.append("❌ CRITICAL: Direct player position/velocity manipulation - OoT never allows other actors to directly manipulate player physics")
                break
        
        return issues

    def _check_missing_variable_declarations(self, code: str) -> List[str]:
        """Check for missing variable declarations in structs."""
        issues = []
        
        # Check for SkelAnime usage without declaration
        if "SkelAnime_" in code or "skelAnime." in code:
            # Look for SkelAnime declaration in struct
            struct_pattern = r'typedef\s+struct\s*\{[^}]*\}'
            struct_matches = re.finditer(struct_pattern, code, re.DOTALL)
            
            for struct_match in struct_matches:
                struct_content = struct_match.group(0)
                if "SkelAnime" in code and "SkelAnime skelAnime" not in struct_content:
                    issues.append("❌ CRITICAL: Missing SkelAnime declaration in struct")
                    break
        
        # Check for other common missing declarations
        missing_decl_patterns = [
            (r'Collider_InitCylinder', r'ColliderCylinder collider'),
            (r'Collider_UpdateCylinder', r'ColliderCylinder collider'),
            (r'CollisionCheck_SetOC', r'ColliderCylinder collider'),
            (r'CollisionCheck_SetAC', r'ColliderCylinder collider')
        ]
        
        for func_pattern, decl_pattern in missing_decl_patterns:
            if re.search(func_pattern, code) and not re.search(decl_pattern, code):
                issues.append("❌ CRITICAL: Missing collider declaration in struct")
                break
        
        return issues

    def _check_wrong_flag_usage(self, code: str) -> List[str]:
        """Check for incorrect flag usage patterns."""
        issues = []
        
        # Check for wrong flag checking patterns
        wrong_flag_patterns = [
            r'CHECK_FLAG_ALL\s*\(\s*player->actor\.flags,\s*ACTOR_FLAG_8\s*\)',
            r'CHECK_FLAG_ALL\s*\(\s*[^,]+,\s*ACTOR_FLAG_[89]\s*\)',
            r'ACTOR_FLAG_8',
            r'ACTOR_FLAG_9',
            r'ACTOR_FLAG_[89]'
        ]
        
        for pattern in wrong_flag_patterns:
            if re.search(pattern, code):
                issues.append("❌ CRITICAL: Wrong flag usage - ACTOR_FLAG_8/9 don't exist in OoT")
                break
        
        return issues

    def _check_nonexistent_drawing_functions_enhanced(self, code: str) -> List[str]:
        """Enhanced check for non-existent drawing functions."""
        issues = []
        
        # Check for fabricated drawing functions
        fabricated_drawing = [
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*g[A-Z][a-zA-Z0-9_]*DL\s*\)',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[a-z][a-zA-Z0-9_]*DL\s*\)',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_DrawOpa\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_DrawModel\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_DrawMesh\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_RenderModel\s*\(\s*play,\s*[^)]+\s*\)',
            r'Actor_DrawScale\s*\(\s*play,\s*[^)]+\s*\)',
            r'Gfx_DrawDList\s*\(\s*play,\s*[^)]+\s*\)',
            r'Gfx_DrawModel\s*\(\s*play,\s*[^)]+\s*\)'
        ]
        
        for pattern in fabricated_drawing:
            if re.search(pattern, code):
                issues.append("❌ CRITICAL: Non-existent drawing function - Gfx_DrawDListOpa(play, gSomeDL) doesn't exist in OoT")
                break
        
        return issues

