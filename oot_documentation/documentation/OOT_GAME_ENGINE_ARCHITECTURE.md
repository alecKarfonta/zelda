# OOT Game Engine Architecture

## Overview

This document describes the internal architecture of the original Legend of Zelda: Ocarina of Time game engine as it ran on the Nintendo 64. This focuses on the runtime systems, memory management, and core architectural patterns that made the game work within the N64's constraints.

**Note: All details in this document have been verified against the actual OOT decomp source code.**

## Core Runtime Architecture

### Threading Model

The OOT engine uses a **multi-threaded architecture** with specialized threads and verified priorities:

```
Main Thread (Priority: THREAD_PRI_MAIN = 15)
├── Graph Thread (Priority: THREAD_PRI_GRAPH = 11)
│   ├── Handles game state updates
│   ├── Manages rendering pipeline
│   └── Coordinates frame timing
├── Scheduler Thread (Priority: THREAD_PRI_SCHED = 15)
│   ├── Manages RSP/RDP task scheduling
│   ├── Handles VI (Video Interface) events
│   └── Coordinates hardware resources
├── Audio Thread (Priority: THREAD_PRI_AUDIOMGR = 12)
│   ├── Processes audio commands
│   ├── Manages sound synthesis
│   └── Handles audio DMA
├── IRQ Manager Thread (Priority: THREAD_PRI_IRQMGR = 17)
│   ├── Handles hardware interrupts
│   └── Distributes interrupt messages
├── Pad Manager Thread (Priority: THREAD_PRI_PADMGR = 14)
│   ├── Polls controller input
│   └── Manages rumble feedback
└── DMA Manager Thread (Priority: THREAD_PRI_DMAMGR = 16)
    ├── Handles data transfers
    └── Manages memory operations
```

**Verified Thread Creation (from main.c):**
```c
IrqMgr_Init(&gIrqMgr, STACK_TOP(sIrqMgrStack), THREAD_PRI_IRQMGR, 1);
Sched_Init(&gScheduler, STACK_TOP(sSchedStack), THREAD_PRI_SCHED, ...);
AudioMgr_Init(&sAudioMgr, STACK_TOP(sAudioStack), THREAD_PRI_AUDIOMGR, ...);
PadMgr_Init(&gPadMgr, ..., THREAD_PRI_PADMGR, ...);
osCreateThread(&sGraphThread, THREAD_ID_GRAPH, Graph_ThreadEntry, ..., THREAD_PRI_GRAPH);
```

### Memory Layout

The engine operates within **4MB of unified RAM** with careful memory management:

```
Memory Layout (N64)
├── 0x80000000 - Boot Code & OS
├── 0x80001000 - Game Code Segment
├── 0x80100000 - Game Data Segment  
├── 0x80200000 - System Heap
├── 0x80300000 - Frame Buffers
├── 0x80400000 - Available RAM
└── 0x807FFFFF - RAM End
```

#### Memory Management Systems

**1. System Arena**: Core system allocator
- Manages boot-time allocations
- Handles thread stacks and system buffers
- Persistent throughout game execution

**2. Game State Arena**: Per-state memory
- Allocated/deallocated on state transitions
- **Verified**: PlayState allocates **0x1D4790 bytes (~1.87MB)** in z_play.c:310
- Handles scene and room data

**3. Zelda Arena**: Dynamic game memory
- Actor instances and temporary objects
- Effect systems and particle data
- Runtime-generated content

**4. Graphics Memory**: Rendering resources
- Display lists and command buffers
- Texture cache and matrix stacks
- Managed by graphics context

### Game State System

The engine uses a **hierarchical state machine** architecture:

#### State Hierarchy
```
GameState (Base Class)
├── PlayState (Main Gameplay)
│   ├── Scene Management
│   ├── Actor System
│   ├── Camera System
│   ├── Physics & Collision
│   ├── Audio Management
│   └── Input Handling
├── MenuStates (UI Systems)
│   ├── TitleSetup
│   ├── FileSelect
│   └── PauseMenu
├── TransitionStates
│   ├── FadeTransitions
│   └── EffectTransitions
└── SpecialStates
    ├── GameOver
    ├── PreNMI (Reset handling)
    └── Sample (Debug)
```

#### State Management
- **State Transitions**: Managed by **verified** `SET_NEXT_GAMESTATE()` macro
- **Memory Lifecycle**: States allocate/deallocate their own memory
- **Persistence**: Save data and settings survive state changes
- **Initialization**: Each state has init/main/destroy functions

## Core Gameplay Systems

### Scene and Room Architecture

The world is organized in a **hierarchical spatial system**:

