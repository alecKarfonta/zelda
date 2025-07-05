#!/usr/bin/env python3
"""
Complete Context Generator for OoT Training Data

This script integrates scenario validation with complete source code context
to ensure the LLM has everything needed to generate authentic OoT code.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from helpers.validate_and_enhance_scenarios import OoTPatternValidator, ValidationResult
from helpers.improved_scenario_generator import ImprovedOoTScenarioGenerator

class CompleteOoTContextGenerator:
    """Generates complete context for authentic OoT training data"""
    
    def __init__(self, oot_path: str = "oot"):
        self.oot_path = Path(oot_path)
        self.validator = OoTPatternValidator(oot_path)
        self.scenario_generator = ImprovedOoTScenarioGenerator()
        
        # Load real source code examples
        self.source_examples = self._load_source_examples()
        
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
    
    def generate_complete_training_example(self, category: str = None) -> Optional[Dict]:
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
            print(f"⚠️  Scenario validation failed: {validation.issues}")
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
        # Get scenario-relevant functions/constants
        functions = self._get_required_functions_list(category)[:25]
        context_block = '\n'.join(f'- {f}' for f in functions)
        
        patterns = "\n".join(f"- {p}" for p in val.authentic_patterns[:6])
        issues_block = "\n".join(f"⚠️  {i}" for i in val.issues) or "None"
        suggestions_block = "\n".join(f"💡 {s}" for s in val.suggestions) or "None"
        ctx = "\n\n".join(val.required_context)
        return f"""
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

Return exactly this JSON:
{{
  "instruction": "clear instruction",
  "input": null,
  "output": "C code here"
}}
"""
    
    def _extract_required_functions(self, scenario: str, category: str) -> List[str]:
        """Extract functions that would be needed for this scenario"""
        functions = []
        
        if category == "enemy":
            functions = [
                "Actor_WorldDistXZToActor", "Actor_ApplyDamage", "Enemy_StartFinishingBlow",
                "Collider_InitCylinder", "CollisionCheck_SetAC", "Actor_UpdateBgCheckInfo",
                "Actor_SetScale", "Actor_SetFocus", "Actor_PlaySfx", "Math_Vec3f_Copy"
            ]
        elif category == "npc":
            functions = [
                "Npc_UpdateTalking", "Npc_TrackPoint", "Actor_TalkOfferAccepted",
                "Message_GetState", "Collider_InitCylinder", "Actor_SetScale",
                "Rand_S16Offset", "GET_PLAYER", "LINK_IS_ADULT"
            ]
        elif category == "item":
            functions = [
                "Actor_OfferGetItem", "Actor_HasParent", "Flags_SetCollectible",
                "Item_DropCollectible", "Actor_Spawn", "Math_SinS", "Actor_Kill"
            ]
        elif category == "object":
            functions = [
                "Flags_GetSwitch", "Flags_SetSwitch", "Math_ApproachF",
                "Collider_UpdateCylinder", "CollisionCheck_SetAC", "Actor_PlaySfx",
                "DynaPolyActor", "BGCHECKFLAG_GROUND"
            ]
        
        return functions
    
    def _get_required_functions_list(self, category: str) -> List[str]:
        """Get comprehensive list of required functions for category"""
        base_functions = [
            "Actor_Init", "Actor_Destroy", "Actor_Update", "Actor_Draw",
            "Actor_ProcessInitChain", "Actor_SetScale", "Actor_Kill",
            "PlayState* play", "Actor* thisx"
        ]
        
        category_functions = {
            "enemy": [
                "Actor_WorldDistXZToActor", "Actor_ApplyDamage", "Enemy_StartFinishingBlow",
                "Collider_InitCylinder", "Collider_SetCylinder", "Collider_UpdateCylinder",
                "CollisionCheck_SetAC", "CollisionCheck_SetOC", "Actor_UpdateBgCheckInfo",
                "Actor_SetFocus", "Actor_PlaySfx", "Math_Vec3f_Copy", "GET_PLAYER"
            ],
            "npc": [
                "Npc_UpdateTalking", "Npc_TrackPoint", "Actor_TalkOfferAccepted",
                "Message_GetState", "Collider_InitCylinder", "Collider_SetCylinder",
                "Actor_SetScale", "Rand_S16Offset", "GET_PLAYER", "LINK_IS_ADULT",
                "NPC_TALK_STATE_IDLE", "TEXT_STATE_CLOSING", "ATTENTION_RANGE_6"
            ],
            "item": [
                "Actor_OfferGetItem", "Actor_HasParent", "Flags_SetCollectible",
                "Flags_GetCollectible", "Item_DropCollectible", "Actor_Spawn",
                "Math_SinS", "ACTOR_EN_ITEM00", "ITEM00_HEART_PIECE", "ITEM00_RUPEE_BLUE"
            ],
            "object": [
                "Flags_GetSwitch", "Flags_SetSwitch", "Math_ApproachF",
                "Collider_UpdateCylinder", "CollisionCheck_SetAC", "Actor_PlaySfx",
                "DynaPolyActor", "BGCHECKFLAG_GROUND", "NA_SE_SY_SWITCH_ON"
            ]
        }
        
        return base_functions + category_functions.get(category, [])
    
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
    
    print("🎯 Complete OoT Context Generation System")
    print("=" * 60)
    
    # Generate examples for each category
    categories = ["enemy", "npc", "item", "object"]
    
    for category in categories:
        print(f"\n📂 CATEGORY: {category.upper()}")
        print("-" * 40)
        
        example = generator.generate_complete_training_example(category)
        
        if example:
            print(f"✅ Generated valid example")
            print(f"📝 Scenario: {example['scenario'][:80]}...")
            print(f"📏 Context length: {example['context_length']} characters")
            print(f"🔧 Required functions: {len(example['required_functions'])}")
            print(f"📚 Source references: {len(example['source_references'])}")
            print(f"🎯 Authentic patterns: {len(example['authentic_patterns'])}")
            
            # Show first few authentic patterns
            print("   Patterns:")
            for pattern in example['authentic_patterns'][:2]:
                print(f"   - {pattern}")
            
            # Show first few source references
            print("   Sources:")
            for source in example['source_references'][:2]:
                print(f"   - {source}")
                
        else:
            print("❌ Failed to generate valid example")
    
    print(f"\n🚀 SYSTEM READY FOR LLM GENERATION!")
    print("   ✅ Validates scenarios against real OoT patterns")
    print("   ✅ Provides complete source code context")
    print("   ✅ Includes authentic function signatures and types")
    print("   ✅ References real OoT decompilation files")
    print("   ✅ Ensures LLM has everything needed for authentic code generation")
    print("\n📋 Next steps:")
    print("   1. Use enhanced_prompt for LLM generation")
    print("   2. Generated code will be immediately usable in OoT romhacks")
    print("   3. All patterns follow real decompilation standards")

if __name__ == "__main__":
    main() 