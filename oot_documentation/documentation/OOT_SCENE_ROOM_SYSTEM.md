# OOT Scene/Room System Deep Dive

## Overview

This document provides a comprehensive analysis of the Scene and Room systems in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code in the `oot/src` folder. The scene/room system is the foundational architecture that defines OOT's world structure, managing everything from geometry and lighting to actor placement and environmental effects.

## Scene/Room Architecture Overview

### Conceptual Design

The OOT engine uses a hierarchical two-level world organization:

- **Scenes**: High-level areas containing shared data and configuration (Hyrule Field, Kakariko Village, Fire Temple)
- **Rooms**: Sub-areas within scenes containing specific geometry and actors (individual rooms in a dungeon, different sections of an overworld area)

This design allows for:
- **Memory efficiency**: Only the current room's geometry is loaded while scene data remains persistent
- **Seamless transitions**: Smooth movement between rooms without loading screens
- **Modular content**: Artists and designers can work on individual rooms independently
- **Dynamic loading**: Rooms can be swapped in and out based on player movement

### Core Data Structures

**Scene Table Entry (`z_scene_table.c:120`):**
```c
typedef struct {
    RomFile sceneFile;     // ROM location of scene data
    RomFile titleFile;     // ROM location of title card image
    u8 config;             // Scene configuration flags
    u8 drawConfig;         // Rendering configuration index
    u8 unk_12;             // Unknown field
    u8 unk_13;             // Runtime loading state
} SceneTableEntry;
```

**Room Context (`play_state.h`):**
```c
typedef struct {
    Room curRoom;          // Currently active room
    Room prevRoom;         // Previous room (for transitions)
    void* roomRequestAddr; // Address of room being loaded
    s32 status;            // Loading status (0=ready, 1=loading)
    OSMesgQueue loadQueue; // Message queue for async loading
    OSMesg loadMsg;        // Message buffer for DMA completion
    s32 drawParams[2];     // Room-specific drawing parameters
} RoomContext;
```

**Scene Command Structure (`scene.h`):**
```c
typedef struct {
    u8 code;    // Command type ID
    u8 data1;   // Command-specific data
    u16 data2;  // Command-specific data
    u32 data;   // Pointer to command data
} SceneCmd;
```

## Scene Loading and Initialization System

### Scene Spawning Process

The scene loading process follows a precise sequence initiated by `Play_SpawnScene()`:

**Step 1: Scene Table Lookup (`z_play.c:1567`):**
```c
scene = &gSceneTable[sceneId];
this->loadedScene = scene;
this->sceneId = sceneId;
this->sceneDrawConfig = scene->drawConfig;
```

The engine first looks up the scene in the global scene table, which maps scene IDs to their ROM file locations and configuration parameters.

**Step 2: Scene File Loading (`z_play.c:1583`):**
```c
this->sceneSegment = Play_LoadFile(this, &scene->sceneFile);
ASSERT(this->sceneSegment != NULL, "this->sceneSegment != NULL", "../z_play.c", 4960);
gSegments[2] = OS_K0_TO_PHYSICAL(this->sceneSegment);
```

The scene file is loaded from ROM into memory and assigned to segment 2 of the segmented memory system. This segment contains all scene-level data including headers, collision, and shared resources.

**Step 3: Scene Initialization (`z_play.c:1544`):**
```c
void Play_InitScene(PlayState* this, s32 spawn) {
    this->spawn = spawn;
    this->playerEntry = NULL;
    this->spawnList = NULL;
    this->exitList = NULL;
    this->pathList = NULL;
    this->numActorEntries = 0;
    
    Object_InitContext(this, &this->objectCtx);
    LightContext_Init(this, &this->lightCtx);
    Scene_ResetTransitionActorList(&this->state, &this->transitionActors);
    Room_Init(this, &this->roomCtx.curRoom);
    
    Scene_ExecuteCommands(this, this->sceneSegment);
    Play_InitEnvironment(this, this->skyboxId);
}
```

Scene initialization resets all scene-specific state, initializes subsystems, and processes the scene command list.

