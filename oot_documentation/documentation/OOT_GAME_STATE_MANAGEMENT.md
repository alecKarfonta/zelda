# OOT Game State Management System Deep Dive

## Overview

This document provides a comprehensive analysis of the Game State Management System in The Legend of Zelda: Ocarina of Time (OOT) based on examination of the actual decomp source code. The game state system is responsible for managing the overall flow of the game, handling transitions between different modes (title screen, file select, gameplay, etc.), and providing a framework for the game's main loop architecture.

## Architecture Overview

### Game State Structure

The game state system centers around the `GameState` structure, which serves as the base for all game modes:

**Core Components:**
- **State Function Pointers**: Main update and destroy functions for each state
- **Graphics Context**: Connection to the graphics rendering system
- **Input Management**: Interface to controller input system
- **Memory Management**: Allocation and cleanup for state-specific resources
- **Transition Control**: Mechanisms for switching between states

### Game State Lifecycle

**Game State Entry (`game.c:461`):**
```c
void GameState_Init(GameState* gameState, GameStateFunc init, GraphicsContext* gfxCtx) {
    UNUSED_NDEBUG OSTime startTime;
    UNUSED_NDEBUG OSTime endTime;

    PRINTF(T("game コンストラクタ開始\n", "game constructor start\n"));
    gameState->gfxCtx = gfxCtx;
    gameState->frames = 0;
    gameState->main = NULL;
    gameState->destroy = NULL;
    gameState->running = 1;
    startTime = osGetTime();

    // These assignments must be written this way for matching and to avoid a warning due to casting a pointer to an
    // integer without a cast. This assigns init = NULL and size = 0.
    gameState->size = (u32)(gameState->init = NULL);

    {
        s32 requiredScopeTemp;
        endTime = osGetTime();
        PRINTF(T("game_set_next_game_null 処理時間 %d us\n", "game_set_next_game_null processing time %d us\n"),
               OS_CYCLES_TO_USEC(endTime - startTime));
        startTime = endTime;
        GameAlloc_Init(&gameState->alloc);
    }

    endTime = osGetTime();
    PRINTF(T("gamealloc_init 処理時間 %d us\n", "gamealloc_init processing time %d us\n"),
           OS_CYCLES_TO_USEC(endTime - startTime));
    startTime = endTime;
    GameState_InitArena(gameState, 0x100000);

    R_UPDATE_RATE = 3;
    init(gameState);
    endTime = osGetTime();
    PRINTF(T("init 処理時間 %d us\n", "init processing time %d us\n"), OS_CYCLES_TO_USEC(endTime - startTime));

    startTime = endTime;
    LOG_UTILS_CHECK_NULL_POINTER("this->cleanup", gameState->destroy, "../game.c", 1088);
    VisCvg_Init(&sVisCvg);
    VisZBuf_Init(&sVisZBuf);
    VisMono_Init(&sVisMono);
    if ((R_VI_MODE_EDIT_STATE == VI_MODE_EDIT_STATE_INACTIVE) || !DEBUG_FEATURES) {
        ViMode_Init(&sViMode);
    }
    SpeedMeter_Init(&D_801664D0);
    Rumble_Init();
    osSendMesg(&gameState->gfxCtx->queue, NULL, OS_MESG_BLOCK);
    endTime = osGetTime();
    PRINTF(T("その他初期化 処理時間 %d us\n", "Other initialization processing time %d us\n"),
           OS_CYCLES_TO_USEC(endTime - startTime));

#if DEBUG_FEATURES
    Fault_AddClient(&sGameFaultClient, GameState_FaultPrint, NULL, NULL);
#endif

    PRINTF(T("game コンストラクタ終了\n", "game constructor end\n"));
}
```

### Game State Update Loop

