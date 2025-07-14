# OOT Collision Detection System Deep Dive

## Overview

This document provides a comprehensive analysis of the Collision Detection System in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The collision system is a sophisticated multi-layered architecture that handles static background collision, dynamic object collision, and actor-to-actor collision detection through spatial subdivision and optimized collision algorithms.

## Architecture Overview

### Collision System Components

The collision system consists of several interconnected subsystems:

1. **Background Collision (BgCheck)**: Static world geometry collision
2. **Dynamic Collision (DynaPoly)**: Moving platform and object collision  
3. **Actor Collision (CollisionCheck)**: Actor-to-actor collision detection
4. **Spatial Subdivision**: Optimization through spatial partitioning
5. **Surface Type System**: Material and property detection

### Core Data Structures

**Collision Context (`bgcheck.h`):**
```c
typedef struct CollisionContext {
    /* 0x00 */ CollisionHeader* colHeader;
    /* 0x04 */ Vec3f minBounds;
    /* 0x10 */ Vec3f maxBounds;
    /* 0x1C */ Vec3i subdivAmount;
    /* 0x28 */ Vec3f subdivLength;
    /* 0x34 */ Vec3f subdivLengthInv;
    /* 0x40 */ StaticLookup* lookupTbl;
    /* 0x44 */ SSList* polyList;
    /* 0x48 */ DynaCollisionContext dyna;
    /* 0x64 */ WaterBox* waterBoxes;
    /* 0x68 */ s32 waterBoxCount;
} CollisionContext;
```

## Background Collision System

### Static Collision Header

**Collision Header Processing (`z_bgcheck.c:3905`):**
```c
void CollisionHeader_SegmentedToVirtual(CollisionHeader* colHeader) {
    colHeader->vtxList = SEGMENTED_TO_VIRTUAL(colHeader->vtxList);
    colHeader->polyList = SEGMENTED_TO_VIRTUAL(colHeader->polyList);
    colHeader->surfaceTypeList = SEGMENTED_TO_VIRTUAL(colHeader->surfaceTypeList);
    colHeader->bgCamList = SEGMENTED_TO_VIRTUAL(colHeader->bgCamList);
    colHeader->waterBoxes = SEGMENTED_TO_VIRTUAL(colHeader->waterBoxes);
}
```

### Collision Polygon System

**Collision Polygon Structure and Functions (`z_bgcheck.c:213`):**
```c
s16 CollisionPoly_GetMinY(CollisionPoly* poly, Vec3s* vtxList) {
    s16 vtxId;
    s16 minY;
    s16 temp;
    
    vtxId = COLPOLY_GET_VTXA(poly->flags);
    minY = vtxList[vtxId].y;
    
    vtxId = COLPOLY_GET_VTXB(poly->flags);
    temp = vtxList[vtxId].y;
    if (temp < minY) {
        minY = temp;
    }
    
    vtxId = COLPOLY_GET_VTXC(poly->flags);
    temp = vtxList[vtxId].y;
    if (temp < minY) {
        minY = temp;
    }
    
    return minY;
}
```

**Polygon Normal Calculation (`z_bgcheck.c:237`):**
```c
void CollisionPoly_GetNormalF(CollisionPoly* poly, f32* nx, f32* ny, f32* nz) {
    f32 mag;
    f32 tempX, tempY, tempZ;
    
    tempX = poly->normal.x;
    tempY = poly->normal.y;
    tempZ = poly->normal.z;
    
    mag = sqrtf(SQ(tempX) + SQ(tempY) + SQ(tempZ));
    
    if (IS_ZERO(mag)) {
        *nx = 0.0f;
        *ny = 1.0f;
        *nz = 0.0f;
        return;
    }
    
    mag = 1.0f / mag;
    *nx = tempX * mag;
    *ny = tempY * mag;
    *nz = tempZ * mag;
}
```

### Ray Casting System

**Downward Ray Casting (`z_bgcheck.c:1714`):**
```c
f32 BgCheck_RaycastDownImpl(PlayState* play, CollisionContext* colCtx, u16 xpFlags, 
                           CollisionPoly** outPoly, s32* outBgId, Vec3f* pos, Actor* actor, 
                           u32 downChkFlags, f32 chkDist) {
    f32 yIntersect;
    f32 yIntersectStatic;
    f32 yIntersectDyna;
    CollisionPoly* polyStatic;
    CollisionPoly* polyDyna;
    s32 bgIdStatic;
    s32 bgIdDyna;
    
    *outBgId = BGCHECK_SCENE;
    *outPoly = NULL;
    yIntersect = BGCHECK_Y_MIN;
    
    // Check if position is within static bounding box
    if (BgCheck_PosInStaticBoundingBox(colCtx, pos)) {
        // Raycast against static geometry
        yIntersectStatic = BgCheck_RaycastDownStatic(&colCtx->lookupTbl[0], colCtx, xpFlags, 
                                                    &polyStatic, pos, downChkFlags, chkDist, yIntersect);
        
        if (yIntersectStatic > yIntersect) {
            yIntersect = yIntersectStatic;
            *outPoly = polyStatic;
            *outBgId = BGCHECK_SCENE;
        }
    }
    
    // Check dynamic collision if enabled
    if (downChkFlags & BGCHECK_RAYCAST_DOWN_CHECK_DYNA) {
        DynaRaycastDown dynaRaycastDown;
        
        dynaRaycastDown.colCtx = colCtx;
        dynaRaycastDown.xpFlags = xpFlags;
        dynaRaycastDown.pos = *pos;
        dynaRaycastDown.chkDist = chkDist;
        dynaRaycastDown.yIntersect = yIntersect;
        dynaRaycastDown.poly = NULL;
        dynaRaycastDown.bgId = BGCHECK_SCENE;
        
        yIntersectDyna = BgCheck_RaycastDownDyna(&dynaRaycastDown);
        
        if (yIntersectDyna > yIntersect) {
            yIntersect = yIntersectDyna;
            *outPoly = dynaRaycastDown.poly;
            *outBgId = dynaRaycastDown.bgId;
        }
    }
    
    return yIntersect;
}
```

