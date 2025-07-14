# OOT Graphics Rendering Pipeline Deep Dive

## Overview

This document provides a comprehensive analysis of the Graphics Rendering Pipeline in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The graphics pipeline is a sophisticated system that manages display lists, handles frame rendering, and coordinates between the main CPU and the Reality Signal Processor (RSP) to produce the final rendered output.

## Architecture Overview

### Graphics Context Structure

The graphics system centers around the `GraphicsContext` structure, which manages all rendering state and resources:

**Core Components:**
- **Display Lists**: Buffers for graphics commands (POLY_OPA_DISP, POLY_XLU_DISP, OVERLAY_DISP, WORK_DISP)
- **Frame Buffers**: Double-buffered rendering targets
- **Task Management**: RSP task scheduling and execution
- **Memory Management**: Graphics memory allocation and tracking

### Main Graphics Thread

**Graphics Thread Entry (`graph.c:481`):**
```c
void Graph_ThreadEntry(void* arg0) {
    GraphicsContext gfxCtx;
    GameState* gameState;
    u32 size;
    GameStateOverlay* nextOvl = &gGameStateOverlayTable[GAMESTATE_SETUP];
    
    PRINTF(T("グラフィックスレッド実行開始\n", "Start graphics thread execution\n"));
    
    Graph_Init(&gfxCtx);
    
    while (nextOvl != NULL) {
        ovl = nextOvl;
        Overlay_LoadGameState(ovl);
        
        size = ovl->instanceSize;
        gameState = SYSTEM_ARENA_MALLOC(size, "../graph.c", 1196);
        
        GameState_Init(gameState, ovl->init, &gfxCtx);
        
        while (GameState_IsRunning(gameState)) {
            Graph_Update(&gfxCtx, gameState);
        }
        
        nextOvl = Graph_GetNextGameState(gameState);
        GameState_Destroy(gameState);
        SYSTEM_ARENA_FREE(gameState, "../graph.c", 1227);
        Overlay_FreeGameState(ovl);
    }
    
    Graph_Destroy(&gfxCtx);
}
```

## Frame Rendering Pipeline

### Frame Update Cycle

The core rendering cycle is orchestrated by `Graph_Update()`:

**Main Update Function (`graph.c:325`):**
```c
void Graph_Update(GraphicsContext* gfxCtx, GameState* gameState) {
    gameState->inPreNMIState = false;
    Graph_InitTHGA(gfxCtx);
    
    // Process game state updates
    GameState_ReqPadData(gameState);
    GameState_Update(gameState);
    
    // Set up display list branching
    OPEN_DISPS(gfxCtx, "../graph.c", 999);
    
    gSPBranchList(WORK_DISP++, gfxCtx->polyOpaBuffer);
    gSPBranchList(POLY_OPA_DISP++, gfxCtx->polyXluBuffer);
    gSPBranchList(POLY_XLU_DISP++, gfxCtx->overlayBuffer);
    gDPPipeSync(OVERLAY_DISP++);
    gDPFullSync(OVERLAY_DISP++);
    gSPEndDisplayList(OVERLAY_DISP++);
    
    CLOSE_DISPS(gfxCtx, "../graph.c", 1028);
}
```

### Display List Management

The graphics system uses four main display lists:

1. **WORK_DISP**: Work buffer for temporary graphics operations
2. **POLY_OPA_DISP**: Opaque geometry rendering
3. **POLY_XLU_DISP**: Translucent geometry rendering  
4. **OVERLAY_DISP**: UI and overlay elements

**Display List Initialization (`graph.c:129`):**
```c
void Graph_InitTHGA(GraphicsContext* gfxCtx) {
    GraphicsContext* gfxCtx2 = gfxCtx;
    TwoHeadGfxArena* thga = &gfxCtx2->polyOpa;
    
    thga->p = thga->start;
    thga->d = (u8*)thga->start + thga->size;
    
    gfxCtx2->polyOpaBuffer = (Gfx*)thga->p;
    gfxCtx2->polyXluBuffer = (Gfx*)thga->d;
    gfxCtx2->overlayBuffer = (Gfx*)thga->d;
    
    gfxCtx2->workBuffer = (Gfx*)thga->p;
    gfxCtx2->workBufferSize = 0x1000;
}
```

