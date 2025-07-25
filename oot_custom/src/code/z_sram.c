#include "sram.h"

#include "array_count.h"
#include "file_select_state.h"
#include "controller.h"
#include "memory_utils.h"
#include "printf.h"
#include "terminal.h"
#include "translation.h"
#include "versions.h"
#include "audio.h"
#include "game.h"
#include "interface.h"
#include "message.h"
#include "ocarina.h"
#include "save.h"
#include "scene.h"
#include "ss_sram.h"

#define SLOT_SIZE (sizeof(SaveContext) + 0x28)
#define CHECKSUM_SIZE (sizeof(Save) / 2)

#define DEATHS offsetof(SaveContext, save.info.playerData.deaths)
#define NAME offsetof(SaveContext, save.info.playerData.playerName)
#define N64DD offsetof(SaveContext, save.info.playerData.n64ddFlag)
#define HEALTH_CAP offsetof(SaveContext, save.info.playerData.healthCapacity)
#define QUEST offsetof(SaveContext, save.info.inventory.questItems)
#define DEFENSE offsetof(SaveContext, save.info.inventory.defenseHearts)
#if OOT_PAL
#define HEALTH offsetof(SaveContext, save.info.playerData.health)
#endif

#define SLOT_OFFSET(index) (SRAM_HEADER_SIZE + 0x10 + (index * SLOT_SIZE))

#if !PLATFORM_IQUE

#define SRAM_READ(addr, dramAddr, size) SsSram_ReadWrite(addr, dramAddr, size, OS_READ)
#define SRAM_WRITE(addr, dramAddr, size) SsSram_ReadWrite(addr, dramAddr, size, OS_WRITE)

#else

void Sram_ReadWriteIQue(s32 addr, void* dramAddr, size_t size, s32 direction) {
    void* sramAddr;

    addr -= OS_K1_TO_PHYSICAL(0xA8000000);
    sramAddr = (void*)(__osBbSramAddress + addr);
    if (direction == OS_READ) {
        bcopy(sramAddr, dramAddr, size);
    } else if (direction == OS_WRITE) {
        bcopy(dramAddr, sramAddr, size);
    }
}

#define SRAM_READ(addr, dramAddr, size) Sram_ReadWriteIQue(addr, dramAddr, size, OS_READ)
#define SRAM_WRITE(addr, dramAddr, size) Sram_ReadWriteIQue(addr, dramAddr, size, OS_WRITE)

#endif

u16 gSramSlotOffsets[] = {
    SLOT_OFFSET(0),
    SLOT_OFFSET(1),
    SLOT_OFFSET(2),
    // the latter three saves are backup saves for the former saves
    SLOT_OFFSET(3),
    SLOT_OFFSET(4),
    SLOT_OFFSET(5),
};

static u8 sSramDefaultHeader[] = {
    SOUND_SETTING_STEREO,    // SRAM_HEADER_SOUND
    Z_TARGET_SETTING_SWITCH, // SRAM_HEADER_Z_TARGET
#if OOT_NTSC
    LANGUAGE_JPN, // SRAM_HEADER_LANGUAGE
#else
    LANGUAGE_ENG, // SRAM_HEADER_LANGUAGE
#endif

    // SRAM_HEADER_MAGIC
    0x98,
    0x09,
    0x10,
    0x21,
    'Z',
    'E',
    'L',
    'D',
    'A',
};

static SavePlayerData sNewSavePlayerData = {
    { '\0', '\0', '\0', '\0', '\0', '\0' }, // newf
    0,                                      // deaths
#if OOT_NTSC
    {
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
    }, // playerName
#else
    {
        FILENAME_UPPERCASE('L'),
        FILENAME_UPPERCASE('I'),
        FILENAME_UPPERCASE('N'),
        FILENAME_UPPERCASE('K'),
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
    }, // playerName
#endif
    0,                  // n64ddFlag
    0xE0,               // healthCapacity - 14 hearts (INCREASED from 0x30 = 3 hearts)
    0xE0,               // health - 14 hearts (INCREASED from 0x30 = 3 hearts)
    1,                  // magicLevel - Has magic (INCREASED from 0 = no magic)
    MAGIC_NORMAL_METER, // magic - Full magic meter
    150,                // rupees - Start with some rupees (INCREASED from 0 = no rupees)
    8,                  // swordHealth
    0,                  // naviTimer
    true,               // isMagicAcquired - Magic acquired (CHANGED from false = no magic)
    0,                  // unk_1F
    false,              // isDoubleMagicAcquired - (DEFAULT: false)
    false,              // isDoubleDefenseAcquired - (DEFAULT: false)
    0,                  // bgsFlag
    0,                  // ocarinaGameRoundNum
    {
        { ITEM_NONE, ITEM_NONE, ITEM_NONE, ITEM_NONE }, // buttonItems
        { SLOT_NONE, SLOT_NONE, SLOT_NONE },            // cButtonSlots
        0,                                              // equipment
    },                                                  // childEquips
    {
        { ITEM_NONE, ITEM_NONE, ITEM_NONE, ITEM_NONE }, // buttonItems
        { SLOT_NONE, SLOT_NONE, SLOT_NONE },            // cButtonSlots
        0,                                              // equipment
    },                                                  // adultEquips
    0,                                                  // unk_38
    { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },       // unk_3C
    SCENE_LINKS_HOUSE,                                  // savedSceneId
};

static ItemEquips sNewSaveEquips = {
    // buttonItems - Default equipment (CHANGED from all ITEM_NONE = no items equipped)
    { ITEM_SWORD_MASTER, ITEM_BOW, ITEM_BOMB, ITEM_OCARINA_FAIRY }, 
    // cButtonSlots - C button assignments (CHANGED from all SLOT_NONE = no assignments)
    { SLOT_BOW, SLOT_BOMB, SLOT_OCARINA },                          
    // equipment - All equipment unlocked (CHANGED from 0x1100 = basic Kokiri equipment only)
    // Original: 0x1100 = Only Kokiri Tunic + Kokiri Boots
    // New: Full equipment including swords, shields, tunics, boots
    (EQUIP_VALUE_SWORD_MASTER << (EQUIP_TYPE_SWORD * 4)) | (EQUIP_VALUE_SHIELD_HYLIAN << (EQUIP_TYPE_SHIELD * 4)) |
        (EQUIP_VALUE_TUNIC_KOKIRI << (EQUIP_TYPE_TUNIC * 4)) | (EQUIP_VALUE_BOOTS_KOKIRI << (EQUIP_TYPE_BOOTS * 4)),
};