### Spatial Subdivision System

**Subdivision Initialization (`z_bgcheck.c:1400`):**
```c
u32 BgCheck_InitializeStaticLookup(CollisionContext* colCtx, PlayState* play, StaticLookup* lookupTbl) {
    s32 subdivMinX, subdivMinY, subdivMinZ;
    s32 subdivMaxX, subdivMaxY, subdivMaxZ;
    s32 subdivX, subdivY, subdivZ;
    s32 polyListMax;
    StaticLookup* lookup;
    s32 i;
    
    // Initialize all subdivision entries
    for (subdivZ = 0; subdivZ < colCtx->subdivAmount.z; subdivZ++) {
        for (subdivY = 0; subdivY < colCtx->subdivAmount.y; subdivY++) {
            for (subdivX = 0; subdivX < colCtx->subdivAmount.x; subdivX++) {
                lookup = &lookupTbl[subdivZ * (colCtx->subdivAmount.x * colCtx->subdivAmount.y) + 
                                  subdivY * colCtx->subdivAmount.x + subdivX];
                SSList_SetNull(&lookup->floor);
                SSList_SetNull(&lookup->wall);
                SSList_SetNull(&lookup->ceiling);
            }
        }
    }
    
    // Add polygons to appropriate subdivisions
    for (i = 0; i < colCtx->colHeader->numPolygons; i++) {
        // Calculate polygon's subdivision bounds
        BgCheck_GetPolySubdivisionBounds(colCtx, colCtx->colHeader->vtxList, colCtx->colHeader->polyList,
                                        &subdivMinX, &subdivMinY, &subdivMinZ, &subdivMaxX, &subdivMaxY, &subdivMaxZ, i);
        
        // Add polygon to all subdivisions it intersects
        for (subdivZ = subdivMinZ; subdivZ <= subdivMaxZ; subdivZ++) {
            for (subdivY = subdivMinY; subdivY <= subdivMaxY; subdivY++) {
                for (subdivX = subdivMinX; subdivX <= subdivMaxX; subdivX++) {
                    lookup = &lookupTbl[subdivZ * (colCtx->subdivAmount.x * colCtx->subdivAmount.y) + 
                                      subdivY * colCtx->subdivAmount.x + subdivX];
                    StaticLookup_AddPoly(lookup, colCtx, colCtx->colHeader->polyList, 
                                        colCtx->colHeader->vtxList, i);
                }
            }
        }
    }
    
    return polyListMax;
}
```

### Wall Collision Detection

**Sphere vs Wall Collision (`z_bgcheck.c:1954`):**
```c
s32 BgCheck_CheckWallImpl(CollisionContext* colCtx, u16 xpFlags, Vec3f* posResult, Vec3f* posNext, 
                         Vec3f* posPrev, f32 radius, CollisionPoly** outPoly, s32* outBgId, 
                         Actor* actor, f32 checkHeight, u8 argA) {
    f32 intersectDist;
    f32 wallPolyNormalX, wallPolyNormalY, wallPolyNormalZ;
    f32 wallPolyDistXZ;
    f32 invWallPolyDistXZ;
    f32 planeDist;
    f32 tempX, tempZ;
    f32 posInterpX, posInterpZ;
    CollisionPoly* wallPoly;
    s32 bgId;
    
    *outBgId = BGCHECK_SCENE;
    *outPoly = NULL;
    
    // Check static wall collision
    if (BgCheck_PosInStaticBoundingBox(colCtx, posNext)) {
        if (BgCheck_SphVsStaticWall(&colCtx->lookupTbl[0], colCtx, xpFlags, &posResult->x, &posResult->z,
                                   posNext, radius, &wallPoly)) {
            *outPoly = wallPoly;
            *outBgId = BGCHECK_SCENE;
        }
    }
    
    // Check dynamic wall collision
    if (BgCheck_SphVsDynaWall(colCtx, xpFlags, &posResult->x, &posResult->z, posNext, 
                             radius, &wallPoly, &bgId, actor)) {
        // Compare distances to determine closest collision
        CollisionPoly_GetNormalF(wallPoly, &wallPolyNormalX, &wallPolyNormalY, &wallPolyNormalZ);
        
        planeDist = Math3D_PlaneF(wallPolyNormalX, wallPolyNormalY, wallPolyNormalZ, 
                                 wallPoly->dist, posNext->x, posNext->y, posNext->z);
        
        if (planeDist < radius) {
            *outPoly = wallPoly;
            *outBgId = bgId;
        }
    }
    
    return (*outPoly != NULL);
}
```

## Dynamic Collision System

### DynaPoly Architecture

**DynaPoly Initialization (`z_bgcheck.c:2709`):**
```c
void DynaPoly_Init(PlayState* play, DynaCollisionContext* dyna) {
    dyna->bgActorCount = 0;
    dyna->polyNodeList.tbl = NULL;
    dyna->polyNodeList.count = 0;
    dyna->polyNodeList.max = 0;
    dyna->vtxList = NULL;
    dyna->vtxListCount = 0;
    dyna->polyList = NULL;
    dyna->polyListCount = 0;
    dyna->polyListMax = 0;
    dyna->bgActors = NULL;
    dyna->bgActorMax = 0;
    
    DynaLookup_Reset(&dyna->dynaLookup);
}
```

