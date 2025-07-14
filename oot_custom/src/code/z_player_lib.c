/**
 * @file z_player_lib.c
 * @brief Player Library - Core player character systems for The Legend of Zelda: Ocarina of Time
 * 
 * This file contains the fundamental systems that control Link's behavior, appearance, and physics.
 * It includes the boot data system (movement physics), equipment model mapping, rendering functions,
 * environmental hazard detection, and player state management.
 * 
 * Key Systems:
 * - Boot Data: Controls movement speed, acceleration, and physics based on equipped boots
 * - Model Groups: Maps equipped items/weapons to appropriate 3D models and animations
 * - Equipment Data: Manages Link's current tunic, boots, shield, and weapon configuration
 * - Rendering: Functions to draw Link in gameplay and pause menu contexts
 * - Environmental: Hazard detection and response (hot rooms, underwater, etc.)
 * - Z-Targeting: Lock-on system and camera focus management
 */

#include "libc64/math64.h"
#include "gfx.h"
#include "gfx_setupdl.h"
#include "regs.h"
#include "segmented_address.h"
#include "sys_matrix.h"
#include "versions.h"
#include "z_lib.h"
#include "draw.h"
#include "effect.h"
#include "play_state.h"
#include "player.h"
#include "save.h"
#include "skin_matrix.h"

#include "assets/objects/gameplay_keep/gameplay_keep.h"
#include "assets/objects/object_link_boy/object_link_boy.h"
#include "assets/objects/object_link_child/object_link_child.h"

#pragma increment_block_number "gc-eu:0 gc-eu-mq:0 gc-jp:0 gc-jp-ce:0 gc-jp-mq:0 gc-us:0 gc-us-mq:0" \
                               "pal-1.0:0 pal-1.1:0"

typedef struct BowSlingshotStringData {
    /* 0x00 */ Gfx* dList;
    /* 0x04 */ Vec3f pos;
} BowSlingshotStringData; // size = 0x10

FlexSkeletonHeader* gPlayerSkelHeaders[] = { &gLinkAdultSkel, &gLinkChildSkel };

/**
 * Boot Data System - Controls Link's movement physics based on equipped boots
 * 
 * This 2D array contains movement parameters for each boot type. The system dynamically
 * adjusts Link's physics by loading these values into global registers when boots are
 * equipped or when environmental conditions change (like entering water with Iron Boots).
 * 
 * Array Structure: sBootData[BOOT_TYPE][PARAMETER_INDEX]
 * 
 * Boot Types:
 * - KOKIRI: Standard movement, fastest run speed
 * - IRON: Heavy movement, slower speed, can walk underwater
 * - HOVER: Special anti-gravity properties on certain surfaces
 * - INDOOR: Reduced speed caps for indoor areas
 * - IRON_UNDERWATER: Special Iron Boot physics when submerged
 * - KOKIRI_CHILD: Child Link variant with different proportions
 * 
 * Each boot type has 17 parameters that control various aspects of movement:
 * [0]  REG(19)     - Basic movement multiplier
 * [1]  REG(30)     - Animation timing / step frequency
 * [2]  REG(32)     - Turn/rotation speed parameters  
 * [3]  REG(34)     - Jump/leap distance modifiers
 * [4]  REG(35)     - Walking animation speed
 * [5]  REG(36)     - Running animation transition speed
 * [6]  REG(37)     - Special movement mode parameters
 * [7]  REG(38)     - Additional animation timing
 * [8]  R_DECELERATE_RATE - How quickly Link slows down when stopping
 * [9]  R_RUN_SPEED_LIMIT - Maximum running speed (CHANGED: Kokiri boots increased from 600 to 800)
 * [10] REG(68)     - Gravity/physics modifiers (negative values)
 * [11] REG(69)     - Ground friction/traction values
 * [12] IREG(66)    - Advanced physics parameter 1
 * [13] IREG(67)    - Advanced physics parameter 2  
 * [14] IREG(68)    - Advanced physics parameter 3
 * [15] IREG(69)    - Advanced physics parameter 4
 * [16] MREG(95)    - Miscellaneous timing parameter
 * 
 * MODIFICATION NOTES: 
 * - Adult Kokiri Boots speed increased from 600 to 800 for faster movement
 * - Child Kokiri Boots significantly enhanced for much faster child movement
 *   (speed limit increased from 550 to 2000, movement multiplier from 200 to 600)
 */
s16 sBootData[PLAYER_BOOTS_MAX][17] = {
    // PLAYER_BOOTS_KOKIRI - Default boots, fastest movement
    {
        600,                         // REG(19) - Basic movement multiplier (INCREASED from 200 to 600)
        FRAMERATE_CONST(1000, 1200), // REG(30) - Animation timing constant
        FRAMERATE_CONST(300, 360),   // REG(32) - Turn speed parameter
        700,                         // REG(34) - Jump distance modifier
        FRAMERATE_CONST(550, 660),   // REG(35) - Walking animation speed
        FRAMERATE_CONST(270, 324),   // REG(36) - Running transition speed
        600,                         // REG(37) - Special movement parameter
        FRAMERATE_CONST(350, 420),   // REG(38) - Additional animation timing
        800,                         // R_DECELERATE_RATE - Stopping deceleration rate
        1800,                        // R_RUN_SPEED_LIMIT - INCREASED from 800 to 1800 for much faster adult movement
        -100,                        // REG(68) - Gravity modifier (negative)
        600,                         // REG(69) - Ground friction/traction
        590,                         // IREG(66) - Advanced physics parameter
        750,                         // IREG(67) - Advanced physics parameter
        125,                         // IREG(68) - Advanced physics parameter
        200,                         // IREG(69) - Advanced physics parameter
        FRAMERATE_CONST(130, 156),   // MREG(95) - Miscellaneous timing
    },
    // PLAYER_BOOTS_IRON - Heavy boots, can walk underwater, slower movement
    {
        200,                         // REG(19) - Basic movement multiplier
        FRAMERATE_CONST(1000, 1200), // REG(30) - Animation timing
        FRAMERATE_CONST(300, 360),   // REG(32) - Turn speed
        700,                         // REG(34) - Jump distance
        FRAMERATE_CONST(550, 660),   // REG(35) - Walking speed
        FRAMERATE_CONST(270, 324),   // REG(36) - Running transition
        1000,                        // REG(37) - Special movement (heavier feel)
        FRAMERATE_CONST(0, 0),       // REG(38) - No special animation timing
        800,                         // R_DECELERATE_RATE - Deceleration rate
        300,                         // R_RUN_SPEED_LIMIT - Much slower max speed
        -160,                        // REG(68) - Stronger gravity (heavier)
        600,                         // REG(69) - Ground friction
        590,                         // IREG(66) - Advanced physics
        750,                         // IREG(67) - Advanced physics
        125,                         // IREG(68) - Advanced physics
        200,                         // IREG(69) - Advanced physics
        FRAMERATE_CONST(130, 156),   // MREG(95) - Timing
    },
    // PLAYER_BOOTS_HOVER - Hover boots, can float over certain surfaces
    {
        300,                         // REG(19) - Basic movement multiplier (INCREASED from 200)
        FRAMERATE_CONST(1000, 1200), // REG(30) - Animation timing
        FRAMERATE_CONST(300, 360),   // REG(32) - Turn speed
        700,                         // REG(34) - Jump distance
        FRAMERATE_CONST(550, 660),   // REG(35) - Walking speed
        FRAMERATE_CONST(270, 324),   // REG(36) - Running transition
        600,                         // REG(37) - Standard movement
        FRAMERATE_CONST(600, 720),   // REG(38) - Hover animation timing
        800,                         // R_DECELERATE_RATE - Deceleration
        900,                         // R_RUN_SPEED_LIMIT - INCREASED from 550 to 900
        -100,                        // REG(68) - Normal gravity when not hovering
        600,                         // REG(69) - Ground friction
        540,                         // IREG(66) - Hover physics parameter
        270,                         // IREG(67) - Hover physics parameter
        25,                          // IREG(68) - Reduced physics for floating
        0,                           // IREG(69) - No additional physics
        FRAMERATE_CONST(130, 156),   // MREG(95) - Timing
    },
    // PLAYER_BOOTS_INDOOR - Special indoor movement limits
    {
        250,                         // REG(19) - Basic movement multiplier (INCREASED from 200)
        FRAMERATE_CONST(1000, 1200), // REG(30) - Animation timing
        FRAMERATE_CONST(300, 360),   // REG(32) - Turn speed
        700,                         // REG(34) - Jump distance
        FRAMERATE_CONST(380, 456),   // REG(35) - Slower walking for indoors
        FRAMERATE_CONST(400, 480),   // REG(36) - Slower running transition
        0,                           // REG(37) - No special movement
        FRAMERATE_CONST(300, 360),   // REG(38) - Indoor animation timing
        800,                         // R_DECELERATE_RATE - Deceleration
        700,                         // R_RUN_SPEED_LIMIT - INCREASED from 500 to 700
        -100,                        // REG(68) - Normal gravity
        600,                         // REG(69) - Ground friction
        590,                         // IREG(66) - Standard physics
        750,                         // IREG(67) - Standard physics
        125,                         // IREG(68) - Standard physics
        200,                         // IREG(69) - Standard physics
        FRAMERATE_CONST(130, 156),   // MREG(95) - Timing
    },
    // PLAYER_BOOTS_IRON_UNDERWATER - Iron boots when submerged
    {
        80,                        // REG(19) - Reduced movement underwater
        FRAMERATE_CONST(800, 960), // REG(30) - Slower animation timing
        FRAMERATE_CONST(150, 180), // REG(32) - Slower turns underwater
        700,                       // REG(34) - Jump distance (unused underwater)
        FRAMERATE_CONST(480, 576), // REG(35) - Underwater walking speed
        FRAMERATE_CONST(270, 324), // REG(36) - Underwater running transition
        600,                       // REG(37) - Standard movement
        FRAMERATE_CONST(50, 60),   // REG(38) - Very slow underwater animation
        800,                       // R_DECELERATE_RATE - Deceleration
        550,                       // R_RUN_SPEED_LIMIT - Moderate underwater speed
        -40,                       // REG(68) - Reduced gravity underwater
        400,                       // REG(69) - Reduced friction underwater
        540,                       // IREG(66) - Underwater physics
        270,                       // IREG(67) - Underwater physics
        25,                        // IREG(68) - Underwater physics
        0,                         // IREG(69) - No additional physics
        FRAMERATE_CONST(80, 96),   // MREG(95) - Underwater timing
    },
    // PLAYER_BOOTS_KOKIRI_CHILD - Child Link variant with different proportions
    {
        1200,                        // REG(19) - Basic movement multiplier (INCREASED from 600 to 1200)
        FRAMERATE_CONST(1000, 1200), // REG(30) - Animation timing (DEFAULT)
        FRAMERATE_CONST(300, 360),   // REG(32) - Turn speed (DEFAULT)
        10000,                       // REG(34) - Child proportional jump distance (INCREASED from 800)
        FRAMERATE_CONST(500, 2000),  // REG(35) - Child walking speed (INCREASED from 500-600)
        FRAMERATE_CONST(400, 480),   // REG(36) - Child running transition (DEFAULT)
        2000,                        // REG(37) - Child movement modifier (INCREASED from 800)
        FRAMERATE_CONST(400, 480),   // REG(38) - Child animation timing (DEFAULT)
        800,                         // R_DECELERATE_RATE - Deceleration (DEFAULT)
        3500,                        // R_RUN_SPEED_LIMIT - INCREASED from 2000 to 3500 for super fast child movement
        -20,                         // REG(68) - Normal gravity (CHANGED from -100)
        600,                         // REG(69) - Ground friction (DEFAULT)
        540,                         // IREG(66) - Child physics (DEFAULT)
        750,                         // IREG(67) - Child physics (DEFAULT)
        125,                         // IREG(68) - Child physics (DEFAULT)
        400,                         // IREG(69) - Child-specific physics (DEFAULT)
        FRAMERATE_CONST(200, 240),   // MREG(95) - Child timing (DEFAULT)
    },
};

/**
 * Item Action to Model Group Mapping
 * 
 * This array maps each possible item action (PLAYER_IA_*) to a corresponding model group
 * (PLAYER_MODELGROUP_*). When Link uses an item, this determines which set of 3D models
 * and animations should be used for his hands, weapons, and equipment.
 * 
 * Model Groups control:
 * - Which 3D models are used for Link's hands (open, closed, holding items)
 * - What weapons/tools appear in Link's hands
 * - How shields and sheaths are positioned on Link's body
 * - Which animation set is used for movement and actions
 * 
 * Key Model Groups:
 * - DEFAULT: Basic open hands, no weapons
 * - SWORD_AND_SHIELD: Sword in left hand, shield ready in right hand
 * - BGS: Two-handed Biggoron's Sword
 * - BOW_SLINGSHOT: Bow/slingshot aiming stance
 * - HOOKSHOT: Hookshot/Longshot in right hand
 * - BOTTLE: Bottle held in left hand
 * - HAMMER: Two-handed Megaton Hammer
 * - BOOMERANG: Boomerang in left hand
 * - OCARINA/OOT: Various ocarina holding positions
 */
