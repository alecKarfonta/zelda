# OOT AI System Deep Dive

## Overview

This document provides a comprehensive analysis of the AI system in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code in the `oot/src` folder. The AI system encompasses enemy behavior, pathfinding, detection systems, NPC interactions, and dynamic state management. These systems work together to create intelligent, responsive actors that provide engaging gameplay challenges and believable world interactions.

## AI System Architecture

### Core AI Components

The OOT AI system consists of several interconnected subsystems:

1. **State Machine Architecture** - Function pointer-based state systems for all actors
2. **Pathfinding and Navigation** - Waypoint-based movement and goal-directed navigation
3. **Detection and Perception** - Vision, proximity, and line-of-sight systems
4. **Attention and Targeting** - Player focus and lock-on management
5. **Behavioral Controllers** - Complex multi-state AI patterns for different actor types

## State Machine Architecture

### Function Pointer State Systems

OOT uses a sophisticated function pointer-based state machine system that allows actors to dynamically switch between different behaviors.

**Base State Machine Pattern:**
```c
typedef void (*EnMbActionFunc)(struct EnMb*, struct PlayState*);

typedef struct EnMb {
    /* 0x0000 */ Actor actor;
    /* 0x0324 */ EnMbActionFunc actionFunc;
    /* 0x0320 */ EnMbState state;
    /* 0x032A */ s16 timer1;
    /* 0x032C */ s16 timer2;
    /* 0x032E */ s16 timer3;
    // ... other state variables
} EnMb; // Moblin actor structure
```

This pattern is used consistently across all intelligent actors, providing:
- **Dynamic Behavior Switching**: Function pointers allow instant state changes
- **State Persistence**: State variables maintain context between frames
- **Hierarchical States**: States can have sub-states and timers for complex behaviors

### Enemy State Machine Example - Iron Knuckle

**Iron Knuckle AI States (`z_en_ik.c:351`):**
```c
void EnIk_Idle(EnIk* this, PlayState* play) {
    s32 detectionThreshold = (this->armorStatusFlag == 0) ? 0xAAA : 0x3FFC;
    s16 yawDiff = this->actor.yawTowardsPlayer - this->actor.shape.rot.y;

    if ((ABS(yawDiff) <= detectionThreshold) && (this->actor.xzDistToPlayer < 100.0f) &&
        (ABS(this->actor.yDistToPlayer) < 150.0f)) {
        if ((play->gameplayFrames & 1)) {
            EnIk_SetupVerticalAttack(this);
        } else {
            EnIk_SetupDoubleHorizontalAttack(this);
        }
    } else if ((ABS(yawDiff) <= 0x4000) && (ABS(this->actor.yDistToPlayer) < 150.0f)) {
        EnIk_SetupWalkOrRun(this);
    } else {
        EnIk_SetupWalkOrRun(this);
    }

    EnIk_HandleBlocking(this, play);
    SkelAnime_Update(&this->skelAnime);
}
```

Key AI decision-making factors:
- **Armor Status**: Different detection thresholds based on armor state
- **Player Distance**: XZ and Y distance checks for attack/movement decisions
- **Facing Direction**: Yaw difference determines appropriate actions
- **Frame-Based Randomization**: Prevents predictable attack patterns

