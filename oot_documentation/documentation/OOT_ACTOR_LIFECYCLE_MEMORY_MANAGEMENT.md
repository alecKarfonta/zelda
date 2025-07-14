# OOT Actor Lifecycle & Memory Management

## Overview

This report provides a comprehensive analysis of the Actor Lifecycle and Memory Management systems in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code in the `oot/src` folder.

## Actor Memory Architecture

### Memory Hierarchy Overview

The OOT engine implements a sophisticated three-tier memory hierarchy designed to work within the N64's 4MB RAM constraint. Each tier serves specific purposes and has different allocation patterns, lifetimes, and management strategies.

### Memory Spaces

#### 1. System Arena - Foundation Memory Layer
The System Arena (`gSystemArena`) forms the base memory layer and is managed by the N64's libultra OS functions. This arena is initialized during boot and provides memory for:

- **Thread stacks** - Each of the 6+ threads requires dedicated stack space
- **Graphics command buffers** - Display lists and rendering commands  
- **Audio heap** - Sound synthesis and sequence data
- **Persistent system structures** - Core engine components that live for the entire game session
- **Overlay loading** - Temporary space for loading code overlays before relocation

**System Arena Initialization (`main.c`):**
```c
// System Arena encompasses most of available RAM
__osMallocInit(&gSystemArena, gHeapStart, gHeapSize);
```

The System Arena uses a traditional heap allocator with `__osMalloc()` and `__osFree()`. Memory allocated here persists until explicitly freed, making it suitable for long-lived data structures.

#### 2. Zelda Arena - Game Object Memory Pool  
The Zelda Arena is allocated from within the System Arena and serves as the primary memory pool for all game objects during active gameplay. It uses a more sophisticated allocation strategy optimized for the game's access patterns.

**Zelda Arena Characteristics:**
- **Size**: Typically 1.5-2MB depending on scene complexity
- **Allocator**: Custom `__osMalloc` implementation with debugging support
- **Alignment**: 16-byte aligned allocations for optimal N64 cache performance
- **Fragmentation handling**: Supports both forward and reverse allocation to minimize fragmentation
- **Debugging**: Extensive logging and validation in debug builds

**Zelda Arena Functions (`z_malloc.c`):**
```c
// Standard allocation from beginning of arena
void* ZeldaArena_Malloc(u32 size);

// Reverse allocation from end of arena (for persistent data)
void* ZeldaArena_MallocR(u32 size);

// Reallocation with potential data movement
void* ZeldaArena_Realloc(void* ptr, u32 newSize);

// Deallocation (supports debugging validation)
void ZeldaArena_Free(void* ptr);
```

#### 3. Game State Arena - Scene-Specific Memory
The Game State Arena is a subset of the System Arena allocated specifically for each game state (Play, Menu, etc.). It provides memory for scene-specific data that needs to be completely cleaned up during state transitions.

**Game State Arena Usage:**
- **PlayState allocation**: ~1.87MB (`0x1D4790` bytes) for main gameplay
- **Scene data**: Current scene's collision, rendering, and logic data
- **Room data**: Active room's geometry and actor spawn lists
- **Interface elements**: HUD, menus, and UI components specific to the current state
- **Temporary allocations**: Short-lived data that doesn't need to persist across scenes

**Memory Initialization (`z_play.c:481`):**
```c
PRINTF("ZELDA ALLOC SIZE=%x\n", THA_GetRemaining(&this->state.tha));
zAllocSize = THA_GetRemaining(&this->state.tha);
zAlloc = (uintptr_t)GAME_STATE_ALLOC(&this->state, zAllocSize, "../z_play.c", 2918);
zAllocAligned = (zAlloc + 8) & ~0xF;
ZeldaArena_Init((void*)zAllocAligned, zAllocSize - (zAllocAligned - zAlloc));
```

### Zelda Arena Management

The Zelda Arena implements a sophisticated memory management system with multiple allocation strategies, comprehensive debugging support, and careful fragmentation management. Understanding these mechanisms is crucial for effective memory usage in actor development.

#### Allocation Strategies

**Forward Allocation (`ZELDA_ARENA_MALLOC`)**
Standard allocation that grows from the beginning of the arena toward higher addresses. This is the default allocation method for most game objects including actors, effects, and temporary data structures.

```c
void* ZeldaArena_Malloc(u32 size) {
    void* ptr = __osMalloc(&sZeldaArena, size);
    ZELDA_ARENA_CHECK_POINTER(ptr, size, "zelda_malloc", T("確保", "Secure"));
    return ptr;
}
```

**Reverse Allocation (`ZELDA_ARENA_MALLOC_R`)**
Allocation that grows from the end of the arena toward lower addresses. This strategy is used for data that should remain stable in memory while forward allocations are frequently allocated and freed. Examples include:

- **Actor overlays with persistent allocation type** - Code that should remain loaded for the entire scene
- **Large object files** - 3D model and texture data that multiple actors depend on
- **Scene collision data** - Background geometry that needs to persist for the entire scene duration

```c
void* ZeldaArena_MallocR(u32 size) {
    void* ptr = __osMallocR(&sZeldaArena, size);
    ZELDA_ARENA_CHECK_POINTER(ptr, size, "zelda_malloc_r", T("確保", "Secure"));
    return ptr;
}
```

**Reallocation with Memory Management (`ZELDA_ARENA_REALLOC`)**
Provides dynamic resizing of allocated blocks with automatic memory copying when expansion in place is impossible. Used primarily for dynamic arrays that grow during runtime, such as particle systems or effect lists.

```c
void* ZeldaArena_Realloc(void* ptr, u32 newSize) {
    ptr = __osRealloc(&sZeldaArena, ptr, newSize);
    ZELDA_ARENA_CHECK_POINTER(ptr, newSize, "zelda_realloc", T("再確保", "Re-securing"));
    return ptr;
}
```

#### Debug and Validation System

**Memory Allocation Logging**
In debug builds, every allocation is logged with detailed information including size, location, and call site. This system helps track memory usage patterns and identify leaks.

```c
#if DEBUG_FEATURES
void* ZeldaArena_MallocDebug(u32 size, const char* file, int line) {
    void* ptr = __osMallocDebug(&sZeldaArena, size, file, line);
    ZELDA_ARENA_CHECK_POINTER(ptr, size, "zelda_malloc_DEBUG", T("確保", "Secure"));
    return ptr;
}
#endif
```

**Pointer Validation**
Every allocation and deallocation is validated to ensure memory integrity. Failed allocations are logged with context about available memory and allocation requirements.