u8 sActionModelGroups[PLAYER_IA_MAX] = {
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_NONE - No item equipped
    PLAYER_MODELGROUP_SWORD,            // PLAYER_IA_SWORD_CS - Cutscene sword
    PLAYER_MODELGROUP_10,               // PLAYER_IA_FISHING_POLE - Fishing pole (special handling)
    PLAYER_MODELGROUP_SWORD_AND_SHIELD, // PLAYER_IA_SWORD_MASTER - Master Sword with shield
    PLAYER_MODELGROUP_SWORD_AND_SHIELD, // PLAYER_IA_SWORD_KOKIRI - Kokiri Sword with shield
    PLAYER_MODELGROUP_BGS,              // PLAYER_IA_SWORD_BIGGORON - Two-handed Biggoron's Sword
    PLAYER_MODELGROUP_10,               // PLAYER_IA_DEKU_STICK - Deku Stick (drawn separately)
    PLAYER_MODELGROUP_HAMMER,           // PLAYER_IA_HAMMER - Two-handed Megaton Hammer
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW - Adult bow aiming stance
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_FIRE - Fire Arrow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_ICE - Ice Arrow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_LIGHT - Light Arrow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_0C - Unused bow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_0D - Unused bow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_BOW_0E - Unused bow variant
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_SLINGSHOT - Child slingshot aiming
    PLAYER_MODELGROUP_HOOKSHOT,         // PLAYER_IA_HOOKSHOT - Hookshot in right hand
    PLAYER_MODELGROUP_HOOKSHOT,         // PLAYER_IA_LONGSHOT - Longshot in right hand
    PLAYER_MODELGROUP_EXPLOSIVES,       // PLAYER_IA_BOMB - Bomb (uses default models)
    PLAYER_MODELGROUP_EXPLOSIVES,       // PLAYER_IA_BOMBCHU - Bombchu (uses default models)
    PLAYER_MODELGROUP_BOOMERANG,        // PLAYER_IA_BOOMERANG - Boomerang in left hand
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MAGIC_SPELL_15 - Magic spell casting
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MAGIC_SPELL_16 - Magic spell casting
    PLAYER_MODELGROUP_BOW_SLINGSHOT,    // PLAYER_IA_MAGIC_SPELL_17 - Magic bow spell
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_FARORES_WIND - Farore's Wind spell
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_NAYRUS_LOVE - Nayru's Love spell
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_DINS_FIRE - Din's Fire spell
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_DEKU_NUT - Deku Nut throwing
    PLAYER_MODELGROUP_OCARINA,          // PLAYER_IA_OCARINA_FAIRY - Fairy Ocarina in right hand
    PLAYER_MODELGROUP_OOT,              // PLAYER_IA_OCARINA_OF_TIME - Ocarina of Time special pose
    // All bottle variants use the BOTTLE model group (bottle in left hand)
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE - Empty bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_FISH - Bottle with fish
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_FIRE - Bottle with blue fire
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_BUG - Bottle with bug
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_POE - Bottle with Poe soul
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_BIG_POE - Bottle with Big Poe soul
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_RUTOS_LETTER - Bottle with Ruto's letter
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_POTION_RED - Red potion bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_POTION_BLUE - Blue potion bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_POTION_GREEN - Green potion bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_MILK_FULL - Full milk bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_MILK_HALF - Half milk bottle
    PLAYER_MODELGROUP_BOTTLE,           // PLAYER_IA_BOTTLE_FAIRY - Bottle with fairy
    // Quest items and masks use default model group (open hands)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_ZELDAS_LETTER - Zelda's letter
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_WEIRD_EGG - Weird egg (child)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_CHICKEN - Cucco (child)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MAGIC_BEAN - Magic bean
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_POCKET_EGG - Pocket egg (child)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_POCKET_CUCCO - Pocket cucco (child)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_COJIRO - Cojiro (trading sequence)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_ODD_MUSHROOM - Odd mushroom (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_ODD_POTION - Odd potion (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_POACHERS_SAW - Poacher's saw (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_BROKEN_GORONS_SWORD - Broken Goron's sword
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_PRESCRIPTION - Prescription (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_FROG - Frog (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_EYEDROPS - Eyedrops (trading)
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_CLAIM_CHECK - Claim check (trading)
    // All masks use default model group as mask models are handled separately
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_KEATON - Keaton mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_SKULL - Skull mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_SPOOKY - Spooky mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_BUNNY_HOOD - Bunny hood mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_GORON - Goron mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_ZORA - Zora mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_GERUDO - Gerudo mask
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_MASK_TRUTH - Mask of Truth
    PLAYER_MODELGROUP_DEFAULT,          // PLAYER_IA_LENS_OF_TRUTH - Lens of Truth
};

typedef struct EnvHazardTextTriggerEntry {
    /* 0x0 */ u8 flag;
    /* 0x2 */ u16 textId;
} EnvHazardTextTriggerEntry; // size = 0x4

/**
 * Environmental Hazard Text Triggers
 * 
 * This array defines which text messages should be displayed when Link enters
 * dangerous environmental conditions. Each entry contains a flag to track if
 * the message has been shown and the text ID to display.
 * 
 * The system prevents spam by setting flags in gSaveContext.envHazardTextTriggerFlags
 * after showing each message once.
 */
EnvHazardTextTriggerEntry sEnvHazardTextTriggers[] = {
    { ENV_HAZARD_TEXT_TRIGGER_HOTROOM, 0x3040 },    // Hot room warning (like Death Mountain)
    { ENV_HAZARD_TEXT_TRIGGER_UNDERWATER, 0x401D }, // Underwater air warning (floor)
    { 0, 0x0000 },                                  // Swimming (no text warning)
    { ENV_HAZARD_TEXT_TRIGGER_UNDERWATER, 0x401D }, // Underwater air warning (free swimming)
};

/**
 * Player Model Type Configuration Matrix
 * 
 * This is the core of Link's visual appearance system. Each model group maps to specific
 * model types for different parts of Link's body and equipment. The system supports
 * different configurations for adult and child Link automatically.
 * 
 * Matrix Structure: gPlayerModelTypes[MODEL_GROUP][COMPONENT_TYPE]
 * 
 * Component Types:
 * [0] ANIM - Animation type (determines movement animation set)
 * [1] LEFT_HAND - What Link holds/how his left hand appears
 * [2] RIGHT_HAND - What Link holds/how his right hand appears  
 * [3] SHEATH - How sword/shield appear on Link's back
 * [4] WAIST - Waist/belt equipment appearance
 * 
 * Animation Types:
 * - ANIMTYPE_0: Basic idle/movement animations
 * - ANIMTYPE_1: Sword and shield combat animations
 * - ANIMTYPE_2: Shield-only defensive animations
 * - ANIMTYPE_3: Two-handed weapon animations (BGS, Hammer)
 * - ANIMTYPE_4: Ranged weapon animations (Bow, Hookshot)
 * - ANIMTYPE_5: Item throwing animations (Bombs, etc.)
 * 
 * Left Hand Types:
 * - LH_OPEN: Empty open hand
 * - LH_CLOSED: Empty closed fist
 * - LH_SWORD: Holding sword (Kokiri/Master)
 * - LH_BGS: Holding Biggoron's Sword (Child uses Master Sword model)
 * - LH_HAMMER: Holding Megaton Hammer (Child uses empty hand)
 * - LH_BOOMERANG: Holding boomerang (Adult uses empty hand)
 * - LH_BOTTLE: Holding bottle (bottle mesh drawn separately)
 * 
 * Right Hand Types:
 * - RH_OPEN: Empty open hand
 * - RH_CLOSED: Empty closed fist
 * - RH_SHIELD: Holding shield (type determined by currentShield)
 * - RH_BOW_SLINGSHOT: Holding bow (adult) or slingshot (child)
 * - RH_OCARINA: Holding Fairy Ocarina (child) or OoT (adult)
 * - RH_OOT: Holding Ocarina of Time specifically
 * - RH_HOOKSHOT: Holding Hookshot/Longshot (adult only)
 * 
 * Sheath Types:
 * - SHEATH_16: Sword sheathed, no shield on back
 * - SHEATH_17: Empty sheath, no shield on back
 * - SHEATH_18: Sword sheathed, shield on back
 * - SHEATH_19: Empty sheath, shield on back
 */
u8 gPlayerModelTypes[PLAYER_MODELGROUP_MAX][PLAYER_MODELGROUPENTRY_MAX] = {
    /* PLAYER_MODELGROUP_0 - Unused group (legacy/bug workaround) */
    { PLAYER_ANIMTYPE_2, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_SHIELD, PLAYER_MODELTYPE_SHEATH_16,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_CHILD_HYLIAN_SHIELD - Child Link with Hylian Shield and sword */
    { PLAYER_ANIMTYPE_1, PLAYER_MODELTYPE_LH_SWORD, PLAYER_MODELTYPE_RH_CLOSED, PLAYER_MODELTYPE_SHEATH_19,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_SWORD_AND_SHIELD - Standard sword and shield combat */
    { PLAYER_ANIMTYPE_1, PLAYER_MODELTYPE_LH_SWORD, PLAYER_MODELTYPE_RH_SHIELD, PLAYER_MODELTYPE_SHEATH_17,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_DEFAULT - Basic stance with no weapons */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_4 - Unused group, identical to DEFAULT */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_BGS - Two-handed Biggoron's Sword */
    { PLAYER_ANIMTYPE_3, PLAYER_MODELTYPE_LH_BGS, PLAYER_MODELTYPE_RH_CLOSED, PLAYER_MODELTYPE_SHEATH_19,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_BOW_SLINGSHOT - Ranged weapon aiming */
    { PLAYER_ANIMTYPE_4, PLAYER_MODELTYPE_LH_CLOSED, PLAYER_MODELTYPE_RH_BOW_SLINGSHOT, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_EXPLOSIVES - Bomb/Bombchu throwing */
    { PLAYER_ANIMTYPE_5, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_BOOMERANG - Boomerang in left hand */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_BOOMERANG, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_HOOKSHOT - Hookshot/Longshot in right hand */
    { PLAYER_ANIMTYPE_4, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_HOOKSHOT, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_10 - Special items (Deku Stick, Fishing Pole) */
    { PLAYER_ANIMTYPE_3, PLAYER_MODELTYPE_LH_CLOSED, PLAYER_MODELTYPE_RH_CLOSED, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_HAMMER - Two-handed Megaton Hammer */
    { PLAYER_ANIMTYPE_3, PLAYER_MODELTYPE_LH_HAMMER, PLAYER_MODELTYPE_RH_CLOSED, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_OCARINA - Fairy Ocarina held in right hand */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_OCARINA, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_OOT - Ocarina of Time special holding pose */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_OPEN, PLAYER_MODELTYPE_RH_OOT, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_BOTTLE - Bottle held in left hand */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_BOTTLE, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_18,
      PLAYER_MODELTYPE_WAIST },
    /* PLAYER_MODELGROUP_SWORD - Sword without shield */
    { PLAYER_ANIMTYPE_0, PLAYER_MODELTYPE_LH_SWORD, PLAYER_MODELTYPE_RH_OPEN, PLAYER_MODELTYPE_SHEATH_19,
      PLAYER_MODELTYPE_WAIST },
};

Gfx* sPlayerRightHandShieldDLs[PLAYER_SHIELD_MAX * 4] = {
    // PLAYER_SHIELD_NONE
    gLinkAdultRightHandClosedNearDL,
    gLinkChildRightHandClosedNearDL,
    gLinkAdultRightHandClosedFarDL,
    gLinkChildRightHandClosedFarDL,
    // PLAYER_SHIELD_DEKU
    gLinkAdultRightHandClosedNearDL,
    gLinkChildRightFistAndDekuShieldNearDL,
    gLinkAdultRightHandClosedFarDL,
    gLinkChildRightFistAndDekuShieldFarDL,
    // PLAYER_SHIELD_HYLIAN
    gLinkAdultRightHandHoldingHylianShieldNearDL,
    gLinkChildRightHandClosedNearDL,
    gLinkAdultRightHandHoldingHylianShieldFarDL,
    gLinkChildRightHandClosedFarDL,
    // PLAYER_SHIELD_MIRROR
    gLinkAdultRightHandHoldingMirrorShieldNearDL,
    gLinkChildRightHandClosedNearDL,
    gLinkAdultRightHandHoldingMirrorShieldFarDL,
    gLinkChildRightHandClosedFarDL,
};

Gfx* D_80125D28[(PLAYER_SHIELD_MAX + 2) * 4] = {
    // PLAYER_SHIELD_NONE
    gLinkAdultMasterSwordAndSheathNearDL,
    gLinkChildSwordAndSheathNearDL,
    gLinkAdultMasterSwordAndSheathFarDL,
    gLinkChildSwordAndSheathFarDL,
    // PLAYER_SHIELD_DEKU
    gLinkAdultMasterSwordAndSheathNearDL,
    gLinkChildDekuShieldSwordAndSheathNearDL,
    gLinkAdultMasterSwordAndSheathFarDL,
    gLinkChildDekuShieldSwordAndSheathFarDL,
    // PLAYER_SHIELD_HYLIAN
    gLinkAdultHylianShieldSwordAndSheathNearDL,
    gLinkChildHylianShieldSwordAndSheathNearDL,
    gLinkAdultHylianShieldSwordAndSheathFarDL,
    gLinkChildHylianShieldSwordAndSheathFarDL,
    // PLAYER_SHIELD_MIRROR
    gLinkAdultMirrorShieldSwordAndSheathNearDL,
    gLinkChildSwordAndSheathNearDL,
    gLinkAdultMirrorShieldSwordAndSheathFarDL,
    gLinkChildSwordAndSheathFarDL,
    // PLAYER_SHIELD_NONE (child, no sword)
    NULL,
    NULL,
    NULL,
    NULL,
    // PLAYER_SHIELD_DEKU (child, no sword)
    NULL,
    gLinkChildDekuShieldWithMatrixDL,
    NULL,
    gLinkChildDekuShieldWithMatrixDL,
};

Gfx* D_80125D88[(PLAYER_SHIELD_MAX + 2) * 4] = {
    // PLAYER_SHIELD_NONE
    gLinkAdultSheathNearDL,
    gLinkChildSheathNearDL,
    gLinkAdultSheathFarDL,
    gLinkChildSheathFarDL,
    // PLAYER_SHIELD_DEKU
    gLinkAdultSheathNearDL,
    gLinkChildDekuShieldAndSheathNearDL,
    gLinkAdultSheathFarDL,
    gLinkChildDekuShieldAndSheathFarDL,
    // PLAYER_SHIELD_HYLIAN
    gLinkAdultHylianShieldAndSheathNearDL,
    gLinkChildHylianShieldAndSheathNearDL,
    gLinkAdultHylianShieldAndSheathFarDL,
    gLinkChildHylianShieldAndSheathFarDL,
    // PLAYER_SHIELD_MIRROR
    gLinkAdultMirrorShieldAndSheathNearDL,
    gLinkChildSheathNearDL,
    gLinkAdultMirrorShieldAndSheathFarDL,
    gLinkChildSheathFarDL,
    // PLAYER_SHIELD_NONE (child, no sword)
    NULL,
    NULL,
    NULL,
    NULL,
    // PLAYER_SHIELD_DEKU (child, no sword)
    gLinkAdultSheathNearDL,
    gLinkChildDekuShieldWithMatrixDL,
    gLinkAdultSheathNearDL,
    gLinkChildDekuShieldWithMatrixDL,
};

Gfx* gPlayerLeftHandBgsDLs[] = {
    // biggoron sword
    gLinkAdultLeftHandHoldingBgsNearDL,
    gLinkChildLeftHandHoldingMasterSwordDL,
    gLinkAdultLeftHandHoldingBgsFarDL,
    gLinkChildLeftHandHoldingMasterSwordDL,
    // broken giant knife
    gLinkAdultHandHoldingBrokenGiantsKnifeDL,
    gLinkChildLeftHandHoldingMasterSwordDL,
    gLinkAdultHandHoldingBrokenGiantsKnifeFarDL,
    gLinkChildLeftHandHoldingMasterSwordDL,
};

Gfx* gPlayerLeftHandOpenDLs[] = {
    gLinkAdultLeftHandNearDL,
    gLinkChildLeftHandNearDL,
    gLinkAdultLeftHandFarDL,
    gLinkChildLeftHandFarDL,
};

Gfx* gPlayerLeftHandClosedDLs[] = {
    gLinkAdultLeftHandClosedNearDL,
    gLinkChildLeftFistNearDL,
    gLinkAdultLeftHandClosedFarDL,
    gLinkChildLeftFistFarDL,
};

// Identical to `sPlayerLeftHandSwordDLs` and unused
Gfx* sPlayerLeftHandSwordDLs2[] = {
    gLinkAdultLeftHandHoldingMasterSwordNearDL,
    gLinkChildLeftFistAndKokiriSwordNearDL,
    gLinkAdultLeftHandHoldingMasterSwordFarDL,
    gLinkChildLeftFistAndKokiriSwordFarDL,
};

Gfx* sPlayerLeftHandSwordDLs[] = {
    gLinkAdultLeftHandHoldingMasterSwordNearDL,
    gLinkChildLeftFistAndKokiriSwordNearDL,
    gLinkAdultLeftHandHoldingMasterSwordFarDL,
    gLinkChildLeftFistAndKokiriSwordFarDL,
};

Gfx* sPlayerRightHandOpenDLs[] = {
    gLinkAdultRightHandNearDL,
    gLinkChildRightHandNearDL,
    gLinkAdultRightHandFarDL,
    gLinkChildRightHandFarDL,
};

Gfx* sPlayerRightHandClosedDLs[] = {
    gLinkAdultRightHandClosedNearDL,
    gLinkChildRightHandClosedNearDL,
    gLinkAdultRightHandClosedFarDL,
    gLinkChildRightHandClosedFarDL,
};

Gfx* sPlayerRightHandBowSlingshotDLs[] = {
    gLinkAdultRightHandHoldingBowNearDL,
    gLinkChildRightHandHoldingSlingshotNearDL,
    gLinkAdultRightHandHoldingBowFarDL,
    gLinkChildRightHandHoldingSlingshotFarDL,
};

Gfx* D_80125E78[] = {
    gLinkAdultMasterSwordAndSheathNearDL,
    gLinkChildSwordAndSheathNearDL,
    gLinkAdultMasterSwordAndSheathFarDL,
    gLinkChildSwordAndSheathFarDL,
};

Gfx* D_80125E88[] = {
    gLinkAdultSheathNearDL,
    gLinkChildSheathNearDL,
    gLinkAdultSheathFarDL,
    gLinkChildSheathFarDL,
};

Gfx* sPlayerWaistDLs[] = {
    gLinkAdultWaistNearDL,
    gLinkChildWaistNearDL,
    gLinkAdultWaistFarDL,
    gLinkChildWaistFarDL,
};

// Identical to `sPlayerRightHandBowSlingshotDLs` and unused
Gfx* sPlayerRightHandBowSlingshotDLs2[] = {
    gLinkAdultRightHandHoldingBowNearDL,
    gLinkChildRightHandHoldingSlingshotNearDL,
    gLinkAdultRightHandHoldingBowFarDL,
    gLinkChildRightHandHoldingSlingshotFarDL,
};

Gfx* sPlayerRightHandOcarinaDLs[] = {
    gLinkAdultRightHandHoldingOotNearDL,
    gLinkChildRightHandHoldingFairyOcarinaNearDL,
    gLinkAdultRightHandHoldingOotFarDL,
    gLinkChildRightHandHoldingFairyOcarinaFarDL,
};

Gfx* sPlayerRightHandOotDLs[] = {
    gLinkAdultRightHandHoldingOotNearDL,
    gLinkChildRightHandAndOotNearDL,
    gLinkAdultRightHandHoldingOotFarDL,
    gLinkChildRightHandHoldingOOTFarDL,
};

Gfx* sPlayerRightHandHookshotDLs[] = {
    gLinkAdultRightHandHoldingHookshotNearDL,
    gLinkChildRightHandNearDL,
    gLinkAdultRightHandHoldingHookshotNearDL, // The 'far' display list exists but is not used
    gLinkChildRightHandFarDL,
};

Gfx* sPlayerLeftHandHammerDLs[] = {
    gLinkAdultLeftHandHoldingHammerNearDL,
    gLinkChildLeftHandNearDL,
    gLinkAdultLeftHandHoldingHammerFarDL,
    gLinkChildLeftHandFarDL,
};

Gfx* gPlayerLeftHandBoomerangDLs[] = {
    gLinkAdultLeftHandNearDL,
    gLinkChildLeftFistAndBoomerangNearDL,
    gLinkAdultLeftHandFarDL,
    gLinkChildLeftFistAndBoomerangFarDL,
};

Gfx* sPlayerLeftHandBottleDLs[] = {
    gLinkAdultLeftHandOutNearDL,
    gLinkChildLeftHandUpNearDL,
    gLinkAdultLeftHandOutNearDL,
    gLinkChildLeftHandUpNearDL,
};

Gfx* sFirstPersonLeftForearmDLs[] = {
    gLinkAdultRightArmOutNearDL,
    NULL,
};

Gfx* sFirstPersonLeftHandDLs[] = {
    gLinkAdultRightHandOutNearDL,
    NULL,
};

Gfx* sFirstPersonRightShoulderDLs[] = {
    gLinkAdultRightShoulderNearDL,
    gLinkChildRightShoulderNearDL,
};

Gfx* sFirstPersonForearmDLs[] = {
    gLinkAdultLeftArmOutNearDL,
    NULL,
};

Gfx* sFirstPersonRightHandHoldingWeaponDLs[] = {
    gLinkAdultRightHandHoldingBowFirstPersonDL,
    gLinkChildRightArmStretchedSlingshotDL,
};

// Indexed by model types (left hand, right hand, sheath or waist)
Gfx** sPlayerDListGroups[PLAYER_MODELTYPE_MAX] = {
    gPlayerLeftHandOpenDLs,           // PLAYER_MODELTYPE_LH_OPEN
    gPlayerLeftHandClosedDLs,         // PLAYER_MODELTYPE_LH_CLOSED
    sPlayerLeftHandSwordDLs,          // PLAYER_MODELTYPE_LH_SWORD
    sPlayerLeftHandSwordDLs2,         // PLAYER_MODELTYPE_LH_SWORD_2
    gPlayerLeftHandBgsDLs,            // PLAYER_MODELTYPE_LH_BGS
    sPlayerLeftHandHammerDLs,         // PLAYER_MODELTYPE_LH_HAMMER
    gPlayerLeftHandBoomerangDLs,      // PLAYER_MODELTYPE_LH_BOOMERANG
    sPlayerLeftHandBottleDLs,         // PLAYER_MODELTYPE_LH_BOTTLE
    sPlayerRightHandOpenDLs,          // PLAYER_MODELTYPE_RH_OPEN
    sPlayerRightHandClosedDLs,        // PLAYER_MODELTYPE_RH_CLOSED
    sPlayerRightHandShieldDLs,        // PLAYER_MODELTYPE_RH_SHIELD
    sPlayerRightHandBowSlingshotDLs,  // PLAYER_MODELTYPE_RH_BOW_SLINGSHOT
    sPlayerRightHandBowSlingshotDLs2, // PLAYER_MODELTYPE_RH_BOW_SLINGSHOT_2
    sPlayerRightHandOcarinaDLs,       // PLAYER_MODELTYPE_RH_OCARINA
    sPlayerRightHandOotDLs,           // PLAYER_MODELTYPE_RH_OOT
    sPlayerRightHandHookshotDLs,      // PLAYER_MODELTYPE_RH_HOOKSHOT
    D_80125E78,                       // PLAYER_MODELTYPE_SHEATH_16
    D_80125E88,                       // PLAYER_MODELTYPE_SHEATH_17
    D_80125D28,                       // PLAYER_MODELTYPE_SHEATH_18
    D_80125D88,                       // PLAYER_MODELTYPE_SHEATH_19
    sPlayerWaistDLs,                  // PLAYER_MODELTYPE_WAIST
};

Gfx gCullBackDList[] = {
    gsSPSetGeometryMode(G_CULL_BACK),
    gsSPEndDisplayList(),
};

Gfx gCullFrontDList[] = {
    gsSPSetGeometryMode(G_CULL_FRONT),
    gsSPEndDisplayList(),
};

Vec3f* sCurBodyPartPos;
s32 sDListsLodOffset;
Vec3f sGetItemRefPos;
s32 sLeftHandType;
s32 sRightHandType;

/**
 * Link's Tunic Color Configuration
 * 
 * This array defines the RGB color values used to tint Link's tunic model.
 * The colors are applied as environment colors during rendering to change
 * the appearance of the base tunic model without requiring separate textures.
 * 
 * MODIFICATION NOTE: The Kokiri Tunic has been changed from the original
 * green color { 30, 105, 27 } to purple { 128, 0, 128 } for gameplay modification.
 * This creates a visual distinction from the traditional green tunic.
 * 
 * Original Colors:
 * - Kokiri: Green { 30, 105, 27 } - CHANGED to Purple { 128, 0, 128 }
 * - Goron: Red-Orange { 100, 20, 0 } - Heat resistance tunic (DEFAULT)
 * - Zora: Blue { 0, 60, 100 } - Underwater breathing tunic (DEFAULT)
 */
Color_RGB8 sTunicColors[PLAYER_TUNIC_MAX] = {
    { 128, 0, 128 }, // PLAYER_TUNIC_KOKIRI - MODIFIED: Changed from green { 30, 105, 27 } to purple { 128, 0, 128 }
    { 100, 20, 0 },  // PLAYER_TUNIC_GORON - Heat-resistant red/orange (DEFAULT)
    { 0, 60, 100 },  // PLAYER_TUNIC_ZORA - Water-breathing blue (DEFAULT)
};

/**
 * Gauntlet Color Configuration
 * 
 * Colors for the Silver Gauntlets and Golden Gauntlets that appear
 * over Link's hands when equipped. These are rendered as additional
 * geometry on top of the hand models.
 */
Color_RGB8 sGauntletColors[] = {
    { 255, 255, 255 }, // Silver Gauntlets - White/silver
    { 254, 207, 15 },  // Golden Gauntlets - Gold/yellow
};

/**
 * Boot Display List Groups
 * 
 * Special boot models that are rendered over Link's feet for Iron Boots
 * and Hover Boots. Kokiri Boots use the default foot models.
 * Each entry contains [left_boot_model, right_boot_model].
 */
Gfx* sBootDListGroups[][2] = {
    { gLinkAdultLeftIronBootDL, gLinkAdultRightIronBootDL },   // PLAYER_BOOTS_IRON - Heavy metal boots
    { gLinkAdultLeftHoverBootDL, gLinkAdultRightHoverBootDL }, // PLAYER_BOOTS_HOVER - Floating boots
};

/**
 * Player Boot Data System - Core Movement Physics Controller
 * 
 * This function is the heart of Link's movement system. It loads movement parameters
 * from the sBootData array into global registers that control physics, animations,
 * and behavior throughout the game engine.
 * 
 * The system dynamically adjusts Link's capabilities based on:
 * - Currently equipped boots (Kokiri, Iron, Hover)
 * - Environmental conditions (underwater, indoor/outdoor)
 * - Age state (Adult vs Child Link)
 * - Special movement states (swimming, climbing, etc.)
 * 
 * Key Features:
 * - Automatic switching to child-specific parameters for young Link
 * - Special underwater physics when Iron Boots are worn in water
 * - Indoor speed limiting to prevent running in tight spaces
 * - Frame-rate independent timing using FRAMERATE_CONST macros
 * 
 * Boot Type Selection Logic:
 * 1. Start with player's currentBoots value
 * 2. If Kokiri + Child Link -> Use KOKIRI_CHILD parameters  
 * 3. If Iron + Underwater -> Use IRON_UNDERWATER parameters
 * 4. Apply special register settings for Iron Boots (gravity, camera)
 * 5. Load all 17 parameters from selected boot data entry
 * 6. Override speed limit for indoor rooms
 * 
 * Global Registers Affected:
 * - REG(19, 27, 30, 32, 34-38, 48, 68-69): Movement and animation timing
 * - R_DECELERATE_RATE: How quickly Link stops when stick is released
 * - R_RUN_SPEED_LIMIT: Maximum running speed (modified for faster gameplay)
 * - IREG(66-69): Advanced physics parameters for special behaviors
 * - MREG(95): Miscellaneous timing parameter
 * 
 * @param play Current PlayState context
 * @param this Player instance
 */
void Player_SetBootData(PlayState* play, Player* this) {
    s32 currentBoots;
    s16* bootRegs;

    // Set default camera and physics parameters
    REG(27) = 2000; // Camera-related parameter
    REG(48) = 370;  // Physics-related parameter

    // Determine which boot data entry to use based on equipment and state
    currentBoots = this->currentBoots;
    
    // Special case: Child Link with Kokiri Boots uses different proportions
    if (currentBoots == PLAYER_BOOTS_KOKIRI) {
        if (!LINK_IS_ADULT) {
            currentBoots = PLAYER_BOOTS_KOKIRI_CHILD;
        }
    } 
    // Special case: Iron Boots underwater have modified physics
    else if (currentBoots == PLAYER_BOOTS_IRON) {
        if (this->stateFlags1 & PLAYER_STATE1_27) { // Swimming/underwater state
            currentBoots = PLAYER_BOOTS_IRON_UNDERWATER;
        }
        // Iron Boots modify camera and gravity parameters
        REG(27) = 500;  // Reduced camera responsiveness (heavier feel)
        REG(48) = 100;  // Modified physics parameter
    }

    // Load the 17-parameter array for the selected boot type
    bootRegs = sBootData[currentBoots];
    
    // Apply all movement parameters from the boot data
    REG(19) = bootRegs[0];           // Basic movement multiplier
    REG(30) = bootRegs[1];           // Animation timing constant
    REG(32) = bootRegs[2];           // Turn/rotation speed
    REG(34) = bootRegs[3];           // Jump distance modifier
    REG(35) = bootRegs[4];           // Walking animation speed
    REG(36) = bootRegs[5];           // Running transition speed
    REG(37) = bootRegs[6];           // Special movement parameter
    REG(38) = bootRegs[7];           // Additional animation timing
    R_DECELERATE_RATE = bootRegs[8]; // Stopping deceleration rate
    R_RUN_SPEED_LIMIT = bootRegs[9]; // Maximum running speed
    REG(68) = bootRegs[10];          // Gravity modifier
    REG(69) = bootRegs[11];          // Ground friction/traction
    IREG(66) = bootRegs[12];         // Advanced physics parameter 1
    IREG(67) = bootRegs[13];         // Advanced physics parameter 2
    IREG(68) = bootRegs[14];         // Advanced physics parameter 3
    IREG(69) = bootRegs[15];         // Advanced physics parameter 4
    MREG(95) = bootRegs[16];         // Miscellaneous timing parameter

    // Override speed limit for indoor areas to prevent fast movement in tight spaces
    // REMOVED: This was preventing child Link speed modifications from working
    // if (play->roomCtx.curRoom.type == ROOM_TYPE_INDOORS) {
    //     R_RUN_SPEED_LIMIT = 500; // Reduced speed limit for indoor areas
    // }
}

/**
 * Player Blocking Cutscene Mode Check
 * 
 * Determines if the player is in a state that should block normal gameplay actions.
 * This includes cutscenes, death states, magic casting, and other special modes.
 * Used throughout the game to prevent player input during important sequences.
 * 
 * Blocking States:
 * - PLAYER_STATE1_DEAD: Link has died
 * - PLAYER_STATE1_29: Special state flag  
 * - csAction != NONE: Currently in a cutscene action
 * - Transition starting: Scene/room transition beginning
 * - PLAYER_STATE1_0: Special blocking state
 * - PLAYER_STATE3_FLYING_WITH_HOOKSHOT: Flying with hookshot
 * - Active magic spell: Currently casting a magic spell
 * 
 * @param play Current PlayState context
 * @param this Player instance  
 * @return true if player actions should be blocked, false otherwise
 */
int Player_InBlockingCsMode(PlayState* play, Player* this) {
    return (this->stateFlags1 & (PLAYER_STATE1_DEAD | PLAYER_STATE1_29)) || 
           (this->csAction != PLAYER_CSACTION_NONE) ||
           (play->transitionTrigger == TRANS_TRIGGER_START) || 
           (this->stateFlags1 & PLAYER_STATE1_0) ||
           (this->stateFlags3 & PLAYER_STATE3_FLYING_WITH_HOOKSHOT) ||
           ((gSaveContext.magicState != MAGIC_STATE_IDLE) && 
            (Player_ActionToMagicSpell(this, this->itemAction) >= 0));
}

/**
 * Player Cutscene Mode Check
 * 
 * Extended cutscene check that includes blocking mode plus additional
 * first-person view state. Used for more comprehensive input blocking.
 * 
 * @param play Current PlayState context
 * @return true if player is in any cutscene mode, false otherwise
 */
int Player_InCsMode(PlayState* play) {
    Player* this = GET_PLAYER(play);

    return Player_InBlockingCsMode(play, this) || (this->unk_6AD == 4);
}

/**
 * Checks if Player is currently locked onto a hostile actor.
 * `PLAYER_STATE1_HOSTILE_LOCK_ON` controls Player's "battle" response to hostile actors.
 *
 * Note that within Player, `Player_UpdateHostileLockOn` exists, which updates the flag and also returns the check.
 * Player can use this function instead if the flag should be checked, but not updated.
 */
s32 Player_CheckHostileLockOn(Player* this) {
    return (this->stateFlags1 & PLAYER_STATE1_HOSTILE_LOCK_ON);
}

int Player_IsChildWithHylianShield(Player* this) {
    return gSaveContext.save.linkAge != LINK_AGE_ADULT && (this->currentShield == PLAYER_SHIELD_HYLIAN);
}

s32 Player_ActionToModelGroup(Player* this, s32 itemAction) {
    s32 modelGroup = sActionModelGroups[itemAction];

    if ((modelGroup == PLAYER_MODELGROUP_SWORD_AND_SHIELD) && Player_IsChildWithHylianShield(this)) {
        // child, using kokiri sword with hylian shield equipped
        return PLAYER_MODELGROUP_CHILD_HYLIAN_SHIELD;
    } else {
        return modelGroup;
    }
}

void Player_SetModelsForHoldingShield(Player* this) {
    if ((this->stateFlags1 & PLAYER_STATE1_SHIELDING) &&
        ((this->itemAction < 0) || (this->itemAction == this->heldItemAction))) {
        if (!Player_HoldsTwoHandedWeapon(this) && !Player_IsChildWithHylianShield(this)) {
            this->rightHandType = PLAYER_MODELTYPE_RH_SHIELD;
            this->rightHandDLists =
                sPlayerDListGroups[PLAYER_MODELTYPE_RH_SHIELD] + ((void)0, gSaveContext.save.linkAge);
            if (this->sheathType == PLAYER_MODELTYPE_SHEATH_18) {
                this->sheathType = PLAYER_MODELTYPE_SHEATH_16;
            } else if (this->sheathType == PLAYER_MODELTYPE_SHEATH_19) {
                this->sheathType = PLAYER_MODELTYPE_SHEATH_17;
            }
            this->sheathDLists = sPlayerDListGroups[this->sheathType] + ((void)0, gSaveContext.save.linkAge);
            this->modelAnimType = PLAYER_ANIMTYPE_2;
            this->itemAction = -1;
        }
    }
}

void Player_SetModels(Player* this, s32 modelGroup) {
    this->leftHandType = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_LEFT_HAND];
    this->rightHandType = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_RIGHT_HAND];
    this->sheathType = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_SHEATH];

    this->leftHandDLists = sPlayerDListGroups[gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_LEFT_HAND]] +
                           ((void)0, gSaveContext.save.linkAge);
    this->rightHandDLists = sPlayerDListGroups[gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_RIGHT_HAND]] +
                            ((void)0, gSaveContext.save.linkAge);
    this->sheathDLists = sPlayerDListGroups[gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_SHEATH]] +
                         ((void)0, gSaveContext.save.linkAge);
    this->waistDLists = sPlayerDListGroups[gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_WAIST]] +
                        ((void)0, gSaveContext.save.linkAge);

    Player_SetModelsForHoldingShield(this);
}

void Player_SetModelGroup(Player* this, s32 modelGroup) {
    this->modelGroup = modelGroup;

    if (modelGroup == PLAYER_MODELGROUP_CHILD_HYLIAN_SHIELD) {
        this->modelAnimType = PLAYER_ANIMTYPE_0;
    } else {
        this->modelAnimType = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_ANIM];
    }

    if ((this->modelAnimType < PLAYER_ANIMTYPE_3) && (this->currentShield == PLAYER_SHIELD_NONE)) {
        this->modelAnimType = PLAYER_ANIMTYPE_0;
    }

    Player_SetModels(this, modelGroup);
}

void func_8008EC70(Player* this) {
    this->itemAction = this->heldItemAction;
    Player_SetModelGroup(this, Player_ActionToModelGroup(this, this->heldItemAction));
    this->unk_6AD = 0;
}

void Player_SetEquipmentData(PlayState* play, Player* this) {
    if (this->csAction != PLAYER_CSACTION_86) {
        this->currentShield = SHIELD_EQUIP_TO_PLAYER(CUR_EQUIP_VALUE(EQUIP_TYPE_SHIELD));
        this->currentTunic = TUNIC_EQUIP_TO_PLAYER(CUR_EQUIP_VALUE(EQUIP_TYPE_TUNIC));
        this->currentBoots = BOOTS_EQUIP_TO_PLAYER(CUR_EQUIP_VALUE(EQUIP_TYPE_BOOTS));
        this->currentSwordItemId = B_BTN_ITEM;
        Player_SetModelGroup(this, Player_ActionToModelGroup(this, this->heldItemAction));
        Player_SetBootData(play, this);
    }
}

void Player_UpdateBottleHeld(PlayState* play, Player* this, s32 item, s32 itemAction) {
    Inventory_UpdateBottleItem(play, item, this->heldItemButton);

    if (item != ITEM_BOTTLE_EMPTY) {
        this->heldItemId = item;
        this->heldItemAction = itemAction;
    }

    this->itemAction = itemAction;
}

void Player_ReleaseLockOn(Player* this) {
    this->focusActor = NULL;
    this->stateFlags2 &= ~PLAYER_STATE2_LOCK_ON_WITH_SWITCH;
}

/**
 * This function aims to clear Z-Target related state when it isn't in use.
 * It also handles setting a specific free fall related state that is interntwined with Z-Targeting.
 * TODO: Learn more about this and give a name to PLAYER_STATE1_19
 */
void Player_ClearZTargeting(Player* this) {
    if ((this->actor.bgCheckFlags & BGCHECKFLAG_GROUND) ||
        (this->stateFlags1 & (PLAYER_STATE1_21 | PLAYER_STATE1_23 | PLAYER_STATE1_27)) ||
        (!(this->stateFlags1 & (PLAYER_STATE1_18 | PLAYER_STATE1_19)) &&
         ((this->actor.world.pos.y - this->actor.floorHeight) < 100.0f))) {
        this->stateFlags1 &= ~(PLAYER_STATE1_Z_TARGETING | PLAYER_STATE1_FRIENDLY_ACTOR_FOCUS | PLAYER_STATE1_PARALLEL |
                               PLAYER_STATE1_18 | PLAYER_STATE1_19 | PLAYER_STATE1_LOCK_ON_FORCED_TO_RELEASE);
    } else if (!(this->stateFlags1 & (PLAYER_STATE1_18 | PLAYER_STATE1_19 | PLAYER_STATE1_21))) {
        this->stateFlags1 |= PLAYER_STATE1_19;
    }

    Player_ReleaseLockOn(this);
}

/**
 * Sets the "auto lock-on actor" to lock onto an actor without Player's input.
 * This function will first release any existing lock-on or (try to) release parallel.
 *
 * When using Switch Targeting, it is not possible to carry an auto lock-on actor into a normal
 * lock-on when the auto lock-on is finished.
 * This is because the `PLAYER_STATE2_LOCK_ON_WITH_SWITCH` flag is never set with an auto lock-on.
 * With Hold Targeting it is possible to keep the auto lock-on going by keeping the Z button held down.
 *
 * The auto lock-on is considered "friendly" even if the actor is actually hostile. If the auto lock-on is hostile,
 * Player's battle response will not occur (if he is actionable) and the camera behaves differently.
 * When transitioning from auto lock-on to normal lock-on (with Hold Targeting) there will be a noticeable change
 * when it switches from "friendly" mode to "hostile" mode.
 */
void Player_SetAutoLockOnActor(PlayState* play, Actor* actor) {
    Player* this = GET_PLAYER(play);

    Player_ClearZTargeting(this);
    this->focusActor = actor;
    this->autoLockOnActor = actor;
    this->stateFlags1 |= PLAYER_STATE1_FRIENDLY_ACTOR_FOCUS;
    Camera_SetViewParam(Play_GetCamera(play, CAM_ID_MAIN), CAM_VIEW_TARGET, actor);
    Camera_RequestMode(Play_GetCamera(play, CAM_ID_MAIN), CAM_MODE_Z_TARGET_FRIENDLY);
}

s32 func_8008EF30(PlayState* play) {
    Player* this = GET_PLAYER(play);

    return (this->stateFlags1 & PLAYER_STATE1_23);
}

s32 func_8008EF44(PlayState* play, s32 ammo) {
    play->shootingGalleryStatus = ammo + 1;
    return 1;
}

int Player_IsBurningStickInRange(PlayState* play, Vec3f* pos, f32 xzRange, f32 yRange) {
    Player* this = GET_PLAYER(play);
    Vec3f diff;
    s32 pad;

    if ((this->heldItemAction == PLAYER_IA_DEKU_STICK) && (this->unk_860 != 0)) {
        Math_Vec3f_Diff(MELEE_WEAPON_INFO_TIP(&this->meleeWeaponInfo[0]), pos, &diff);
        return ((SQ(diff.x) + SQ(diff.z)) <= SQ(xzRange)) && (0.0f <= diff.y) && (diff.y <= yRange);
    } else {
        return false;
    }
}

s32 Player_GetStrength(void) {
    s32 strengthUpgrade = CUR_UPG_VALUE(UPG_STRENGTH);

    if (LINK_IS_ADULT) {
        return strengthUpgrade;
    } else if (strengthUpgrade != 0) {
        return PLAYER_STR_BRACELET;
    } else {
        return PLAYER_STR_NONE;
    }
}

u8 Player_GetMask(PlayState* play) {
    Player* this = GET_PLAYER(play);

    return this->currentMask;
}

Player* Player_UnsetMask(PlayState* play) {
    Player* this = GET_PLAYER(play);

    this->currentMask = PLAYER_MASK_NONE;

    return this;
}

s32 Player_HasMirrorShieldEquipped(PlayState* play) {
    Player* this = GET_PLAYER(play);

    return (this->currentShield == PLAYER_SHIELD_MIRROR);
}

int Player_HasMirrorShieldSetToDraw(PlayState* play) {
    Player* this = GET_PLAYER(play);

    return (this->rightHandType == PLAYER_MODELTYPE_RH_SHIELD) && (this->currentShield == PLAYER_SHIELD_MIRROR);
}

s32 Player_ActionToMagicSpell(Player* this, s32 itemAction) {
    // Special case for Chronos Magic
    if (itemAction == PLAYER_IA_CHRONOS_MAGIC) {
        return 3; // Use magic spell slot 3 (48 magic cost)
    }
    
    // Original magic spell mapping (starting from what was PLAYER_IA_MAGIC_SPELL_16)
    if (itemAction == PLAYER_IA_FARORES_WIND) {
        return 0;
    } else if (itemAction == PLAYER_IA_NAYRUS_LOVE) {
        return 1;
    } else if (itemAction == PLAYER_IA_DINS_FIRE) {
        return 2;
    } else {
        return -1;
    }
}

int Player_HoldsHookshot(Player* this) {
    return (this->heldItemAction == PLAYER_IA_HOOKSHOT) || (this->heldItemAction == PLAYER_IA_LONGSHOT);
}

int func_8008F128(Player* this) {
    return Player_HoldsHookshot(this) && (this->heldActor == NULL);
}

s32 Player_ActionToMeleeWeapon(s32 itemAction) {
    s32 meleeWeapon = itemAction - PLAYER_IA_FISHING_POLE;

    if ((meleeWeapon > 0) && (meleeWeapon < 6)) {
        return meleeWeapon;
    } else {
        return 0;
    }
}

s32 Player_GetMeleeWeaponHeld(Player* this) {
    return Player_ActionToMeleeWeapon(this->heldItemAction);
}

s32 Player_HoldsTwoHandedWeapon(Player* this) {
    if ((this->heldItemAction >= PLAYER_IA_SWORD_BIGGORON) && (this->heldItemAction <= PLAYER_IA_HAMMER)) {
        return 1;
    } else {
        return 0;
    }
}

int Player_HoldsBrokenKnife(Player* this) {
    return (this->heldItemAction == PLAYER_IA_SWORD_BIGGORON) &&
           (gSaveContext.save.info.playerData.swordHealth <= 0.0f);
}

s32 Player_ActionToBottle(Player* this, s32 itemAction) {
    s32 bottle = itemAction - PLAYER_IA_BOTTLE;

    if ((bottle >= 0) && (bottle < 13)) {
        return bottle;
    } else {
        return -1;
    }
}

s32 Player_GetBottleHeld(Player* this) {
    return Player_ActionToBottle(this, this->heldItemAction);
}

s32 Player_ActionToExplosive(Player* this, s32 itemAction) {
    s32 explosive = itemAction - PLAYER_IA_BOMB;

    if ((explosive >= 0) && (explosive < 2)) {
        return explosive;
    } else {
        return -1;
    }
}

s32 Player_GetExplosiveHeld(Player* this) {
    return Player_ActionToExplosive(this, this->heldItemAction);
}

s32 func_8008F2BC(Player* this, s32 itemAction) {
    s32 sword = 0;

    if (itemAction != PLAYER_IA_SWORD_CS) {
        sword = itemAction - PLAYER_IA_SWORD_MASTER;
        if ((sword < 0) || (sword >= 3)) {
            goto return_neg;
        }
    }

    return sword;

return_neg:
    return -1;
}

s32 Player_GetEnvironmentalHazard(PlayState* play) {
    Player* this = GET_PLAYER(play);
    EnvHazardTextTriggerEntry* triggerEntry;
    s32 envHazard;

    if (play->roomCtx.curRoom.environmentType == ROOM_ENV_HOT) { // Room is hot
        envHazard = PLAYER_ENV_HAZARD_HOTROOM - 1;
    } else if ((this->underwaterTimer > 80) &&
               ((this->currentBoots == PLAYER_BOOTS_IRON) || (this->underwaterTimer >= 300))) {
        envHazard = ((this->currentBoots == PLAYER_BOOTS_IRON) && (this->actor.bgCheckFlags & BGCHECKFLAG_GROUND))
                        ? (PLAYER_ENV_HAZARD_UNDERWATER_FLOOR - 1)
                        : (PLAYER_ENV_HAZARD_UNDERWATER_FREE - 1);
    } else if (this->stateFlags1 & PLAYER_STATE1_27) { // Swimming
        envHazard = PLAYER_ENV_HAZARD_SWIMMING - 1;
    } else {
        return PLAYER_ENV_HAZARD_NONE;
    }

    triggerEntry = &sEnvHazardTextTriggers[envHazard];
    if (!Player_InCsMode(play)) {
        if ((triggerEntry->flag != 0) && !(gSaveContext.envHazardTextTriggerFlags & triggerEntry->flag) &&
            (((envHazard == (PLAYER_ENV_HAZARD_HOTROOM - 1)) && (this->currentTunic != PLAYER_TUNIC_GORON)) ||
             (((envHazard == (PLAYER_ENV_HAZARD_UNDERWATER_FLOOR - 1)) ||
               (envHazard == (PLAYER_ENV_HAZARD_UNDERWATER_FREE - 1))) &&
              (this->currentBoots == PLAYER_BOOTS_IRON) && (this->currentTunic != PLAYER_TUNIC_ZORA)))) {
            Message_StartTextbox(play, triggerEntry->textId, NULL);
            gSaveContext.envHazardTextTriggerFlags |= triggerEntry->flag;
        }
    }

    return envHazard + 1;
}

PlayerFaceIndices sPlayerFaces[PLAYER_FACE_MAX] = {
    // The first 6 faces defined must be default blinking faces. See relevant code in `Player_UpdateCommon`.
    { PLAYER_EYES_OPEN, PLAYER_MOUTH_CLOSED },   // PLAYER_FACE_NEUTRAL
    { PLAYER_EYES_HALF, PLAYER_MOUTH_CLOSED },   // PLAYER_FACE_NEUTRAL_BLINKING_HALF
    { PLAYER_EYES_CLOSED, PLAYER_MOUTH_CLOSED }, // PLAYER_FACE_NEUTRAL_BLINKING_CLOSED

    // This duplicate set of blinking faces is defined because Player will choose between the first and second set
    // based on gameplayFrames. See relevant code in `Player_UpdateCommon`.
    // This, in theory, allows for psuedo-random variance in the faces used. But in practice, duplicate faces are used.
    { PLAYER_EYES_OPEN, PLAYER_MOUTH_CLOSED },   // PLAYER_FACE_NEUTRAL_2
    { PLAYER_EYES_HALF, PLAYER_MOUTH_CLOSED },   // PLAYER_FACE_NEUTRAL_BLINKING_HALF_2
    { PLAYER_EYES_CLOSED, PLAYER_MOUTH_CLOSED }, // PLAYER_FACE_NEUTRAL_BLINKING_CLOSED_2

    // The rest of these faces go unused. Face data encoded within animations handles all other faces.
    { PLAYER_EYES_LEFT, PLAYER_MOUTH_CLOSED },  // PLAYER_FACE_LOOK_LEFT
    { PLAYER_EYES_WIDE, PLAYER_MOUTH_HALF },    // PLAYER_FACE_SURPRISED
    { PLAYER_EYES_WINCING, PLAYER_MOUTH_OPEN }, // PLAYER_FACE_HURT
    { PLAYER_EYES_OPEN, PLAYER_MOUTH_OPEN },    // PLAYER_FACE_GASP
    { PLAYER_EYES_RIGHT, PLAYER_MOUTH_CLOSED }, // PLAYER_FACE_LOOK_RIGHT
    { PLAYER_EYES_LEFT, PLAYER_MOUTH_CLOSED },  // PLAYER_FACE_LOOK_LEFT_2
    { PLAYER_EYES_CLOSED, PLAYER_MOUTH_OPEN },  // PLAYER_FACE_EYES_CLOSED_MOUTH_OPEN
    { PLAYER_EYES_HALF, PLAYER_MOUTH_HALF },    // PLAYER_FACE_OPENING
    { PLAYER_EYES_OPEN, PLAYER_MOUTH_OPEN },    // PLAYER_FACE_EYES_AND_MOUTH_OPEN
    { PLAYER_EYES_OPEN, PLAYER_MOUTH_CLOSED },  // PLAYER_FACE_NEUTRAL_3
};

/**
 * Link's eyes and mouth textures are placed at the exact same place in adult and child Link's respective object files.
 * This allows the array to only contain the symbols for one file and have it apply to both. This is a problem for
 * shiftability, and changes will need to be made in the code to account for this in a modding scenario. The symbols
 * from adult Link's object are used here.
 */
#ifndef AVOID_UB
void* sEyeTextures[PLAYER_EYES_MAX] = {
    gLinkAdultEyesOpenTex,    // PLAYER_EYES_OPEN
    gLinkAdultEyesHalfTex,    // PLAYER_EYES_HALF
    gLinkAdultEyesClosedfTex, // PLAYER_EYES_CLOSED
    gLinkAdultEyesRightTex,   // PLAYER_EYES_RIGHT
    gLinkAdultEyesLeftTex,    // PLAYER_EYES_LEFT
    gLinkAdultEyesWideTex,    // PLAYER_EYES_WIDE
    gLinkAdultEyesDownTex,    // PLAYER_EYES_DOWN
    gLinkAdultEyesWincingTex, // PLAYER_EYES_WINCING
};

void* sMouthTextures[PLAYER_MOUTH_MAX] = {
    gLinkAdultMouthClosedTex, // PLAYER_MOUTH_CLOSED
    gLinkAdultMouthHalfTex,   // PLAYER_MOUTH_HALF
    gLinkAdultMouthOpenTex,   // PLAYER_MOUTH_OPEN
    gLinkAdultMouthSmileTex,  // PLAYER_MOUTH_SMILE
};
#else
// Defining `AVOID_UB` will use a 2D array instead and properly use the child link pointers to allow for shifting.
void* sEyeTextures[][PLAYER_EYES_MAX] = {
    {
        gLinkAdultEyesOpenTex,    // PLAYER_EYES_OPEN
        gLinkAdultEyesHalfTex,    // PLAYER_EYES_HALF
        gLinkAdultEyesClosedfTex, // PLAYER_EYES_CLOSED
        gLinkAdultEyesRightTex,   // PLAYER_EYES_RIGHT
        gLinkAdultEyesLeftTex,    // PLAYER_EYES_LEFT
        gLinkAdultEyesWideTex,    // PLAYER_EYES_WIDE
        gLinkAdultEyesDownTex,    // PLAYER_EYES_DOWN
        gLinkAdultEyesWincingTex, // PLAYER_EYES_WINCING
    },
    {
        gLinkChildEyesOpenTex,    // PLAYER_EYES_OPEN
        gLinkChildEyesHalfTex,    // PLAYER_EYES_HALF
        gLinkChildEyesClosedfTex, // PLAYER_EYES_CLOSED
        /*
        Note `PLAYER_EYES_RIGHT` corresponds to the "left" eyes texture, and vice-versa with the "right" eyes textures.
        This is because on the textures Link appears to look left/right as if facing outwards the screen,
        but the image is mirrored by the child Link model's UVs, reversing the direction actually looked in,
        which results in-game in the correct eyes direction.
        */
        gLinkChildEyesLeftTex,    // PLAYER_EYES_RIGHT
        gLinkChildEyesRightTex,   // PLAYER_EYES_LEFT
        gLinkChildEyesWideTex,    // PLAYER_EYES_WIDE
        gLinkChildEyesDownTex,    // PLAYER_EYES_DOWN
        gLinkChildEyesWincingTex, // PLAYER_EYES_WINCING
    },
};

void* sMouthTextures[][PLAYER_MOUTH_MAX] = {
    {
        gLinkAdultMouthClosedTex, // PLAYER_MOUTH_CLOSED
        gLinkAdultMouthHalfTex,   // PLAYER_MOUTH_HALF
        gLinkAdultMouthOpenTex,   // PLAYER_MOUTH_OPEN
        gLinkAdultMouthSmileTex,  // PLAYER_MOUTH_SMILE
    },
    {
        gLinkChildMouthClosedTex, // PLAYER_MOUTH_CLOSED
        gLinkChildMouthHalfTex,   // PLAYER_MOUTH_HALF
        gLinkChildMouthOpenTex,   // PLAYER_MOUTH_OPEN
        gLinkChildMouthSmileTex,  // PLAYER_MOUTH_SMILE
    },
};
#endif

void Player_DrawImpl(PlayState* play, void** skeleton, Vec3s* jointTable, s32 dListCount, s32 lod, s32 tunic, s32 boots,
                     s32 face, OverrideLimbDrawOpa overrideLimbDraw, PostLimbDrawOpa postLimbDraw, void* data) {
    Color_RGB8* color;
    s32 eyesIndex;
    s32 mouthIndex;

    // Player's animation data includes eyes and mouth indices for which texture to use on a given frame.
    // Despite being accessed as "the x component of the 22nd limb", the eyes and mouth indices are stored in 2
    // additional bytes tacked onto the end of the limb rotation data for a given animation frame.
    eyesIndex = (jointTable[22].x & 0xF) - 1;
    mouthIndex = (jointTable[22].x >> 4) - 1;

    OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 1721);

    // If the eyes index provided by the animation is negative, use the value provided by the `face` argument instead
    if (eyesIndex < 0) {
        eyesIndex = sPlayerFaces[face].eyeIndex;
    }

#ifndef AVOID_UB
    gSPSegment(POLY_OPA_DISP++, 0x08, SEGMENTED_TO_VIRTUAL(sEyeTextures[eyesIndex]));
#else
    gSPSegment(POLY_OPA_DISP++, 0x08, SEGMENTED_TO_VIRTUAL(sEyeTextures[gSaveContext.save.linkAge][eyesIndex]));
#endif

    // If the mouth index provided by the animation is negative, use the value provided by the `face` argument instead
    if (mouthIndex < 0) {
        mouthIndex = sPlayerFaces[face].mouthIndex;
    }

#ifndef AVOID_UB
    gSPSegment(POLY_OPA_DISP++, 0x09, SEGMENTED_TO_VIRTUAL(sMouthTextures[mouthIndex]));
#else
    gSPSegment(POLY_OPA_DISP++, 0x09, SEGMENTED_TO_VIRTUAL(sMouthTextures[gSaveContext.save.linkAge][mouthIndex]));
#endif

    color = &sTunicColors[tunic];
    gDPSetEnvColor(POLY_OPA_DISP++, color->r, color->g, color->b, 0);

    sDListsLodOffset = lod * 2;

    SkelAnime_DrawFlexLod(play, skeleton, jointTable, dListCount, overrideLimbDraw, postLimbDraw, data, lod);

    if ((overrideLimbDraw != Player_OverrideLimbDrawGameplayFirstPerson) &&
        (overrideLimbDraw != Player_OverrideLimbDrawGameplayCrawling) &&
        (gSaveContext.gameMode != GAMEMODE_END_CREDITS)) {
        if (LINK_IS_ADULT) {
            s32 strengthUpgrade = CUR_UPG_VALUE(UPG_STRENGTH);

            if (strengthUpgrade >= 2) { // silver or gold gauntlets
                gDPPipeSync(POLY_OPA_DISP++);

                color = &sGauntletColors[strengthUpgrade - 2];
                gDPSetEnvColor(POLY_OPA_DISP++, color->r, color->g, color->b, 0);

                gSPDisplayList(POLY_OPA_DISP++, gLinkAdultLeftGauntletPlate1DL);
                gSPDisplayList(POLY_OPA_DISP++, gLinkAdultRightGauntletPlate1DL);
                gSPDisplayList(POLY_OPA_DISP++, (sLeftHandType == PLAYER_MODELTYPE_LH_OPEN)
                                                    ? gLinkAdultLeftGauntletPlate2DL
                                                    : gLinkAdultLeftGauntletPlate3DL);
                gSPDisplayList(POLY_OPA_DISP++, (sRightHandType == PLAYER_MODELTYPE_RH_OPEN)
                                                    ? gLinkAdultRightGauntletPlate2DL
                                                    : gLinkAdultRightGauntletPlate3DL);
            }

            if (boots != PLAYER_BOOTS_KOKIRI) {
                Gfx** bootDLists = sBootDListGroups[boots - PLAYER_BOOTS_IRON];

                gSPDisplayList(POLY_OPA_DISP++, bootDLists[0]);
                gSPDisplayList(POLY_OPA_DISP++, bootDLists[1]);
            }
        } else {
            if (Player_GetStrength() > PLAYER_STR_NONE) {
                gSPDisplayList(POLY_OPA_DISP++, gLinkChildGoronBraceletDL);
            }
        }
    }

    CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 1803);
}

Vec3f sZeroVec = { 0.0f, 0.0f, 0.0f };

Vec3f D_80126038[] = {
    { 1304.0f, 0.0f, 0.0f },
    { 695.0f, 0.0f, 0.0f },
};

f32 D_80126050[] = { 1265.0f, 826.0f };
f32 D_80126058[] = { SQ(13.04f), SQ(6.95f) };
f32 D_80126060[] = { 10.019104f, -19.925102f };
f32 D_80126068[] = { 5.0f, 3.0f };

Vec3f D_80126070 = { 0.0f, -300.0f, 0.0f };

void func_8008F87C(PlayState* play, Player* this, SkelAnime* skelAnime, Vec3f* pos, Vec3s* rot, s32 thighLimbIndex,
                   s32 shinLimbIndex, s32 footLimbIndex) {
    Vec3f spA4;
    Vec3f sp98;
    Vec3f footprintPos;
    CollisionPoly* sp88;
    s32 sp84;
    f32 sp80;
    f32 sp7C;
    f32 sp78;
    f32 sp74;
    f32 sp70;
    f32 sp6C;
    f32 sp68;
    f32 sp64;
    f32 sp60;
    f32 sp5C;
    f32 sp58;
    f32 sp54;
    f32 sp50;
    s16 temp1;
    s16 temp2;
    s32 temp3;

    if ((this->actor.scale.y >= 0.0f) && !(this->stateFlags1 & PLAYER_STATE1_DEAD) &&
        (Player_ActionToMagicSpell(this, this->itemAction) < 0)) {
        s32 pad;

        sp7C = D_80126058[(void)0, gSaveContext.save.linkAge];
        sp78 = D_80126060[(void)0, gSaveContext.save.linkAge];
        sp74 = D_80126068[(void)0, gSaveContext.save.linkAge] - this->unk_6C4;

        Matrix_Push();
        Matrix_TranslateRotateZYX(pos, rot);
        Matrix_MultVec3f(&sZeroVec, &spA4);
        Matrix_TranslateRotateZYX(&D_80126038[(void)0, gSaveContext.save.linkAge],
                                  &skelAnime->jointTable[shinLimbIndex]);
        Matrix_Translate(D_80126050[(void)0, gSaveContext.save.linkAge], 0.0f, 0.0f, MTXMODE_APPLY);
        Matrix_MultVec3f(&sZeroVec, &sp98);
        Matrix_MultVec3f(&D_80126070, &footprintPos);
        Matrix_Pop();

        footprintPos.y += 15.0f;

        sp80 = BgCheck_EntityRaycastDown4(&play->colCtx, &sp88, &sp84, &this->actor, &footprintPos) + sp74;

        if (sp98.y < sp80) {
            sp70 = sp98.x - spA4.x;
            sp6C = sp98.y - spA4.y;
            sp68 = sp98.z - spA4.z;

            sp64 = sqrtf(SQ(sp70) + SQ(sp6C) + SQ(sp68));
            sp60 = (SQ(sp64) + sp78) / (2.0f * sp64);

            sp58 = sp7C - SQ(sp60);
            sp58 = (sp7C < SQ(sp60)) ? 0.0f : sqrtf(sp58);

            sp54 = Math_FAtan2F(sp58, sp60);

            sp6C = sp80 - spA4.y;

            sp64 = sqrtf(SQ(sp70) + SQ(sp6C) + SQ(sp68));
            sp60 = (SQ(sp64) + sp78) / (2.0f * sp64);
            sp5C = sp64 - sp60;

            sp58 = sp7C - SQ(sp60);
            sp58 = (sp7C < SQ(sp60)) ? 0.0f : sqrtf(sp58);

            sp50 = Math_FAtan2F(sp58, sp60);

            temp1 = RAD_TO_BINANG(M_PI - (Math_FAtan2F(sp5C, sp58) + ((M_PI / 2) - sp50)));
            temp1 -= skelAnime->jointTable[shinLimbIndex].z;

            if ((s16)(ABS(skelAnime->jointTable[shinLimbIndex].x) + ABS(skelAnime->jointTable[shinLimbIndex].y)) < 0) {
                temp1 += 0x8000;
            }

            temp2 = RAD_TO_BINANG(sp50 - sp54);
            rot->z -= temp2;

            skelAnime->jointTable[thighLimbIndex].z = skelAnime->jointTable[thighLimbIndex].z - temp2;
            skelAnime->jointTable[shinLimbIndex].z = skelAnime->jointTable[shinLimbIndex].z + temp1;
            skelAnime->jointTable[footLimbIndex].z = skelAnime->jointTable[footLimbIndex].z + temp2 - temp1;

            temp3 = SurfaceType_GetFloorType(&play->colCtx, sp88, sp84);

            if ((temp3 >= FLOOR_TYPE_2) && (temp3 <= FLOOR_TYPE_3) && !func_80042108(&play->colCtx, sp88, sp84)) {
                footprintPos.y = sp80;
                EffectSsGFire_Spawn(play, &footprintPos);
            }
        }
    }
}

s32 Player_OverrideLimbDrawGameplayCommon(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot,
                                          void* thisx) {
    Player* this = (Player*)thisx;

    if (limbIndex == PLAYER_LIMB_ROOT) {
        sLeftHandType = this->leftHandType;
        sRightHandType = this->rightHandType;

        // `sCurBodyPartPos` is incremented before each usage, so it starts at index -1.
        // What determines if a limb corresponds to a body part is whether or not it has a non-NULL `dList`.
        // Note: The increment would not be done for the root limb, even if it had a non-NULL `dList`.
        //       So if the root limb had a non-NULL `dList` (which is not the case in vanilla),
        //       an out-of-bounds write to `bodyPartsPos` would occur.
        sCurBodyPartPos = &this->bodyPartsPos[0] - 1;

        if (!LINK_IS_ADULT) {
            if (!(this->skelAnime.movementFlags & ANIM_FLAG_DISABLE_CHILD_ROOT_ADJUSTMENT) ||
                (this->skelAnime.movementFlags & ANIM_FLAG_UPDATE_XZ)) {
                pos->x *= 0.64f;
                pos->z *= 0.64f;
            }

            if (!(this->skelAnime.movementFlags & ANIM_FLAG_DISABLE_CHILD_ROOT_ADJUSTMENT) ||
                (this->skelAnime.movementFlags & ANIM_FLAG_UPDATE_Y)) {
                pos->y *= 0.64f;
            }
        }

        pos->y -= this->unk_6C4;

        if (this->unk_6C2 != 0) {
            Matrix_Translate(pos->x, ((Math_CosS(this->unk_6C2) - 1.0f) * 200.0f) + pos->y, pos->z, MTXMODE_APPLY);
            Matrix_RotateX(BINANG_TO_RAD(this->unk_6C2), MTXMODE_APPLY);
            Matrix_RotateZYX(rot->x, rot->y, rot->z, MTXMODE_APPLY);
            pos->x = pos->y = pos->z = 0.0f;
            rot->x = rot->y = rot->z = 0;
        }
    } else {
        if (*dList != NULL) {
            sCurBodyPartPos++;
        }

        if (limbIndex == PLAYER_LIMB_HEAD) {
            rot->x += this->headLimbRot.z;
            rot->y -= this->headLimbRot.y;
            rot->z += this->headLimbRot.x;
        } else if (limbIndex == PLAYER_LIMB_UPPER) {
            if (this->upperLimbYawSecondary != 0) {
                Matrix_RotateZ(BINANG_TO_RAD(0x44C), MTXMODE_APPLY);
                Matrix_RotateY(BINANG_TO_RAD(this->upperLimbYawSecondary), MTXMODE_APPLY);
            }
            if (this->upperLimbRot.y != 0) {
                Matrix_RotateY(BINANG_TO_RAD(this->upperLimbRot.y), MTXMODE_APPLY);
            }
            if (this->upperLimbRot.x != 0) {
                Matrix_RotateX(BINANG_TO_RAD(this->upperLimbRot.x), MTXMODE_APPLY);
            }
            if (this->upperLimbRot.z != 0) {
                Matrix_RotateZ(BINANG_TO_RAD(this->upperLimbRot.z), MTXMODE_APPLY);
            }
        } else if (limbIndex == PLAYER_LIMB_L_THIGH) {
            s32 pad;

            func_8008F87C(play, this, &this->skelAnime, pos, rot, PLAYER_LIMB_L_THIGH, PLAYER_LIMB_L_SHIN,
                          PLAYER_LIMB_L_FOOT);
        } else if (limbIndex == PLAYER_LIMB_R_THIGH) {
            s32 pad;

            func_8008F87C(play, this, &this->skelAnime, pos, rot, PLAYER_LIMB_R_THIGH, PLAYER_LIMB_R_SHIN,
                          PLAYER_LIMB_R_FOOT);
        } else {
            return false;
        }
    }

    return false;
}

s32 Player_OverrideLimbDrawGameplayDefault(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot,
                                           void* thisx) {
    Player* this = (Player*)thisx;

    if (!Player_OverrideLimbDrawGameplayCommon(play, limbIndex, dList, pos, rot, thisx)) {
        if (limbIndex == PLAYER_LIMB_L_HAND) {
            Gfx** dLists = this->leftHandDLists;

            if ((sLeftHandType == PLAYER_MODELTYPE_LH_BGS) && (gSaveContext.save.info.playerData.swordHealth <= 0.0f)) {
                dLists += 4;
            } else if ((sLeftHandType == PLAYER_MODELTYPE_LH_BOOMERANG) &&
                       (this->stateFlags1 & PLAYER_STATE1_BOOMERANG_THROWN)) {
                dLists = gPlayerLeftHandOpenDLs + gSaveContext.save.linkAge;
                sLeftHandType = PLAYER_MODELTYPE_LH_OPEN;
            } else if ((this->leftHandType == PLAYER_MODELTYPE_LH_OPEN) && (this->actor.speed > 2.0f) &&
                       !(this->stateFlags1 & PLAYER_STATE1_27)) {
                dLists = gPlayerLeftHandClosedDLs + gSaveContext.save.linkAge;
                sLeftHandType = PLAYER_MODELTYPE_LH_CLOSED;
            }

            *dList = *(dLists + sDListsLodOffset);
        } else if (limbIndex == PLAYER_LIMB_R_HAND) {
            Gfx** dLists = this->rightHandDLists;

            if (sRightHandType == PLAYER_MODELTYPE_RH_SHIELD) {
                dLists += this->currentShield * 4;
            } else if ((this->rightHandType == PLAYER_MODELTYPE_RH_OPEN) && (this->actor.speed > 2.0f) &&
                       !(this->stateFlags1 & PLAYER_STATE1_27)) {
                dLists = sPlayerRightHandClosedDLs + gSaveContext.save.linkAge;
                sRightHandType = PLAYER_MODELTYPE_RH_CLOSED;
            }

            *dList = *(dLists + sDListsLodOffset);
        } else if (limbIndex == PLAYER_LIMB_SHEATH) {
            Gfx** dLists = this->sheathDLists;

            if ((this->sheathType == PLAYER_MODELTYPE_SHEATH_18) || (this->sheathType == PLAYER_MODELTYPE_SHEATH_19)) {
                dLists += this->currentShield * 4;
                if (!LINK_IS_ADULT && (this->currentShield < PLAYER_SHIELD_HYLIAN) &&
                    (gSaveContext.save.info.equips.buttonItems[0] != ITEM_SWORD_KOKIRI)) {
                    dLists += PLAYER_SHIELD_MAX * 4;
                }
            } else if (!LINK_IS_ADULT &&
                       ((this->sheathType == PLAYER_MODELTYPE_SHEATH_16) ||
                        (this->sheathType == PLAYER_MODELTYPE_SHEATH_17)) &&
                       (gSaveContext.save.info.equips.buttonItems[0] != ITEM_SWORD_KOKIRI)) {
                dLists = D_80125D28 + PLAYER_SHIELD_MAX * 4;
            }

            *dList = *(dLists + sDListsLodOffset);
        } else if (limbIndex == PLAYER_LIMB_WAIST) {
            *dList = *(this->waistDLists + sDListsLodOffset);
        }
    }

    return false;
}

s32 Player_OverrideLimbDrawGameplayFirstPerson(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot,
                                               void* thisx) {
    Player* this = (Player*)thisx;

    if (!Player_OverrideLimbDrawGameplayCommon(play, limbIndex, dList, pos, rot, thisx)) {
        if (this->unk_6AD != 2) {
            *dList = NULL;
        } else if (limbIndex == PLAYER_LIMB_L_FOREARM) {
            *dList = sFirstPersonLeftForearmDLs[(void)0, gSaveContext.save.linkAge];
        } else if (limbIndex == PLAYER_LIMB_L_HAND) {
            *dList = sFirstPersonLeftHandDLs[(void)0, gSaveContext.save.linkAge];
        } else if (limbIndex == PLAYER_LIMB_R_SHOULDER) {
            *dList = sFirstPersonRightShoulderDLs[(void)0, gSaveContext.save.linkAge];
        } else if (limbIndex == PLAYER_LIMB_R_FOREARM) {
            *dList = sFirstPersonForearmDLs[(void)0, gSaveContext.save.linkAge];
        } else if (limbIndex == PLAYER_LIMB_R_HAND) {
            *dList = Player_HoldsHookshot(this)
                         ? gLinkAdultRightHandHoldingHookshotFarDL
                         : sFirstPersonRightHandHoldingWeaponDLs[(void)0, gSaveContext.save.linkAge];
        } else {
            *dList = NULL;
        }
    }

    return false;
}

s32 Player_OverrideLimbDrawGameplayCrawling(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot,
                                            void* thisx) {
    if (!Player_OverrideLimbDrawGameplayCommon(play, limbIndex, dList, pos, rot, thisx)) {
        *dList = NULL;
    }

    return false;
}

/**
 * Handles colliders for player weapons, by creating a quad collider each frame between the weapon's previous position
 * and its new position.
 * This position is given as a pair, `newPosA` and `newPosB`, representing two ends of a line that can be thought of as
 * the active part of the weapon. Note that this line is not necessarily following the weapon's shape: for example
 * arrows use a line perpendicular to the shaft.
 * @param collider The quad collider to use for the weapon.
 * @param newPosA One end of the line. For melee weapons, this is the tip.
 * @param newPosB One end of the line. For melee weapons, this is the base.
 * @return true if the weapon is active at a new position.
 */
u8 Player_UpdateWeaponInfo(PlayState* play, ColliderQuad* collider, WeaponInfo* weaponInfo, Vec3f* newPosA,
                           Vec3f* newPosB) {
    if (!weaponInfo->active) {
        if (collider != NULL) {
            Collider_ResetQuadAT(play, &collider->base);
        }
        Math_Vec3f_Copy(&weaponInfo->posA, newPosA);
        Math_Vec3f_Copy(&weaponInfo->posB, newPosB);
        weaponInfo->active = true;
        return true;
    } else if ((weaponInfo->posA.x == newPosA->x) && (weaponInfo->posA.y == newPosA->y) &&
               (weaponInfo->posA.z == newPosA->z) && (weaponInfo->posB.x == newPosB->x) &&
               (weaponInfo->posB.y == newPosB->y) && (weaponInfo->posB.z == newPosB->z)) {
        if (collider != NULL) {
            Collider_ResetQuadAT(play, &collider->base);
        }
        return false;
    } else {
        if (collider != NULL) {
            Collider_SetQuadVertices(collider, newPosB, newPosA, &weaponInfo->posB, &weaponInfo->posA);
            CollisionCheck_SetAT(play, &play->colChkCtx, &collider->base);
        }
        Math_Vec3f_Copy(&weaponInfo->posB, newPosB);
        Math_Vec3f_Copy(&weaponInfo->posA, newPosA);
        weaponInfo->active = true;
        return true;
    }
}

void Player_UpdateShieldCollider(PlayState* play, Player* this, ColliderQuad* collider, Vec3f* quadSrc) {
    static u8 shieldColMaterials[PLAYER_SHIELD_MAX] = {
        COL_MATERIAL_METAL,
        COL_MATERIAL_WOOD,
        COL_MATERIAL_METAL,
        COL_MATERIAL_METAL,
    };

    if (this->stateFlags1 & PLAYER_STATE1_SHIELDING) {
        Vec3f quadDest[4];

        this->shieldQuad.base.colMaterial = shieldColMaterials[this->currentShield];

        Matrix_MultVec3f(&quadSrc[0], &quadDest[0]);
        Matrix_MultVec3f(&quadSrc[1], &quadDest[1]);
        Matrix_MultVec3f(&quadSrc[2], &quadDest[2]);
        Matrix_MultVec3f(&quadSrc[3], &quadDest[3]);
        Collider_SetQuadVertices(collider, &quadDest[0], &quadDest[1], &quadDest[2], &quadDest[3]);

        CollisionCheck_SetAC(play, &play->colChkCtx, &collider->base);
        CollisionCheck_SetAT(play, &play->colChkCtx, &collider->base);
    }
}

// Positions for the tip of melee weapons, in the left hand limb's own model space.
Vec3f sMeleeWeaponTipOffsetFromLeftHand0 = { 5000.0f, 400.0f, 0.0f };
Vec3f sMeleeWeaponTipOffsetFromLeftHand1 = { 5000.0f, -400.0f, 1000.0f };
Vec3f sMeleeWeaponTipOffsetFromLeftHand2 = { 5000.0f, 1400.0f, -1000.0f };

// Positions for the base of melee weapons, in the left hand limb's own model space.
Vec3f sMeleeWeaponBaseOffsetFromLeftHand0 = { 0.0f, 400.0f, 0.0f };
Vec3f sMeleeWeaponBaseOffsetFromLeftHand1 = { 0.0f, 1400.0f, -1000.0f };
Vec3f sMeleeWeaponBaseOffsetFromLeftHand2 = { 0.0f, -400.0f, 1000.0f };

void Player_UpdateMeleeWeaponInfo(PlayState* play, Player* this, Vec3f* newTipPositions) {
    Vec3f newBasePositions[3];

    Matrix_MultVec3f(&sMeleeWeaponBaseOffsetFromLeftHand0, &newBasePositions[0]);
    Matrix_MultVec3f(&sMeleeWeaponBaseOffsetFromLeftHand1, &newBasePositions[1]);
    Matrix_MultVec3f(&sMeleeWeaponBaseOffsetFromLeftHand2, &newBasePositions[2]);

    if (Player_UpdateWeaponInfo(play, NULL, &this->meleeWeaponInfo[0], &newTipPositions[0], &newBasePositions[0]) &&
        !(this->stateFlags1 & PLAYER_STATE1_SHIELDING)) {
        EffectBlure_AddVertex(Effect_GetByIndex(this->meleeWeaponEffectIndex), &this->meleeWeaponInfo[0].posA,
                              &this->meleeWeaponInfo[0].posB);
    }

    if ((this->meleeWeaponState > 0) &&
        ((this->meleeWeaponAnimation < PLAYER_MWA_SPIN_ATTACK_1H) || (this->stateFlags2 & PLAYER_STATE2_17))) {
        Player_UpdateWeaponInfo(play, &this->meleeWeaponQuads[0], &this->meleeWeaponInfo[1], &newTipPositions[1],
                                &newBasePositions[1]);
        Player_UpdateWeaponInfo(play, &this->meleeWeaponQuads[1], &this->meleeWeaponInfo[2], &newTipPositions[2],
                                &newBasePositions[2]);
    }
}

void Player_DrawGetItemImpl(PlayState* play, Player* this, Vec3f* refPos, s32 drawIdPlusOne) {
    f32 height = (this->exchangeItemId != EXCH_ITEM_NONE) ? 6.0f : 14.0f;

    OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2401);

    gSegments[6] = OS_K0_TO_PHYSICAL(this->giObjectSegment);

    gSPSegment(POLY_OPA_DISP++, 0x06, this->giObjectSegment);
    gSPSegment(POLY_XLU_DISP++, 0x06, this->giObjectSegment);

    Matrix_Translate(refPos->x + (3.3f * Math_SinS(this->actor.shape.rot.y)), refPos->y + height,
                     refPos->z + ((3.3f + (IREG(90) / 10.0f)) * Math_CosS(this->actor.shape.rot.y)), MTXMODE_NEW);
    Matrix_RotateZYX(0, play->gameplayFrames * 1000, 0, MTXMODE_APPLY);
    Matrix_Scale(0.2f, 0.2f, 0.2f, MTXMODE_APPLY);

    GetItem_Draw(play, drawIdPlusOne - 1);

    CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2421);
}

