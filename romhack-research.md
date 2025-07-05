# OoT Romhack Dataset Creation Research Document
## Research Collection for Fine-Tuning Dataset Development

### Executive Summary

This research document compiles comprehensive information about Ocarina of Time romhacking to aid in creating an effective instruction-response dataset for fine-tuning an AI model. The goal is to enable the model to suggest code changes when requesting game features or modifications.

---

## 1. Primary Source Code Repositories

### 1.1 Main Decompilation Projects

**zeldaret/oot** - The primary decompilation project
- URL: https://github.com/zeldaret/oot
- **Key Features:**
  - Complete reverse-engineered C source code from assembly
  - Supports 14 different ROM versions (NTSC, PAL, GameCube, etc.)
  - Over 5,100 stars on GitHub indicating active community
  - Uses original function names from debug symbols found on Master Quest disc
  - Fully builds matching ROMs when compiled

**HackerOoT** - Modding-focused fork
- URL: https://github.com/HackerN64/HackerOoT  
- **Key Features:**
  - Based on zeldaret/oot but optimized for romhacking
  - Includes example scene and cutscene
  - Has `new_actor.py` script for easily adding actors
  - F3DEX3 microcode support for enhanced graphics
  - Active Discord community for modding discussions

### 1.2 Related Zelda Projects
- **zeldaret/mm** - Majora's Mask decompilation
- **zeldaret/oot3d** - Ocarina of Time 3D decompilation  
- **zeldaret/tww** - Wind Waker decompilation
- **zeldaret/tp** - Twilight Princess decompilation

---

## 2. Actor System Architecture

### 2.1 Actor Structure and Lifecycle

**Core Actor Components:**
```c
typedef struct {
    s16 Id;              // Actor identifier
    u8 Type;             // Category (0-11: Switch, Bg, Player, Bomb, etc.)
    s32 Flags;           // Behavior flags, affects Z-targeting
    s16 ObjectId;        // Primary object dependency
    int InstanceSize;    // Memory allocation size (min 0x128 bytes)
    void* Init;          // Constructor function
    void* Dest;          // Destructor function  
    void* Main;          // Main update function
    void* Draw;          // Rendering function
} z_ActorInit;
```

**Actor Lifecycle Functions:**
1. **Initialization** - Run when actor instance is loaded
2. **Main** - Always run during gameplay (update loop)
3. **Drawing** - Run when actor is close enough to camera

### 2.2 Actor Categories and Examples

**Actor Categories:**
- Type 0: Switch actors (buttons, crystal switches)
- Type 1: Background actors (doors, blocks)
- Type 2: Player actor (Link)
- Type 3: Bomb actors
- Type 4: NPC actors (characters, enemies)
- Type 5: Player shot actors (arrows, boomerang)
- Type 6: Enemy shot actors 
- Type 7: Item actors (rupees, hearts)
- Type 8: Miscellaneous actors
- Type 9: Boss actors
- Type 10: Door actors
- Type 11: Chest actors

**Common Actor Examples from Source:**
- `ovl_En_Torch2` (Dark Link) - Complex AI mirroring player actions
- `ovl_En_Item00` - Collectible items with various spawn behaviors
- `ovl_Player` - Link's player controller with movement, combat, inventory
- `ovl_Bg_Pushbox` - Pushable blocks with physics

---

## 3. Specific Code Examples for Training Data

### 3.1 Actor Animation System

From `src/code/z_skelanime.c`:
```c
/**
 * Creates a task which will move an actor according to the translation 
 * of its root limb for the current frame.
 */
void AnimTaskQueue_AddActorMovement(PlayState* play, Actor* actor, 
                                   SkelAnime* skelAnime, f32 moveDiffScaleY) {
    AnimTask* task = AnimTaskQueue_NewTask(&play->animTaskQueue, ANIMTASK_ACTOR_MOVE);
    
    if (task != NULL) {
        task->data.actorMovement.actor = actor;
        task->data.actorMovement.skelAnime = skelAnime;
        task->data.actorMovement.diffScaleY = moveDiffScaleY;
    }
}
```

### 3.2 Player Z-Targeting System

