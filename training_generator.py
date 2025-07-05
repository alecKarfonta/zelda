#!/usr/bin/env python3
"""
Enhanced OoT Romhack Training Data Generator with Authentic Source Data

This script leverages Claude to generate high-quality training data for fine-tuning
a language model on Ocarina of Time romhacking tasks. It uses authentic function
signatures, struct definitions, and patterns extracted from the actual OoT 
decompilation codebase for maximum technical accuracy.
"""

import json
import re
import random
import time
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import anthropic
import argparse
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Use pip install python-dotenv")

class ExampleType(Enum):
    CODE_EXPLANATION = "code_explanation"
    FEATURE_IMPLEMENTATION = "feature_implementation" 
    DEBUGGING_HELP = "debugging_help"
    ARCHITECTURE_QUESTION = "architecture_question"
    CONVERSATIONAL = "conversational"
    CODE_MODIFICATION = "code_modification"
    ACTOR_CREATION = "actor_creation"
    FUNCTION_USAGE = "function_usage"

@dataclass
class TrainingExample:
    """Represents a single training example"""
    example_type: ExampleType
    instruction: str
    input: Optional[str] = None
    output: str = ""
    metadata: Optional[Dict[str, Any]] = None
    quality_score: float = 0.0
    validation_notes: str = ""

class BasicSourceValidator:
    """Validates source code for common OoT patterns and functions"""
    
    def __init__(self):
        self.known_functions = set([
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
            "Actor_SpawnEntry", "Actor_Delete", "Actor_AddToCategory", "Actor_Find", "Actor_FindNearby",
            "Actor_ChangeCategory", "Actor_InitContext", "Actor_UpdateAll", "Actor_DrawAll", "Actor_KillAllWithMissingObject",
            "Actor_FreezeAllEnemies",
            
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
            "CollisionCheck_AC", "CollisionCheck_AT", "CollisionCheck_OC", "CollisionCheck_Damage", "CollisionCheck_LineOC",
            "CollisionCheck_LineOCCheckAll", "CollisionCheck_LineOCCheck",
            
            # Interaction functions
            "Actor_TalkOfferAccepted", "Actor_OfferTalkExchange", "Actor_OfferTalkExchangeEquiCylinder", "Actor_OfferTalk",
            "Actor_OfferTalkNearColChkInfoCylinder", "Actor_TextboxIsClosing", "Actor_GetPlayerExchangeItemId", 
            "Actor_GetScreenPos", "Actor_HasParent", "Actor_OfferGetItem", "Actor_OfferGetItemNearby", "Actor_OfferCarry",
            "Actor_HasNoParent", "Actor_IsFacingPlayer", "Actor_ActorAIsFacingActorB", "Actor_IsFacingAndNearPlayer",
            "Actor_ActorAIsFacingAndNearActorB", "Player_IsFacingActor", "Actor_ActorBIsFacingActorA", "Actor_IsLockedOn",
            "Actor_OtherIsLockedOn", "Npc_UpdateTalking", "Npc_GetTrackingPresetMaxPlayerYaw", "Npc_TrackPoint",
            "Npc_UpdateAutoTurn", "Npc_TrackPointWithLimits",
            
            # Flag system functions
            "Flags_GetSwitch", "Flags_SetSwitch", "Flags_UnsetSwitch", "Flags_GetUnknown", "Flags_SetUnknown",
            "Flags_UnsetUnknown", "Flags_GetTreasure", "Flags_SetTreasure", "Flags_GetClear", "Flags_SetClear",
            "Flags_UnsetClear", "Flags_GetTempClear", "Flags_SetTempClear", "Flags_UnsetTempClear", "Flags_GetCollectible",
            "Flags_SetCollectible", "Flags_GetEventChkInf", "Flags_SetEventChkInf", "Flags_GetInfTable", "Flags_SetInfTable",
            
            # Math and utility functions
            "Math_SinS", "Math_CosS", "Math_ApproachF", "Math_ApproachS", "Math_Vec3f_Copy", "Math_Vec3f_DistXZ",
            "Math_Vec3f_DistXYZ", "Rand_CenteredFloat", "Rand_ZeroFloat", "Player_GetHeight", "Player_PlaySfx",
            "Player_SetCsAction", "Player_SetCsActionWithHaltedActors", "Matrix_Translate", "Matrix_Scale", "Matrix_RotateX",
            "Matrix_RotateY", "Matrix_RotateZ", "Matrix_Push", "Matrix_Pop", "Matrix_NewMtx", "Matrix_Put", "Matrix_Get",
            "Matrix_MultVec3f",
            
            # Audio functions
            "Actor_PlaySfx", "Actor_PlaySfx_SurfaceBomb", "Actor_PlaySfx_Flagged2", "Actor_PlaySfx_FlaggedCentered1",
            "Actor_PlaySfx_FlaggedCentered2", "Actor_PlaySfx_Flagged", "Actor_PlaySfx_FlaggedTimer", "Audio_PlayActorSound2",
            "Audio_PlaySoundGeneral",
            
            # Graphics functions
            "Gfx_DrawDListOpa", "Gfx_DrawDListXlu", "Gfx_SetupDL", "func_80034BA0", "func_80034CC4", 
            "Actor_UpdateAlphaByDistance", "Actor_SetColorFilter", "Actor_DrawDoorLock",
            
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
            
            # Memory functions
            "ZELDA_ARENA_MALLOC", "ZELDA_ARENA_FREE", "THA_GetRemaining",
            
            # Background collision functions
            "func_800BFCB8", "func_8002F9EC", "func_80038A28",
            
            # Common macros
            "OPEN_DISPS", "CLOSE_DISPS", "MATRIX_FINALIZE_AND_LOAD", "GET_PLAYER"
        ])
        
        self.known_types = set([
            # Core OoT types from actor.h and other headers
            "Actor", "PlayState", "GlobalContext", "Vec3f", "Vec3s", "PosRot", "s16", "u16", "s32", "u32", "s8", "u8", "f32",
            
            # Actor system types
            "ActorShape", "ActorFunc", "ActorShadowFunc", "ActorProfile", "ActorEntry", "ActorOverlay", "ActorContext",
            "ActorListEntry", "ActorContextSceneFlags", "EnItem00", "EnItem00ActionFunc", "DynaPolyActor",
            
            # Collision types
            "ColliderCylinder", "ColliderJntSph", "ColliderTris", "ColliderQuad", "ColliderElement", "CollisionCheckInfo",
            "CollisionCheckContext", "ColliderCylinderInit", "ColliderJntSphInit", "ColliderElementInit", 
            "ColliderElementDamageInfoAT", "ColliderElementDamageInfoAC", "ColliderJntSphElement", "ColliderJntSphElementDim",
            "ColliderJntSphElementInit", "ColliderInit", "ColliderInitToActor", "ColliderInitType1", "Collider",
            "CollisionPoly", "BgCheckFlags", "OcLine",
            
            # Animation types
            "SkelAnime", "AnimationHeader", "OverrideLimbDraw", "PostLimbDraw", "AnimationInfo",
            
            # Graphics types
            "Gfx", "GraphicsContext", "Color_RGBA8", "Color_RGB8", "Color_RGBAf", "MtxF", "Mtx", "Lights", "Light",
            "BodyBreak", "Hilite", "Vtx",
            
            # Player and NPC types
            "Player", "NpcInteractInfo", "NpcGetTextIdFunc", "NpcUpdateTalkStateFunc", "NpcTrackingMode", "NpcTalkState",
            "NpcTrackingRotLimits", "NpcTrackingParams",
            
            # Attention system types
            "Attention", "LockOnReticle", "AttentionColor", "AttentionRangeType",
            
            # Title card types
            "TitleCardContext",
            
            # Context types
            "ObjectContext", "GameState",
            
            # Item and effect types
            "InitChainEntry", "ItemId", "GetItemId",
            
            # Math types
            "Math3D", "Sphere16", "Cylinder16", "TriNorm",
            
            # Enum types
            "ActorCategory", "ActorFootIndex", "DoorLockType", "NaviEnemy", "AttentionRangeType", "ColChkBloodType",
            "ColChkHitType", "ColChkMassType", "DoorOpenAnim", "NpcTalkState", "NpcTrackingMode",
            
            # Flag and parameter types
            "s32", "u32", "s16", "u16", "s8", "u8", "f32", "f64",
            
            # Common preprocessor types
            "NULL", "true", "false"
        ])
        
        # Common corrections for outdated/incorrect patterns
        self.corrections = {
            "GlobalContext": "PlayState",
            "globalCtx": "play",
            "this->actor.pos": "this->actor.world.pos",
            "this->actor.rot": "this->actor.world.rot",
            "Actor_Spawn(": "Actor_SpawnAsChild(",
            "gPlayState": "play",
            "gGlobalCtx": "play",
            "player->actor.pos": "player->actor.world.pos",
            "ACTORCAT_BG": "ACTORCAT_BG",  # These are correct
            "ACTORCAT_SWITCH": "ACTORCAT_SWITCH",
            "ACTORCAT_EXPLOSIVE": "ACTORCAT_EXPLOSIVE",
            "ACTORCAT_NPC": "ACTORCAT_NPC",
            "ACTORCAT_ENEMY": "ACTORCAT_ENEMY",
            "ACTORCAT_PROP": "ACTORCAT_PROP",
            "ACTORCAT_ITEMACTION": "ACTORCAT_ITEMACTION",
            "ACTORCAT_MISC": "ACTORCAT_MISC",
            "ACTORCAT_BOSS": "ACTORCAT_BOSS",
            "ACTORCAT_DOOR": "ACTORCAT_DOOR",
            "ACTORCAT_CHEST": "ACTORCAT_CHEST"
        }
    
    def validate_functions(self, code: str) -> List[str]:
        """Validate function usage in code"""
        issues = []
        func_pattern = r'(\w+)\s*\('
        
        for match in re.finditer(func_pattern, code):
            func_name = match.group(1)
            if (func_name not in self.known_functions and 
                func_name not in ['if', 'for', 'while', 'switch', 'sizeof', 'typedef'] and
                not func_name.startswith('g') and  # Skip display lists like gSPDisplayList
                not func_name.isupper()):  # Skip macros
                issues.append(f"Unknown function: {func_name}")
        
        return issues
    
    def suggest_corrections(self, code: str) -> str:
        """Apply common corrections to code"""
        corrected = code
        for old, new in self.corrections.items():
            corrected = corrected.replace(old, new)
        return corrected