void Player_DrawGetItem(PlayState* play, Player* this) {
    if (!this->giObjectLoading || osRecvMesg(&this->giObjectLoadQueue, NULL, OS_MESG_NOBLOCK) == 0) {
        this->giObjectLoading = false;
        Player_DrawGetItemImpl(play, this, &sGetItemRefPos, ABS(this->unk_862));
    }
}

void Player_CalcMeleeWeaponTipPositions(Player* this, Vec3f* tipPositions) {
    sMeleeWeaponTipOffsetFromLeftHand1.x = sMeleeWeaponTipOffsetFromLeftHand0.x;

    if (this->unk_845 >= 3) {
        this->unk_845++;
        sMeleeWeaponTipOffsetFromLeftHand1.x *= 1.0f + ((9 - this->unk_845) * 0.1f);
    }

    sMeleeWeaponTipOffsetFromLeftHand1.x += 1200.0f;
    sMeleeWeaponTipOffsetFromLeftHand2.x = sMeleeWeaponTipOffsetFromLeftHand1.x;

    Matrix_MultVec3f(&sMeleeWeaponTipOffsetFromLeftHand0, &tipPositions[0]);
    Matrix_MultVec3f(&sMeleeWeaponTipOffsetFromLeftHand1, &tipPositions[1]);
    Matrix_MultVec3f(&sMeleeWeaponTipOffsetFromLeftHand2, &tipPositions[2]);
}