**State Transition Logic (`z_en_ik.c:390`):**
```c
void EnIk_WalkOrRun(EnIk* this, PlayState* play) {
    s16 temp_t0;
    s16 targetYaw;
    s16 yawDiff;
    s16 stepVal;

    if (this->armorStatusFlag == 0) {
        temp_t0 = 0xAAA;      // Narrow detection cone
        stepVal = 0x320;      // Slower turning
    } else {
        temp_t0 = 0x3FFC;     // Wide detection cone
        stepVal = 0x4B0;      // Faster turning
    }

    // Wall avoidance AI
    targetYaw = this->actor.wallYaw - this->actor.shape.rot.y;
    if ((this->actor.bgCheckFlags & BGCHECKFLAG_WALL) && (ABS(targetYaw) >= 0x4000)) {
        targetYaw = (this->actor.yawTowardsPlayer > 0) ? 
                    this->actor.wallYaw - 0x4000 : this->actor.wallYaw + 0x4000;
        Math_SmoothStepToS(&this->actor.world.rot.y, targetYaw, 1, stepVal, 0);
    } else {
        Math_SmoothStepToS(&this->actor.world.rot.y, this->actor.yawTowardsPlayer, 1, stepVal, 0);
    }

    // Attack distance check
    yawDiff = this->actor.yawTowardsPlayer - this->actor.shape.rot.y;
    if ((ABS(yawDiff) <= temp_t0) && (this->actor.xzDistToPlayer < 100.0f)) {
        if (ABS(this->actor.yDistToPlayer) < 150.0f) {
            if (play->gameplayFrames & 1) {
                EnIk_SetupVerticalAttack(this);
            } else {
                EnIk_SetupDoubleHorizontalAttack(this);
            }
        }
    }
}
```

This demonstrates sophisticated AI featuring:
- **Adaptive Behavior**: Different parameters based on internal state
- **Wall Avoidance**: Intelligent navigation around obstacles
- **Pursuit Logic**: Balanced following vs. attack decision-making
- **Attack Timing**: Frame-based randomization prevents exploitation

### Behavioral State Patterns

**Armos Statue AI States (`z_en_am.c:56`):**
```c
typedef enum ArmosBehavior {
    /* 00 */ AM_BEHAVIOR_NONE,
    /* 01 */ AM_BEHAVIOR_DAMAGED,
    /* 03 */ AM_BEHAVIOR_DO_NOTHING = 3,
    /* 05 */ AM_BEHAVIOR_5 = 5,
    /* 06 */ AM_BEHAVIOR_STUNNED,
    /* 07 */ AM_BEHAVIOR_GO_HOME,
    /* 08 */ AM_BEHAVIOR_RICOCHET,
    /* 10 */ AM_BEHAVIOR_AGGRO = 10
} ArmosBehavior;
```

Different enemy types use specialized state enums that reflect their unique behavioral patterns. This type-safe approach prevents invalid state transitions and makes AI debugging more tractable.

## Pathfinding and Navigation

### Waypoint-Based Navigation System

OOT implements a sophisticated waypoint-based pathfinding system using path data defined in each scene.

**Path Structure and Navigation (`z_path.c:23`):**
```c
f32 Path_OrientAndGetDistSq(Actor* actor, Path* path, s16 waypoint, s16* yaw) {
    f32 dx;
    f32 dz;
    Vec3s* pointPos;

    if (path == NULL) {
        return -1.0;
    }

    pointPos = SEGMENTED_TO_VIRTUAL(path->points);
    pointPos = &pointPos[waypoint];

    dx = pointPos->x - actor->world.pos.x;
    dz = pointPos->z - actor->world.pos.z;

    *yaw = RAD_TO_BINANG(Math_FAtan2F(dx, dz));

    return SQ(dx) + SQ(dz);
}
```

This utility function provides the foundation for all pathfinding by:
- **Direction Calculation**: Computing exact yaw needed to face target waypoint
- **Distance Measurement**: Returning squared distance for efficient comparisons
- **Null Safety**: Graceful handling of missing path data

### Dynamic Pathfinding Implementation