From `src/code/z_player_lib.c`:
```c
/**
 * Sets the "auto lock-on actor" to lock onto an actor without Player's input.
 * This function will first release any existing lock-on or (try to) release parallel.
 */
void Player_ClearZTargeting(Player* this) {
    if ((this->actor.bgCheckFlags & BGCHECKFLAG_GROUND) ||
        (this->stateFlags1 & (PLAYER_STATE1_21 | PLAYER_STATE1_23 | PLAYER_STATE1_27)) ||
        (!(this->stateFlags1 & (PLAYER_STATE1_18 | PLAYER_STATE1_19)) &&
         ((this->actor.world.pos.y - this->actor.floorHeight) < 100.0f))) {
        this->stateFlags1 &= ~(PLAYER_STATE1_Z_TARGETING | PLAYER_STATE1_FRIENDLY_ACTOR_FOCUS | 
                               PLAYER_STATE1_PARALLEL | PLAYER_STATE1_18 | PLAYER_STATE1_19 | 
                               PLAYER_STATE1_LOCK_ON_FORCED_TO_RELEASE);
    } else if (!(this->stateFlags1 & (PLAYER_STATE1_18 | PLAYER_STATE1_19 | PLAYER_STATE1_21))) {
        this->stateFlags1 |= PLAYER_STATE1_19;
    }
}
```

### 3.3 Dark Link Implementation

From HackerOoT's `ovl_En_Torch2/z_en_torch2.c`:
```c
// Dark Link damage handling and respawn logic
case ENTORCH2_DAMAGE:
    this->meleeWeaponState = 0;
    input->cur.stick_x = input->cur.stick_y = 0;
    if ((this->invincibilityTimer > 0) && (this->actor.world.pos.y < (this->actor.floorHeight - 160.0f))) {
        this->stateFlags3 &= ~PLAYER_STATE3_0;
        this->actor.flags |= ACTOR_FLAG_ATTENTION_ENABLED;
        this->invincibilityTimer = 0;
        this->actor.velocity.y = 0.0f;
        this->actor.world.pos.y = sSpawnPoint.y + 40.0f;
        this->actor.world.pos.x = (Math_SinS(player->actor.shape.rot.y) * -120.0f) + player->actor.world.pos.x;
        this->actor.world.pos.z = (Math_CosS(player->actor.shape.rot.y) * -120.0f) + player->actor.world.pos.z;
    }
```

---

## 4. Community Resources and Tutorials

### 4.1 CloudModding Wiki Documentation

**Comprehensive Technical References:**
- **Actors Page**: Detailed actor system explanation with memory layout
- **Actor List (Variables)**: Complete documentation of actor spawn variables
- **Actor Replacement Tutorial**: Step-by-step guide for replacing actors in scenes
- **Switch/Flag Tutorial**: Dungeon design elements and event flags

**Key Technical Information:**
- Actor variable bitpacking formats (e.g., `v &>> F000` for chest flags)
- Memory addresses for actor lists in different rooms
- Object dependency requirements for custom actors
- Scene and room header structure documentation

### 4.2 Dragorn421's Romhack Tutorials

**Repository**: https://github.com/Dragorn421/z64-romhack-tutorials

**Available Tutorials:**
- Custom Actors tutorial (WIP) - Non-decomp approach
- OoT64 Overview (WIP) - Architecture focused on decomp
- ROM structure documentation explaining VROM vs ROM offsets

### 4.3 Community Forums and Discord

**Active Communities:**
- HackerOoT Discord Server - Main hub for decomp-based modding
- ZeldaRET Discord - Reverse engineering discussions
- Hylian Modding Discord - General Zelda modding community
- romhacking.net forums - Broader ROM hacking community

---

## 5. Popular Romhacks and Modification Examples

### 5.1 Quality of Life Improvements

**OoT Redux** - Community standard for improved experience
- **Features Implemented:**
  - 2x faster text speed
  - D-pad shortcuts for ocarina and boots
  - Bunny Hood speed boost like Majora's Mask
  - No more Gold Skulltula Token freeze
  - Fixed Bombchu Bowling prize order
  - Stone of Agony works without rumble pack
  - Extended draw distance

**Technical Implementation:** Uses ASM patches from OoT Randomizer project

### 5.2 New Content Romhacks

**The Missing Link** - Story expansion
- Bridges gap between OoT and Majora's Mask
- Custom dungeon with unique mechanics
- Magic hourglass item for time rewind
- Custom boss fight and storyline

**Ultimate Trial** - Challenge content
- Custom stronghold location
- Advanced puzzle design
- References modern romhacking Discord communities

### 5.3 Randomizer Modifications

**OoT Randomizer** - Item location shuffling
- **Technical Features:**
  - Dynamic ASM patching system
  - ZPF patch file format for sharing seeds
  - Extensive cosmetic modification system
  - Music randomization with custom AudioSeq support
  - Co-op multiplayer synchronization

---

## 6. Development Tools and Workflows

### 6.1 Core Development Tools

**Patcher64+ Tool** - Modular patch system
- PowerShell-based tool for applying selective modifications
- Toggle-able features from various romhacks
- Supports both OoT and Master Quest
- Community standard for customizing QoL improvements

**z64tools Ecosystem:**
- z64compress - Fast ROM compression
- gzinject - Overlay injection for debug features
- F3DEX3 - Enhanced graphics microcode

