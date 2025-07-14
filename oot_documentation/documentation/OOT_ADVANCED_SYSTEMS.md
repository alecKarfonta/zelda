# OOT Advanced Systems Deep Dive

## Overview

This document provides a comprehensive analysis of the advanced systems in The Legend of Zelda: Ocarina of Time (OOT), covering physics simulation, AI behavior, effects rendering, and debug tools. These systems work together to create the game's dynamic, interactive world with intelligent enemies and rich visual feedback.

## Physics System

The physics system in OOT handles collision detection, movement, gravity, and physical interactions between actors. It's built around a sophisticated collision detection framework that supports multiple collision types.

### Core Physics Architecture

**Physics Update Loop (`z_actor.c:990`):**
```c
void Actor_UpdateVelocityXZGravity(Actor* actor) {
    actor->velocity.x = actor->speed * Math_SinS(actor->world.rot.y);
    actor->velocity.z = actor->speed * Math_CosS(actor->world.rot.y);

    actor->velocity.y += actor->gravity;

    if (actor->velocity.y < actor->minVelocityY) {
        actor->velocity.y = actor->minVelocityY;
    }
}
```

**Position Update (`z_actor.c:979`):**
```c
void Actor_UpdatePos(Actor* actor) {
    f32 speedRate = R_UPDATE_RATE * 0.5f;

    actor->world.pos.x += (actor->velocity.x * speedRate) + actor->colChkInfo.displacement.x;
    actor->world.pos.y += (actor->velocity.y * speedRate) + actor->colChkInfo.displacement.y;
    actor->world.pos.z += (actor->velocity.z * speedRate) + actor->colChkInfo.displacement.z;
}
```

**Integrated Movement (`z_actor.c:1006`):**
```c
void Actor_MoveXZGravity(Actor* actor) {
    Actor_UpdateVelocityXZGravity(actor);
    Actor_UpdatePos(actor);
}
```

### Collision Detection System

The collision system uses multiple collider types for different interaction scenarios:

**Collider Types:**
- **JntSph**: Joint spheres for complex animated objects
- **Cylinder**: Simple cylinder collision for basic objects
- **Quad**: Quad collision for sword attacks and shields
- **Tris**: Triangle collision for complex surfaces
- **Line**: Line collision for sight lines and projectiles

**Collision Categories:**
- **AT (Attack)**: Damage-dealing colliders
- **AC (Attack Checker)**: Damage-receiving colliders  
- **OC (Object Collision)**: Physical pushing/blocking colliders

### Mass and Physics Interactions

**Mass-Based Collision Response (`z_collision_check.c:2730`):**
```c
void CollisionCheck_SetOCvsOC(Collider* leftCol, ColliderElement* leftElem, Vec3f* leftPos, 
                              Collider* rightCol, ColliderElement* rightElem, Vec3f* rightPos, f32 overlap) {
    Actor* leftActor = leftCol->actor;
    Actor* rightActor = rightCol->actor;
    f32 leftMass = leftActor->colChkInfo.mass;
    f32 rightMass = rightActor->colChkInfo.mass;
    f32 totalMass = leftMass + rightMass;
    
    // Calculate displacement based on mass ratio
    if (leftMassType == MASSTYPE_IMMOVABLE) {
        leftDispRatio = 0;
        rightDispRatio = 1;
    } else if (rightMassType == MASSTYPE_IMMOVABLE) {
        leftDispRatio = 1;
        rightDispRatio = 0;
    } else {
        inverseTotalMass = 1.0f / totalMass;
        leftDispRatio = rightMass * inverseTotalMass;
        rightDispRatio = leftMass * inverseTotalMass;
    }
    
    // Apply displacement
    leftActor->colChkInfo.displacement.x += xDelta * leftDispRatio;
    leftActor->colChkInfo.displacement.z += zDelta * leftDispRatio;
    rightActor->colChkInfo.displacement.x += xDelta * rightDispRatio;
    rightActor->colChkInfo.displacement.z += zDelta * rightDispRatio;
}
```

**Mass Types:**
```c
typedef enum ColChkMassType {
    /* 0 */ MASSTYPE_IMMOVABLE,
    /* 1 */ MASSTYPE_HEAVY,
    /* 2 */ MASSTYPE_NORMAL
} ColChkMassType;
```

### Specialized Movement Functions