**NPC Pathfinding Example (`z_en_cs.c:294`):**
```c
s32 EnCs_HandleWalking(EnCs* this, PlayState* play) {
    f32 xDiff;
    f32 zDiff;
    Vec3f pathPos;
    s32 waypointCount;
    s16 walkAngle1;
    s16 walkAngle2;

    EnCs_GetPathPoint(play->pathList, &pathPos, this->path, this->waypoint);
    xDiff = pathPos.x - this->actor.world.pos.x;
    zDiff = pathPos.z - this->actor.world.pos.z;
    walkAngle1 = RAD_TO_BINANG(Math_FAtan2F(xDiff, zDiff));
    this->walkAngle = walkAngle1;
    this->walkDist = sqrtf((xDiff * xDiff) + (zDiff * zDiff));

    while (this->walkDist <= 10.44f) {
        this->waypoint++;
        waypointCount = EnCs_GetwaypointCount(play->pathList, this->path);

        if ((this->waypoint < 0) || (!(this->waypoint < waypointCount))) {
            this->waypoint = 0;  // Loop back to start
        }

        EnCs_GetPathPoint(play->pathList, &pathPos, this->path, this->waypoint);
        xDiff = pathPos.x - this->actor.world.pos.x;
        zDiff = pathPos.z - this->actor.world.pos.z;
        walkAngle2 = RAD_TO_BINANG(Math_FAtan2F(xDiff, zDiff));
        this->walkAngle = walkAngle2;
        this->walkDist = sqrtf((xDiff * xDiff) + (zDiff * zDiff));
    }

    Math_SmoothStepToS(&this->actor.shape.rot.y, this->walkAngle, 1, 2500, 0);
    this->actor.world.rot.y = this->actor.shape.rot.y;
    this->actor.speed = this->walkSpeed;
    Actor_MoveXZGravity(&this->actor);
    Actor_UpdateBgCheckInfo(play, &this->actor, 0.0f, 0.0f, 0.0f, UPDBGCHECKINFO_FLAG_2);

    return 0;
}
```

Advanced pathfinding features:
- **Lookahead Processing**: Handles multiple waypoints in a single frame if close
- **Smooth Turning**: Gradual rotation instead of instant snapping
- **Path Looping**: Automatic wraparound for patrol routes
- **Integrated Physics**: Combines pathfinding with collision detection

### Adaptive Navigation Systems

**Guard Patrol with Complex Waypoint Logic (`z_en_heishi1.c:165`):**
```c
void EnHeishi1_Walk(EnHeishi1* this, PlayState* play) {
    Path* path;
    Vec3s* pointPos;
    f32 pathDiffX;
    f32 pathDiffZ;
    s16 randOffset;

    if (!sPlayerIsCaught) {
        path = &play->pathList[this->path];
        pointPos = SEGMENTED_TO_VIRTUAL(path->points);
        pointPos += this->waypoint;

        Math_ApproachF(&this->actor.world.pos.x, pointPos->x, 1.0f, this->moveSpeed);
        Math_ApproachF(&this->actor.world.pos.z, pointPos->z, 1.0f, this->moveSpeed);

        Math_ApproachF(&this->moveSpeed, this->moveSpeedTarget, 1.0f, this->moveSpeedMax);

        pathDiffX = pointPos->x - this->actor.world.pos.x;
        pathDiffZ = pointPos->z - this->actor.world.pos.z;
        Math_SmoothStepToS(&this->actor.shape.rot.y, RAD_TO_BINANG(Math_FAtan2F(pathDiffX, pathDiffZ)), 3,
                           this->bodyTurnSpeed, 0);

        Math_ApproachF(&this->bodyTurnSpeed, this->bodyTurnSpeedTarget, 1.0f, this->bodyTurnSpeedMax);

        // Head movement behavior during walking
        if (this->headTimer == 0) {
            this->headDirection++;
            this->headAngleTarget = 0x2000;
            if ((this->headDirection & 1) != 0) {
                this->headAngleTarget *= -1;
            }
            randOffset = Rand_ZeroFloat(30.0f);
            this->headTimer = sBaseHeadTimers[this->type] + randOffset;
        }

        Math_ApproachF(&this->headAngle, this->headAngleTarget, this->headTurnSpeedScale, this->headTurnSpeedMax);
    }
}
```

This sophisticated guard patrol demonstrates:
- **Velocity Control**: Gradual acceleration/deceleration for natural movement
- **Body vs. Head Control**: Separate tracking for body and head rotation
- **Randomized Behavior**: Random timing for head movements
- **State-Dependent Logic**: Movement only when player not caught

## Detection and Perception Systems

