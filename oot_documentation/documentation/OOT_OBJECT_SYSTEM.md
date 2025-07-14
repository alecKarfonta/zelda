# OOT Object System Deep Dive

## Overview

This document provides a comprehensive analysis of the Object System in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The object system is responsible for loading and managing graphics assets, models, textures, and other game resources that are required by actors and the game engine. It provides a sophisticated caching mechanism with DMA loading and memory management optimized for the N64's constraints.

## Architecture Overview

### Object System Components

The object system consists of several key components working together:

**Core Components:**
- **Object Context**: Manages object slots and memory allocation
- **Object Table**: Master table of all available objects in the ROM
- **Object Slots**: Individual memory slots for loaded objects
- **DMA Management**: Asynchronous loading system for object data
- **Segmented Memory**: Memory addressing system for object references

### Object Context Structure

**Object Context Initialization (`z_scene.c:92`):**
```c
void Object_InitContext(PlayState* play, ObjectContext* objectCtx) {
    PlayState* play2 = play;
    s32 pad;
    u32 spaceSize;
    s32 i;

    if (play2->sceneId == SCENE_HYRULE_FIELD) {
        spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else if (play2->sceneId == SCENE_GANON_BOSS) {
        if (gSaveContext.sceneLayer != 4) {
            spaceSize = 1150 * 1024 - OBJECT_SPACE_ADJUSTMENT;
        } else {
            spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT;
        }
    } else if (play2->sceneId == SCENE_SPIRIT_TEMPLE_BOSS) {
        spaceSize = 1050 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else if (play2->sceneId == SCENE_CHAMBER_OF_THE_SAGES) {
        spaceSize = 1050 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else if (play2->sceneId == SCENE_GANONDORF_BOSS) {
        spaceSize = 1050 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else {
        spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    }

    objectCtx->numEntries = objectCtx->numPersistentEntries = 0;
    objectCtx->mainKeepSlot = objectCtx->subKeepSlot = 0;

    for (i = 0; i < ARRAY_COUNT(objectCtx->slots); i++) {
        objectCtx->slots[i].id = OBJECT_INVALID;
    }

    PRINTF_COLOR_GREEN();
    PRINTF(T("オブジェクト入れ替えバンク情報 %8.3fKB\n", "Object exchange bank data %8.3fKB\n"), spaceSize / 1024.0f);
    PRINTF_RST();

    objectCtx->spaceStart = objectCtx->slots[0].segment =
        GAME_STATE_ALLOC(&play->state, spaceSize, "../z_scene.c", 219);
    objectCtx->spaceEnd = (void*)((uintptr_t)objectCtx->spaceStart + spaceSize);

    objectCtx->mainKeepSlot = Object_SpawnPersistent(objectCtx, OBJECT_GAMEPLAY_KEEP);
    gSegments[4] = OS_K0_TO_PHYSICAL(objectCtx->slots[objectCtx->mainKeepSlot].segment);
}
```

### Object Table System

**Object Table Definition (`object_table.c:24`):**
```c
RomFile gObjectTable[] = {
#include "tables/object_table.h"
};
```

**Object Table Access:**
```c
s16 gLinkObjectIds[] = { OBJECT_LINK_BOY, OBJECT_LINK_CHILD };
u32 gObjectTableSize = ARRAY_COUNT(gObjectTable);
```

## Object Loading and Caching

### Persistent Object Loading

**Persistent Object Spawning (`z_scene.c:32`):**
```c
s32 Object_SpawnPersistent(ObjectContext* objectCtx, s16 objectId) {
    u32 size;

    objectCtx->slots[objectCtx->numEntries].id = objectId;
    size = gObjectTable[objectId].vromEnd - gObjectTable[objectId].vromStart;

    PRINTF("OBJECT[%d] SIZE %fK SEG=%x\n", objectId, size / 1024.0f, objectCtx->slots[objectCtx->numEntries].segment);

    PRINTF("num=%d adrs=%x end=%x\n", objectCtx->numEntries,
           (uintptr_t)objectCtx->slots[objectCtx->numEntries].segment + size, objectCtx->spaceEnd);

    ASSERT(((objectCtx->numEntries < ARRAY_COUNT(objectCtx->slots)) &&
            (((uintptr_t)objectCtx->slots[objectCtx->numEntries].segment + size) < (uintptr_t)objectCtx->spaceEnd)),
           "this->num < OBJECT_EXCHANGE_BANK_MAX && (this->status[this->num].Segment + size) < this->endSegment",
           "../z_scene.c", 142);

    DMA_REQUEST_SYNC(objectCtx->slots[objectCtx->numEntries].segment, gObjectTable[objectId].vromStart, size,
                     "../z_scene.c", 145);

    if (objectCtx->numEntries < (ARRAY_COUNT(objectCtx->slots) - 1)) {
        objectCtx->slots[objectCtx->numEntries + 1].segment =
            (void*)ALIGN16((uintptr_t)objectCtx->slots[objectCtx->numEntries].segment + size);
    }

    objectCtx->numEntries++;
    objectCtx->numPersistentEntries = objectCtx->numEntries;

    return objectCtx->numEntries - 1;
}
```