**3D Movement (`z_actor.c:1010`):**
```c
void Actor_UpdateVelocityXYZ(Actor* actor) {
    f32 speedXZ = actor->speed * Math_CosS(actor->world.rot.x);

    actor->velocity.x = speedXZ * Math_SinS(actor->world.rot.y);
    actor->velocity.y = actor->speed * Math_SinS(actor->world.rot.x);
    actor->velocity.z = speedXZ * Math_CosS(actor->world.rot.y);
}
```

**Projectile Physics (`z_actor.c:1030`):**
```c
void Actor_SetProjectileSpeed(Actor* actor, f32 speedXYZ) {
    actor->speed = speedXYZ * Math_CosS(actor->world.rot.x);
    actor->velocity.y = speedXYZ * -Math_SinS(actor->world.rot.x);
}
```

### Background Collision Integration

**Background Check Update (`z_actor.c:1430`):**
```c
void Actor_UpdateBgCheckInfo(PlayState* play, Actor* actor, f32 wallCheckHeight, 
                             f32 wallCheckRadius, f32 ceilingCheckHeight, s32 flags) {
    // Wall collision check
    if (flags & UPDBGCHECKINFO_FLAG_2) {
        actor->bgCheckFlags &= ~BGCHECKFLAG_WALL;
        if (BgCheck_EntitySphVsWall3(...)) {
            actor->bgCheckFlags |= BGCHECKFLAG_WALL;
        }
    }
    
    // Floor collision check
    if (flags & UPDBGCHECKINFO_FLAG_0) {
        actor->world.pos.y += 1.0f;
        actor->floorHeight = BgCheck_EntityRaycastFloor5(...);
        if (actor->world.pos.y <= actor->floorHeight) {
            actor->world.pos.y = actor->floorHeight;
            actor->bgCheckFlags |= BGCHECKFLAG_GROUND;
        }
    }
    
    // Ceiling collision check
    if (flags & UPDBGCHECKINFO_FLAG_1) {
        actor->ceilingHeight = BgCheck_EntityRaycastCeiling(...);
        if (actor->world.pos.y >= actor->ceilingHeight) {
            actor->world.pos.y = actor->ceilingHeight;
            actor->bgCheckFlags |= BGCHECKFLAG_CEILING;
        }
    }
}
```

## AI System

The AI system in OOT provides intelligent behavior for enemies and NPCs through state machines, pathfinding, and attention systems.

### State Machine Architecture

Most AI actors use function pointer-based state machines:

**State Machine Example (`ovl_En_Mb/z_en_mb.c`):**
```c
typedef struct EnMb {
    Actor actor;
    SkelAnime skelAnime;
    EnMbState state;
    EnMbActionFunc actionFunc;  // Current state function
    s16 timer1;
    s16 timer2;
    s16 timer3;
    f32 maxHomeDist;
    f32 playerDetectionRange;
    Vec3f waypointPos;
    s8 waypoint;
    s8 path;
    s8 direction;
    // ... collision and other data
} EnMb;
```

**State Transitions:**
```c
void EnMb_SetupWalk(EnMb* this) {
    this->state = ENMB_STATE_WALK;
    this->actionFunc = EnMb_Walk;
    this->timer1 = 0;
    Animation_ChangeByInfo(&this->skelAnime, sWalkAnimation, 0);
}

void EnMb_Walk(EnMb* this, PlayState* play) {
    // Walking behavior logic
    if (this->actor.xzDistToPlayer < this->playerDetectionRange) {
        EnMb_SetupAttack(this);
    } else if (/* reached waypoint */) {
        EnMb_SetupIdle(this);
    }
}
```

### Pathfinding System

**Basic Path Following (`ovl_En_Heishi1/z_en_heishi1.c:165`):**
```c
void EnHeishi1_Walk(EnHeishi1* this, PlayState* play) {
    Path* path = &play->pathList[this->path];
    Vec3s* pointPos = SEGMENTED_TO_VIRTUAL(path->points);
    pointPos += this->waypoint;
    
    // Calculate direction to waypoint
    f32 pathDiffX = pointPos->x - this->actor.world.pos.x;
    f32 pathDiffZ = pointPos->z - this->actor.world.pos.z;
    
    // Move towards waypoint
    Math_ApproachF(&this->actor.world.pos.x, pointPos->x, 1.0f, this->moveSpeed);
    Math_ApproachF(&this->actor.world.pos.z, pointPos->z, 1.0f, this->moveSpeed);
    
    // Update rotation to face movement direction
    Math_SmoothStepToS(&this->actor.shape.rot.y, 
                       RAD_TO_BINANG(Math_FAtan2F(pathDiffX, pathDiffZ)), 
                       3, this->bodyTurnSpeed, 0);
    
    // Check if reached waypoint
    if (Math_Vec3f_DistXZ(&this->actor.world.pos, (Vec3f*)pointPos) < 20.0f) {
        this->waypoint = (this->waypoint + 1) % path->count;
    }
}
```