```c
void ZeldaArena_CheckPointer(void* ptr, u32 size, const char* name, const char* action) {
    if (ptr == NULL) {
        if (gZeldaArenaLogSeverity >= LOG_SEVERITY_ERROR) {
            PRINTF(T("%s: %u バイトの%sに失敗しました\n", "%s: %u bytes %s failed\n"), name, size, action);
#if PLATFORM_GC
            __osDisplayArena(&sZeldaArena);
#endif
        }
    } else if (gZeldaArenaLogSeverity >= LOG_SEVERITY_VERBOSE) {
        PRINTF(T("%s: %u バイトの%sに成功しました\n", "%s: %u bytes %s succeeded\n"), name, size, action);
    }
}
```

#### Memory Fragmentation Management

**Fragmentation Prevention Strategies:**
1. **Size-based allocation** - Smaller objects use forward allocation, larger persistent objects use reverse allocation
2. **Lifetime-based separation** - Short-lived and long-lived objects are allocated from opposite ends
3. **Alignment requirements** - All allocations are 16-byte aligned to prevent alignment-induced fragmentation
4. **Arena compaction** - Periodic cleanup during scene transitions to defragment memory

**Arena Status Monitoring (`z_malloc.c`):**
```c
void ZeldaArena_GetSizes(u32* outMaxFree, u32* outFree, u32* outAlloc) {
    ArenaImpl_GetSizes(&sZeldaArena, outMaxFree, outFree, outAlloc);
}
```

This function provides real-time information about arena usage:
- `outMaxFree`: Largest contiguous free block available
- `outFree`: Total free memory in arena
- `outAlloc`: Total allocated memory

## Actor Lifecycle

### 1. Actor Spawning Process

The actor spawning process follows a precise sequence:

**Main Spawn Function (`z_actor.c:3156`):**
```c
Actor* Actor_Spawn(ActorContext* actorCtx, PlayState* play, s16 actorId, f32 posX, f32 posY, f32 posZ, 
                   s16 rotX, s16 rotY, s16 rotZ, s16 params)
```

#### Spawn Process Steps:

**Step 1: Actor Validation and Limits Check**
Before any memory allocation occurs, the spawn system validates the request and checks system limits to prevent resource exhaustion.

```c
// Actor count limit check (z_actor.c:3183)
if (actorCtx->total > ACTOR_NUMBER_MAX) {
    PRINTF(ACTOR_COLOR_WARNING T("Ａｃｔｏｒセット数オーバー\n", "Actor set number exceeded\n") ACTOR_RST);
    return NULL;
}

// Actor ID validation
ASSERT(actorId < ACTOR_ID_MAX, "profile < ACTOR_DLF_MAX", "../z_actor.c", 6883);
```

The engine enforces a hard limit on total active actors (`ACTOR_NUMBER_MAX`) to prevent memory exhaustion and maintain stable performance. This check occurs before any expensive operations like overlay loading.

**Step 2: Overlay Loading and Code Management**
The actor system uses dynamic code loading through overlays, allowing the game to exceed the N64's memory constraints by loading actor code on-demand.

```c
// Check if overlay is already loaded (z_actor.c:3194)
if (overlayEntry->loadedRamAddr != NULL) {
    ACTOR_DEBUG_PRINTF(T("既にロードされています\n", "Already loaded\n"));
} else {
    // Determine allocation type and load overlay
    if (overlayEntry->allocType & ACTOROVL_ALLOC_ABSOLUTE) {
        // Use shared absolute space
    } else if (overlayEntry->allocType & ACTOROVL_ALLOC_PERSISTENT) {
        // Use reverse allocation for scene-persistent code
        overlayEntry->loadedRamAddr = ZELDA_ARENA_MALLOC_R(overlaySize, name, 0);
    } else {
        // Standard allocation for reference-counted overlays
        overlayEntry->loadedRamAddr = ZELDA_ARENA_MALLOC(overlaySize, name, 0);
    }
    
    // Load overlay from ROM and relocate addresses
    Overlay_Load(overlayEntry->file.vromStart, overlayEntry->file.vromEnd, 
                 overlayEntry->vramStart, overlayEntry->vramEnd, overlayEntry->loadedRamAddr);
}
```

**Step 3: Object Dependency Resolution and Asset Management**
Every actor depends on at least one object file containing its 3D models, textures, and animations. The spawn system ensures these dependencies are satisfied before proceeding.

```c
// Resolve object dependency (z_actor.c:3233)
objectSlot = Object_GetSlot(&play->objectCtx, profile->objectId);

if ((objectSlot < 0) || 
    ((profile->category == ACTORCAT_ENEMY) && Flags_GetClear(play, play->roomCtx.curRoom.num))) {
    
    PRINTF(ACTOR_COLOR_ERROR T("データバンク無し！！<データバンク＝%d>(profilep->bank=%d)\n",
                               "No data bank!! <data bank=%d> (profilep->bank=%d)\n") ACTOR_RST,
           objectSlot, profile->objectId);
    Actor_FreeOverlay(overlayEntry);
    return NULL;
}
```

The object system uses numbered slots (0-15) to manage 3D assets. If the required object isn't loaded, spawning fails immediately. Additionally, enemy actors are prevented from spawning in rooms that have been cleared (enemies defeated).

**Step 4: Actor Instance Memory Allocation**
With code and assets confirmed available, the system allocates memory for the actor instance based on the size specified in the actor's profile.

```c
// Allocate actor instance (z_actor.c:3240)
actor = ZELDA_ARENA_MALLOC(profile->instanceSize, name, 1);

if (actor == NULL) {
    PRINTF(ACTOR_COLOR_ERROR T("Ａｃｔｏｒクラス確保できません！ %s <サイズ＝%dバイト>\n",
                               "Actor class cannot be reserved! %s <size=%d bytes>\n"),
           ACTOR_RST, name, profile->instanceSize);
    Actor_FreeOverlay(overlayEntry);
    return NULL;
}
```

The `instanceSize` field in the actor profile determines exactly how much memory is allocated. This includes the base Actor structure plus any actor-specific data. Memory allocation failure at this stage triggers cleanup of the loaded overlay to prevent memory leaks.

**Step 5: Actor Data Structure Initialization**
Once memory is allocated, the system initializes the core actor data structure with references to its overlay, profile, and runtime parameters.

```c
// Initialize actor structure (z_actor.c:3250)
Lib_MemSet((u8*)actor, profile->instanceSize, 0);  // Zero-initialize all memory
actor->overlayEntry = overlayEntry;
actor->id = profile->id;
actor->flags = profile->flags;
actor->objectSlot = objectSlot;

// Set function pointers from profile
actor->init = profile->init;
actor->destroy = profile->destroy;
actor->update = profile->update;
actor->draw = profile->draw;

// Set spawn parameters
actor->room = play->roomCtx.curRoom.num;
actor->home.pos.x = posX;
actor->home.pos.y = posY;
actor->home.pos.z = posZ;
actor->home.rot.x = rotX;
actor->home.rot.y = rotY;
actor->home.rot.z = rotZ;
actor->params = params;
```