class OoTTrainingDataGenerator:
    """Enhanced training data generator with authentic OoT source data"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Try to get API key from environment first, then parameter
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Either:\n"
                "1. Set ANTHROPIC_API_KEY in .env file, or\n" 
                "2. Pass api_key parameter to constructor"
            )
        
        # Try to get model from environment, then parameter, then default
        self.model = model or os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        
        # Initialize Claude client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Load enhanced context templates and validation
        self.context_templates = self._load_enhanced_context_templates()
        self.example_templates = self._load_enhanced_example_templates()
        self.validator = BasicSourceValidator()
        
    def _load_authentic_function_database(self) -> Dict[str, List[str]]:
        """Load authentic function signatures from the OoT decompilation"""
        return {
            "actor_management": [
                # From z_actor.c - Core actor system functions
                "void ActorShape_Init(ActorShape* shape, f32 yOffset, ActorShadowFunc shadowDraw, f32 shadowScale)",
                "void ActorShadow_DrawCircle(Actor* actor, Lights* lights, PlayState* play)",
                "void ActorShadow_DrawWhiteCircle(Actor* actor, Lights* lights, PlayState* play)",
                "void ActorShadow_DrawHorse(Actor* actor, Lights* lights, PlayState* play)",
                "void ActorShadow_DrawFeet(Actor* actor, Lights* lights, PlayState* play)",
                "void Actor_SetFeetPos(Actor* actor, s32 limbIndex, s32 leftFootIndex, Vec3f* leftFootPos, s32 rightFootIndex, Vec3f* rightFootPos)",
                "void Actor_ProjectPos(PlayState* play, Vec3f* src, Vec3f* xyzDest, f32* cappedInvWDest)",
                "void Actor_Kill(Actor* actor)",
                "void Actor_SetWorldToHome(Actor* actor)",
                "void Actor_SetFocus(Actor* actor, f32 yOffset)",
                "void Actor_SetWorldRotToShape(Actor* actor)",
                "void Actor_SetShapeRotToWorld(Actor* actor)",
                "void Actor_SetScale(Actor* actor, f32 scale)",
                "void Actor_SetObjectDependency(PlayState* play, Actor* actor)",
                "void Actor_Init(Actor* actor, PlayState* play)",
                "void Actor_Destroy(Actor* actor, PlayState* play)",
                "void Actor_UpdatePos(Actor* actor)",
                "void Actor_UpdateVelocityXZGravity(Actor* actor)",
                "void Actor_MoveXZGravity(Actor* actor)",
                "void Actor_UpdateVelocityXYZ(Actor* actor)",
                "void Actor_MoveXYZ(Actor* actor)",
                "void Actor_SetProjectileSpeed(Actor* actor, f32 speedXYZ)",
                "void Actor_UpdatePosByAnimation(Actor* actor, SkelAnime* skelAnime)",
                "s16 Actor_WorldYawTowardActor(Actor* origin, Actor* target)",
                "s16 Actor_FocusYawTowardActor(Actor* origin, Actor* target)",
                "s16 Actor_WorldYawTowardPoint(Actor* origin, Vec3f* point)",
                "s16 Actor_WorldPitchTowardActor(Actor* actorA, Actor* actorB)",
                "s16 Actor_FocusPitchTowardActor(Actor* actorA, Actor* actorB)",
                "s16 Actor_WorldPitchTowardPoint(Actor* actor, Vec3f* refPoint)",
                "f32 Actor_WorldDistXYZToActor(Actor* actorA, Actor* actorB)",
                "f32 Actor_WorldDistXYZToPoint(Actor* actor, Vec3f* refPoint)",
                "f32 Actor_WorldDistXZToActor(Actor* actorA, Actor* actorB)",
                "f32 Actor_WorldDistXZToPoint(Actor* actor, Vec3f* refPoint)",
                "void Actor_WorldToActorCoords(Actor* actor, Vec3f* dest, Vec3f* pos)",
                "f32 Actor_HeightDiff(Actor* actorA, Actor* actorB)",
                "void Actor_UpdateBgCheckInfo(PlayState* play, Actor* actor, f32 wallCheckHeight, f32 wallCheckRadius, f32 ceilingCheckHeight, s32 flags)",
                "PosRot Actor_GetFocus(Actor* actor)",
                "PosRot Actor_GetWorld(Actor* actor)",
                "PosRot Actor_GetWorldPosShapeRot(Actor* actor)",
                "Actor* Actor_Spawn(ActorContext* actorCtx, PlayState* play, s16 actorId, f32 posX, f32 posY, f32 posZ, s16 rotX, s16 rotY, s16 rotZ, s16 params)",
                "Actor* Actor_SpawnAsChild(ActorContext* actorCtx, Actor* parent, PlayState* play, s16 actorId, f32 posX, f32 posY, f32 posZ, s16 rotX, s16 rotY, s16 rotZ, s16 params)",
                "void Actor_SpawnTransitionActors(PlayState* play, ActorContext* actorCtx)",
                "Actor* Actor_SpawnEntry(ActorContext* actorCtx, ActorEntry* actorEntry, PlayState* play)",
                "Actor* Actor_Delete(ActorContext* actorCtx, Actor* actor, PlayState* play)",
                "void Actor_AddToCategory(ActorContext* actorCtx, Actor* actorToAdd, u8 actorCategory)",
                "Actor* Actor_Find(ActorContext* actorCtx, s32 actorId, s32 actorCategory)",
                "Actor* Actor_FindNearby(PlayState* play, Actor* refActor, s16 actorId, u8 actorCategory, f32 range)",
                "void Actor_ChangeCategory(PlayState* play, ActorContext* actorCtx, Actor* actor, u8 actorCategory)",
                "void Actor_InitContext(PlayState* play, ActorContext* actorCtx, ActorEntry* playerEntry)",
                "void Actor_UpdateAll(PlayState* play, ActorContext* actorCtx)",
                "void Actor_DrawAll(PlayState* play, ActorContext* actorCtx)",
                "void Actor_KillAllWithMissingObject(PlayState* play, ActorContext* actorCtx)",
                "void Actor_FreezeAllEnemies(PlayState* play, ActorContext* actorCtx, s32 duration)"
            ],
            
            "collision_system": [
                # From z_collision_check.c - Collision system functions
                "s32 Collider_InitBase(PlayState* play, Collider* col)",
                "s32 Collider_DestroyBase(PlayState* play, Collider* col)",
                "s32 Collider_SetBaseToActor(PlayState* play, Collider* col, ColliderInitToActor* src)",
                "s32 Collider_SetBaseType1(PlayState* play, Collider* col, Actor* actor, ColliderInitType1* src)",
                "s32 Collider_SetBase(PlayState* play, Collider* col, Actor* actor, ColliderInit* src)",
                "void Collider_ResetATBase(PlayState* play, Collider* col)",
                "void Collider_ResetACBase(PlayState* play, Collider* col)",
                "void Collider_ResetOCBase(PlayState* play, Collider* col)",
                "s32 Collider_InitElement(PlayState* play, ColliderElement* elem)",
                "s32 Collider_DestroyElement(PlayState* play, ColliderElement* elem)",
                "s32 Collider_SetElement(PlayState* play, ColliderElement* elem, ColliderElementInit* elemInit)",
                "void Collider_ResetATElement(PlayState* play, ColliderElement* elem)",
                "void Collider_ResetACElement(PlayState* play, ColliderElement* elem)",
                "void Collider_ResetOCElement(PlayState* play, ColliderElement* elem)",
                
                # Cylinder colliders
                "s32 Collider_InitCylinder(PlayState* play, ColliderCylinder* cyl)",
                "s32 Collider_DestroyCylinder(PlayState* play, ColliderCylinder* cyl)",
                "s32 Collider_SetCylinderToActor(PlayState* play, ColliderCylinder* dest, ColliderCylinderInitToActor* src)",
                "s32 Collider_SetCylinderType1(PlayState* play, ColliderCylinder* dest, Actor* actor, ColliderCylinderInitType1* src)",
                "s32 Collider_SetCylinder(PlayState* play, ColliderCylinder* dest, Actor* actor, ColliderCylinderInit* src)",
                "s32 Collider_ResetCylinderAT(PlayState* play, Collider* col)",
                "s32 Collider_ResetCylinderAC(PlayState* play, Collider* col)",
                "s32 Collider_ResetCylinderOC(PlayState* play, Collider* col)",
                "void Collider_UpdateCylinder(Actor* actor, ColliderCylinder* cyl)",
                "void Collider_SetCylinderPosition(ColliderCylinder* cyl, Vec3s* pos)",
                
                # JntSph colliders  
                "s32 Collider_InitJntSph(PlayState* play, ColliderJntSph* jntSph)",
                "s32 Collider_FreeJntSph(PlayState* play, ColliderJntSph* jntSph)",
                "s32 Collider_DestroyJntSph(PlayState* play, ColliderJntSph* jntSph)",
                "s32 Collider_SetJntSphToActor(PlayState* play, ColliderJntSph* dest, ColliderJntSphInitToActor* src)",
                "s32 Collider_SetJntSphAllocType1(PlayState* play, ColliderJntSph* dest, Actor* actor, ColliderJntSphInitType1* src)",
                "s32 Collider_SetJntSphAlloc(PlayState* play, ColliderJntSph* dest, Actor* actor, ColliderJntSphInit* src)",
                "s32 Collider_SetJntSph(PlayState* play, ColliderJntSph* dest, Actor* actor, ColliderJntSphInit* src, ColliderJntSphElement* jntSphElements)",
                "s32 Collider_ResetJntSphAT(PlayState* play, Collider* col)",
                "s32 Collider_ResetJntSphAC(PlayState* play, Collider* col)",
                "s32 Collider_ResetJntSphOC(PlayState* play, Collider* col)",
                "void Collider_UpdateSpheres(s32 limb, ColliderJntSph* jntSph)",
                
                # Collision check context
                "void CollisionCheck_InitContext(PlayState* play, CollisionCheckContext* colChkCtx)",
                "void CollisionCheck_DestroyContext(PlayState* play, CollisionCheckContext* colChkCtx)",
                "void CollisionCheck_ClearContext(PlayState* play, CollisionCheckContext* colChkCtx)",
                "s32 CollisionCheck_SetAT(PlayState* play, CollisionCheckContext* colChkCtx, Collider* collider)",
                "s32 CollisionCheck_SetAC(PlayState* play, CollisionCheckContext* colChkCtx, Collider* collider)",
                "s32 CollisionCheck_SetOC(PlayState* play, CollisionCheckContext* colChkCtx, Collider* collider)",
                "s32 CollisionCheck_SetOCLine(PlayState* play, CollisionCheckContext* colChkCtx, OcLine* collider)",
                
                # Collision checking functions
                "void CollisionCheck_AC(PlayState* play, CollisionCheckContext* colChkCtx, Collider* atCol)",
                "void CollisionCheck_AT(PlayState* play, CollisionCheckContext* colChkCtx)",
                "void CollisionCheck_OC(PlayState* play, CollisionCheckContext* colChkCtx)",
                "void CollisionCheck_Damage(PlayState* play, CollisionCheckContext* colChkCtx)",
                "s32 CollisionCheck_LineOC(PlayState* play, CollisionCheckContext* colChkCtx, Vec3f* a, Vec3f* b, Actor** exclusions, s32 numExclusions)",
                "s32 CollisionCheck_LineOCCheckAll(PlayState* play, CollisionCheckContext* colChkCtx, Vec3f* a, Vec3f* b)",
                "s32 CollisionCheck_LineOCCheck(PlayState* play, CollisionCheckContext* colChkCtx, Vec3f* a, Vec3f* b, Actor** exclusions, s32 numExclusions)"
            ],
            
            "interaction_system": [
                # From z_actor.c - Actor interaction functions
                "s32 Actor_TalkOfferAccepted(Actor* actor, PlayState* play)",
                "s32 Actor_OfferTalkExchange(Actor* actor, PlayState* play, f32 xzRange, f32 yRange, u32 exchangeItemId)",
                "s32 Actor_OfferTalkExchangeEquiCylinder(Actor* actor, PlayState* play, f32 radius, u32 exchangeItemId)",
                "s32 Actor_OfferTalk(Actor* actor, PlayState* play, f32 radius)",
                "s32 Actor_OfferTalkNearColChkInfoCylinder(Actor* actor, PlayState* play)",
                "u32 Actor_TextboxIsClosing(Actor* actor, PlayState* play)",
                "s8 Actor_GetPlayerExchangeItemId(PlayState* play)",
                "void Actor_GetScreenPos(PlayState* play, Actor* actor, s16* x, s16* y)",
                "u32 Actor_HasParent(Actor* actor, PlayState* play)",
                "s32 Actor_OfferGetItem(Actor* actor, PlayState* play, s32 getItemId, f32 xzRange, f32 yRange)",
                "s32 Actor_OfferGetItemNearby(Actor* actor, PlayState* play, s32 getItemId)",
                "s32 Actor_OfferCarry(Actor* actor, PlayState* play)",
                "u32 Actor_HasNoParent(Actor* actor, PlayState* play)",
                "s32 Actor_IsFacingPlayer(Actor* actor, s16 maxAngle)",
                "s32 Actor_ActorAIsFacingActorB(Actor* actorA, Actor* actorB, s16 maxAngle)",
                "s32 Actor_IsFacingAndNearPlayer(Actor* actor, f32 range, s16 maxAngle)",
                "s32 Actor_ActorAIsFacingAndNearActorB(Actor* actorA, Actor* actorB, f32 range, s16 maxAngle)",
                "s32 Player_IsFacingActor(Actor* actor, s16 maxAngle, PlayState* play)",
                "s32 Actor_ActorBIsFacingActorA(Actor* actorA, Actor* actorB, s16 maxAngle)",
                "s32 Actor_IsLockedOn(PlayState* play, Actor* actor)",
                "s32 Actor_OtherIsLockedOn(PlayState* play, Actor* actor)",
                
                # NPC interaction functions
                "s32 Npc_UpdateTalking(PlayState* play, Actor* actor, s16* talkState, f32 interactRange, NpcGetTextIdFunc getTextId, NpcUpdateTalkStateFunc updateTalkState)",
                "s16 Npc_GetTrackingPresetMaxPlayerYaw(s16 presetIndex)",
                "void Npc_TrackPoint(Actor* actor, NpcInteractInfo* interactInfo, s16 presetIndex, s16 trackingMode)",
                "s16 Npc_UpdateAutoTurn(Actor* actor, NpcInteractInfo* interactInfo, f32 distanceRange, s16 maxYawForPlayerTracking, s16 trackingMode)",
                "void Npc_TrackPointWithLimits(Actor* actor, NpcInteractInfo* interactInfo, s16 maxHeadYaw, s16 maxHeadPitch, s16 minHeadPitch, s16 maxTorsoYaw, s16 maxTorsoPitch, s16 minTorsoPitch, u8 rotateYaw)"
            ],
            
            "flag_system": [
                # From z_actor.c - Game flag functions
                "s32 Flags_GetSwitch(PlayState* play, s32 flag)",
                "void Flags_SetSwitch(PlayState* play, s32 flag)",
                "void Flags_UnsetSwitch(PlayState* play, s32 flag)",
                "s32 Flags_GetUnknown(PlayState* play, s32 flag)",
                "void Flags_SetUnknown(PlayState* play, s32 flag)",
                "void Flags_UnsetUnknown(PlayState* play, s32 flag)",
                "s32 Flags_GetTreasure(PlayState* play, s32 flag)",
                "void Flags_SetTreasure(PlayState* play, s32 flag)",
                "s32 Flags_GetClear(PlayState* play, s32 flag)",
                "void Flags_SetClear(PlayState* play, s32 flag)",
                "void Flags_UnsetClear(PlayState* play, s32 flag)",
                "s32 Flags_GetTempClear(PlayState* play, s32 flag)",
                "void Flags_SetTempClear(PlayState* play, s32 flag)",
                "void Flags_UnsetTempClear(PlayState* play, s32 flag)",
                "s32 Flags_GetCollectible(PlayState* play, s32 flag)",
                "void Flags_SetCollectible(PlayState* play, s32 flag)",
                "s32 Flags_GetEventChkInf(s32 flag)",
                "void Flags_SetEventChkInf(s32 flag)",
                "s32 Flags_GetInfTable(s32 flag)",
                "void Flags_SetInfTable(s32 flag)"
            ],
            
            "utility_functions": [
                # Math functions
                "f32 Math_SinS(s16 angle)",
                "f32 Math_CosS(s16 angle)",
                "s32 Math_ApproachF(f32* pValue, f32 target, f32 scale, f32 maxStep)",
                "s32 Math_ApproachS(s16* pValue, s16 target, s16 scale, s16 maxStep)",
                "void Math_Vec3f_Copy(Vec3f* dest, Vec3f* src)",
                "f32 Math_Vec3f_DistXZ(Vec3f* a, Vec3f* b)",
                "f32 Math_Vec3f_DistXYZ(Vec3f* a, Vec3f* b)",
                "f32 Rand_CenteredFloat(f32 scale)",
                "f32 Rand_ZeroFloat(f32 scale)",
                
                # Player functions
                "f32 Player_GetHeight(Player* player)",
                "void Player_PlaySfx(Player* player, u16 sfxId)",
                "s32 Player_SetCsAction(PlayState* play, Actor* csActor, u8 csAction)",
                "s32 Player_SetCsActionWithHaltedActors(PlayState* play, Actor* csActor, u8 csAction)",
                
                # Matrix functions
                "void Matrix_Translate(f32 x, f32 y, f32 z, u8 mode)",
                "void Matrix_Scale(f32 x, f32 y, f32 z, u8 mode)",
                "void Matrix_RotateX(f32 x, u8 mode)",
                "void Matrix_RotateY(f32 y, u8 mode)",
                "void Matrix_RotateZ(f32 z, u8 mode)",
                "void Matrix_Push(void)",
                "void Matrix_Pop(void)",
                "Mtx* Matrix_NewMtx(GraphicsContext* gfxCtx, char* file, s32 line)",
                "void Matrix_Put(MtxF* src)",
                "void Matrix_Get(MtxF* dest)",
                "void Matrix_MultVec3f(Vec3f* src, Vec3f* dest)"
            ],
            
            "audio_functions": [
                # From z_actor.c - Audio functions
                "void Actor_PlaySfx(Actor* actor, u16 sfxId)",
                "void Actor_PlaySfx_SurfaceBomb(PlayState* play, Actor* actor)",
                "void Actor_PlaySfx_Flagged2(Actor* actor, u16 sfxId)",
                "void Actor_PlaySfx_FlaggedCentered1(Actor* actor, u16 sfxId)",
                "void Actor_PlaySfx_FlaggedCentered2(Actor* actor, u16 sfxId)",
                "void Actor_PlaySfx_Flagged(Actor* actor, u16 sfxId)",
                "void Actor_PlaySfx_FlaggedTimer(Actor* actor, s32 timer)",
                "void Audio_PlayActorSound2(Actor* actor, u16 sfxId)",
                "void Audio_PlaySoundGeneral(u16 sfxId, Vec3f* pos, u8 token, f32* freqScale, f32* volume, s8* reverbAdd)"
            ],
            
            "graphics_functions": [
                # Graphics and drawing functions
                "void Gfx_DrawDListOpa(PlayState* play, Gfx* dlist)",
                "void Gfx_DrawDListXlu(PlayState* play, Gfx* dlist)",
                "Gfx* Gfx_SetupDL(Gfx* gfx, u32 i)",
                "void func_80034BA0(PlayState* play, SkelAnime* skelAnime, OverrideLimbDraw overrideLimbDraw, PostLimbDraw postLimbDraw, Actor* actor, s16 alpha)",
                "void func_80034CC4(PlayState* play, SkelAnime* skelAnime, OverrideLimbDraw overrideLimbDraw, PostLimbDraw postLimbDraw, Actor* actor, s16 alpha)",
                "s16 Actor_UpdateAlphaByDistance(Actor* actor, PlayState* play, s16 alpha, f32 radius)",
                "void Actor_SetColorFilter(Actor* actor, s16 colorFlag, s16 colorIntensityMax, s16 bufFlag, s16 duration)",
                "void Actor_DrawDoorLock(PlayState* play, s32 frame, s32 type)"
            ],
            
            "item_functions": [
                # From z_en_item00.c - Item functions
                "void EnItem00_SetupAction(EnItem00* this, EnItem00ActionFunc actionFunc)",
                "void EnItem00_Init(Actor* thisx, PlayState* play)",
                "void EnItem00_Destroy(Actor* thisx, PlayState* play)",
                "void EnItem00_Update(Actor* thisx, PlayState* play)",
                "void EnItem00_Draw(Actor* thisx, PlayState* play)",
                "void EnItem00_DrawRupee(EnItem00* this, PlayState* play)",
                "void EnItem00_DrawCollectible(EnItem00* this, PlayState* play)",
                "void EnItem00_DrawHeartContainer(EnItem00* this, PlayState* play)",
                "void EnItem00_DrawHeartPiece(EnItem00* this, PlayState* play)",
                "EnItem00* Item_DropCollectible(PlayState* play, Vec3f* spawnPos, s16 params)",
                "EnItem00* Item_DropCollectible2(PlayState* play, Vec3f* spawnPos, s16 params)",
                "void Item_DropCollectibleRandom(PlayState* play, Actor* fromActor, Vec3f* spawnPos, s16 params)",
                "s16 func_8001F404(s16 dropId)"
            ],
            
            "effect_functions": [
                # Effect system functions
                "void Effect_Add(PlayState* play, s32* pIndex, s32 type, u8 flag, u8 id, void* initParams)",
                "void EffectBlure_AddVertex(EffectBlure* this, Vec3f* p1, Vec3f* p2)",
                "void EffectBlure_AddSpace(EffectBlure* this)",
                "void Actor_SpawnFloorDustRing(PlayState* play, Actor* actor, Vec3f* posXZ, f32 radius, s32 amountMinusOne, f32 randAccelWeight, s16 scale, s16 scaleStep, u8 useLighting)"
            ],
            
            "initialization_functions": [
                # Initialization chain functions
                "void Actor_ProcessInitChain(Actor* actor, InitChainEntry* ichain)",
                "s32 Object_GetSlot(ObjectContext* objectCtx, s16 objectId)",
                "void Object_LoadAll(ObjectContext* objectCtx)",
                "s32 Object_IsLoaded(ObjectContext* objectCtx, s32 slot)"
            ],
            
            "attention_system": [
                # From z_actor.c - Attention system functions  
                "void Attention_Init(Attention* attention, Actor* actor, PlayState* play)",
                "void Attention_SetNaviState(Attention* attention, Actor* actor, s32 actorCategory, PlayState* play)",
                "void Attention_InitReticle(Attention* attention, s32 actorCategory, PlayState* play)",
                "void Attention_SetReticlePos(Attention* attention, s32 reticleNum, f32 x, f32 y, f32 z)",
                "void Attention_Draw(Attention* attention, PlayState* play)",
                "Actor* Attention_FindActor(PlayState* play, ActorContext* actorCtx, Actor** attentionActorP, Player* player)",
                "s32 Attention_ShouldReleaseLockOn(Actor* actor, Player* player, s32 ignoreLeash)"
            ]
        }
    
    def _load_authentic_structs(self) -> Dict[str, Dict]:
        """Load authentic struct definitions from the OoT decompilation"""
        return {
            "Actor": {
                "description": "Base actor structure - all actors inherit from this",
                "size": "0x14C",
                "fields": [
                    "/* 0x000 */ s16 id;",
                    "/* 0x002 */ u8 category;",
                    "/* 0x003 */ s8 room;",
                    "/* 0x004 */ u32 flags;",
                    "/* 0x008 */ PosRot home;",
                    "/* 0x01C */ s16 params;",
                    "/* 0x01E */ s8 objectSlot;",
                    "/* 0x01F */ s8 attentionRangeType;",
                    "/* 0x020 */ u16 sfx;",
                    "/* 0x024 */ PosRot world;",
                    "/* 0x038 */ PosRot focus;",
                    "/* 0x04C */ f32 lockOnArrowOffset;",
                    "/* 0x050 */ Vec3f scale;",
                    "/* 0x05C */ Vec3f velocity;",
                    "/* 0x068 */ f32 speed;",
                    "/* 0x06C */ f32 gravity;",
                    "/* 0x070 */ f32 minVelocityY;",
                    "/* 0x074 */ CollisionPoly* wallPoly;",
                    "/* 0x078 */ CollisionPoly* floorPoly;",
                    "/* 0x07C */ u8 wallBgId;",
                    "/* 0x07D */ u8 floorBgId;",
                    "/* 0x07E */ s16 wallYaw;",
                    "/* 0x080 */ f32 floorHeight;",
                    "/* 0x084 */ f32 depthInWater;",
                    "/* 0x088 */ u16 bgCheckFlags;",
                    "/* 0x08A */ s16 yawTowardsPlayer;",
                    "/* 0x08C */ f32 xyzDistToPlayerSq;",
                    "/* 0x090 */ f32 xzDistToPlayer;",
                    "/* 0x094 */ f32 yDistToPlayer;",
                    "/* 0x098 */ CollisionCheckInfo colChkInfo;",
                    "/* 0x0B4 */ ActorShape shape;",
                    "/* 0x0E4 */ Vec3f projectedPos;",
                    "/* 0x0F0 */ f32 projectedW;",
                    "/* 0x118 */ Actor* parent;",
                    "/* 0x11C */ Actor* child;",
                    "/* 0x120 */ Actor* prev;",
                    "/* 0x124 */ Actor* next;",
                    "/* 0x128 */ ActorFunc init;",
                    "/* 0x12C */ ActorFunc destroy;",
                    "/* 0x130 */ ActorFunc update;",
                    "/* 0x134 */ ActorFunc draw;"
                ]
            },
            "ActorShape": {
                "description": "Actor shape and shadow information",
                "size": "0x30",
                "fields": [
                    "/* 0x00 */ Vec3s rot;",
                    "/* 0x06 */ s16 face;",
                    "/* 0x08 */ f32 yOffset;",
                    "/* 0x0C */ ActorShadowFunc shadowDraw;",
                    "/* 0x10 */ f32 shadowScale;",
                    "/* 0x14 */ u8 shadowAlpha;",
                    "/* 0x15 */ u8 feetFloorFlag;",
                    "/* 0x18 */ Vec3f feetPos[2];"
                ]
            },
            "EnItem00": {
                "description": "Collectible item actor (rupees, hearts, etc.)",
                "size": "0x160",
                "fields": [
                    "/* 0x000 */ Actor actor;",
                    "/* 0x14C */ s16 collectibleFlag;",
                    "/* 0x14E */ s16 unk_14E;",
                    "/* 0x150 */ s16 unk_150;",
                    "/* 0x152 */ s16 unk_152;",
                    "/* 0x154 */ f32 scale;",
                    "/* 0x158 */ u8 unk_158;",
                    "/* 0x159 */ u8 unk_159;",
                    "/* 0x15A */ s16 unk_15A;",
                    "/* 0x15C */ ColliderCylinder collider;",
                    "/* 0x15C */ EnItem00ActionFunc actionFunc;"
                ]
            }
        }
    
    def _load_enhanced_context_templates(self) -> Dict[str, str]:
        """Load enhanced context templates with authentic OoT data"""
        authentic_functions = self._load_authentic_function_database()
        authentic_structs = self._load_authentic_structs()
        
        return {
            "actor_system": f"""