static Inventory sNewSaveInventory = {
    // items - All major items given by default (CHANGED from all ITEM_NONE = empty inventory)
    {
        ITEM_DEKU_STICK,          // SLOT_DEKU_STICK (was ITEM_NONE)
        ITEM_DEKU_NUT,            // SLOT_DEKU_NUT (was ITEM_NONE)
        ITEM_BOMB,                // SLOT_BOMB (was ITEM_NONE)
        ITEM_BOW,                 // SLOT_BOW (was ITEM_NONE)
        ITEM_ARROW_FIRE,          // SLOT_ARROW_FIRE (was ITEM_NONE)
        ITEM_DINS_FIRE,           // SLOT_DINS_FIRE (was ITEM_NONE)
        ITEM_SLINGSHOT,           // SLOT_SLINGSHOT (was ITEM_NONE)
        ITEM_OCARINA_FAIRY,       // SLOT_OCARINA (was ITEM_NONE)
        ITEM_BOMBCHU,             // SLOT_BOMBCHU (was ITEM_NONE)
        ITEM_HOOKSHOT,            // SLOT_HOOKSHOT (was ITEM_NONE)
        ITEM_ARROW_ICE,           // SLOT_ARROW_ICE (was ITEM_NONE)
        ITEM_FARORES_WIND,        // SLOT_FARORES_WIND (was ITEM_NONE)
        ITEM_BOOMERANG,           // SLOT_BOOMERANG (was ITEM_NONE)
        ITEM_LENS_OF_TRUTH,       // SLOT_LENS_OF_TRUTH (was ITEM_NONE)
        ITEM_MAGIC_BEAN,          // SLOT_MAGIC_BEAN (was ITEM_NONE)
        ITEM_HAMMER,              // SLOT_HAMMER (was ITEM_NONE)
        ITEM_ARROW_LIGHT,         // SLOT_ARROW_LIGHT (was ITEM_NONE)
        ITEM_NAYRUS_LOVE,         // SLOT_NAYRUS_LOVE (was ITEM_NONE)
        ITEM_CHRONOS_MAGIC,       // SLOT_CHRONOS_MAGIC (was ITEM_NONE)
        ITEM_BOTTLE_EMPTY,        // SLOT_BOTTLE_1 (was ITEM_NONE)
        ITEM_BOTTLE_POTION_RED,   // SLOT_BOTTLE_2 (was ITEM_NONE)
        ITEM_BOTTLE_POTION_GREEN, // SLOT_BOTTLE_3 (was ITEM_NONE)
        ITEM_BOTTLE_POTION_BLUE,  // SLOT_BOTTLE_4 (was ITEM_NONE)
        ITEM_POCKET_EGG,          // SLOT_TRADE_ADULT (was ITEM_NONE)
    },
    // ammo - Appropriate ammo counts for each item (CHANGED from all 0 = no ammo)
    {
        50, // SLOT_DEKU_STICK (was 0)
        50, // SLOT_DEKU_NUT (was 0)
        10, // SLOT_BOMB (was 0)
        30, // SLOT_BOW (was 0)
        1,  // SLOT_ARROW_FIRE (was 0)
        1,  // SLOT_DINS_FIRE (was 0)
        30, // SLOT_SLINGSHOT (was 0)
        1,  // SLOT_OCARINA (was 0)
        50, // SLOT_BOMBCHU (was 0)
        1,  // SLOT_HOOKSHOT (was 0)
        1,  // SLOT_ARROW_ICE (was 0)
        1,  // SLOT_FARORES_WIND (was 0)
        1,  // SLOT_BOOMERANG (was 0)
        1,  // SLOT_LENS_OF_TRUTH (was 0)
        1,  // SLOT_MAGIC_BEAN (was 0)
        1,  // SLOT_HAMMER (was 0)
    },
    // equipment - All equipment unlocked (CHANGED from basic equipment only)
    // Original: (((1 << EQUIP_INV_TUNIC_KOKIRI) << (EQUIP_TYPE_TUNIC * 4)) | ((1 << EQUIP_INV_BOOTS_KOKIRI) << (EQUIP_TYPE_BOOTS * 4)))
    // New: All swords, shields, tunics, and boots available
    ((((1 << EQUIP_INV_SWORD_KOKIRI) << (EQUIP_TYPE_SWORD * 4)) |
      ((1 << EQUIP_INV_SWORD_MASTER) << (EQUIP_TYPE_SWORD * 4)) |
      ((1 << EQUIP_INV_SWORD_BIGGORON) << (EQUIP_TYPE_SWORD * 4))) |
     (((1 << EQUIP_INV_SHIELD_DEKU) << (EQUIP_TYPE_SHIELD * 4)) |
      ((1 << EQUIP_INV_SHIELD_HYLIAN) << (EQUIP_TYPE_SHIELD * 4)) |
      ((1 << EQUIP_INV_SHIELD_MIRROR) << (EQUIP_TYPE_SHIELD * 4))) |
     (((1 << EQUIP_INV_TUNIC_KOKIRI) << (EQUIP_TYPE_TUNIC * 4)) |
      ((1 << EQUIP_INV_TUNIC_GORON) << (EQUIP_TYPE_TUNIC * 4)) |
      ((1 << EQUIP_INV_TUNIC_ZORA) << (EQUIP_TYPE_TUNIC * 4))) |
     (((1 << EQUIP_INV_BOOTS_KOKIRI) << (EQUIP_TYPE_BOOTS * 4)) |
      ((1 << EQUIP_INV_BOOTS_IRON) << (EQUIP_TYPE_BOOTS * 4)) |
      ((1 << EQUIP_INV_BOOTS_HOVER) << (EQUIP_TYPE_BOOTS * 4)))),
    0x125249,   // upgrades - All item upgrades (CHANGED from 0 = no upgrades)
    0x1E3FFFF,  // questItems - All quest items (CHANGED from 0 = no quest items)
    // dungeonItems - All dungeon items (CHANGED from all 0 = no dungeon items)
    // Each entry has value 7 (0b111) = Boss Key + Compass + Map
    { 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, 
    // dungeonKeys - All dungeon keys (CHANGED from all 0xFF = no keys)  
    // Each entry has value 8 = maximum number of small keys for that dungeon
    { 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8 },    
    0,                                                              // defenseHearts
    0,                                                              // gsTokens
};

static Checksum sNewSaveChecksum = { 0 };

/**
 *  Initialize new save.
 *  This save now has a full inventory with 14 hearts and magic.
 */
void Sram_InitNewSave(void) {
    bzero(&gSaveContext.save.info, sizeof(SaveInfo));
    gSaveContext.save.totalDays = 0;
    gSaveContext.save.bgsDayCount = 0;

    gSaveContext.save.info.playerData = sNewSavePlayerData;
    gSaveContext.save.info.equips = sNewSaveEquips;
    gSaveContext.save.info.inventory = sNewSaveInventory;
    gSaveContext.save.info.checksum = sNewSaveChecksum;

    gSaveContext.save.info.horseData.sceneId = SCENE_HYRULE_FIELD;
    gSaveContext.save.info.horseData.pos.x = -1840;
    gSaveContext.save.info.horseData.pos.y = 72;
    gSaveContext.save.info.horseData.pos.z = 5497;
    gSaveContext.save.info.horseData.angle = -0x6AD9;
    // Don't override magicLevel since we want magic by default now
    // REMOVED: gSaveContext.save.info.playerData.magicLevel = 0; (was resetting magic to 0)
    // This was overriding the magicLevel = 1 set in sNewSavePlayerData
    gSaveContext.save.info.infTable[INFTABLE_INDEX_1DX] = 1;
    gSaveContext.save.info.sceneFlags[SCENE_WATER_TEMPLE].swch = 0x40000000;
}

static SavePlayerData sDebugSavePlayerData = {
    { 'Z', 'E', 'L', 'D', 'A', 'Z' }, // newf
    0,                                // deaths
#if OOT_VERSION < PAL_1_0
    {
        0x81, // リ
        0x87, // ン
        0x61, // ク
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
    }, // playerName
#else
    {
        FILENAME_UPPERCASE('L'),
        FILENAME_UPPERCASE('I'),
        FILENAME_UPPERCASE('N'),
        FILENAME_UPPERCASE('K'),
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
        FILENAME_SPACE,
    }, // playerName
#endif
    0,                  // n64ddFlag
    0xE0,               // healthCapacity
    0xE0,               // health
    0,                  // magicLevel
    MAGIC_NORMAL_METER, // magic
    999,                // rupees - INCREASED from 150 for more starting money
    8,                  // swordHealth
    0,                  // naviTimer
    true,               // isMagicAcquired
    0,                  // unk_1F
    true,              // isDoubleMagicAcquired - CHANGED from false to give double magic bar
    true,              // isDoubleDefenseAcquired - CHANGED from false to give double defense
    0,                  // bgsFlag
    0,                  // ocarinaGameRoundNum
    {
        { ITEM_NONE, ITEM_NONE, ITEM_NONE, ITEM_NONE }, // buttonItems
        { SLOT_NONE, SLOT_NONE, SLOT_NONE },            // cButtonSlots
        0,                                              // equipment
    },                                                  // childEquips
    {
        { ITEM_NONE, ITEM_NONE, ITEM_NONE, ITEM_NONE }, // buttonItems
        { SLOT_NONE, SLOT_NONE, SLOT_NONE },            // cButtonSlots
        0,                                              // equipment
    },                                                  // adultEquips
    0,                                                  // unk_38
    { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 },       // unk_3C
    SCENE_HYRULE_FIELD,                                 // savedSceneId
};

static ItemEquips sDebugSaveEquips = {
    { ITEM_SWORD_MASTER, ITEM_BOW, ITEM_BOMB, ITEM_OCARINA_FAIRY }, // buttonItems
    { SLOT_BOW, SLOT_BOMB, SLOT_OCARINA },                          // cButtonSlots
    // equipment
    (EQUIP_VALUE_SWORD_MASTER << (EQUIP_TYPE_SWORD * 4)) | (EQUIP_VALUE_SHIELD_HYLIAN << (EQUIP_TYPE_SHIELD * 4)) |
        (EQUIP_VALUE_TUNIC_KOKIRI << (EQUIP_TYPE_TUNIC * 4)) | (EQUIP_VALUE_BOOTS_KOKIRI << (EQUIP_TYPE_BOOTS * 4)),
};

static Inventory sDebugSaveInventory = {
    // items
    {
        ITEM_DEKU_STICK,          // SLOT_DEKU_STICK
        ITEM_DEKU_NUT,            // SLOT_DEKU_NUT
        ITEM_BOMB,                // SLOT_BOMB
        ITEM_BOW,                 // SLOT_BOW
        ITEM_ARROW_FIRE,          // SLOT_ARROW_FIRE
        ITEM_DINS_FIRE,           // SLOT_DINS_FIRE
        ITEM_SLINGSHOT,           // SLOT_SLINGSHOT
        ITEM_OCARINA_FAIRY,       // SLOT_OCARINA
        ITEM_BOMBCHU,             // SLOT_BOMBCHU
        ITEM_HOOKSHOT,            // SLOT_HOOKSHOT
        ITEM_ARROW_ICE,           // SLOT_ARROW_ICE
        ITEM_FARORES_WIND,        // SLOT_FARORES_WIND
        ITEM_BOOMERANG,           // SLOT_BOOMERANG
        ITEM_LENS_OF_TRUTH,       // SLOT_LENS_OF_TRUTH
        ITEM_MAGIC_BEAN,          // SLOT_MAGIC_BEAN
        ITEM_HAMMER,              // SLOT_HAMMER
        ITEM_ARROW_LIGHT,         // SLOT_ARROW_LIGHT
        ITEM_NAYRUS_LOVE,         // SLOT_NAYRUS_LOVE
        ITEM_BOTTLE_EMPTY,        // SLOT_BOTTLE_1
        ITEM_BOTTLE_POTION_RED,   // SLOT_BOTTLE_2
        ITEM_BOTTLE_POTION_GREEN, // SLOT_BOTTLE_3
        ITEM_BOTTLE_POTION_BLUE,  // SLOT_BOTTLE_4
        ITEM_POCKET_EGG,          // SLOT_TRADE_ADULT
        ITEM_WEIRD_EGG,           // SLOT_TRADE_CHILD
    },
    // ammo
    {
        50, // SLOT_DEKU_STICK
        50, // SLOT_DEKU_NUT
        10, // SLOT_BOMB
        30, // SLOT_BOW
        1,  // SLOT_ARROW_FIRE
        1,  // SLOT_DINS_FIRE
        30, // SLOT_SLINGSHOT
        1,  // SLOT_OCARINA
        50, // SLOT_BOMBCHU
        1,  // SLOT_HOOKSHOT
        1,  // SLOT_ARROW_ICE
        1,  // SLOT_FARORES_WIND
        1,  // SLOT_BOOMERANG
        1,  // SLOT_LENS_OF_TRUTH
        1,  // SLOT_MAGIC_BEAN
        1   // SLOT_HAMMER
    },
    // equipment
    ((((1 << EQUIP_INV_SWORD_KOKIRI) << (EQUIP_TYPE_SWORD * 4)) |
      ((1 << EQUIP_INV_SWORD_MASTER) << (EQUIP_TYPE_SWORD * 4)) |
      ((1 << EQUIP_INV_SWORD_BIGGORON) << (EQUIP_TYPE_SWORD * 4))) |
     (((1 << EQUIP_INV_SHIELD_DEKU) << (EQUIP_TYPE_SHIELD * 4)) |
      ((1 << EQUIP_INV_SHIELD_HYLIAN) << (EQUIP_TYPE_SHIELD * 4)) |
      ((1 << EQUIP_INV_SHIELD_MIRROR) << (EQUIP_TYPE_SHIELD * 4))) |
     (((1 << EQUIP_INV_TUNIC_KOKIRI) << (EQUIP_TYPE_TUNIC * 4)) |
      ((1 << EQUIP_INV_TUNIC_GORON) << (EQUIP_TYPE_TUNIC * 4)) |
      ((1 << EQUIP_INV_TUNIC_ZORA) << (EQUIP_TYPE_TUNIC * 4))) |
     (((1 << EQUIP_INV_BOOTS_KOKIRI) << (EQUIP_TYPE_BOOTS * 4)) |
      ((1 << EQUIP_INV_BOOTS_IRON) << (EQUIP_TYPE_BOOTS * 4)) |
      ((1 << EQUIP_INV_BOOTS_HOVER) << (EQUIP_TYPE_BOOTS * 4)))),
    0x125249,                                                       // upgrades
    0x1E3FFFF,                                                      // questItems
    { 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }, // dungeonItems
    { 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8 },    // dungeonKeys
    0,                                                              // defenseHearts
    0,                                                              // gsTokens
};

static Checksum sDebugSaveChecksum = { 0 };

/**
 *  Initialize debug save. This is also used on the Title Screen
 *  This save has a mostly full inventory with 10 hearts and single magic.
 *
 *  Some noteable flags that are set:
 *  Showed Mido sword/shield, met Deku Tree, Deku Tree mouth opened,
 *  used blue warp in Gohmas room, Zelda fled castle, light arrow cutscene watched,
 *  and set water level in Water Temple to lowest level.
 */
void Sram_InitDebugSave(void) {
    bzero(&gSaveContext.save.info, sizeof(SaveInfo));
    gSaveContext.save.totalDays = 0;
    gSaveContext.save.bgsDayCount = 0;

    gSaveContext.save.info.playerData = sDebugSavePlayerData;
    gSaveContext.save.info.equips = sDebugSaveEquips;
    gSaveContext.save.info.inventory = sDebugSaveInventory;
    gSaveContext.save.info.checksum = sDebugSaveChecksum;

    gSaveContext.save.info.horseData.sceneId = SCENE_HYRULE_FIELD;
    gSaveContext.save.info.horseData.pos.x = -1840;
    gSaveContext.save.info.horseData.pos.y = 72;
    gSaveContext.save.info.horseData.pos.z = 5497;
    gSaveContext.save.info.horseData.angle = -0x6AD9;
    gSaveContext.save.info.infTable[INFTABLE_INDEX_0] |= INFTABLE_MASK(INFTABLE_00) | INFTABLE_MASK(INFTABLE_03) |
                                                         INFTABLE_MASK(INFTABLE_0C) | INFTABLE_MASK(INFTABLE_0E);

    gSaveContext.save.info.eventChkInf[EVENTCHKINF_INDEX_0] |=
        EVENTCHKINF_MASK(EVENTCHKINF_00_UNUSED) | EVENTCHKINF_MASK(EVENTCHKINF_01_UNUSED) |
        EVENTCHKINF_MASK(EVENTCHKINF_MIDO_DENIED_DEKU_TREE_ACCESS) | EVENTCHKINF_MASK(EVENTCHKINF_03) |
        EVENTCHKINF_MASK(EVENTCHKINF_04) | EVENTCHKINF_MASK(EVENTCHKINF_05) | EVENTCHKINF_MASK(EVENTCHKINF_09) |
        EVENTCHKINF_MASK(EVENTCHKINF_0C);

    SET_EVENTCHKINF(EVENTCHKINF_80);
    SET_EVENTCHKINF(EVENTCHKINF_C4);

    if (LINK_AGE_IN_YEARS == YEARS_CHILD) {
        gSaveContext.save.info.equips.buttonItems[0] = ITEM_SWORD_KOKIRI;
        Inventory_ChangeEquipment(EQUIP_TYPE_SWORD, EQUIP_VALUE_SWORD_KOKIRI);
        if (gSaveContext.fileNum == 0xFF) {
            gSaveContext.save.info.equips.buttonItems[1] = ITEM_SLINGSHOT;
            gSaveContext.save.info.equips.cButtonSlots[0] = SLOT_SLINGSHOT;
            Inventory_ChangeEquipment(EQUIP_TYPE_SHIELD, EQUIP_VALUE_SHIELD_DEKU);
        }
    }

    gSaveContext.save.entranceIndex = ENTR_HYRULE_FIELD_0;
    gSaveContext.save.info.playerData.magicLevel = 0;
    gSaveContext.save.info.sceneFlags[SCENE_WATER_TEMPLE].swch = 0x40000000;
}

static s16 sDungeonEntrances[] = {
    ENTR_DEKU_TREE_0,                      // SCENE_DEKU_TREE
    ENTR_DODONGOS_CAVERN_0,                // SCENE_DODONGOS_CAVERN
    ENTR_JABU_JABU_0,                      // SCENE_JABU_JABU
    ENTR_FOREST_TEMPLE_0,                  // SCENE_FOREST_TEMPLE
    ENTR_FIRE_TEMPLE_0,                    // SCENE_FIRE_TEMPLE
    ENTR_WATER_TEMPLE_0,                   // SCENE_WATER_TEMPLE
    ENTR_SPIRIT_TEMPLE_0,                  // SCENE_SPIRIT_TEMPLE
    ENTR_SHADOW_TEMPLE_0,                  // SCENE_SHADOW_TEMPLE
    ENTR_BOTTOM_OF_THE_WELL_0,             // SCENE_BOTTOM_OF_THE_WELL
    ENTR_ICE_CAVERN_0,                     // SCENE_ICE_CAVERN
    ENTR_GANONS_TOWER_0,                   // SCENE_GANONS_TOWER
    ENTR_GERUDO_TRAINING_GROUND_0,         // SCENE_GERUDO_TRAINING_GROUND
    ENTR_THIEVES_HIDEOUT_0,                // SCENE_THIEVES_HIDEOUT
    ENTR_INSIDE_GANONS_CASTLE_0,           // SCENE_INSIDE_GANONS_CASTLE
    ENTR_GANONS_TOWER_COLLAPSE_INTERIOR_0, // SCENE_GANONS_TOWER_COLLAPSE_INTERIOR
    ENTR_INSIDE_GANONS_CASTLE_COLLAPSE_0,  // SCENE_INSIDE_GANONS_CASTLE_COLLAPSE
};

/**
 *  Copy save currently on the buffer to Save Context and complete various tasks to open the save.
 *  This includes:
 *  - Set proper entrance depending on where the game was saved
 *  - If health is less than 3 hearts, give 3 hearts
 *  - If either scarecrow song is set, copy them from save context to the proper location
 *  - Handle a case where the player saved and quit after zelda cutscene but didnt get the song
 *  - Give and equip master sword if player is adult and doesn't have master sword
 *  - Revert any trade items that spoil
 */
void Sram_OpenSave(SramContext* sramCtx) {
    u16 i;
    u16 j;
    u8* ptr;

    PRINTF(T("個人Ｆｉｌｅ作成\n", "Create personal file\n"));
    i = gSramSlotOffsets[gSaveContext.fileNum];
    PRINTF(T("ぽいんと＝%x(%d)\n", "Point=%x(%d)\n"), i, gSaveContext.fileNum);

    MemCpy(&gSaveContext, sramCtx->readBuff + i, sizeof(Save));

    PRINTF_COLOR_YELLOW();
    PRINTF("SCENE_DATA_ID = %d   SceneNo = %d\n", gSaveContext.save.info.playerData.savedSceneId,
           ((void)0, gSaveContext.save.entranceIndex));

    switch (gSaveContext.save.info.playerData.savedSceneId) {
        case SCENE_DEKU_TREE:
        case SCENE_DODONGOS_CAVERN:
        case SCENE_JABU_JABU:
        case SCENE_FOREST_TEMPLE:
        case SCENE_FIRE_TEMPLE:
        case SCENE_WATER_TEMPLE:
        case SCENE_SPIRIT_TEMPLE:
        case SCENE_SHADOW_TEMPLE:
        case SCENE_BOTTOM_OF_THE_WELL:
        case SCENE_ICE_CAVERN:
        case SCENE_GANONS_TOWER:
        case SCENE_GERUDO_TRAINING_GROUND:
        case SCENE_THIEVES_HIDEOUT:
        case SCENE_INSIDE_GANONS_CASTLE:
            gSaveContext.save.entranceIndex = sDungeonEntrances[gSaveContext.save.info.playerData.savedSceneId];
            break;

        case SCENE_DEKU_TREE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_DEKU_TREE_0;
            break;

        case SCENE_DODONGOS_CAVERN_BOSS:
            gSaveContext.save.entranceIndex = ENTR_DODONGOS_CAVERN_0;
            break;

        case SCENE_JABU_JABU_BOSS:
            gSaveContext.save.entranceIndex = ENTR_JABU_JABU_0;
            break;

        case SCENE_FOREST_TEMPLE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_FOREST_TEMPLE_0;
            break;

        case SCENE_FIRE_TEMPLE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_FIRE_TEMPLE_0;
            break;

        case SCENE_WATER_TEMPLE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_WATER_TEMPLE_0;
            break;

        case SCENE_SPIRIT_TEMPLE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_SPIRIT_TEMPLE_0;
            break;

        case SCENE_SHADOW_TEMPLE_BOSS:
            gSaveContext.save.entranceIndex = ENTR_SHADOW_TEMPLE_0;
            break;

        case SCENE_GANONS_TOWER_COLLAPSE_INTERIOR:
        case SCENE_INSIDE_GANONS_CASTLE_COLLAPSE:
        case SCENE_GANONDORF_BOSS:
        case SCENE_GANONS_TOWER_COLLAPSE_EXTERIOR:
        case SCENE_GANON_BOSS:
            gSaveContext.save.entranceIndex = ENTR_GANONS_TOWER_0;
            break;

        default:
            if (gSaveContext.save.info.playerData.savedSceneId != SCENE_LINKS_HOUSE) {
                if (LINK_AGE_IN_YEARS == YEARS_CHILD) {
                    gSaveContext.save.entranceIndex = ENTR_LINKS_HOUSE_0;
                } else {
                    gSaveContext.save.entranceIndex = ENTR_TEMPLE_OF_TIME_7;
                }
            } else {
                gSaveContext.save.entranceIndex = ENTR_LINKS_HOUSE_0;
            }
            break;
    }

    PRINTF("scene_no = %d\n", gSaveContext.save.entranceIndex);
    PRINTF_RST();

    if (gSaveContext.save.info.playerData.health < 0x30) {
        gSaveContext.save.info.playerData.health = 0x30;
    }

    if (gSaveContext.save.info.scarecrowLongSongSet) {
        PRINTF_COLOR_BLUE();
        PRINTF("\n====================================================================\n");

        MemCpy(gScarecrowLongSongPtr, gSaveContext.save.info.scarecrowLongSong,
               sizeof(gSaveContext.save.info.scarecrowLongSong));

        ptr = (u8*)gScarecrowLongSongPtr;
        for (i = 0; i < ARRAY_COUNT(gSaveContext.save.info.scarecrowLongSong); i++, ptr++) {
            PRINTF("%d, ", *ptr);
        }

        PRINTF("\n====================================================================\n");
        PRINTF_RST();
    }

    if (gSaveContext.save.info.scarecrowSpawnSongSet) {
        PRINTF_COLOR_GREEN();
        PRINTF("\n====================================================================\n");

        MemCpy(gScarecrowSpawnSongPtr, gSaveContext.save.info.scarecrowSpawnSong,
               sizeof(gSaveContext.save.info.scarecrowSpawnSong));

        ptr = gScarecrowSpawnSongPtr;
        for (i = 0; i < ARRAY_COUNT(gSaveContext.save.info.scarecrowSpawnSong); i++, ptr++) {
            PRINTF("%d, ", *ptr);
        }

        PRINTF("\n====================================================================\n");
        PRINTF_RST();
    }

    // if zelda cutscene has been watched but lullaby was not obtained, restore cutscene and take away letter
    if (GET_EVENTCHKINF(EVENTCHKINF_40) && !CHECK_QUEST_ITEM(QUEST_SONG_LULLABY)) {
        i = gSaveContext.save.info.eventChkInf[EVENTCHKINF_INDEX_40];
        i &= ~EVENTCHKINF_MASK(EVENTCHKINF_40);
        gSaveContext.save.info.eventChkInf[EVENTCHKINF_INDEX_40] = i;

        INV_CONTENT(ITEM_ZELDAS_LETTER) = ITEM_CHICKEN;

        for (j = 1; j < 4; j++) {
            if (gSaveContext.save.info.equips.buttonItems[j] == ITEM_ZELDAS_LETTER) {
                gSaveContext.save.info.equips.buttonItems[j] = ITEM_CHICKEN;
            }
        }
    }

    if (LINK_AGE_IN_YEARS == YEARS_ADULT && !CHECK_OWNED_EQUIP(EQUIP_TYPE_SWORD, EQUIP_INV_SWORD_MASTER)) {
        gSaveContext.save.info.inventory.equipment |= OWNED_EQUIP_FLAG(EQUIP_TYPE_SWORD, EQUIP_INV_SWORD_MASTER);
#if OOT_VERSION >= NTSC_1_1
        gSaveContext.save.info.equips.buttonItems[0] = ITEM_SWORD_MASTER;
        gSaveContext.save.info.equips.equipment &= ~(0xF << (EQUIP_TYPE_SWORD * 4));
        gSaveContext.save.info.equips.equipment |= EQUIP_VALUE_SWORD_MASTER << (EQUIP_TYPE_SWORD * 4);
#endif
    }

    for (i = 0; i < ARRAY_COUNT(gSpoilingItems); i++) {
        if (INV_CONTENT(ITEM_TRADE_ADULT) == gSpoilingItems[i]) {
            INV_CONTENT(gSpoilingItemReverts[i]) = gSpoilingItemReverts[i];

            for (j = 1; j < 4; j++) {
                if (gSaveContext.save.info.equips.buttonItems[j] == gSpoilingItems[i]) {
                    gSaveContext.save.info.equips.buttonItems[j] = gSpoilingItemReverts[i];
                }
            }
        }
    }

    gSaveContext.save.info.playerData.magicLevel = 0;
}

/**
 *  Write the contents of the Save Context to a main and backup slot in SRAM.
 *  Note: The whole Save Context is written even though only the `save` substruct is read back later
 */
void Sram_WriteSave(SramContext* sramCtx) {
    u16 offset;
    u16 checksum;
    u16 j;
    u16* ptr;

    gSaveContext.save.info.checksum.value = 0;

    ptr = (u16*)&gSaveContext;
    checksum = j = 0;

    for (offset = 0; offset < CHECKSUM_SIZE; offset++) {
        if (++j == 0x20) {
            j = 0;
        }
        checksum += *ptr++;
    }

    gSaveContext.save.info.checksum.value = checksum;

    ptr = (u16*)&gSaveContext;
    checksum = 0;

    for (offset = 0; offset < CHECKSUM_SIZE; offset++) {
        if (++j == 0x20) {
            j = 0;
        }
        checksum += *ptr++;
    }

    offset = gSramSlotOffsets[gSaveContext.fileNum];
    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + offset, &gSaveContext, SLOT_SIZE);

    ptr = (u16*)&gSaveContext;
    checksum = 0;

    for (offset = 0; offset < CHECKSUM_SIZE; offset++) {
        if (++j == 0x20) {
            j = 0;
        }
        checksum += *ptr++;
    }

    offset = gSramSlotOffsets[gSaveContext.fileNum + 3];
    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + offset, &gSaveContext, SLOT_SIZE);
}