**DynaPoly Actor Registration (`z_bgcheck.c:2740`):**
```c
s32 DynaPoly_SetBgActor(PlayState* play, DynaCollisionContext* dyna, Actor* actor, CollisionHeader* colHeader) {
    CollisionPoly* polyList;
    Vec3s* vtxList;
    s32 vtxStartIndex;
    s32 polyStartIndex;
    s32 bgId;
    
    bgId = dyna->bgActorCount;
    
    if (bgId >= dyna->bgActorMax) {
        return BGCHECK_SCENE;
    }
    
    // Set up BG actor
    BgActor_SetActor(&dyna->bgActors[bgId], actor, colHeader);
    
    // Allocate vertex list
    DynaPoly_AllocVtxList(play, &vtxList, colHeader->numVertices);
    DynaPoly_AllocPolyList(play, &polyList, colHeader->numPolygons);
    
    // Copy collision data
    vtxStartIndex = dyna->vtxListCount;
    for (s32 i = 0; i < colHeader->numVertices; i++) {
        vtxList[vtxStartIndex + i] = colHeader->vtxList[i];
    }
    
    polyStartIndex = dyna->polyListCount;
    for (s32 i = 0; i < colHeader->numPolygons; i++) {
        polyList[polyStartIndex + i] = colHeader->polyList[i];
    }
    
    // Update counters
    dyna->vtxListCount += colHeader->numVertices;
    dyna->polyListCount += colHeader->numPolygons;
    dyna->bgActorCount++;
    
    // Add to lookup table
    DynaPoly_AddBgActorToLookup(play, dyna, bgId, &vtxStartIndex, &polyStartIndex);
    
    return bgId;
}
```

### Dynamic Collision Updates

**DynaPoly Update System (`z_bgcheck.c:3067`):**
```c
void DynaPoly_UpdateContext(PlayState* play, DynaCollisionContext* dyna) {
    BgActor* bgActor;
    s32 i;
    
    // Update all dynamic actors
    for (i = 0; i < dyna->bgActorCount; i++) {
        bgActor = &dyna->bgActors[i];
        
        if (bgActor->actor != NULL) {
            // Check if transform has changed
            if (!BgActor_IsTransformUnchanged(bgActor)) {
                // Update transform and mark lookup for invalidation
                DynaPoly_SetBgActorPrevTransform(play, bgActor);
                DynaPoly_InvalidateLookup(play, dyna);
            }
        }
    }
    
    // Update background actor transforms
    DynaPoly_UpdateBgActorTransforms(play, dyna);
}
```

## Actor Collision System

### Collision Check Context

**Collision Check Initialization (`z_collision_check.c:3024`):**
```c
void CollisionCheck_InitContext(PlayState* play, CollisionCheckContext* colChkCtx) {
    colChkCtx->colATCount = 0;
    colChkCtx->colACCount = 0;
    colChkCtx->colOCCount = 0;
    colChkCtx->sacFlags = 0;
    
    // Initialize collider arrays
    for (s32 i = 0; i < COLLISION_CHECK_AT_MAX; i++) {
        colChkCtx->colAT[i] = NULL;
    }
    for (s32 i = 0; i < COLLISION_CHECK_AC_MAX; i++) {
        colChkCtx->colAC[i] = NULL;
    }
    for (s32 i = 0; i < COLLISION_CHECK_OC_MAX; i++) {
        colChkCtx->colOC[i] = NULL;
    }
}
```

### AT vs AC Collision Detection

**AT/AC Collision Processing (`z_collision_check.c:2658`):**
```c
void CollisionCheck_AT(PlayState* play, CollisionCheckContext* colChkCtx) {
    Collider** atColP;
    Collider* atCol;
    
    if (colChkCtx->colATCount == 0 || colChkCtx->colACCount == 0) {
        return;
    }
    
    // Check all AT colliders against all AC colliders
    for (atColP = colChkCtx->colAT; atColP < colChkCtx->colAT + colChkCtx->colATCount; atColP++) {
        atCol = *atColP;
        
        if (atCol != NULL && atCol->atFlags & AT_ON) {
            if (atCol->actor != NULL && atCol->actor->update == NULL) {
                continue;
            }
            CollisionCheck_AC(play, colChkCtx, atCol);
        }
    }
    
    // Spawn hit effects for successful collisions
    CollisionCheck_SetHitEffects(play, colChkCtx);
}
```

**AT vs AC Collision Resolution (`z_collision_check.c:1716`):**
```c
s32 CollisionCheck_SetATvsAC(PlayState* play, Collider* atCol, ColliderElement* atElem, Vec3f* atPos, 
                            Collider* acCol, ColliderElement* acElem, Vec3f* acPos, Vec3f* hitPos) {
    // Handle collision bounce for hard surfaces
    if (acCol->acFlags & AC_HARD && atCol->actor != NULL && acCol->actor != NULL) {
        CollisionCheck_SetBounce(atCol, acCol);
    }
    
    // Set AT (attack) collision info
    if (!(acElem->acElemFlags & ACELEM_NO_AT_INFO)) {
        atCol->atFlags |= AT_HIT;
        atCol->at = acCol->actor;
        atElem->atHit = acCol;
        atElem->atHitElem = acElem;
        atElem->atElemFlags |= ATELEM_HIT;
        
        if (atCol->actor != NULL) {
            atCol->actor->colChkInfo.atHitBacklash = acElem->acDmgInfo.hitBacklash;
        }
    }
    
    // Set AC (attack collision) info
    acCol->acFlags |= AC_HIT;
    acCol->ac = atCol->actor;
    acElem->acHit = atCol;
    acElem->acHitElem = atElem;
    acElem->acElemFlags |= ACELEM_HIT;
    
    if (acCol->actor != NULL) {
        acCol->actor->colChkInfo.acHitSpecialEffect = atElem->atDmgInfo.hitSpecialEffect;
    }
    
    // Store hit position
    acElem->acDmgInfo.hitPos.x = hitPos->x;
    acElem->acDmgInfo.hitPos.y = hitPos->y;
    acElem->acDmgInfo.hitPos.z = hitPos->z;
    
    // Handle hit effects
    if (!(atElem->atElemFlags & ATELEM_AT_HITMARK) && 
        acCol->colMaterial != COL_MATERIAL_METAL &&
        acCol->colMaterial != COL_MATERIAL_WOOD && 
        acCol->colMaterial != COL_MATERIAL_HARD) {
        acElem->acElemFlags |= ACELEM_DRAW_HITMARK;
    } else {
        CollisionCheck_HitEffects(play, atCol, atElem, acCol, acElem, hitPos);
        atElem->atElemFlags |= ATELEM_DREW_HITMARK;
    }
    
    return true;
}
```