### Asynchronous Object Loading

**Object Update System (`z_scene.c:235`):**
```c
void Object_UpdateEntries(ObjectContext* objectCtx) {
    s32 i;
    ObjectEntry* entry = &objectCtx->slots[0];
    RomFile* objectFile;
    u32 size;

    for (i = 0; i < objectCtx->numEntries; i++) {
        if (entry->id < 0) {
            if (entry->dmaRequest.vromAddr == 0) {
                osCreateMesgQueue(&entry->loadQueue, &entry->loadMsg, 1);
                objectFile = &gObjectTable[-entry->id];
                size = objectFile->vromEnd - objectFile->vromStart;

                PRINTF("OBJECT EXCHANGE BANK-%2d SIZE %8.3fK SEG=%08x\n", i, size / 1024.0f, entry->segment);

                DMA_REQUEST_ASYNC(&entry->dmaRequest, entry->segment, objectFile->vromStart, size, 0, &entry->loadQueue,
                                  NULL, "../z_scene.c", 266);
            } else if (osRecvMesg(&entry->loadQueue, NULL, OS_MESG_NOBLOCK) == 0) {
                entry->id = -entry->id;
            }
        }
        entry++;
    }
}
```

### Object Slot Management

**Object Slot Lookup (`z_scene.c:275`):**
```c
s32 Object_GetSlot(ObjectContext* objectCtx, s16 objectId) {
    s32 i;

    for (i = 0; i < objectCtx->numEntries; i++) {
        if (ABS(objectCtx->slots[i].id) == objectId) {
            return i;
        }
    }

    return -1;
}
```

**Object Loading Status (`z_scene.c:286`):**
```c
s32 Object_IsLoaded(ObjectContext* objectCtx, s32 slot) {
    if (objectCtx->slots[slot].id > 0) {
        return true;
    } else {
        return false;
    }
}
```

### Dynamic Object Loading

**Object Loading Preparation (`z_scene.c:321`):**
```c
void* func_800982FC(ObjectContext* objectCtx, s32 slot, s16 objectId) {
    ObjectEntry* entry = &objectCtx->slots[slot];
    RomFile* objectFile = &gObjectTable[objectId];
    u32 size;
    void* nextPtr;

    entry->id = -objectId;
    entry->dmaRequest.vromAddr = 0;

    size = objectFile->vromEnd - objectFile->vromStart;
    PRINTF("OBJECT EXCHANGE NO=%2d BANK=%3d SIZE=%8.3fK\n", slot, objectId, size / 1024.0f);

    nextPtr = (void*)ALIGN16((uintptr_t)entry->segment + size);

    ASSERT(nextPtr < objectCtx->spaceEnd, "nextptr < this->endSegment", "../z_scene.c", 381);

    PRINTF(T("オブジェクト入れ替え空きサイズ=%08x\n", "Object exchange free size=%08x\n"),
           (uintptr_t)objectCtx->spaceEnd - (uintptr_t)nextPtr);

    return nextPtr;
}
```

## Memory Management

### Object Space Allocation

**Memory Space Calculation:**
```c
// PAL N64 versions reduce the size of object space by 4 KiB in order to give some space back to
// the Zelda arena, which can help prevent an issue where actors fail to spawn in specific areas
// (sometimes referred to as the "Hyrule Field Glitch" although it can happen in more places than Hyrule Field).
#if !OOT_PAL_N64
#define OBJECT_SPACE_ADJUSTMENT 0
#else
#define OBJECT_SPACE_ADJUSTMENT (4 * 1024)
#endif
```

**Scene-Specific Memory Allocation:**
- **Hyrule Field**: 1000KB - adjustment
- **Ganon Boss**: 1150KB - adjustment (non-layer 4), 1000KB - adjustment (layer 4)
- **Spirit Temple Boss**: 1050KB - adjustment
- **Chamber of the Sages**: 1050KB - adjustment
- **Ganondorf Boss**: 1050KB - adjustment
- **Default Scenes**: 1000KB - adjustment

### Segmented Memory System