**Main Update Function (`game.c:294`):**
```c
void GameState_Update(GameState* gameState) {
    GraphicsContext* gfxCtx = gameState->gfxCtx;

    GameState_SetFrameBuffer(gfxCtx);

    gameState->main(gameState);

#if PLATFORM_N64
    if (D_80121212 != 0) {
        func_801C7E78();
    }
    if ((B_80121220 != NULL) && (B_80121220->unk_74 != NULL)) {
        B_80121220->unk_74(gameState);
    }
#endif

    func_800C4344(gameState);

#if OOT_VERSION < PAL_1_0
    if (R_VI_MODE_EDIT_STATE != VI_MODE_EDIT_STATE_INACTIVE) {
        ViMode_Update(&sViMode, &gameState->input[0]);
        gfxCtx->viMode = &sViMode.customViMode;
        gfxCtx->viFeatures = sViMode.viFeatures;
    }
#endif

#if OOT_VERSION >= PAL_1_0 && DEBUG_FEATURES
    if (SREG(63) == 1u) {
        if (R_VI_MODE_EDIT_STATE < VI_MODE_EDIT_STATE_INACTIVE) {
            R_VI_MODE_EDIT_STATE = VI_MODE_EDIT_STATE_INACTIVE;
            gfxCtx->viMode = &gViConfigMode;
            gfxCtx->viFeatures = gViConfigFeatures;
            gfxCtx->xScale = gViConfigXScale;
            gfxCtx->yScale = gViConfigYScale;
        } else if (R_VI_MODE_EDIT_STATE > VI_MODE_EDIT_STATE_INACTIVE) {
            ViMode_Update(&sViMode, &gameState->input[0]);
            gfxCtx->viMode = &sViMode.customViMode;
            gfxCtx->viFeatures = sViMode.viFeatures;
            gfxCtx->xScale = 1.0f;
            gfxCtx->yScale = 1.0f;
        }
    }
#endif
}
```

## Game State Types and Transitions

### Major Game State Types

**Game State Overlay Table (`z_game_dlftbls.c:41`):**
```c
GameStateOverlay gGameStateOverlayTable[] = {
#include "tables/gamestate_table.h"
};
```

**Common Game States:**
- **TitleSetupState**: Initializes title screen sequence
- **PlayState**: Main gameplay state (in-game)
- **FileSelectState**: File selection and management
- **MapSelectState**: Debug map selection (debug builds)
- **ConsoleLogo**: Console manufacturer logo display
- **GameOver**: Game over screen handling

### State Transition Mechanism

**State Transition Macro (`game.h`):**
```c
#define SET_NEXT_GAMESTATE(gameState, init, size) \
    do { \
        (gameState)->init = init; \
        (gameState)->size = size; \
    } while (0)
```

**Transition Example (`z_file_choose.c:1865`):**
```c
void FileSelect_LoadGame(GameState* thisx) {
    FileSelectState* this = (FileSelectState*)thisx;

#if DEBUG_FEATURES
    if (this->buttonIndex == FS_BTN_SELECT_FILE_1) {
        SFX_PLAY_CENTERED(NA_SE_SY_FSEL_DECIDE_L);
        gSaveContext.fileNum = this->buttonIndex;
        Sram_OpenSave(&this->sramCtx);
        gSaveContext.gameMode = GAMEMODE_NORMAL;
        SET_NEXT_GAMESTATE(&this->state, MapSelect_Init, MapSelectState);
        this->state.running = false;
    } else
#endif
    {
        SFX_PLAY_CENTERED(NA_SE_SY_FSEL_DECIDE_L);
        gSaveContext.fileNum = this->buttonIndex;
        Sram_OpenSave(&this->sramCtx);
        gSaveContext.gameMode = GAMEMODE_NORMAL;
        SET_NEXT_GAMESTATE(&this->state, Play_Init, PlayState);
        this->state.running = false;
    }

    gSaveContext.respawn[RESPAWN_MODE_DOWN].entranceIndex = ENTR_LOAD_OPENING;
    gSaveContext.respawnFlag = 0;
    gSaveContext.seqId = (u8)NA_BGM_DISABLED;
    gSaveContext.natureAmbienceId = 0xFF;
    gSaveContext.showTitleCard = true;
    gSaveContext.dogParams = 0;
    gSaveContext.timerState = TIMER_STATE_OFF;
    gSaveContext.subTimerState = SUBTIMER_STATE_OFF;
    gSaveContext.eventInf[0] = 0;
    gSaveContext.eventInf[1] = 0;
    gSaveContext.eventInf[2] = 0;
    gSaveContext.eventInf[3] = 0;
    gSaveContext.prevHudVisibilityMode = HUD_VISIBILITY_ALL;
    gSaveContext.nayrusLoveTimer = 0;
    gSaveContext.healthAccumulator = 0;
    gSaveContext.magicState = MAGIC_STATE_IDLE;
    gSaveContext.prevMagicState = MAGIC_STATE_IDLE;
    gSaveContext.forcedSeqId = NA_BGM_GENERAL_SFX;
    gSaveContext.skyboxTime = CLOCK_TIME(0, 0);
    gSaveContext.nextTransitionType = TRANS_NEXT_TYPE_DEFAULT;
    gSaveContext.nextCutsceneIndex = NEXT_CS_INDEX_NONE;
    gSaveContext.cutsceneTrigger = 0;
    gSaveContext.chamberCutsceneNum = CHAMBER_CS_FOREST;
    gSaveContext.nextDayTime = NEXT_TIME_NONE;
    gSaveContext.retainWeatherMode = false;
}
```