void Player_DrawHookshotReticle(PlayState* play, Player* this, f32 arg2) {
    static Vec3f D_801260C8 = { -500.0f, -100.0f, 0.0f };
    CollisionPoly* sp9C;
    s32 bgId;
    Vec3f sp8C;
    Vec3f sp80;
    Vec3f sp74;
    Vec3f sp68;
    f32 sp64;
    f32 sp60;

    D_801260C8.z = 0.0f;
    Matrix_MultVec3f(&D_801260C8, &sp8C);
    D_801260C8.z = arg2;
    Matrix_MultVec3f(&D_801260C8, &sp80);

    if (1) {}

    if (BgCheck_AnyLineTest3(&play->colCtx, &sp8C, &sp80, &sp74, &sp9C, 1, 1, 1, 1, &bgId)) {
        OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2572);

        OVERLAY_DISP = Gfx_SetupDL(OVERLAY_DISP, SETUPDL_7);

        SkinMatrix_Vec3fMtxFMultXYZW(&play->viewProjectionMtxF, &sp74, &sp68, &sp64);

        sp60 = (sp64 < 200.0f) ? 0.08f : (sp64 / 200.0f) * 0.08f;

        Matrix_Translate(sp74.x, sp74.y, sp74.z, MTXMODE_NEW);
        Matrix_Scale(sp60, sp60, sp60, MTXMODE_APPLY);

        MATRIX_FINALIZE_AND_LOAD(OVERLAY_DISP++, play->state.gfxCtx, "../z_player_lib.c", 2587);
        gSPSegment(OVERLAY_DISP++, 0x06, play->objectCtx.slots[this->actor.objectSlot].segment);
        gSPDisplayList(OVERLAY_DISP++, gLinkAdultHookshotReticleDL);

        CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2592);
    }
}