**Object Dependency Setting (`z_actor.c:932`):**
```c
void Actor_SetObjectDependency(PlayState* play, Actor* actor) {
    gSegments[6] = OS_K0_TO_PHYSICAL(play->objectCtx.slots[actor->objectSlot].segment);
}
```

**Segment Updates (`z_play.c:589`):**
```c
gSegments[4] = OS_K0_TO_PHYSICAL(this->objectCtx.slots[this->objectCtx.mainKeepSlot].segment);
gSegments[5] = OS_K0_TO_PHYSICAL(this->objectCtx.slots[this->objectCtx.subKeepSlot].segment);
gSegments[2] = OS_K0_TO_PHYSICAL(this->sceneSegment);
```

## Scene Command Integration

### Object List Processing

**Scene Command Object List (`z_scene.c:665`):**
```c
BAD_RETURN(s32) Scene_CommandObjectList(PlayState* play, SceneCmd* cmd) {
    s32 i;
    s32 j;
    s32 k;
    ObjectEntry* entry;
    ObjectEntry* invalidatedEntry;
    ObjectEntry* entries;
    s16* objectListEntry = SEGMENTED_TO_VIRTUAL(cmd->objectList.data);
    void* nextPtr;

    k = 0;
    i = play->objectCtx.numPersistentEntries;
    entries = play->objectCtx.slots;
    entry = &play->objectCtx.slots[i];

    while (i < play->objectCtx.numEntries) {
        if (entry->id != *objectListEntry) {

            invalidatedEntry = &play->objectCtx.slots[i];
            for (j = i; j < play->objectCtx.numEntries; j++) {
                invalidatedEntry->id = OBJECT_INVALID;
                invalidatedEntry++;
            }

            play->objectCtx.numEntries = i;
            Actor_KillAllWithMissingObject(play, &play->actorCtx);

            continue;
        }

        i++;
        k++;
        objectListEntry++;
        entry++;
    }

    ASSERT(cmd->objectList.length <= ARRAY_COUNT(play->objectCtx.slots),
           "scene_info->object_bank.num <= OBJECT_EXCHANGE_BANK_MAX", "../z_scene.c", 705);

    while (k < cmd->objectList.length) {
        nextPtr = func_800982FC(&play->objectCtx, i, *objectListEntry);
        if (i < (ARRAY_COUNT(play->objectCtx.slots) - 1)) {
            entries[i + 1].segment = nextPtr;
        }
        i++;
        k++;
        objectListEntry++;
    }

    play->objectCtx.numEntries = i;
}
```

### Special Object Files

**Special File Handling (`z_scene.c:616`):**
```c
BAD_RETURN(s32) Scene_CommandSpecialFiles(PlayState* play, SceneCmd* cmd) {
    if (cmd->specialFiles.keepObjectId != OBJECT_INVALID) {
        play->objectCtx.subKeepSlot = Object_SpawnPersistent(&play->objectCtx, cmd->specialFiles.keepObjectId);
        gSegments[5] = OS_K0_TO_PHYSICAL(play->objectCtx.slots[play->objectCtx.subKeepSlot].segment);
    }

    if (cmd->specialFiles.naviQuestHintFileId != NAVI_QUEST_HINTS_NONE) {
        play->naviQuestHints = Play_LoadFile(play, &sNaviQuestHintFiles[cmd->specialFiles.naviQuestHintFileId - 1]);
    }
}
```

## Actor Integration

### Actor Object Requirements

**Actor Initialization with Object Dependency (`z_actor.c:947`):**
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
        actor->init = NULL;
    }
}
```

### Actor Spawning with Object Validation

**Actor Spawn Object Validation (`z_actor.c:3244`):**
```c
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

### Actor Update with Object Dependency

**Actor Update Loop Object Checks (`z_actor.c:2457`):**
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

## Object Types and Examples

### Essential Objects

**Gameplay Keep Object:**
- **OBJECT_GAMEPLAY_KEEP**: Core gameplay assets always loaded
- **mainKeepSlot**: Always slot 0, contains essential game elements
- **Segment 4**: Always points to gameplay keep data

**Link Objects:**
```c
s16 gLinkObjectIds[] = { OBJECT_LINK_BOY, OBJECT_LINK_CHILD };
```