/**
 *  For all 3 slots, verify that the checksum is correct. If corrupted, attempt to load a backup save.
 *  If backup is also corrupted, default to a new save (or debug save for slot 0 on debug rom).
 *
 *  After verifying all 3 saves, pass relevant data to File Select to be displayed.
 */
void Sram_VerifyAndLoadAllSaves(FileSelectState* fileSelect, SramContext* sramCtx) {
    u16 i;
    u16 newChecksum;
    u16 slotNum;
    u16 offset;
    u16 j;
    u16 oldChecksum;
    u16* ptr;
    u16 dayTime;

    PRINTF("ＳＲＡＭ ＳＴＡＲＴ─ＬＯＡＤ\n");
    bzero(sramCtx->readBuff, SRAM_SIZE);
    SRAM_READ(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);

    dayTime = ((void)0, gSaveContext.save.dayTime);

    for (slotNum = 0; slotNum < 3; slotNum++) {
        offset = gSramSlotOffsets[slotNum];
        PRINTF(T("ぽいんと＝%x(%d)    SAVE_MAX=%d\n", "Point=%x(%d)    SAVE_MAX=%d\n"), offset, gSaveContext.fileNum,
               sizeof(Save));
        MemCpy(&gSaveContext, sramCtx->readBuff + offset, sizeof(Save));

        oldChecksum = gSaveContext.save.info.checksum.value;
        gSaveContext.save.info.checksum.value = 0;
        ptr = (u16*)&gSaveContext;
        PRINTF("\n＝＝＝＝＝＝＝＝＝＝＝＝＝  Ｓ（%d） ＝＝＝＝＝＝＝＝＝＝＝＝＝\n", slotNum);

        for (i = newChecksum = j = 0; i < CHECKSUM_SIZE; i++, offset += 2) {
#if OOT_VERSION < PAL_1_0
            if (j) {}
            j += 2;
            if (j == 0x20) {
                j = 0;
            }
#endif
            newChecksum += *ptr++;
        }

        PRINTF(T("\nＳＡＶＥチェックサム計算  j=%x  mmm=%x  ", "\nSAVE checksum calculation  j=%x  mmm=%x  "),
               newChecksum, oldChecksum);

        if (newChecksum != oldChecksum) {
            // checksum didnt match, try backup save
            PRINTF("ＥＲＲＯＲ！！！ ＝ %x(%d)\n", gSramSlotOffsets[slotNum], slotNum);
            offset = gSramSlotOffsets[slotNum + 3];
            MemCpy(&gSaveContext, sramCtx->readBuff + offset, sizeof(Save));

            oldChecksum = gSaveContext.save.info.checksum.value;
            gSaveContext.save.info.checksum.value = 0;
            ptr = (u16*)&gSaveContext;
            PRINTF("================= ＢＡＣＫ─ＵＰ ========================\n");

            for (i = newChecksum = j = 0; i < CHECKSUM_SIZE; i++, offset += 2) {
#if OOT_VERSION < PAL_1_0
                if (j) {}
                j += 2;
                if (j == 0x20) {
                    j = 0;
                }
#endif
                newChecksum += *ptr++;
            }
            PRINTF(T("\n（Ｂ）ＳＡＶＥチェックサム計算  j=%x  mmm=%x  ",
                     "\n(B) SAVE checksum calculation  j=%x  mmm=%x  "),
                   newChecksum, oldChecksum);

            if (newChecksum != oldChecksum) {
                // backup save didnt work, make new save
                PRINTF("ＥＲＲＯＲ！！！ ＝ %x(%d+3)\n", gSramSlotOffsets[slotNum + 3], slotNum);
                bzero(&gSaveContext.save.entranceIndex, sizeof(s32));
                bzero(&gSaveContext.save.linkAge, sizeof(s32));
                bzero(&gSaveContext.save.cutsceneIndex, sizeof(s32));
                //! @bug gSaveContext.save.dayTime is a u16 but is cleared as a 32-bit value. This is harmless as-is
                //! since it is followed by nightFlag which is also reset here, but can become an issue if the save
                //! layout is changed.
                bzero(&gSaveContext.save.dayTime, sizeof(s32));
                bzero(&gSaveContext.save.nightFlag, sizeof(s32));
                bzero(&gSaveContext.save.totalDays, sizeof(s32));
                bzero(&gSaveContext.save.bgsDayCount, sizeof(s32));

#if DEBUG_FEATURES
                if (!slotNum) {
                    Sram_InitDebugSave();
                    gSaveContext.save.info.playerData.newf[0] = 'Z';
                    gSaveContext.save.info.playerData.newf[1] = 'E';
                    gSaveContext.save.info.playerData.newf[2] = 'L';
                    gSaveContext.save.info.playerData.newf[3] = 'D';
                    gSaveContext.save.info.playerData.newf[4] = 'A';
                    gSaveContext.save.info.playerData.newf[5] = 'Z';
                    PRINTF("newf=%x,%x,%x,%x,%x,%x\n", gSaveContext.save.info.playerData.newf[0],
                           gSaveContext.save.info.playerData.newf[1], gSaveContext.save.info.playerData.newf[2],
                           gSaveContext.save.info.playerData.newf[3], gSaveContext.save.info.playerData.newf[4],
                           gSaveContext.save.info.playerData.newf[5]);
                } else {
                    Sram_InitNewSave();
                }
#else
                Sram_InitNewSave();
#endif

                ptr = (u16*)&gSaveContext;
                PRINTF("\n--------------------------------------------------------------\n");

                for (i = newChecksum = j = 0; i < CHECKSUM_SIZE; i++) {
                    PRINTF("%x ", *ptr);
                    if (++j == 0x20) {
                        PRINTF("\n");
                        j = 0;
                    }
                    newChecksum += *ptr++;
                }

                gSaveContext.save.info.checksum.value = newChecksum;
                PRINTF("\nCheck_Sum=%x(%x)\n", gSaveContext.save.info.checksum.value, newChecksum);

                i = gSramSlotOffsets[slotNum + 3];
                SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + i, &gSaveContext, SLOT_SIZE);

                //! @bug The ??= below is interpreted as a trigraph for # by IDO, so we escape it
                // FIXED: Changed from "??????=%x..." to "?\??\??\??\?=%x..." to prevent trigraph compilation error
                // Original Japanese characters were causing trigraph warnings in modern compilers
                PRINTF("?\??\??\??\?=%x,%x,%x,%x,%x,%x\n", gSaveContext.save.info.playerData.newf[0],
                       gSaveContext.save.info.playerData.newf[1], gSaveContext.save.info.playerData.newf[2],
                       gSaveContext.save.info.playerData.newf[3], gSaveContext.save.info.playerData.newf[4],
                       gSaveContext.save.info.playerData.newf[5]);
                PRINTF(T("\nぽいんと＝%x(%d+3)  check_sum=%x(%x)\n", "\npoints=%x(%d+3) check_sum=%x(%x)\n"), i,
                       slotNum, gSaveContext.save.info.checksum.value, newChecksum);
            }

            i = gSramSlotOffsets[slotNum];
            SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + i, &gSaveContext, SLOT_SIZE);

            PRINTF(T("ぽいんと＝%x(%d)  check_sum=%x(%x)\n", "point=%x(%d) check_sum=%x(%x)\n"), i, slotNum,
                   gSaveContext.save.info.checksum.value, newChecksum);
        } else {
            PRINTF(T("\nＳＡＶＥデータ ＯＫ！！！！\n", "\nSAVE data OK!!!!\n"));
        }
    }

    bzero(sramCtx->readBuff, SRAM_SIZE);
    SRAM_READ(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);
    gSaveContext.save.dayTime = dayTime;

    PRINTF("SAVECT=%x, NAME=%x, LIFE=%x, ITEM=%x,  64DD=%x,  HEART=%x\n", DEATHS, NAME, HEALTH_CAP, QUEST, N64DD,
           DEFENSE);

    MemCpy(&fileSelect->deaths[0], sramCtx->readBuff + SLOT_OFFSET(0) + DEATHS, sizeof(fileSelect->deaths[0]));
    MemCpy(&fileSelect->deaths[1], sramCtx->readBuff + SLOT_OFFSET(1) + DEATHS, sizeof(fileSelect->deaths[0]));
    MemCpy(&fileSelect->deaths[2], sramCtx->readBuff + SLOT_OFFSET(2) + DEATHS, sizeof(fileSelect->deaths[0]));

    MemCpy(&fileSelect->fileNames[0], sramCtx->readBuff + SLOT_OFFSET(0) + NAME, sizeof(fileSelect->fileNames[0]));
    MemCpy(&fileSelect->fileNames[1], sramCtx->readBuff + SLOT_OFFSET(1) + NAME, sizeof(fileSelect->fileNames[0]));
    MemCpy(&fileSelect->fileNames[2], sramCtx->readBuff + SLOT_OFFSET(2) + NAME, sizeof(fileSelect->fileNames[0]));

    MemCpy(&fileSelect->healthCapacities[0], sramCtx->readBuff + SLOT_OFFSET(0) + HEALTH_CAP,
           sizeof(fileSelect->healthCapacities[0]));
    MemCpy(&fileSelect->healthCapacities[1], sramCtx->readBuff + SLOT_OFFSET(1) + HEALTH_CAP,
           sizeof(fileSelect->healthCapacities[0]));
    MemCpy(&fileSelect->healthCapacities[2], sramCtx->readBuff + SLOT_OFFSET(2) + HEALTH_CAP,
           sizeof(fileSelect->healthCapacities[0]));

    MemCpy(&fileSelect->questItems[0], sramCtx->readBuff + SLOT_OFFSET(0) + QUEST, sizeof(fileSelect->questItems[0]));
    MemCpy(&fileSelect->questItems[1], sramCtx->readBuff + SLOT_OFFSET(1) + QUEST, sizeof(fileSelect->questItems[0]));
    MemCpy(&fileSelect->questItems[2], sramCtx->readBuff + SLOT_OFFSET(2) + QUEST, sizeof(fileSelect->questItems[0]));

    MemCpy(&fileSelect->n64ddFlags[0], sramCtx->readBuff + SLOT_OFFSET(0) + N64DD, sizeof(fileSelect->n64ddFlags[0]));
    MemCpy(&fileSelect->n64ddFlags[1], sramCtx->readBuff + SLOT_OFFSET(1) + N64DD, sizeof(fileSelect->n64ddFlags[0]));
    MemCpy(&fileSelect->n64ddFlags[2], sramCtx->readBuff + SLOT_OFFSET(2) + N64DD, sizeof(fileSelect->n64ddFlags[0]));

    MemCpy(&fileSelect->defense[0], sramCtx->readBuff + SLOT_OFFSET(0) + DEFENSE, sizeof(fileSelect->defense[0]));
    MemCpy(&fileSelect->defense[1], sramCtx->readBuff + SLOT_OFFSET(1) + DEFENSE, sizeof(fileSelect->defense[0]));
    MemCpy(&fileSelect->defense[2], sramCtx->readBuff + SLOT_OFFSET(2) + DEFENSE, sizeof(fileSelect->defense[0]));

