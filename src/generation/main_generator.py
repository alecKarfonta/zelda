#!/usr/bin/env python3
"""
Main OoT Training Data Generator
"""

import os
import json
import time
import random
import re
from typing import Dict, List, Optional

import anthropic

from src.core.logger import logger
from src.models.enums import ExampleType, TrainingExample, ActorCategory
from src.analyzers.source_analyzer import DynamicSourceAnalyzer
from src.validation.authenticity_validator import StrictAuthenticityValidator
from src.generation.diversity_injector import DiversityInjector
from src.generation.temperature_manager import DynamicTemperatureManager
from src.parsers.response_parser import ResponseParser
from src.compilation.c_code_compiler import TrainingDataCompiler


class EnhancedOoTTrainingGenerator:
    """Enhanced generator with strict authenticity + real OoT decompilation data + diversity injection"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022", 
                 oot_path: str = "oot", use_dynamic_analysis: bool = True, enable_compilation: bool = False):
        # Try to get API key from environment first, then parameter
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY in .env file or pass as parameter")
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        
        # Initialize dynamic source analyzer if enabled
        logger.info(f"🔍 Initializing dynamic source analysis from {oot_path}...")
        self.source_analyzer = DynamicSourceAnalyzer(oot_path)
        logger.success("✅ Dynamic source analysis initialized successfully")

        self.validator = StrictAuthenticityValidator(self.source_analyzer)
        
        # Initialize diversity injector
        self.diversity_injector = DiversityInjector()
        
        # Initialize dynamic temperature manager
        self.temperature_manager = DynamicTemperatureManager()
        
        # Initialize response parser
        self.response_parser = ResponseParser()
        
        # Initialize validation and context system
        from helpers.validate_and_enhance_scenarios import OoTPatternValidator
        from helpers.complete_context_generator import CompleteOoTContextGenerator
        self.pattern_validator = OoTPatternValidator(oot_path)
        self.context_generator = CompleteOoTContextGenerator(oot_path)
        self.use_validation = True
        logger.success("✅ Enhanced validation and context generation enabled")
        
        # Initialize C code compilation if enabled
        self.enable_compilation = enable_compilation
        if enable_compilation:
            try:
                self.compiler = TrainingDataCompiler(oot_path)
                logger.success("✅ C code compilation enabled")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize C code compiler: {e}")
                self.enable_compilation = False
        
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

// Authentic collision initialization pattern
static ColliderCylinderInit sCylinderInit = {
    {
        COL_MATERIAL_NONE,  // Use COL_MATERIAL_* constants, not COLTYPE_*
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEM_MATERIAL_UNK0,  // Use ELEM_MATERIAL_* constants, not ELEMTYPE_*
        { 0x00000000, HIT_SPECIAL_EFFECT_NONE, 0x00 },
        { 0x00000010, HIT_BACKLASH_NONE, 0x00 },
        ATELEM_NONE,
        ACELEM_ON,
        OCELEM_ON,
    },
    { 15, 25, 0, { 0, 0, 0 } },
};

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
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2);
    Collider_UpdateCylinder(&this->actor, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Authentic movement pattern
    Actor_MoveXZGravity(&this->actor);
}

void EnExample_Draw(Actor* thisx, PlayState* play) {
    EnExample* this = (EnExample*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__);
    
    // Drawing code here
    
    CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__);
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
        COL_MATERIAL_NONE,  // Use COL_MATERIAL_* constants, not COLTYPE_*
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    },
    {
        ELEM_MATERIAL_UNK0,  // Use ELEM_MATERIAL_* constants, not ELEMTYPE_*
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

// Authentic background check pattern
Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2);
""",
        }

    def _load_enhanced_contexts(self) -> Dict[str, str]:
        """Load contexts with strict requirements + real examples"""
        
        # Get dynamic function list if available
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
        return {
            "strict_requirements": f"""
CRITICAL AUTHENTICITY REQUIREMENTS (ENFORCED):
✗ NEVER use Majora's Mask mechanics (transformation masks, Deku/Goron/Zora forms)
✗ NEVER use fabricated functions that don't exist in OoT decompilation
✗ NEVER use player->health, player->currentShield, player->swordState - these don't exist
✗ NEVER use non-existent constants like PLAYER_SHIELD_MAX, LIMB_COUNT, ACTOR_PLAYER
✗ NEVER use Matrix_NewMtx(play->state.gfxCtx, "string") - use __FILE__, __LINE__ instead
✗ NEVER use OPEN_DISPS/CLOSE_DISPS with file/line parameters
✗ NEVER use func_80093D18() or other fabricated graphics functions
✗ NEVER implement dynamic memory allocation in actors
✗ NEVER reference jointTable/morphTable without declaring them in struct

✓ Use authentic OoT patterns from real decompilation
✓ Use gSaveContext.inventory and gSaveContext.equips for player data
✓ Use specific numbers instead of fabricated constants
✓ Use GET_PLAYER(play) without additional ID checks
✓ Use Gfx_SetupDL_25Opa() for graphics setup
✓ Use Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__)
✓ Use OPEN_DISPS(play->state.gfxCtx) and CLOSE_DISPS(play->state.gfxCtx)
✓ Use pre-allocated memory structures in actors
✓ Declare Vec3s jointTable[LIMB_COUNT]; and Vec3s morphTable[LIMB_COUNT]; in struct if using skeleton animation

🚨 CRITICAL GAME CONTEXT REQUIREMENTS:
   ✗ NEVER use BGCHECKFLAG_LAVA (doesn't exist in OoT)
   ✗ NEVER use WaterBox_GetSurface1 (wrong signature for OoT)
   ✗ NEVER use ACTORCAT_PLAYER (reserved for player actor only)
   ✓ Use authentic OoT water detection patterns
   ✓ Use ACTORCAT_NPC, ACTORCAT_MISC, ACTORCAT_PROP, or ACTORCAT_ENEMY

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

6. BACKGROUND CHECK PATTERNS (MANDATORY):
   ✓ Use Actor_UpdateBgCheckInfo(play, &actor, 35.0f, 60.0f, 60.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2)
   ✗ NEVER use BGCHECKFLAG_LAVA or BGCHECKFLAG_GROUND (don't exist in OoT)

VALIDATION WILL REJECT ANY EXAMPLE VIOLATING THESE REQUIREMENTS.

🚨 CRITICAL AUTHENTICITY REQUIREMENTS (ENFORCED):
✗ NEVER use Gfx_DrawDListOpa(play, gSomeDL) - this function doesn't exist in OoT
✗ NEVER directly manipulate player->actor.world.pos or player->actor.velocity
✗ NEVER access player->health or player->healthCapacity  
✗ NEVER use SkelAnime functions without declaring SkelAnime in struct
✗ NEVER use ACTOR_FLAG_8 or other non-existent flags
✗ NEVER use fabricated patterns like INV_CONTENT(), Actor_DrawOpa(), etc.
✗ NEVER use play->colCtx.waterLevel = value - water level is handled through room systems
✗ NEVER use play->msgCtx.ocarinaMode == OCARINA_MODE_04 - ocarina handled through player state
✗ NEVER use gSaveContext.inventory.questItems & 0x3F - use specific quest item flags
✗ NEVER use func_8002F71C() - this function doesn't exist in OoT
✗ NEVER use this->collider.base.ac->actor->id - wrong collision access pattern
✗ NEVER use SkelAnime_DrawOpa(play, skeleton, jointTable, NULL, NULL, this) - wrong signature
✗ NEVER spawn same actor type recursively - use different actor types for illusions/effects
✗ NEVER assign Math_SmoothStepToF() result to variable - function returns bool, not float
✗ NEVER use player->stateFlags1 & PLAYER_STATE1_20 - this flag doesn't exist in OoT
✗ NEVER use SkelAnime_InitFlex(play, &skelAnime, skeleton, NULL, NULL, NULL, 0) - missing required parameters
✗ NEVER reference jointTable/morphTable without declaring them in struct
✗ NEVER use ZeldaArena_MallocDebug() or ZeldaArena_FreeDebug() - these don't exist in OoT
✗ NEVER use OPEN_DISPS(play->state.gfxCtx, "file.c", line) - these don't take file/line parameters
✗ NEVER implement dynamic memory allocation in actors - not an authentic OoT pattern
✗ NEVER use player->currentShield, player->swordState - these don't exist
✗ NEVER use PLAYER_SHIELD_MAX, PLAYER_SWORD_MAX, LIMB_COUNT - these constants don't exist
✗ NEVER use player->actor.id != ACTOR_PLAYER - GET_PLAYER() always returns player

✓ Use SkelAnime_DrawFlexOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, this->skelAnime.dListCount, NULL, NULL, this)
✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health
✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)
✓ Declare SkelAnime skelAnime; in struct if using skeleton animation
✓ Use Actor_WorldDistXZToActor(&this->actor, &player->actor) for distance checks
✓ Use if (gSaveContext.inventory.items[SLOT_HOOKSHOT] != ITEM_NONE) for item checks
✓ Use Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__) for matrix creation
✓ Use room-specific water systems instead of direct colCtx manipulation
✓ Use player actor state machine for ocarina handling
✓ Use specific quest item flags like QUEST_MEDALLION_FOREST
✓ Use proper collision access patterns from OoT collision system
✓ Use authentic drawing function signatures from OoT decompilation
✓ Use different actor types for illusions/effects (not recursive spawning)
✓ Use Math_SmoothStepToF(&variable, target, step, maxStep, minStep) without assignment
✓ Use authentic player state flags from OoT decompilation
✓ Use SkelAnime_InitFlex(play, &skelAnime, skeleton, animation, jointTable, morphTable, limbCount)
✓ Declare Vec3s jointTable[LIMB_COUNT]; and Vec3s morphTable[LIMB_COUNT]; in struct if using skeleton animation
✓ Use ZeldaArena_Malloc(size) and ZeldaArena_Free(ptr) for memory management
✓ Use OPEN_DISPS(play->state.gfxCtx) and CLOSE_DISPS(play->state.gfxCtx) without file/line parameters
✓ Use pre-allocated memory structures instead of dynamic allocation in actors
✓ Use gSaveContext.equips.buttonItems[0] for current sword, gSaveContext.equips.buttonItems[1] for shield
✓ Use specific numbers like 20 for limb count instead of LIMB_COUNT
✓ Use GET_PLAYER(play) without additional ID checks
✓ Use Gfx_SetupDL_25Opa(play->state.gfxCtx) for graphics setup

🚨 UPDATED AUTHENTICITY REQUIREMENTS BASED ON COMPILATION TESTING:
✗ NEVER use COLTYPE_NONE, COLTYPE_HIT0, etc. - use COL_MATERIAL_NONE, COL_MATERIAL_HIT0 instead
✗ NEVER use ELEMTYPE_UNK0, ELEMTYPE_UNK1, etc. - use ELEM_MATERIAL_UNK0, ELEM_MATERIAL_UNK1 instead
✗ NEVER use OPEN_DISPS(play->state.gfxCtx) without file/line - use OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__)
✗ NEVER use CLOSE_DISPS(play->state.gfxCtx) without file/line - use CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__)
✗ NEVER use func_8002F71C() - this function doesn't exist in OoT
✗ NEVER use sCylinderInit without declaring it as static ColliderCylinderInit sCylinderInit
✗ NEVER use SkelAnime_InitFlex with wrong parameters - must include jointTable and morphTable
✗ NEVER use player->actor.id != ACTOR_PLAYER - GET_PLAYER() always returns player
✗ NEVER use gSaveContext.inventory.questItems & 0x3F - use specific quest item flags
✗ NEVER use play->colCtx.waterLevel = value - water level is handled through room systems
✗ NEVER use play->msgCtx.ocarinaMode == OCARINA_MODE_04 - ocarina handled through player state
✗ NEVER use player->health or player->healthCapacity - use gSaveContext.health and gSaveContext.healthCapacity
✗ NEVER use player->currentShield or player->swordState - these don't exist
✗ NEVER use PLAYER_SHIELD_MAX, PLAYER_SWORD_MAX, LIMB_COUNT - these constants don't exist
✗ NEVER use ACTOR_FLAG_8 or other non-existent flags - use ACTOR_FLAG_0 through ACTOR_FLAG_15
✗ NEVER use fabricated patterns like INV_CONTENT(), Actor_DrawOpa(), etc.
✗ NEVER use SkelAnime_DrawOpa with wrong signature - use SkelAnime_DrawFlexOpa
✗ NEVER spawn same actor type recursively - use different actor types for illusions/effects
✗ NEVER assign Math_SmoothStepToF() result to variable - function returns bool, not float
✗ NEVER use player->stateFlags1 & PLAYER_STATE1_20 - this flag doesn't exist in OoT
✗ NEVER reference jointTable/morphTable without declaring them in struct
✗ NEVER use ZeldaArena_MallocDebug() or ZeldaArena_FreeDebug() - these don't exist in OoT
✗ NEVER implement dynamic memory allocation in actors - not an authentic OoT pattern

✓ Use COL_MATERIAL_NONE, COL_MATERIAL_HIT0, COL_MATERIAL_HIT1, etc. for collision materials
✓ Use ELEM_MATERIAL_UNK0, ELEM_MATERIAL_UNK1, etc. for element materials
✓ Use OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__) and CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__)
✓ Use static ColliderCylinderInit sCylinderInit = { ... }; for collision initialization
✓ Use SkelAnime_InitFlex(play, &skelAnime, skeleton, animation, jointTable, morphTable, limbCount)
✓ Use GET_PLAYER(play) without additional ID checks
✓ Use specific quest item flags like QUEST_MEDALLION_FOREST
✓ Use room-specific water systems instead of direct colCtx manipulation
✓ Use player actor state machine for ocarina handling
✓ Use gSaveContext.health and gSaveContext.healthCapacity for player health
✓ Use gSaveContext.equips.buttonItems[0] for current sword, gSaveContext.equips.buttonItems[1] for shield
✓ Use specific numbers like 20 for limb count instead of LIMB_COUNT
✓ Use ACTOR_FLAG_0 through ACTOR_FLAG_15 for actor flags
✓ Use authentic drawing function signatures from OoT decompilation
✓ Use different actor types for illusions/effects (not recursive spawning)
✓ Use Math_SmoothStepToF(&variable, target, step, maxStep, minStep) without assignment
✓ Use authentic player state flags from OoT decompilation
✓ Declare Vec3s jointTable[LIMB_COUNT]; and Vec3s morphTable[LIMB_COUNT]; in struct if using skeleton animation
✓ Use ZeldaArena_Malloc(size) and ZeldaArena_Free(ptr) for memory management
✓ Use pre-allocated memory structures instead of dynamic allocation in actors
✓ Use Gfx_SetupDL_25Opa(play->state.gfxCtx) for graphics setup
✓ Use Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__) for matrix creation
✓ Use Actor_WorldDistXZToActor(&this->actor, &player->actor) for distance checks
✓ Use if (gSaveContext.inventory.items[SLOT_HOOKSHOT] != ITEM_NONE) for item checks
✓ Use proper collision access patterns from OoT collision system
✓ Use SkelAnime_DrawFlexOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, this->skelAnime.dListCount, NULL, NULL, this)
✓ Use proper flag checking: if (this->actor.flags & ACTOR_FLAG_0)
✓ Declare SkelAnime skelAnime; in struct if using skeleton animation
""",
            
            "authentic_actor_context": f"""
AUTHENTIC ACTOR SYSTEM (FROM REAL OoT DECOMPILATION):

🚨 CRITICAL: This is Ocarina of Time, NOT Majora's Mask
   ✗ NO transformation masks (Deku, Goron, Zora)
   ✗ NO BGCHECKFLAG_LAVA (doesn't exist in OoT)
   ✗ NO WaterBox_GetSurface1 (wrong signature)
   ✗ NO ACTORCAT_PLAYER (reserved for player only)

REAL ACTOR STRUCTURE PATTERN (from actor.h):
```c
typedef struct {{
    /* 0x0000 */ Actor actor;  // Base actor (size 0x14C)
    /* 0x014C */ // Custom fields start here with proper offsets
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 actionState;
    /* 0x0150 */ f32 customScale;
    /* 0x0154 */ ColliderCylinder collider;  // If collision needed
    /* 0x01A0 */ SkelAnime skelAnime;  // If skeleton animation needed
    /* 0x01E4 */ Vec3s jointTable[20];  // If skeleton animation needed
    /* 0x0254 */ Vec3s morphTable[20];  // If skeleton animation needed
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
    /**/ ACTORCAT_MISC,  // Use ACTORCAT_NPC, ACTORCAT_MISC, ACTORCAT_PROP, or ACTORCAT_ENEMY
    /**/ FLAGS,
    /**/ OBJECT_ACTORNAME,
    /**/ sizeof(ActorName),
    /**/ ActorName_Init,
    /**/ ActorName_Destroy,
    /**/ ActorName_Update,
    /**/ ActorName_Draw,
}};
```

AUTHENTIC COLLISION PATTERN (from z_collision_check.c):
```c
static ColliderCylinderInit sCylinderInit = {{
    {{
        COL_MATERIAL_NONE,  // Use COL_MATERIAL_* constants, not COLTYPE_*
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    }},
    {{
        ELEM_MATERIAL_UNK0,  // Use ELEM_MATERIAL_* constants, not ELEMTYPE_*
        {{ 0x00000000, HIT_SPECIAL_EFFECT_NONE, 0x00 }},
        {{ 0x00000010, HIT_BACKLASH_NONE, 0x00 }},
        ATELEM_NONE,
        ACELEM_ON,
        OCELEM_ON,
    }},
    {{ 15, 25, 0, {{ 0, 0, 0 }} }},
}};
```

AUTHENTIC GRAPHICS PATTERN (from z_actor.c):
```c
void ActorName_Draw(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    
    OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__);
    
    Gfx_SetupDL_25Opa(play->state.gfxCtx);
    Matrix_NewMtx(play->state.gfxCtx, __FILE__, __LINE__);
    
    // Drawing code here
    
    CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__);
}}
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
            logger.debug(f"[DEBUG] Generation failed - no example returned")
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Phase 2: Multi-pass validation and correction
        example = self._multi_pass_validation(example)
        
        # NEW: Validate against feedback patterns
        feedback_issues = self.validator.validate_feedback_patterns(example.output)
        if feedback_issues:
            example.validation_notes += "Feedback validation issues: " + "; ".join(feedback_issues) + ". "
            logger.warning(f"Feedback validation found {len(feedback_issues)} issues")
        
        # Fix instruction if it's a placeholder
        if example.instruction.strip().lower() in ["clear instruction", "", None]:
            logger.warning(f"[WARNING] Instruction is a placeholder, generating a new one")
            # Try to get a better scenario
            diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
            example.instruction = diverse_instruction
        
        # Phase 3: Final authenticity scoring
        example.authenticity_score = self.validator.calculate_authenticity_score(example.output)
        
        # More lenient rejection criteria
        quality_threshold = 4.0  # Reduced from 6.0
        authenticity_threshold = 4.0  # Reduced from 6.0
        
        if example.authenticity_score < authenticity_threshold or example.quality_score < quality_threshold:
            logger.error(f"[REJECT] Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
            logger.debug(f"[DEBUG] Instruction: {example.instruction[:50]}...")
            logger.debug(f"[DEBUG] Output length: {len(example.output)}")
            logger.debug(f"[DEBUG] Validation notes: {example.validation_notes}")
            self.generation_stats["total_rejected"] += 1
            return TrainingExample(example_type=example_type, instruction="", output="")
        
        # Update acceptance stats
        self.generation_stats["total_accepted"] += 1
            
        return example

    def _generate_with_diverse_prompt(self, example_type: ExampleType, complexity: str) -> Optional[TrainingExample]:
        """Generate with diversity injection and enhanced prompts"""
        
        # Get diverse instruction from injector
        diverse_instruction = self.diversity_injector.get_diverse_instruction(example_type, complexity)
        
        # Get dynamic temperature based on diversity needs
        diversity_metrics = {
            "actor_categories": {cat.value: 0 for cat in ActorCategory},
            "example_types": {t.value: 0 for t in ExampleType},
            "complexities": {"basic": 0, "intermediate": 0, "advanced": 0},
            "unique_scenarios": set()
        }
        logger.refinement(f"🔧 Calculating dynamic temperature for {example_type.value} ({complexity})")
        dynamic_temperature = self.temperature_manager.get_dynamic_temperature(example_type, complexity, diversity_metrics)
        
        # Create enhanced prompt
        enhanced_prompt = self._create_enhanced_prompt(diverse_instruction, example_type, complexity)
        
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
            return self.response_parser.parse_response(raw_response, example_type)
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None

    def _create_enhanced_prompt(self, instruction: str, example_type: ExampleType, complexity: str) -> str:
        """Create enhanced prompt with all necessary context"""
        
        # Get context snippets
        header_block, macro_block, example_block = self._get_context_snippets(example_type)
        
        # Get relevant functions and constants
        category = self._map_example_type_to_category(example_type)
        relevant_functions = self._get_relevant_functions_and_constants(example_type, category)
        functions_and_constants = '\n'.join(f'- {f}' for f in relevant_functions)
        
        # Create the enhanced prompt
        prompt = f"""
{self.context_templates["strict_requirements"]}

{self.context_templates["authentic_actor_context"]}

AUTHENTIC OoT HEADER SNIPPETS:
{header_block}

AUTHENTIC OoT MACRO SNIPPETS:
{macro_block}

AUTHENTIC OoT EXAMPLE SNIPPETS:
{example_block}

RELEVANT AUTHENTIC FUNCTIONS AND CONSTANTS:
{functions_and_constants}

INSTRUCTION: {instruction}

COMPLEXITY: {complexity}

You are generating diverse OoT romhacking training data. You MUST follow authentic decompilation patterns exactly while creating varied and interesting content.

Return exactly this JSON:
{{
  "instruction": "{instruction}",
  "input": null,
  "output": "Authentic C code here"
}}
"""
        
        return prompt

    def _multi_pass_validation(self, example: TrainingExample) -> TrainingExample:
        """Multi-pass validation with progressive correction and compilation testing"""
        
        # Pass 1: CRITICAL - Feedback pattern validation
        feedback_issues = self.validator.validate_feedback_patterns(example.output)
        if feedback_issues:
            example.validation_notes += f"CRITICAL feedback issues: {len(feedback_issues)}. "
            logger.error(f"[CRITICAL] Feedback validation issues detected: {feedback_issues}")
        
        # Pass 2: Function signature validation against real functions
        signature_issues = self.validator.validate_function_signatures(example.output)
        if signature_issues:
            example.validation_notes += f"Signature issues: {len(signature_issues)}. "
            # Apply mandatory corrections
            example.output = self.validator.apply_mandatory_corrections(example.output)
        
        # Pass 3: Architectural validation against real patterns
        arch_issues = self.validator.validate_architectural_authenticity(example.output, example.instruction)
        if arch_issues:
            example.validation_notes += f"Architecture issues: {len(arch_issues)}. "
        
        # Pass 4: Additional source-based validation
        if self.source_analyzer:
            source_issues = self.source_analyzer.validate_against_real_source(example.output)
            if source_issues:
                example.validation_notes += f"Source validation issues: {len(source_issues)}. "
        
        # Pass 5: Enhanced feedback pattern validation
        feedback_issues = self.validator.validate_feedback_patterns(example.output)
        if feedback_issues:
            example.validation_notes += f"Feedback validation issues: {len(feedback_issues)}. "
            logger.warning(f"[FEEDBACK] Found {len(feedback_issues)} feedback issues")
        
        # Pass 6: Compilation validation (if enabled)
        if self.enable_compilation:
            category = self._map_example_type_to_category(example.example_type)
            validation_result = self.validator.validate_code(example.output, category)
            
            if validation_result.compilation_result:
                if validation_result.compilation_result.success:
                    example.validation_notes += "Compilation: SUCCESS. "
                    logger.success(f"[COMPILATION] Code compiles successfully")
                else:
                    error_count = len(validation_result.compilation_result.error_messages or [])
                    example.validation_notes += f"Compilation: FAILED ({error_count} errors). "
                    logger.warning(f"[COMPILATION] Code has compilation errors")
                    if validation_result.compilation_result.error_messages:
                        for error in validation_result.compilation_result.error_messages[:3]:
                            logger.warning(f"  - {error}")
            
            # Update authenticity score based on compilation result
            example.authenticity_score = validation_result.score
        
        # Pass 7: Final quality scoring
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

    def _get_context_snippets(self, example_type: ExampleType):
        """Get header, macro, and example snippets"""
        # Placeholder - would integrate with helpers.oot_context_cache
        return "// Header snippets", "// Macro snippets", "// Example snippets"

    def _get_relevant_functions_and_constants(self, example_type: ExampleType, category: str) -> List[str]:
        """Get relevant functions and constants for the example type"""
        # Placeholder - would load from database files
        return [
            "Actor_Init", "Actor_Destroy", "Actor_Update", "Actor_Draw",
            "Collider_InitCylinder", "Collider_SetCylinder", "Collider_UpdateCylinder",
            "Actor_SetScale", "Actor_SetFocus", "Actor_UpdateBgCheckInfo"
        ]

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
        
        logger.generation(f"Generating {num_examples} diverse authentic examples...")
        logger.stats(f"Using {len(self.validator.authentic_function_signatures)} real OoT functions for validation")
        logger.stats(f"Target distribution: {len(type_weights)} example types with weighted selection")
        
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
            
            logger.generation(f"Generating example {len(examples)+1}/{num_examples}: {example_type.value} ({complexity})")
            
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
                        
                        logger.success(f"  ✓ ACCEPTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                    else:
                        rejected_count += 1
                        logger.warning(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}, Diversity: +{diversity_bonus:.1f}")
                else:
                    rejected_count += 1
                    logger.warning(f"  ✗ REJECTED - Quality: {example.quality_score:.1f}, Auth: {example.authenticity_score:.1f}")
                    
            except Exception as e:
                logger.error(f"  ✗ ERROR: {e}")
                rejected_count += 1
                
            time.sleep(0.5)  # Rate limiting
        
        # Save results with enhanced metadata
        self._save_dataset_with_diversity(examples, output_file, diversity_metrics)
        
        logger.info(f"\nFINAL RESULTS:")
        logger.success(f"✓ Accepted: {len(examples)} examples")
        logger.warning(f"✗ Rejected: {rejected_count} examples")
        logger.stats(f"📊 Acceptance rate: {len(examples)/(len(examples)+rejected_count)*100:.1f}%")
        logger.info(f" Diversity achieved:")
        logger.info(f"   - Actor categories: {len([c for c in diversity_metrics['actor_categories'].values() if c > 0])}/14")
        logger.info(f"   - Example types: {len([t for t in diversity_metrics['example_types'].values() if t > 0])}/{len(ExampleType)}")
        logger.info(f"   - Unique scenarios: {len(diversity_metrics['unique_scenarios'])}")
        logger.file_ops(f" Saved to: {output_file}")
        
        # Compile C code if enabled
        if self.enable_compilation:
            self._compile_generated_dataset(output_file)

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
    
    def _compile_generated_dataset(self, output_file: str) -> None:
        """Compile C code from the generated dataset"""
        if not self.enable_compilation:
            return
            
        logger.info("🔧 Compiling C code from generated dataset...")
        
        try:
            # Process the generated dataset
            results = self.compiler.process_training_data(output_file)
            
            # Generate compilation report
            report = self.compiler.generate_compilation_report(results)
            
            # Save compilation report
            report_file = output_file.replace('.jsonl', '_compilation_report.txt')
            with open(report_file, 'w') as f:
                f.write(report)
            
            # Print summary
            total_examples = len(results)
            successful_compilations = sum(1 for r in results if r.success)
            
            logger.info("📊 Compilation Results:")
            logger.info(f"  - Total C code snippets: {total_examples}")
            logger.info(f"  - Successful compilations: {successful_compilations}")
            logger.info(f"  - Success rate: {(successful_compilations/total_examples*100):.1f}%" if total_examples > 0 else "  - Success rate: 0.0%")
            logger.info(f"  - Report saved to: {report_file}")
            
            if successful_compilations > 0:
                logger.success(f"✅ {successful_compilations} C code snippets compiled successfully!")
            else:
                logger.warning("⚠️ No C code snippets compiled successfully")
                
        except Exception as e:
            logger.error(f"❌ Compilation error: {e}")
    
    def _refine_response(self, prompt: str, response: str, validation_result) -> Optional[str]:
        """Refine response based on validation feedback including compilation errors"""
        
        if not validation_result.issues:
            return None
            
        # Create refinement prompt with specific compilation errors
        refinement_prompt = f"""
The following C code has compilation errors and needs to be fixed:

ORIGINAL CODE:
{response}

COMPILATION ERRORS:
{chr(10).join(f"- {issue}" for issue in validation_result.issues[:5])}

SUGGESTIONS:
{chr(10).join(f"- {suggestion}" for suggestion in validation_result.suggestions[:5])}

Please fix the compilation errors and provide corrected C code that follows OoT decompilation patterns exactly. 
Focus on:
1. Including proper header files
2. Using correct OoT function signatures
3. Following authentic struct patterns
4. Fixing syntax errors

Return only the corrected C code:
"""
        
        try:
            refined_response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.1,  # Low temperature for corrections
                messages=[{"role": "user", "content": refinement_prompt}]
            )
            
            content_block = refined_response.content[0]
            if content_block.type == 'text':
                return content_block.text
            else:
                return str(content_block)
                
        except Exception as e:
            logger.error(f"Refinement failed: {e}")
            return None 