AUTHENTIC OOT ACTOR SYSTEM CONTEXT (From Decompilation):

ACTOR STRUCTURE ({authentic_structs['Actor']['size']} bytes):
{chr(10).join(authentic_structs['Actor']['fields'][:20])}
... (full structure has {len(authentic_structs['Actor']['fields'])} fields)

ACTOR CATEGORIES:
- ACTORCAT_SWITCH (0): Switch actors
- ACTORCAT_BG (1): Background actors  
- ACTORCAT_PLAYER (2): Player actor
- ACTORCAT_EXPLOSIVE (3): Bomb actors
- ACTORCAT_NPC (4): NPC actors
- ACTORCAT_ENEMY (5): Enemy actors
- ACTORCAT_PROP (6): Prop actors
- ACTORCAT_ITEMACTION (7): Item action actors
- ACTORCAT_MISC (8): Misc actors
- ACTORCAT_BOSS (9): Boss actors
- ACTORCAT_DOOR (10): Door actors
- ACTORCAT_CHEST (11): Chest actors

CORE ACTOR FUNCTIONS:
{chr(10).join('- ' + func for func in authentic_functions['actor_management'][:10])}

ACTOR LIFECYCLE PATTERN:
```c
typedef struct {{
    /* 0x0000 */ Actor actor;
    /* 0x014C */ // Custom actor fields start here
    /* 0x014C */ s16 timer;
    /* 0x014E */ s16 state;
    /* 0x150 */ f32 customScale;
    /* 0x154 */ Vec3f targetPos;
    /* 0x160 */ ColliderCylinder collider;
}} ActorName; // size = 0x1A8

void ActorName_Init(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    
    // Initialize collider
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);
    
    // Set actor properties
    Actor_SetScale(&this->actor, 0.01f);
    Actor_SetFocus(&this->actor, 25.0f);
    
    // Initialize custom fields
    this->timer = 0;
    this->state = 0;
    this->customScale = 1.0f;
    
    // Set action function
    this->actionFunc = ActorName_Wait;
}}

void ActorName_Update(Actor* thisx, PlayState* play) {{
    ActorName* this = (ActorName*)thisx;
    
    // Update collision
    Actor_UpdateBgCheckInfo(play, &this->actor, 26.0f, 10.0f, 0.0f, BGCHECKFLAG_GROUND);
    
    // Update collider
    Collider_Update(play, &this->collider);
    CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
    
    // Call action function
    this->actionFunc(this, play);
    
    // Update movement
    Actor_MoveXZGravity(&this->actor);
}}
```