## PlayState Deep Dive

### PlayState Initialization

**PlayState is the primary game state for actual gameplay:**

**Play_Init Function (`z_play.c:286`):**
```c
void Play_Init(GameState* thisx) {
    PlayState* this = (PlayState*)thisx;
    GraphicsContext* gfxCtx = this->state.gfxCtx;
    uintptr_t zAlloc;
    uintptr_t zAllocAligned;
    size_t zAllocSize;
    Player* player;
    s32 playerStartBgCamIndex;
    s32 i;
    u8 baseSceneLayer;
    s32 pad[2];

    if (gSaveContext.save.entranceIndex == ENTR_LOAD_OPENING) {
        gSaveContext.save.entranceIndex = 0;
        this->state.running = false;
        SET_NEXT_GAMESTATE(&this->state, TitleSetup_Init, TitleSetupState);
        return;
    }

    // System initialization
    GameState_Realloc(&this->state, 0x1D4790);
    
    // Initialize core systems
    KaleidoManager_Init(this);
    View_Init(&this->view, gfxCtx);
    Audio_SetExtraFilter(0);
    Quake_Init();

    // Initialize camera system
    for (i = 0; i < ARRAY_COUNT(this->cameraPtrs); i++) {
        this->cameraPtrs[i] = NULL;
    }

    Camera_Init(&this->mainCamera, &this->view, &this->colCtx, this);
    Camera_ChangeStatus(&this->mainCamera, CAM_STAT_ACTIVE);

    for (i = 0; i < 3; i++) {
        Camera_Init(&this->subCameras[i], &this->view, &this->colCtx, this);
        Camera_ChangeStatus(&this->subCameras[i], CAM_STAT_UNK100);
    }

    this->cameraPtrs[CAM_ID_MAIN] = &this->mainCamera;
    this->cameraPtrs[CAM_ID_MAIN]->uid = 0;
    this->activeCamId = CAM_ID_MAIN;
    
    // Initialize other systems
    Sram_Init(&this->state, &this->sramCtx);
    Regs_InitData(this);
    Message_Init(this);
    GameOver_Init(this);
    SfxSource_InitAll(this);
    Effect_InitContext(this);
    
    // Initialize scene
    Play_InitScene(this, spawn);
}
```

### PlayState Main Loop

**Play_Main Function (`z_play.c:1414`):**
```c
void Play_Main(GameState* thisx) {
    PlayState* this = (PlayState*)thisx;

    D_8012D1F8 = &this->state.input[0];

    DebugDisplay_Init();

    PLAY_LOG(4556);

    if (DEBUG_FEATURES && (R_HREG_MODE == HREG_MODE_PLAY) && (R_PLAY_INIT != HREG_MODE_PLAY)) {
        R_PLAY_RUN_UPDATE = true;
        R_PLAY_RUN_DRAW = true;
        R_PLAY_DRAW_SKYBOX = true;
        R_PLAY_DRAW_ROOM_FLAGS = (ROOM_DRAW_OPA | ROOM_DRAW_XLU);
        R_PLAY_DRAW_ACTORS = true;
        R_PLAY_DRAW_LENS_FLARES = true;
        R_PLAY_DRAW_SCREEN_FILLS = true;
        R_PLAY_DRAW_SANDSTORM = true;
        R_PLAY_DRAW_OVERLAY_ELEMENTS = true;
        R_PLAY_DRAW_ENV_FLAGS = (PLAY_ENV_DRAW_SKYBOX_FILTERS | PLAY_ENV_DRAW_SUN_AND_MOON | PLAY_ENV_DRAW_LIGHTNING |
                                 PLAY_ENV_DRAW_LIGHTS);
        HREG(91) = 1; // reg is not used in this mode
        R_PLAY_DRAW_COVER_ELEMENTS = true;
        R_PLAY_DRAW_DEBUG_OBJECTS = true;
        R_PLAY_INIT = HREG_MODE_PLAY;
    }

    if (!DEBUG_FEATURES || (R_HREG_MODE != HREG_MODE_PLAY) || R_PLAY_RUN_UPDATE) {
        Play_Update(this);
    }

    PLAY_LOG(4583);

    Play_Draw(this);

    PLAY_LOG(4587);
}
```