### Vision and Proximity Detection

AI actors use multiple detection methods to create believable perception systems.

**Gerudo Guard Detection (`z_en_ge2.c:178`):**
```c
s32 Ge2_DetectPlayerInUpdate(PlayState* play, EnGe2* this, Vec3f* pos, s16 yRot, f32 yDetectRange) {
    Player* player = GET_PLAYER(play);
    Vec3f posResult;
    CollisionPoly* outPoly;
    f32 visionScale;

    visionScale = (!IS_DAY ? 0.75f : 1.5f);

    if ((250.0f * visionScale) < this->actor.xzDistToPlayer) {
        return 0;  // Too far away
    }

    if (yDetectRange < ABS(this->actor.yDistToPlayer)) {
        return 0;  // Wrong height
    }

    if (ABS((s16)(this->actor.yawTowardsPlayer - yRot)) > 0x2000) {
        return 0;  // Outside vision cone
    }

    if (BgCheck_AnyLineTest1(&play->colCtx, pos, &player->bodyPartsPos[PLAYER_BODYPART_HEAD], &posResult, &outPoly,
                             0)) {
        return 0;  // Line of sight blocked
    }
    return 1;
}
```

Sophisticated detection features:
- **Time-Based Vision**: Different detection ranges for day/night
- **3D Detection Volume**: XZ distance and Y height requirements
- **Directional Vision**: Angular field-of-view constraints
- **Line-of-Sight**: Ray casting to verify unobstructed vision

**Courtyard Guard Vision System (`z_en_heishi1.c:438`):**
```c
// Search ball creation for guard vision
Vec3f searchBallVel;
Vec3f searchBallAccel = { 0.0f, 0.0f, 0.0f };
Vec3f searchBallMult = { 0.0f, 0.0f, 20.0f };
Vec3f searchBallPos;

searchBallPos.x = this->actor.world.pos.x;
searchBallPos.y = this->actor.world.pos.y + 60.0f;
searchBallPos.z = this->actor.world.pos.z;

Matrix_Push();
Matrix_RotateY(BINANG_TO_RAD_ALT(this->actor.shape.rot.y + this->headAngle), MTXMODE_NEW);
searchBallMult.z = 30.0f;
Matrix_MultVec3f(&searchBallMult, &searchBallVel);
Matrix_Pop();

EffectSsSolderSrchBall_Spawn(play, &searchBallPos, &searchBallVel, &searchBallAccel, 2,
                             &this->linkDetected);

if (this->actor.xzDistToPlayer < 60.0f) {
    this->linkDetected = true;
} else if (this->actor.xzDistToPlayer < 70.0f) {
    if (player->actor.velocity.y > -4.0f) {
        this->linkDetected = true;  // Detect jump sounds
    }
}
```

This creates a visual effect system that:
- **Projects Vision**: Creates moving particles showing guard's line of sight
- **Multi-Range Detection**: Different detection distances for different behaviors
- **Audio Cues**: Detects player jumping sounds at intermediate range
- **Head Tracking Integration**: Vision follows guard's head movement

### Attention and Lock-On System