// Coordinates of the player focus position, in the head limb's own model space.
Vec3f sPlayerFocusOffsetFromHead = { 1100.0f, -700.0f, 0.0f };

f32 sMeleeWeaponLengths[] = {
    0.0f,    // not a melee weapon
    4000.0f, // Master Sword
    3000.0f, // Kokiri Sword
    5500.0f, // Biggoron's Sword
    0.0f,    // Deku Stick
    2500.0f, // Hammer
};

Gfx* sBottleDLists[] = { gLinkAdultBottleDL, gLinkChildBottleDL };

Color_RGB8 sBottleColors[] = {
    { 255, 255, 255 }, // Empty
    { 80, 80, 255 },   // Fish
    { 255, 100, 255 }, // Fire
    { 0, 0, 255 },     // Bug
    { 255, 0, 255 },   // Poe
    { 255, 0, 255 },   // Big Poe
    { 200, 200, 100 }, // Letter
    { 255, 0, 0 },     // Red Potion
    { 0, 0, 255 },     // Blue Potion
    { 0, 255, 0 },     // Green Potion
    { 255, 255, 255 }, // Milk
    { 255, 255, 255 }, // Half Milk
    { 80, 80, 255 },   // Fairy
};

void Player_PostLimbDrawGameplay(PlayState* play, s32 limbIndex, Gfx** dList, Vec3s* rot, void* thisx) {
    Player* this = (Player*)thisx;

    if (*dList != NULL) {
        Matrix_MultVec3f(&sZeroVec, sCurBodyPartPos);
    }

    if (limbIndex == PLAYER_LIMB_L_HAND) {
        MtxF leftHandMtx;
        Actor* heldActor;

        Math_Vec3f_Copy(&this->leftHandPos, sCurBodyPartPos);

        if (this->itemAction == PLAYER_IA_DEKU_STICK) {
            Vec3f tipPositions[3];

            OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2633);

            if (this->actor.scale.y >= 0.0f) {
                sMeleeWeaponTipOffsetFromLeftHand0.x = this->unk_85C * 5000.0f;
                Player_CalcMeleeWeaponTipPositions(this, tipPositions);
                if (this->meleeWeaponState != 0) {
                    Player_UpdateMeleeWeaponInfo(play, this, tipPositions);
                } else {
                    Math_Vec3f_Copy(MELEE_WEAPON_INFO_TIP(&this->meleeWeaponInfo[0]), &tipPositions[0]);
                }
            }

            Matrix_Translate(-428.26f, 267.2f, -33.82f, MTXMODE_APPLY);
            Matrix_RotateZYX(-0x8000, 0, 0x4000, MTXMODE_APPLY);
            Matrix_Scale(1.0f, this->unk_85C, 1.0f, MTXMODE_APPLY);

            MATRIX_FINALIZE_AND_LOAD(POLY_OPA_DISP++, play->state.gfxCtx, "../z_player_lib.c", 2653);
            gSPDisplayList(POLY_OPA_DISP++, gLinkChildLinkDekuStickDL);

            CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2656);
        } else if ((this->actor.scale.y >= 0.0f) && (this->meleeWeaponState != 0)) {
            Vec3f tipPositions[3];

            if (Player_HoldsBrokenKnife(this)) {
                sMeleeWeaponTipOffsetFromLeftHand0.x = 1500.0f;
            } else {
                sMeleeWeaponTipOffsetFromLeftHand0.x = sMeleeWeaponLengths[Player_GetMeleeWeaponHeld(this)];
            }

            Player_CalcMeleeWeaponTipPositions(this, tipPositions);
            Player_UpdateMeleeWeaponInfo(play, this, tipPositions);
        } else if ((*dList != NULL) && (this->leftHandType == PLAYER_MODELTYPE_LH_BOTTLE)) {
            //! @bug When Player is actively using shield, the `itemAction` value will be set to -1.
            //! If shield is used at the same time a bottle is in hand, `Player_ActionToBottle` will
            //! return -1, which results in an out of bounds access behind the `sBottleColors` array.
            //! A value of -1 happens to access `gLinkChildBottleDL` (0x06018478). The last 3 bytes of
            //! this pointer are read as a color, which results in a dark teal color used for the bottle.
            Color_RGB8* bottleColor = &sBottleColors[Player_ActionToBottle(this, this->itemAction)];

            OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2710);

            MATRIX_FINALIZE_AND_LOAD(POLY_XLU_DISP++, play->state.gfxCtx, "../z_player_lib.c", 2712);
            gDPSetEnvColor(POLY_XLU_DISP++, bottleColor->r, bottleColor->g, bottleColor->b, 0);
            gSPDisplayList(POLY_XLU_DISP++, sBottleDLists[((void)0, gSaveContext.save.linkAge)]);

            CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2717);
        }

        if (this->actor.scale.y >= 0.0f) {
            if (!Player_HoldsHookshot(this) && ((heldActor = this->heldActor) != NULL)) {
                if (this->stateFlags1 & PLAYER_STATE1_9) {
                    static Vec3f D_80126128 = { 398.0f, 1419.0f, 244.0f };

                    Matrix_MultVec3f(&D_80126128, &heldActor->world.pos);
                    Matrix_RotateZYX(0x69E8, -0x5708, 0x458E, MTXMODE_APPLY);
                    Matrix_Get(&leftHandMtx);
                    Matrix_MtxFToYXZRotS(&leftHandMtx, &heldActor->world.rot, 0);
                    heldActor->shape.rot = heldActor->world.rot;
                } else if (this->stateFlags1 & PLAYER_STATE1_CARRYING_ACTOR) {
                    Vec3s leftHandRot;

                    Matrix_Get(&leftHandMtx);
                    Matrix_MtxFToYXZRotS(&leftHandMtx, &leftHandRot, 0);

                    if (heldActor->flags & ACTOR_FLAG_CARRY_X_ROT_INFLUENCE) {
                        heldActor->world.rot.x = heldActor->shape.rot.x = leftHandRot.x - this->unk_3BC.x;
                    } else {
                        heldActor->world.rot.y = heldActor->shape.rot.y = this->actor.shape.rot.y + this->unk_3BC.y;
                    }
                }
            } else {
                Matrix_Get(&this->mf_9E0);
                Matrix_MtxFToYXZRotS(&this->mf_9E0, &this->unk_3BC, 0);
            }
        }
    } else if (limbIndex == PLAYER_LIMB_R_HAND) {
        Actor* heldActor = this->heldActor;

        if (this->rightHandType == PLAYER_MODELTYPE_RH_FF) {
            Matrix_Get(&this->shieldMf);
        } else if ((this->rightHandType == PLAYER_MODELTYPE_RH_BOW_SLINGSHOT) ||
                   (this->rightHandType == PLAYER_MODELTYPE_RH_BOW_SLINGSHOT_2)) {
            static BowSlingshotStringData sBowSlingshotStringData[] = {
                { gLinkAdultBowStringDL, { 0.0f, -360.4f, 0.0f } },        // Bow
                { gLinkChildSlingshotStringDL, { 606.0f, 236.0f, 0.0f } }, // Slingshot
            };
            BowSlingshotStringData* stringData = &sBowSlingshotStringData[gSaveContext.save.linkAge];

            OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2783);

            Matrix_Push();
            Matrix_Translate(stringData->pos.x, stringData->pos.y, stringData->pos.z, MTXMODE_APPLY);

            if ((this->stateFlags1 & PLAYER_STATE1_9) && (this->unk_860 >= 0) && (this->unk_834 <= 10)) {
                Vec3f sp90;
                f32 distXYZ;

                Matrix_MultVec3f(&sZeroVec, &sp90);
                distXYZ = Math_Vec3f_DistXYZ(sCurBodyPartPos, &sp90);

                this->unk_858 = distXYZ - 3.0f;
                if (distXYZ < 3.0f) {
                    this->unk_858 = 0.0f;
                } else {
                    this->unk_858 *= 1.6f;
                    if (this->unk_858 > 1.0f) {
                        this->unk_858 = 1.0f;
                    }
                }

                this->unk_85C = -0.5f;
            }

            Matrix_Scale(1.0f, this->unk_858, 1.0f, MTXMODE_APPLY);

            if (!LINK_IS_ADULT) {
                Matrix_RotateZ(this->unk_858 * -0.2f, MTXMODE_APPLY);
            }

            MATRIX_FINALIZE_AND_LOAD(POLY_XLU_DISP++, play->state.gfxCtx, "../z_player_lib.c", 2804);
            gSPDisplayList(POLY_XLU_DISP++, stringData->dList);

            Matrix_Pop();

            CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 2809);
        } else if ((this->actor.scale.y >= 0.0f) && (this->rightHandType == PLAYER_MODELTYPE_RH_SHIELD)) {
            // Coordinates of the shield quad collider vertices, in the right hand limb's own model space.
            static Vec3f sRightHandLimbModelShieldQuadVertices[] = {
                { -4500.0f, -3000.0f, -600.0f },
                { 1500.0f, -3000.0f, -600.0f },
                { -4500.0f, 3000.0f, -600.0f },
                { 1500.0f, 3000.0f, -600.0f },
            };

            Matrix_Get(&this->shieldMf);
            Player_UpdateShieldCollider(play, this, &this->shieldQuad, sRightHandLimbModelShieldQuadVertices);
        }

        if (this->actor.scale.y >= 0.0f) {
            if ((this->heldItemAction == PLAYER_IA_HOOKSHOT) || (this->heldItemAction == PLAYER_IA_LONGSHOT)) {
                static Vec3f D_80126184 = { 100.0f, 1500.0f, 0.0f };

                Matrix_MultVec3f(&D_80126184, &this->unk_3C8);

                if (heldActor != NULL) {
                    static Vec3f D_80126190 = { 100.0f, 1640.0f, 0.0f };
                    MtxF sp44;
                    s32 pad;

                    Matrix_MultVec3f(&D_80126190, &heldActor->world.pos);
                    Matrix_RotateZYX(0, -0x4000, -0x4000, MTXMODE_APPLY);
                    Matrix_Get(&sp44);
                    Matrix_MtxFToYXZRotS(&sp44, &heldActor->world.rot, 0);
                    heldActor->shape.rot = heldActor->world.rot;

                    if (func_8002DD78(this)) {
                        Matrix_Translate(500.0f, 300.0f, 0.0f, MTXMODE_APPLY);
                        Player_DrawHookshotReticle(play, this,
                                                   (this->heldItemAction == PLAYER_IA_HOOKSHOT) ? 38600.0f : 77600.0f);
                    }
                }
            }

            if ((this->unk_862 != 0) || ((func_8002DD6C(this) == 0) && (heldActor != NULL))) {
                if (!(this->stateFlags1 & PLAYER_STATE1_10) && (this->unk_862 != 0) &&
                    (this->exchangeItemId != EXCH_ITEM_NONE)) {
                    Math_Vec3f_Copy(&sGetItemRefPos, &this->leftHandPos);
                } else {
                    sGetItemRefPos.x = (this->bodyPartsPos[PLAYER_BODYPART_R_HAND].x + this->leftHandPos.x) * 0.5f;
                    sGetItemRefPos.y = (this->bodyPartsPos[PLAYER_BODYPART_R_HAND].y + this->leftHandPos.y) * 0.5f;
                    sGetItemRefPos.z = (this->bodyPartsPos[PLAYER_BODYPART_R_HAND].z + this->leftHandPos.z) * 0.5f;
                }

                if (this->unk_862 == 0) {
                    Math_Vec3f_Copy(&heldActor->world.pos, &sGetItemRefPos);
                }
            }
        }
    } else if (this->actor.scale.y >= 0.0f) {
        if (limbIndex == PLAYER_LIMB_SHEATH) {
            if ((this->rightHandType != PLAYER_MODELTYPE_RH_SHIELD) &&
                (this->rightHandType != PLAYER_MODELTYPE_RH_FF)) {
                // Coordinates of the shield quad collider vertices, in the sheath limb's own model space.
                static Vec3f sSheathLimbModelShieldQuadVertices[] = {
                    { -3000.0f, -3000.0f, -900.0f },
                    { 3000.0f, -3000.0f, -900.0f },
                    { -3000.0f, 3000.0f, -900.0f },
                    { 3000.0f, 3000.0f, -900.0f },
                };
                // Position and rotation of the shield on Link's back, in the sheath limb's own model space.
                static Vec3f sSheathLimbModelShieldOnBackPos = { 630.0f, 100.0f, -30.0f };
                static Vec3s sSheathLimbModelShieldOnBackZyxRot = { 0, 0, 0x7FFF };

                if (Player_IsChildWithHylianShield(this)) {
                    Player_UpdateShieldCollider(play, this, &this->shieldQuad, sSheathLimbModelShieldQuadVertices);
                }

                Matrix_TranslateRotateZYX(&sSheathLimbModelShieldOnBackPos, &sSheathLimbModelShieldOnBackZyxRot);
                Matrix_Get(&this->shieldMf);
            }
        } else if (limbIndex == PLAYER_LIMB_HEAD) {
            Matrix_MultVec3f(&sPlayerFocusOffsetFromHead, &this->actor.focus.pos);
        } else {
            // Position of Link's foot, in the foot limb's own model space.
            static Vec3f sLeftRightFootLimbModelFootPos[] = {
                { 200.0f, 300.0f, 0.0f },
                { 200.0f, 200.0f, 0.0f },
            };
            Vec3f* footPos = &sLeftRightFootLimbModelFootPos[((void)0, gSaveContext.save.linkAge)];

            // The same model position is used for both feet,
            // but the resulting world position will be different for each limb.
            Actor_SetFeetPos(&this->actor, limbIndex, PLAYER_LIMB_L_FOOT, footPos, PLAYER_LIMB_R_FOOT, footPos);
        }
    }
}