**Player Object Loading (`z_scene.c:571`):**
```c
BAD_RETURN(s32) Scene_CommandPlayerEntryList(PlayState* play, SceneCmd* cmd) {
    ActorEntry* playerEntry = play->playerEntry =
        (ActorEntry*)SEGMENTED_TO_VIRTUAL(cmd->playerEntryList.data) + play->spawnList[play->spawn].playerEntryIndex;
    s16 linkObjectId;

    play->linkAgeOnLoad = ((void)0, gSaveContext.save.linkAge);

    linkObjectId = gLinkObjectIds[((void)0, gSaveContext.save.linkAge)];

    gActorOverlayTable[playerEntry->id].profile->objectId = linkObjectId;
    Object_SpawnPersistent(&play->objectCtx, linkObjectId);
}
```

### Actor-Specific Objects

**Example Actor Object Dependency:**
```c
ActorProfile En_A_Obj_Profile = {
    /**/ ACTOR_EN_A_OBJ,
    /**/ ACTORCAT_PROP,
    /**/ FLAGS,
    /**/ OBJECT_GAMEPLAY_KEEP,
    /**/ sizeof(EnAObj),
    /**/ EnAObj_Init,
    /**/ EnAObj_Destroy,
    /**/ EnAObj_Update,
    /**/ EnAObj_Draw,
};
```

## Performance Optimization

### Object Memory Management

**Memory Allocation Strategies:**
1. **Persistent Objects**: Loaded once and remain until scene change
2. **Room-Specific Objects**: Loaded per room and unloaded when room changes
3. **Dynamic Objects**: Loaded and unloaded as needed

### Loading Performance

**Asynchronous Loading Benefits:**
- Non-blocking DMA transfers
- Parallel loading with game logic
- Efficient memory utilization
- Reduced loading times

### Memory Fragmentation Prevention

**Object Slot Reuse:**
```c
for (i = 0; i < ARRAY_COUNT(objectCtx->slots); i++) {
    objectCtx->slots[i].id = OBJECT_INVALID;
}
```

**Aligned Memory Allocation:**
```c
nextPtr = (void*)ALIGN16((uintptr_t)entry->segment + size);
```

## Debugging and Development

### Object Debug Information

**Object Loading Debug (`z_play.c:563`):**
```c
if ((R_HREG_MODE == HREG_MODE_PRINT_OBJECT_TABLE) && (R_PRINT_OBJECT_TABLE_TRIGGER < 0)) {
    u32 i;
    s32 pad2;

    R_PRINT_OBJECT_TABLE_TRIGGER = 0;
    PRINTF("object_exchange_rom_address %u\n", gObjectTableSize);
    PRINTF("RomStart RomEnd   Size\n");

    for (i = 0; i < gObjectTableSize; i++) {
        s32 size = gObjectTable[i].vromEnd - gObjectTable[i].vromStart;

        PRINTF("%08x-%08x %08x(%8.3fKB)\n", gObjectTable[i].vromStart, gObjectTable[i].vromEnd, size,
               size / 1024.0f);
    }

    PRINTF("\n");
}
```

### Object Status Monitoring

**Object Loading Status:**
```c
void func_800981B8(ObjectContext* objectCtx) {
    s32 i;
    s32 id;
    u32 size;

    for (i = 0; i < objectCtx->numEntries; i++) {
        id = objectCtx->slots[i].id;
        size = gObjectTable[id].vromEnd - gObjectTable[id].vromStart;
        PRINTF("OBJECT[%d] SIZE %fK SEG=%x\n", objectCtx->slots[i].id, size / 1024.0f, objectCtx->slots[i].segment);
        PRINTF("num=%d adrs=%x end=%x\n", objectCtx->numEntries, (uintptr_t)objectCtx->slots[i].segment + size,
               objectCtx->spaceEnd);
        DMA_REQUEST_SYNC(objectCtx->slots[i].segment, gObjectTable[id].vromStart, size, "../z_scene.c", 342);
    }
}
```

## Practical Examples

### Custom Object Integration

**Creating Custom Object Support:**

```c
// Custom object ID definition
#define OBJECT_CUSTOM_ACTOR 0x200

// Custom actor profile with object dependency
ActorProfile CustomActor_Profile = {
    /**/ ACTOR_CUSTOM_ACTOR,
    /**/ ACTORCAT_MISC,
    /**/ FLAGS,
    /**/ OBJECT_CUSTOM_ACTOR,
    /**/ sizeof(CustomActor),
    /**/ CustomActor_Init,
    /**/ CustomActor_Destroy,
    /**/ CustomActor_Update,
    /**/ CustomActor_Draw,
};

// Custom actor initialization with object check
void CustomActor_Init(Actor* thisx, PlayState* play) {
    CustomActor* this = (CustomActor*)thisx;
    
    // Check if required object is loaded
    if (!Object_IsLoaded(&play->objectCtx, this->actor.objectSlot)) {
        PRINTF("Custom object not loaded for actor\n");
        Actor_Kill(&this->actor);
        return;
    }
    
    // Set object dependency
    Actor_SetObjectDependency(play, &this->actor);
    
    // Initialize actor
    Actor_SetScale(&this->actor, 0.01f);
    // ... rest of initialization
}
```

