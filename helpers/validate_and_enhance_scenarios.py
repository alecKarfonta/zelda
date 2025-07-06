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
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)"
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
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)"
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
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)"
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
            "- REQUIRED: Function signatures (Actor* thisx, PlayState* play)"
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