**Step 4: Scene Command Processing (`z_scene.c:203`):**
```c
s32 Scene_ExecuteCommands(PlayState* play, SceneCmd* sceneCmd) {
    while (true) {
        u32 cmdCode = sceneCmd->base.code;
        
        if (cmdCode == SCENE_CMD_ID_END) {
            break;
        }
        
        if (cmdCode < ARRAY_COUNT(sSceneCmdHandlers)) {
            sSceneCmdHandlers[cmdCode](play, sceneCmd);
        }
        
        sceneCmd++;
    }
    return 0;
}
```

The scene command processor iterates through a list of commands that define the scene's properties and content.

### Scene Layer System

OOT implements a sophisticated layer system that allows different versions of the same scene based on story progression:

**Layer Selection (`z_play.c:368`):**
```c
if (gSaveContext.gameMode != GAMEMODE_NORMAL || gSaveContext.save.cutsceneIndex >= CS_INDEX_0) {
    gSaveContext.sceneLayer = GET_CUTSCENE_LAYER(gSaveContext.save.cutsceneIndex);
} else if (!LINK_IS_ADULT && IS_DAY) {
    gSaveContext.sceneLayer = SCENE_LAYER_CHILD_DAY;
} else if (!LINK_IS_ADULT && !IS_DAY) {
    gSaveContext.sceneLayer = SCENE_LAYER_CHILD_NIGHT;
} else if (LINK_IS_ADULT && IS_DAY) {
    gSaveContext.sceneLayer = SCENE_LAYER_ADULT_DAY;
} else {
    gSaveContext.sceneLayer = SCENE_LAYER_ADULT_NIGHT;
}
```

**Special Layer Handling:**
- **Hyrule Field**: Uses quest item progression to determine layer
- **Kokiri Forest**: Changes based on adult Link's story progress
- **Cutscenes**: Override normal layer logic for story sequences

## Room System and Management

### Room Loading Architecture

**Room Setup (`z_room.c:585`):**
```c
u32 Room_SetupFirstRoom(PlayState* play, RoomContext* roomCtx) {
    size_t size;
    
    roomCtx->curRoom.num = play->roomList.romFiles[0].num;
    roomCtx->curRoom.type = ROOM_TYPE_NORMAL;
    
    size = play->roomList.romFiles[0].vromEnd - play->roomList.romFiles[0].vromStart;
    roomCtx->curRoom.segment = GAME_STATE_ALLOC(&play->state, size, "../z_room.c", 604);
    
    DMA_REQUEST_SYNC(roomCtx->curRoom.segment, 
                     play->roomList.romFiles[0].vromStart, size, "../z_room.c", 608);
    
    gSegments[3] = OS_K0_TO_PHYSICAL(roomCtx->curRoom.segment);
    
    Scene_ExecuteCommands(play, roomCtx->curRoom.segment);
    return size;
}
```

The first room is loaded synchronously during scene initialization, while subsequent room changes use asynchronous loading.

**Asynchronous Room Loading (`z_room.c:713`):**
```c
s32 Room_ProcessRoomRequest(PlayState* play, RoomContext* roomCtx) {
    if (roomCtx->status == 1) {
        if (osRecvMesg(&roomCtx->loadQueue, NULL, OS_MESG_NOBLOCK) == 0) {
            roomCtx->status = 0;
            roomCtx->curRoom.segment = roomCtx->roomRequestAddr;
            gSegments[3] = OS_K0_TO_PHYSICAL(roomCtx->curRoom.segment);
            
            Scene_ExecuteCommands(play, roomCtx->curRoom.segment);
            Player_SetBootData(play, GET_PLAYER(play));
            Actor_SpawnTransitionActors(play, &play->actorCtx);
        } else {
            return false;
        }
    }
    return true;
}
```

Room loading uses the N64's DMA system with message queues for non-blocking I/O.

### Room Shape Types

The engine supports three different room rendering approaches:

#### ROOM_SHAPE_TYPE_NORMAL - Standard Geometry
Used for most indoor areas and simple outdoor spaces.