### Object Preloading

**Preloading Objects for Performance:**

```c
// Preload objects for better performance
void Scene_PreloadObjects(PlayState* play, s16* objectList, s32 numObjects) {
    s32 i;
    s32 slot;
    
    for (i = 0; i < numObjects; i++) {
        slot = Object_GetSlot(&play->objectCtx, objectList[i]);
        if (slot < 0) {
            // Object not loaded, prepare for loading
            slot = play->objectCtx.numEntries;
            if (slot < ARRAY_COUNT(play->objectCtx.slots)) {
                func_800982FC(&play->objectCtx, slot, objectList[i]);
                play->objectCtx.numEntries++;
            }
        }
    }
}
```

### Object Memory Monitoring

**Object Memory Usage Tracking:**

```c
// Track object memory usage
void Object_PrintMemoryUsage(ObjectContext* objectCtx) {
    s32 i;
    u32 totalSize = 0;
    u32 objectSize;
    
    PRINTF("Object Memory Usage:\n");
    PRINTF("Slot | Object ID | Size (KB) | Address\n");
    PRINTF("----|-----------|-----------|----------\n");
    
    for (i = 0; i < objectCtx->numEntries; i++) {
        if (objectCtx->slots[i].id != OBJECT_INVALID) {
            objectSize = gObjectTable[ABS(objectCtx->slots[i].id)].vromEnd - 
                        gObjectTable[ABS(objectCtx->slots[i].id)].vromStart;
            totalSize += objectSize;
            
            PRINTF("%4d | %9d | %8.3f | %08x\n", 
                   i, ABS(objectCtx->slots[i].id), objectSize / 1024.0f, 
                   (uintptr_t)objectCtx->slots[i].segment);
        }
    }
    
    PRINTF("Total: %.3fKB / %.3fKB\n", totalSize / 1024.0f, 
           ((uintptr_t)objectCtx->spaceEnd - (uintptr_t)objectCtx->spaceStart) / 1024.0f);
}
```

## Error Handling and Edge Cases

### Object Loading Failures

**Common Object Loading Issues:**
1. **Object Not Found**: Object ID not in object table
2. **Memory Exhaustion**: Not enough memory for object
3. **DMA Failure**: ROM read error or corruption
4. **Slot Exhaustion**: Too many objects loaded simultaneously

### Memory Management Issues

**Hyrule Field Glitch Prevention:**
```c
// PAL versions reduce object space to prevent actor spawn failures
#define OBJECT_SPACE_ADJUSTMENT (4 * 1024)
```

**Memory Fragmentation Handling:**
- Objects are loaded in contiguous memory blocks
- Alignment ensures efficient memory usage
- Persistent objects are loaded first to minimize fragmentation

## Platform-Specific Considerations

### N64 Memory Constraints

**Memory Limitations:**
- 4MB RAM on N64 (8MB on development units)
- Object space typically 1MB
- DMA transfer overhead considerations

### GameCube Optimizations

**Enhanced Memory Management:**
- Larger available memory allows for bigger object spaces
- Reduced memory pressure for object loading
- Improved performance for object-heavy scenes

## Conclusion

The Object System in OOT provides a sophisticated asset management solution that efficiently handles the loading and caching of game resources. Understanding its architecture is crucial for:

- Creating custom actors with proper object dependencies
- Optimizing memory usage in scenes
- Debugging object loading issues
- Implementing custom asset loading systems
- Understanding the relationship between actors and their graphical assets

The system's design allows for efficient memory utilization while providing the flexibility needed for a complex game like Ocarina of Time. The asynchronous loading system, combined with intelligent memory management, ensures that the game can smoothly handle the large number of objects required for different scenes and gameplay situations.

**Key Files Reference:**
- `src/code/z_scene.c` - Object context management and loading
- `src/code/object_table.c` - Object table definitions
- `src/code/z_actor.c` - Actor-object integration
- `src/code/z_play.c` - Object system integration with gameplay
- `include/object.h` - Object system definitions
- `assets/objects/` - Individual object asset files

## Additional Resources

For more detailed information about specific aspects of the object system, refer to:
- Individual object file implementations in `assets/objects/`
- Actor system documentation for object dependency patterns
- Scene system documentation for object loading in scenes
- Memory management documentation for arena and allocation strategies 