### OC (Object Collision) System

**OC Collision Processing (`z_collision_check.c:2966`):**
```c
void CollisionCheck_OC(PlayState* play, CollisionCheckContext* colChkCtx) {
    Collider** leftColP;
    Collider** rightColP;
    ColChkVsFunc vsFunc;
    
    for (leftColP = colChkCtx->colOC; leftColP < colChkCtx->colOC + colChkCtx->colOCCount; leftColP++) {
        if (*leftColP == NULL || CollisionCheck_SkipOC(*leftColP) == true) {
            continue;
        }
        
        for (rightColP = leftColP + 1; rightColP < colChkCtx->colOC + colChkCtx->colOCCount; rightColP++) {
            if (*rightColP == NULL || CollisionCheck_SkipOC(*rightColP) == true ||
                CollisionCheck_Incompatible(*leftColP, *rightColP) == true) {
                continue;
            }
            
            vsFunc = sOCVsFuncs[(*leftColP)->shape][(*rightColP)->shape];
            if (vsFunc == NULL) {
                continue;
            }
            
            vsFunc(play, colChkCtx, *leftColP, *rightColP);
        }
    }
}
```

**OC Collision Resolution (`z_collision_check.c:2720`):**
```c
void CollisionCheck_SetOCvsOC(Collider* leftCol, ColliderElement* leftElem, Vec3f* leftPos, 
                             Collider* rightCol, ColliderElement* rightElem, Vec3f* rightPos, f32 overlap) {
    f32 leftDispRatio;
    f32 rightDispRatio;
    f32 xzDist;
    f32 leftMass;
    f32 rightMass;
    f32 totalMass;
    f32 xDelta;
    f32 zDelta;
    Actor* leftActor = leftCol->actor;
    Actor* rightActor = rightCol->actor;
    s32 leftMassType;
    s32 rightMassType;
    
    // Set collision flags
    leftCol->ocFlags1 |= OC1_HIT;
    leftCol->oc = rightActor;
    leftElem->ocElemFlags |= OCELEM_HIT;
    
    rightCol->oc = leftActor;
    rightCol->ocFlags1 |= OC1_HIT;
    rightElem->ocElemFlags |= OCELEM_HIT;
    
    // Handle player collision flags
    if (rightCol->ocFlags2 & OC2_TYPE_PLAYER) {
        leftCol->ocFlags2 |= OC2_HIT_PLAYER;
    }
    if (leftCol->ocFlags2 & OC2_TYPE_PLAYER) {
        rightCol->ocFlags2 |= OC2_HIT_PLAYER;
    }
    
    // Skip physics if either actor is null or has no-push flag
    if (leftActor == NULL || rightActor == NULL || 
        leftCol->ocFlags1 & OC1_NO_PUSH || rightCol->ocFlags1 & OC1_NO_PUSH) {
        return;
    }
    
    // Calculate mass types and values
    leftMassType = CollisionCheck_GetMassType(leftActor->colChkInfo.mass);
    rightMassType = CollisionCheck_GetMassType(rightActor->colChkInfo.mass);
    
    leftMass = leftActor->colChkInfo.mass;
    rightMass = rightActor->colChkInfo.mass;
    totalMass = leftMass + rightMass;
    
    if (IS_ZERO(totalMass)) {
        leftMass = rightMass = 1.0f;
        totalMass = 2.0f;
    }
    
    // Calculate separation vector
    xDelta = rightPos->x - leftPos->x;
    zDelta = rightPos->z - leftPos->z;
    xzDist = sqrtf(SQ(xDelta) + SQ(zDelta));
    
    if (IS_ZERO(xzDist)) {
        xDelta = 1.0f;
        zDelta = 0.0f;
        xzDist = 1.0f;
    }
    
    // Calculate displacement ratios based on mass
    leftDispRatio = (rightMass / totalMass) * (overlap / xzDist);
    rightDispRatio = (leftMass / totalMass) * (overlap / xzDist);
    
    // Apply mass-based movement restrictions
    if ((leftMassType == MASSTYPE_IMMOVABLE) || 
        (leftMassType == MASSTYPE_HEAVY && rightMassType == MASSTYPE_NORMAL)) {
        leftDispRatio = 0.0f;
        rightDispRatio = overlap / xzDist;
    } else if ((rightMassType == MASSTYPE_IMMOVABLE) || 
               (rightMassType == MASSTYPE_HEAVY && leftMassType == MASSTYPE_NORMAL)) {
        rightDispRatio = 0.0f;
        leftDispRatio = overlap / xzDist;
    }
    
    // Apply displacement
    leftActor->world.pos.x -= xDelta * leftDispRatio;
    leftActor->world.pos.z -= zDelta * leftDispRatio;
    rightActor->world.pos.x += xDelta * rightDispRatio;
    rightActor->world.pos.z += zDelta * rightDispRatio;
}
```