**Attention Actor Finding (`z_actor.c:3456`):**
```c
void Attention_FindActorInCategory(PlayState* play, ActorContext* actorCtx, Player* player, u32 actorCategory) {
    f32 distSq;
    Actor* actor;
    Actor* playerFocusActor;
    CollisionPoly* poly;
    s32 bgId;
    Vec3f lineTestResultPos;

    actor = actorCtx->actorLists[actorCategory].head;
    playerFocusActor = player->focusActor;

    while (actor != NULL) {
        if ((actor->update != NULL) && ((Player*)actor != player) &&
            ACTOR_FLAGS_CHECK_ALL(actor, ACTOR_FLAG_ATTENTION_ENABLED)) {
            
            if ((actorCategory == ACTORCAT_ENEMY) &&
                ACTOR_FLAGS_CHECK_ALL(actor, ACTOR_FLAG_ATTENTION_ENABLED | ACTOR_FLAG_HOSTILE) &&
                (actor->xyzDistToPlayerSq < SQ(500.0f)) && (actor->xyzDistToPlayerSq < sBgmEnemyDistSq)) {
                actorCtx->attention.bgmEnemy = actor;
                sBgmEnemyDistSq = actor->xyzDistToPlayerSq;
            }

            if (actor != playerFocusActor) {
                distSq = Attention_WeightedDistToPlayerSq(actor, player, sAttentionPlayerRotY);

                if ((distSq < sNearestAttentionActorDistSq) && Attention_ActorIsInRange(actor, distSq) &&
                    Attention_ActorOnScreen(play, actor) &&
                    (!BgCheck_CameraLineTest1(&play->colCtx, &player->actor.focus.pos, &actor->focus.pos,
                                              &lineTestResultPos, &poly, true, true, true, true, &bgId) ||
                     SurfaceType_IsIgnoredByProjectiles(&play->colCtx, poly, bgId))) {
                    if (actor->attentionPriority != 0) {
                        if (actor->attentionPriority < sHighestAttentionPriority) {
                            sPrioritizedAttentionActor = actor;
                            sHighestAttentionPriority = actor->attentionPriority;
                        }
                    } else {
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

The attention system provides:
- **Priority-Based Selection**: Higher priority actors take precedence
- **Screen Space Checking**: Only considers on-screen actors
- **Line-of-Sight Verification**: Ensures unobstructed path to target
- **BGM Enemy Tracking**: Closest enemy triggers battle music
- **Weighted Distance**: Player facing direction affects selection

## NPC Interaction AI

### Advanced NPC Tracking Systems

**NPC Auto-Turn Behavior (`z_actor.c:4387`):**
```c
s16 Npc_UpdateAutoTurn(Actor* actor, NpcInteractInfo* interactInfo, f32 distanceRange, s16 maxYawForPlayerTracking,
                       s16 trackingMode) {
    s32 pad;
    s16 yaw;
    s16 yawDiff;

    if (trackingMode != NPC_TRACKING_PLAYER_AUTO_TURN) {
        return trackingMode;
    }

    if (interactInfo->talkState != NPC_TALK_STATE_IDLE) {
        return NPC_TRACKING_FULL_BODY;  // Always face player when talking
    }

    if (distanceRange < Math_Vec3f_DistXYZ(&actor->world.pos, &interactInfo->trackPos)) {
        interactInfo->autoTurnTimer = 0;
        interactInfo->autoTurnState = 0;
        return NPC_TRACKING_NONE;  // Player too far away
    }

    yaw = Math_Vec3f_Yaw(&actor->world.pos, &interactInfo->trackPos);
    yawDiff = ABS((s16)((f32)yaw - actor->shape.rot.y));
    if (maxYawForPlayerTracking >= yawDiff) {
        interactInfo->autoTurnTimer = 0;
        interactInfo->autoTurnState = 0;
        return NPC_TRACKING_HEAD_AND_TORSO;  // Player in front
    }

    // Player is behind the actor, run the auto-turn sequence
    if (DECR(interactInfo->autoTurnTimer) != 0) {
        return interactInfo->trackingMode;
    }

    switch (interactInfo->autoTurnState) {
        case 0:
        case 2:
            // Stand still, not tracking the player
            interactInfo->autoTurnTimer = Rand_S16Offset(30, 30);
            interactInfo->autoTurnState++;
            return NPC_TRACKING_NONE;
        case 1:
            // Glance at the player by only turning the head
            interactInfo->autoTurnTimer = Rand_S16Offset(10, 10);
            interactInfo->autoTurnState++;
            return NPC_TRACKING_HEAD;
    }

    // Auto-turn sequence complete, turn towards the player
    return NPC_TRACKING_FULL_BODY;
}
```

This creates believable NPC behavior:
- **Natural Awareness**: NPCs notice when player is behind them
- **Staged Response**: Look forward → glance → look forward → turn around
- **Randomized Timing**: Prevents robotic, predictable behavior
- **Context Awareness**: Different behavior when talking vs. idle

### Dog Following AI

**Dog Behavior State Machine (`z_en_dog.c:406`):**
```c
void EnDog_FollowPlayer(EnDog* this, PlayState* play) {
    f32 speedXZ;

    if (gSaveContext.dogParams == 0) {
        this->nextBehavior = DOG_SIT;
        this->actionFunc = EnDog_Wait;
        this->actor.speed = 0.0f;
        return;
    }

    if (this->actor.xzDistToPlayer > 400.0f) {
        if (this->nextBehavior != DOG_SIT && this->nextBehavior != DOG_SIT_2) {
            this->nextBehavior = DOG_BOW;
        }
        gSaveContext.dogParams = 0;
        speedXZ = 0.0f;
    } else if (this->actor.xzDistToPlayer > 100.0f) {
        this->nextBehavior = DOG_RUN;
        speedXZ = 4.0f;
    } else if (this->actor.xzDistToPlayer < 40.0f) {
        if (this->nextBehavior != DOG_BOW && this->nextBehavior != DOG_BOW_2) {
            this->nextBehavior = DOG_BOW;
        }
        speedXZ = 0.0f;
    } else {
        this->nextBehavior = DOG_WALK;
        speedXZ = 1.0f;
    }

    Math_ApproachF(&this->actor.speed, speedXZ, 0.6f, 1.0f);

    if (!(this->actor.xzDistToPlayer > 400.0f)) {
        Math_SmoothStepToS(&this->actor.world.rot.y, this->actor.yawTowardsPlayer, 10, 1000, 1);
        this->actor.shape.rot = this->actor.world.rot;
    }
}
```

Pet AI features:
- **Distance-Based Behavior**: Different actions based on distance to player
- **Global State Tracking**: Uses save context to track following status
- **Smooth Speed Transitions**: Gradual acceleration/deceleration
- **Animation State Management**: Coordinates movement with animations

## Boss AI Systems

### Complex Multi-Phase AI

**Gohma Boss State System (`z_boss_goma.c:58`):**
```c
typedef enum GohmaEyeState {
    EYESTATE_IRIS_FOLLOW_BONUS_IFRAMES,
    EYESTATE_IRIS_NO_FOLLOW_NO_IFRAMES,
    EYESTATE_IRIS_FOLLOW_NO_IFRAMES
} GohmaEyeState;