### 6.2 Build Systems and Makefiles

**Standard Build Process:**
```bash
make setup    # Extract assets and setup dependencies
make          # Build ROM with modifications
make clean    # Clean build artifacts
```

**Modding-Specific Options:**
- Configurable Makefile with modding flags
- Support for custom actors via new_actor.py script
- Object dependency management
- Scene and room modification workflows

### 6.3 Testing and Debugging

**Debug ROM Features:**
- Map select for quick scene access
- Real-time memory viewer
- Actor spawning and variable modification
- Flag manipulation for testing features

**Emulator Requirements:**
- Ares or Parallel Launcher for F3DEX3 support (LLE)
- Project64 compatibility with specific settings
- Bizhawk for TAS and co-op features

---

## 7. ASM Patches and Low-Level Modifications

### 7.1 OoT Randomizer ASM System

**Patch Architecture:**
```python
# Example from Patches.py - Tunic color modification
Tunics = [
    (world.kokiricolor, 0x00B6DA38), # Kokiri Tunic
    (world.goroncolor,  0x00B6DA3B), # Goron Tunic  
    (world.zoracolor,   0x00B6DA3E), # Zora Tunic
]

for tunic_option, address in Tunics:
    if tunic_option == 'Random Choice':
        tunic_option = random.choice(colorList)
    elif tunic_option == 'Completely Random':
        color = [random.getrandbits(8), random.getrandbits(8), random.getrandbits(8)]
    elif tunic_option in TunicColors: 
        color = TunicColors[tunic_option] 
    else: 
        color = list(int(tunic_option[i:i+2], 16) for i in (0, 2 ,4)) 
    rom.write_bytes(address, color)
```

### 7.2 Music System Modifications

**BGM Randomization Example:**
```python
bgm_sequence_ids = [
    ('Hyrule Field', 0x02),
    ('Market', 0x03),
    ('Hyrule Castle Courtyard', 0x04),
    ('Lost Woods', 0x05),
    # ... more sequences
]

def randomize_music(rom):
    bgm_data = []
    for bgm in bgm_sequence_ids:
        bgm_sequence = rom.read_bytes(0xB89AE0 + (bgm[1] * 0x10), 0x10)
        bgm_instrument = rom.read_int16(0xB89910 + 0xDD + (bgm[1] * 2))
        bgm_data.append((bgm_sequence, bgm_instrument))
    
    random.shuffle(bgm_data)
    # Write back shuffled data...
```

---

## 8. Common Romhacking Problems and Solutions

### 8.1 Actor Memory Management

**Problem**: Custom actors crashing due to insufficient memory allocation
**Solution**: Ensure minimum 0x128 bytes allocation, properly initialize all pointers

**Problem**: Actors not loading objects properly
**Solution**: Check object dependencies and ensure objects are in scene object list

### 8.2 Scene Transitions and Object Persistence

**Problem**: Custom door skins disappearing during room transitions
**Solution**: Place dependent objects in same order and position in all connected rooms

### 8.3 Flag and Switch Management

**Problem**: Switches not persisting between save/load
**Solution**: Use proper flag types (scene flags vs global flags) and bit allocation

### 8.4 Animation and Model Issues

**Problem**: Custom models causing graphics glitches
**Solution**: Ensure proper bone structure, animation frame counts, and texture format compatibility

---

## 9. Instruction-Response Dataset Examples

### 9.1 Code Explanation Pairs

**Format**: Technical explanation of existing functions
```json
{
  "instruction": "Explain what this OoT actor initialization function does",
  "input": "void EnItem00_Init(Actor* thisx, GlobalContext* globalCtx) {\n    EnItem00* this = (EnItem00*)thisx;\n    s32 getItemId = thisx->params & 0xFF;\n    // ...\n}",
  "output": "This function initializes a collectible item actor in OoT. The `params` field stores the item type in the lower 8 bits (0xFF mask). The function sets up the item's appearance, physics properties, and collection behavior based on the getItemId value extracted from the parameters."
}
```

### 9.2 Feature Implementation Requests  