### Two-Head Graphics Arena (THGA)

**Memory Management System:**
The THGA system manages graphics memory allocation from both ends of a buffer:

**Allocation Functions (`graph.c:528`):**
```c
void* Graph_Alloc(GraphicsContext* gfxCtx, size_t size) {
    TwoHeadGfxArena* thga = &gfxCtx->polyOpa;
    
    if (HREG(59) == 1) {
        PRINTF("graph_alloc siz=%d thga size=%08x bufp=%08x head=%08x tail=%08x\n", 
               size, thga->size, thga->start, thga->p, thga->d);
    }
    
    return THGA_AllocTail(&gfxCtx->polyOpa, ALIGN16(size));
}
```

## RSP Graphics Processing

### RSP Task Structure

**Task Creation (`graph.c:194`):**
```c
void Graph_TaskSet00(GraphicsContext* gfxCtx) {
    static s32 retryCount = 0;
    OSTask_t* task = &gfxCtx->task.t;
    OSTimer timer;
    
    if (gfxCtx->workBuffer != NULL) {
        Graph_UCodeFaultClient(gfxCtx->workBuffer);
        Graph_DisassembleUCode(gfxCtx->workBuffer);
    }
    
    gfxCtx->workBuffer = NULL;
    
    // Set up RSP task
    task->type = M_GFXTASK;
    task->flags = 0;
    task->ucode_boot = (u64*)gspF3DZEX2_NoN_PosLight_fifoTextStart;
    task->ucode_boot_size = SP_UCODE_SIZE;
    task->ucode = (u64*)gspF3DZEX2_NoN_PosLight_fifoTextStart;
    task->ucode_size = SP_UCODE_SIZE;
    task->data_ptr = (u64*)gfxCtx->workBuffer;
    task->data_size = (u32)gfxCtx->workBufferSize;
    task->dram_stack = (u64*)gfxCtx->workBuffer;
    task->dram_stack_size = 0x1000;
    task->output_buff = (u64*)gfxCtx->workBuffer;
    task->output_buff_size = gfxCtx->workBufferSize;
    task->yield_data_ptr = (u64*)gfxCtx->workBuffer;
    task->yield_data_size = OS_YIELD_DATA_SIZE;
}
```

### Microcode and Display Lists

The RSP uses F3DZEX2 microcode for high-performance graphics processing:

**Microcode Types:**
- **F3DZEX2**: Primary graphics microcode for 3D rendering
- **S2DEX**: 2D sprite/image processing microcode

**Display List Processing:**
Display lists contain graphics commands that are processed by the RSP:

```c
// Example display list commands
gSPDisplayList(POLY_OPA_DISP++, someDisplayList);
gDPSetPrimColor(POLY_OPA_DISP++, 0, 0, 255, 255, 255, 255);
gSPMatrix(POLY_OPA_DISP++, matrixPtr, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
```

## Scene Rendering Integration

### Scene Draw Pipeline

**Scene Drawing (`z_scene_table.c:206`):**
```c
void Scene_Draw(PlayState* play) {
    sSceneDrawConfigs[play->sceneDrawConfig](play);
}
```