## Memory Management

### Game State Memory Arena

**Game State Memory Initialization (`game.c:433`):**
```c
void GameState_InitArena(GameState* gameState, size_t size) {
    void* arena;
    
    arena = SYSTEM_ARENA_MALLOC(size, "../game.c", 1063);
    THA_Init(&gameState->tha, arena, size);
    
    PRINTF(T("ゲームエリア初期化完了\n", "Game area initialization complete\n"));
}
```

### Memory Allocation Macros

**Game State Memory Allocation:**
```c
#define GAME_STATE_ALLOC(gameState, size, file, line) \
    THA_AllocTailAlign16(&(gameState)->tha, size)

#define GAME_ALLOC(gameState, size) \
    GameAlloc_Malloc(&(gameState)->alloc, size)
```

## Graphics Thread Integration

### Graphics Thread Entry

**Graphics Thread Main Loop (`graph.c:481`):**
```c
void Graph_ThreadEntry(void* arg0) {
    GraphicsContext gfxCtx;
    GameState* gameState;
    u32 size;
    GameStateOverlay* nextOvl = &gGameStateOverlayTable[GAMESTATE_SETUP];
    GameStateOverlay* ovl;

    PRINTF(T("グラフィックスレッド実行開始\n", "Start graphic thread execution\n"));
    
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
    
    PRINTF(T("グラフィックスレッド実行終了\n", "End graphic thread execution\n"));
}
```

### State Identification

**Next State Resolution (`graph.c:154`):**
```c
GameStateOverlay* Graph_GetNextGameState(GameState* gameState) {
    void* gameStateInitFunc = GameState_GetInit(gameState);

    // Generates code to match gameStateInitFunc to a gamestate entry and returns it if found
#define DEFINE_GAMESTATE_INTERNAL(typeName, enumName) \
    if (gameStateInitFunc == typeName##_Init) {       \
        return &gGameStateOverlayTable[enumName];     \
    }
#define DEFINE_GAMESTATE(typeName, enumName, name) DEFINE_GAMESTATE_INTERNAL(typeName, enumName)
#include "tables/gamestate_table.h"
#undef DEFINE_GAMESTATE
#undef DEFINE_GAMESTATE_INTERNAL

    LOG_ADDRESS("game_init_func", gameStateInitFunc, "../graph.c", 696);
    return NULL;
}
```

## Save Context Integration

### Save Context Structure

**The save context manages persistent game state:**

**Save Context Initialization (`z_common_data.c:16`):**
```c
void SaveContext_Init(void) {
    bzero(&gSaveContext, sizeof(gSaveContext));
    D_8015FA88 = 0;
    D_8015FA8C = 0;
    gSaveContext.seqId = (u8)NA_BGM_DISABLED;
    gSaveContext.natureAmbienceId = NATURE_ID_DISABLED;
    gSaveContext.forcedSeqId = NA_BGM_GENERAL_SFX;
    gSaveContext.nextCutsceneIndex = NEXT_CS_INDEX_NONE;
    gSaveContext.cutsceneTrigger = 0;
    gSaveContext.chamberCutsceneNum = CHAMBER_CS_FOREST;
    gSaveContext.nextDayTime = NEXT_TIME_NONE;
    gSaveContext.skyboxTime = 0;
    gSaveContext.dogIsLost = true;
    gSaveContext.nextTransitionType = TRANS_NEXT_TYPE_DEFAULT;
    gSaveContext.prevHudVisibilityMode = HUD_VISIBILITY_ALL;
    
    // Language initialization (version-specific)
#if OOT_NTSC && OOT_VERSION < GC_US || PLATFORM_IQUE
    if (gCurrentRegion == REGION_JP) {
        gSaveContext.language = LANGUAGE_JPN;
    }
    if (gCurrentRegion == REGION_US) {
        gSaveContext.language = LANGUAGE_ENG;
    }
#elif OOT_VERSION == GC_US || OOT_VERSION == GC_US_MQ
    gSaveContext.language = LANGUAGE_ENG;
#elif OOT_VERSION == GC_JP_CE
    gSaveContext.language = LANGUAGE_JPN;
#endif
}
```