u32 Player_InitPauseDrawData(PlayState* play, u8* segment, SkelAnime* skelAnime) {
    s16 linkObjectId = gLinkObjectIds[(void)0, gSaveContext.save.linkAge];
    u32 size;
    void* ptr;

    size = gObjectTable[OBJECT_GAMEPLAY_KEEP].vromEnd - gObjectTable[OBJECT_GAMEPLAY_KEEP].vromStart;
    ptr = segment + PAUSE_EQUIP_BUFFER_SIZE;
    DMA_REQUEST_SYNC(ptr, gObjectTable[OBJECT_GAMEPLAY_KEEP].vromStart, size, "../z_player_lib.c", 2982);

    size = gObjectTable[linkObjectId].vromEnd - gObjectTable[linkObjectId].vromStart;
    ptr = segment + PAUSE_EQUIP_BUFFER_SIZE + PAUSE_PLAYER_SEGMENT_GAMEPLAY_KEEP_BUFFER_SIZE;
    DMA_REQUEST_SYNC(ptr, gObjectTable[linkObjectId].vromStart, size, "../z_player_lib.c", 2988);

    ptr = (void*)ALIGN16((uintptr_t)ptr + size);

    gSegments[4] = OS_K0_TO_PHYSICAL(segment + PAUSE_EQUIP_BUFFER_SIZE);
    gSegments[6] =
        OS_K0_TO_PHYSICAL(segment + PAUSE_EQUIP_BUFFER_SIZE + PAUSE_PLAYER_SEGMENT_GAMEPLAY_KEEP_BUFFER_SIZE);

    SkelAnime_InitLink(play, skelAnime, gPlayerSkelHeaders[(void)0, gSaveContext.save.linkAge],
                       &gPlayerAnim_link_normal_wait, 9, ptr, ptr, PLAYER_LIMB_MAX);

    return PAUSE_EQUIP_BUFFER_SIZE + PAUSE_PLAYER_SEGMENT_GAMEPLAY_KEEP_BUFFER_SIZE + size +
           sizeof(Vec3s[PLAYER_LIMB_BUF_COUNT]);
}