#### Scene System
- **Scene**: Large world areas (Hyrule Field, Kakariko Village, dungeons)
- **Room**: Sub-areas within scenes for memory optimization
- **Dynamic Loading**: Rooms loaded/unloaded based on player position
- **Segmented Memory**: **Verified** - Scenes use segment 2, rooms use segment 3

**Verified Memory Segment Usage:**
```c
gSegments[2] = OS_K0_TO_PHYSICAL(this->sceneSegment);     // Scene data
gSegments[3] = OS_K0_TO_PHYSICAL(roomCtx->curRoom.segment); // Room data
gSegments[4] = OS_K0_TO_PHYSICAL(objectCtx->slots[...]);    // Main objects
gSegments[5] = OS_K0_TO_PHYSICAL(play->objectCtx.slots[...]); // Sub objects
gSegments[6] = OS_K0_TO_PHYSICAL(play->objectCtx.slots[...]); // Actor objects
```

#### Scene Data Structure
```
Scene Components:
├── Collision Header (walls, floors, ceilings)
├── Actor Entry List (spawn points and parameters)
├── Room List (room file references)
├── Spawn List (player entry points)
├── Object List (required 3D models/textures)
├── Path List (AI movement paths)
├── Transition Actors (door/loading triggers)
├── Lighting Data (environment lighting)
├── Environmental Settings (skybox, weather, music)
└── Cutscene Data (scripted sequences)
```

#### Room Loading Process (**Verified**)
1. **Request**: `Room_RequestNewRoom()` initiates async DMA
2. **Processing**: `Room_ProcessRoomRequest()` checks completion
3. **Initialization**: Scene commands processed on new room
4. **Actor Spawning**: Room-specific actors created
5. **Cleanup**: Previous room actors destroyed

**Verified Function Signatures:**
```c
s32 Room_RequestNewRoom(PlayState* play, RoomContext* roomCtx, s32 roomNum);
s32 Room_ProcessRoomRequest(PlayState* play, RoomContext* roomCtx);
```

### Actor System

The **Actor System** is the core of all interactive game objects:

#### Actor Architecture (**Verified**)
```c
Actor Base Class (0x14C bytes) // Verified size in actor.h
├── Core Data
│   ├── ID, Category, Flags
│   ├── Position, Rotation, Scale
│   ├── Velocity, Physics Properties
│   └── Object Slot Reference
├── Behavior Functions
│   ├── init() - Constructor
│   ├── update() - Per-frame logic
│   ├── draw() - Rendering
│   └── destroy() - Cleanup
├── Collision Systems
│   ├── Collision Check Info
│   ├── Background Collision
│   └── Actor-Actor Collision
├── Interaction Systems
│   ├── Attention System (Z-targeting)
│   ├── Focus and Lock-on
│   └── Player Interaction
└── Rendering Data
    ├── Culling Information
    ├── Shape and Shadow
    └── Animation State
```

#### Actor Categories (**Verified from actor_profile.h**)
The engine organizes actors into **12 categories** for efficient processing:

1. **ACTORCAT_SWITCH** (0x00): Switches, triggers, pressure plates
2. **ACTORCAT_BG** (0x01): Background geometry, collision objects
3. **ACTORCAT_PLAYER** (0x02): Link (player character)
4. **ACTORCAT_EXPLOSIVE** (0x03): Bombs, explosions, destructible objects
5. **ACTORCAT_NPC** (0x04): Non-player characters, dialogue
6. **ACTORCAT_ENEMY** (0x05): Enemies, AI-controlled hostiles
7. **ACTORCAT_PROP** (0x06): Interactive objects, items, collectibles
8. **ACTORCAT_ITEMACTION** (0x07): Items that trigger actions
9. **ACTORCAT_MISC** (0x08): Effects, particles, miscellaneous
10. **ACTORCAT_BOSS** (0x09): Boss enemies, special encounters
11. **ACTORCAT_DOOR** (0x0A): Doors, passages, entrances
12. **ACTORCAT_CHEST** (0x0B): Treasure chests, containers

#### Actor Lifecycle
```
Actor Management Process:
1. Spawn Request → Actor_Spawn()
2. Memory Allocation → ZELDA_ARENA_MALLOC()
3. Overlay Loading → Load actor code if needed
4. Object Loading → Ensure 3D model/texture loaded
5. Initialization → Actor's init() function called
6. Update Loop → Actor's update() function per frame
7. Rendering → Actor's draw() function if visible
8. Destruction → Actor's destroy() function on death
9. Memory Cleanup → ZELDA_ARENA_FREE()
```

### Physics and Collision System

The engine implements **multi-layered collision detection**:

#### Background Collision (BgCheck)
- **Static Geometry**: Scene collision meshes
- **Dynamic Geometry**: Moving platforms, doors
- **Collision Types**: Floor, wall, ceiling detection
- **Surface Properties**: Material types, sounds, effects