## Surface Type System

### Surface Material Properties

**Surface Type Functions (`z_bgcheck.c:3952`):**
```c
u32 SurfaceType_GetData(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId, s32 dataIdx) {
    SurfaceType* surfaceType;
    u32 surfaceTypeIdx;
    
    if (bgId == BGCHECK_SCENE) {
        surfaceTypeIdx = SurfaceType_GetSurfaceTypeIdx(colCtx, poly, bgId);
        if (surfaceTypeIdx == SURFACE_TYPE_0) {
            return 0;
        }
        surfaceType = &colCtx->colHeader->surfaceTypeList[surfaceTypeIdx];
    } else {
        DynaPolyActor* bgActor = DynaPoly_GetActor(colCtx, bgId);
        if (bgActor == NULL) {
            return 0;
        }
        surfaceTypeIdx = SurfaceType_GetSurfaceTypeIdx(colCtx, poly, bgId);
        surfaceType = &bgActor->colHeader->surfaceTypeList[surfaceTypeIdx];
    }
    
    return surfaceType->data[dataIdx];
}
```

**Material-based SFX Mapping (`z_bgcheck.c:64`):**
```c
u16 sSurfaceMaterialToSfxOffset[SURFACE_MATERIAL_MAX] = {
    SURFACE_SFX_OFFSET_DIRT,          // SURFACE_MATERIAL_DIRT
    SURFACE_SFX_OFFSET_SAND,          // SURFACE_MATERIAL_SAND
    SURFACE_SFX_OFFSET_STONE,         // SURFACE_MATERIAL_STONE
    SURFACE_SFX_OFFSET_JABU,          // SURFACE_MATERIAL_JABU
    SURFACE_SFX_OFFSET_WATER_SHALLOW, // SURFACE_MATERIAL_WATER_SHALLOW
    SURFACE_SFX_OFFSET_WATER_DEEP,    // SURFACE_MATERIAL_WATER_DEEP
    SURFACE_SFX_OFFSET_TALL_GRASS,    // SURFACE_MATERIAL_TALL_GRASS
    SURFACE_SFX_OFFSET_LAVA,          // SURFACE_MATERIAL_LAVA
    SURFACE_SFX_OFFSET_GRASS,         // SURFACE_MATERIAL_GRASS
    SURFACE_SFX_OFFSET_BRIDGE,        // SURFACE_MATERIAL_BRIDGE
    SURFACE_SFX_OFFSET_WOOD,          // SURFACE_MATERIAL_WOOD
    SURFACE_SFX_OFFSET_DIRT,          // SURFACE_MATERIAL_DIRT_SOFT
    SURFACE_SFX_OFFSET_ICE,           // SURFACE_MATERIAL_ICE
    SURFACE_SFX_OFFSET_CARPET,        // SURFACE_MATERIAL_CARPET
};
```

### Surface Property Queries

**Surface Property Functions (`z_bgcheck.c:4144`):**
```c
u32 SurfaceType_GetFloorProperty(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    return SurfaceType_GetData(colCtx, poly, bgId, 0) & SURFACE_PROPERTY_MASK;
}

u32 SurfaceType_GetWallType(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    return (SurfaceType_GetData(colCtx, poly, bgId, 0) & WALL_TYPE_MASK) >> WALL_TYPE_SHIFT;
}

u32 SurfaceType_GetMaterial(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    return (SurfaceType_GetData(colCtx, poly, bgId, 0) & SURFACE_MATERIAL_MASK) >> SURFACE_MATERIAL_SHIFT;
}

u16 SurfaceType_GetSfxOffset(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    u32 material = SurfaceType_GetMaterial(colCtx, poly, bgId);
    return sSurfaceMaterialToSfxOffset[material];
}

u32 SurfaceType_GetFloorEffect(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    return (SurfaceType_GetData(colCtx, poly, bgId, 1) & FLOOR_EFFECT_MASK) >> FLOOR_EFFECT_SHIFT;
}

u32 SurfaceType_CanHookshot(CollisionContext* colCtx, CollisionPoly* poly, s32 bgId) {
    u32 hookshotSettings = SurfaceType_GetData(colCtx, poly, bgId, 1) & HOOKSHOT_MASK;
    return hookshotSettings != HOOKSHOT_NONE;
}
```

## Water Box System

### Water Box Detection

**Water Surface Detection (`z_bgcheck.c:4267`):**
```c
s32 WaterBox_GetSurface1(PlayState* play, CollisionContext* colCtx, f32 x, f32 z, 
                        f32* ySurface, WaterBox** outWaterBox) {
    WaterBox* waterBox;
    s32 i;
    
    for (i = 0; i < colCtx->waterBoxCount; i++) {
        waterBox = &colCtx->waterBoxes[i];
        
        // Check if point is within water box XZ bounds
        if (x >= waterBox->xMin && x <= waterBox->xMax && 
            z >= waterBox->zMin && z <= waterBox->zMax) {
            
            *ySurface = waterBox->ySurface;
            *outWaterBox = waterBox;
            return true;
        }
    }
    
    return false;
}
```