**Implementation (`z_room.c:86`):**
```c
void Room_DrawNormal(PlayState* play, Room* room, u32 flags) {
    RoomShapeNormal* roomShape = &room->roomShape->normal;
    RoomShapeDListsEntry* entry = SEGMENTED_TO_VIRTUAL(roomShape->entries);
    
    for (i = 0; i < roomShape->numEntries; i++) {
        if ((flags & ROOM_DRAW_OPA) && (entry->opa != NULL)) {
            gSPDisplayList(POLY_OPA_DISP++, entry->opa);
        }
        if ((flags & ROOM_DRAW_XLU) && (entry->xlu != NULL)) {
            gSPDisplayList(POLY_XLU_DISP++, entry->xlu);
        }
        entry++;
    }
}
```

This approach renders all geometry unconditionally, suitable for smaller rooms where occlusion culling isn't necessary.

#### ROOM_SHAPE_TYPE_CULLABLE - Frustum Culling
Used for large outdoor areas and complex indoor spaces where performance optimization is critical.

**Culling Implementation (`z_room.c:127`):**
```c
void Room_DrawCullable(PlayState* play, Room* room, u32 flags) {
    RoomShapeCullable* roomShape = &room->roomShape->cullable;
    RoomShapeCullableEntryLinked linkedEntriesBuffer[ROOM_SHAPE_CULLABLE_MAX_ENTRIES];
    RoomShapeCullableEntryLinked* head = NULL;
    
    // Z-sort entries and perform frustum culling
    for (each entry) {
        // Transform bounding sphere to view space
        // Cull entries outside view frustum
        // Insert remaining entries into Z-sorted linked list
    }
    
    // Render entries from nearest to furthest
    for (iter = head; iter != NULL; iter = iter->next) {
        // Render display lists
    }
}
```

This system performs view frustum culling and Z-sorting for optimal rendering performance.

#### ROOM_SHAPE_TYPE_IMAGE - Pre-rendered Backgrounds
Used for complex backgrounds that would be too expensive to render in real-time.

**Image Rendering (`z_room.c:557`):**
```c
void Room_DrawImage(PlayState* play, Room* room, u32 flags) {
    RoomShapeImageBase* roomShape = &room->roomShape->image.base;
    
    if (roomShape->amountType == ROOM_SHAPE_IMAGE_AMOUNT_SINGLE) {
        Room_DrawImageSingle(play, room, flags);
    } else if (roomShape->amountType == ROOM_SHAPE_IMAGE_AMOUNT_MULTI) {
        Room_DrawImageMulti(play, room, flags);
    }
}
```

This system displays pre-rendered JPEG backgrounds with 3D objects rendered on top.

### Room Transition System

**Room Change Finalization (`z_room.c:741`):**
```c
void Room_FinishRoomChange(PlayState* play, RoomContext* roomCtx) {
    // Delete the previous room
    roomCtx->prevRoom.num = -1;
    roomCtx->prevRoom.segment = NULL;
    
    func_80031B14(play, &play->actorCtx);
    Actor_SpawnTransitionActors(play, &play->actorCtx);
    Map_InitRoomData(play, roomCtx->curRoom.num);
    
    Audio_SetEnvReverb(play->roomCtx.curRoom.echo);
}
```

The transition system maintains both current and previous rooms in memory during transitions, allowing for smooth movement between areas.

## Scene Command System

The scene command system is the core mechanism for defining scene content and properties. Each command type handles a specific aspect of scene configuration.

### Command Handler Architecture

