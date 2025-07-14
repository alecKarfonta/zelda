# OOT System Architecture

## Overview

The Legend of Zelda: Ocarina of Time (OOT) decomp project is a complete decompilation of the N64 game into readable C source code. This document describes the system architecture, major components, and how they interact to create the complete game experience.

## Project Structure

### Build System
- **Makefile-based**: Uses GNU Make with complex dependency management
- **Multi-version support**: Builds 13+ different game versions (NTSC, PAL, GameCube, iQue)
- **Docker integration**: Containerized development environment
- **Asset extraction**: Automated extraction of graphics, audio, and data from ROM files

### Source Organization

```
oot/
├── src/                    # Core source code
│   ├── code/              # Main game engine code
│   ├── overlays/          # Loadable code modules
│   ├── boot/              # Boot sequence and initialization
│   ├── audio/             # Audio system implementation
│   ├── libultra/          # Nintendo 64 OS library
│   └── buffers/           # Memory buffer management
├── include/               # Header files and type definitions
├── assets/                # Game assets (extracted from ROM)
├── tools/                 # Build tools and utilities
└── spec/                  # Linker specifications
```

## Core Architecture

### 1. Game State System

The game operates through a **hierarchical state machine**:

#### GameState Base Class
- **Central dispatcher**: Manages state transitions and lifecycle
- **Memory management**: Handles allocation/deallocation for each state
- **Input processing**: Distributes controller input to active states
- **Graphics context**: Manages rendering pipeline setup

#### Major Game States
- **PlayState**: Main gameplay (exploring, combat, puzzles)
- **Title/Menu States**: Title screen, file select, pause menus
- **Cutscene States**: Story sequences and transitions
- **Loading States**: Scene transitions and data loading

### 2. Actor System

The **Actor System** is the core of OOT's gameplay logic:

#### Actor Framework
- **Component-based**: Each actor contains position, graphics, physics, AI
- **Category-based organization**: 12 categories (Player, Enemy, NPC, etc.)
- **Lifecycle management**: Standardized init/update/draw/destroy pattern
- **Dynamic loading**: Actors loaded/unloaded as needed

#### Actor Categories
```
ACTORCAT_SWITCH      // Switches and triggers
ACTORCAT_BG          // Background/collision objects  
ACTORCAT_PLAYER      // Link (player character)
ACTORCAT_EXPLOSIVE   // Bombs, explosions
ACTORCAT_NPC         // Non-player characters
ACTORCAT_ENEMY       // Enemies and bosses
ACTORCAT_PROP        // Interactive objects
ACTORCAT_ITEMACTION  // Items and pickups
ACTORCAT_MISC        // Effects and miscellaneous
ACTORCAT_BOSS        // Boss-specific actors
ACTORCAT_DOOR        // Doors and entrances
ACTORCAT_CHEST       // Treasure chests
```

#### Actor Lifecycle
1. **Spawn**: Actor created with parameters from scene data
2. **Init**: Actor-specific initialization routine
3. **Update**: Per-frame logic updates (60 FPS)
4. **Draw**: Rendering and graphics updates
5. **Destroy**: Cleanup when actor is removed

### 3. Scene and Room System

#### Scene Architecture
- **Scene**: Large game area (e.g., Hyrule Field, Kakariko Village)
- **Room**: Subdivisions within scenes for memory optimization
- **Room loading**: Dynamic loading/unloading based on player position

#### Scene Components
- **Collision mesh**: 3D collision geometry
- **Actor spawn points**: Definitions for where actors appear
- **Entrance/exit points**: Scene transitions
- **Environmental settings**: Lighting, weather, music
- **Cutscene data**: Scripted sequences

### 4. Graphics System

#### Rendering Pipeline
- **Display lists**: N64 RDP (Reality Display Processor) commands
- **Matrix stack**: 3D transformation management
- **Texture management**: Loading and caching of graphics
- **Animation system**: Skeletal animation for characters