**Advanced Path Following with Waypoint Selection (`ovl_En_Niw/z_en_niw.c:614`):**
```c
void func_80AB6A38(EnNiw* this, PlayState* play) {
    if (this->path == 0) {
        // Reset to idle position
        this->unk_2AC = this->actor.world.pos;
        this->actionFunc = EnNiw_ResetAction;
    } else {
        Path* path = &play->pathList[this->path - 1];
        Vec3s* pointPos = SEGMENTED_TO_VIRTUAL(path->points);
        pointPos += this->waypoint;
        
        f32 pathDiffX = pointPos->x - this->actor.world.pos.x;
        f32 pathDiffZ = pointPos->z - this->actor.world.pos.z;
        
        this->unk_2E4 = RAD_TO_BINANG(Math_FAtan2F(pathDiffX, pathDiffZ));
        
        // Check if close enough to waypoint
        if (fabsf(pathDiffX) < 30.0f && fabsf(pathDiffZ) < 30.0f) {
            this->waypoint++;
            if (this->waypoint >= this->unk_2EC) {
                this->waypoint = 0;  // Loop back to start
            }
        }
    }
}
```

### Attention and Targeting System

**Attention System (`z_actor.c:3417`):**
```c
void Attention_FindActorInCategory(PlayState* play, ActorContext* actorCtx, 
                                   Player* player, u32 actorCategory) {
    Actor* actor = actorCtx->actorLists[actorCategory].head;
    
    while (actor != NULL) {
        if (actor->update != NULL && actor != &player->actor && 
            (actor->flags & ACTOR_FLAG_ATTENTION_ENABLED)) {
            
            // Check if actor is within attention range
            f32 distSq = Math_Vec3f_DistXYZSq(&actor->world.pos, &player->actor.world.pos);
            if (distSq < sNearestAttentionActorDistSq) {
                
                // Check if actor is roughly on screen
                if (Attention_ActorOnScreen(play, actor)) {
                    
                    // Check if not blocked by collision
                    if (!CollisionCheck_LineOCCheckAll(play, &play->colChkCtx, 
                                                       &player->actor.world.pos, 
                                                       &actor->world.pos)) {
                        sNearestAttentionActor = actor;
                        sNearestAttentionActorDistSq = distSq;
                    }
                }
            }
        }
        actor = actor->next;
    }
}
```

**Distance-Based Behavior (`ovl_En_Dog/z_en_dog.c:364`):**
```c
void EnDog_FollowPlayer(EnDog* this, PlayState* play) {
    f32 speedXZ;
    
    if (this->actor.xzDistToPlayer > 400.0f) {
        // Too far - stop following
        this->nextBehavior = DOG_BOW;
        gSaveContext.dogParams = 0;
        speedXZ = 0.0f;
    } else if (this->actor.xzDistToPlayer > 100.0f) {
        // Far - run to catch up
        this->nextBehavior = DOG_RUN;
        speedXZ = 4.0f;
    } else if (this->actor.xzDistToPlayer < 40.0f) {
        // Close - bow/idle
        this->nextBehavior = DOG_BOW;
        speedXZ = 0.0f;
    } else {
        // Medium distance - walk
        this->nextBehavior = DOG_WALK;
        speedXZ = 1.0f;
    }
    
    Math_ApproachF(&this->actor.speed, speedXZ, 0.6f, 1.0f);
    
    // Face player
    Math_SmoothStepToS(&this->actor.world.rot.y, this->actor.yawTowardsPlayer, 
                       10, 1000, 1);
    this->actor.shape.rot = this->actor.world.rot;
}
```

### Enemy AI Patterns