u8 sPauseModelGroupBySword[] = {
    PLAYER_MODELGROUP_SWORD_AND_SHIELD, // PLAYER_SWORD_KOKIRI
    PLAYER_MODELGROUP_SWORD_AND_SHIELD, // PLAYER_SWORD_MASTER
    PLAYER_MODELGROUP_BGS,              // PLAYER_SWORD_BIGGORON
};

s32 Player_OverrideLimbDrawPause(PlayState* play, s32 limbIndex, Gfx** dList, Vec3f* pos, Vec3s* rot, void* arg) {
    u8* playerSwordAndShield = arg;
    //! @bug `playerSwordAndShield[0]` can be 0 (`PLAYER_SWORD_NONE`), which indexes `sPauseModelGroupBySword[-1]`.
    //! The result happens to be 0 (`PLAYER_MODELGROUP_0`) in vanilla, but weird values are likely to cause a crash.
    u8 modelGroup = sPauseModelGroupBySword[playerSwordAndShield[0] - PLAYER_SWORD_KOKIRI];
    s32 type;
    s32 dListOffset = 0;
    Gfx** dLists;

    if ((modelGroup == PLAYER_MODELGROUP_SWORD_AND_SHIELD) && !LINK_IS_ADULT &&
        (playerSwordAndShield[1] == PLAYER_SHIELD_HYLIAN)) {
        modelGroup = PLAYER_MODELGROUP_CHILD_HYLIAN_SHIELD;
    }

    if (limbIndex == PLAYER_LIMB_L_HAND) {
        type = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_LEFT_HAND];
        sLeftHandType = type;
        if ((type == PLAYER_MODELTYPE_LH_BGS) && (gSaveContext.save.info.playerData.swordHealth <= 0.0f)) {
            dListOffset = 4;
        }
    } else if (limbIndex == PLAYER_LIMB_R_HAND) {
        type = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_RIGHT_HAND];
        sRightHandType = type;
        if (type == PLAYER_MODELTYPE_RH_SHIELD) {
            dListOffset = playerSwordAndShield[1] * 4;
        }
    } else if (limbIndex == PLAYER_LIMB_SHEATH) {
        type = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_SHEATH];
        if ((type == PLAYER_MODELTYPE_SHEATH_18) || (type == PLAYER_MODELTYPE_SHEATH_19)) {
            dListOffset = playerSwordAndShield[1] * 4;
        }
    } else if (limbIndex == PLAYER_LIMB_WAIST) {
        type = gPlayerModelTypes[modelGroup][PLAYER_MODELGROUPENTRY_WAIST];
    } else {
        return false;
    }

    dLists = sPlayerDListGroups[type] + ((void)0, gSaveContext.save.linkAge);
    *dList = *(dLists + dListOffset);

    return false;
}