**Water Box Surface Query (`z_bgcheck.c:4287`):**
```c
s32 WaterBox_GetSurfaceImpl(PlayState* play, CollisionContext* colCtx, f32 x, f32 z, 
                           f32* ySurface, WaterBox** outWaterBox) {
    WaterBox* waterBox;
    f32 waterBoxDistSq;
    f32 minDistSq = FLT_MAX;
    WaterBox* closestWaterBox = NULL;
    f32 closestSurface = BGCHECK_Y_MIN;
    s32 i;
    
    // Find closest water box
    for (i = 0; i < colCtx->waterBoxCount; i++) {
        waterBox = &colCtx->waterBoxes[i];
        
        if (x >= waterBox->xMin && x <= waterBox->xMax && 
            z >= waterBox->zMin && z <= waterBox->zMax) {
            
            // Point is inside water box
            *ySurface = waterBox->ySurface;
            *outWaterBox = waterBox;
            return true;
        }
        
        // Calculate distance to water box
        waterBoxDistSq = Math3D_DistToBox(x, 0, z, waterBox->xMin, waterBox->zMin, 
                                         waterBox->xMax, waterBox->zMax);
        
        if (waterBoxDistSq < minDistSq) {
            minDistSq = waterBoxDistSq;
            closestWaterBox = waterBox;
            closestSurface = waterBox->ySurface;
        }
    }
    
    // Use closest water box if within reasonable distance
    if (minDistSq < 1000.0f && closestWaterBox != NULL) {
        *ySurface = closestSurface;
        *outWaterBox = closestWaterBox;
        return true;
    }
    
    return false;
}
```

## Collision Utility Functions

### Polygon Intersection Tests

**Y-Intersection Test (`z_bgcheck.c:347`):**
```c
s32 CollisionPoly_CheckYIntersectApprox1(CollisionPoly* poly, Vec3s* vtxList, f32 x, f32 z, 
                                        f32* yIntersect, f32 chkDist) {
    Vec3f vtx0, vtx1, vtx2;
    f32 nx, ny, nz;
    f32 originDist;
    f32 intersectDist;
    
    // Get polygon vertices
    CollisionPoly_GetVertices(poly, vtxList, vtx0, vtx1, vtx2);
    
    // Get polygon normal
    CollisionPoly_GetNormalF(poly, &nx, &ny, &nz);
    
    // Skip near-vertical polygons
    if (fabsf(ny) < 0.001f) {
        return false;
    }
    
    // Calculate plane equation: nx*x + ny*y + nz*z + d = 0
    originDist = -(nx * vtx0.x + ny * vtx0.y + nz * vtx0.z);
    
    // Calculate Y intersection point
    intersectDist = -(nx * x + nz * z + originDist) / ny;
    
    // Check if intersection is within distance threshold
    if (fabsf(intersectDist - *yIntersect) > chkDist) {
        return false;
    }
    
    // Check if point is inside triangle
    if (Math3D_PointInTriangle(&vtx0, &vtx1, &vtx2, x, intersectDist, z)) {
        *yIntersect = intersectDist;
        return true;
    }
    
    return false;
}
```

### Line vs Polygon Intersection

**Line-Polygon Intersection (`z_bgcheck.c:435`):**
```c
s32 CollisionPoly_LineVsPoly(CollisionPoly* poly, Vec3s* vtxList, Vec3f* posA, Vec3f* posB, 
                            Vec3f* planeIntersect, s32 chkOneFace, f32 chkDist) {
    Vec3f vtx0, vtx1, vtx2;
    f32 nx, ny, nz;
    f32 originDist;
    f32 lineDir[3];
    f32 denominator;
    f32 t;
    f32 intersectX, intersectY, intersectZ;
    
    // Get polygon vertices and normal
    CollisionPoly_GetVertices(poly, vtxList, vtx0, vtx1, vtx2);
    CollisionPoly_GetNormalF(poly, &nx, &ny, &nz);
    
    // Calculate line direction
    lineDir[0] = posB->x - posA->x;
    lineDir[1] = posB->y - posA->y;
    lineDir[2] = posB->z - posA->z;
    
    // Calculate denominator (line direction dot normal)
    denominator = lineDir[0] * nx + lineDir[1] * ny + lineDir[2] * nz;
    
    // Check if line is parallel to plane
    if (IS_ZERO(denominator)) {
        return false;
    }
    
    // Check one-face collision (line approaching from front)
    if (chkOneFace && denominator > 0) {
        return false;
    }
    
    // Calculate plane distance
    originDist = -(nx * vtx0.x + ny * vtx0.y + nz * vtx0.z);
    
    // Calculate intersection parameter t
    t = -(nx * posA->x + ny * posA->y + nz * posA->z + originDist) / denominator;
    
    // Check if intersection is within line segment
    if (t < 0.0f || t > 1.0f) {
        return false;
    }
    
    // Calculate intersection point
    intersectX = posA->x + t * lineDir[0];
    intersectY = posA->y + t * lineDir[1];
    intersectZ = posA->z + t * lineDir[2];
    
    // Check if intersection is within distance threshold
    if (Math3D_Vec3fDistSq(posA, &(Vec3f){intersectX, intersectY, intersectZ}) > SQ(chkDist)) {
        return false;
    }
    
    // Check if point is inside triangle
    if (Math3D_PointInTriangle(&vtx0, &vtx1, &vtx2, intersectX, intersectY, intersectZ)) {
        planeIntersect->x = intersectX;
        planeIntersect->y = intersectY;
        planeIntersect->z = intersectZ;
        return true;
    }
    
    return false;
}
```

## Player Integration

### Player Collision Processing