**Command Handler Table (`z_scene.c:531`):**
```c
SceneCmdHandlerFunc sSceneCmdHandlers[SCENE_CMD_ID_MAX] = {
    Scene_CommandPlayerEntryList,          // SCENE_CMD_ID_SPAWN_LIST
    Scene_CommandActorEntryList,           // SCENE_CMD_ID_ACTOR_LIST
    Scene_CommandUnused2,                  // SCENE_CMD_ID_UNUSED_2
    Scene_CommandCollisionHeader,          // SCENE_CMD_ID_COLLISION_HEADER
    Scene_CommandRoomList,                 // SCENE_CMD_ID_ROOM_LIST
    Scene_CommandWindSettings,             // SCENE_CMD_ID_WIND_SETTINGS
    Scene_CommandSpawnList,                // SCENE_CMD_ID_ENTRANCE_LIST
    Scene_CommandSpecialFiles,             // SCENE_CMD_ID_SPECIAL_FILES
    Scene_CommandRoomBehavior,             // SCENE_CMD_ID_ROOM_BEHAVIOR
    Scene_CommandUndefined9,               // SCENE_CMD_ID_UNDEFINED_9
    Scene_CommandRoomShape,                // SCENE_CMD_ID_ROOM_SHAPE
    Scene_CommandObjectList,               // SCENE_CMD_ID_OBJECT_LIST
    Scene_CommandLightList,                // SCENE_CMD_ID_LIGHT_LIST
    Scene_CommandPathList,                 // SCENE_CMD_ID_PATH_LIST
    Scene_CommandTransitionActorEntryList, // SCENE_CMD_ID_TRANSITION_ACTOR_LIST
    Scene_CommandLightSettingsList,        // SCENE_CMD_ID_LIGHT_SETTINGS_LIST
    Scene_CommandTimeSettings,             // SCENE_CMD_ID_TIME_SETTINGS
    Scene_CommandSkyboxSettings,           // SCENE_CMD_ID_SKYBOX_SETTINGS
    Scene_CommandSkyboxDisables,           // SCENE_CMD_ID_SKYBOX_DISABLES
    Scene_CommandExitList,                 // SCENE_CMD_ID_EXIT_LIST
    NULL,                                  // SCENE_CMD_ID_END
    Scene_CommandSoundSettings,            // SCENE_CMD_ID_SOUND_SETTINGS
    Scene_CommandEchoSettings,             // SCENE_CMD_ID_ECHO_SETTINGS
    Scene_CommandCutsceneData,             // SCENE_CMD_ID_CUTSCENE_DATA
    Scene_CommandAlternateHeaderList,      // SCENE_CMD_ID_ALTERNATE_HEADER_LIST
    Scene_CommandMiscSettings,             // SCENE_CMD_ID_MISC_SETTINGS
};
```

### Essential Scene Commands

#### Room List Command (0x04)
Defines the list of rooms available within the scene.

**Implementation (`z_scene.c:252`):**
```c
BAD_RETURN(s32) Scene_CommandRoomList(PlayState* play, SceneCmd* cmd) {
    play->roomList.count = cmd->roomList.length;
    play->roomList.romFiles = SEGMENTED_TO_VIRTUAL(cmd->roomList.data);
}
```

The room list contains ROM file pointers for each room, allowing the engine to load specific rooms on demand.

#### Collision Header Command (0x03)
Loads and initializes collision data for the scene.

**Implementation (`z_scene.c:244`):**
```c
BAD_RETURN(s32) Scene_CommandCollisionHeader(PlayState* play, SceneCmd* cmd) {
    CollisionHeader* colHeader = SEGMENTED_TO_VIRTUAL(cmd->colHeader.data);
    
    colHeader->vtxList = SEGMENTED_TO_VIRTUAL(colHeader->vtxList);
    colHeader->polyList = SEGMENTED_TO_VIRTUAL(colHeader->polyList);
    colHeader->surfaceTypeList = SEGMENTED_TO_VIRTUAL(colHeader->surfaceTypeList);
    colHeader->bgCamList = SEGMENTED_TO_VIRTUAL(colHeader->bgCamList);
    colHeader->waterBoxes = SEGMENTED_TO_VIRTUAL(colHeader->waterBoxes);
    
    BgCheck_Allocate(&play->colCtx, play, colHeader);
}
```

Collision data includes vertex lists, polygon definitions, surface types, camera regions, and water boxes.

#### Object List Command (0x0B)
Manages the loading and allocation of object files required by the scene.