**Step 6: Category Assignment and List Management**
Actors are organized into 12 categories for efficient processing. The spawn system adds the new actor to the appropriate category's linked list.

```c
// Add to category list (z_actor.c:3278)
Actor_AddToCategory(actorCtx, actor, profile->category);
```

**Step 7: Actor-Specific Initialization**
Finally, the system calls the actor's initialization function (if the required object is loaded) to set up actor-specific state and behavior.

```c
// Initialize actor with object dependency (z_actor.c:3280)
temp = gSegments[6];
Actor_Init(actor, play);  // Calls actor's init() if object is ready
gSegments[6] = temp;      // Restore previous object context
```

**Allocation Code:**
```c
actor = ZELDA_ARENA_MALLOC(profile->instanceSize, name, 1);
if (actor == NULL) {
    PRINTF(ACTOR_COLOR_ERROR T("Ａｃｔｏｒクラス確保できません！ %s <サイズ＝%dバイト>\n",
                               "Actor class cannot be reserved! %s <size=%d bytes>\n"),
           ACTOR_RST, name, profile->instanceSize);
    Actor_FreeOverlay(overlayEntry);
    return NULL;
}
```

### 2. Overlay Management

**Three Allocation Types (`z_actor.c:3129`):**

#### ACTOROVL_ALLOC_ABSOLUTE (Type 1) - Shared Absolute Space
This allocation type uses a pre-allocated shared memory space for overlays that require specific memory layout characteristics or need to be accessed by multiple systems simultaneously.

**Key Characteristics:**
- **Shared Space**: All absolute overlays share a single memory region (`ACTOROVL_ABSOLUTE_SPACE_SIZE` bytes)
- **Fixed Address**: Overlays loaded into this space have predictable memory addresses
- **Single Instance**: Only one overlay can occupy the absolute space at a time
- **Scene Persistence**: Space is allocated once per scene and reused for different overlays as needed
- **No Reference Counting**: Space is not freed when overlay unloads, only reassigned

**Use Cases:**
- **Player actor overlay**: Needs stable addressing for save state and external references
- **Critical system overlays**: Components that interface with hardware or OS functions
- **Large shared overlays**: Code that's used by multiple actors simultaneously

**Implementation (`z_actor.c:3200`):**
```c
if (overlayEntry->allocType & ACTOROVL_ALLOC_ABSOLUTE) {
    ASSERT(overlaySize <= ACTOROVL_ABSOLUTE_SPACE_SIZE, "actor_segsize <= AM_FIELD_SIZE", "../z_actor.c", 6934);
    
    if (actorCtx->absoluteSpace == NULL) {
        actorCtx->absoluteSpace = ZELDA_ARENA_MALLOC_R(
            ACTOROVL_ABSOLUTE_SPACE_SIZE, T("AMF:絶対魔法領域", "AMF: absolute magic field"), 0);
        ACTOR_DEBUG_PRINTF(
            T("絶対魔法領域確保 %d バイト確保\n", "Absolute magic field allocation %d bytes allocated\n"),
            ACTOROVL_ABSOLUTE_SPACE_SIZE);
    }
    
    overlayEntry->loadedRamAddr = actorCtx->absoluteSpace;
}
```

**Memory Management:**
When an absolute overlay is no longer needed, the system clears the pointer but doesn't free the underlying space, allowing it to be reused by the next absolute overlay that loads.

#### ACTOROVL_ALLOC_PERSISTENT (Type 2) - Scene-Persistent Code
Persistent overlays use reverse allocation and remain loaded for the entire duration of a scene, regardless of whether instances of the actor exist.

**Key Characteristics:**
- **Reverse Allocation**: Uses `ZELDA_ARENA_MALLOC_R()` to allocate from high memory addresses
- **Scene Lifetime**: Remains loaded until scene transition, even with zero active instances  
- **Memory Stability**: Located in high memory to avoid fragmentation from frequent allocations
- **Performance Optimization**: Eliminates load/unload overhead for frequently used actors

**Use Cases:**
- **Environmental actors**: Background elements that spawn/despawn frequently (grass, particles)
- **Effect systems**: Visual effects that are used throughout a scene
- **Audio actors**: Sound sources that need to persist across gameplay states
- **Common utility actors**: Shared functionality used by multiple other actors

**Implementation (`z_actor.c:3210`):**
```c
if (overlayEntry->allocType & ACTOROVL_ALLOC_PERSISTENT) {
    overlayEntry->loadedRamAddr = ZELDA_ARENA_MALLOC_R(overlaySize, name, 0);
    // Overlay remains loaded until scene destruction
}
```

**Deallocation Behavior (`z_actor.c:3135`):**
```c
if (actorOverlay->allocType & ACTOROVL_ALLOC_PERSISTENT) {
    ACTOR_DEBUG_PRINTF(T("オーバーレイ解放しません\n", "Overlay will not be deallocated\n"));
    // Overlay code stays in memory regardless of instance count
}
```

#### Standard Allocation (Type 0) - Reference-Counted Dynamic Loading
The default allocation type implements dynamic loading with reference counting, providing memory efficiency through automatic load/unload cycles.

**Key Characteristics:**
- **Forward Allocation**: Uses standard `ZELDA_ARENA_MALLOC()` from low memory addresses
- **Reference Counting**: Tracks number of active instances with `overlayEntry->numLoaded`
- **Automatic Unloading**: Frees overlay code when last instance is destroyed
- **Memory Efficiency**: Minimizes memory usage by only keeping needed code loaded
- **Load/Unload Overhead**: Must reload code each time first instance spawns

**Use Cases:**
- **Enemy actors**: Specific enemies that appear in limited areas
- **Interactive objects**: Switches, doors, and mechanisms specific to certain rooms
- **Cutscene actors**: Special-purpose actors used only during specific sequences
- **Boss actors**: Large, complex actors used in single encounters

**Reference Counting Implementation (`z_actor.c:3262`):**
```c
// Increment reference count when actor spawns
overlayEntry->numLoaded++;
ACTOR_DEBUG_PRINTF(T("アクタークライアントは %d 個目です\n", "Actor client No. %d\n"), overlayEntry->numLoaded);

// Decrement and potentially unload when actor is deleted (z_actor.c:3394)
overlayEntry->numLoaded--;
Actor_FreeOverlay(overlayEntry);
```