**Frame Setup (`z_rcp.c:1489`):**
```c
void Gfx_SetupFrame(GraphicsContext* gfxCtx, u8 r, u8 g, u8 b) {
    OPEN_DISPS(gfxCtx, "../z_rcp.c", 2386);
    
    // Set up RDP render state for rectangles in FILL mode
    gSPDisplayList(POLY_OPA_DISP++, sFillSetupDL);
    gSPDisplayList(POLY_XLU_DISP++, sFillSetupDL);
    gSPDisplayList(OVERLAY_DISP++, sFillSetupDL);
    
    // Set scissor region to full screen
    gDPSetScissor(POLY_OPA_DISP++, G_SC_NON_INTERLACE, 0, 0, gScreenWidth, gScreenHeight);
    gDPSetScissor(POLY_XLU_DISP++, G_SC_NON_INTERLACE, 0, 0, gScreenWidth, gScreenHeight);
    gDPSetScissor(OVERLAY_DISP++, G_SC_NON_INTERLACE, 0, 0, gScreenWidth, gScreenHeight);
    
    // Set up framebuffer
    gDPSetColorImage(POLY_OPA_DISP++, G_IM_FMT_RGBA, G_IM_SIZ_16b, gScreenWidth, gfxCtx->curFrameBuffer);
    gDPSetColorImage(POLY_XLU_DISP++, G_IM_FMT_RGBA, G_IM_SIZ_16b, gScreenWidth, gfxCtx->curFrameBuffer);
    gDPSetColorImage(OVERLAY_DISP++, G_IM_FMT_RGBA, G_IM_SIZ_16b, gScreenWidth, gfxCtx->curFrameBuffer);
    
    // Set up z-buffer
    gDPSetDepthImage(POLY_OPA_DISP++, gZBuffer);
    gDPSetDepthImage(POLY_XLU_DISP++, gZBuffer);
    gDPSetDepthImage(OVERLAY_DISP++, gZBuffer);
    
    CLOSE_DISPS(gfxCtx, "../z_rcp.c", 2513);
}
```

### Play State Rendering

**Main Rendering Function (`z_play.c:1167`):**
```c
void Play_Draw(PlayState* this) {
    GraphicsContext* gfxCtx = this->state.gfxCtx;
    
    OPEN_DISPS(gfxCtx, "../z_play.c", 3907);
    
    // Set up segments
    gSegments[4] = OS_K0_TO_PHYSICAL(this->objectCtx.slots[this->objectCtx.mainKeepSlot].segment);
    gSegments[5] = OS_K0_TO_PHYSICAL(this->objectCtx.slots[this->objectCtx.subKeepSlot].segment);
    gSegments[2] = OS_K0_TO_PHYSICAL(this->sceneSegment);
    
    // Set up display lists
    gSPSegment(POLY_OPA_DISP++, 0x04, this->objectCtx.slots[this->objectCtx.mainKeepSlot].segment);
    gSPSegment(POLY_XLU_DISP++, 0x04, this->objectCtx.slots[this->objectCtx.mainKeepSlot].segment);
    gSPSegment(OVERLAY_DISP++, 0x04, this->objectCtx.slots[this->objectCtx.mainKeepSlot].segment);
    
    Gfx_SetupFrame(gfxCtx, 0, 0, 0);
    
    // Scene-specific drawing
    if (R_PLAY_DRAW_SKYBOX) {
        if (this->skyboxId && (this->skyboxId != SKYBOX_UNSET_1D) && !this->envCtx.skyboxDisabled) {
            Skybox_Draw(&this->skyboxCtx, gfxCtx, this->skyboxId, this->envCtx.skyboxBlend,
                       this->view.eye.x, this->view.eye.y, this->view.eye.z);
        }
    }
    
    // Draw room geometry
    Room_Draw(this, &this->roomCtx.curRoom, roomDrawFlags & (ROOM_DRAW_OPA | ROOM_DRAW_XLU));
    
    // Draw actors
    if (R_PLAY_DRAW_ACTORS) {
        Actor_DrawAll(this, &this->actorCtx);
    }
    
    CLOSE_DISPS(gfxCtx, "../z_play.c", 4508);
}
```

## Camera and View System

### View Matrix Setup

**View System (`z_view.c:284`):**
```c
s32 View_Apply(View* view, s32 mask) {
    mask = (view->flags & mask) | (mask >> 4);
    
    if (mask & VIEW_PROJECTION_ORTHO) {
        return View_ApplyOrtho(view);
    } else {
        return View_ApplyPerspective(view);
    }
}
```