#### Graphics Components
- **Gfx context**: Manages graphics state and command buffers
- **Camera system**: Multiple camera types (fixed, follow, cutscene)
- **Lighting**: Dynamic lighting and shadows
- **Effects**: Particle systems, weather, transitions

### 5. Audio System

#### Audio Architecture
- **Sequence-based**: MIDI-like sequences for music
- **Sample-based**: PCM audio samples for sound effects
- **Voice management**: Allocation of audio channels
- **Spatial audio**: 3D positioning of sounds

#### Audio Components
- **Audio heap**: Memory management for audio data
- **Sound font**: Instrument definitions and samples
- **Audio thread**: Separate processing thread for audio
- **Audio commands**: Interface between game and audio system

### 6. Memory Management

#### Memory Layout
- **Heap management**: Dynamic allocation using custom allocators
- **Overlay system**: Code modules loaded on-demand
- **Asset streaming**: Loading graphics/audio as needed
- **Garbage collection**: Automatic cleanup of unused resources

#### Memory Regions
- **Code segment**: Game executable code
- **Data segment**: Static game data
- **BSS segment**: Uninitialized data
- **Heap**: Dynamic memory allocation
- **Stack**: Function call stack

### 7. Input System

#### Input Processing
- **Controller polling**: 60 FPS controller state updates
- **Input buffering**: Stores recent input for combo detection
- **Context-sensitive**: Different input handling per game state
- **Rumble support**: Force feedback integration

### 8. Save System

#### Save Data Management
- **SRAM**: Battery-backed save memory
- **Save slots**: Multiple save files support
- **Checksum validation**: Data integrity verification
- **Save context**: Current game state persistence

## System Interactions

### Main Game Loop
1. **Input processing**: Read controller state
2. **Game state update**: Update active game state
3. **Actor updates**: Process all active actors
4. **Physics/collision**: Handle movement and interactions
5. **Audio update**: Process audio commands
6. **Graphics rendering**: Draw frame to screen
7. **Memory management**: Cleanup and allocation

### Actor-Scene Integration
- Actors exist within scenes and rooms
- Scene data defines actor spawn parameters
- Collision system mediates actor-environment interaction
- Scene transitions trigger actor lifecycle events

### Graphics-Audio Coordination
- Audio cues triggered by visual events
- Synchronized cutscene audio and video
- Spatial audio positioning based on camera
- Music transitions coordinated with scene changes

## Development Features

### Debug Systems
- **Console output**: Debug logging and profiling
- **GDB integration**: Source-level debugging
- **Screen printing**: In-game debug text
- **Memory visualization**: Heap and stack monitoring

### Build System Features
- **Incremental compilation**: Only rebuild changed files
- **Asset pipeline**: Automated asset conversion
- **Version management**: Multiple ROM targets
- **Difference tracking**: Compare builds against original

## Technical Specifications

### Performance Targets
- **60 FPS**: Consistent frame rate
- **4MB RAM**: N64 memory constraints
- **Limited bandwidth**: Cartridge/ROM access optimization
- **Real-time constraints**: Audio/video synchronization

### Platform Integration
- **N64 hardware**: Direct hardware register access
- **libultra**: Nintendo's OS library integration
- **RCP utilization**: Reality Coprocessor programming
- **Cartridge features**: Special chip integration (e.g., rumble)

## Modding Implications

### Extensibility Points
- **Actor system**: Easy to add new gameplay objects
- **Scene system**: Create new areas and rooms
- **Graphics pipeline**: Modify rendering and effects
- **Audio system**: Add new music and sound effects

### Common Modifications
- **Custom actors**: New enemies, NPCs, objects
- **Scene modifications**: Level design changes
- **Graphics enhancements**: Texture packs, effects
- **Gameplay changes**: New mechanics, items, abilities

This architecture enables both faithful recreation of the original game and extensive modification capabilities for the romhacking community. 