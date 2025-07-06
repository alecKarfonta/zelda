#!/usr/bin/env python3
"""
OoT Scenario Validator & Context Generator

Enhanced version with comprehensive pattern validation.
• Extracts authentic patterns per category (enemy, npc, item, object).  
• Provides ValidationResult detailing issues/suggestions.  
• Supplies rich context snippets to feed the LLM.  
• Exposes create_enhanced_prompt() for prompt assembly.
• Validates against real OoT function names and patterns.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Optional
import re
import os
import keyword
import builtins
import logging

# ============================================================================
# ENHANCED LOGGING SYSTEM
# ============================================================================

class OoTLogger:
    """Enhanced logging system with function names and relevant emojis"""
    
    def __init__(self, name: str = "OoTValidator"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler with custom formatter
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Custom formatter with function names and emojis
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s() | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler if not already added
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str, func_name: Optional[str] = None):
        """Debug level with 🔍 emoji"""
        if func_name:
            self.logger.debug(f"🔍 {message}")
        else:
            self.logger.debug(f"🔍 {message}")
    
    def info(self, message: str, func_name: Optional[str] = None):
        """Info level with ℹ️ emoji"""
        if func_name:
            self.logger.info(f"ℹ️  {message}")
        else:
            self.logger.info(f"ℹ️  {message}")
    
    def warning(self, message: str, func_name: Optional[str] = None):
        """Warning level with ⚠️ emoji"""
        if func_name:
            self.logger.warning(f"⚠️  {message}")
        else:
            self.logger.warning(f"⚠️  {message}")
    
    def error(self, message: str, func_name: Optional[str] = None):
        """Error level with ❌ emoji"""
        if func_name:
            self.logger.error(f"❌ {message}")
        else:
            self.logger.error(f"❌ {message}")
    
    def validation(self, message: str, func_name: Optional[str] = None):
        """Validation level with 🛡️ emoji"""
        if func_name:
            self.logger.info(f"🛡️  {message}")
        else:
            self.logger.info(f"🛡️  {message}")

# Global logger instance
logger = OoTLogger()

# ------------------------------------------------------------
# Data classes
# ------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of scenario validation"""
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    authentic_patterns: List[str]
    required_context: List[str]

# ------------------------------------------------------------
# OoT Authentic Patterns Database
# ------------------------------------------------------------

class OoTAuthenticPatterns:
    """Database of authentic OoT patterns, functions, and constants."""
    
    def __init__(self):
        self.AUTHENTIC_FUNCTIONS = self._load_set('oot_valid_functions.txt', normalize_case=True)
        self.AUTHENTIC_CONSTANTS = self._load_set('oot_valid_constants.txt', normalize_case=True)
        self.AUTHENTIC_SOUND_EFFECTS = self._load_set('oot_valid_sound_effects.txt', normalize_case=True)
        logger.debug(f"Loaded {len(self.AUTHENTIC_FUNCTIONS)} functions from database")
        logger.debug(f"Sample functions: {list(self.AUTHENTIC_FUNCTIONS)[:10]}")

    def _load_set(self, filename, normalize_case=False):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
                if normalize_case:
                    lines = [line.lower() for line in lines]
                logger.debug(f"Loading {len(lines)} items from {filename}")
                logger.debug(f"First 5 items: {lines[:5]}")
                # Debug: Check if specific functions are in the lines
                if filename == 'oot_valid_functions.txt':
                    test_funcs = ['Actor_SetScale', 'Collider_InitCylinder', 'Actor_PlaySfx']
                    for func in test_funcs:
                        check_func = func.lower() if normalize_case else func
                        if check_func in lines:
                            logger.debug(f"{func} found in lines")
                        else:
                            logger.debug(f"{func} NOT found in lines")
                return set(lines)
        else:
            logger.warning(f"{filename} not found. Using empty set.")
            return set()

# ------------------------------------------------------------
# Validator class
# ------------------------------------------------------------