#if OOT_PAL
    MemCpy(&fileSelect->health[0], sramCtx->readBuff + SLOT_OFFSET(0) + HEALTH, sizeof(fileSelect->health[0]));
    MemCpy(&fileSelect->health[1], sramCtx->readBuff + SLOT_OFFSET(1) + HEALTH, sizeof(fileSelect->health[0]));
    MemCpy(&fileSelect->health[2], sramCtx->readBuff + SLOT_OFFSET(2) + HEALTH, sizeof(fileSelect->health[0]));
#endif

    PRINTF("f_64dd=%d, %d, %d\n", fileSelect->n64ddFlags[0], fileSelect->n64ddFlags[1], fileSelect->n64ddFlags[2]);
    PRINTF("heart_status=%d, %d, %d\n", fileSelect->defense[0], fileSelect->defense[1], fileSelect->defense[2]);
#if OOT_PAL
    PRINTF("now_life=%d, %d, %d\n", fileSelect->health[0], fileSelect->health[1], fileSelect->health[2]);
#endif
}

void Sram_InitSave(FileSelectState* fileSelect, SramContext* sramCtx) {
    u16 offset;
    u16 j;
    u16* ptr;
    u16 checksum;

#if DEBUG_FEATURES
    if (fileSelect->buttonIndex != 0) {
        Sram_InitNewSave();
    } else {
        Sram_InitDebugSave();
    }
#else
    Sram_InitNewSave();
#endif

    gSaveContext.save.entranceIndex = ENTR_HYRULE_FIELD_0;
    gSaveContext.save.linkAge = LINK_AGE_CHILD;
    gSaveContext.save.dayTime = CLOCK_TIME(21, 0); // Start at 9 PM (nighttime)
    gSaveContext.save.cutsceneIndex = CS_INDEX_NONE;

#if DEBUG_FEATURES
    if (fileSelect->buttonIndex == 0) {
        gSaveContext.save.cutsceneIndex = CS_INDEX_NONE;
    }
#endif

    for (offset = 0; offset < 8; offset++) {
#if !PLATFORM_IQUE
        gSaveContext.save.info.playerData.playerName[offset] = fileSelect->fileNames[fileSelect->buttonIndex][offset];
#else
        // Workaround for EGCS internal compiler error (see docs/compilers.md)
        u8* fileName = fileSelect->fileNames[fileSelect->buttonIndex];

        gSaveContext.save.info.playerData.playerName[offset] = fileName[offset];
#endif
    }

    gSaveContext.save.info.playerData.newf[0] = 'Z';
    gSaveContext.save.info.playerData.newf[1] = 'E';
    gSaveContext.save.info.playerData.newf[2] = 'L';
    gSaveContext.save.info.playerData.newf[3] = 'D';
    gSaveContext.save.info.playerData.newf[4] = 'A';
    gSaveContext.save.info.playerData.newf[5] = 'Z';

    gSaveContext.save.info.playerData.n64ddFlag = fileSelect->n64ddFlag;
    PRINTF(T("６４ＤＤフラグ=%d\n", "64DD flags=%d\n"), fileSelect->n64ddFlag);
    PRINTF("newf=%x,%x,%x,%x,%x,%x\n", gSaveContext.save.info.playerData.newf[0],
           gSaveContext.save.info.playerData.newf[1], gSaveContext.save.info.playerData.newf[2],
           gSaveContext.save.info.playerData.newf[3], gSaveContext.save.info.playerData.newf[4],
           gSaveContext.save.info.playerData.newf[5]);
    PRINTF("\n$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n");

    ptr = (u16*)&gSaveContext;

    for (j = 0, checksum = 0, offset = 0; offset < CHECKSUM_SIZE; offset++) {
        PRINTF("%x ", *ptr);
        checksum += *ptr++;
        if (++j == 0x20) {
            PRINTF("\n");
            j = 0;
        }
    }

    gSaveContext.save.info.checksum.value = checksum;
    PRINTF(T("\nチェックサム＝%x\n", "\nChecksum = %x\n"), gSaveContext.save.info.checksum.value);

    offset = gSramSlotOffsets[gSaveContext.fileNum];
    PRINTF("I=%x no=%d\n", offset, gSaveContext.fileNum);
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));

    offset = gSramSlotOffsets[gSaveContext.fileNum + 3];
    PRINTF("I=%x no=%d\n", offset, gSaveContext.fileNum + 3);
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));

    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);

    PRINTF(T("ＳＡＶＥ終了\n", "SAVE end\n"));
    PRINTF("z_common_data.file_no = %d\n", gSaveContext.fileNum);
    PRINTF("SAVECT=%x, NAME=%x, LIFE=%x, ITEM=%x,  SAVE_64DD=%x\n", DEATHS, NAME, HEALTH_CAP, QUEST, N64DD);

    j = gSramSlotOffsets[gSaveContext.fileNum];

    MemCpy(&fileSelect->deaths[gSaveContext.fileNum], sramCtx->readBuff + j + DEATHS, sizeof(fileSelect->deaths[0]));
    MemCpy(&fileSelect->fileNames[gSaveContext.fileNum], sramCtx->readBuff + j + NAME,
           sizeof(fileSelect->fileNames[0]));
    MemCpy(&fileSelect->healthCapacities[gSaveContext.fileNum], sramCtx->readBuff + j + HEALTH_CAP,
           sizeof(fileSelect->healthCapacities[0]));
    MemCpy(&fileSelect->questItems[gSaveContext.fileNum], sramCtx->readBuff + j + QUEST,
           sizeof(fileSelect->questItems[0]));
    MemCpy(&fileSelect->n64ddFlags[gSaveContext.fileNum], sramCtx->readBuff + j + N64DD,
           sizeof(fileSelect->n64ddFlags[0]));
    MemCpy(&fileSelect->defense[gSaveContext.fileNum], sramCtx->readBuff + j + DEFENSE, sizeof(fileSelect->defense[0]));