ACTORPROFILE STRUCTURE:
```c
ActorProfile ActorName_Profile = {{
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
""",
            
            "collision_system": f"""
AUTHENTIC OOT COLLISION SYSTEM CONTEXT:

COLLISION FUNCTIONS:
{chr(10).join('- ' + func for func in authentic_functions['collision_system'])}

COLLIDER INITIALIZATION PATTERN:
```c
static ColliderCylinderInit sCylinderInit = {{
    {{
        COL_MATERIAL_NONE,
        AT_NONE,
        AC_ON | AC_TYPE_PLAYER,
        OC1_ON | OC1_TYPE_ALL,
        OC2_TYPE_1,
        COLSHAPE_CYLINDER,
    }},
    {{
        ELEM_MATERIAL_UNK0,
        {{ 0x00000000, HIT_SPECIAL_EFFECT_NONE, 0x00 }},
        {{ 0x00000010, HIT_BACKLASH_NONE, 0x00 }},
        ATELEM_NONE,
        ACELEM_ON,
        OCELEM_ON,
    }},
    {{ 15, 25, 0, {{ 0, 0, 0 }} }},
}};

// In Init function:
Collider_InitCylinder(play, &this->collider);
Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);

// In Update function:
Collider_Update(play, &this->collider);
CollisionCheck_SetOC(play, &play->colChkCtx, &this->collider.base);
CollisionCheck_SetAC(play, &play->colChkCtx, &this->collider.base);
```

BGCHECK FLAGS:
- BGCHECKFLAG_GROUND (1 << 0): Standing on ground
- BGCHECKFLAG_WALL (1 << 3): Touching a wall
- BGCHECKFLAG_CEILING (1 << 4): Touching ceiling
- BGCHECKFLAG_WATER (1 << 5): In water
""",
            
            "interaction_system": f"""
AUTHENTIC OOT INTERACTION SYSTEM CONTEXT:

INTERACTION FUNCTIONS:
{chr(10).join('- ' + func for func in authentic_functions['interaction_system'])}

TALK INTERACTION PATTERN:
```c
// In Update function:
if (Actor_OfferTalk(&this->actor, play, 50.0f)) {{
    this->actionFunc = ActorName_Talk;
}}