**Aggressive AI (`ovl_En_Mb/z_en_mb.c`):**
```c
void EnMb_ChasePlayer(EnMb* this, PlayState* play) {
    Player* player = GET_PLAYER(play);
    
    // Update detection range based on alert state
    if (this->alertLevel > 0) {
        this->playerDetectionRange = 300.0f;
    } else {
        this->playerDetectionRange = 150.0f;
    }
    
    // Check if player is within detection range
    if (this->actor.xzDistToPlayer < this->playerDetectionRange) {
        // Face player
        Math_SmoothStepToS(&this->actor.world.rot.y, this->actor.yawTowardsPlayer, 
                           5, 1000, 0);
        
        // Move towards player
        Math_ApproachF(&this->actor.speed, 3.0f, 0.2f, 0.5f);
        
        // Check attack range
        if (this->actor.xzDistToPlayer < 80.0f) {
            EnMb_SetupAttack(this);
        }
    } else {
        // Lost player - return to patrol
        EnMb_SetupReturnToPatrol(this);
    }
}
```

**Defensive AI (`ovl_En_Am/z_en_am.c`):**
```c
void EnAm_Cooldown(EnAm* this, PlayState* play) {
    Math_SmoothStepToF(&this->actor.speed, 0.0f, 0.1f, 0.5f, 0.0f);
    
    if (this->cooldownTimer > 0) {
        this->cooldownTimer--;
    } else {
        f32 distToHome = Math_Vec3f_DistXYZ(&this->actor.world.pos, &this->actor.home.pos);
        
        if (distToHome > 200.0f) {
            // Too far from home - return
            this->actionFunc = EnAm_RotateToHome;
        } else if (this->actor.xzDistToPlayer < 120.0f) {
            // Player still close - attack again
            this->actionFunc = EnAm_Lunge;
        } else {
            // Return to idle
            this->actionFunc = EnAm_Idle;
        }
    }
}
```

### NPC Interaction System

**NPC Dialogue Management (`z_actor.c:4229`):**
```c
s32 Npc_UpdateTalking(PlayState* play, Actor* actor, s16* talkState, f32 interactRange,
                      NpcGetTextIdFunc getTextId, NpcUpdateTalkStateFunc updateTalkState) {
    Player* player = GET_PLAYER(play);
    s32 talkResult = NPC_TALK_RESULT_NONE;
    
    switch (*talkState) {
        case NPC_TALK_STATE_IDLE:
            if (Actor_TalkOfferAccepted(actor, play)) {
                *talkState = NPC_TALK_STATE_TALKING;
                talkResult = NPC_TALK_RESULT_STARTED;
            } else if (Actor_IsFacingAndNearPlayer(actor, interactRange, 0x3000)) {
                u16 textId = getTextId(play, actor);
                Actor_OfferTalk(actor, play, interactRange);
            }
            break;
            
        case NPC_TALK_STATE_TALKING:
            if (Actor_TextboxIsClosing(actor, play)) {
                *talkState = NPC_TALK_STATE_IDLE;
                talkResult = NPC_TALK_RESULT_ENDED;
            }
            break;
    }
    
    updateTalkState(play, actor);
    return talkResult;
}
```

## Effects System

The effects system manages visual effects, particle systems, and special rendering effects throughout the game.

### Core Effects Architecture

**Effect Context (`z_effect.c`):**
```c
typedef struct EffectContext {
    PlayState* play;
    EffectSpark sparks[SPARK_COUNT];
    EffectBlure blures[BLURE_COUNT];
    EffectShieldParticle shieldParticles[SHIELD_PARTICLE_COUNT];
} EffectContext;

EffectContext sEffectContext;
```

**Effect Information Table:**
```c
EffectInfo sEffectInfoTable[] = {
    {
        sizeof(EffectSpark),
        EffectSpark_Init,
        EffectSpark_Destroy,
        EffectSpark_Update,
        EffectSpark_Draw,
    },
    {
        sizeof(EffectBlure),
        EffectBlure_Init1,
        EffectBlure_Destroy,
        EffectBlure_Update,
        EffectBlure_Draw,
    },
    // ... more effect types
};
```

### Effect Management