class OoTPatternValidator:
    """Validate scenario text against known OoT patterns (enhanced version)."""

    def __init__(self, oot_path: str = "oot") -> None:
        self.oot_path = oot_path
        self.context_templates = self._build_context_templates()
        self.patterns = OoTAuthenticPatterns()

    # ------------------------ public API ---------------------

    def validate_scenario(self, scenario: str, category: str) -> ValidationResult:
        category = category.lower().strip()
        if category == "enemy":
            issues, sugg, pats = self._validate_enemy_scenario(scenario)
            ctx = [self.context_templates["enemy"]]
        elif category == "npc":
            issues, sugg, pats = self._validate_npc_scenario(scenario)
            ctx = [self.context_templates["npc"]]
        elif category == "item":
            issues, sugg, pats = self._validate_item_scenario(scenario)
            ctx = [self.context_templates["item"]]
        else:
            # treat anything else as object/mechanism
            issues, sugg, pats = self._validate_object_scenario(scenario)
            ctx = [self.context_templates["object"]]

        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=sugg,
            authentic_patterns=pats,
            required_context=ctx,
        )

    def create_enhanced_prompt(self, scenario: str, category: str, val: ValidationResult) -> str:
        """Return a rich prompt containing requirements & authentic snippets."""
        patterns = "\n".join(f"- {p}" for p in val.authentic_patterns[:6])
        issues_block = "\n".join(f"⚠️  {i}" for i in val.issues) or "None"
        suggestions_block = "\n".join(f"💡 {s}" for s in val.suggestions) or "None"
        ctx = "\n\n".join(val.required_context)
        
        # Add OoT pattern examples
        oot_examples = self._get_oot_pattern_examples(category)
        
        return f"""
You are generating **authentic OoT rom-hacking code**.  Follow REAL decompilation patterns.

SCENARIO (category={category}): {scenario}

STRICT REQUIREMENTS:
1. Function signatures **must** be `(Actor* thisx, PlayState* play)`
2. Use real struct layouts and collision setup (`Collider_InitCylinder`, etc.)
3. Access positions via `actor.world.pos`, not deprecated fields.
4. Prefer re-using `EnItem00` for collectibles.
5. Use ONLY authentic OoT function names and constants.
6. Use `ActorProfile` structure correctly (see real examples).
7. **REQUIRED**: Include ActorProfile struct at the end
8. **REQUIRED**: Define ColliderCylinderInit static struct
9. **REQUIRED**: Actor field must be first in struct
10. **REQUIRED**: Add proper casting: `ActorName* this = (ActorName*)thisx;`

AUTHENTIC PATTERNS TO EMULATE:
{patterns}

OoT PATTERN EXAMPLES:
{oot_examples}

KNOWN ISSUES:
{issues_block}

SUGGESTIONS TO IMPROVE:
{suggestions_block}

{ctx}

Return exactly this JSON:
{{
  "instruction": "clear instruction",
  "input": null,
  "output": "C code here"
}}
"""

    def validate_code_output(self, code: str, category: str) -> ValidationResult:
        """Validate C code output for function/constant/sfx/struct existence and OoT patterns."""
        issues, sugg, pats = [], [], []
        
        # CRITICAL: Check for Majora's Mask contamination first
        self._check_majoras_mask_contamination(code, issues, sugg)
        
        # NEW: Check for critical syntax errors
        self._check_syntax_errors(code, issues, sugg)
        
        # NEW: Check for fabricated patterns that don't exist in OoT
        self._check_fabricated_patterns(code, issues, sugg)
        
        # Check for non-existent patterns (existing functionality)
        self._check_nonexistent_patterns(code, issues, sugg)
        
        # NEW: Check for missing OoT-specific patterns
        self._check_missing_oot_patterns(code, issues, sugg)
        
        # NEW: Check for incorrect struct definitions
        self._check_struct_patterns(code, issues, sugg)
        
        # NEW: Check for missing ActorProfile
        self._check_actor_profile(code, issues, sugg)
        
        # NEW: Check for missing ColliderInit structs
        self._check_collider_init_structs(code, issues, sugg)
        
        # NEW: Check for incorrect function signatures
        self._check_function_signatures(code, issues, sugg)
        
        # NEW: Check for incorrect background check usage
        self._check_incorrect_bgcheck_usage(code, issues, sugg)
        
        # NEW: Check for wrong background check flags
        self._check_wrong_bgcheck_flags(code, issues, sugg)
        
        # NEW: Check for incorrect water detection patterns
        self._check_incorrect_water_detection(code, issues, sugg)
        
        # NEW: Check for incorrect actor categories
        self._check_incorrect_actor_categories(code, issues, sugg)
        
        # NEW: Check for non-existent drawing functions
        self._check_nonexistent_drawing_functions(code, issues, sugg)
        
        # NEW: Check for incorrect animation blending
        self._check_incorrect_animation_blending(code, issues, sugg)
        
        # NEW: Check for incorrect math functions
        self._check_incorrect_math_functions(code, issues, sugg)
        
        # NEW: Check for incorrect struct access
        self._check_incorrect_struct_access(code, issues, sugg)
        
        # NEW: Check for wrong inventory patterns
        self._check_wrong_inventory_patterns(code, issues, sugg)
        
        # NEW: Check for non-existent functions
        self._check_nonexistent_functions(code, issues, sugg)
        
        # NEW: Check for missing input declarations
        self._check_missing_input_declaration(code, issues, sugg)
        
        # NEW: Check for wrong actor flags
        self._check_wrong_actor_flags(code, issues, sugg)
        
        # NEW: Check for non-existent magic systems
        self._check_nonexistent_magic_system(code, issues, sugg)
        
        # NEW: Check for wrong sound effects
        self._check_wrong_sound_effects(code, issues, sugg)
        
        # NEW: Check for broken sqrtf syntax
        self._check_broken_sqrtf_syntax(code, issues, sugg)
        
        # NEW: Check for direct player physics manipulation
        self._check_direct_player_physics_manipulation(code, issues, sugg)
        
        # NEW: Check for wrong matrix function parameters
        self._check_wrong_matrix_function_parameters(code, issues, sugg)
        
        # NEW: Check for non-existent actor spawn functions
        self._check_nonexistent_actor_spawn_functions(code, issues, sugg)
        
        # NEW: Check for game design issues
        self._check_game_design_issues(code, issues, sugg)
        
        # NEW: Check for non-existent player health access
        self._check_nonexistent_player_health_access(code, issues, sugg)
        
        # NEW: Check for direct player position manipulation
        self._check_direct_player_position_manipulation(code, issues, sugg)
        
        # NEW: Check for missing variable declarations
        self._check_missing_variable_declarations(code, issues, sugg)
        
        # NEW: Check for wrong flag usage
        self._check_wrong_flag_usage(code, issues, sugg)
        
        # NEW: Enhanced check for non-existent drawing functions
        self._check_nonexistent_drawing_functions_enhanced(code, issues, sugg)
        
        # NEW: Check for authentic patterns (positive validation)
        self._check_authentic_patterns(code, issues, sugg)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=sugg,
            authentic_patterns=pats,
            required_context=[]
        )

    # ------------------------ private helpers ---------------

    def _validate_enemy_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        
        # Check for non-existent functions/constants
        self._check_nonexistent_patterns(s, issues, sugg)
        
        # More flexible validation for actor creation scenarios
        actor_keywords = ["actor", "enemy", "boss", "attack", "damage", "state", "create", "implement", "build"]
        has_actor_content = any(keyword in s.lower() for keyword in actor_keywords)
        
        if not has_actor_content:
            issues.append("Scenario does not mention concrete actor/enemy behaviour")
            sugg.append("Describe the actor's behavior, states, or goals (e.g., 'charges player when low health', 'creates a switch that activates when player stands on it')")
        
        pats.extend([
            "Use Actor_WorldDistXZToActor for distance checks",
            "State machine via `actionState` field",
            "Damage via Actor_ApplyDamage + Enemy_StartFinishingBlow",
            "Collision with Collider_InitCylinder + CollisionCheck_SetAC",
            "Animation with SkelAnime_InitFlex + SkelAnime_Update",
        ])
        return issues, sugg, pats

    def _validate_npc_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        
        # Check for non-existent patterns
        self._check_nonexistent_patterns(s, issues, sugg)
        
        if "dialog" not in s.lower() and "shop" not in s.lower():
            sugg.append("Mention dialogue, shop or quest behaviour to clarify NPC role")
        pats.extend([
            "Dialogue via Npc_UpdateTalking and TEXT_STATE_CLOSING",
            "Tracking with NpcInteractInfo structure",
            "Text IDs handled in GetTextId function",
        ])
        return issues, sugg, pats

    def _validate_item_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        
        # Check for non-existent patterns
        self._check_nonexistent_patterns(s, issues, sugg)
        
        if not re.search(r"item|rupee|heart|key|mask", s, re.I):
            issues.append("Missing explicit item type")
        pats.append("Spawn with EnItem00 and ITEM00_* params")
        pats.extend([
            "Use EnItem00 for collectibles",
            "ITEM00_* constants for types",
            "Bobbing animation via Math_SinS",
        ])
        return issues, sugg, pats

    def _validate_object_scenario(self, s: str) -> Tuple[List[str], List[str], List[str]]:
        issues, sugg, pats = [], [], []
        
        # Check for non-existent patterns
        self._check_nonexistent_patterns(s, issues, sugg)
        
        if not re.search(r"switch|platform|door|mechanism|puzzle", s, re.I):
            sugg.append("Specify mechanism type (switch, platform, door, etc.)")
        pats.extend([
            "Use DynaPolyActor for moving/mechanic objects",
            "Switch state toggled with Flags_Get/SetSwitch",
            "Movement with Math_ApproachF",
            "Collision via DynaPoly_SetBgActor",
        ])
        return issues, sugg, pats

    def _check_nonexistent_patterns(self, text: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for non-existent functions, constants, and patterns using dynamic authentic sets, but skip user-defined symbols."""
        # --- Extract user-defined symbols ---
        user_defined_funcs = set()
        user_defined_consts = set()
        user_defined_types = set()

        # Function definitions (static or global)
        func_def_pattern = re.compile(r'^[ \t]*(?:static[ \t]+)?(?:[A-Za-z_][A-Za-z0-9_\* ]+)[ \t]+([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{', re.MULTILINE)
        for match in func_def_pattern.finditer(text):
            user_defined_funcs.add(match.group(1))

        # Macro/constant definitions - IMPROVED to catch more patterns
        macro_pattern = re.compile(r'^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)', re.MULTILINE)
        for match in macro_pattern.finditer(text):
            user_defined_consts.add(match.group(1))
            
        # Also catch constants defined in #define macros that reference other constants
        macro_ref_pattern = re.compile(r'#define\s+([A-Z][A-Z0-9_]*)\s*\([^)]*\)')
        for match in macro_ref_pattern.finditer(text):
            user_defined_consts.add(match.group(1))

        # Typedef struct/enum/union
        typedef_pattern = re.compile(r'typedef\s+(?:struct|enum|union)\s*\w*\s*\{[^}]+\}\s*([A-Za-z_][A-Za-z0-9_]*);', re.DOTALL)
        for match in typedef_pattern.finditer(text):
            user_defined_types.add(match.group(1))

        # Extract enum values from enum definitions - IMPROVED
        enum_pattern = re.compile(r'typedef\s+enum\s*\w*\s*\{([^}]+)\}', re.DOTALL)
        for match in enum_pattern.finditer(text):
            enum_body = match.group(1)
            # Extract enum values (lines that look like constants)
            for line in enum_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    # Extract constant name (before comma or comment)
                    const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                    if const_match:
                        user_defined_consts.add(const_match.group(1))

        # Extract enum values from inline enum definitions - IMPROVED
        inline_enum_pattern = re.compile(r'enum\s*\w*\s*\{([^}]+)\}', re.DOTALL)
        for match in inline_enum_pattern.finditer(text):
            enum_body = match.group(1)
            for line in enum_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                    if const_match:
                        user_defined_consts.add(const_match.group(1))

        # Extract constants from enum definitions without typedef
        enum_def_pattern = re.compile(r'enum\s+[A-Za-z_][A-Za-z0-9_]*\s*\{([^}]+)\}', re.DOTALL)
        for match in enum_def_pattern.finditer(text):
            enum_body = match.group(1)
            for line in enum_body.split('\n'):
                line = line.strip()
                if line and not line.startswith('/*') and not line.startswith('//'):
                    const_match = re.match(r'([A-Z][A-Z0-9_]*)\s*(?:,|$)', line)
                    if const_match:
                        user_defined_consts.add(const_match.group(1))

        # Extract constants from #define statements with values
        define_value_pattern = re.compile(r'#define\s+([A-Z][A-Z0-9_]*)\s+[^\n]+')
        for match in define_value_pattern.finditer(text):
            user_defined_consts.add(match.group(1))

        # Extract constants from const declarations
        const_decl_pattern = re.compile(r'const\s+[A-Za-z_][A-Za-z0-9_]*\s+([A-Z][A-Z0-9_]*)\s*=')
        for match in const_decl_pattern.finditer(text):
            user_defined_consts.add(match.group(1))

        # Extract constants from static const declarations
        static_const_pattern = re.compile(r'static\s+const\s+[A-Za-z_][A-Za-z0-9_]*\s+([A-Z][A-Z0-9_]*)\s*=')
        for match in static_const_pattern.finditer(text):
            user_defined_consts.add(match.group(1))

        # --- Extract function calls ---
        func_pattern = re.compile(r'\b([A-Z][A-Za-z0-9_]*)\s*\(')
        found_funcs = set(match.group(1) for match in func_pattern.finditer(text))

        # --- Extract all-caps constants ---
        const_pattern = re.compile(r'\b([A-Z][A-Z0-9_]{2,})\b')
        found_consts = set(match.group(1) for match in const_pattern.finditer(text))

        # Known C keywords and builtins to ignore
        c_keywords = set(keyword.kwlist) | set(dir(builtins)) | {
            'NULL', 'TRUE', 'FALSE', 'bool', 'int', 'float', 'double', 'char', 'void', 'size_t',
            'u8', 'u16', 'u32', 's8', 's16', 's32', 'f32', 'f64', 'uintptr_t', 'intptr_t',
            'struct', 'enum', 'union', 'typedef', 'const', 'static', 'extern', 'volatile',
            'register', 'unsigned', 'signed', 'short', 'long', 'inline', 'restrict',
            'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue', 'goto', 'return',
            'sizeof', 'offsetof',
            # Common C functions that should not be flagged
            'CLAMP', 'MIN', 'MAX', 'ABS', 'SIGN', 'ROUND', 'FLOOR', 'CEIL',
            'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh',
            'exp', 'log', 'log10', 'pow', 'sqrt', 'fabs', 'floor', 'ceil',
            'malloc', 'free', 'calloc', 'realloc', 'memcpy', 'memmove', 'memset',
            'strcpy', 'strcat', 'strcmp', 'strlen', 'strchr', 'strstr',
        }

        # --- Check functions ---
        for func in found_funcs:
            if func in user_defined_funcs:
                continue
            # Normalize function name to lowercase for comparison
            func_norm = func.lower()
            # --- FIX: Cross-check with constants database ---
            if func in self.patterns.AUTHENTIC_CONSTANTS:
                continue  # It's a macro/constant, not a function
            if func_norm not in self.patterns.AUTHENTIC_FUNCTIONS and func_norm not in c_keywords:
                # Debug: Check if the function exists in the database
                if func_norm in self.patterns.AUTHENTIC_FUNCTIONS:
                    logger.debug(f"Function {func} ({func_norm}) found in database but still flagged")
                else:
                    logger.debug(f"Function {func} ({func_norm}) NOT found in database")
                    # Debug: Show some functions that are in the database for comparison
                    sample_funcs = list(self.patterns.AUTHENTIC_FUNCTIONS)[:5]
                    logger.debug(f"Sample functions in database: {sample_funcs}")
                    # Direct check for specific functions
                    if func_norm in ['actor_setscale', 'collider_initcylinder', 'actor_playsfx']:
                        logger.debug(f"Direct check - {func_norm} in set: {func_norm in self.patterns.AUTHENTIC_FUNCTIONS}")
                        logger.debug(f"Set size: {len(self.patterns.AUTHENTIC_FUNCTIONS)}")
                        # Check if the function exists in the original file
                        with open('oot_valid_functions.txt', 'r') as f:
                            file_contents = f.read().lower()
                            if func_norm in file_contents:
                                logger.debug(f"{func_norm} found in file but not in set!")
                            else:
                                logger.debug(f"{func_norm} not found in file either")
                issues.append(f"Non-existent function: {func}")
                suggestions.append(f"Replace {func} with an authentic OoT function or define it in the code block")

        # --- Check constants (including sound effects) ---
        for const in found_consts:
            if const in user_defined_consts or const in user_defined_types:
                continue
                
            # Skip certain patterns that are commonly user-defined
            if const.startswith('ACTOR_EN_') or const.startswith('ACTOR_OBJ_') or const.startswith('ACTOR_BG_'):
                continue  # These are typically user-defined actor constants
                
            # Skip FLAGS as it's commonly user-defined
            if const == 'FLAGS':
                continue
                
            # Skip common romhacking constants that are user-defined
            romhacking_constants = {
                'COLTYPE_NONE', 'COLTYPE_HIT1', 'COLTYPE_HIT2', 'COLTYPE_HIT3',
                'COLSHAPE_CYLINDER', 'COLSHAPE_SPHERE', 'COLSHAPE_BOX', 'COLSHAPE_TRIS',
                'ELEMTYPE_UNK0', 'ELEMTYPE_UNK1', 'ELEMTYPE_UNK2', 'ELEMTYPE_UNK3',
                'TOUCH_NONE', 'TOUCH_ON', 'BUMP_ON', 'BUMP_NONE',
                'OC_ON', 'OC_NONE', 'OCELEM_ON', 'OCELEM_NONE',
                'AT_NONE', 'AT_ON', 'AC_ON', 'AC_NONE',
                'ACTORCAT_ENEMY', 'ACTORCAT_NPC', 'ACTORCAT_MISC', 'ACTORCAT_ITEMACTION',
                'ACTOR_FLAG_0', 'ACTOR_FLAG_1', 'ACTOR_FLAG_2', 'ACTOR_FLAG_3', 'ACTOR_FLAG_4', 'ACTOR_FLAG_5',
                'MASS_IMMOVABLE', 'MASS_50', 'MASS_40', 'MASS_30',
                'OBJECT_GAMEPLAY_KEEP', 'OBJECT_GAMEPLAY_DANGEON_KEEP',
                'UPDBGCHECKINFO_FLAG_0', 'UPDBGCHECKINFO_FLAG_2', 'UPDBGCHECKINFO_FLAG_4',
                'FLAGS_NONE', 'FLAGS_0', 'FLAGS_1', 'FLAGS_2', 'FLAGS_3', 'FLAGS_4', 'FLAGS_5'
            }
            if const in romhacking_constants:
                continue  # These are commonly used in romhacking and should not be flagged
                
            const_norm = const.lower()
            if const_norm.startswith('na_se_'):
                if const_norm not in self.patterns.AUTHENTIC_SOUND_EFFECTS:
                    issues.append(f"Non-existent sound effect: {const}")
                    suggestions.append(f"Replace {const} with an authentic OoT sound effect or define it in the code block")
            elif const_norm not in self.patterns.AUTHENTIC_CONSTANTS and const_norm not in self.patterns.AUTHENTIC_SOUND_EFFECTS:
                # Be more lenient with certain constant patterns
                if const.startswith('ACTOR_FLAG_') and const.endswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                    # These are commonly used in user-defined FLAGS macros, so be more lenient
                    if const not in ['ACTOR_FLAG_0', 'ACTOR_FLAG_1', 'ACTOR_FLAG_2', 'ACTOR_FLAG_3', 'ACTOR_FLAG_4', 'ACTOR_FLAG_5']:
                        issues.append(f"Non-existent constant: {const}")
                        suggestions.append(f"Replace {const} with authentic OoT actor flags like ACTOR_FLAG_TALK, ACTOR_FLAG_FRIENDLY, etc.")
                elif const.startswith('ACTORCAT_'):
                    # These are commonly used in ActorProfile, so be more lenient
                    if const not in ['ACTORCAT_ENEMY', 'ACTORCAT_NPC', 'ACTORCAT_ITEMACTION', 'ACTORCAT_MISC']:
                        issues.append(f"Non-existent constant: {const}")
                        suggestions.append(f"Replace {const} with authentic OoT actor categories like ACTORCAT_ENEMY, ACTORCAT_NPC, etc.")
                elif const.startswith('OBJECT_'):
                    # These are commonly used in ActorProfile, so be more lenient
                    if const not in ['OBJECT_GAMEPLAY_KEEP', 'OBJECT_GAMEPLAY_DANGEON_KEEP']:
                        issues.append(f"Non-existent constant: {const}")
                        suggestions.append(f"Replace {const} with an authentic OoT object constant or define it in the code block")
                else:
                    issues.append(f"Non-existent constant: {const}")
                    suggestions.append(f"Replace {const} with an authentic OoT constant or define it in the code block")

        # --- Check for incorrect ActorProfile usage ---
        if "ActorProfile" in text and "Profile" not in text:
            issues.append("Incorrect ActorProfile usage")
            suggestions.append("Use 'Profile' suffix for actor profiles (e.g., 'En_Shopnuts_Profile')")

        # --- Check for incorrect function signatures ---
        if "void" in text and "Actor* thisx" not in text and "PlayState* play" not in text:
            if any(func in text for func in ["Init(", "Update(", "Draw(", "Destroy("]):
                issues.append("Missing correct function signatures")
                suggestions.append("Use (Actor* thisx, PlayState* play) for all actor functions")

    def _check_missing_oot_patterns(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for missing essential OoT patterns."""
        
        # Check for proper actor struct definition
        if "typedef struct" in code and "Actor actor;" not in code:
            issues.append("Missing base Actor field in struct definition")
            suggestions.append("Include 'Actor actor;' as the first field in your struct")
        
        # Check for proper size comment
        if "typedef struct" in code and "// size = " not in code and "/* size = " not in code:
            issues.append("Missing size comment in struct definition")
            suggestions.append("Add '// size = 0xXXXX' comment after struct definition")
        
        # Check for proper field offsets
        if "typedef struct" in code:
            offset_pattern = r'/\* 0x[0-9A-F]{4} \*/'
            if not re.search(offset_pattern, code):
                issues.append("Missing field offset comments")
                suggestions.append("Add offset comments like '/* 0x014C */' before each field")
        
        # Check for proper function naming convention
        if "void" in code and "Init(" in code:
            func_pattern = r'void\s+([A-Za-z_]+)_Init\s*\('
            if not re.search(func_pattern, code):
                issues.append("Incorrect Init function naming")
                suggestions.append("Use 'ActorName_Init' naming convention")
        
        # Check for proper ActorProfile naming
        if "ActorProfile" in code:
            profile_pattern = r'const ActorProfile\s+([A-Za-z_]+)_Profile'
            if not re.search(profile_pattern, code):
                issues.append("Incorrect ActorProfile naming")
                suggestions.append("Use 'ActorName_Profile' naming convention")

    def _check_struct_patterns(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for proper OoT struct patterns."""
        
        # Check for proper field types
        if "typedef struct" in code:
            # Check for common OoT types
            oot_types = ["s16", "u16", "s32", "u32", "f32", "Vec3f", "Vec3s", "ColliderCylinder"]
            found_oot_types = any(t in code for t in oot_types)
            if not found_oot_types:
                issues.append("Missing OoT-specific field types")
                suggestions.append("Use OoT types like s16, u16, f32, Vec3f, ColliderCylinder")
            
            # Check for proper field ordering
            if "Actor actor;" in code:
                # Actor should be first field
                lines = code.split('\n')
                actor_line = -1
                for i, line in enumerate(lines):
                    if "Actor actor;" in line:
                        actor_line = i
                        break
                
                if actor_line > 0:
                    # Check if there are other fields before Actor
                    for i in range(actor_line):
                        if re.search(r'[a-zA-Z_][a-zA-Z0-9_]*\s+[a-zA-Z_][a-zA-Z0-9_]*;', lines[i]):
                            issues.append("Actor field should be first in struct")
                            suggestions.append("Move 'Actor actor;' to be the first field")
                            break

    def _check_actor_profile(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for proper ActorProfile definition."""
        
        if "ActorProfile" not in code:
            issues.append("Missing ActorProfile definition")
            suggestions.append("Add ActorProfile struct with proper fields (actorId, category, flags, object, size, init, destroy, update, draw)")
        else:
            # Check for proper ActorProfile structure
            required_fields = ["ACTOR_", "ACTORCAT_", "FLAGS", "OBJECT_", "sizeof", "Init", "Destroy", "Update", "Draw"]
            missing_fields = [field for field in required_fields if field not in code]
            if missing_fields:
                issues.append(f"Missing ActorProfile fields: {', '.join(missing_fields)}")
                suggestions.append("Include all required ActorProfile fields")

    def _check_collider_init_structs(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for proper ColliderInit struct definitions."""
        
        if "Collider_InitCylinder" in code or "Collider_SetCylinder" in code:
            # Should have corresponding ColliderCylinderInit struct
            if "ColliderCylinderInit" not in code and "sCylinderInit" not in code:
                issues.append("Missing ColliderCylinderInit struct definition")
                suggestions.append("Define static ColliderCylinderInit struct with proper collision flags and dimensions")
            
            # Check for proper collision setup pattern
            if "Collider_SetCylinder" in code and "&sCylinderInit" not in code:
                issues.append("Missing ColliderCylinderInit reference")
                suggestions.append("Use '&sCylinderInit' as the last parameter in Collider_SetCylinder")

    def _check_function_signatures(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for proper OoT function signatures."""
        
        # Check Init function signature
        if "Init(" in code:
            if "Actor* thisx, PlayState* play" not in code:
                issues.append("Incorrect Init function signature")
                suggestions.append("Use 'void ActorName_Init(Actor* thisx, PlayState* play)' signature")
        
        # Check Update function signature
        if "Update(" in code:
            if "Actor* thisx, PlayState* play" not in code:
                issues.append("Incorrect Update function signature")
                suggestions.append("Use 'void ActorName_Update(Actor* thisx, PlayState* play)' signature")
        
        # Check Draw function signature
        if "Draw(" in code:
            if "Actor* thisx, PlayState* play" not in code:
                issues.append("Incorrect Draw function signature")
                suggestions.append("Use 'void ActorName_Draw(Actor* thisx, PlayState* play)' signature")
        
        # Check for proper casting pattern
        if "Init(" in code or "Update(" in code or "Draw(" in code:
            if "ActorName* this = (ActorName*)thisx;" not in code and "thisx" in code:
                issues.append("Missing proper casting pattern")
                suggestions.append("Add 'ActorName* this = (ActorName*)thisx;' at start of function")

    def _check_majoras_mask_contamination(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for Majora's Mask content that doesn't belong in OoT."""
        
        # Check for transformation mask mechanics (Majora's Mask only)
        # These are specific to MM transformation system, not OoT Deku enemies/items
        majoras_mask_patterns = [
            "TRANSFORM_STATE_DEKU",
            "TRANSFORM_STATE_GORON", 
            "TRANSFORM_STATE_ZORA",
            "TRANSFORM_STATE_HUMAN",
            "TRANSFORM_STATE_",
            "transformState",
            "transformTimer", 
            "transformLock",
            "transformScale",
            "transformation",
            "mask mechanics", "transformation masks"
        ]
        
        for pattern in majoras_mask_patterns:
            if pattern in code:
                issues.append(f"CRITICAL: Majora's Mask content detected - '{pattern}' is from MM, not OoT")
                suggestions.append("Remove Majora's Mask transformation mechanics. OoT does not have mask transformations.")
                break
        
        # Check for MM-specific transformation references (not OoT Deku enemies/items)
        # These patterns indicate MM transformation system usage
        mm_transformation_patterns = [
            r'\bDeku\s+form\b',  # "Deku form" - MM transformation
            r'\bGoron\s+form\b', # "Goron form" - MM transformation  
            r'\bZora\s+form\b',  # "Zora form" - MM transformation
            r'\btransform\s+into\s+Deku\b',  # "transform into Deku" - MM
            r'\btransform\s+into\s+Goron\b', # "transform into Goron" - MM
            r'\btransform\s+into\s+Zora\b',  # "transform into Zora" - MM
            r'\bDeku\s+transformation\b',     # "Deku transformation" - MM
            r'\bGoron\s+transformation\b',    # "Goron transformation" - MM
            r'\bZora\s+transformation\b',     # "Zora transformation" - MM
        ]
        
        for pattern in mm_transformation_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"CRITICAL: Majora's Mask transformation content detected - '{pattern}' is from MM, not OoT")
                suggestions.append("Remove Majora's Mask transformation mechanics. OoT has Deku enemies/items but no transformation system.")
                break
        
        # Check for Majora's Mask specific constants
        mm_constants = [
            "BGCHECKFLAG_LAVA",  # This doesn't exist in OoT
            "WaterBox_GetSurface1",  # Wrong function signature for OoT
            "ACTORCAT_PLAYER"  # Reserved for player actor only
        ]
        
        for constant in mm_constants:
            if constant in code:
                if constant == "BGCHECKFLAG_LAVA":
                    issues.append("CRITICAL: BGCHECKFLAG_LAVA does not exist in OoT")
                    suggestions.append("Use BGCHECKFLAG_WATER for water detection. Lava detection uses different methods in OoT.")
                elif constant == "WaterBox_GetSurface1":
                    issues.append("CRITICAL: WaterBox_GetSurface1 has wrong signature for OoT")
                    suggestions.append("Use authentic OoT water detection patterns from collision system.")
                elif constant == "ACTORCAT_PLAYER":
                    issues.append("CRITICAL: ACTORCAT_PLAYER is reserved for player actor only")
                    suggestions.append("Use ACTORCAT_NPC, ACTORCAT_MISC, ACTORCAT_PROP, or ACTORCAT_ENEMY for custom actors.")
                break

    def _check_incorrect_bgcheck_usage(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect background check function usage."""
        
        # Check for wrong Actor_UpdateBgCheckInfo signature
        if "Actor_UpdateBgCheckInfo" in code:
            # Look for the specific wrong signature pattern
            wrong_pattern = r'Actor_UpdateBgCheckInfo\s*\(\s*play,\s*&this->actor,\s*26\.0f,\s*10\.0f,\s*0\.0f'
            if re.search(wrong_pattern, code):
                issues.append("CRITICAL: Wrong Actor_UpdateBgCheckInfo parameters")
                suggestions.append("Use authentic signature: Actor_UpdateBgCheckInfo(play, &this->actor, 35.0f, 60.0f, 60.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2)")
            
            # Check for missing flags parameter
            if "UPDBGCHECKINFO_FLAG_0" not in code and "Actor_UpdateBgCheckInfo" in code:
                issues.append("Missing UPDBGCHECKINFO flags in Actor_UpdateBgCheckInfo")
                suggestions.append("Add UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2 as the last parameter")

    def _check_incorrect_water_detection(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect water detection patterns."""
        
        # Check for wrong WaterBox function usage
        if "WaterBox_GetSurface1" in code:
            issues.append("CRITICAL: WaterBox_GetSurface1 has wrong signature for OoT")
            suggestions.append("Use authentic OoT water detection patterns from collision system")
        
        # Check for non-existent water detection patterns
        wrong_water_patterns = [
            r'WaterBox_GetSurface1\s*\(\s*play,\s*&play->colCtx',
            r'waterSurface',
            r'waterBox'
        ]
        
        for pattern in wrong_water_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Non-authentic water detection pattern")
                suggestions.append("Use authentic OoT water detection methods from collision system")

    def _check_incorrect_actor_categories(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect actor category usage."""
        
        # Check for reserved actor categories
        reserved_categories = ["ACTORCAT_PLAYER"]
        for category in reserved_categories:
            if category in code:
                issues.append(f"CRITICAL: {category} is reserved for system actors only")
                suggestions.append(f"Use ACTORCAT_NPC, ACTORCAT_MISC, ACTORCAT_PROP, or ACTORCAT_ENEMY instead of {category}")
        
        # Check for valid actor categories
        valid_categories = [
            "ACTORCAT_ENEMY", "ACTORCAT_NPC", "ACTORCAT_ITEMACTION", "ACTORCAT_MISC", 
            "ACTORCAT_PROP", "ACTORCAT_BG", "ACTORCAT_DOOR", "ACTORCAT_CHEST"
        ]
        
        # If ActorProfile is present, check if it uses a valid category
        if "ActorProfile" in code and "ACTORCAT_" in code:
            found_valid = False
            for valid_cat in valid_categories:
                if valid_cat in code:
                    found_valid = True
                    break
            
            if not found_valid:
                issues.append("CRITICAL: Invalid actor category in ActorProfile")
                suggestions.append("Use one of: ACTORCAT_ENEMY, ACTORCAT_NPC, ACTORCAT_ITEMACTION, ACTORCAT_MISC, ACTORCAT_PROP")

    def _check_fabricated_patterns(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for fabricated patterns that don't exist in OoT."""
        
        # Check for fabricated item checking patterns
        fabricated_item_patterns = [
            r'INV_CONTENT\s*\(\s*[^)]+\s*\)\s*==\s*ITEM_NONE\s*\?\s*1\s*:',
            r'gSaveContext\.inventory\.items\[INV_CONTENT\(',
            r'INV_CONTENT\s*\(\s*this->requiredItem\s*\)'
        ]
        
        for pattern in fabricated_item_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Non-existent item checking pattern")
                suggestions.append("Use authentic OoT patterns: if (gSaveContext.inventory.items[SLOT_HOOKSHOT] != ITEM_NONE) { ... }")
                break
        
        # Check for wrong actor traversal patterns
        wrong_traversal_patterns = [
            r'play->actorCtx\.actorLists\[ACTORCAT_\w+\]\.head',
            r'nearbyActor\s*=\s*nearbyActor->next',
            r'while\s*\(\s*nearbyActor\s*!=\s*NULL\s*\)'
        ]
        
        for pattern in wrong_traversal_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Incorrect actor traversal pattern")
                suggestions.append("OoT doesn't expose actor lists this way. Use Actor_FindNearby() or iterate through specific actor types.")
                break
        
        # Check for non-existent drawing functions
        non_existent_drawing = [
            r'Actor_DrawOpa\s*\(',
            r'Actor_DrawModel\s*\(',
            r'Actor_DrawMesh\s*\(',
            r'Actor_RenderModel\s*\(',
            r'Actor_DrawScale\s*\('
        ]
        
        for pattern in non_existent_drawing:
            if re.search(pattern, code):
                issues.append("FABRICATED: Non-existent drawing function")
                suggestions.append("Use authentic OoT drawing: SkelAnime_DrawOpa() or Gfx_DrawDListOpa()")
                break
        
        # Check for wrong distance functions
        wrong_distance_patterns = [
            r'Actor_WorldDistXZToPoint\s*\(\s*&player->actor,\s*&this->actor\.world\.pos\s*\)',
            r'Math_Vec3f_DistXYZ\s*\(\s*&player->actor\.world\.pos,\s*&this->actor\.world\.pos\s*\)'
        ]
        
        for pattern in wrong_distance_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Incorrect distance calculation")
                suggestions.append("Use authentic patterns: Actor_WorldDistXZToActor(&this->actor, &player->actor) or manual sqrtf(SQ(dx) + SQ(dz))")
                break
        
        # Check for non-existent En_Item00 structure access
        wrong_item00_patterns = [
            r'EnItem00\*\s*item\s*=\s*\(EnItem00\*\)nearbyActor',
            r'item->collectibleFlag',
            r'EnItem00\*.*=.*\(EnItem00\*\)'
        ]
        
        for pattern in wrong_item00_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Non-existent En_Item00 structure access")
                suggestions.append("En_Item00 doesn't expose collectibleFlag this way. Use Actor_Spawn() with ITEM00_* parameters instead.")
                break
        
        # Check for wrong inventory access patterns
        wrong_inventory_patterns = [
            r'gSaveContext\.inventory\.items\[INV_CONTENT\(',
            r'INV_CONTENT\s*\(\s*this->requiredItem\s*\)\s*==\s*ITEM_NONE'
        ]
        
        for pattern in wrong_inventory_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Wrong inventory checking pattern")
                suggestions.append("Use authentic patterns: if (gSaveContext.inventory.items[SLOT_HOOKSHOT] != ITEM_NONE) { ... }")
                break
        
        # Check for wrong actor iteration patterns
        wrong_iteration_patterns = [
            r'Actor\*\s*nearbyActor\s*=\s*play->actorCtx\.actorLists\[ACTORCAT_\w+\]\.head',
            r'while\s*\(\s*nearbyActor\s*!=\s*NULL\s*\)\s*\{',
            r'nearbyActor\s*=\s*nearbyActor->next'
        ]
        
        for pattern in wrong_iteration_patterns:
            if re.search(pattern, code):
                issues.append("FABRICATED: Wrong actor iteration pattern")
                suggestions.append("OoT doesn't expose actor lists this way. Use Actor_FindNearby() or specific actor type checks.")
                break

    def _check_authentic_patterns(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for authentic OoT patterns that should be used instead."""
        
        # Check if code uses authentic patterns correctly
        authentic_patterns = {
            # Distance calculations
            r'Actor_WorldDistXZToActor\s*\(\s*&this->actor,\s*&player->actor\s*\)': "✅ Correct distance calculation",
            r'sqrtf\s*\(\s*SQ\s*\(\s*dx\s*\)\s*\+\s*SQ\s*\(\s*dz\s*\)\s*\)': "✅ Correct manual distance calculation",
            
            # Drawing functions
            r'SkelAnime_DrawOpa\s*\(': "✅ Correct skeleton drawing",
            r'Gfx_DrawDListOpa\s*\(': "✅ Correct display list drawing",
            
            # Item checking
            r'gSaveContext\.inventory\.items\[SLOT_\w+\]\s*!=\s*ITEM_NONE': "✅ Correct item checking",
            
            # Actor spawning
            r'Actor_Spawn\s*\(\s*&play->actorCtx,\s*play,\s*ACTOR_EN_ITEM00': "✅ Correct item spawning",
            
            # Collision checking
            r'CollisionCheck_SetOC\s*\(': "✅ Correct collision checking",
            r'CollisionCheck_SetAC\s*\(': "✅ Correct collision checking",
            
            # Background checking
            r'Actor_UpdateBgCheckInfo\s*\(\s*play,\s*&this->actor,\s*35\.0f,\s*60\.0f,\s*60\.0f,\s*UPDBGCHECKINFO_FLAG_0\s*\|\s*UPDBGCHECKINFO_FLAG_2\s*\)': "✅ Correct background checking"
        }
        
        found_authentic = []
        for pattern, message in authentic_patterns.items():
            if re.search(pattern, code):
                found_authentic.append(message)
        
        if found_authentic:
            # This is good - we found authentic patterns
            pass  # Could add positive feedback here if desired

    def _check_syntax_errors(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for critical syntax errors that will prevent compilation."""
        
        # Check for broken sqrtf() syntax
        broken_sqrt_patterns = [
            r'sqrtf\s*\(\s*SQ\s*\(\s*[^)]+\s*\)\s*\+\s*SQ\s*\(\s*[^)]+\s*\)\s*\)\s*\(\s*[^)]+\s*,\s*[^)]+\s*\)',
            r'sqrtf\s*\(\s*[^)]+\s*\)\s*\(\s*[^)]+\s*,\s*[^)]+\s*\)',
            r'sqrtf\s*\(\s*[^)]+\s*\)\s*\(\s*&[^)]+->[^)]+\.world\.pos\s*,\s*&[^)]+->[^)]+\.world\.pos\s*\)'
        ]
        
        for pattern in broken_sqrt_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Broken sqrtf() syntax - function call with wrong parameters")
                suggestions.append("Fix syntax: f32 dx = player->actor.world.pos.x - this->actor.world.pos.x; f32 dz = player->actor.world.pos.z - this->actor.world.pos.z; if (sqrtf(SQ(dx) + SQ(dz)) < 20.0f) {")
                break
        
        # Check for other common syntax errors
        syntax_errors = [
            # Missing semicolons
            (r'[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[^;]+[^;]\s*\n', "Missing semicolon at end of statement"),
            # Broken function calls
            (r'[a-zA-Z_][a-zA-Z0-9_]*\s*\(\s*[^)]*\(\s*[^)]*\)[^)]*\)', "Broken nested function call syntax"),
            # Wrong operator precedence
            (r'[^&]\s*&\s*[A-Z_][A-Z0-9_]*\s*\|\s*[A-Z_][A-Z0-9_]*', "Wrong operator precedence - use parentheses around bitwise operations")
        ]
        
        for pattern, message in syntax_errors:
            if re.search(pattern, code):
                issues.append(f"CRITICAL: {message}")
                suggestions.append("Fix syntax error to ensure code compiles")

    def _check_wrong_bgcheck_flags(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect background check flag usage."""
        
        # Check for wrong flag checking patterns
        wrong_flag_patterns = [
            r'this->actor\.bgCheckFlags\s*&\s*UPDBGCHECKINFO_FLAG_0',
            r'this->actor\.bgCheckFlags\s*&\s*UPDBGCHECKINFO_FLAG_2',
            r'this->actor\.bgCheckFlags\s*&\s*UPDBGCHECKINFO_FLAG_4',
            r'bgCheckFlags\s*&\s*UPDBGCHECKINFO_FLAG_'
        ]
        
        for pattern in wrong_flag_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong background check flag usage")
                suggestions.append("UPDBGCHECKINFO_FLAG_* are input flags for Actor_UpdateBgCheckInfo(), not output flags. Use BGCHECKFLAG_GROUND, BGCHECKFLAG_WATER, etc. for checking contact.")
                break
        
        # Check for correct flag usage patterns
        correct_flag_patterns = [
            r'this->actor\.bgCheckFlags\s*&\s*BGCHECKFLAG_GROUND',
            r'this->actor\.bgCheckFlags\s*&\s*BGCHECKFLAG_WATER',
            r'this->actor\.bgCheckFlags\s*&\s*BGCHECKFLAG_WALL',
            r'bgCheckFlags\s*&\s*BGCHECKFLAG_'
        ]
        
        # If Actor_UpdateBgCheckInfo is used, check for correct input flags
        if "Actor_UpdateBgCheckInfo" in code:
            correct_input_flags = [
                r'Actor_UpdateBgCheckInfo\s*\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*UPDBGCHECKINFO_FLAG_0\s*\|\s*UPDBGCHECKINFO_FLAG_2\s*\)',
                r'Actor_UpdateBgCheckInfo\s*\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*UPDBGCHECKINFO_FLAG_0\s*\)',
                r'Actor_UpdateBgCheckInfo\s*\(\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*UPDBGCHECKINFO_FLAG_2\s*\)'
            ]
            
            found_correct = False
            for pattern in correct_input_flags:
                if re.search(pattern, code):
                    found_correct = True
                    break
            
            if not found_correct:
                issues.append("CRITICAL: Missing or incorrect UPDBGCHECKINFO flags in Actor_UpdateBgCheckInfo")
                suggestions.append("Use UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2 as the last parameter in Actor_UpdateBgCheckInfo")

    def _check_nonexistent_drawing_functions(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for non-existent drawing functions."""
        
        # Check for fabricated drawing functions
        fabricated_drawing = [
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
                issues.append("CRITICAL: Non-existent drawing function")
                suggestions.append("Use authentic OoT drawing: SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this) or Gfx_DrawDListOpa(play, gObjectDL)")
                break
        
        # Check for correct drawing patterns
        correct_drawing_patterns = [
            r'SkelAnime_DrawOpa\s*\(\s*play,\s*this->skelAnime\.skeleton,\s*this->skelAnime\.jointTable',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*g[A-Z][a-zA-Z0-9_]*DL\s*\)',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[a-z][a-zA-Z0-9_]*DL\s*\)'
        ]
        
        # If drawing is mentioned but no correct patterns found
        if ("Draw" in code or "draw" in code) and not any(re.search(pattern, code) for pattern in correct_drawing_patterns):
            if any(re.search(pattern, code) for pattern in fabricated_drawing):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic drawing function")
                suggestions.append("Use SkelAnime_DrawOpa() for skeleton animation or Gfx_DrawDListOpa() for display lists")

    def _check_incorrect_animation_blending(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect animation blending patterns."""
        
        # Check for manual joint interpolation (not how OoT works)
        manual_blending_patterns = [
            r'for\s*\(\s*[^)]+\s*\)\s*\{\s*[^}]*baseJoints\[[^]]+\]\.x\s*=\s*baseJoints\[[^]]+\]\.x\s*\+',
            r'for\s*\(\s*[^)]+\s*\)\s*\{\s*[^}]*blendJoints\[[^]]+\]\.x\s*-\s*baseJoints\[[^]]+\]\.x\s*\)\s*\*\s*this->blendWeight',
            r'manual\s+joint\s+interpolation',
            r'baseJoints\[[^]]+\]\.x\s*=\s*baseJoints\[[^]]+\]\.x\s*\+\s*\(\s*blendJoints\[[^]]+\]\.x\s*-\s*baseJoints\[[^]]+\]\.x\s*\)\s*\*\s*this->blendWeight'
        ]
        
        for pattern in manual_blending_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Manual joint interpolation doesn't match OoT's animation system")
                suggestions.append("OoT uses Animation_Change() with morph frames for blending, not manual joint interpolation. Use Animation_Change(&skelAnime, &targetAnim, 1.0f, 0.0f, lastFrame, ANIMMODE_LOOP, 0.0f)")
                break
        
        # Check for correct animation blending patterns
        correct_blending_patterns = [
            r'Animation_Change\s*\(\s*&this->skelAnime,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*ANIMMODE_LOOP',
            r'Animation_Change\s*\(\s*&this->skelAnime,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*ANIMMODE_ONCE',
            r'Animation_Change\s*\(\s*&this->skelAnime,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*ANIMMODE_BLEND'
        ]
        
        # If animation blending is mentioned but no correct patterns found
        if ("blend" in code.lower() or "blending" in code.lower()) and not any(re.search(pattern, code) for pattern in correct_blending_patterns):
            if any(re.search(pattern, code) for pattern in manual_blending_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic animation blending")
                suggestions.append("Use Animation_Change() with proper parameters for OoT animation blending")

    def _check_incorrect_math_functions(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect math function usage."""
        
        # Check for wrong distance calculation patterns
        wrong_distance_patterns = [
            r'sqrtf\s*\(\s*SQ\s*\(\s*[^)]+\s*\)\s*\+\s*SQ\s*\(\s*[^)]+\s*\)\s*\)\s*\(\s*[^)]+\s*,\s*[^)]+\s*\)',
            r'Math_Vec3f_DistXYZ\s*\(\s*&[^)]+->[^)]+\.world\.pos\s*,\s*&[^)]+->[^)]+\.world\.pos\s*\)',
            r'Actor_WorldDistXZToPoint\s*\(\s*&[^)]+->[^)]+\.world\.pos\s*,\s*&[^)]+->[^)]+\.world\.pos\s*\)'
        ]
        
        for pattern in wrong_distance_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Incorrect distance calculation")
                suggestions.append("Use authentic patterns: Actor_WorldDistXZToActor(&this->actor, &player->actor) or manual f32 dx = x1 - x2; f32 dz = z1 - z2; sqrtf(SQ(dx) + SQ(dz))")
                break
        
        # Check for correct distance patterns
        correct_distance_patterns = [
            r'Actor_WorldDistXZToActor\s*\(\s*&this->actor,\s*&player->actor\s*\)',
            r'f32\s+dx\s*=\s*[^;]+\.x\s*-\s*[^;]+\.x;\s*f32\s+dz\s*=\s*[^;]+\.z\s*-\s*[^;]+\.z;\s*if\s*\(\s*sqrtf\s*\(\s*SQ\s*\(\s*dx\s*\)\s*\+\s*SQ\s*\(\s*dz\s*\)\s*\)\s*<\s*[^)]+\)'
        ]
        
        # If distance checking is mentioned but no correct patterns found
        if ("dist" in code.lower() or "distance" in code.lower()) and not any(re.search(pattern, code) for pattern in correct_distance_patterns):
            if any(re.search(pattern, code) for pattern in wrong_distance_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic distance calculation")
                suggestions.append("Use Actor_WorldDistXZToActor(&this->actor, &player->actor) for distance checks")

    def _check_incorrect_struct_access(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect struct field access patterns."""
        
        # Check for wrong position access
        wrong_pos_patterns = [
            r'this->actor\.pos\.',
            r'player->actor\.pos\.',
            r'actor\.pos\.',
            r'this->actor\.rot\.',
            r'player->actor\.rot\.',
            r'actor\.rot\.'
        ]
        
        for pattern in wrong_pos_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong position/rotation access")
                suggestions.append("Use actor.world.pos and actor.world.rot, not actor.pos or actor.rot")
                break
        
        # Check for correct position access patterns
        correct_pos_patterns = [
            r'this->actor\.world\.pos\.',
            r'player->actor\.world\.pos\.',
            r'actor\.world\.pos\.',
            r'this->actor\.world\.rot\.',
            r'player->actor\.world\.rot\.',
            r'actor\.world\.rot\.'
        ]
        
        # If position access is mentioned but no correct patterns found
        if (".pos." in code or ".rot." in code) and not any(re.search(pattern, code) for pattern in correct_pos_patterns):
            if any(re.search(pattern, code) for pattern in wrong_pos_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic position access")
                suggestions.append("Use actor.world.pos and actor.world.rot for position and rotation access")

    # ------------------------ context templates -------------

    def _build_context_templates(self) -> Dict[str, str]:
        tpl = {}
        tpl["enemy"] = (
            "AUTHENTIC ENEMY PATTERNS:\n"
            "- Collider_InitCylinder for body\n"
            "- actionState enum controlling AI\n"
            "- Damage handled with Actor_ApplyDamage\n"
            "- Distance checks via Actor_WorldDistXZToActor\n"
            "- Use Actor_PlaySfx for sound effects\n"
            "- State machine with actionFunc pointer\n"
            "- REQUIRED: ActorProfile struct at end\n"
            "- REQUIRED: ColliderCylinderInit static struct\n"
            "- REQUIRED: Proper struct with Actor as first field\n"
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)\n"
            "\n🚨 CRITICAL WARNINGS:\n"
            "✗ NEVER use Gfx_DrawDListOpa(play, gSomeDL) - this function doesn't exist\n"
            "✗ NEVER directly manipulate player->actor.world.pos or player->actor.velocity\n"
            "✗ NEVER access player->health or player->healthCapacity\n"
            "✗ NEVER use SkelAnime functions without declaring SkelAnime in struct\n"
            "✗ NEVER use ACTOR_FLAG_8 or other non-existent flags\n"
            "✓ Use SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this)\n"
            "✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health\n"
            "✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)\n"
            "✓ Declare SkelAnime skelAnime; in struct if using skeleton animation"
        )
        tpl["npc"] = (
            "AUTHENTIC NPC PATTERNS:\n"
            "- Dialogue via Npc_UpdateTalking\n"
            "- Text IDs handled in GetTextId function\n"
            "- Tracking player with NpcInteractInfo\n"
            "- Use Actor_PlaySfx for sound effects\n"
            "- State machine with actionFunc pointer\n"
            "- REQUIRED: ActorProfile struct at end\n"
            "- REQUIRED: ColliderCylinderInit static struct\n"
            "- REQUIRED: Proper struct with Actor as first field\n"
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)\n"
            "\n🚨 CRITICAL WARNINGS:\n"
            "✗ NEVER use Gfx_DrawDListOpa(play, gSomeDL) - this function doesn't exist\n"
            "✗ NEVER directly manipulate player->actor.world.pos or player->actor.velocity\n"
            "✗ NEVER access player->health or player->healthCapacity\n"
            "✗ NEVER use SkelAnime functions without declaring SkelAnime in struct\n"
            "✗ NEVER use ACTOR_FLAG_8 or other non-existent flags\n"
            "✓ Use SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this)\n"
            "✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health\n"
            "✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)\n"
            "✓ Declare SkelAnime skelAnime; in struct if using skeleton animation"
        )
        tpl["item"] = (
            "AUTHENTIC ITEM PATTERNS:\n"
            "- Use EnItem00 for collectibles\n"
            "- ITEM00_* constants for types\n"
            "- Bobbing animation via Math_SinS\n"
            "- Use Actor_PlaySfx for sound effects\n"
            "- Collision with Collider_InitCylinder\n"
            "- REQUIRED: ActorProfile struct at end\n"
            "- REQUIRED: ColliderCylinderInit static struct\n"
            "- REQUIRED: Proper struct with Actor as first field\n"
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)\n"
            "\n🚨 CRITICAL WARNINGS:\n"
            "✗ NEVER use Gfx_DrawDListOpa(play, gSomeDL) - this function doesn't exist\n"
            "✗ NEVER directly manipulate player->actor.world.pos or player->actor.velocity\n"
            "✗ NEVER access player->health or player->healthCapacity\n"
            "✗ NEVER use SkelAnime functions without declaring SkelAnime in struct\n"
            "✗ NEVER use ACTOR_FLAG_8 or other non-existent flags\n"
            "✓ Use SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this)\n"
            "✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health\n"
            "✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)\n"
            "✓ Declare SkelAnime skelAnime; in struct if using skeleton animation"
        )
        tpl["object"] = (
            "AUTHENTIC OBJECT PATTERNS:\n"
            "- Mechanics via DynaPolyActor\n"
            "- Switch state toggled with Flags_Get/SetSwitch\n"
            "- Movement with Math_ApproachF\n"
            "- Use Actor_PlaySfx for sound effects\n"
            "- Collision via DynaPoly_SetBgActor\n"
            "- REQUIRED: ActorProfile struct at end\n"
            "- REQUIRED: ColliderCylinderInit static struct\n"
            "- REQUIRED: Proper struct with Actor as first field\n"
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)\n"
            "- AUTHENTIC PATTERNS ONLY:\n"
            "  ✓ Use Actor_WorldDistXZToActor(&this->actor, &player->actor) for distance\n"
            "  ✓ Use SkelAnime_DrawOpa() or Gfx_DrawDListOpa() for drawing\n"
            "  ✓ Use if (gSaveContext.inventory.items[SLOT_HOOKSHOT] != ITEM_NONE) for items\n"
            "  ✓ Use Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00, ...) for spawning\n"
            "  ✗ NEVER use fabricated patterns like INV_CONTENT(), Actor_DrawOpa(), etc.\n"
            "\n🚨 CRITICAL WARNINGS:\n"
            "✗ NEVER use Gfx_DrawDListOpa(play, gSomeDL) - this function doesn't exist\n"
            "✗ NEVER directly manipulate player->actor.world.pos or player->actor.velocity\n"
            "✗ NEVER access player->health or player->healthCapacity\n"
            "✗ NEVER use SkelAnime functions without declaring SkelAnime in struct\n"
            "✗ NEVER use ACTOR_FLAG_8 or other non-existent flags\n"
            "✓ Use SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this)\n"
            "✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health\n"
            "✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)\n"
            "✓ Declare SkelAnime skelAnime; in struct if using skeleton animation"
        )
        return tpl

    def _get_oot_pattern_examples(self, category: str) -> str:
        """Get OoT pattern examples for the given category."""
        examples = {
            "enemy": """
// CORRECT STRUCT PATTERN:
typedef struct {
    /* 0x0000 */ Actor actor;  // MUST be first field
    /* 0x014C */ ColliderCylinder collider;
    /* 0x01B0 */ s16 actionState;
    /* 0x01B2 */ s16 timer;
    /* 0x01B4 */ SkelAnime skelAnime;  // REQUIRED if using skeleton animation
} EnTest; // size = 0x01B4

// CORRECT FUNCTION SIGNATURES:
void EnTest_Init(Actor* thisx, PlayState* play) {
    EnTest* this = (EnTest*)thisx;  // REQUIRED casting
    // ... implementation
}

// CORRECT COLLIDER INIT:
static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_HIT5,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    { 25, 65, 0, { 0, 0, 0 } },
};

// CORRECT DRAWING (if using skeleton):
void EnTest_Draw(Actor* thisx, PlayState* play) {
    EnTest* this = (EnTest*)thisx;
    SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this);
}

// CORRECT PLAYER HEALTH ACCESS:
if (gSaveContext.health < gSaveContext.healthCapacity) {
    // Player needs healing
}

// CORRECT FLAG CHECKING:
if (this->actor.flags & ACTOR_FLAG_0) {
    // Flag is set
}

// CORRECT ACTORPROFILE:
const ActorProfile EnTest_Profile = {
    /**/ ACTOR_EN_TEST,
    /**/ ACTORCAT_ENEMY,
    /**/ FLAGS,
    /**/ OBJECT_SK2,
    /**/ sizeof(EnTest),
    /**/ EnTest_Init,
    /**/ EnTest_Destroy,
    /**/ EnTest_Update,
    /**/ EnTest_Draw,
};
""",
            "npc": """
// CORRECT STRUCT PATTERN:
typedef struct {
    /* 0x0000 */ Actor actor;  // MUST be first field
    /* 0x014C */ ColliderCylinder collider;
    /* 0x01B0 */ s16 talkState;
    /* 0x01B2 */ s16 textId;
} EnNpc; // size = 0x01B4

// CORRECT FUNCTION SIGNATURES:
void EnNpc_Init(Actor* thisx, PlayState* play) {
    EnNpc* this = (EnNpc*)thisx;  // REQUIRED casting
    // ... implementation
}

// CORRECT COLLIDER INIT:
static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    { 20, 40, 0, { 0, 0, 0 } },
};

// CORRECT ACTORPROFILE:
const ActorProfile EnNpc_Profile = {
    /**/ ACTOR_EN_NPC,
    /**/ ACTORCAT_NPC,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnNpc),
    /**/ EnNpc_Init,
    /**/ EnNpc_Destroy,
    /**/ EnNpc_Update,
    /**/ EnNpc_Draw,
};
""",
            "item": """
// CORRECT STRUCT PATTERN:
typedef struct {
    /* 0x0000 */ Actor actor;  // MUST be first field
    /* 0x014C */ ColliderCylinder collider;
    /* 0x01B0 */ s16 itemId;
    /* 0x01B2 */ s16 bobTimer;
} EnItem; // size = 0x01B4

// CORRECT FUNCTION SIGNATURES:
void EnItem_Init(Actor* thisx, PlayState* play) {
    EnItem* this = (EnItem*)thisx;  // REQUIRED casting
    // ... implementation
}

// CORRECT COLLIDER INIT:
static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    { 15, 30, 0, { 0, 0, 0 } },
};

// CORRECT ACTORPROFILE:
const ActorProfile EnItem_Profile = {
    /**/ ACTOR_EN_ITEM,
    /**/ ACTORCAT_ITEMACTION,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnItem),
    /**/ EnItem_Init,
    /**/ EnItem_Destroy,
    /**/ EnItem_Update,
    /**/ EnItem_Draw,
};
""",
            "object": """
// CORRECT STRUCT PATTERN:
typedef struct {
    /* 0x0000 */ DynaPolyActor dyna;  // For objects with collision
    /* 0x0164 */ ColliderCylinder collider;
    /* 0x01B0 */ s16 switchFlag;
    /* 0x01B2 */ s16 timer;
} ObjSwitch; // size = 0x01B4

// CORRECT FUNCTION SIGNATURES:
void ObjSwitch_Init(Actor* thisx, PlayState* play) {
    ObjSwitch* this = (ObjSwitch*)thisx;  // REQUIRED casting
    // ... implementation
}

// CORRECT COLLIDER INIT:
static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    { 20, 40, 0, { 0, 0, 0 } },
};

// CORRECT ACTORPROFILE:
const ActorProfile ObjSwitch_Profile = {
    /**/ ACTOR_OBJ_SWITCH,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(ObjSwitch),
    /**/ ObjSwitch_Init,
    /**/ ObjSwitch_Destroy,
    /**/ ObjSwitch_Update,
    /**/ ObjSwitch_Draw,
};
"""
        }
        
        return examples.get(category, examples["object"])

    def _check_wrong_inventory_patterns(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect inventory access patterns."""
        
        # Check for wrong INV_CONTENT() macro usage
        wrong_inv_patterns = [
            r'INV_CONTENT\s*\(\s*ITEM_\w+\s*\)',
            r'INV_CONTENT\s*\(\s*[^)]+\s*\)\s*!=\s*ITEM_NONE',
            r'INV_CONTENT\s*\(\s*[^)]+\s*\)\s*==\s*ITEM_NONE'
        ]
        
        for pattern in wrong_inv_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong inventory access pattern - INV_CONTENT() macro doesn't exist in OoT")
                suggestions.append("Use authentic pattern: if (gSaveContext.inventory.items[SLOT_BOW] != ITEM_NONE) { ... }")
                break
        
        # Check for correct inventory patterns
        correct_inv_patterns = [
            r'gSaveContext\.inventory\.items\[SLOT_\w+\]\s*!=\s*ITEM_NONE',
            r'gSaveContext\.inventory\.items\[SLOT_\w+\]\s*==\s*ITEM_NONE'
        ]
        
        # If inventory checking is mentioned but no correct patterns found
        if ("inventory" in code.lower() or "item" in code.lower()) and not any(re.search(pattern, code) for pattern in correct_inv_patterns):
            if any(re.search(pattern, code) for pattern in wrong_inv_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic inventory checking")
                suggestions.append("Use gSaveContext.inventory.items[SLOT_*] for inventory checks")

    def _check_nonexistent_functions(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for non-existent functions that don't exist in OoT."""
        
        # Check for fabricated functions
        fabricated_functions = [
            r'Actor_DrawTransform\s*\(',
            r'Actor_DrawModel\s*\(',
            r'Actor_DrawMesh\s*\(',
            r'Actor_RenderModel\s*\(',
            r'Actor_DrawScale\s*\(',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[^)]+\s*\)',
            r'Math_Vec3f_DistXYZ\s*\(',
            r'Actor_WorldDistXZToPoint\s*\(',
            r'WaterBox_GetSurface1\s*\(',
            r'Lights_PointGlowSetInfo\s*\(',
            r'Lights_PointNoGlowSetInfo\s*\(',
            r'SkelAnime_BlendFrames\s*\(',
            r'Animation_MorphToLoop\s*\(',
            r'Message_GetState\s*\(\s*&play->msgCtx\s*\)\s*==\s*TEXT_STATE_CHOICE',
            r'play->msgCtx\.choiceIndex',
            r'LightContext_InsertLight\s*\('
        ]
        
        for pattern in fabricated_functions:
            if re.search(pattern, code):
                issues.append("CRITICAL: Non-existent function detected")
                suggestions.append("Replace with authentic OoT function or implement properly")
                break

    def _check_missing_input_declaration(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for missing input variable declarations."""
        
        # Check for CHECK_BTN_ALL usage without proper input declaration
        if "CHECK_BTN_ALL" in code:
            # Look for proper input declaration
            input_decl_pattern = r'Input\*\s*input\s*=\s*&play->state\.input\[0\]'
            if not re.search(input_decl_pattern, code):
                issues.append("CRITICAL: Missing input variable declaration")
                suggestions.append("Add 'Input* input = &play->state.input[0];' before using CHECK_BTN_ALL")
            
            # Check for wrong input access patterns
            wrong_input_patterns = [
                r'play->state\.input\[0\]\.press\.button',
                r'CHECK_BTN_ALL\s*\(\s*[^,]+,\s*[^)]+\s*\)\s*\{'
            ]
            
            for pattern in wrong_input_patterns:
                if re.search(pattern, code):
                    issues.append("CRITICAL: Wrong input access pattern")
                    suggestions.append("Use 'Input* input = &play->state.input[0]; if (CHECK_BTN_ALL(input->press.button, BTN_A))'")
                    break

    def _check_wrong_actor_flags(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect actor flag constants."""
        
        # Check for wrong flag constants
        wrong_flag_patterns = [
            r'FLAGS_0,',
            r'FLAGS_UPDATE_WHILE_CULLED,',
            r'FLAGS_\d+,',
            r'FLAGS_[A-Z_]+,'  # Any specific flag that might not exist
        ]
        
        for pattern in wrong_flag_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong actor flag constant")
                suggestions.append("Use 'FLAGS,' for ActorProfile flags unless you have a specific reason")
                break
        
        # Check for correct flag usage
        correct_flag_patterns = [
            r'FLAGS,',
            r'FLAGS_NONE,'
        ]
        
        # If ActorProfile is present but no correct flags found
        if "ActorProfile" in code and "FLAGS" in code and not any(re.search(pattern, code) for pattern in correct_flag_patterns):
            if any(re.search(pattern, code) for pattern in wrong_flag_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing or incorrect actor flags")
                suggestions.append("Use 'FLAGS,' in ActorProfile unless you need specific flags")

    def _check_nonexistent_magic_system(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for non-existent magic systems that don't belong in OoT."""
        
        # Check for fabricated magic systems
        magic_system_patterns = [
            r'manaPoints',
            r'maxManaPoints',
            r'spellCooldown',
            r'activeSpellId',
            r'spellChargeTimer',
            r'MANA_COST_',
            r'SPELL_RANGE_',
            r'EnMagicCaster',
            r'CastSpell',
            r'magic\s+spell',
            r'mana\s+system',
            r'spell\s+casting'
        ]
        
        for pattern in magic_system_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("CRITICAL: Non-existent magic system - OoT doesn't have general spell casting")
                suggestions.append("OoT uses magic meter for specific items (Din's Fire, Farore's Wind), not general spell casting")
                break

    def _check_wrong_sound_effects(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect sound effect usage patterns."""
        
        # Check for wrong sound effect combinations
        wrong_sound_patterns = [
            r'NA_SE_PL_FREEZE',
            r'NA_SE_EV_LIGHT_GATHER',
            r'NA_SE_EV_STONE_DOOR',
            r'NA_SE_IT_SWORD_SWING\s*\(\s*&this->actor\s*\)',
            r'NA_SE_PL_FREEZE\s*\(\s*&this->actor\s*\)',
            r'NA_SE_EV_LIGHT_GATHER\s*\(\s*&this->actor\s*\)'
        ]
        
        for pattern in wrong_sound_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong sound effect usage - context doesn't match OoT patterns")
                suggestions.append("Use authentic OoT sound effects in appropriate contexts")
                break
        
        # Check for correct sound effect patterns
        correct_sound_patterns = [
            r'NA_SE_IT_SWORD_SWING',
            r'NA_SE_PL_FREEZE',
            r'NA_SE_EV_STONE_BOUND',
            r'NA_SE_EV_LIGHT_GATHER'
        ]
        
        # If sound effects are mentioned but no correct patterns found
        if ("NA_SE_" in code) and not any(re.search(pattern, code) for pattern in correct_sound_patterns):
            if any(re.search(pattern, code) for pattern in wrong_sound_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic sound effects")
                suggestions.append("Use authentic OoT sound effects like NA_SE_IT_SWORD_SWING, NA_SE_EV_STONE_BOUND")

    def _check_broken_sqrtf_syntax(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for broken sqrtf() syntax patterns."""
        
        # Check for broken sqrtf with extra parameters
        broken_sqrt_patterns = [
            r'sqrtf\s*\(\s*SQ\s*\(\s*[^)]+\s*\)\s*\+\s*SQ\s*\(\s*[^)]+\s*\)\s*\)\s*\(\s*[^)]+\s*,\s*[^)]+\s*\)',
            r'sqrtf\s*\(\s*[^)]+\s*\)\s*\(\s*[^)]+\s*,\s*[^)]+\s*\)',
            r'sqrtf\s*\(\s*[^)]+\s*\)\s*\(\s*&[^)]+->[^)]+\.world\.pos\s*,\s*&[^)]+->[^)]+\.world\.pos\s*\)'
        ]
        
        for pattern in broken_sqrt_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Broken sqrtf() syntax - function call with wrong parameters")
                suggestions.append("Fix syntax: f32 dx = this->actor.world.pos.x - player->actor.world.pos.x; f32 dz = this->actor.world.pos.z - player->actor.world.pos.z; this->targetDistance = sqrtf(SQ(dx) + SQ(dz));")
                break

    def _check_direct_player_physics_manipulation(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for direct manipulation of player physics from other actors."""
        
        # Check for direct player physics manipulation
        player_physics_patterns = [
            r'player->actor\.velocity\.',
            r'player->actor\.speed',
            r'player->actor\.world\.pos\.',
            r'player->actor\.world\.rot\.',
            r'player->actor\.shape\.',
            r'player->actor\.colChkInfo\.'
        ]
        
        for pattern in player_physics_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Direct player physics manipulation - OoT never allows other actors to directly manipulate player physics")
                suggestions.append("Use player state changes, scripted sequences, or room-specific logic instead of direct physics manipulation")
                break

    def _check_wrong_matrix_function_parameters(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect matrix function parameters."""
        
        # Check for wrong Matrix_NewMtx usage
        wrong_matrix_patterns = [
            r'Matrix_NewMtx\s*\(\s*[^,]+,\s*"[^"]+"\s*\)',
            r'Matrix_NewMtx\s*\(\s*[^,]+,\s*[^,]+,\s*[^)]+\)',
            r'gSPMatrix\s*\(\s*[^,]+,\s*Matrix_NewMtx\s*\(\s*[^,]+,\s*"[^"]+"\s*\)'
        ]
        
        for pattern in wrong_matrix_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong Matrix_NewMtx parameters - use __FILE__ and __LINE__")
                suggestions.append("Use: Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__)")
                break

    def _check_nonexistent_actor_spawn_functions(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for non-existent actor spawn function signatures."""
        
        # Check for fabricated actor spawn functions
        fabricated_spawn_patterns = [
            r'Actor_SpawnAsChild\s*\(',
            r'Actor_SpawnChild\s*\(',
            r'Actor_SpawnWithParent\s*\(',
            r'Actor_SpawnRelative\s*\('
        ]
        
        for pattern in fabricated_spawn_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Non-existent actor spawn function")
                suggestions.append("Use: Actor_Spawn(&play->actorCtx, play, ACTOR_TYPE, x, y, z, rx, ry, rz, params)")
                break

    def _check_game_design_issues(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for game design issues that don't match OoT patterns."""
        
        # Check for environmental effects that don't exist in OoT
        environmental_effect_patterns = [
            r'gravity\s+well',
            r'gravitational\s+effect',
            r'environmental\s+hazards',
            r'room\s+layout\s+manipulation',
            r'dynamic\s+room\s+changes',
            r'physics\s+manipulation',
            r'velocity\s+modification',
            r'strength\s*=\s*[^;]+;\s*player->actor\.velocity'
        ]
        
        for pattern in environmental_effect_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append("CRITICAL: Game design issue - environmental effects don't work this way in OoT")
                suggestions.append("OoT uses scripted sequences, player state changes, and room-specific logic, not direct physics manipulation")
                break

    def _check_nonexistent_player_health_access(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect player health access patterns."""
        
        # Check for wrong player health access
        wrong_health_patterns = [
            r'player->health',
            r'player->healthCapacity',
            r'player->maxHealth',
            r'player->currentHealth'
        ]
        
        for pattern in wrong_health_patterns:
            if re.search(pattern, code):
                issues.append("CRITICAL: Wrong player health access - player->health doesn't exist in OoT")
                suggestions.append("Use gSaveContext.health and gSaveContext.healthCapacity for player health values")
                break
        
        # Check for correct health access patterns
        correct_health_patterns = [
            r'gSaveContext\.health',
            r'gSaveContext\.healthCapacity',
            r'gSaveContext\.maxHealth'
        ]
        
        # If health checking is mentioned but no correct patterns found
        if ("health" in code.lower()) and not any(re.search(pattern, code) for pattern in correct_health_patterns):
            if any(re.search(pattern, code) for pattern in wrong_health_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic player health access")
                suggestions.append("Use gSaveContext.health and gSaveContext.healthCapacity for player health")

    def _check_direct_player_position_manipulation(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for direct manipulation of player position from other actors."""
        
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
                issues.append("CRITICAL: Direct player position/velocity manipulation - OoT never allows other actors to directly manipulate player physics")
                suggestions.append("Use player state changes, scripted sequences, or room-specific logic instead of direct physics manipulation")
                break

    def _check_missing_variable_declarations(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for missing variable declarations in structs."""
        
        # Check for SkelAnime usage without declaration
        if "SkelAnime_" in code or "skelAnime." in code:
            # Look for SkelAnime declaration in struct
            struct_pattern = r'typedef\s+struct\s*\{[^}]*\}'
            struct_matches = re.finditer(struct_pattern, code, re.DOTALL)
            
            for struct_match in struct_matches:
                struct_content = struct_match.group(0)
                if "SkelAnime" in code and "SkelAnime skelAnime" not in struct_content:
                    issues.append("CRITICAL: Missing SkelAnime declaration in struct")
                    suggestions.append("Add 'SkelAnime skelAnime;' to struct if using skeleton animation functions")
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
                issues.append("CRITICAL: Missing collider declaration in struct")
                suggestions.append("Add 'ColliderCylinder collider;' to struct if using collision functions")
                break

    def _check_wrong_flag_usage(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Check for incorrect flag usage patterns."""
        
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
                issues.append("CRITICAL: Wrong flag usage - ACTOR_FLAG_8/9 don't exist in OoT")
                suggestions.append("Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)")
                break
        
        # Check for correct flag usage patterns
        correct_flag_patterns = [
            r'this->actor\.flags\s*&\s*ACTOR_FLAG_[0-7]',
            r'player->actor\.flags\s*&\s*ACTOR_FLAG_[0-7]',
            r'flags\s*&\s*ACTOR_FLAG_[0-7]'
        ]
        
        # If flag checking is mentioned but no correct patterns found
        if ("ACTOR_FLAG" in code) and not any(re.search(pattern, code) for pattern in correct_flag_patterns):
            if any(re.search(pattern, code) for pattern in wrong_flag_patterns):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic flag checking")
                suggestions.append("Use: if (this->actor.flags & ACTOR_FLAG_0)")

    def _check_nonexistent_drawing_functions_enhanced(self, code: str, issues: List[str], suggestions: List[str]) -> None:
        """Enhanced check for non-existent drawing functions."""
        
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
                issues.append("CRITICAL: Non-existent drawing function - Gfx_DrawDListOpa(play, gSomeDL) doesn't exist in OoT")
                suggestions.append("Use SkelAnime_DrawOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, NULL, NULL, this) for skeleton drawing")
                break
        
        # Check for correct drawing patterns
        correct_drawing_patterns = [
            r'SkelAnime_DrawOpa\s*\(\s*play,\s*this->skelAnime\.skeleton,\s*this->skelAnime\.jointTable',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*g[A-Z][a-zA-Z0-9_]*DL\s*\)',
            r'Gfx_DrawDListOpa\s*\(\s*play,\s*[a-z][a-zA-Z0-9_]*DL\s*\)'
        ]
        
        # If drawing is mentioned but no correct patterns found
        if ("Draw" in code or "draw" in code) and not any(re.search(pattern, code) for pattern in correct_drawing_patterns):
            if any(re.search(pattern, code) for pattern in fabricated_drawing):
                pass  # Already caught above
            else:
                issues.append("CRITICAL: Missing authentic drawing function")
                suggestions.append("Use SkelAnime_DrawOpa() for skeleton animation or Gfx_DrawDListOpa() for display lists")

# ------------------------------------------------------------
# Simple CLI test
# ------------------------------------------------------------

if __name__ == "__main__":
    val = OoTPatternValidator()
    
    # Test with problematic training example that contains non-existent functions
    scenario = """I need help creating a facial expression system for NPCs in OoT. I want NPCs to be able to switch between happy, sad, and angry expressions using a timer-based system. The expressions should smoothly transition using scale interpolation on the face mesh. Can you show me how to implement this as an actor with proper state management and animation timing? Use Audio_PlayActorSfx2 for sound effects and NA_SE_EV_STONE_DOOR for door sounds. The actor should be called ACTOR_EN_FACE_EXPR and use ActorProfile structure."""
    
    res = val.validate_scenario(scenario, "enemy")
    logger.validation("=== VALIDATION RESULT ===")
    logger.validation(f"Valid: {res.is_valid}")
    logger.validation(f"Issues: {res.issues}")
    logger.validation(f"Suggestions: {res.suggestions}")
    logger.validation(f"Patterns: {res.authentic_patterns}")
    
    logger.validation("\n--- Enhanced Prompt Preview (first 500 chars) ---")
    logger.validation(val.create_enhanced_prompt(scenario, "enemy", res)[:500] + "...\n") 