typedef enum GohmaVisualState {
    VISUALSTATE_RED,         // main/eye: red
    VISUALSTATE_DEFAULT,     // main: greenish cyan
    VISUALSTATE_DEFEATED,    // main/eye: dark gray
    VISUALSTATE_STUNNED = 4, // main: alternates with blue
    VISUALSTATE_HIT          // main: alternates with red
} GohmaVisualState;
```

Boss AI incorporates:
- **Multi-Component State**: Separate eye and body state systems
- **Visual Feedback**: Different visual states communicate AI status to player
- **Invincibility Management**: Frame-based invincibility systems
- **Phase Transitions**: Complex state machines for multi-phase encounters

## Performance and Optimization

### AI Update Culling

**Actor Category-Based Freezing (`z_actor.c:2361`):**
```c
u32 sCategoryFreezeMasks[ACTORCAT_MAX] = {
    // ACTORCAT_SWITCH
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_28,
    // ACTORCAT_BG
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_28,
    // ACTORCAT_PLAYER
    0,
    // ACTORCAT_EXPLOSIVE
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_10 | PLAYER_STATE1_28,
    // ACTORCAT_NPC
    PLAYER_STATE1_DEAD,
    // ACTORCAT_ENEMY
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_28 | PLAYER_STATE1_29,
    // ACTORCAT_PROP
    PLAYER_STATE1_DEAD | PLAYER_STATE1_28,
    // ACTORCAT_ITEMACTION
    0,
    // ACTORCAT_MISC
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_28 | PLAYER_STATE1_29,
    // ACTORCAT_BOSS
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_10 | PLAYER_STATE1_28,
    // ACTORCAT_DOOR
    0,
    // ACTORCAT_CHEST
    PLAYER_STATE1_TALKING | PLAYER_STATE1_DEAD | PLAYER_STATE1_28,
};
```

The system optimizes performance by:
- **Selective AI Freezing**: Different actor categories freeze under different conditions
- **Context-Aware Updates**: NPCs continue during conversations, enemies freeze
- **Cutscene Optimization**: Most AI disabled during story sequences
- **Death State Handling**: Minimal processing when player is dead

### Distance-Based AI Activation

Many AI systems use distance checks to reduce computational load:
- **Far Distance**: Minimal or no AI processing
- **Medium Distance**: Basic movement and pathfinding only
- **Close Distance**: Full AI including detection and combat logic
- **Very Close Distance**: Maximum responsiveness and detail

## Advanced AI Patterns

### Emergent Behavior Examples

**Wolfos Pack Behavior (`z_en_wf.c:439`):**
```c
void EnWf_Wait(EnWf* this, PlayState* play) {
    Player* player = GET_PLAYER(play);
    s32 pad;
    s16 angle;

    player = GET_PLAYER(play);
    SkelAnime_Update(&this->skelAnime);

    angle = this->actor.yawTowardsPlayer - this->actor.shape.rot.y;
    angle = ABS(angle);

    if (!EnWf_DodgeRanged(play, this)) {
        angle = player->actor.shape.rot.y - this->actor.shape.rot.y;
        angle = ABS(angle);

        if ((this->actor.xzDistToPlayer < 80.0f) && (player->meleeWeaponState != 0) && (angle >= 0x1F40)) {
            this->actor.shape.rot.y = this->actor.world.rot.y = this->actor.yawTowardsPlayer;
            EnWf_SetupRunAroundPlayer(this);
        } else {
            this->actionTimer--;
            if (this->actionTimer == 0) {
                if (Actor_IsFacingPlayer(&this->actor, 0x1555)) {
                    if (Rand_ZeroOne() > 0.3f) {
                        EnWf_SetupRunAtPlayer(this, play);
                    } else {
                        EnWf_SetupRunAroundPlayer(this);
                    }
                } else {
                    EnWf_SetupSearchForPlayer(this);
                }
            }
        }
    }
}
```

Sophisticated enemy AI featuring:
- **Weapon Awareness**: Reacts to player's sword state
- **Flanking Behavior**: Runs around player when sword is drawn
- **Randomized Decisions**: Probabilistic attack vs. circle behavior
- **Search Behavior**: Actively hunts player when not in direct sight

### Flare Dancer Intelligence

**Bomb Detection and Evasion (`z_en_fd.c:334`):**
```c
s32 EnFd_CanSeeActor(EnFd* this, Actor* actor, PlayState* play) {
    CollisionPoly* colPoly;
    s32 bgId;
    Vec3f colPoint;
    s16 angle;

    if (Math_Vec3f_DistXYZ(&this->actor.world.pos, &actor->world.pos) > 400.0f) {
        return false;
    }

    angle = (f32)Math_Vec3f_Yaw(&this->actor.world.pos, &actor->world.pos) - this->actor.shape.rot.y;
    if (ABS(angle) > 0x1C70) {
        return false;
    }

    if (BgCheck_EntityLineTest1(&play->colCtx, &this->actor.world.pos, &actor->world.pos, &colPoint, &colPoly, true,
                                false, false, false, true, &bgId)) {
        return false;
    }

    return true;
}