**Adding Effects (`z_effect.c:104`):**
```c
void Effect_Add(PlayState* play, s32* pIndex, s32 type, u8 arg3, u8 arg4, void* initParams) {
    s32 i;
    u32 slotFound = false;
    void* effect = NULL;
    EffectStatus* status = NULL;
    
    *pIndex = TOTAL_EFFECT_COUNT;
    
    // Find available slot based on effect type
    switch (type) {
        case EFFECT_SPARK:
            for (i = 0; i < SPARK_COUNT; i++) {
                if (!sEffectContext.sparks[i].status.active) {
                    effect = &sEffectContext.sparks[i].effect;
                    status = &sEffectContext.sparks[i].status;
                    *pIndex = i;
                    slotFound = true;
                    break;
                }
            }
            break;
            
        case EFFECT_BLURE1:
        case EFFECT_BLURE2:
            for (i = 0; i < BLURE_COUNT; i++) {
                if (!sEffectContext.blures[i].status.active) {
                    effect = &sEffectContext.blures[i].effect;
                    status = &sEffectContext.blures[i].status;
                    *pIndex = i + SPARK_COUNT;
                    slotFound = true;
                    break;
                }
            }
            break;
    }
    
    if (slotFound) {
        sEffectInfoTable[type].init(effect, initParams);
        status->active = true;
        status->unk_01 = arg4;
        status->unk_02 = arg3;
    }
}
```

**Effect Update Loop (`z_effect.c:190`):**
```c
void Effect_UpdateAll(PlayState* play) {
    s32 i;
    
    // Update spark effects
    for (i = 0; i < SPARK_COUNT; i++) {
        if (sEffectContext.sparks[i].status.active) {
            if (sEffectInfoTable[EFFECT_SPARK].update(&sEffectContext.sparks[i].effect) == 1) {
                Effect_Delete(play, i);
            }
        }
    }
    
    // Update blur effects
    for (i = 0; i < BLURE_COUNT; i++) {
        if (sEffectContext.blures[i].status.active) {
            if (sEffectInfoTable[EFFECT_BLURE1].update(&sEffectContext.blures[i].effect) == 1) {
                Effect_Delete(play, i + SPARK_COUNT);
            }
        }
    }
}
```

### Actor-Specific Effects

**Boss Effects (`ovl_Boss_Tw/z_boss_tw.c:4551`):**
```c
void BossTw_UpdateEffects(PlayState* play) {
    static Color_RGB8 sDotColors[] = {
        { 255, 128, 0 },   { 255, 0, 0 },     { 255, 255, 0 },   { 255, 0, 0 },
        { 100, 100, 100 }, { 255, 255, 255 }, { 150, 150, 150 }, { 255, 255, 255 },
    };
    
    BossTwEffect* eff = play->specialEffects;
    
    for (s16 i = 0; i < BOSS_TW_EFFECT_COUNT; i++) {
        if (eff->type != TWEFF_NONE) {
            // Update position
            eff->pos.x += eff->curSpeed.x;
            eff->pos.y += eff->curSpeed.y;
            eff->pos.z += eff->curSpeed.z;
            
            // Update frame counter
            eff->frame++;
            
            // Apply acceleration
            eff->curSpeed.x += eff->accel.x;
            eff->curSpeed.y += eff->accel.y;
            eff->curSpeed.z += eff->accel.z;
            
            // Animate color
            s16 colorIdx = eff->frame % 4;
            eff->color.r = sDotColors[colorIdx].r;
            eff->color.g = sDotColors[colorIdx].g;
            eff->color.b = sDotColors[colorIdx].b;
            
            // Update alpha
            eff->alpha -= 20;
            if (eff->alpha <= 0) {
                eff->alpha = 0;
                eff->type = TWEFF_NONE;
            }
        }
    }
}
```

**Particle Effects (`ovl_En_Fw/z_en_fw.c:445`):**
```c
void EnFw_UpdateEffects(EnFw* this) {
    EnFwEffect* eff = this->effects;
    
    for (s16 i = 0; i < EN_FW_EFFECT_COUNT; i++, eff++) {
        if (eff->type != 0) {
            if ((--eff->timer) == 0) {
                eff->type = 0;  // Deactivate effect
            }
            
            // Add randomness to movement
            eff->accel.x = (Rand_ZeroOne() * 0.4f) - 0.2f;
            eff->accel.z = (Rand_ZeroOne() * 0.4f) - 0.2f;
            
            // Update position
            eff->pos.x += eff->velocity.x;
            eff->pos.y += eff->velocity.y;
            eff->pos.z += eff->velocity.z;
            
            // Update velocity
            eff->velocity.x += eff->accel.x;
            eff->velocity.y += eff->accel.y;
            eff->velocity.z += eff->accel.z;
            
            // Update scale
            eff->scale += eff->scaleStep;
        }
    }
}
```

### Effect Rendering