// Talk action function:
void ActorName_Talk(ActorName* this, PlayState* play) {{
    if (Actor_TalkOfferAccepted(&this->actor, play)) {{
        switch (this->actor.textId) {{
            case 0x1000:
                this->actor.textId = 0x1001;
                break;
            default:
                this->actionFunc = ActorName_Wait;
                break;
        }}
    }}
}}
```

ITEM GIVING PATTERN:
```c
if (Actor_OfferGetItem(&this->actor, play, GI_RUPEE_BLUE, 30.0f, 30.0f)) {{
    this->actionFunc = ActorName_GiveItem;
}}

void ActorName_GiveItem(ActorName* this, PlayState* play) {{
    if (Actor_HasParent(&this->actor, play)) {{
        this->actionFunc = ActorName_Wait;
    }} else {{
        Actor_OfferGetItem(&this->actor, play, GI_RUPEE_BLUE, 30.0f, 30.0f);
    }}
}}
```
""",
            
            "debugging_context": """
AUTHENTIC OOT DEBUGGING CONTEXT:

COMMON CRASH SCENARIOS:
1. Actor size mismatch in ActorProfile (sizeof field incorrect)
2. Uninitialized collider usage
3. Object dependency not set before using object graphics
4. Accessing NULL pointers (actor->parent, actor->child)
5. Stack overflow from recursive action functions
6. Collision poly dereferencing without NULL checks
7. Invalid array access in animation or display lists

MEMORY ADDRESSES (Debug ROM):
- Current PlayState: 0x801C84A0
- Actor Context: 0x801C6F20  
- Heap Status: 0x801D9B60
- Object Context: 0x801C8440

DEBUG VALIDATION PATTERNS:
```c
// Always check object loading
s32 objBankIndex = Object_GetSlot(&play->objectCtx, OBJECT_ID);
if (objBankIndex < 0) {{
    // Object not loaded, can't proceed
    Actor_Kill(&this->actor);
    return;
}}