**Player Scene Collision (`z_player.c:11063`):**
```c
void Player_ProcessSceneCollision(PlayState* play, Player* this) {
    static Vec3f sInteractWallCheckOffset = { 0.0f, 18.0f, 0.0f };
    u8 nextLedgeClimbType = PLAYER_LEDGE_CLIMB_NONE;
    CollisionPoly* floorPoly;
    f32 vWallCheckRadius;
    f32 vWallCheckHeight;
    f32 ceilingCheckHeight;
    u32 flags;
    
    sPrevFloorProperty = this->floorProperty;
    
    // Set collision check parameters based on player state
    if (this->stateFlags2 & PLAYER_STATE2_CRAWLING) {
        vWallCheckRadius = 10.0f;
        vWallCheckHeight = 15.0f;
        ceilingCheckHeight = 30.0f;
    } else {
        vWallCheckRadius = this->ageProperties->wallCheckRadius;
        vWallCheckHeight = 26.0f;
        ceilingCheckHeight = this->ageProperties->ceilingCheckHeight;
    }
    
    // Update background collision info
    Actor_UpdateBgCheckInfo(play, &this->actor, vWallCheckHeight, vWallCheckRadius, 
                           ceilingCheckHeight, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_1 | 
                           UPDBGCHECKINFO_FLAG_2 | UPDBGCHECKINFO_FLAG_3 | UPDBGCHECKINFO_FLAG_4);
    
    // Update floor properties
    if (this->actor.floorPoly != NULL) {
        this->floorProperty = SurfaceType_GetFloorProperty(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
        this->floorSfxOffset = SurfaceType_GetSfxOffset(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
    }
    
    // Handle conveyor belts
    if (this->actor.floorPoly != NULL) {
        if (SurfaceType_IsFloorConveyor(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId)) {
            u32 conveyorDirection = SurfaceType_GetConveyorDirection(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
            u32 conveyorSpeed = SurfaceType_GetConveyorSpeed(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
            
            // Apply conveyor movement
            f32 conveyorStrength = conveyorSpeed * 0.0025f;
            f32 conveyorAngle = conveyorDirection * (M_PI / 180.0f);
            
            this->actor.world.pos.x += Math_SinF(conveyorAngle) * conveyorStrength;
            this->actor.world.pos.z += Math_CosF(conveyorAngle) * conveyorStrength;
        }
    }
    
    // Handle exits and voids
    if (this->actor.floorPoly != NULL) {
        u32 exitIndex = SurfaceType_GetExitIndex(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
        if (exitIndex != 0) {
            // Trigger scene exit
            play->nextEntranceIndex = exitIndex;
            play->transitionTrigger = TRANS_TRIGGER_START;
        }
    }
    
    // Update lighting and reverb based on floor
    if (this->actor.floorPoly != NULL) {
        u32 lightSetting = SurfaceType_GetLightSetting(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
        u32 echo = SurfaceType_GetEcho(&play->colCtx, this->actor.floorPoly, this->actor.floorBgId);
        
        if (lightSetting != this->currentLightSetting) {
            this->currentLightSetting = lightSetting;
            // Update environment lighting
        }
        
        if (echo != this->currentEcho) {
            this->currentEcho = echo;
            Audio_SetEnvReverb(echo);
        }
    }
}
```

## Debugging and Visualization

### Collision Debug Drawing

**Debug Collision Visualization (`z_bgcheck.c:4462`):**
```c
void BgCheck_DrawDynaCollision(PlayState* play, CollisionContext* colCtx) {
    DynaCollisionContext* dyna = &colCtx->dyna;
    s32 i;
    
    // Draw all dynamic collision actors
    for (i = 0; i < dyna->bgActorCount; i++) {
        BgActor* bgActor = &dyna->bgActors[i];
        
        if (bgActor->actor != NULL) {
            BgCheck_DrawBgActor(play, colCtx, i);
        }
    }
}

void BgCheck_DrawBgActor(PlayState* play, CollisionContext* colCtx, s32 bgId) {
    DynaPolyActor* bgActor = DynaPoly_GetActor(colCtx, bgId);
    CollisionHeader* colHeader;
    
    if (bgActor != NULL) {
        colHeader = bgActor->colHeader;
        
        // Draw collision polygons
        BgCheck_DrawDynaPolyList(play, colCtx, &colCtx->dyna, 
                                &colCtx->dyna.dynaLookup.wall, 255, 0, 0);  // Red walls
        BgCheck_DrawDynaPolyList(play, colCtx, &colCtx->dyna, 
                                &colCtx->dyna.dynaLookup.floor, 0, 255, 0); // Green floors
        BgCheck_DrawDynaPolyList(play, colCtx, &colCtx->dyna, 
                                &colCtx->dyna.dynaLookup.ceiling, 0, 0, 255); // Blue ceilings
    }
}
```

### Collision Statistics

**Collision Performance Monitoring (`z_bgcheck.c:100`):**
```c
void BgCheck_PosErrorCheck(Vec3f* pos, char* file, s32 line) {
    if (!(-32000.0f <= pos->x && pos->x <= 32000.0f) ||
        !(-32000.0f <= pos->y && pos->y <= 32000.0f) ||
        !(-32000.0f <= pos->z && pos->z <= 32000.0f)) {
        
        PRINTF_COLOR_RED();
        PRINTF("BgCheck_PosErrorCheck: Position out of bounds!\n");
        PRINTF("Position: (%f, %f, %f)\n", pos->x, pos->y, pos->z);
        PRINTF("File: %s, Line: %d\n", file, line);
        PRINTF_RST();
    }
}
```

## Practical Implications for Modding

### Custom Collision Implementation

**Adding Custom Collision Types:**
1. **Surface Type Extension**: Extend surface type definitions
2. **Custom Materials**: Add new material types and properties
3. **Collision Callbacks**: Implement custom collision response functions
4. **Dynamic Collision**: Create moving collision objects