**Perspective Projection (`z_view.c:343`):**
```c
s32 View_ApplyPerspective(View* view) {
    GraphicsContext* gfxCtx = view->gfxCtx;
    Vp* vp;
    Mtx* projection;
    Mtx* viewing;
    f32 aspect;
    
    OPEN_DISPS(gfxCtx, "../z_view.c", 596);
    
    // Set up viewport
    vp = GRAPH_ALLOC(gfxCtx, sizeof(Vp));
    View_ViewportToVp(vp, &view->viewport);
    view->vp = *vp;
    
    gSPViewport(POLY_OPA_DISP++, vp);
    gSPViewport(POLY_XLU_DISP++, vp);
    
    // Set up projection matrix
    projection = GRAPH_ALLOC(gfxCtx, sizeof(Mtx));
    view->projectionPtr = projection;
    
    width = view->viewport.rightX - view->viewport.leftX;
    height = view->viewport.bottomY - view->viewport.topY;
    aspect = (f32)width / (f32)height;
    
    guPerspective(projection, &view->normal, view->fovy, aspect, 
                  view->zNear, view->zFar, view->scale);
    
    gSPPerspNormalize(POLY_OPA_DISP++, view->normal);
    gSPMatrix(POLY_OPA_DISP++, projection, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_PROJECTION);
    
    CLOSE_DISPS(gfxCtx, "../z_view.c", 996);
    
    return 1;
}
```

## Actor Rendering System

### Actor Draw Pipeline

**Actor Drawing (`z_actor.c:2592`):**
```c
void Actor_Draw(PlayState* play, Actor* actor) {
    Lights* lights;
    
    OPEN_DISPS(play->state.gfxCtx, "../z_actor.c", 6026);
    
    // Set up object segment
    gSPSegment(POLY_OPA_DISP++, 0x06, play->objectCtx.slots[actor->objectSlot].segment);
    gSPSegment(POLY_XLU_DISP++, 0x06, play->objectCtx.slots[actor->objectSlot].segment);
    
    // Apply color filters
    if (actor->colorFilterTimer != 0) {
        Color_RGBA8 color = { 0, 0, 0, 255 };
        
        if (actor->colorFilterParams & COLORFILTER_COLORFLAG_RED) {
            color.r = COLORFILTER_GET_COLORINTENSITY(actor->colorFilterParams) | 7;
        }
        
        func_80026400(play, &color, actor->colorFilterTimer, 
                     COLORFILTER_GET_DURATION(actor->colorFilterParams));
    }
    
    // Call actor's draw function
    actor->draw(actor, play);
    
    // Clean up color filters
    if (actor->colorFilterTimer != 0) {
        func_80026608(play);
    }
    
    CLOSE_DISPS(play->state.gfxCtx, "../z_actor.c", 6119);
}
```

### Actor Rendering Loop

**Actor Draw All (`z_actor.c:2873`):**
```c
void Actor_DrawAll(PlayState* play, ActorContext* actorCtx) {
    Actor* actor;
    ActorListEntry* actorListEntry;
    
    OPEN_DISPS(play->state.gfxCtx, "../z_actor.c", 6336);
    
    actorListEntry = &actorCtx->actorLists[0];
    
    for (i = 0; i < ARRAY_COUNT(actorCtx->actorLists); i++, actorListEntry++) {
        actor = actorListEntry->head;
        
        while (actor != NULL) {
            if (Actor_CullingCheck(play, actor)) {
                actor->flags |= ACTOR_FLAG_INSIDE_CULLING_VOLUME;
            } else {
                actor->flags &= ~ACTOR_FLAG_INSIDE_CULLING_VOLUME;
            }
            
            if ((actor->flags & ACTOR_FLAG_INSIDE_CULLING_VOLUME) && 
                (actor->draw != NULL)) {
                
                Actor_Draw(play, actor);
                actor->isDrawn = true;
            }
            
            actor = actor->next;
        }
    }
    
    CLOSE_DISPS(play->state.gfxCtx, "../z_actor.c", 6336);
}
```

## Skybox System

### Skybox Rendering