Actor* EnFd_FindBomb(EnFd* this, PlayState* play) {
    Actor* actor = play->actorCtx.actorLists[ACTORCAT_EXPLOSIVE].head;

    while (actor != NULL) {
        if (actor->params != 0 || actor->parent != NULL) {
            actor = actor->next;
            continue;
        }

        if (actor->id != ACTOR_EN_BOM) {
            actor = actor->next;
            continue;
        }

        if (EnFd_CanSeeActor(this, actor, play) != 1) {
            actor = actor->next;
            continue;
        }

        return actor;
    }
    return NULL;
}
```

This creates intelligent bomb-avoidance behavior:
- **Explosive Detection**: Actively searches for bombs in environment
- **Vision-Based Detection**: Only reacts to bombs within sight range
- **Line-of-Sight Verification**: Uses collision detection for realistic vision
- **Type Filtering**: Specifically looks for particular explosive types

## Debugging and AI Analysis

### AI State Visualization

The engine includes various debugging systems for AI development:
- **State Display**: Visual indicators of current AI state
- **Pathfinding Visualization**: Debug rendering of waypoint paths
- **Detection Range Display**: Visual representation of AI perception
- **Attention System Debug**: Shows which actors are being considered for focus

### Performance Profiling

Debug builds include AI performance metrics:
- **AI Update Times**: Time spent in different AI systems per frame
- **Detection Check Counts**: Number of vision/proximity tests per frame
- **State Transition Frequency**: Tracking of behavioral changes

## Practical Implications for Modding

### Custom AI Implementation

**Adding New Behavior States:**
Understanding the function pointer system allows modders to:
- Implement custom enemy AI patterns
- Create new NPC interaction systems
- Add environmental AI behaviors
- Modify existing AI parameters for different difficulty levels

**Example AI State Addition:**
```c
void CustomEnemy_PatrolBehavior(CustomEnemy* this, PlayState* play) {
    // Custom patrol logic
    if (this->detectionTimer > 0) {
        this->detectionTimer--;
        // Heightened awareness behavior
    }
    
    // Switch to pursuit when player detected
    if (Player_InDetectionRange(this, play)) {
        this->actionFunc = CustomEnemy_PursuitBehavior;
    }
}
```

### AI Parameter Tuning

**Detection System Modification:**
```c
// Example: Modified guard detection for stealth gameplay
if (Player_IsCrouching(player)) {
    detectionRange *= 0.6f;  // Reduced detection when crouching
}