**Effect Drawing (`ovl_Boss_Tw/z_boss_tw.c:4895`):**
```c
void BossTw_DrawEffects(PlayState* play) {
    GraphicsContext* gfxCtx = play->state.gfxCtx;
    BossTwEffect* currentEffect = play->specialEffects;
    u8 materialFlag = 0;
    
    OPEN_DISPS(gfxCtx, "../z_boss_tw.c", 9592);
    
    Gfx_SetupDL_25Xlu(play->state.gfxCtx);
    
    for (s16 i = 0; i < BOSS_TW_EFFECT_COUNT; i++) {
        if (currentEffect->type == TWEFF_DOT) {
            // Set material once for all dot effects
            if (materialFlag == 0) {
                gSPDisplayList(POLY_XLU_DISP++, gTwinrovaMagicParticleMaterialDL);
                materialFlag++;
            }
            
            // Set color
            gDPSetPrimColor(POLY_XLU_DISP++, 0, 0, 
                           currentEffect->color.r, currentEffect->color.g,
                           currentEffect->color.b, currentEffect->alpha);
            
            // Set position and scale
            Matrix_Translate(currentEffect->pos.x, currentEffect->pos.y, 
                           currentEffect->pos.z, MTXMODE_NEW);
            Matrix_ReplaceRotation(&play->billboardMtxF);
            Matrix_Scale(currentEffect->workf[EFF_SCALE], 
                        currentEffect->workf[EFF_SCALE], 1.0f, MTXMODE_APPLY);
            
            MATRIX_FINALIZE_AND_LOAD(POLY_XLU_DISP++, gfxCtx, "../z_boss_tw.c", 9617);
            gSPDisplayList(POLY_XLU_DISP++, gTwinrovaMagicParticleModelDL);
        }
        currentEffect++;
    }
    
    CLOSE_DISPS(gfxCtx, "../z_boss_tw.c", 9946);
}
```

## Debug Tools

OOT includes comprehensive debug tools for development and testing, including crash handling, debug display, and register editing.

### Debug Display System

**Debug Text Drawing (`z_debug.c:127`):**
```c
void DebugCamera_ScreenTextColored(u8 x, u8 y, u8 colorIndex, const char* text) {
    DebugCamTextBufferEntry* entry = &sDebugCamTextBuffer[sDebugCamTextEntryCount];
    
    if (sDebugCamTextEntryCount < ARRAY_COUNT(sDebugCamTextBuffer)) {
        entry->x = x;
        entry->y = y;
        entry->colorIndex = colorIndex;
        
        // Copy text with bounds checking
        char* textDest = entry->text;
        s16 charCount = 0;
        
        while ((*textDest++ = *text++) != '\0') {
            if (charCount++ > (ARRAY_COUNT(entry->text) - 1)) {
                break;
            }
        }
        *textDest = '\0';
        
        sDebugCamTextEntryCount++;
    }
}
```

**Debug Text Rendering (`z_debug.c:154`):**
```c
void DebugCamera_DrawScreenText(GfxPrint* printer) {
    for (s32 i = 0; i < sDebugCamTextEntryCount; i++) {
        DebugCamTextBufferEntry* entry = &sDebugCamTextBuffer[i];
        Color_RGBA8* color = &sDebugCamTextColors[entry->colorIndex];
        
        GfxPrint_SetColor(printer, color->r, color->g, color->b, color->a);
        GfxPrint_SetPos(printer, entry->x, entry->y);
        GfxPrint_Printf(printer, "%s", entry->text);
    }
}
```

### Register Editor

**Register Editor Update (`z_debug.c:177`):**
```c
void Regs_UpdateEditor(Input* input) {
    s32 dPadInputCur = input->cur.button & (BTN_DUP | BTN_DDOWN | BTN_DLEFT | BTN_DRIGHT);
    s32 pageDataStart = ((gRegEditor->regGroup * REG_PAGES) + gRegEditor->regPage - 1) * REGS_PER_PAGE;
    
    // Handle input repeat timing
    if (dPadInputCur != 0) {
        if (gRegEditor->inputRepeatTimer >= 16) {
            gRegEditor->inputRepeatTimer = 14;
        } else {
            gRegEditor->inputRepeatTimer++;
        }
    } else {
        gRegEditor->inputRepeatTimer = 0;
    }
    
    // Process input if not repeating too fast
    if (gRegEditor->inputRepeatTimer < 16) {
        
        // Navigate between registers
        if (CHECK_BTN_ALL(input->press.button, BTN_DDOWN)) {
            gRegEditor->regCur = (gRegEditor->regCur + 1) % REGS_PER_PAGE;
        }
        if (CHECK_BTN_ALL(input->press.button, BTN_DUP)) {
            gRegEditor->regCur = (gRegEditor->regCur - 1 + REGS_PER_PAGE) % REGS_PER_PAGE;
        }
        
        // Modify register values
        if (CHECK_BTN_ALL(input->press.button, BTN_DRIGHT)) {
            gRegEditor->data[pageDataStart + gRegEditor->regCur]++;
        }
        if (CHECK_BTN_ALL(input->press.button, BTN_DLEFT)) {
            gRegEditor->data[pageDataStart + gRegEditor->regCur]--;
        }
    }
}
```