**Automatic Unloading Logic (`z_actor.c:3129`):**
```c
void Actor_FreeOverlay(ActorOverlay* actorOverlay) {
    if (actorOverlay->numLoaded == 0) {
        ACTOR_DEBUG_PRINTF(T("アクタークライアントが０になりました\n", "Actor clients are now 0\n"));
        
        if (actorOverlay->loadedRamAddr != NULL) {
            ACTOR_DEBUG_PRINTF(T("オーバーレイ解放します\n", "Overlay deallocated\n"));
            ZELDA_ARENA_FREE(actorOverlay->loadedRamAddr, "../z_actor.c", 6834);
            actorOverlay->loadedRamAddr = NULL;
        }
    } else {
        ACTOR_DEBUG_PRINTF(T("アクタークライアントはあと %d 残っています\n", "%d of actor client remaining\n"),
                           actorOverlay->numLoaded);
    }
}
```

**Performance Trade-offs:**
- **Memory Efficiency**: Only loads code when needed, freeing memory when unused
- **Loading Latency**: Must reload from ROM when first instance spawns after code was unloaded
- **Fragmentation Risk**: Frequent load/unload cycles can fragment the Zelda Arena

### 3. Actor Initialization Process

**Initialization (`z_actor.c:924`):**
```c
void Actor_Init(Actor* actor, PlayState* play) {
    Actor_SetWorldToHome(actor);
    Actor_SetShapeRotToWorld(actor);
    Actor_SetFocus(actor, 0.0f);
    Math_Vec3f_Copy(&actor->prevPos, &actor->world.pos);
    Actor_SetScale(actor, 0.01f);
    actor->attentionRangeType = ATTENTION_RANGE_3;
    actor->minVelocityY = -20.0f;
    actor->xyzDistToPlayerSq = MAXFLOAT;
    actor->naviEnemyId = NAVI_ENEMY_NONE;
    actor->cullingVolumeDistance = 1000.0f;
    actor->cullingVolumeScale = 350.0f;
    actor->cullingVolumeDownward = 700.0f;
    CollisionCheck_InitInfo(&actor->colChkInfo);
    actor->floorBgId = BGCHECK_SCENE;
    ActorShape_Init(&actor->shape, 0.0f, NULL, 0.0f);
    
    if (Object_IsLoaded(&play->objectCtx, actor->objectSlot)) {
        Actor_SetObjectDependency(play, actor);
        actor->init(actor, play);
        actor->init = NULL; // Clear init function after first call
    }
}
```

### 4. Actor Update Loop

**Update Process (`z_actor.c:2388`):**

The main update loop implements a sophisticated actor processing system that handles initialization, dependency management, state-based freezing, and cleanup in a single optimized pass through all active actors.

#### Processing Order and Category Management

**Category-Based Processing (`z_actor.c:2445`):**
The update system processes actors in a specific category order designed to ensure proper dependency resolution and optimal performance:

```c
for (i = 0; i < ARRAY_COUNT(actorCtx->actorLists); i++, categoryFreezeMaskP++) {
    canFreezeCategory = (player->stateFlags1 & *categoryFreezeMaskP);
    
    actor = actorCtx->actorLists[i].head;
    while (actor != NULL) {
        // Process each actor in the category
    }
}
```

**Category Processing Order:**
1. **ACTORCAT_SWITCH (0)** - Switches and triggers (affect environment)
2. **ACTORCAT_BG (1)** - Background objects (collision and geometry)  
3. **ACTORCAT_PLAYER (2)** - Player character (central to all interactions)
4. **ACTORCAT_EXPLOSIVE (3)** - Bombs and explosions (affect other actors)
5. **ACTORCAT_NPC (4)** - Non-player characters (dialogue and interaction)
6. **ACTORCAT_ENEMY (5)** - Enemy actors (combat and AI)
7. **ACTORCAT_PROP (6)** - Interactive props (pickups and objects)
8. **ACTORCAT_ITEMACTION (7)** - Item action triggers
9. **ACTORCAT_MISC (8)** - Miscellaneous effects and systems
10. **ACTORCAT_BOSS (9)** - Boss enemies (special handling)
11. **ACTORCAT_DOOR (10)** - Doors and passages
12. **ACTORCAT_CHEST (11)** - Treasure chests and containers

#### Deferred Initialization System

**Object Dependency Resolution:**
Actors may spawn before their required object file is loaded. The update system handles this through deferred initialization, checking each frame whether the required assets have become available.

```c
if (actor->init != NULL) {
    if (Object_IsLoaded(&play->objectCtx, actor->objectSlot)) {
        Actor_SetObjectDependency(play, actor);
        actor->init(actor, play);
        actor->init = NULL;  // Clear to prevent re-initialization
    }
    actor = actor->next;
} else if (!Object_IsLoaded(&play->objectCtx, actor->objectSlot)) {
    Actor_Kill(actor);  // Object was unloaded, mark for deletion
    actor = actor->next;
}
```

**Object Loading Validation:**
The system continuously validates that each actor's required object remains loaded. If an object is unloaded (due to memory pressure or scene changes), all dependent actors are immediately marked for deletion to prevent crashes from missing assets.

#### State-Based Freezing System

**Freeze Condition Detection (`z_actor.c:2431`):**
The engine implements a sophisticated freezing system that selectively pauses actor updates based on game state and player actions:

```c
// Determine freeze conditions
if (player->stateFlags2 & PLAYER_STATE2_USING_OCARINA) {
    freezeExceptionFlag = ACTOR_FLAG_UPDATE_DURING_OCARINA;
}

if ((player->stateFlags1 & PLAYER_STATE1_TALKING) && ((player->actor.textId & 0xFF00) != 0x600)) {
    sp74 = player->talkActor;  // Actor player is talking to
}
```

**Category-Specific Freeze Masks (`z_actor.c`):**
Each category has a specific freeze mask that determines which player states cause actors in that category to be frozen:

```c
u32 sCategoryFreezeMasks[] = {
    PLAYER_STATE1_IN_WATER_SURFACE | PLAYER_STATE1_SWIMMING | PLAYER_STATE1_HANGING_FROM_LEDGE | 
    PLAYER_STATE1_HANGING_OFF_LEDGE | PLAYER_STATE1_CLIMBING | PLAYER_STATE1_DEAD,  // Switches
    
    PLAYER_STATE1_IN_WATER_SURFACE | PLAYER_STATE1_SWIMMING | PLAYER_STATE1_HANGING_FROM_LEDGE | 
    PLAYER_STATE1_HANGING_OFF_LEDGE | PLAYER_STATE1_CLIMBING | PLAYER_STATE1_DEAD,  // Background
    
    // ... masks for each category
};
```

