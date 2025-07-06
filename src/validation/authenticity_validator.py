#!/usr/bin/env python3
"""
Strict Authenticity Validator for OoT Training Data
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from src.core.logger import logger
from src.analyzers.source_analyzer import DynamicSourceAnalyzer
from .function_signature_validator import FunctionSignatureValidator


@dataclass
class ValidationResult:
    """Result of scenario validation"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    authentic_patterns: List[str]
    required_context: List[str]


class StrictAuthenticityValidator:
    """Enhanced validator with strict authenticity enforcement + real OoT function data"""
    
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
            "ocarina": "Ocarina handling is done through player actor's state machine, not separate actors. Use Player_UpdateOcarina() and built-in song recognition",
            "animation_blending": "Use Animation_MorphToLoop() or Animation_Change() with morph parameters, not dedicated blending functions",
            "transitions": "Use authentic entrance constants and transition types from OoT decompilation",
            "lighting": "Use LightContext_InsertLight() with proper LightInfo structure, not Lights_PointGlowSetInfo()",
            "matrix_strings": "Use __FILE__, __LINE__ for Matrix_NewMtx(), not triple-quoted strings",
            "background_collision": "Use UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2 for Actor_UpdateBgCheckInfo()",
            "math_functions": "Use sqrtf(SQ(dx) + SQ(dz)) for distance calculations, not Math_Vec3f_DistXZ()",
        }

        self.function_validator = FunctionSignatureValidator()

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

    def validate_code_output(self, code: str, category: str) -> ValidationResult:
        """Validate C code output for function/constant/sfx/struct existence and OoT patterns."""
        issues, sugg, pats = [], [], []
        
        # NEW: Validate function calls against authentic signatures
        function_issues = self.function_validator.validate_code_function_calls(code)
        issues.extend(function_issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=sugg,
            authentic_patterns=pats,
            required_context=[]
        )

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