// Null pointer checks
if (this->actor.parent == NULL) {{
    // Handle no parent case
}}

// Collision poly validation
if (this->actor.floorPoly != NULL) {{
    // Safe to use floor polygon
    Vec3f normal;
    func_80038A28(this->actor.floorPoly, 
                  this->actor.world.pos.x, 
                  this->actor.world.pos.y,
                  this->actor.world.pos.z, &normal);
}}

// Array bounds checking
if (index >= 0 && index < ARRAY_COUNT(array)) {{
    return array[index];
}}
```

MEMORY DEBUGGING:
- Use THA_GetRemaining() to check available heap space
- Check for memory leaks by monitoring actor count
- Validate DMA transfers complete before accessing data
- Use ZELDA_ARENA_MALLOC/FREE for tracked allocation
""",
            
            "animation_system": """
AUTHENTIC OOT ANIMATION SYSTEM CONTEXT:

SKELANIME INITIALIZATION:
```c
// In actor struct:
SkelAnime skelAnime;

// In Init function:
SkelAnime_Init(play, &this->skelAnime, skeleton, animation, jointTable, morphTable, jointCount);

// In Update function:
SkelAnime_Update(&this->skelAnime);

// In Draw function:
SkelAnime_DrawFlexOpa(play, this->skelAnime.skeleton, this->skelAnime.jointTable, 
                      this->skelAnime.dListCount, NULL, NULL, this);
```

ANIMATION CHANGE PATTERNS:
```c
// Change animation
Animation_Change(&this->skelAnime, animation, 1.0f, 0.0f, Animation_GetLastFrame(animation), 
                 ANIMMODE_LOOP, -10.0f);

// Check if animation finished
if (SkelAnime_Update(&this->skelAnime)) {{
    // Animation finished, change to next
    Animation_Change(&this->skelAnime, nextAnimation, 1.0f, 0.0f, 
                     Animation_GetLastFrame(nextAnimation), ANIMMODE_ONCE, 0.0f);
}}
```

LIMB DRAWING OVERRIDES:
```c
s32 ActorName_OverrideLimbDraw(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot, void* thisx) {{
    ActorName* this = (ActorName*)thisx;
    
    if (limbIndex == LIMB_HEAD) {{
        // Modify head rotation for looking at player
        rot->y += this->headRotY;
    }}
    
    return false; // Don't skip drawing this limb
}}
```
""",
            
            "authentic_patterns": """
AUTHENTIC OOT CODING PATTERNS:

ACTOR FLAGS (from authentic decompilation):
- ACTOR_FLAG_ATTENTION_ENABLED (1 << 0): Discoverable by attention system
- ACTOR_FLAG_HOSTILE (1 << 2): Hostile toward player
- ACTOR_FLAG_FRIENDLY (1 << 3): Friendly NPC
- ACTOR_FLAG_UPDATE_CULLING_DISABLED (1 << 4): Always update
- ACTOR_FLAG_DRAW_CULLING_DISABLED (1 << 5): Always draw
- ACTOR_FLAG_TALK (1 << 8): Currently talking
- ACTOR_FLAG_HOOKSHOT_PULLS_PLAYER (1 << 10): Hookshot target
- ACTOR_FLAG_IGNORE_QUAKE (1 << 12): Ignore earthquakes
- ACTOR_FLAG_LOCK_ON_DISABLED (1 << 27): Cannot be locked onto

ICHAIN INITIALIZATION:
```c
static InitChainEntry sInitChain[] = {{
    ICHAIN_VEC3F_DIV1000(scale, 10, ICHAIN_CONTINUE),
    ICHAIN_F32(lockOnArrowOffset, 2000, ICHAIN_CONTINUE),
    ICHAIN_U8(naviEnemyId, NAVI_ENEMY_DEFAULT, ICHAIN_CONTINUE),
    ICHAIN_U16(sfx, 0, ICHAIN_STOP),
}};

// In Init:
Actor_ProcessInitChain(&this->actor, sInitChain);
```

PARAMETER EXTRACTION:
```c
// Extract parameters from actor spawn data
s16 switchFlag = PARAMS_GET_S(this->actor.params, 0, 6);    // Bits 0-5
s16 itemType = PARAMS_GET_S(this->actor.params, 6, 4);      // Bits 6-9
s16 behaviorType = PARAMS_GET_S(this->actor.params, 10, 2); // Bits 10-11
```

DISTANCE CHECKS:
```c
// Check distance to player
f32 distToPlayer = this->actor.xzDistToPlayer;
if (distToPlayer < 100.0f) {{
    // Player is close
}}

// Check if facing player
if (Actor_IsFacingPlayer(&this->actor, 0x4000)) {{
    // Actor is facing player (within 90 degrees)
}}
```

GRAPHICS CONTEXT USAGE:
```c
// In Draw function:
OPEN_DISPS(play->state.gfxCtx, __FILE__, __LINE__);