**Implementation (`z_scene.c:291`):**
```c
BAD_RETURN(s32) Scene_CommandObjectList(PlayState* play, SceneCmd* cmd) {
    s32 i, j, k;
    ObjectEntry* entry;
    s16* objectListEntry = SEGMENTED_TO_VIRTUAL(cmd->objectList.data);
    
    // Handle existing objects
    while (i < play->objectCtx.numEntries) {
        if (entry->id != *objectListEntry) {
            // Invalidate objects no longer needed
            for (j = i; j < play->objectCtx.numEntries; j++) {
                invalidatedEntry->id = OBJECT_INVALID;
                invalidatedEntry++;
            }
            play->objectCtx.numEntries = i;
            Actor_KillAllWithMissingObject(play, &play->actorCtx);
            continue;
        }
        // Object matches, continue to next
    }
    
    // Load new objects
    while (k < cmd->objectList.length) {
        nextPtr = func_800982FC(&play->objectCtx, i, *objectListEntry);
        if (i < (ARRAY_COUNT(play->objectCtx.slots) - 1)) {
            entries[i + 1].segment = nextPtr;
        }
        i++; k++; objectListEntry++;
    }
    
    play->objectCtx.numEntries = i;
}
```

This command handles dynamic object loading, ensuring required assets are available while freeing unused objects.

#### Actor Entry List Command (0x01)
Defines the list of actors that should be spawned in rooms.

**Implementation (`z_scene.c:231`):**
```c
BAD_RETURN(s32) Scene_CommandActorEntryList(PlayState* play, SceneCmd* cmd) {
    play->numActorEntries = cmd->actorEntryList.length;
    play->actorEntryList = SEGMENTED_TO_VIRTUAL(cmd->actorEntryList.data);
}
```

Actor entries are stored in scene data and spawned when rooms are loaded.

#### Environmental Commands

**Skybox Settings (0x11):**
```c
BAD_RETURN(s32) Scene_CommandSkyboxSettings(PlayState* play, SceneCmd* cmd) {
    play->skyboxId = cmd->skyboxSettings.skyboxId;
    play->envCtx.skyboxConfig = play->envCtx.changeSkyboxNextConfig = cmd->skyboxSettings.skyboxConfig;
    play->envCtx.lightMode = cmd->skyboxSettings.envLightMode;
}
```

**Sound Settings (0x15):**
```c
BAD_RETURN(s32) Scene_CommandSoundSettings(PlayState* play, SceneCmd* cmd) {
    play->sceneSequences.seqId = cmd->soundSettings.seqId;
    play->sceneSequences.natureAmbienceId = cmd->soundSettings.natureAmbienceId;
    
    if (gSaveContext.seqId == (u8)NA_BGM_DISABLED) {
        SEQCMD_RESET_AUDIO_HEAP(0, cmd->soundSettings.specId);
    }
}
```

**Light Settings List (0x0F):**
```c
BAD_RETURN(s32) Scene_CommandLightSettingsList(PlayState* play, SceneCmd* cmd) {
    play->envCtx.numLightSettings = cmd->lightSettingList.length;
    play->envCtx.lightSettingsList = SEGMENTED_TO_VIRTUAL(cmd->lightSettingList.data);
}
```

## Memory Management

### Segmented Memory Architecture

OOT uses a segmented memory system where different types of data are assigned to specific segments:

**Segment Assignment:**
- **Segment 2**: Scene data (persistent for entire scene)
- **Segment 3**: Room data (changes with room transitions)
- **Segment 4**: Main gameplay objects (`object_gameplay_keep`)
- **Segment 5**: Sub-keep objects (scene-specific persistent objects)
- **Segment 6**: Regular objects (loaded per room)

**Segment Updates (`z_room.c:718`):**
```c
gSegments[3] = OS_K0_TO_PHYSICAL(roomCtx->curRoom.segment);
```

### Object Memory Management