**Skybox Drawing (`z_vr_box_draw.c:47`):**
```c
void Skybox_Draw(SkyboxContext* skyboxCtx, GraphicsContext* gfxCtx, s16 skyboxId, 
                 s16 blend, f32 x, f32 y, f32 z) {
    OPEN_DISPS(gfxCtx, "../z_vr_box_draw.c", 52);
    
    Gfx_SetupDL_40Opa(gfxCtx);
    
    // Set up segments
    gSPSegment(POLY_OPA_DISP++, 0x7, skyboxCtx->staticSegments[0]);
    gSPSegment(POLY_OPA_DISP++, 0x8, skyboxCtx->staticSegments[1]);
    gSPSegment(POLY_OPA_DISP++, 0x9, skyboxCtx->palettes);
    
    gDPSetPrimColor(POLY_OPA_DISP++, 0x00, 0x00, 0, 0, 0, blend);
    gSPTexture(POLY_OPA_DISP++, 0x8000, 0x8000, 0, G_TX_RENDERTILE, G_ON);
    
    // Prepare matrix
    sSkyboxDrawMatrix = GRAPH_ALLOC(gfxCtx, sizeof(Mtx));
    Matrix_Translate(x, y, z, MTXMODE_NEW);
    Matrix_Scale(1.0f, 1.0f, 1.0f, MTXMODE_APPLY);
    Matrix_RotateX(skyboxCtx->rot.x, MTXMODE_APPLY);
    Matrix_RotateY(skyboxCtx->rot.y, MTXMODE_APPLY);
    Matrix_RotateZ(skyboxCtx->rot.z, MTXMODE_APPLY);
    MATRIX_TO_MTX(sSkyboxDrawMatrix, "../z_vr_box_draw.c", 76);
    
    gSPMatrix(POLY_OPA_DISP++, sSkyboxDrawMatrix, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
    
    // Configure texture filtering
    gDPSetColorDither(POLY_OPA_DISP++, G_CD_MAGICSQ);
    gDPSetTextureFilter(POLY_OPA_DISP++, G_TF_BILERP);
    
    // Load palette and set texture mode
    gDPLoadTLUT_pal256(POLY_OPA_DISP++, skyboxCtx->palettes[0]);
    gDPSetTextureLUT(POLY_OPA_DISP++, G_TT_RGBA16);
    
    CLOSE_DISPS(gfxCtx, "../z_vr_box_draw.c", 52);
}
```

## Setup Display Lists

### Pre-configured Display Lists

**Setup Display Lists (`z_rcp.c:9`):**
```c
Gfx sSetupDL[SETUPDL_MAX][6] = {
    {
        /* SETUPDL_0 */
        gsDPPipeSync(),
        gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON),
        gsDPSetCombineLERP(PRIMITIVE, ENVIRONMENT, TEXEL0, ENVIRONMENT, PRIMITIVE, 0, TEXEL0, 0, 
                           0, 0, 0, COMBINED, 0, 0, 0, COMBINED),
        gsDPSetOtherMode(G_AD_NOISE | G_CD_NOISE | G_CK_NONE | G_TC_FILT | G_TF_BILERP | G_TT_NONE | 
                         G_TL_TILE | G_TD_CLAMP | G_TP_PERSP | G_CYC_2CYCLE | G_PM_NPRIMITIVE,
                         G_AC_NONE | G_ZS_PIXEL | G_RM_FOG_SHADE_A | G_RM_ZB_CLD_SURF2),
        gsSPLoadGeometryMode(G_ZBUFFER | G_SHADE | G_CULL_BACK | G_FOG | G_SHADING_SMOOTH),
        gsSPEndDisplayList(),
    },
    // ... more setup configurations
};
```

## Room Drawing System

### Room Shape Rendering

**Room Drawing (`z_room.c:737`):**
```c
void Room_Draw(PlayState* play, Room* room, u32 flags) {
    if (room->segment != NULL) {
        gSegments[3] = OS_K0_TO_PHYSICAL(room->segment);
        sRoomDrawHandlers[room->roomShape->base.type](play, room, flags);
    }
}
```

**Room Shape Types:**
- **ROOM_SHAPE_TYPE_NORMAL**: Standard geometry rendering
- **ROOM_SHAPE_TYPE_CULLABLE**: Frustum culling optimization
- **ROOM_SHAPE_TYPE_IMAGE**: Pre-rendered background images

## Performance Optimization

### Culling System