#if OOT_PAL
    MemCpy(&fileSelect->health[gSaveContext.fileNum], sramCtx->readBuff + j + HEALTH, sizeof(fileSelect->health[0]));
#endif

    PRINTF("f_64dd[%d]=%d\n", gSaveContext.fileNum, fileSelect->n64ddFlags[gSaveContext.fileNum]);
    PRINTF("heart_status[%d]=%d\n", gSaveContext.fileNum, fileSelect->defense[gSaveContext.fileNum]);
#if OOT_PAL
    PRINTF("now_life[%d]=%d\n", gSaveContext.fileNum, fileSelect->health[gSaveContext.fileNum]);
#endif
}

void Sram_EraseSave(FileSelectState* fileSelect, SramContext* sramCtx) {
    u16 offset;

    Sram_InitNewSave();

    offset = gSramSlotOffsets[fileSelect->selectedFileIndex];
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));
    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + offset, &gSaveContext, SLOT_SIZE);

    MemCpy(&fileSelect->n64ddFlags[fileSelect->selectedFileIndex], sramCtx->readBuff + offset + N64DD,
           sizeof(fileSelect->n64ddFlags[0]));

    offset = gSramSlotOffsets[fileSelect->selectedFileIndex + 3];
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));
    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000) + offset, &gSaveContext, SLOT_SIZE);

    PRINTF(T("ＣＬＥＡＲ終了\n", "CLEAR END\n"));
}