**Example Custom Collision System:**
```c
// Custom surface type handler
void CustomSurface_ProcessCollision(PlayState* play, Actor* actor, CollisionPoly* poly, s32 bgId) {
    u32 customType = SurfaceType_GetCustomType(&play->colCtx, poly, bgId);
    
    switch (customType) {
        case CUSTOM_SURFACE_ICE:
            // Apply ice physics
            actor->speed *= 1.1f;  // Reduce friction
            break;
            
        case CUSTOM_SURFACE_BOUNCE:
            // Apply bounce effect
            if (actor->velocity.y < 0) {
                actor->velocity.y = -actor->velocity.y * 0.8f;
            }
            break;
            
        case CUSTOM_SURFACE_DAMAGE:
            // Apply damage over time
            if (actor->category == ACTORCAT_PLAYER) {
                Actor_ApplyDamage(actor);
            }
            break;
    }
}

// Custom collision detection
s32 CustomCollision_CheckSpecialGeometry(PlayState* play, Vec3f* pos, f32 radius) {
    // Check against custom collision geometry
    for (s32 i = 0; i < sCustomCollisionCount; i++) {
        CustomCollisionEntry* entry = &sCustomCollisionTable[i];
        
        if (Math3D_SphVsSph(pos, radius, &entry->center, entry->radius)) {
            // Handle custom collision
            return entry->responseType;
        }
    }
    
    return COLLISION_NONE;
}
```

### Performance Optimization

**Collision Optimization Strategies:**
1. **Spatial Partitioning**: Use appropriate subdivision sizes
2. **Early Rejection**: Implement efficient bounds checking
3. **LOD Systems**: Simplify collision at distance
4. **Selective Updates**: Only update necessary collision

**Example Optimization:**
```c
// Optimized collision checking
void OptimizedCollision_Update(PlayState* play, Actor* actor) {
    // Skip collision for distant actors
    f32 distanceToPlayer = Math3D_Vec3fDistSq(&actor->world.pos, &GET_PLAYER(play)->actor.world.pos);
    if (distanceToPlayer > SQ(1000.0f)) {
        return;
    }
    
    // Use simplified collision for medium distance
    if (distanceToPlayer > SQ(500.0f)) {
        // Use sphere-only collision
        CollisionCheck_SetOC(play, &play->colChkCtx, &actor->collider.base);
        return;
    }
    
    // Full collision for close actors
    CollisionCheck_SetAC(play, &play->colChkCtx, &actor->collider.base);
    CollisionCheck_SetOC(play, &play->colChkCtx, &actor->collider.base);
    
    // Update background collision
    Actor_UpdateBgCheckInfo(play, actor, 26.0f, 18.0f, 60.0f, UPDBGCHECKINFO_FLAG_0 | UPDBGCHECKINFO_FLAG_2);
}
```

### Custom Collision Shapes

**Adding New Collision Shapes:**
1. **Shape Definition**: Define new collision shape types
2. **Intersection Tests**: Implement shape-vs-shape tests
3. **Integration**: Add to collision system framework
4. **Optimization**: Implement efficient algorithms

**Example Custom Shape:**
```c
// Custom capsule collision shape
typedef struct ColliderCapsule {
    Collider base;
    ColliderCapsuleElement elem;
    CapsuleDim dim;
} ColliderCapsule;

// Capsule vs capsule collision test
s32 CollisionCheck_CapsuleVsCapsule(ColliderCapsule* capsule1, ColliderCapsule* capsule2) {
    f32 distance = Math3D_CapsuleVsCapsule(&capsule1->dim, &capsule2->dim);
    return distance < 0.0f;
}

// Register custom collision shape
void CollisionCheck_RegisterCustomShape(void) {
    sCustomCollisionFuncs[COLSHAPE_CAPSULE][COLSHAPE_CAPSULE] = CollisionCheck_CapsuleVsCapsule;
    sCustomCollisionFuncs[COLSHAPE_CAPSULE][COLSHAPE_CYLINDER] = CollisionCheck_CapsuleVsCylinder;
    sCustomCollisionFuncs[COLSHAPE_CAPSULE][COLSHAPE_JNTSPH] = CollisionCheck_CapsuleVsJntSph;
}
```

## Common Issues and Solutions

### Collision Debugging

**Debug Collision Issues:**
1. **Visualization**: Use debug rendering to see collision geometry
2. **Logging**: Add debug output for collision events
3. **Performance**: Profile collision performance
4. **Validation**: Check for common collision errors

**Common Problems:**
- **Collision Gaps**: Insufficient subdivision or polygon gaps
- **Performance Issues**: Too many collision checks or inefficient algorithms
- **Floating Point Errors**: Precision issues with collision calculations
- **Memory Issues**: Collision data memory leaks or corruption

### Best Practices

**Collision System Guidelines:**
1. **Efficient Algorithms**: Use spatial partitioning appropriately
2. **Error Handling**: Validate collision parameters
3. **Performance**: Monitor collision performance
4. **Testing**: Comprehensive collision testing

**Code Organization:**
- **Modular Design**: Separate collision types and systems
- **Clear Interfaces**: Well-defined collision APIs
- **Documentation**: Document collision behavior
- **Testing**: Automated collision testing

## Conclusion

The OOT collision detection system represents a sophisticated approach to 3D collision detection that balances accuracy, performance, and flexibility. The multi-layered architecture handles everything from basic movement collision to complex interactive surfaces through efficient spatial subdivision and optimized algorithms.

Key architectural strengths include:
- **Multi-layered Architecture**: Separate systems for different collision types
- **Spatial Optimization**: Efficient subdivision for performance
- **Flexible Surface System**: Rich material and property system
- **Integration**: Seamless integration with game systems
- **Performance**: Optimized for N64 hardware constraints
- **Extensibility**: Flexible framework for custom collision types

Understanding this system is essential for effective OOT modding, as collision detection affects virtually every aspect of gameplay. The careful balance between accuracy and performance demonstrates expert engineering that continues to serve as a reference for modern game collision systems. 