## Debug Features

### Debug Input Processing

**Debug Input Handling (`game.c:98`):**
```c
void func_800C4344(GameState* gameState) {
#if DEBUG_FEATURES
    Input* selectedInput;
    s32 hexDumpSize;
    u16 inputCompareValue;

    if (R_HREG_MODE == HREG_MODE_INPUT_TEST) {
        selectedInput =
            &gameState->input[(u32)R_INPUT_TEST_CONTROLLER_PORT < MAXCONTROLLERS ? R_INPUT_TEST_CONTROLLER_PORT : 0];

        inputCompareValue = R_INPUT_TEST_COMPARE_VALUE;
        R_INPUT_TEST_BUTTON_CUR = selectedInput->cur.button;
        R_INPUT_TEST_BUTTON_PRESS = selectedInput->press.button;
        R_INPUT_TEST_REL_STICK_X = selectedInput->rel.stick_x;
        R_INPUT_TEST_REL_STICK_Y = selectedInput->rel.stick_y;
        R_INPUT_TEST_REL_STICK_X_2 = selectedInput->rel.stick_x;
        R_INPUT_TEST_REL_STICK_Y_2 = selectedInput->rel.stick_y;
        R_INPUT_TEST_CUR_STICK_X = selectedInput->cur.stick_x;
        R_INPUT_TEST_CUR_STICK_Y = selectedInput->cur.stick_y;
        R_INPUT_TEST_COMPARE_BUTTON_CUR = (selectedInput->cur.button == inputCompareValue);
        R_INPUT_TEST_COMPARE_COMBO_CUR = CHECK_BTN_ALL(selectedInput->cur.button, inputCompareValue);
        R_INPUT_TEST_COMPARE_COMBO_PRESS = CHECK_BTN_ALL(selectedInput->press.button, inputCompareValue);
    }

    if (gIsCtrlr2Valid) {
        Regs_UpdateEditor(&gameState->input[1]);
    }

    gDmaMgrVerbose = HREG(60);
    gDmaMgrDmaBuffSize = SREG(21) != 0 ? ALIGN16(SREG(21)) : DMAMGR_DEFAULT_BUFSIZE;
    gSystemArenaLogSeverity = HREG(61);
    gZeldaArenaLogSeverity = HREG(62);
#endif
}
```

## Practical Examples

### Custom Game State Creation

**Creating a Custom Game State:**

```c
// Custom game state structure
typedef struct {
    GameState state;
    // Add custom fields here
    s32 customTimer;
    u8 customFlag;
} CustomGameState;

// Custom initialization function
void CustomGameState_Init(GameState* thisx) {
    CustomGameState* this = (CustomGameState*)thisx;
    
    // Initialize base game state
    this->state.main = CustomGameState_Main;
    this->state.destroy = CustomGameState_Destroy;
    
    // Initialize custom fields
    this->customTimer = 0;
    this->customFlag = 0;
    
    // Initialize any required subsystems
    Matrix_Init(&this->state);
}

// Custom main loop
void CustomGameState_Main(GameState* thisx) {
    CustomGameState* this = (CustomGameState*)thisx;
    
    // Update custom logic
    this->customTimer++;
    
    // Handle input
    if (CHECK_BTN_ALL(this->state.input[0].press.button, BTN_START)) {
        // Transition to another state
        SET_NEXT_GAMESTATE(&this->state, Play_Init, PlayState);
        this->state.running = false;
    }
}

// Custom cleanup
void CustomGameState_Destroy(GameState* thisx) {
    CustomGameState* this = (CustomGameState*)thisx;
    
    // Clean up custom resources
    // ...
}
```