void Sram_CopySave(FileSelectState* fileSelect, SramContext* sramCtx) {
    u16 offset;

    PRINTF("ＲＥＡＤ=%d(%x)  ＣＯＰＹ=%d(%x)\n", fileSelect->selectedFileIndex,
           gSramSlotOffsets[fileSelect->selectedFileIndex], fileSelect->copyDestFileIndex,
           gSramSlotOffsets[fileSelect->copyDestFileIndex]);

    offset = gSramSlotOffsets[fileSelect->selectedFileIndex];
    MemCpy(&gSaveContext, sramCtx->readBuff + offset, sizeof(Save));

    offset = gSramSlotOffsets[fileSelect->copyDestFileIndex];
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));

    offset = gSramSlotOffsets[fileSelect->copyDestFileIndex + 3];
    MemCpy(sramCtx->readBuff + offset, &gSaveContext, sizeof(Save));

    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);

    offset = gSramSlotOffsets[fileSelect->copyDestFileIndex];

    MemCpy(&fileSelect->deaths[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + DEATHS,
           sizeof(fileSelect->deaths[0]));
    MemCpy(&fileSelect->fileNames[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + NAME,
           sizeof(fileSelect->fileNames[0]));
    MemCpy(&fileSelect->healthCapacities[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + HEALTH_CAP,
           sizeof(fileSelect->healthCapacities[0]));
    MemCpy(&fileSelect->questItems[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + QUEST,
           sizeof(fileSelect->questItems[0]));
    MemCpy(&fileSelect->n64ddFlags[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + N64DD,
           sizeof(fileSelect->n64ddFlags[0]));
    MemCpy(&fileSelect->defense[fileSelect->copyDestFileIndex], sramCtx->readBuff + offset + DEFENSE,
           sizeof(fileSelect->defense[0]));
#if OOT_PAL
    MemCpy(&fileSelect->health[fileSelect->copyDestFileIndex], (sramCtx->readBuff + offset) + HEALTH,
           sizeof(fileSelect->health[0]));
#endif

    PRINTF("f_64dd[%d]=%d\n", gSaveContext.fileNum, fileSelect->n64ddFlags[gSaveContext.fileNum]);
    PRINTF("heart_status[%d]=%d\n", gSaveContext.fileNum, fileSelect->defense[gSaveContext.fileNum]);
    PRINTF(T("ＣＯＰＹ終了\n", "Copy end\n"));
}

/**
 *  Write the first 16 bytes of the read buffer to the SRAM header
 */
void Sram_WriteSramHeader(SramContext* sramCtx) {
    SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_HEADER_SIZE);
}

void Sram_InitSram(GameState* gameState, SramContext* sramCtx) {
    u16 i;

    PRINTF("sram_initialize( Game *game, Sram *sram )\n");
    SRAM_READ(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);

    for (i = 0; i < ARRAY_COUNTU(sSramDefaultHeader) - SRAM_HEADER_MAGIC; i++) {
        if (sSramDefaultHeader[i + SRAM_HEADER_MAGIC] != sramCtx->readBuff[i + SRAM_HEADER_MAGIC]) {
            PRINTF(T("ＳＲＡＭ破壊！！！！！！\n", "SRAM destruction!!!!!!\n"));
#if PLATFORM_GC && OOT_PAL
            gSaveContext.language = sramCtx->readBuff[SRAM_HEADER_LANGUAGE];
#endif

            MemCpy(sramCtx->readBuff, sSramDefaultHeader, sizeof(sSramDefaultHeader));

#if PLATFORM_GC && OOT_PAL
            sramCtx->readBuff[SRAM_HEADER_LANGUAGE] = gSaveContext.language;
#endif
            Sram_WriteSramHeader(sramCtx);
        }
    }

    gSaveContext.soundSetting = sramCtx->readBuff[SRAM_HEADER_SOUND] & 3;
    gSaveContext.zTargetSetting = sramCtx->readBuff[SRAM_HEADER_Z_TARGET] & 1;

#if OOT_PAL
    gSaveContext.language = sramCtx->readBuff[SRAM_HEADER_LANGUAGE];
    if (gSaveContext.language >= LANGUAGE_MAX) {
        gSaveContext.language = LANGUAGE_ENG;
        sramCtx->readBuff[SRAM_HEADER_LANGUAGE] = gSaveContext.language;
        Sram_WriteSramHeader(sramCtx);
    }
#endif

#if DEBUG_FEATURES
    if (CHECK_BTN_ANY(gameState->input[2].cur.button, BTN_DRIGHT)) {
        bzero(sramCtx->readBuff, SRAM_SIZE);
        for (i = 0; i < CHECKSUM_SIZE; i++) {
            sramCtx->readBuff[i] = i;
        }
        SRAM_WRITE(OS_K1_TO_PHYSICAL(0xA8000000), sramCtx->readBuff, SRAM_SIZE);
        PRINTF(T("ＳＲＡＭ破壊！！！！！！\n", "SRAM destruction!!!!!!\n"));
    }
#endif

    PRINTF(T("ＧＯＯＤ！ＧＯＯＤ！ サイズ＝%d + %d ＝ %d\n", "GOOD! GOOD! Size = %d + %d = %d\n"), sizeof(SaveInfo), 4,
           sizeof(SaveInfo) + 4);
    PRINTF_COLOR_BLUE();
    PRINTF("Na_SetSoundOutputMode = %d\n", gSaveContext.soundSetting);
    PRINTF("Na_SetSoundOutputMode = %d\n", gSaveContext.soundSetting);
    PRINTF("Na_SetSoundOutputMode = %d\n", gSaveContext.soundSetting);
    PRINTF_RST();
    Audio_SetSoundOutputMode(gSaveContext.soundSetting);
}

void Sram_Alloc(GameState* gameState, SramContext* sramCtx) {
    sramCtx->readBuff = GAME_STATE_ALLOC(gameState, SRAM_SIZE, "../z_sram.c", 1294);
    ASSERT(sramCtx->readBuff != NULL, "sram->read_buff != NULL", "../z_sram.c", 1295);
}

void Sram_Init(GameState* gameState, SramContext* sramCtx) {
}