**Frustum Culling (`z_room.c:127`):**
```c
void Room_DrawCullable(PlayState* play, Room* room, u32 flags) {
    RoomShapeCullable* roomShape = &room->roomShape->cullable;
    
    // Perform frustum culling
    for (each entry) {
        // Transform bounding sphere to view space
        // Cull entries outside view frustum
        // Insert remaining entries into Z-sorted linked list
    }
    
    // Render entries from nearest to furthest
    for (iter = head; iter != NULL; iter = iter->next) {
        gSPDisplayList(POLY_OPA_DISP++, iter->opa);
        gSPDisplayList(POLY_XLU_DISP++, iter->xlu);
    }
}
```

### Memory Management

**Graphics Memory Allocation:**
- **THGA System**: Two-headed arena allocation
- **Segment Management**: Efficient memory segmentation
- **Buffer Management**: Double-buffered rendering

## Debug and Development Features

### Debug Display Lists

**UCode Disassembly (`graph.c:72`):**
```c
void Graph_DisassembleUCode(Gfx* workBuf) {
    UCodeDisas disassembler;
    
    if (R_HREG_MODE == HREG_MODE_UCODE_DISAS && R_UCODE_DISAS_TOGGLE != 0) {
        UCodeDisas_Init(&disassembler);
        disassembler.enableLog = R_UCODE_DISAS_LOG_LEVEL;
        
        UCodeDisas_RegisterUCode(&disassembler, ARRAY_COUNT(D_8012D230), D_8012D230);
        UCodeDisas_SetCurUCode(&disassembler, gspF3DZEX2_NoN_PosLight_fifoTextStart);
        
        UCodeDisas_Disassemble(&disassembler, workBuf);
        
        // Update debug registers with stats
        R_UCODE_DISAS_VTX_COUNT = disassembler.vtxCnt;
        R_UCODE_DISAS_TRI1_COUNT = disassembler.tri1Cnt;
        R_UCODE_DISAS_TRI2_COUNT = disassembler.tri2Cnt;
    }
}
```

### Fault Handling

**Graphics Fault Client (`graph.c:58`):**
```c
void Graph_FaultClient(void) {
    void* nextFb = osViGetNextFramebuffer();
    void* newFb = (SysCfb_GetFbPtr(0) != nextFb) ? SysCfb_GetFbPtr(0) : SysCfb_GetFbPtr(1);
    
    osViSwapBuffer(newFb);
    Fault_WaitForInput();
    osViSwapBuffer(nextFb);
}
```

## Integration with Game Systems

### GameState Integration

**GameState Draw Function (`game.c:195`):**
```c
void GameState_Draw(GameState* gameState, GraphicsContext* gfxCtx) {
    Gfx* newDList;
    Gfx* polyOpaP;
    
    OPEN_DISPS(gfxCtx, "../game.c", 746);
    
    newDList = Gfx_Open(polyOpaP = POLY_OPA_DISP);
    gSPDisplayList(OVERLAY_DISP++, newDList);
    
    if (R_ENABLE_FB_FILTER == 1) {
        GameState_SetFBFilter(&newDList);
    }
    
    gSPEndDisplayList(newDList++);
    Gfx_Close(polyOpaP, newDList);
    POLY_OPA_DISP = newDList;
    
    CLOSE_DISPS(gfxCtx, "../game.c", 800);
    
    Debug_DrawText(gfxCtx);
}
```

### Frame Buffer Management

**Frame Buffer Setup (`game.c:814`):**
```c
void GameState_SetFrameBuffer(GraphicsContext* gfxCtx) {
    OPEN_DISPS(gfxCtx, "../game.c", 814);
    
    gSPSegment(POLY_OPA_DISP++, 0, 0);
    gSPSegment(POLY_OPA_DISP++, 0xF, gfxCtx->curFrameBuffer);
    gSPSegment(POLY_OPA_DISP++, 0xE, gZBuffer);
    gSPSegment(POLY_XLU_DISP++, 0, 0);
    gSPSegment(POLY_XLU_DISP++, 0xF, gfxCtx->curFrameBuffer);
    gSPSegment(POLY_XLU_DISP++, 0xE, gZBuffer);
    gSPSegment(OVERLAY_DISP++, 0, 0);
    gSPSegment(OVERLAY_DISP++, 0xF, gfxCtx->curFrameBuffer);
    gSPSegment(OVERLAY_DISP++, 0xE, gZBuffer);
    
    CLOSE_DISPS(gfxCtx, "../game.c", 838);
}
```