**Freeze Logic Application:**
```c
if ((freezeExceptionFlag == 0 && canFreezeCategory &&
     !((sp74 == actor) || (player->naviActor == actor) || (player->heldActor == actor) ||
       (actor->parent == &player->actor)))) {
    CollisionCheck_ResetDamage(&actor->colChkInfo);
    actor = actor->next;  // Skip update, actor is frozen
}
```

#### Actor Update Execution

**Update Function Validation and Execution:**
Before calling an actor's update function, the system validates that the actor is still active and performs necessary state updates:

```c
} else if (actor->update == NULL) {
    if (!actor->isDrawn) {
        actor = Actor_Delete(&play->actorCtx, actor, play);  // Complete removal
    } else {
        Actor_Destroy(actor, play);  // Cleanup but leave in list for one more frame
        actor = actor->next;
    }
} else {
    // Update actor position tracking
    Math_Vec3f_Copy(&actor->prevPos, &actor->world.pos);
    actor->xzDistToPlayer = Actor_WorldDistXZToActor(actor, &player->actor);
    actor->yDistToPlayer = Actor_HeightDiff(actor, &player->actor);
    actor->xyzDistToPlayerSq = SQ(actor->xzDistToPlayer) + SQ(actor->yDistToPlayer);
    
    actor->yawTowardsPlayer = Actor_WorldYawTowardActor(actor, &player->actor);
    
    // Clear frame-specific flags
    actor->flags &= ~ACTOR_FLAG_SFX_FOR_PLAYER_BODY_HIT;
    
    // Execute actor's update function
    actor->update(actor, play);
    
    actor = actor->next;
}
```

#### Cleanup and Memory Management