**Format**: Request for specific functionality with complete implementation
```json
{
  "instruction": "Create an actor that makes Link move twice as fast when equipped",
  "output": "To modify Link's movement speed, you need to edit the player actor's velocity calculations. Here's the implementation:\n\n```c\n// In z_player.c, modify the movement function\nvoid Player_UpdateMovement(Player* this, PlayState* play) {\n    f32 speedMultiplier = 1.0f;\n    \n    // Check if speed boost item is equipped\n    if (this->currentBoots == PLAYER_BOOTS_SPEED) {\n        speedMultiplier = 2.0f;\n    }\n    \n    this->linearVelocity *= speedMultiplier;\n    // Continue with normal movement processing...\n}\n```\n\nYou'll also need to create a custom boot item and add it to the item table."
}
```

### 9.3 Debugging and Problem Solving

**Format**: Common issues with diagnostic steps and solutions
```json
{
  "instruction": "My custom actor crashes when spawning. Here's the code:",
  "input": "void MyActor_Init(Actor* thisx, PlayState* play) {\n    MyActor* this = (MyActor*)thisx;\n    this->somePointer->value = 0;\n}",
  "output": "The crash is caused by accessing an uninitialized pointer. In your init function, `this->somePointer` is NULL and you're trying to dereference it. You need to allocate memory or initialize the pointer first:\n\n```c\nvoid MyActor_Init(Actor* thisx, PlayState* play) {\n    MyActor* this = (MyActor*)thisx;\n    \n    // Option 1: Allocate memory\n    this->somePointer = ZELDA_ARENA_MALLOC(sizeof(SomeStruct), __FILE__, __LINE__);\n    \n    // Option 2: Point to existing data\n    this->somePointer = &someGlobalVariable;\n    \n    // Now safe to access\n    this->somePointer->value = 0;\n}\n```"
}
```

### 9.4 System Architecture Questions

**Format**: High-level understanding of game systems
```json
{
  "instruction": "How does the Z-targeting system work in OoT?",
  "output": "The Z-targeting system in OoT works through several components:\n\n1. **Actor Flags**: Actors set ACTOR_FLAG_ATTENTION_ENABLED to be targetable\n2. **Distance Checking**: The system finds all targetable actors within range\n3. **Camera Focus**: The camera system smoothly transitions to keep the target in view\n4. **Player State**: Player sets PLAYER_STATE1_Z_TARGETING flag when locked on\n5. **Input Handling**: Z button press/hold behavior determines lock-on vs switch targeting\n\nThe core logic is in z_player_lib.c with functions like Player_UpdateLockOnTarget() and Player_ClearZTargeting()."
}
```

---

## 10. Advanced Topics for Dataset Expansion

### 10.1 3D Graphics and F3DEX3

**Vertex Processing**: Custom geometry creation and modification
**Display Lists**: Optimized rendering commands for N64 hardware
**Microcode**: Low-level graphics processor programming

### 10.2 Audio System Integration

**AudioSeq Format**: Custom music sequence creation
**Soundfont Management**: Instrument sample organization
**Spatial Audio**: 3D positioned sound effects

### 10.3 Save Data Management

**SRAM Structure**: Save file format and flag organization
**Checksum Validation**: Ensuring save data integrity
**Feature Flags**: Adding new persistent game states

### 10.4 Network and Co-op Features

**State Synchronization**: Keeping multiple players in sync
**Event Broadcasting**: Sharing game events between players
**Memory Layout**: Ensuring consistent game state

---

## 11. Dataset Creation Strategy

### 11.1 Content Categories and Ratios

**Suggested Distribution:**
- 30% - Code explanation and documentation
- 25% - Feature implementation requests
- 20% - Debugging and problem solving
- 15% - System architecture questions
- 10% - Advanced topics and edge cases

### 11.2 Quality Assurance

**Code Verification:**
- All code examples should compile against decomp
- Test implementations in emulator/hardware
- Validate against community best practices

**Technical Accuracy:**
- Cross-reference with official documentation
- Review by experienced community members
- Include version-specific information where relevant

### 11.3 Data Source Priorities

1. **Primary**: zeldaret/oot and HackerOoT source code
2. **Secondary**: CloudModding wiki documentation
3. **Tertiary**: Community tutorials and forum discussions
4. **Supporting**: Popular romhack implementations as examples

---

## 12. Implementation Recommendations

### 12.1 Incremental Development

Start with basic actor modifications and gradually expand to:
- Scene editing and custom rooms
- Complex gameplay mechanics
- Advanced graphics and audio features
- Cross-game compatibility (MM, other Zelda titles)

### 12.2 Community Integration

- Maintain compatibility with existing tools (Patcher64+, randomizer)
- Follow community coding standards and naming conventions
- Integrate with popular development workflows
- Support both decomp and traditional hex-editing approaches

### 12.3 Documentation and Examples

- Provide complete, working examples for each feature type
- Include both simple and complex implementations
- Cross-reference with official game behavior
- Maintain compatibility notes for different ROM versions

---

## Conclusion

This research compilation provides a comprehensive foundation for creating an effective instruction-response dataset for OoT romhacking AI assistance. The combination of technical source code, community documentation, and real-world examples creates opportunities for diverse, high-quality training data that can help users implement requested game features through appropriate code modifications.

The ultimate goal is enabling natural language requests like "make Link run faster" or "add a new enemy type" to result in specific, implementable code changes that integrate properly with the existing game engine and community standards.