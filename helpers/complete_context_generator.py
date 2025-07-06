#!/usr/bin/env python3
"""
Complete Context Generator for OoT Training Data

This script integrates scenario validation with complete source code context
to ensure the LLM has everything needed to generate authentic OoT code.
"""

import json
import random
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
from helpers.validate_and_enhance_scenarios import OoTPatternValidator, ValidationResult
from helpers.improved_scenario_generator import ImprovedOoTScenarioGenerator

# ============================================================================
# ENHANCED LOGGING SYSTEM
# ============================================================================

class OoTLogger:
    """Enhanced logging system with function names and relevant emojis"""
    
    def __init__(self, name: str = "OoTContextGenerator"):
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
    
    def success(self, message: str, func_name: Optional[str] = None):
        """Success level with ✅ emoji"""
        if func_name:
            self.logger.info(f"✅ {message}")
        else:
            self.logger.info(f"✅ {message}")

# Global logger instance
logger = OoTLogger()

class CompleteOoTContextGenerator:
    """Generates complete context for authentic OoT training data"""
    
    def __init__(self, oot_path: str = "oot"):
        self.oot_path = Path(oot_path)
        self.validator = OoTPatternValidator(oot_path)
        self.scenario_generator = ImprovedOoTScenarioGenerator()
        
        # Load real source code examples
        self.source_examples = self._load_source_examples()
        
        # Load real functions and constants from database
        self.real_functions = self._load_real_functions()
        self.real_constants = self._load_real_constants()
        self.real_sound_effects = self._load_real_sound_effects()
        
        logger.success(f"Loaded {len(self.real_functions)} real functions, {len(self.real_constants)} constants, {len(self.real_sound_effects)} sound effects")
    
    def _load_real_functions(self) -> List[str]:
        """Load real functions from the database file"""
        try:
            with open('oot_valid_functions.txt', 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            logger.warning("oot_valid_functions.txt not found")
            return []
    
    def _load_real_constants(self) -> List[str]:
        """Load real constants from the database file"""
        try:
            with open('oot_valid_constants.txt', 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            logger.warning("oot_valid_constants.txt not found")
            return []
    
    def _load_real_sound_effects(self) -> List[str]:
        """Load real sound effects from the database file"""
        try:
            with open('oot_valid_sound_effects.txt', 'r') as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            logger.warning("oot_valid_sound_effects.txt not found")
            return []
    
    def _get_category_functions(self, category: str) -> List[str]:
        """Dynamically get category-specific functions from real database"""
        if not self.real_functions:
            return []
        
        # Define category-specific patterns with priority scoring - using correct casing from OoT source
        category_patterns = {
            "enemy": {
                "high_priority": [
                    "Enemy_", "En_", "Actor_WorldDist", "Actor_ApplyDamage", 
                    "Enemy_Start", "CollisionCheck_", "Collider_"
                ],
                "medium_priority": [
                    "Actor_PlaySfx", "Actor_SetFocus", "Actor_UpdateBgCheckInfo",
                    "Math_Vec3f", "Math_Approach", "Flags_", "Matrix_"
                ],
                "low_priority": ["Actor_"]
            },
            "npc": {
                "high_priority": [
                    "Npc_", "Actor_OfferTalk", "Attention_", "Message_",
                    "Actor_Talk", "Npc_Interact", "Rand_", "Link_"
                ],
                "medium_priority": [
                    "Actor_SetFocus", "Collider_", "Actor_PlaySfx"
                ],
                "low_priority": ["Actor_"]
            },
            "item": {
                "high_priority": [
                    "Actor_OfferGetItem", "Actor_HasParent", "Flags_SetCollectible",
                    "Flags_GetCollectible", "Item_", "En_Item00", "Item00_", "Gi_"
                ],
                "medium_priority": [
                    "Actor_Spawn", "Math_", "Actor_PlaySfx"
                ],
                "low_priority": ["Actor_"]
            },
            "object": {
                "high_priority": [
                    "Flags_GetSwitch", "Flags_SetSwitch", "Obj_", "Bg_",
                    "DynaPoly_", "BgCheckFlag_"
                ],
                "medium_priority": [
                    "Collider_", "CollisionCheck_", "Actor_PlaySfx",
                    "Math_Approach", "Actor_"
                ],
                "low_priority": ["Actor_"]
            }
        }
        
        # Get patterns for this category
        patterns = category_patterns.get(category, {
            "high_priority": ["Actor_"],
            "medium_priority": ["Collider_"],
            "low_priority": ["Actor_"]
        })
        
        # Score functions by priority
        scored_functions = []
        for func in self.real_functions:
            func_lower = func.lower()
            score = 0
            
            # High priority patterns get highest score
            if any(pattern in func_lower for pattern in patterns["high_priority"]):
                score += 100
            # Medium priority patterns get medium score
            elif any(pattern in func_lower for pattern in patterns["medium_priority"]):
                score += 50
            # Low priority patterns get lowest score
            elif any(pattern in func_lower for pattern in patterns["low_priority"]):
                score += 10
            
            if score > 0:
                scored_functions.append((func, score))
        
        # Sort by score (highest first) and take top functions
        scored_functions.sort(key=lambda x: x[1], reverse=True)
        category_functions = [func for func, score in scored_functions[:50]]
        
        # Ensure we have core functions if they exist - using correct casing from OoT source
        core_functions = [
            "Actor_Init", "Actor_Destroy", "Actor_Update", "Actor_Draw",
            "Actor_ProcessInitChain", "Actor_SetScale", "Actor_Kill",
            "Collider_InitCylinder", "Collider_SetCylinder", "Collider_UpdateCylinder",
            "CollisionCheck_SetAC", "CollisionCheck_SetOC", "Actor_UpdateBgCheckInfo",
            "Actor_SetFocus", "Actor_PlaySfx", "Math_Vec3f_Copy", "Math_ApproachF"
        ]
        
        # Add core functions that exist in database and aren't already included
        for core_func in core_functions:
            if core_func in self.real_functions and core_func not in category_functions:
                category_functions.append(core_func)
        
        return category_functions[:50]
    
    def _get_category_constants(self, category: str) -> List[str]:
        """Dynamically get category-specific constants from real database"""
        if not self.real_constants:
            return []
        
        # Define category-specific patterns to filter real constants - using correct casing from OoT source
        category_patterns = {
            "enemy": [
                "ACTOR_FLAG_", "ACTORCAT_", "COL_", "COLLISION_", "COLLIDER_",
                "AT_", "AC_", "OC_", "OCELEM_", "TOUCH_", "BUMP_", "COLSHAPE_",
                "COLTYPE_", "ELEMTYPE_", "MASS_", "UPDBGCHECKINFO_FLAG_"
            ],
            "npc": [
                "ACTOR_FLAG_", "ACTORCAT_", "NPC_", "ATTENTION_", "MESSAGE_",
                "TALK_", "TEXT_", "COL_", "COLLISION_", "COLLIDER_"
            ],
            "item": [
                "ITEM00_", "GI_", "ACTOR_FLAG_", "ACTORCAT_", "FLAGS_",
                "COLLECTIBLE_", "ITEM_", "COL_", "COLLISION_", "COLLIDER_"
            ],
            "object": [
                "FLAGS_", "SWITCH_", "BGCHECKFLAG_", "ACTOR_FLAG_", "ACTORCAT_",
                "COL_", "COLLISION_", "COLLIDER_", "DYNAPOLY_", "OBJECT_"
            ]
        }
        
        # Get patterns for this category
        patterns = category_patterns.get(category, ["ACTOR_FLAG_", "ACTORCAT_", "COL_", "COLLISION_"])
        
        # Filter real constants by category patterns
        category_constants = []
        for const in self.real_constants:
            const_lower = const.lower()
            if any(pattern.lower() in const_lower for pattern in patterns):
                category_constants.append(const)
        
        # Return top 30 most relevant constants
        return category_constants[:30]
    
    def _get_category_sound_effects(self, category: str) -> List[str]:
        """Dynamically get category-specific sound effects from real database"""
        if not self.real_sound_effects:
            return []
        
        # Define category-specific patterns to filter real sound effects - using correct casing from OoT source
        category_patterns = {
            "enemy": [
                "NA_SE_EN_", "NA_SE_SY_", "NA_SE_IT_", "ATTACK", "DAMAGE", "DEATH"
            ],
            "npc": [
                "NA_SE_EN_", "NA_SE_SY_", "TALK", "VOICE", "CONVERSATION"
            ],
            "item": [
                "NA_SE_IT_", "NA_SE_EN_", "GET_", "COLLECT", "ITEM_"
            ],
            "object": [
                "NA_SE_SY_", "NA_SE_IT_", "SWITCH", "MECHANISM", "SY_"
            ]
        }
        
        # Get patterns for this category
        patterns = category_patterns.get(category, ["NA_SE_"])
        
        # Filter real sound effects by category patterns
        category_sfx = []
        for sfx in self.real_sound_effects:
            sfx_lower = sfx.lower()
            if any(pattern.lower() in sfx_lower for pattern in patterns):
                category_sfx.append(sfx)
        
        # Return top 20 most relevant sound effects
        return category_sfx[:20]
    
    def _load_source_examples(self) -> Dict[str, str]:
        """Load real source code examples from OoT decompilation"""
        return {
            "enemy_example": """
// REAL EXAMPLE: En_Am (Armos) from z_en_am.c
typedef struct EnAm {
    /* 0x0000 */ DynaPolyActor dyna;
    /* 0x0164 */ SkelAnime skelAnime;
    /* 0x01A8 */ s32 behavior;
    /* 0x01AC */ Vec3s jointTable[14];
    /* 0x0200 */ Vec3s morphTable[14];
    /* 0x0254 */ EnAmActionFunc actionFunc;
    /* 0x0258 */ s16 unk_258;
    /* 0x025A */ s16 cooldownTimer;
    /* 0x025C */ s16 attackTimer;
    /* 0x025E */ s16 iceTimer;
    /* 0x0260 */ s16 deathTimer;
    /* 0x0262 */ s16 panicSpinRot;
    /* 0x0264 */ s16 unk_264;
    /* 0x0266 */ u8 textureBlend;
    /* 0x0267 */ u8 damageReaction;
    /* 0x0267 */ Vec3f shakeOrigin;
    /* 0x0274 */ ColliderCylinder hurtCollider;
    /* 0x02C0 */ ColliderCylinder blockCollider;
    /* 0x030C */ ColliderQuad hitCollider;
} EnAm; // size = 0x038C

void EnAm_Init(Actor* thisx, PlayState* play) {
    EnAm* this = (EnAm*)thisx;
    
    Actor_ProcessInitChain(&this->dyna.actor, sInitChain);
    this->dyna.actor.colChkInfo.damageTable = &sDamageTable;
    this->dyna.actor.colChkInfo.health = 1;
    Collider_InitCylinder(play, &this->hurtCollider);
    Collider_SetCylinderType1(play, &this->hurtCollider, &this->dyna.actor, &sHurtCylinderInit);
    Collider_InitCylinder(play, &this->blockCollider);
    Collider_SetCylinderType1(play, &this->blockCollider, &this->dyna.actor, &sBlockCylinderInit);
    Collider_InitQuad(play, &this->hitCollider);
    Collider_SetQuad(play, &this->hitCollider, &this->dyna.actor, &sHitQuadInit);
    
    this->behavior = AM_BEHAVIOR_DO_NOTHING;
    this->dyna.actor.gravity = -2.0f;
    EnAm_SetupStatue(this);
}
""",
            
            "npc_example": """
// REAL EXAMPLE: En_Zo (Zora) from z_en_zo.c
typedef struct EnZo {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ SkelAnime skelAnime;
    /* 0x0190 */ EnZoActionFunc actionFunc;
    /* 0x0194 */ NpcInteractInfo interactInfo;
    /* 0x01BC */ ColliderCylinder collider;
    /* 0x0208 */ u8 canSpeak;
    /* 0x020A */ Vec3s jointTable[20];
    /* 0x0282 */ Vec3s morphTable[20];
    /* 0x02FC */ EnZoEffect effects[EN_ZO_EFFECT_COUNT];
    /* 0x0644 */ f32 dialogRadius;
    /* 0x0648 */ f32 alpha;
    /* 0x064C */ s16 trackingMode;
    /* 0x064E */ s16 rippleTimer;
    /* 0x0650 */ s16 timeToDive;
    /* 0x0652 */ s16 blinkTimer;
    /* 0x0654 */ s16 eyeTexture;
    /* 0x0656 */ s16 fidgetTableY[20];
    /* 0x067E */ s16 fidgetTableZ[20];
} EnZo; // size = 0x06A8

void EnZo_Dialog(EnZo* this, PlayState* play) {
    Player* player = GET_PLAYER(play);
    
    this->interactInfo.trackPos = player->actor.world.pos;
    if (this->actionFunc == EnZo_Standing) {
        this->interactInfo.yOffset = !LINK_IS_ADULT ? 10.0f : -10.0f;
    } else {
        this->interactInfo.trackPos.y = this->actor.world.pos.y;
    }
    Npc_TrackPoint(&this->actor, &this->interactInfo, 11, this->trackingMode);
    if (this->canSpeak == true) {
        Npc_UpdateTalking(play, &this->actor, &this->interactInfo.talkState, 
                          this->dialogRadius, EnZo_GetTextId, EnZo_UpdateTalkState);
    }
}
""",
            
            "item_example": """
// REAL EXAMPLE: Item_B_Heart (Heart Container) from z_item_b_heart.c
typedef struct ItemBHeart {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ ItemBHeartActionFunc actionFunc;
    /* 0x0150 */ s16 collectibleFlag;
} ItemBHeart; // size = 0x0154

void ItemBHeart_Init(Actor* thisx, PlayState* play) {
    ItemBHeart* this = (ItemBHeart*)thisx;
    
    if (Flags_GetCollectible(play, 0x1F)) {
        Actor_Kill(&this->actor);
    } else {
        Actor_ProcessInitChain(&this->actor, sInitChain);
        ActorShape_Init(&this->actor.shape, 0.0f, NULL, 0.8f);
    }
}

// REAL EXAMPLE: En_Item00 usage for collectibles
void SpawnHeartPiece(PlayState* play, Vec3f* pos) {
    Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00, 
                pos->x, pos->y, pos->z, 0, 0, 0, ITEM00_HEART_PIECE);
}
""",
            
            "object_example": """
// REAL EXAMPLE: Obj_Tsubo (Breakable Pot) from z_obj_tsubo.c
typedef struct ObjTsubo {
    /* 0x0000 */ Actor actor;
    /* 0x014C */ ObjTsuboActionFunc actionFunc;
    /* 0x0150 */ ColliderCylinder collider;
} ObjTsubo; // size = 0x019C

void ObjTsubo_Idle(ObjTsubo* this, PlayState* play) {
    if (Actor_HasParent(&this->actor, play)) {
        ObjTsubo_SetupHeld(this);
    } else if ((this->actor.bgCheckFlags & BGCHECKFLAG_WATER) && (this->actor.depthInWater > 19.0f)) {
        ObjTsubo_WaterBreak(this, play);
        SfxSource_PlaySfxAtFixedWorldPos(play, &this->actor.world.pos, 20, NA_SE_EV_POT_BROKEN);
        ObjTsubo_SpawnCollectible(this, play);
        Actor_Kill(&this->actor);
    } else if (this->collider.base.acFlags & AC_HIT) {
        ObjTsubo_AirBreak(this, play);
        SfxSource_PlaySfxAtFixedWorldPos(play, &this->actor.world.pos, 20, NA_SE_EV_POT_BROKEN);
        ObjTsubo_SpawnCollectible(this, play);
        Actor_Kill(&this->actor);
    }
}
"""
        }
    
    def generate_complete_training_example(self, category: str = "misc") -> Optional[Dict]:
        """Generate a complete training example with full context validation"""
        
        # Generate diverse scenario
        if category == "enemy":
            scenarios = self.scenario_generator.generate_enemy_scenarios(1)
        elif category == "npc":
            scenarios = self.scenario_generator.generate_npc_scenarios(1)
        elif category == "item":
            scenarios = self.scenario_generator.generate_item_scenarios(1)
        elif category == "object":
            scenarios = self.scenario_generator.generate_object_scenarios(1)
        else:
            # Random category
            all_scenarios = (
                self.scenario_generator.generate_enemy_scenarios(1) +
                self.scenario_generator.generate_npc_scenarios(1) +
                self.scenario_generator.generate_item_scenarios(1) +
                self.scenario_generator.generate_object_scenarios(1)
            )
            scenarios = [random.choice(all_scenarios)]
            category = self._detect_category(scenarios[0])
        
        scenario = scenarios[0]
        
        # Validate scenario
        validation = self.validator.validate_scenario(scenario, category)
        
        if not validation.is_valid:
            logger.warning(f"Scenario validation failed: {validation.issues}")
            return None
        
        # Create enhanced prompt with complete context
        enhanced_prompt = self._create_complete_prompt(scenario, category, validation)
        
        return {
            "scenario": scenario,
            "category": category,
            "validation": validation,
            "enhanced_prompt": enhanced_prompt,
            "context_length": len(enhanced_prompt),
            "authentic_patterns": validation.authentic_patterns,
            "required_functions": self._extract_required_functions(scenario, category),
            "source_references": self._get_source_references(category)
        }
    
    def _detect_category(self, scenario: str) -> str:
        """Detect category from scenario text"""
        if any(word in scenario.lower() for word in ["enemy", "boss", "attack", "combat", "hostile"]):
            return "enemy"
        elif any(word in scenario.lower() for word in ["npc", "dialogue", "shop", "talk", "merchant"]):
            return "npc"
        elif any(word in scenario.lower() for word in ["item", "sword", "shield", "potion", "collectible"]):
            return "item"
        elif any(word in scenario.lower() for word in ["object", "switch", "door", "platform", "mechanism"]):
            return "object"
        else:
            return "misc"
    
    def _create_complete_prompt(self, scenario: str, category: str, val) -> str:
        """Return a rich prompt containing requirements, authentic snippets, and a scenario-relevant function/constant list."""
        # Get real category-specific functions and constants
        functions = self._get_category_functions(category)
        constants = self._get_category_constants(category)
        sound_effects = self._get_category_sound_effects(category)
        

        
        # Combine all items
        all_items = functions + constants + sound_effects
        
        # Limit to reasonable number for prompt
        context_block = '\n'.join(f'- {item}' for item in all_items[:50])
        
        patterns = "\n".join(f"- {p}" for p in val.authentic_patterns[:6])
        issues_block = "\n".join(f"⚠️  {i}" for i in val.issues) or "None"
        suggestions_block = "\n".join(f"💡 {s}" for s in val.suggestions) or "None"
        ctx = "\n\n".join(val.required_context)
        complete_prompt = f"""
YOU MAY ONLY USE THE FOLLOWING FUNCTIONS AND CONSTANTS (from real OoT decompilation):
{context_block}

SCENARIO (category={category}): {scenario}

STRICT REQUIREMENTS:
1. Function signatures **must** be `(Actor* thisx, PlayState* play)`
2. Use real struct layouts and collision setup (`Collider_InitCylinder`, etc.)
3. Access positions via `actor.world.pos`, not deprecated fields.
4. Prefer re-using `EnItem00` for collectibles.
5. Use ONLY authentic OoT function names and constants.
6. Use `ActorProfile` structure correctly (see real examples).

AUTHENTIC PATTERNS TO EMULATE:
{patterns}

KNOWN ISSUES:
{issues_block}

SUGGESTIONS TO IMPROVE:
{suggestions_block}

{ctx}

Return only the C code, no explanations or JSON formatting.
"""
        

        
        return complete_prompt
    
    def _extract_required_functions(self, scenario: str, category: str) -> List[str]:
        """Extract functions that would be needed for this scenario"""
        # Use the dynamic category functions instead of hardcoded lists
        return self._get_category_functions(category)
    
    def _get_required_functions_list(self, category: str) -> List[str]:
        """Get comprehensive list of required functions for category"""
        # Use the dynamic category functions instead of hardcoded lists
        return self._get_category_functions(category)
    
    def _get_authentic_types(self, category: str) -> List[str]:
        """Get authentic type definitions for category"""
        base_types = [
            "Actor actor", "PlayState* play", "Vec3f world.pos", "s16 timer",
            "ColliderCylinder collider", "f32 scale", "u8 flags"
        ]
        
        category_types = {
            "enemy": [
                "s16 actionState", "s16 health", "s16 invincibilityTimer",
                "Vec3f homePos", "s16 attackTimer", "u8 damageReaction",
                "ColliderCylinder hurtCollider", "EnEnemyActionFunc actionFunc"
            ],
            "npc": [
                "NpcInteractInfo interactInfo", "s16 talkState", "s16 textId",
                "s16 blinkTimer", "s16 eyeTexIndex", "EnNpcActionFunc actionFunc",
                "NPC_TALK_STATE_IDLE", "ATTENTION_RANGE_6"
            ],
            "item": [
                "s16 itemId", "s16 collectTimer", "f32 bobPhase",
                "ITEM00_HEART_PIECE", "ITEM00_RUPEE_BLUE", "GI_HEART_PIECE"
            ],
            "object": [
                "DynaPolyActor dyna", "s16 switchState", "s16 activationTimer",
                "f32 targetY", "SWITCH_ON", "SWITCH_OFF"
            ]
        }
        
        return base_types + category_types.get(category, [])
    
    def _get_source_references(self, category: str) -> List[str]:
        """Get source file references for category"""
        references = {
            "enemy": [
                "z_en_am.c (Armos statue enemy)",
                "z_en_rr.c (Like Like enemy)",
                "z_en_mb.c (Moblin spear enemy)",
                "z_en_peehat.c (Flying Peahat enemy)"
            ],
            "npc": [
                "z_en_zo.c (Zora NPC)",
                "z_en_hy.c (Hylian townspeople)",
                "z_en_ds.c (Potion Shop Granny)",
                "z_en_go.c (Goron NPCs)"
            ],
            "item": [
                "z_item_b_heart.c (Heart Container)",
                "z_item_etcetera.c (Special items)",
                "z_en_item00.c (Collectibles)",
                "z_en_ex_item.c (Prize items)"
            ],
            "object": [
                "z_obj_tsubo.c (Breakable pot)",
                "z_obj_kibako.c (Wooden box)",
                "z_obj_switch.c (Switches)",
                "z_bg_haka_tubo.c (Large jars)"
            ]
        }
        
        return references.get(category, [])

def main():
    """Demonstrate the complete context generation system"""
    generator = CompleteOoTContextGenerator()
    
    logger.info("🎯 Complete OoT Context Generation System")
    logger.info("=" * 60)
    
    # Generate examples for each category
    categories = ["enemy", "npc", "item", "object"]
    
    for category in categories:
        logger.info(f"\n📂 CATEGORY: {category.upper()}")
        logger.info("-" * 40)
        
        example = generator.generate_complete_training_example(category)
        
        if example:
            logger.success(f"Generated valid example")
            logger.info(f"📝 Scenario: {example['scenario'][:80]}...")
            logger.info(f"📏 Context length: {example['context_length']} characters")
            logger.info(f"🔧 Required functions: {len(example['required_functions'])}")
            logger.info(f"📚 Source references: {len(example['source_references'])}")
            logger.info(f"🎯 Authentic patterns: {len(example['authentic_patterns'])}")
            
            # Show first few authentic patterns
            logger.info("   Patterns:")
            for pattern in example['authentic_patterns'][:2]:
                logger.info(f"   - {pattern}")
            
            # Show first few source references
            logger.info("   Sources:")
            for source in example['source_references'][:2]:
                logger.info(f"   - {source}")
                
        else:
            logger.warning("Failed to generate valid example")
    
    logger.info(f"\n🚀 SYSTEM READY FOR LLM GENERATION!")
    logger.info("   ✅ Validates scenarios against real OoT patterns")
    logger.info("   ✅ Provides complete source code context")
    logger.info("   ✅ Includes authentic function signatures and types")
    logger.info("   ✅ References real OoT decompilation files")
    logger.info("   ✅ Ensures LLM has everything needed for authentic code generation")
    logger.info("\n📋 Next steps:")
    logger.info("   1. Use enhanced_prompt for LLM generation")
    logger.info("   2. Generated code will be immediately usable in OoT romhacks")
    logger.info("   3. All patterns follow real decompilation standards")

if __name__ == "__main__":
    main() 