### Debug Camera

**Debug Camera System (`db_camera.c:1014`):**
```c
void DebugCamera_Update(DebugCam* debugCam, Camera* cam) {
    if (CHECK_BTN_ALL(sPlay->state.input[DEBUG_CAM_CONTROLLER_PORT].press.button, BTN_Z)) {
        debugCam->unk_00++;
        debugCam->unk_00 %= 3;
        debugCam->unk_38 = 1;
        debugCam->unk_44 = 0;
        debugCam->unk_40 = -1;
        debugCam->sub.demoCtrlActionIdx = 0;
        SFX_PLAY_CENTERED(NA_SE_SY_LOCK_ON);
    }
    
    // Free camera controls
    if (debugCam->unk_00 == 2) {
        // Move camera with analog stick
        Vec3f moveVector;
        moveVector.x = sPlay->state.input[DEBUG_CAM_CONTROLLER_PORT].cur.stick_x * 0.1f;
        moveVector.y = 0.0f;
        moveVector.z = sPlay->state.input[DEBUG_CAM_CONTROLLER_PORT].cur.stick_y * 0.1f;
        
        // Apply movement relative to camera orientation
        Matrix_RotateY(debugCam->sub.unk_104A.y, MTXMODE_NEW);
        Matrix_MultVec3f(&moveVector, &moveVector);
        
        debugCam->eye.x += moveVector.x;
        debugCam->eye.y += moveVector.y;
        debugCam->eye.z += moveVector.z;
    }
    
    // Update camera
    cam->eye = debugCam->eye;
    cam->at = debugCam->at;
    cam->up = debugCam->unk_1C;
    cam->fov = debugCam->fov;
    cam->roll = debugCam->roll;
}
```

### Crash Handler

**Fault Handler (`fault_gc.c:1230`):**
```c
void Fault_PadCallback(Input* input) {
    if (sFaultInstance->faultHandlerEnabled) {
        while (!sFaultInstance->faultHandlerEnabled) {
            Fault_Sleep(1000);
        }
        Fault_Sleep(1000 / 2);
        
        // Display fault framebuffer
        Fault_DisplayFrameBuffer();
        
        if (sFaultInstance->autoScroll) {
            Fault_Wait5Seconds();
        } else {
            // Draw red corner indicating crash screen available
            Fault_DrawCornerRec(GPACK_RGBA5551(255, 0, 0, 1));
            Fault_WaitForButtonCombo();
        }
        
        // Draw crash info pages
        do {
            // Thread context page
            Fault_PrintThreadContext(faultedThread);
            Fault_LogThreadContext(faultedThread);
            Fault_WaitForInput();
            
            // Stack trace page
            Fault_FillScreenBlack();
            Fault_DrawText(120, 16, "STACK TRACE");
            Fault_DrawStackTrace(faultedThread, 36, 24, 22);
            Fault_LogStackTrace(faultedThread, 50);
            Fault_WaitForInput();
            
            // Memory dump page
            Fault_DrawMemDump(faultedThread->context.pc - 0x100, 
                             (uintptr_t)faultedThread->context.sp, 0, 0);
            Fault_WaitForInput();
            
        } while (!sFaultInstance->exit);
    }
}
```

### Audio Debug Tools