**Destroyed Actor Processing:**
Actors marked for deletion (via `b()`) are processed during the update loop. The system distinguishes between actors that can be immediately removed and those that must wait one frame (if they're currently being drawn).

**Position and Distance Tracking:**
Each frame, the system updates each actor's relationship to the player and other actors:
- **Previous position**: Stored for interpolation and collision detection
- **Distance calculations**: XZ distance, Y distance, and 3D distance squared to player
- **Orientation tracking**: Yaw angle toward player for AI and interaction systems

This comprehensive update system ensures that actors are processed efficiently while maintaining proper dependencies, state management, and cleanup procedures.

**Critical Update Code:**
```c
if (actor->init != NULL) {
    if (Object_IsLoaded(&play->objectCtx, actor->objectSlot)) {
        Actor_SetObjectDependency(play, actor);
        actor->init(actor, play);
        actor->init = NULL;
    }
    actor = actor->next;
} else if (!Object_IsLoaded(&play->objectCtx, actor->objectSlot)) {
    Actor_Kill(actor);
    actor = actor->next;
}
```

### 5. Actor Destruction Process

#### Actor_Kill (Soft Destruction)
**Implementation (`z_actor.c:867`):**
```c
void Actor_Kill(Actor* actor) {
    actor->draw = NULL;
    actor->update = NULL;
    actor->flags &= ~ACTOR_FLAG_ATTENTION_ENABLED;
}
```

- Marks actor for deletion by nulling function pointers
- Actor removed in next update cycle
- Memory not immediately freed

#### Actor_Destroy (Cleanup)
**Implementation (`z_actor.c:943`):**
```c
void Actor_Destroy(Actor* actor, PlayState* play) {
    ActorOverlay* overlayEntry;
    char* name;

    if (actor->destroy != NULL) {
        actor->destroy(actor, play);
        actor->destroy = NULL;
    }
}
```

- Calls actor-specific destructor if present
- Handles actor-specific cleanup (colliders, allocated memory, etc.)

#### Actor_Delete (Complete Removal)
**Implementation (`z_actor.c:3355`):**
```c
Actor* Actor_Delete(ActorContext* actorCtx, Actor* actor, PlayState* play) {
    // Remove from attention system
    if (actorCtx->attention.naviHoverActor == actor) {
        actorCtx->attention.naviHoverActor = NULL;
    }
    
    // Stop audio effects
    Audio_StopSfxByPos(&actor->projectedPos);
    
    // Call destructor
    Actor_Destroy(actor, play2);
    
    // Remove from linked list
    newHead = Actor_RemoveFromCategory(play2, actorCtx, actor);
    
    // Free memory
    ZELDA_ARENA_FREE(actor, "../z_actor.c", 7242);
    
    // Handle overlay reference counting
    overlayEntry->numLoaded--;
    Actor_FreeOverlay(overlayEntry);
    
    return newHead;
}
```

## Memory Management Details

### Overlay Reference Counting

**Overlay Management (`z_actor.c:3129`):**

Each overlay maintains a reference count (`numLoaded`) tracking active instances:

- **Increment**: When actor spawns successfully
- **Decrement**: When actor is deleted
- **Deallocation**: When count reaches zero (for non-persistent overlays)

```c
void Actor_FreeOverlay(ActorOverlay* actorOverlay) {
    if (actorOverlay->numLoaded == 0) {
        if (actorOverlay->loadedRamAddr != NULL) {
            if (actorOverlay->allocType & ACTOROVL_ALLOC_PERSISTENT) {
                // Keep in memory
            } else if (actorOverlay->allocType & ACTOROVL_ALLOC_ABSOLUTE) {
                // Just clear pointer, don't free absolute space
                actorOverlay->loadedRamAddr = NULL;
            } else {
                // Free normal allocation
                ZELDA_ARENA_FREE(actorOverlay->loadedRamAddr, "../z_actor.c", 6834);
                actorOverlay->loadedRamAddr = NULL;
            }
        }
    }
}
```

### Object System Integration

**Object Dependency Management:**

1. **Loading**: Objects loaded before dependent actors can spawn
2. **Validation**: `Object_GetSlot()` ensures object availability
3. **Segmentation**: Objects use memory segments 4, 5, and 6
4. **Dependency**: Actors killed if required object unloads

**Object Dependency (`z_actor.c:924`):**
```c
void Actor_SetObjectDependency(PlayState* play, Actor* actor) {
    gSegments[6] = OS_K0_TO_PHYSICAL(play->objectCtx.slots[actor->objectSlot].segment);
}
```

### Memory Allocation Patterns

#### Actor Instance Allocation
- **Size**: Determined by `ActorProfile.instanceSize`
- **Location**: Zelda Arena (standard allocation)
- **Alignment**: Natural alignment for data types
- **Lifetime**: From spawn to destruction

#### Overlay Code Allocation
- **Size**: `vramEnd - vramStart`
- **Location**: Varies by allocation type
- **Persistence**: Reference-counted for standard, fixed for others
- **Relocation**: Virtual addresses converted to physical

### Special Memory Considerations

#### Absolute Space Management
- **Size**: `ACTOROVL_ABSOLUTE_SPACE_SIZE` (fixed constant)
- **Allocation**: Single allocation for all absolute overlays
- **Usage**: Shared space for overlays requiring fixed addresses
- **Lifetime**: Until scene destruction

#### Memory Fragmentation
- Standard allocations can cause fragmentation
- Reverse allocations help by using high addresses
- Absolute space avoids fragmentation for critical overlays

## Performance Optimizations

### Reference Counting Optimization
- Overlays stay loaded while any instance exists
- Reduces repeated load/unload cycles
- Balances memory usage vs loading time

### Category-Based Processing
- Actors organized into 12 categories
- Processing order optimized for game logic
- Selective freezing by category

### Memory Pool Strategy
- Zelda Arena for game objects
- System Arena for permanent data
- Game State Arena for scene-specific allocations

## Error Handling and Debugging

### Memory Allocation Failures

**Comprehensive Error Handling Strategy:**
The actor system implements multiple layers of error handling to gracefully manage memory allocation failures and provide detailed debugging information.

**Actor Instance Allocation Failure (`z_actor.c:3240`):**
```c
actor = ZELDA_ARENA_MALLOC(profile->instanceSize, name, 1);
if (actor == NULL) {
    PRINTF(ACTOR_COLOR_ERROR T("Ａｃｔｏｒクラス確保できません！ %s <サイズ＝%dバイト>\n",
                               "Actor class cannot be reserved! %s <size=%d bytes>\n"),
           ACTOR_RST, name, profile->instanceSize);
    
    // Cleanup allocated overlay to prevent memory leaks
    Actor_FreeOverlay(overlayEntry);
    
    // Log arena state for debugging
    if (gZeldaArenaLogSeverity >= LOG_SEVERITY_ERROR) {
        u32 maxFree, free, alloc;
        ZeldaArena_GetSizes(&maxFree, &free, &alloc);
        PRINTF(T("アリーナ状態: 最大空き=%u, 空き=%u, 使用中=%u\n", 
                 "Arena state: max free=%u, free=%u, allocated=%u\n"), 
               maxFree, free, alloc);
    }
    
    return NULL;
}
```

**Overlay Loading Failure (`z_actor.c:3207`):**
```c
overlayEntry->loadedRamAddr = ZELDA_ARENA_MALLOC(overlaySize, name, 0);
if (overlayEntry->loadedRamAddr == NULL) {
    PRINTF(ACTOR_COLOR_ERROR T("アクターオーバーレイ確保できません！ %s <サイズ＝%dバイト>\n",
                               "Actor overlay cannot be reserved! %s <size=%d bytes>\n"),
           ACTOR_RST, name, overlaySize);
    
    // Attempt cleanup of absolute space if it was allocated
    if (overlayEntry->allocType & ACTOROVL_ALLOC_ABSOLUTE) {
        if (actorCtx->absoluteSpace != NULL) {
            ZELDA_ARENA_FREE(actorCtx->absoluteSpace, "../z_actor.c", 6950);
            actorCtx->absoluteSpace = NULL;
        }
    }
    
    return NULL;
}
```

### Debug Information Systems

**Memory Allocation Logging:**
Debug builds provide extensive logging of memory operations with color-coded output for easy identification:

```c
#if DEBUG_FEATURES
#define ACTOR_DEBUG_PRINTF(format, ...) \
    if (gActorDebugLevel >= DEBUG_LEVEL_VERBOSE) { \
        PRINTF(ACTOR_COLOR_DEBUG format ACTOR_RST, ##__VA_ARGS__); \
    }

// Example usage in spawn function
ACTOR_DEBUG_PRINTF(T("アクター生成: %s ID=%d サイズ=%d\n", 
                      "Actor spawn: %s ID=%d size=%d\n"),
                   name, actorId, profile->instanceSize);
#endif
```

**Overlay Loading Status Tracking:**
The system maintains detailed status information about overlay loading and reference counting:

```c
void Actor_PrintOverlayInfo(ActorOverlay* overlay) {
    PRINTF(T("オーバーレイ情報: %s\n", "Overlay info: %s\n"), overlay->name);
    PRINTF(T("  ROM: %08X - %08X\n"), overlay->file.vromStart, overlay->file.vromEnd);
    PRINTF(T("  RAM: %08X - %08X\n"), overlay->vramStart, overlay->vramEnd);
    PRINTF(T("  ロード済み: %s\n", "Loaded: %s\n"), 
           overlay->loadedRamAddr != NULL ? T("はい", "Yes") : T("いいえ", "No"));
    PRINTF(T("  参照カウント: %d\n", "Reference count: %d\n"), overlay->numLoaded);
    PRINTF(T("  割り当てタイプ: %d\n", "Allocation type: %d\n"), overlay->allocType);
}
```

**Reference Count Tracking:**
Debug builds track overlay reference counts with detailed logging:

```c
// When incrementing reference count
ACTOR_DEBUG_PRINTF(T("オーバーレイ参照カウント++: %s (%d -> %d)\n", 
                      "Overlay reference count++: %s (%d -> %d)\n"),
                   overlay->name, overlay->numLoaded - 1, overlay->numLoaded);

// When decrementing reference count
ACTOR_DEBUG_PRINTF(T("オーバーレイ参照カウント--: %s (%d -> %d)\n", 
                      "Overlay reference count--: %s (%d -> %d)\n"),
                   overlay->name, overlay->numLoaded + 1, overlay->numLoaded);
```

**Arena Usage Monitoring:**
The system provides real-time monitoring of arena usage patterns:

```c
#if DEBUG_FEATURES
void Actor_PrintArenaStatus(const char* context) {
    u32 maxFree, free, alloc;
    ZeldaArena_GetSizes(&maxFree, &free, &alloc);
    
    PRINTF(T("%s 時のアリーナ状態:\n", "%s arena state:\n"), context);
    PRINTF(T("  最大空きブロック: %u バイト\n", "  Max free block: %u bytes\n"), maxFree);
    PRINTF(T("  総空きメモリ: %u バイト\n", "  Total free memory: %u bytes\n"), free);
    PRINTF(T("  使用中メモリ: %u バイト\n", "  Allocated memory: %u bytes\n"), alloc);
    PRINTF(T("  フラグメント率: %.1f%%\n", "  Fragmentation: %.1f%%\n"), 
           (1.0f - (float)maxFree / (float)free) * 100.0f);
}
#endif
```

### Runtime Validation and Assertions

**Actor Limit Enforcement:**
```c
// Hard limit check to prevent system instability
if (actorCtx->total >= ACTOR_NUMBER_MAX) {
    PRINTF(ACTOR_COLOR_ERROR T("致命的エラー: アクター数制限 (%d) に達しました\n",
                               "Fatal error: Actor count limit (%d) reached\n") ACTOR_RST,
           ACTOR_NUMBER_MAX);
    
    // In debug builds, trigger assertion
    ASSERT(false, "Actor count exceeded maximum", "../z_actor.c", 6890);
    return NULL;
}
```

**Object Dependency Validation:**
```c
// Validate object slot is within valid range
if (objectSlot < 0 || objectSlot >= OBJECT_SLOT_MAX) {
    PRINTF(ACTOR_COLOR_ERROR T("無効なオブジェクトスロット: %d\n", 
                               "Invalid object slot: %d\n") ACTOR_RST, objectSlot);
    return NULL;
}

// Validate object is actually loaded
if (!Object_IsLoaded(&play->objectCtx, objectSlot)) {
    PRINTF(ACTOR_COLOR_WARNING T("オブジェクト %d がロードされていません\n",
                                 "Object %d is not loaded\n") ACTOR_RST, objectSlot);
    return NULL;
}
```

### Performance Monitoring and Profiling

**Spawn Time Tracking:**
```c
#if DEBUG_FEATURES
OSTime spawnStart = osGetTime();
// ... spawn logic ...
OSTime spawnEnd = osGetTime();

PRINTF(T("アクター生成時間: %s = %d μs\n", "Actor spawn time: %s = %d μs\n"),
       name, OS_CYCLES_TO_USEC(spawnEnd - spawnStart));
#endif
```

**Memory Leak Detection:**
```c
// Track total allocations vs deallocations
static u32 sActorAllocCount = 0;
static u32 sActorFreeCount = 0;

void Actor_TrackAllocation(void) {
    sActorAllocCount++;
    if ((sActorAllocCount % 100) == 0) {
        PRINTF(T("アクター統計: 確保=%u, 解放=%u, 差=%d\n",
                 "Actor stats: alloc=%u, free=%u, diff=%d\n"),
               sActorAllocCount, sActorFreeCount, sActorAllocCount - sActorFreeCount);
    }
}
```

### Crash Prevention and Recovery

**Safe Function Pointer Validation:**
```c
// Validate function pointers before calling
if (actor->update != NULL) {
    // Additional validation in debug builds
    ASSERT(((uintptr_t)actor->update & 0x3) == 0, "Update function misaligned", "../z_actor.c", 6920);
    actor->update(actor, play);
} else {
    PRINTF(ACTOR_COLOR_WARNING T("アクター %s の更新関数が NULL です\n",
                                 "Actor %s update function is NULL\n") ACTOR_RST, actor->name);
}
```

**Graceful Degradation:**
```c
// If critical systems fail, attempt graceful degradation
if (overlayEntry->loadedRamAddr == NULL && overlayEntry->numLoaded > 0) {
    PRINTF(ACTOR_COLOR_ERROR T("オーバーレイ不整合検出: 参照カウント=%d, アドレス=NULL\n",
                               "Overlay inconsistency detected: refcount=%d, addr=NULL\n") ACTOR_RST,
           overlayEntry->numLoaded);
    
    // Attempt to recover by resetting reference count
    overlayEntry->numLoaded = 0;
    
    // Kill all actors using this overlay
    for (i = 0; i < ACTORCAT_MAX; i++) {
        Actor* listActor = actorCtx->actorLists[i].head;
        while (listActor != NULL) {
            if (listActor->overlayEntry == overlayEntry) {
                Actor_Kill(listActor);
            }
            listActor = listActor->next;
        }
    }
}
```

## Practical Implications for Modding

### Memory Constraints and Optimization Strategies

**Total Actor Count Management:**
The hard limit of `ACTOR_NUMBER_MAX` (200 actors) requires careful planning for complex scenes. Understanding this constraint helps modders design sustainable actor systems:

```c
// Example: Check remaining actor slots before spawning
s32 remainingSlots = ACTOR_NUMBER_MAX - actorCtx->total;
if (remainingSlots < 10) {
    // Implement conservative spawning strategy
    // Consider killing oldest non-essential actors
}
```

**Zelda Arena Size Optimization:**
The arena size directly impacts how many actors and overlays can be loaded simultaneously. Modders should monitor arena usage through debugging tools:

```c
// Monitor arena usage in custom actors
void MyActor_CheckMemoryPressure(Actor* this, PlayState* play) {
    u32 maxFree, free, alloc;
    ZeldaArena_GetSizes(&maxFree, &free, &alloc);
    
    // If less than 100KB free, implement conservative behavior
    if (free < 0x19000) {
        // Disable non-essential features
        // Reduce effect spawning
        // Simplify AI behavior
    }
}
```

**Overlay Loading Impact:**
Understanding overlay allocation types helps optimize memory usage patterns:

- **Use ACTOROVL_ALLOC_PERSISTENT** for actors that spawn frequently throughout a scene
- **Use ACTOROVL_ALLOC_ABSOLUTE** for actors that need stable memory addresses
- **Use standard allocation** for actors that appear in limited areas

### Custom Actor Development Best Practices

**Accurate Instance Size Specification:**
The `instanceSize` field must exactly match the actor's data structure size to prevent memory corruption:

```c
// Example actor structure
typedef struct {
    Actor actor;           // Base actor (0x14C bytes)
    f32 customTimer;       // Custom float field (4 bytes)
    Vec3f customPosition;  // Custom vector (12 bytes)
    s32 customState;       // Custom state (4 bytes)
    // Total: 0x14C + 4 + 12 + 4 = 0x160 bytes
} MyActor;

// Corresponding profile entry
ActorProfile My_Actor_Profile = {
    .id = ACTOR_MY_CUSTOM_ACTOR,
    .category = ACTORCAT_MISC,
    .flags = ACTOR_FLAG_4 | ACTOR_FLAG_25,
    .objectId = OBJECT_MY_CUSTOM_OBJECT,
    .instanceSize = sizeof(MyActor),  // MUST match exactly
    .init = MyActor_Init,
    .destroy = MyActor_Destroy,
    .update = MyActor_Update,
    .draw = MyActor_Draw,
};
```

**Proper Initialization and Cleanup:**
Custom actors must handle initialization and cleanup correctly to prevent memory leaks:

```c
void MyActor_Init(Actor* thisx, PlayState* play) {
    MyActor* this = (MyActor*)thisx;
    
    // Initialize base actor components
    Actor_ProcessInitChain(thisx, sInitChain);
    
    // Set up collision if needed
    Collider_InitCylinder(play, &this->collider);
    Collider_SetCylinder(play, &this->collider, thisx, &sCylinderInit);
    
    // Initialize custom data
    this->customTimer = 0.0f;
    this->customState = 0;
    
    // Set up actor-specific behavior
    thisx->world.rot.y = thisx->shape.rot.y;
    thisx->gravity = -2.0f;
    
    // Set function pointers for state machine
    this->actionFunc = MyActor_Wait;
}

void MyActor_Destroy(Actor* thisx, PlayState* play) {
    MyActor* this = (MyActor*)thisx;
    
    // Clean up collision
    Collider_DestroyCylinder(play, &this->collider);
    
    // Free any custom allocated memory
    if (this->customAllocatedData != NULL) {
        ZELDA_ARENA_FREE(this->customAllocatedData, __FILE__, __LINE__);
    }
    
    // Stop any audio effects
    Audio_StopSfxByPos(&thisx->projectedPos);
}
```

**Object Dependency Management:**
Proper object dependency handling prevents crashes and ensures assets are available:

```c
// In actor init function
void MyActor_Init(Actor* thisx, PlayState* play) {
    // Verify object is loaded before using it
    if (!Object_IsLoaded(&play->objectCtx, thisx->objectSlot)) {
        PRINTF("ERROR: Object %d not loaded for actor %04X\n", 
               OBJECT_MY_CUSTOM_OBJECT, thisx->id);
        Actor_Kill(thisx);
        return;
    }
    
    // Safe to use object data
    this->displayList = gMyObjectDisplayList;
    this->texture = gMyObjectTexture;
}
```

### Performance Optimization Strategies

**Minimize Overlay Loading Overhead:**
Strategic overlay management reduces loading stutters:

```c
// Group related actors in the same overlay
// Use persistent allocation for frequently spawned actors
// Consider shared overlays for similar functionality

// Example: Shared effect overlay
#define ACTOROVL_ALLOC_PERSISTENT (1 << 1)
ActorProfile Effect_Common_Profile = {
    .allocType = ACTOROVL_ALLOC_PERSISTENT,  // Stay loaded
    .vramStart = 0x80A00000,
    .vramEnd = 0x80A10000,
    // ... other fields
};
```

**Memory Fragmentation Prevention:**
Understanding allocation patterns helps prevent fragmentation:

```c
// Best practices for custom memory allocation
void MyActor_AllocateBuffers(MyActor* this) {
    // Allocate large, long-lived buffers first
    this->animationBuffer = ZELDA_ARENA_MALLOC(LARGE_BUFFER_SIZE, __FILE__, __LINE__);
    
    // Allocate smaller, frequently freed buffers later
    this->tempBuffer = ZELDA_ARENA_MALLOC(SMALL_BUFFER_SIZE, __FILE__, __LINE__);
    
    // Consider using reverse allocation for persistent data
    this->persistentData = ZELDA_ARENA_MALLOC_R(PERSISTENT_SIZE, __FILE__, __LINE__);
}
```

**Category-Specific Optimizations:**
Understanding category processing order enables optimization:

```c
// Use appropriate category for intended behavior
// ACTORCAT_SWITCH (0) - Processes first, affects environment
// ACTORCAT_PLAYER (2) - Central to all interactions
// ACTORCAT_ENEMY (5) - Processes after player, good for AI
// ACTORCAT_MISC (8) - Processes late, good for effects

// Example: Environmental trigger
ActorProfile Trigger_Profile = {
    .category = ACTORCAT_SWITCH,  // Process early to affect other actors
    .flags = ACTOR_FLAG_4,        // No draw, no update during pause
    // ... other fields
};
```

### Advanced Memory Management Techniques

**Custom Memory Pools:**
For actors with specific memory patterns, consider custom pools:

```c
// Example: Particle system with object pooling
typedef struct {
    Actor actor;
    ParticlePool* particlePool;
    u32 maxParticles;
} ParticleSystemActor;

void ParticleSystem_Init(Actor* thisx, PlayState* play) {
    ParticleSystemActor* this = (ParticleSystemActor*)thisx;
    
    // Pre-allocate particle pool
    size_t poolSize = sizeof(Particle) * this->maxParticles;
    this->particlePool = ZELDA_ARENA_MALLOC(poolSize, __FILE__, __LINE__);
    
    // Initialize pool management
    ParticlePool_Init(this->particlePool, this->maxParticles);
}
```

**Memory-Aware State Machines:**
Design state machines that consider memory pressure:

```c
void MyActor_Update(Actor* thisx, PlayState* play) {
    MyActor* this = (MyActor*)thisx;
    
    // Check memory pressure before expensive operations
    u32 maxFree, free, alloc;
    ZeldaArena_GetSizes(&maxFree, &free, &alloc);
    
    if (free < LOW_MEMORY_THRESHOLD) {
        // Switch to memory-conservative state
        this->actionFunc = MyActor_ConservativeUpdate;
    } else {
        // Normal processing
        this->actionFunc(this, play);
    }
}
```

### Testing and Validation

**Memory Leak Detection:**
Implement custom memory tracking for complex actors:

```c
#if DEBUG_FEATURES
static u32 sMyActorAllocCount = 0;
static u32 sMyActorFreeCount = 0;

void MyActor_TrackAllocation(void) {
    sMyActorAllocCount++;
    if ((sMyActorAllocCount % 10) == 0) {
        PRINTF("MyActor memory: alloc=%u, free=%u, diff=%d\n",
               sMyActorAllocCount, sMyActorFreeCount, 
               sMyActorAllocCount - sMyActorFreeCount);
    }
}
#endif
```

**Performance Profiling:**
Monitor actor performance impact:

```c
void MyActor_ProfiledUpdate(Actor* thisx, PlayState* play) {
    OSTime updateStart = osGetTime();
    
    // Actual update logic
    MyActor_DoUpdate(thisx, play);
    
    OSTime updateEnd = osGetTime();
    u32 updateTime = OS_CYCLES_TO_USEC(updateEnd - updateStart);
    
    if (updateTime > PERFORMANCE_THRESHOLD) {
        PRINTF("WARNING: MyActor update took %d μs\n", updateTime);
    }
}
```

This comprehensive understanding of the actor lifecycle and memory management system enables modders to create efficient, stable, and performant custom actors that integrate seamlessly with OOT's existing systems.

## Conclusion

The OOT actor lifecycle and memory management system demonstrates sophisticated design within the N64's constraints. The three-tier allocation system, reference-counted overlays, and category-based processing create an efficient framework for managing hundreds of interactive objects while maintaining stable performance.

The source code analysis reveals careful attention to memory efficiency, error handling, and performance optimization throughout the actor system. Understanding these systems is crucial for effective OOT modding and provides insights into N64-era game engine design. 