**Object Context Initialization (`z_scene.c:75`):**
```c
void Object_InitContext(PlayState* play, ObjectContext* objectCtx) {
    u32 spaceSize;
    
    if (play->sceneId == SCENE_HYRULE_FIELD) {
        spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else if (play->sceneId == SCENE_GANON_BOSS) {
        spaceSize = 1150 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    } else {
        spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT;
    }
    
    objectCtx->spaceStart = objectCtx->slots[0].segment =
        GAME_STATE_ALLOC(&play->state, spaceSize, "../z_scene.c", 219);
    objectCtx->spaceEnd = (void*)((uintptr_t)objectCtx->spaceStart + spaceSize);
    
    objectCtx->mainKeepSlot = Object_SpawnPersistent(objectCtx, OBJECT_GAMEPLAY_KEEP);
    gSegments[4] = OS_K0_TO_PHYSICAL(objectCtx->slots[objectCtx->mainKeepSlot].segment);
}
```

Scene-specific memory allocation ensures optimal object space usage based on scene requirements.

**Object Loading and Validation (`z_scene.c:125`):**
```c
void Object_UpdateEntries(ObjectContext* objectCtx) {
    for (i = 0; i < objectCtx->numEntries; i++) {
        if (entry->id < 0) {
            if (entry->dmaRequest.vromAddr == 0) {
                osCreateMesgQueue(&entry->loadQueue, &entry->loadMsg, 1);
                objectFile = &gObjectTable[-entry->id];
                size = objectFile->vromEnd - objectFile->vromStart;
                
                DMA_REQUEST_ASYNC(&entry->dmaRequest, entry->segment, 
                                  objectFile->vromStart, size, 0, &entry->loadQueue,
                                  NULL, "../z_scene.c", 266);
            } else if (osRecvMesg(&entry->loadQueue, NULL, OS_MESG_NOBLOCK) == 0) {
                entry->id = -entry->id;
            }
        }
        entry++;
    }
}
```

Object loading uses asynchronous DMA with message queues to avoid blocking the main thread.

### Room Memory Allocation

**Room Memory Strategy:**
- **Current Room**: Always resident in memory
- **Previous Room**: Kept during transitions for smooth movement
- **Requested Room**: Loaded asynchronously before becoming current

**Memory Cleanup (`z_room.c:741`):**
```c
void Room_FinishRoomChange(PlayState* play, RoomContext* roomCtx) {
    // Delete the previous room
    roomCtx->prevRoom.num = -1;
    roomCtx->prevRoom.segment = NULL;
    
    // Clean up actors from previous room
    func_80031B14(play, &play->actorCtx);
    // Spawn new transition actors
    Actor_SpawnTransitionActors(play, &play->actorCtx);
}
```

## Scene Drawing and Rendering

### Scene-Specific Draw Configurations

The engine supports customized rendering for different scenes through draw configuration functions:

**Draw Configuration Table (`z_scene_table.c:145`):**
```c
SceneDrawConfigFunc sSceneDrawConfigs[SDC_MAX] = {
    Scene_DrawConfigDefault,                     // SDC_DEFAULT
    Scene_DrawConfigHyruleField,                 // SDC_HYRULE_FIELD
    Scene_DrawConfigKakarikoVillage,             // SDC_KAKARIKO_VILLAGE
    Scene_DrawConfigZorasRiver,                  // SDC_ZORAS_RIVER
    Scene_DrawConfigKokiriForest,                // SDC_KOKIRI_FOREST
    Scene_DrawConfigLakeHylia,                   // SDC_LAKE_HYLIA
    Scene_DrawConfigZorasDomain,                 // SDC_ZORAS_DOMAIN
    Scene_DrawConfigZorasFountain,               // SDC_ZORAS_FOUNTAIN
    Scene_DrawConfigGerudoValley,                // SDC_GERUDO_VALLEY
    // ... more configurations
};
```

**Scene Draw Function (`z_scene_table.c:206`):**
```c
void Scene_Draw(PlayState* play) {
    sSceneDrawConfigs[play->sceneDrawConfig](play);
}
```