### State Transition Patterns

**Common State Transition Patterns:**

```c
// Pattern 1: Direct transition
void TransitionToPlay(GameState* gameState) {
    SET_NEXT_GAMESTATE(gameState, Play_Init, PlayState);
    gameState->running = false;
}

// Pattern 2: Conditional transition
void ConditionalTransition(GameState* gameState) {
    if (gSaveContext.save.entranceIndex == ENTR_LOAD_OPENING) {
        SET_NEXT_GAMESTATE(gameState, TitleSetup_Init, TitleSetupState);
    } else {
        SET_NEXT_GAMESTATE(gameState, Play_Init, PlayState);
    }
    gameState->running = false;
}

// Pattern 3: Save context preparation
void PrepareGameplayTransition(GameState* gameState) {
    // Prepare save context
    gSaveContext.gameMode = GAMEMODE_NORMAL;
    gSaveContext.nextTransitionType = TRANS_NEXT_TYPE_DEFAULT;
    gSaveContext.nextCutsceneIndex = NEXT_CS_INDEX_NONE;
    
    // Transition to gameplay
    SET_NEXT_GAMESTATE(gameState, Play_Init, PlayState);
    gameState->running = false;
}
```

## Performance Considerations

### Memory Usage Patterns

**Game State Memory Characteristics:**
- **PlayState**: Largest memory footprint (~1.9MB base allocation)
- **FileSelect**: Moderate memory usage for UI elements
- **TitleSetup**: Minimal memory requirements
- **Memory Reallocation**: States can request different memory sizes

### Optimization Strategies

**Performance Optimization Techniques:**

1. **Efficient State Transitions:**
   - Minimize initialization work in transition functions
   - Reuse common resources where possible
   - Clean up unnecessary resources promptly

2. **Memory Management:**
   - Use appropriate allocation strategies for different state lifetimes
   - Avoid memory fragmentation through proper arena usage
   - Monitor memory usage patterns during development

3. **Input Processing:**
   - Cache frequently accessed input values
   - Use appropriate input filtering for different states
   - Minimize input processing overhead in update loops

## Debugging and Development

### State Debugging Tools

**Debug State Information:**

```c
// Debug macros for state analysis
#define DEBUG_GAMESTATE_PRINT(gameState) \
    PRINTF("GameState: running=%d, frames=%d\n", (gameState)->running, (gameState)->frames)

#define DEBUG_TRANSITION_PRINT(fromState, toState) \
    PRINTF("Transition: %s -> %s\n", #fromState, #toState)
```

### Common Issues and Solutions

**Typical Game State Issues:**

1. **Memory Leaks:**
   - Ensure proper cleanup in destroy functions
   - Use appropriate memory allocation patterns
   - Monitor arena usage over time

2. **State Corruption:**
   - Validate state transitions carefully
   - Check for proper initialization sequences
   - Monitor save context integrity

3. **Performance Issues:**
   - Profile state update functions
   - Optimize critical path operations
   - Consider state-specific optimizations

## Conclusion

The Game State Management System in OOT provides a robust framework for managing the overall game flow. Understanding its architecture is crucial for:

- Creating custom game modes and states
- Implementing proper state transitions
- Managing memory efficiently across different game phases
- Debugging state-related issues
- Optimizing game performance

The system's design allows for clean separation between different game modes while providing consistent interfaces for graphics, input, and memory management. This architecture has proven effective for managing the complex state requirements of a large-scale game like Ocarina of Time.

**Key Files Reference:**
- `src/code/game.c` - Core game state management
- `src/code/graph.c` - Graphics thread integration
- `src/code/z_game_dlftbls.c` - Game state overlay table
- `src/code/z_play.c` - PlayState implementation
- `src/code/z_common_data.c` - Save context management
- `src/overlays/gamestates/` - Individual game state implementations

## Additional Resources

For more detailed information about specific aspects of the game state system, refer to:
- Individual game state overlay implementations
- Graphics system documentation for rendering integration
- Input system documentation for controller handling
- Memory management system documentation for allocation strategies 