**Audio Debug Display (`audio/game/debug.inc.c:122`):**
```c
void AudioDebug_Draw(GfxPrint* printer) {
    u8 numEnabledNotes = 0;
    
    // Count active notes
    for (s32 i = 0; i < gAudioSpecs[gAudioSpecId].numNotes; i++) {
        if (gAudioCtx.notes[i].noteSubEu.bitField0.enabled == 1) {
            numEnabledNotes++;
        }
    }
    
    // Update peak note count
    if (sPeakNumNotes < numEnabledNotes) {
        sPeakNumNotes = numEnabledNotes;
    }
    
    // Draw debug info
    GfxPrint_SetPos(printer, 3, 2);
    GfxPrint_SetColor(printer, 255, 255, 255, 255);
    GfxPrint_Printf(printer, "Audio Debug Mode");
    
    GfxPrint_SetPos(printer, 3, 3);
    GfxPrint_Printf(printer, "- %s -", sAudioDebugPageNames[sAudioDebugPage]);
    
    GfxPrint_SetPos(printer, 3, 5);
    GfxPrint_Printf(printer, "Notes: %d/%d (Peak: %d)", 
                   numEnabledNotes, gAudioSpecs[gAudioSpecId].numNotes, sPeakNumNotes);
}
```

## System Integration

### Physics Integration with AI

**AI with Physics (`ovl_En_Peehat/z_en_peehat.c:938`):**
```c
void EnPeehat_Update(Actor* thisx, PlayState* play) {
    EnPeehat* this = (EnPeehat*)thisx;
    
    // Collision check for adult peahats
    if (thisx->params <= 0) {
        EnPeehat_Adult_CollisionCheck(this, play);
    }
    
    // Physics update
    if (thisx->speed != 0.0f || thisx->velocity.y != 0.0f) {
        Actor_MoveXZGravity(thisx);
        Actor_UpdateBgCheckInfo(play, thisx, 25.0f, 30.0f, 30.0f, 
                               UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2);
    }
    
    // AI behavior
    this->actionFunc(this, play);
    
    // Update focus point for targeting
    if (thisx->params < 0) {
        thisx->focus.pos.x = this->colliderJntSph.elements[0].dim.worldSphere.center.x;
        thisx->focus.pos.y = this->colliderJntSph.elements[0].dim.worldSphere.center.y;
        thisx->focus.pos.z = this->colliderJntSph.elements[0].dim.worldSphere.center.z;
    }
}
```

### Effects Integration with Gameplay

**Effect Spawning from Collisions (`z_collision_check.c:1556`):**
```c
void CollisionCheck_RedBlood(PlayState* play, Collider* collider, Vec3f* v) {
    static Color_RGBA8 bloodPrimColor = { 128, 0, 64, 255 };
    static Color_RGBA8 bloodEnvColor = { 128, 0, 64, 255 };
    
    EffectSsGSpk_SpawnFuse(play, &collider->actor->world.pos, &gZeroVec3f, &gZeroVec3f,
                           &bloodPrimColor, &bloodEnvColor, 400, 40, 0);
    CollisionCheck_SpawnRedBlood(play, v);
}
```

## Performance Considerations

### Physics Optimization

**Collision Culling:**
- Uses spatial partitioning to reduce collision checks
- Implements early-out tests for obviously separated objects
- Caches collision results where possible

**Movement Optimization:**
- Separates XZ movement from Y movement for efficiency
- Uses fast approximation functions for common calculations
- Batches similar physics operations together

### AI Optimization

**State Machine Efficiency:**
- Uses function pointers instead of switch statements
- Minimizes state transition overhead
- Caches frequently used calculations

**Pathfinding Performance:**
- Uses simple waypoint-based pathfinding instead of complex algorithms
- Limits pathfinding updates to every few frames
- Uses distance-based level-of-detail for AI processing

### Effects Performance

**Effect Pooling:**
- Pre-allocates fixed-size effect pools
- Reuses effect instances to avoid allocation overhead
- Limits maximum number of active effects

**Rendering Optimization:**
- Batches similar effects together
- Uses billboarding for orientation-independent effects
- Implements distance-based culling for small effects

## Conclusion

The advanced systems in OOT demonstrate sophisticated game programming techniques that were cutting-edge for the N64 era. The physics system provides realistic movement and interactions, the AI system creates believable enemy and NPC behavior, the effects system adds visual polish and feedback, and the debug tools enable rapid development and testing.

These systems work together seamlessly to create the rich, interactive world that made OOT a landmark achievement in 3D gaming. Understanding these systems provides insights into both historical game development practices and timeless principles of game architecture that remain relevant today.

The modular design and clear separation of concerns make these systems excellent examples for studying game engine architecture, while the extensive debug tools demonstrate the importance of developer productivity in creating complex games. 