**Example: Deku Tree Configuration (`z_scene_table.c:245`):**
```c
void Scene_DrawConfigDekuTree(PlayState* play) {
    u32 gameplayFrames = play->gameplayFrames;
    
    // Animated texture scrolling
    gSPSegment(POLY_XLU_DISP++, 0x09,
               Gfx_TwoTexScroll(play->state.gfxCtx, G_TX_RENDERTILE, 
                                127 - (gameplayFrames % 128),
                                (gameplayFrames * 1) % 128, 32, 32, 1, 
                                gameplayFrames % 128, (gameplayFrames * 1) % 128,
                                32, 32));
    
    // Day/night texture selection
    gSPSegment(POLY_OPA_DISP++, 0x08,
               SEGMENTED_TO_VIRTUAL(sDekuTreeEntranceTextures[gSaveContext.save.nightFlag]));
}
```

### Room Rendering Pipeline

**Room Drawing (`z_room.c:737`):**
```c
void Room_Draw(PlayState* play, Room* room, u32 flags) {
    if (room->segment != NULL) {
        gSegments[3] = OS_K0_TO_PHYSICAL(room->segment);
        sRoomDrawHandlers[room->roomShape->base.type](play, room, flags);
    }
}
```

**Rendering Integration (`z_play.c:1295`):**
```c
// Render scene background configuration
Scene_Draw(this);

// Render room geometry
Room_Draw(this, &this->roomCtx.curRoom, roomDrawFlags & (ROOM_DRAW_OPA | ROOM_DRAW_XLU));
Room_Draw(this, &this->roomCtx.prevRoom, roomDrawFlags & (ROOM_DRAW_OPA | ROOM_DRAW_XLU));
```

Both current and previous rooms are rendered during transitions to ensure smooth visual continuity.

## Debugging and Error Handling

### Scene Command Validation

**Command Bounds Checking (`z_scene.c:203`):**
```c
s32 Scene_ExecuteCommands(PlayState* play, SceneCmd* sceneCmd) {
    while (true) {
        u32 cmdCode = sceneCmd->base.code;
        
        PRINTF("*** Scene_Word = { code=%d, data1=%02x, data2=%04x } ***\n", 
               cmdCode, sceneCmd->base.data1, sceneCmd->base.data2);
        
        if (cmdCode == SCENE_CMD_ID_END) {
            break;
        }
        
        if (cmdCode < ARRAY_COUNT(sSceneCmdHandlers)) {
            sSceneCmdHandlers[cmdCode](play, sceneCmd);
        } else {
            PRINTF_COLOR_RED();
            PRINTF(T("code の値が異常です\n", "code variable is abnormal\n"));
            PRINTF_RST();
        }
        
        sceneCmd++;
    }
    return 0;
}
```

### Room Shape Validation

**Room Shape Type Checking (`z_room.c:737`):**
```c
void Room_Draw(PlayState* play, Room* room, u32 flags) {
    if (room->segment != NULL) {
        gSegments[3] = OS_K0_TO_PHYSICAL(room->segment);
        ASSERT(room->roomShape->base.type < ARRAY_COUNTU(sRoomDrawHandlers),
               "this->ground_shape->polygon.type < number(Room_Draw_Proc)", "../z_room.c", 1125);
        sRoomDrawHandlers[room->roomShape->base.type](play, room, flags);
    }
}
```

### Object Loading Error Handling

**Object Space Validation (`z_scene.c:195`):**
```c
void* func_800982FC(ObjectContext* objectCtx, s32 slot, s16 objectId) {
    ObjectEntry* entry = &objectCtx->slots[slot];
    RomFile* objectFile = &gObjectTable[objectId];
    u32 size = objectFile->vromEnd - objectFile->vromStart;
    
    void* nextPtr = (void*)ALIGN16((uintptr_t)entry->segment + size);
    
    ASSERT(nextPtr < objectCtx->spaceEnd, "nextptr < this->endSegment", "../z_scene.c", 381);
    
    PRINTF(T("オブジェクト入れ替え空きサイズ=%08x\n", "Object exchange free size=%08x\n"),
           (uintptr_t)objectCtx->spaceEnd - (uintptr_t)nextPtr);
    
    return nextPtr;
}
```

### Debug Logging

**Scene Loading Diagnostics (`z_play.c:1574`):**
```c
PRINTF("\nSCENE SIZE %fK\n", (scene->sceneFile.vromEnd - scene->sceneFile.vromStart) / 1024.0f);

// Later in room loading
PRINTF("ROOM SIZE=%fK\n", size / 1024.0f);
```