Gfx_SetupDL_25Opa(play->state.gfxCtx);
gSPMatrix(POLY_OPA_DISP++, MATRIX_NEWMTX(play->state.gfxCtx), G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
gSPDisplayList(POLY_OPA_DISP++, displayList);

CLOSE_DISPS(play->state.gfxCtx, __FILE__, __LINE__);
```
"""
        }
    
    def _load_enhanced_example_templates(self) -> Dict[ExampleType, List[Dict]]:
        """Load enhanced example templates with specific OoT scenarios"""
        return {
            ExampleType.CODE_EXPLANATION: [
                {
                    "scenario": "actor_function_explanation",
                    "instruction_template": "Explain what the function {function_name} does in OoT",
                    "variables": {
                        "function_name": ["Actor_UpdateBgCheckInfo", "Actor_WorldDistXZToActor", "Collider_SetCylinder", "Math_ApproachF", "SkelAnime_Update"]
                    },
                    "context_types": ["actor_system", "collision_system", "animation_system"],
                    "complexity": "intermediate"
                },
                {
                    "scenario": "struct_explanation", 
                    "instruction_template": "Explain the {struct_name} structure in OoT and its purpose",
                    "variables": {
                        "struct_name": ["Actor", "ActorShape", "ColliderCylinder", "SkelAnime", "PlayState"]
                    },
                    "context_types": ["actor_system", "collision_system"],
                    "complexity": "advanced"
                }
            ],
            ExampleType.FEATURE_IMPLEMENTATION: [
                {
                    "scenario": "collectible_actor",
                    "instruction_template": "Create a {item_type} actor that {behavior}",
                    "variables": {
                        "item_type": ["rupee", "heart piece", "key", "magic jar", "arrow bundle"],
                        "behavior": ["spawns from defeated enemies", "appears after hitting a switch", "follows the player", "bounces when dropped", "glows and plays a jingle"]
                    },
                    "context_types": ["actor_system", "collision_system"],
                    "complexity": "intermediate"
                },
                {
                    "scenario": "npc_actor",
                    "instruction_template": "Create an NPC that {interaction} and {behavior}",
                    "variables": {
                        "interaction": ["gives hints about puzzles", "sells items", "teaches songs", "tells stories"],
                        "behavior": ["looks at the player", "moves between waypoints", "reacts to items", "changes dialog based on progress"]
                    },
                    "context_types": ["actor_system", "interaction_system"],
                    "complexity": "advanced"
                }
            ],
            ExampleType.DEBUGGING_HELP: [
                {
                    "scenario": "crash_debugging",
                    "instruction_template": "My {actor_type} actor is crashing when {action}. Here's my code:",
                    "variables": {
                        "actor_type": ["enemy", "NPC", "collectible item", "environmental object"],
                        "action": ["it tries to move", "Link gets close", "it spawns", "it tries to draw", "collision occurs"]
                    },
                    "context_types": ["debugging_context"],
                    "complexity": "intermediate"
                }
            ],
            ExampleType.ACTOR_CREATION: [
                {
                    "scenario": "full_actor_implementation",
                    "instruction_template": "Create a complete {actor_type} actor with {features}",
                    "variables": {
                        "actor_type": ["simple enemy", "interactive object", "moving platform", "puzzle element"],
                        "features": ["collision detection", "animation", "sound effects", "player interaction"]
                    },
                    "context_types": ["actor_system", "collision_system", "animation_system"],
                    "complexity": "advanced"
                }
            ]
        }

    def generate_training_example(self, example_type: ExampleType, complexity: str = "intermediate") -> TrainingExample:
        """Generate a single training example of the specified type"""
        
        # Select appropriate context and template
        templates = self.example_templates[example_type]
        template = random.choice(templates)
        context_type = random.choice(template["context_types"])
        
        # Build enhanced generation prompt with authentic data
        generation_prompt = self._build_enhanced_generation_prompt(example_type, template, context_type, complexity)
        
        # Generate initial example
        raw_example = self._call_claude(generation_prompt)
        
        # Parse the generated example
        example = self._parse_generated_example(raw_example, example_type)
        
        if example:
            # Validate and refine with authentic OoT patterns
            example = self._validate_and_refine_enhanced(example)
            return example
        
        # If parsing failed, return empty example
        return TrainingExample(example_type=example_type, instruction="", output="")

    def _build_enhanced_generation_prompt(self, example_type: ExampleType, template: Dict, 
                                        context_type: str, complexity: str) -> str:
        """Build enhanced prompt with authentic OoT context and specific scenarios"""
        
        context = self.context_templates[context_type]
        
        # Generate specific variables if template has them
        instruction = template["instruction_template"]
        if "variables" in template:
            for var_name, var_options in template["variables"].items():
                chosen_value = random.choice(var_options)
                instruction = instruction.replace(f"{{{var_name}}}", chosen_value)
        
        base_prompt = f"""
You are an expert in Ocarina of Time romhacking and decompilation. Generate a high-quality training example for teaching AI assistants about OoT modding using AUTHENTIC information from the actual decompiled source code.

{context}

Example Type: {example_type.value}
Scenario: {template.get('scenario', 'general')}
Complexity Level: {complexity}
Target Instruction: {instruction}

CRITICAL REQUIREMENTS:
1. Use ONLY authentic function names, signatures, and patterns from the OoT decompilation
2. Include proper memory offsets, struct definitions, and field names as shown above
3. Use correct actor categories (ACTORCAT_MISC, ACTORCAT_NPC, etc.)
4. Follow authentic coding patterns including proper collision setup, action functions, etc.
5. Include realistic debugging scenarios and validation checks
6. Use PlayState* instead of GlobalContext*, world.pos instead of pos, etc.

Output Format:
```json
{{
    "instruction": "The user's request or question (use the target instruction above)",
    "input": "Any input code or context (null if not applicable)", 
    "output": "Complete, helpful response with authentic code examples and explanations",
    "technical_notes": "Brief notes about authenticity and implementation details"
}}
```

Generate 1 example now following the target instruction exactly:
"""

        # Add type-specific guidance with authentic context
        if example_type == ExampleType.CODE_EXPLANATION:
            base_prompt += """
Focus on: Explaining authentic OoT functions from the decompilation, their exact parameters, return values, and how they integrate with the actor system. Use real function signatures and memory layouts.
"""
        elif example_type == ExampleType.FEATURE_IMPLEMENTATION:
            base_prompt += """
Focus on: Complete implementations using authentic OoT patterns including proper ActorProfile setup, collision initialization, action functions, and update/draw patterns from real actors.
"""
        elif example_type == ExampleType.DEBUGGING_HELP:
            base_prompt += """
Focus on: Real crash scenarios from OoT development, authentic validation patterns, memory checking, and debugging techniques used in the actual codebase.
"""
        elif example_type == ExampleType.ACTOR_CREATION:
            base_prompt += """
Focus on: Complete actor creation following authentic patterns from EnItem00 and other real actors, including proper struct layout, initialization, and lifecycle management.
"""
        
        return base_prompt

    def _call_claude(self, prompt: str, max_retries: int = 3) -> str:
        """Make API call to Claude with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                # Handle different types of content blocks
                content_block = response.content[0]
                if content_block.type == 'text':
                    return content_block.text
                else:
                    return str(content_block)
            except Exception as e:
                print(f"API call failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        return ""

    def _parse_generated_example(self, raw_response: str, example_type: ExampleType) -> Optional[TrainingExample]:
        """Parse Claude's response into a TrainingExample object using multiple robust parsing strategies"""
        import re
        
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
                    metadata={"technical_notes": data.get("technical_notes", "")},
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
            r'"instruction":\s*([^,}]+)',  # Unquoted content until comma or brace
        ]
        
        output_patterns = [
            r'"output":\s*"([^"]+)"',  # Standard quoted string
            r'"output":\s*"([^"]*(?:\\.[^"]*)*)"',  # Handle escaped quotes
            r'"output":\s*```([^`]+)```',  # Unescaped code block
            r'"output":\s*```c\s*([^`]+)```',  # Specific C code block
            r'"output":\s*(.+?)(?=,\s*"[^"]*":|$)',  # Content until next field or end
        ]
        
        input_patterns = [
            r'"input":\s*(null|"[^"]*")',  # null or quoted string
            r'"input":\s*([^,}]+)',  # Any content until comma or brace
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
                # If this was a code block, add proper formatting
                if pattern.startswith(r'"output":\s*```'):
                    output = "```c\n" + output + "\n```"
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

    def _validate_and_refine_enhanced(self, example: TrainingExample) -> TrainingExample:
        """Enhanced validation using authentic OoT patterns and source validation"""
        
        # Layer 1: Authentic source code validation
        example = self._validate_authentic_patterns(example)
        
        # Layer 2: Technical accuracy validation with enhanced context
        example = self._validate_technical_accuracy_enhanced(example)
        
        # Layer 3: Final quality assessment
        example.quality_score = self._calculate_enhanced_quality_score(example)
        
        return example

    def _validate_authentic_patterns(self, example: TrainingExample) -> TrainingExample:
        """Validate against authentic OoT patterns and suggest corrections"""
        
        # Check for function usage
        func_issues = self.validator.validate_functions(example.output)
        if func_issues:
            example.validation_notes += f"Function validation issues: {len(func_issues)} unknown functions. "
        
        # Apply common corrections
        corrected_output = self.validator.suggest_corrections(example.output)
        if corrected_output != example.output:
            example.output = corrected_output
            example.validation_notes += "Applied authentic pattern corrections. "
        
        # Check for authentic struct usage
        authentic_structs = ["Actor", "PlayState", "ColliderCylinder", "ActorShape", "Vec3f", "Vec3s"]
        uses_authentic_structs = any(struct in example.output for struct in authentic_structs)
        if not uses_authentic_structs and "```c" in example.output:
            example.validation_notes += "Missing authentic struct usage. "
        
        # Check for modern function signatures
        if "PlayState* play" in example.output:
            example.validation_notes += "Uses correct PlayState signature. "
        elif "GlobalContext" in example.output:
            example.validation_notes += "Still uses outdated GlobalContext. "
        
        return example

    def _validate_technical_accuracy_enhanced(self, example: TrainingExample) -> TrainingExample:
        """Enhanced technical accuracy validation with authentic context"""
        
        validation_prompt = f"""
Review this OoT romhacking training example for technical accuracy against the AUTHENTIC decompiled source code:

Type: {example.example_type.value}
Instruction: {example.instruction}
Output: {example.output}

Validate against AUTHENTIC OoT patterns:
1. Function signatures match the actual decompilation (PlayState* not GlobalContext*, etc.)
2. Actor structure fields use correct offsets and names (world.pos not pos, etc.)
3. Collision setup follows authentic patterns (Collider_InitCylinder, etc.)
4. ActorProfile structure matches real examples (EnItem00, etc.)
5. Memory management and validation follows authentic patterns
6. Actor categories use correct ACTORCAT_ constants
7. Flag definitions match authentic values

Rate technical accuracy (1-10) and provide specific corrections:

Format:
```json
{{
    "accuracy_score": 8,
    "authentic_issues": ["List specific deviations from authentic patterns"],
    "corrections": "Specific corrections to match authentic OoT code",
    "is_valid": true
}}
```
"""
        
        validation_result = self._call_claude(validation_prompt)
        
        # Parse validation result and apply corrections
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', validation_result, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                
                if not data.get("is_valid", True):
                    example.validation_notes += "Authentic pattern validation failed. "
                
                # Apply corrections if provided
                if data.get("corrections") and data.get("authentic_issues"):
                    correction_prompt = f"""
Apply these authenticity corrections to improve the OoT training example:

Original Output: {example.output}
Issues Found: {', '.join(data.get('authentic_issues', []))}
Corrections Needed: {data.get('corrections')}

CRITICAL: Return ONLY the corrected output content. Do not add any commentary, explanations, or meta-text like "Here's the corrected..." or "The authentically corrected...". Start directly with the technical content.

Provide the corrected output that follows authentic OoT decompilation patterns:
"""
                    corrected_output = self._call_claude(correction_prompt)
                    if corrected_output.strip() and len(corrected_output) > 50:
                        example.output = corrected_output.strip()
                        example.validation_notes += "Applied authenticity corrections. "
                    
            except json.JSONDecodeError:
                example.validation_notes += "Validation parsing failed. "
        
        return example

    def _calculate_enhanced_quality_score(self, example: TrainingExample) -> float:
        """Calculate quality score with enhanced criteria for authentic OoT patterns"""
        score = 5.0  # Base score
        
        # Instruction quality
        if len(example.instruction) > 10:
            score += 0.5
        if any(keyword in example.instruction.lower() for keyword in ['actor', 'oot', 'collision', 'function']):
            score += 0.5
        
        # Output quality and authenticity
        if len(example.output) > 100:
            score += 1.0
        if '```c' in example.output or '```' in example.output:
            score += 1.0
        
        # Authentic OoT patterns bonus
        authentic_indicators = [
            'PlayState* play', 'Actor* thisx', 'ColliderCylinder', 'Actor_UpdateBgCheckInfo',
            'ACTORCAT_', 'Actor_SetScale', 'ActorProfile', 'world.pos', 'Actor_SpawnAsChild'
        ]
        authenticity_score = sum(1 for indicator in authentic_indicators if indicator in example.output)
        score += min(authenticity_score * 0.3, 2.0)  # Cap at +2.0 for authenticity
        
        # Function accuracy bonus
        if any(func in example.output for func in self.validator.known_functions):
            score += 1.0
        
        # Structure accuracy bonus  
        if any(struct_type in example.output for struct_type in self.validator.known_types):
            score += 0.5
        
        # Validation penalties
        if "unknown functions" in example.validation_notes:
            score -= 1.0
        if "validation failed" in example.validation_notes:
            score -= 1.5
        if "outdated" in example.validation_notes:
            score -= 0.5
            
        # Authenticity bonuses
        if "authentic pattern corrections" in example.validation_notes:
            score += 0.5
        if "correct PlayState signature" in example.validation_notes:
            score += 0.5
            
        return max(0.0, min(10.0, score))

    def generate_dataset(self, num_examples: int = 100, output_file: str = "oot_training_data.jsonl") -> None:
        """Generate a complete dataset of training examples"""
        
        examples = []
        example_types = list(ExampleType)
        complexities = ["simple", "intermediate", "advanced"]
        
        print(f"Generating {num_examples} training examples...")
        
        for i in range(num_examples):
            # Distribute examples across types and complexities
            example_type = example_types[i % len(example_types)]
            complexity = complexities[i % len(complexities)]
            
            print(f"Generating example {i+1}/{num_examples}: {example_type.value} ({complexity})")
            
            try:
                example = self.generate_training_example(example_type, complexity)
                
                if example.quality_score >= 6.0:  # Only keep high-quality examples
                    examples.append(example)
                    print(f"  ✓ Quality score: {example.quality_score:.1f}")
                else:
                    print(f"  ✗ Low quality score: {example.quality_score:.1f}, skipping")
                    
            except Exception as e:
                print(f"  ✗ Error generating example: {e}")
                
            # Rate limiting
            time.sleep(1)
        
        # Save to file
        self._save_dataset(examples, output_file)
        print(f"\nGenerated {len(examples)} high-quality examples")
        print(f"Saved to: {output_file}")

    def _save_dataset(self, examples: List[TrainingExample], output_file: str) -> None:
        """Save dataset in multiple formats"""
        
        # JSONL format for training
        with open(output_file, 'w') as f:
            for example in examples:
                training_record = {
                    "instruction": example.instruction,
                    "output": example.output
                }
                if example.input:
                    training_record["input"] = example.input
                    
                f.write(json.dumps(training_record) + '\n')
        
        # Detailed metadata file
        metadata_file = output_file.replace('.jsonl', '_metadata.json')
        with open(metadata_file, 'w') as f:
            metadata = {
                "total_examples": len(examples),
                "average_quality": sum(e.quality_score for e in examples) / len(examples) if examples else 0,
                "type_distribution": {t.value: sum(1 for e in examples if e.example_type == t) for t in ExampleType},
                "examples": [
                    {
                        "type": e.example_type.value,
                        "quality_score": e.quality_score,
                        "validation_notes": e.validation_notes,
                        "metadata": e.metadata
                    } for e in examples
                ]
            }
            json.dump(metadata, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Generate OoT romhacking training data")
    parser.add_argument("--api-key", required=True, help="Anthropic API key")
    parser.add_argument("--num-examples", type=int, default=50, help="Number of examples to generate")
    parser.add_argument("--output", default="oot_training_data.jsonl", help="Output file path")
    parser.add_argument("--model", default="claude-3-5-sonnet-20241022", help="Claude model to use")
    
    args = parser.parse_args()
    
    if not args.api_key:
        print("Error: Anthropic API key is required")
        sys.exit(1)
    
    generator = OoTTrainingDataGenerator(args.api_key, args.model)
    generator.generate_dataset(args.num_examples, args.output)

if __name__ == "__main__":
    main()