void Player_DrawPauseImpl(PlayState* play, void* gameplayKeep, void* linkObject, SkelAnime* skelAnime, Vec3f* pos,
                          Vec3s* rot, f32 scale, s32 sword, s32 tunic, s32 shield, s32 boots, s32 width, s32 height,
                          Vec3f* eye, Vec3f* at, f32 fovy, void* colorFrameBuffer, void* depthFrameBuffer) {
    // Note: the viewport x and y values are overwritten below, before usage
    static Vp viewport = { (PAUSE_EQUIP_PLAYER_WIDTH / 2) << 2, (PAUSE_EQUIP_PLAYER_HEIGHT / 2) << 2, G_MAXZ / 2, 0,
                           (PAUSE_EQUIP_PLAYER_WIDTH / 2) << 2, (PAUSE_EQUIP_PLAYER_HEIGHT / 2) << 2, G_MAXZ / 2, 0 };
    static Lights1 lights1 = gdSPDefLights1(80, 80, 80, 255, 255, 255, 84, 84, -84);
    static Vec3f lightDir = { 89.8f, 0.0f, 89.8f };
    u8 playerSwordAndShield[2];
    Gfx* opaRef;
    Gfx* xluRef;
    u16 perspNorm;
    Mtx* perspMtx = GRAPH_ALLOC(play->state.gfxCtx, sizeof(Mtx));
    Mtx* lookAtMtx = GRAPH_ALLOC(play->state.gfxCtx, sizeof(Mtx));

    OPEN_DISPS(play->state.gfxCtx, "../z_player_lib.c", 3129);

    opaRef = POLY_OPA_DISP;
    POLY_OPA_DISP++;

    xluRef = POLY_XLU_DISP;
    POLY_XLU_DISP++;

    gSPDisplayList(WORK_DISP++, POLY_OPA_DISP);
    gSPDisplayList(WORK_DISP++, POLY_XLU_DISP);

    gSPSegment(POLY_OPA_DISP++, 0x00, NULL);

    gDPPipeSync(POLY_OPA_DISP++);

    gSPLoadGeometryMode(POLY_OPA_DISP++, 0);
    gSPTexture(POLY_OPA_DISP++, 0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_OFF);
    gDPSetCombineMode(POLY_OPA_DISP++, G_CC_SHADE, G_CC_SHADE);
    gDPSetOtherMode(POLY_OPA_DISP++,
                    G_AD_DISABLE | G_CD_MAGICSQ | G_CK_NONE | G_TC_FILT | G_TF_BILERP | G_TT_NONE | G_TL_TILE |
                        G_TD_CLAMP | G_TP_PERSP | G_CYC_FILL | G_PM_NPRIMITIVE,
                    G_AC_NONE | G_ZS_PIXEL | G_RM_NOOP | G_RM_NOOP2);

    // Also matches if some of the previous graphics commands are moved inside this block too. Possible macro?
    if (1) {
        s32 pad[2];

        gSPLoadGeometryMode(POLY_OPA_DISP++, G_ZBUFFER | G_SHADE | G_CULL_BACK | G_LIGHTING | G_SHADING_SMOOTH);
    }

    gDPSetScissor(POLY_OPA_DISP++, G_SC_NON_INTERLACE, 0, 0, width, height);
    gSPClipRatio(POLY_OPA_DISP++, FRUSTRATIO_1);

    gDPSetColorImage(POLY_OPA_DISP++, G_IM_FMT_RGBA, G_IM_SIZ_16b, width, depthFrameBuffer);
    gDPSetCycleType(POLY_OPA_DISP++, G_CYC_FILL);
    gDPSetRenderMode(POLY_OPA_DISP++, G_RM_NOOP, G_RM_NOOP2);
    gDPSetFillColor(POLY_OPA_DISP++, (GPACK_ZDZ(G_MAXFBZ, 0) << 16) | GPACK_ZDZ(G_MAXFBZ, 0));
    gDPFillRectangle(POLY_OPA_DISP++, 0, 0, width - 1, height - 1);

    gDPPipeSync(POLY_OPA_DISP++);

    gDPSetColorImage(POLY_OPA_DISP++, G_IM_FMT_RGBA, G_IM_SIZ_16b, width, colorFrameBuffer);
    gDPSetCycleType(POLY_OPA_DISP++, G_CYC_FILL);
    gDPSetRenderMode(POLY_OPA_DISP++, G_RM_NOOP, G_RM_NOOP2);
    gDPSetFillColor(POLY_OPA_DISP++, (GPACK_RGBA5551(0, 0, 0, 1) << 16) | GPACK_RGBA5551(0, 0, 0, 1));
    gDPFillRectangle(POLY_OPA_DISP++, 0, 0, width - 1, height - 1);

    gDPPipeSync(POLY_OPA_DISP++);

    gDPSetDepthImage(POLY_OPA_DISP++, depthFrameBuffer);

    viewport.vp.vscale[0] = viewport.vp.vtrans[0] = width * ((1 << 2) / 2);
    viewport.vp.vscale[1] = viewport.vp.vtrans[1] = height * ((1 << 2) / 2);
    gSPViewport(POLY_OPA_DISP++, &viewport);

    guPerspective(perspMtx, &perspNorm, fovy, (f32)width / (f32)height, 10.0f, 4000.0f, 1.0f);

    gSPPerspNormalize(POLY_OPA_DISP++, perspNorm);
    gSPMatrix(POLY_OPA_DISP++, perspMtx, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_PROJECTION);

    guLookAt(lookAtMtx, eye->x, eye->y, eye->z, at->x, at->y, at->z, 0.0f, 1.0f, 0.0f);

    gSPMatrix(POLY_OPA_DISP++, lookAtMtx, G_MTX_NOPUSH | G_MTX_MUL | G_MTX_PROJECTION);

    playerSwordAndShield[0] = sword;
    playerSwordAndShield[1] = shield;

    Matrix_SetTranslateRotateYXZ(pos->x, pos->y, pos->z, rot);
    Matrix_Scale(scale, scale, scale, MTXMODE_APPLY);

    gSPSegment(POLY_OPA_DISP++, 0x04, gameplayKeep);
    gSPSegment(POLY_OPA_DISP++, 0x06, linkObject);

    gSPSetLights1(POLY_OPA_DISP++, lights1);

    func_80093C80(play);

    POLY_OPA_DISP = Gfx_SetFog2(POLY_OPA_DISP++, 0, 0, 0, 0, 997, 1000);

    func_8002EABC(pos, &play->view.eye, &lightDir, play->state.gfxCtx);

    gSPSegment(POLY_OPA_DISP++, 0x0C, gCullBackDList);

    Player_DrawImpl(play, skelAnime->skeleton, skelAnime->jointTable, skelAnime->dListCount, 0, tunic, boots,
                    PLAYER_FACE_NEUTRAL, Player_OverrideLimbDrawPause, NULL, &playerSwordAndShield);

    gSPEndDisplayList(POLY_OPA_DISP++);
    gSPEndDisplayList(POLY_XLU_DISP++);

    gSPBranchList(opaRef, POLY_OPA_DISP);
    gSPBranchList(xluRef, POLY_XLU_DISP);

    CLOSE_DISPS(play->state.gfxCtx, "../z_player_lib.c", 3288);
}

void Player_DrawPause(PlayState* play, u8* segment, SkelAnime* skelAnime, Vec3f* pos, Vec3s* rot, f32 scale, s32 sword,
                      s32 tunic, s32 shield, s32 boots) {
    static Vec3f eye = { 0.0f, 0.0f, -400.0f };
    static Vec3f at = { 0.0f, 0.0f, 0.0f };
    Vec3s* destTable;
    Vec3s* srcTable;
    s32 i;

    gSegments[4] = OS_K0_TO_PHYSICAL(segment + PAUSE_EQUIP_BUFFER_SIZE);
    gSegments[6] =
        OS_K0_TO_PHYSICAL(segment + PAUSE_EQUIP_BUFFER_SIZE + PAUSE_PLAYER_SEGMENT_GAMEPLAY_KEEP_BUFFER_SIZE);

    if (!LINK_IS_ADULT) {
        if (shield == PLAYER_SHIELD_DEKU) {
            srcTable = gLinkPauseChildDekuShieldJointTable;
        } else {
            srcTable = gLinkPauseChildJointTable;
        }
    } else {
        if (sword == PLAYER_SWORD_BIGGORON) {
            srcTable = gLinkPauseAdultBgsJointTable;
        } else if (shield != PLAYER_SHIELD_NONE) {
            srcTable = gLinkPauseAdultShieldJointTable;
        } else {
            srcTable = gLinkPauseAdultJointTable;
        }
    }

    srcTable = SEGMENTED_TO_VIRTUAL(srcTable);
    destTable = skelAnime->jointTable;
    for (i = 0; i < skelAnime->limbCount; i++) {
        *destTable++ = *srcTable++;
    }

    Player_DrawPauseImpl(play, segment + PAUSE_EQUIP_BUFFER_SIZE,
                         segment + PAUSE_EQUIP_BUFFER_SIZE + PAUSE_PLAYER_SEGMENT_GAMEPLAY_KEEP_BUFFER_SIZE, skelAnime,
                         pos, rot, scale, sword, tunic, shield, boots, PAUSE_EQUIP_PLAYER_WIDTH,
                         PAUSE_EQUIP_PLAYER_HEIGHT, &eye, &at, 60.0f, play->state.gfxCtx->curFrameBuffer,
                         play->state.gfxCtx->curFrameBuffer + (PAUSE_EQUIP_PLAYER_WIDTH * PAUSE_EQUIP_PLAYER_HEIGHT));
}