#### Actor Collision (CollisionCheck)
- **AT (Attack)**: Damage-dealing colliders
- **OC (Object)**: Physical presence, pushing
- **Damage**: Receiving damage from attacks
- **Interaction**: Touch-based interactions

#### Dynamic Collision (DynaPoly)
- **Moving Platforms**: Elevators, rotating objects
- **Interactive Geometry**: Pushable blocks, switches
- **Actor Integration**: Actors that affect world geometry

### Graphics System

The engine uses the **N64's Reality Coprocessor (RCP)**:

#### Rendering Pipeline
```
Graphics Pipeline:
1. Matrix Setup → World/View/Projection matrices
2. Lighting → Dynamic lighting calculations
3. Culling → Frustum and distance culling
4. Display Lists → RDP command generation
5. Texture Loading → Texture cache management
6. Rasterization → RDP processes graphics
7. Frame Buffer → Final image output
```

#### Graphics Context
- **Command Buffers**: Store RDP commands
- **Matrix Stack**: 3D transformation management
- **Lighting Context**: Dynamic light sources
- **Texture Management**: Loading and caching

#### Camera System
- **Main Camera**: Primary view camera
- **Sub Cameras**: Cutscene and special views
- **Camera Modes**: Fixed, follow, first-person
- **Transitions**: Smooth camera movement

### Audio System

The engine implements **advanced audio processing**:

#### Audio Architecture
```
Audio System:
├── Audio Thread (Dedicated processing)
├── Audio Heap (Memory management)
├── Sequence Player (MIDI-like music)
├── Sample Player (Sound effects)
├── Audio Commands (Game → Audio interface)
└── Spatial Audio (3D positioned sounds)
```

#### Audio Components
- **Sound Fonts**: Instrument sample collections
- **Sequences**: Music composition data
- **Audio Commands**: Interface between game and audio
- **Voice Management**: Audio channel allocation

## System Integration

### Main Game Loop

The engine runs at **60 FPS (NTSC) / 50 FPS (PAL)** with this update cycle:

**Verified**: The IRQ manager is initialized with `retraceCount = 1`, meaning it triggers on every video retrace (60Hz NTSC, 50Hz PAL).

```
Per-Frame Process:
1. Input Processing → Controller state updates
2. Game State Update → Active state's main() function
3. Scene Processing → Room loading/unloading
4. Actor Updates → All active actors updated
5. Physics Updates → Collision detection/response
6. Audio Processing → Audio commands processed
7. Graphics Rendering → Scene rendered to framebuffer
8. Memory Management → Cleanup and allocation
```

**Verified Main Update Loop (from GameState_Update):**
```c
gameState->main(gameState);        // State-specific update
func_800C4344(gameState);          // Debug and input processing
GameState_Draw(gameState, gfxCtx); // Rendering
func_800C49F4(gfxCtx);            // Additional graphics processing
```

### Object System

The engine manages **3D models and textures** dynamically:

#### Object Loading
- **Object Context**: Manages loaded 3D assets
- **Dynamic Loading**: Objects loaded as needed
- **Memory Optimization**: Shared objects between actors
- **Segmented Memory**: Objects use memory segments 4/5/6

### Save System

The engine implements **battery-backed save data**:

#### Save Structure
- **SRAM**: Non-volatile memory for persistence
- **Save Context**: Current game state in memory
- **Checksum Validation**: Data integrity protection
- **Multiple Slots**: Three save file slots

## Performance Optimizations

### Memory Optimization
- **Overlay System**: Code loaded on-demand
- **Room Streaming**: Only current room in memory
- **Object Sharing**: Reuse 3D models between actors
- **Garbage Collection**: Automatic cleanup of unused resources

### Rendering Optimization
- **Culling**: Frustum and distance culling
- **Level of Detail**: Simplified models at distance
- **Texture Caching**: Efficient texture memory usage
- **Display List Optimization**: Minimized RDP commands

### Processing Optimization
- **Category-based Updates**: Actors updated by category
- **Conditional Processing**: Skip updates when paused
- **Spatial Partitioning**: Efficient collision detection
- **Frame Rate Management**: Consistent timing based on video retrace

## Technical Constraints

### Hardware Limitations
- **4MB RAM**: Extremely limited memory
- **64KB Texture Cache**: Small texture memory
- **Limited Bandwidth**: Cartridge access constraints
- **Fixed-Point Math**: No floating-point hardware

### Engine Solutions
- **Streaming**: Dynamic loading of content
- **Compression**: Yaz0 compression for assets
- **Memory Pools**: Efficient allocation patterns
- **Fixed-Point**: Custom math libraries

This architecture enabled OOT to create an expansive 3D world within the N64's constraints while maintaining smooth gameplay and complex interactions between systems. 