**Room Status Monitoring (`z_map_exp.c:205`):**
```c
void Map_InitRoomData(PlayState* play, s16 room) {
    PRINTF("＊＊＊＊＊＊＊\n＊＊＊＊＊＊＊\nroom_no=%d (%d)(%d)\n＊＊＊＊＊＊＊\n＊＊＊＊＊＊＊\n", 
           room, mapIndex, play->sceneId);
}
```

## Practical Implications for Modding

### Scene Modification Strategies

**Custom Scene Creation:**
Understanding the scene command system enables modders to create entirely new areas by:
1. **Defining scene headers** with appropriate commands
2. **Setting up room lists** with proper ROM file references
3. **Configuring collision data** for proper player movement
4. **Managing object dependencies** for required assets
5. **Establishing spawn points** and entrance/exit connections

**Scene Layer Customization:**
The layer system allows for:
- **Story-dependent variations** of existing areas
- **Time-based changes** (day/night differences)
- **Conditional modifications** based on player progress

### Room System Optimization

**Memory-Efficient Room Design:**
- **Minimize object usage** to reduce memory pressure
- **Use appropriate room shapes** (cullable for large areas, normal for small)
- **Optimize geometry complexity** based on performance requirements

**Room Transition Optimization:**
- **Strategic room boundaries** to minimize loading times
- **Proper transition actor placement** for smooth movement
- **Efficient asset sharing** between adjacent rooms

### Object Management Best Practices

**Object Allocation Strategy:**
```c
// Example: Scene-specific object space allocation
if (play->sceneId == SCENE_CUSTOM_AREA) {
    spaceSize = 1200 * 1024 - OBJECT_SPACE_ADJUSTMENT; // Larger space for complex scene
} else {
    spaceSize = 1000 * 1024 - OBJECT_SPACE_ADJUSTMENT; // Standard allocation
}
```

**Object Dependency Management:**
- **Minimize object count** to reduce loading overhead
- **Share objects between rooms** when possible
- **Use persistent objects** for frequently accessed assets

### Custom Scene Commands

**Extending the Command System:**
Modders can potentially add new scene commands by:
1. **Defining new command IDs** in the command enumeration
2. **Implementing handler functions** following the existing pattern
3. **Adding entries to the handler table** for command processing
4. **Integrating with scene compilation tools** for asset generation

### Performance Considerations

**Scene Loading Optimization:**
- **Minimize scene file size** through efficient data packing
- **Optimize room geometry** for the target room shape type
- **Balance object loading** between scene and room levels

**Rendering Performance:**
- **Use appropriate draw configurations** for scene-specific effects
- **Implement efficient culling** for large outdoor areas
- **Optimize texture usage** to minimize memory bandwidth

### Testing and Validation

**Scene Testing Workflow:**
1. **Verify command parsing** through debug output
2. **Test memory allocation** across different scenarios
3. **Validate room transitions** for smooth gameplay
4. **Profile rendering performance** under various conditions

**Common Pitfalls:**
- **Memory overflow** from excessive object allocation
- **Segmentation faults** from improper pointer handling
- **Asset loading failures** from incorrect ROM file references
- **Collision issues** from malformed collision data

## Conclusion

The OOT scene/room system represents a sophisticated approach to world organization that balances memory efficiency with gameplay flexibility. The hierarchical design allows for complex, interconnected worlds while maintaining stable performance on the N64's limited hardware. The command-based scene definition system provides a flexible framework for defining diverse environments, from simple indoor rooms to complex outdoor areas with advanced rendering effects.

Understanding this system is crucial for effective OOT modding, as it forms the foundation for all world-building activities. The careful balance between memory management, loading performance, and rendering quality demonstrates the thoughtful engineering that went into creating one of gaming's most memorable worlds.

The modular design of the scene/room system continues to serve as an excellent reference for modern game engine architecture, showing how careful abstraction and systematic organization can enable rich, complex game worlds within tight resource constraints. 