## Practical Implications for Modding

### Custom Graphics Implementation

**Adding Custom Display Lists:**
1. **Allocation**: Use `GRAPH_ALLOC()` for temporary graphics memory
2. **Display List Building**: Build command sequences targeting specific buffers
3. **Segment Management**: Properly set up memory segments for textures and geometry
4. **Integration**: Hook into existing draw functions or create new ones

**Example Custom Draw Function:**
```c
void CustomObject_Draw(CustomObject* this, PlayState* play) {
    GraphicsContext* gfxCtx = play->state.gfxCtx;
    
    OPEN_DISPS(gfxCtx, "../custom_object.c", 100);
    
    // Set up object segment
    gSPSegment(POLY_OPA_DISP++, 0x06, 
               play->objectCtx.slots[this->actor.objectSlot].segment);
    
    // Apply transformations
    Matrix_Push();
    Matrix_Translate(this->actor.world.pos.x, this->actor.world.pos.y, 
                    this->actor.world.pos.z, MTXMODE_NEW);
    Matrix_Scale(this->actor.scale.x, this->actor.scale.y, this->actor.scale.z, MTXMODE_APPLY);
    
    // Set up matrix
    gSPMatrix(POLY_OPA_DISP++, MATRIX_NEW(gfxCtx, "../custom_object.c", 120),
              G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
    
    // Draw geometry
    gSPDisplayList(POLY_OPA_DISP++, gCustomObjectDisplayList);
    
    Matrix_Pop();
    
    CLOSE_DISPS(gfxCtx, "../custom_object.c", 130);
}
```

### Performance Optimization Strategies

**Memory Management:**
- **Efficient Allocation**: Use THGA system appropriately
- **Segment Optimization**: Minimize segment switches
- **Buffer Management**: Balance between display list sizes

**Culling Optimization:**
- **Frustum Culling**: Implement for complex scenes
- **LOD Systems**: Level-of-detail for distant objects
- **Occlusion Culling**: Hide objects behind others

**Display List Optimization:**
- **Batch Similar Operations**: Group similar render states
- **Minimize State Changes**: Reduce RSP pipeline stalls
- **Efficient Matrix Operations**: Use hardware matrix stack

## Common Issues and Solutions

### Debug Techniques

**Graphics Debugging:**
1. **Display List Inspection**: Use UCode disassembly features
2. **Memory Tracking**: Monitor THGA allocation
3. **Performance Profiling**: Track RSP task timing
4. **Visual Debugging**: Use debug draw functions

**Common Problems:**
- **Memory Overflow**: THGA allocation failures
- **Display List Corruption**: Improper command sequences
- **Segment Faults**: Incorrect memory segment setup
- **Performance Issues**: Inefficient rendering paths

### Best Practices

**Code Organization:**
- **Modular Design**: Separate draw functions by object type
- **Error Handling**: Proper validation and assertions
- **Documentation**: Clear commenting of graphics operations
- **Testing**: Comprehensive validation across scenarios

**Performance Guidelines:**
- **Minimize Allocations**: Reuse graphics memory where possible
- **Efficient Rendering**: Batch operations and minimize state changes
- **Culling Implementation**: Use appropriate culling for scene complexity
- **Memory Management**: Careful THGA usage and segment management

## Conclusion

The OOT graphics rendering pipeline represents a sophisticated approach to 3D rendering on the N64 hardware. The system's design around display lists, RSP processing, and efficient memory management enables complex 3D worlds within strict hardware constraints.

Key architectural strengths include:
- **Scalable Design**: Handles simple to complex scenes efficiently
- **Memory Efficiency**: THGA system optimizes graphics memory usage
- **Performance Optimization**: Multiple culling and optimization strategies
- **Modular Structure**: Clean separation between systems
- **Debug Support**: Comprehensive debugging and profiling tools

Understanding this pipeline is essential for effective OOT modding, as it forms the foundation for all visual content in the game. The careful balance between performance, memory usage, and visual quality demonstrates expert engineering that continues to serve as a reference for modern game development. 