if (Player_IsInShadow(player, play)) {
    detectionRange *= 0.4f;  // Further reduction in shadows
}
```

**Pathfinding Enhancements:**
```c
// Example: Dynamic pathfinding difficulty
if (this->actor.params & ENEMY_FLAG_SMART) {
    // Use A* pathfinding for intelligent enemies
    this->targetWaypoint = FindOptimalPath(this, target);
} else {
    // Use simple waypoint following for basic enemies
    this->targetWaypoint = GetNextWaypoint(this);
}
```

### Performance Considerations

**AI Optimization Guidelines:**
- Minimize distance calculations by using squared distances
- Implement distance-based LOD for AI complexity
- Use frame-offset updates for non-critical AI systems
- Cache expensive calculations like line-of-sight tests

**Memory Management:**
- AI state variables should use minimal memory footprint
- Share common AI data structures between similar enemies
- Use bit fields for boolean AI flags to save space

## Conclusion

The OOT AI system demonstrates sophisticated game AI design that was groundbreaking for its time and remains impressive today. The combination of state machines, pathfinding, perception systems, and behavioral controllers creates believable, challenging, and engaging AI opponents and NPCs.

Key strengths of the system include:
- **Modular Design**: Clean separation between different AI subsystems
- **Performance Optimization**: Intelligent culling and LOD systems
- **Behavioral Variety**: Different AI patterns for different actor types
- **Player-Responsive**: AI that adapts to player actions and state

The function pointer-based state machine architecture provides both flexibility and performance, while the sophisticated detection and pathfinding systems create believable world interactions. The attention and targeting systems ensure that the most relevant actors are prioritized for player interaction.

Understanding these AI systems is crucial for effective OOT modding, as AI behavior affects virtually every aspect of gameplay. The careful balance between computational efficiency and behavioral complexity serves as an excellent reference for modern game AI development, showing how systematic design and smart optimization can create compelling AI experiences within strict resource constraints. 