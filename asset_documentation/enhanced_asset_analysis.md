# Enhanced Zelda OoT Asset Analysis Report

Generated on: /home/alec/git/zelda

## 🔍 Quick Search Guide

### By Purpose

**UI Elements**:
- `icon_item_static` (186 assets)
- `icon_item_24_static` (20 assets)
- `do_action_static` (58 assets)

**Text/Fonts**:
- `kanji` (3976 assets)
- `nes_font_static` (141 assets)
- `message_static` (9 assets)

**Maps**:
- `map_i_static` (241 assets)
- `map_name_static` (70 assets)
- `map_48x85_static` (70 assets)
- `map_grand_static` (26 assets)

**Backgrounds**:
- `backgrounds` (155 assets)
- `skyboxes` (92 assets)

**Titles**:
- `title_static` (122 assets)
- `place_title_cards` (114 assets)
- `nintendo_rogo_static` (8 assets)

**Items**:
- `item_name_static` (246 assets)
- `parameter_static` (58 assets)

**Messages**:
- `message_static` (9 assets)
- `message_texture_static` (4 assets)

### By Format

**i4** (4448 assets): 4-bit intensity (most common, good for fonts/text)

**ia8** (419 assets): 8-bit intensity + alpha (good for UI elements)

**ci8** (120 assets): 8-bit color index (good for detailed textures)

**rgba16** (5 assets): 16-bit RGBA (good for detailed images)

**rgba32** (114 assets): 32-bit RGBA (highest quality, largest files)

**i8** (20 assets): 8-bit intensity (good for grayscale)

### Quick Filters

- **Largest Files**: Sort by size_bytes descending
- **Most Referenced**: Filter by reference_count > 0
- **Recent Changes**: Sort by modified_time descending
- **Specific Format**: Filter by detected_format
- **UI Elements**: Search directories with 'icon' or 'static'
- **Backgrounds**: Search 'backgrounds' or 'skyboxes' directories

## 📝 Filename Pattern Analysis

### Common Prefixes

- `g_`: 5554 assets
- `icon_`: 8 assets
- `map_`: 8 assets
- `nintendo_`: 6 assets
- `message_`: 4 assets

### Common Words in Filenames

- `Tex`: 5545 assets
- `Msg`: 4113 assets
- `Kanji`: 3975 assets
- `Item`: 357 assets
- `Empty`: 321 assets
- `Name`: 317 assets
- `Minimap`: 263 assets
- `Room`: 239 assets
- `Temple`: 222 assets
- `Pause`: 203 assets
- `File`: 155 assets
- `Halfwidth`: 141 assets
- `Char`: 140 assets
- `Katakana`: 140 assets
- `Map`: 138 assets

### Language Indicators

- `JPN`: 322 assets
- `ENG`: 301 assets

## 🔗 Asset Relationships

### Paired Files (.c and .h)

- `message_texture_static.c` ↔ `message_texture_static.h` (in message_texture_static)
- `icon_item_dungeon_static.c` ↔ `icon_item_dungeon_static.h` (in icon_item_dungeon_static)
- `nintendo_rogo_static.c` ↔ `nintendo_rogo_static.h` (in nintendo_rogo_static)
- `map_name_static.c` ↔ `map_name_static.h` (in map_name_static)
- `nes_font_static.c` ↔ `nes_font_static.h` (in nes_font_static)
- `map_48x85_static.c` ↔ `map_48x85_static.h` (in map_48x85_static)
- `icon_item_gameover_static.c` ↔ `icon_item_gameover_static.h` (in icon_item_gameover_static)
- `icon_item_field_static.c` ↔ `icon_item_field_static.h` (in icon_item_field_static)
- `parameter_static.c` ↔ `parameter_static.h` (in parameter_static)
- `vr_FCVR_pal_static.c` ↔ `vr_FCVR_pal_static.h` (in backgrounds)

### Similar Names (Common Prefixes)

- `message_texture_static.h` ↔ `message_texture_static.c` (prefix: `message_texture_static.`)
- `gRedMessageXRightTex.i4.png` ↔ `gRedMessageXLeftTex.i4.png` (prefix: `gredmessagex`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMapLinkHeadTex.rgba16.png` (prefix: `gdungeonmap`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMapB1ButtonTex.ia8.png` (prefix: `gdungeonmapb`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMapSkullTex.rgba16.png` (prefix: `gdungeonmap`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMapB7ButtonTex.ia8.png` (prefix: `gdungeonmapb`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMapB6ButtonTex.ia8.png` (prefix: `gdungeonmapb`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMap6FButtonTex.ia8.png` (prefix: `gdungeonmap`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMap2FButtonTex.ia8.png` (prefix: `gdungeonmap`)
- `gDungeonMapBlankFloorButtonTex.ia8.png` ↔ `gDungeonMap8FButtonTex.ia8.png` (prefix: `gdungeonmap`)

## 📊 Size Distribution

**tiny (< 10KB)**: 5633 assets
**small (10KB-100KB)**: 81 assets
**medium (100KB-1MB)**: 2 assets

## 🎯 Asset Complexity Analysis

**Simple Assets**: 5462 (small, basic formats)
**Complex Assets**: 254 (large or high-quality formats)
**Unique Assets**: 29 (in small directories)
**Mass Produced**: 5181 (in large directories)

### Most Complex Assets (Top 10)

- `kanji.h`: 0.675 MB ()
- `kanji.c`: 0.626 MB ()
- `map_i_static.h`: 0.054 MB ()
- `gSariasHouse2BgTex.ci8.png`: 0.051 MB (ci8)
- `gMidosHouse2BgTex.ci8.png`: 0.050 MB (ci8)
- `map_i_static.c`: 0.050 MB ()
- `gHouseOfTwins2BgTex.ci8.png`: 0.049 MB (ci8)
- `gLinksHouseBgTex.ci8.png`: 0.048 MB (ci8)
- `gMidosHouse3BgTex.ci8.png`: 0.048 MB (ci8)
- `gKnowItAllBrosHouseBgTex.ci8.png`: 0.048 MB (ci8)

### Unique Assets (Top 10)

- `message_texture_static.h` (in message_texture_static, 4 total)
- `gRedMessageXRightTex.i4.png` (in message_texture_static, 4 total)
- `gRedMessageXLeftTex.i4.png` (in message_texture_static, 4 total)
- `message_texture_static.c` (in message_texture_static, 4 total)
- `nintendo_rogo_static_000029C0_Tex.i8.png` (in nintendo_rogo_static, 8 total)
- `gNintendo64LogoDL.inc.c` (in nintendo_rogo_static, 8 total)
- `nintendo_rogo_static_Tex_001800.i8.png` (in nintendo_rogo_static, 8 total)
- `nintendo_rogo_static.c` (in nintendo_rogo_static, 8 total)
- `gNintendo64LogoVtx.inc.c` (in nintendo_rogo_static, 8 total)
- `nintendo_rogo_static_Tex_000000.i8.png` (in nintendo_rogo_static, 8 total)

## 💡 Usage Tips

1. **Start with directories**: Use the search guide to find relevant directories
2. **Filter by format**: Choose format based on your needs (i4 for text, rgba32 for quality)
3. **Check relationships**: Look for paired .c/.h files or similar named assets
4. **Consider complexity**: Simple assets are easier to work with
5. **Use references**: Assets with code references are actively used
6. **Language matters**: JPN/ENG indicators show localization differences

## 🔧 Technical Details

### Format Specifications

- **i4**: 4-bit intensity, 16 colors, 1:2 compression
- **ia8**: 8-bit intensity + alpha, 256 colors, good for UI
- **ci8**: 8-bit color index, 256 colors, detailed textures
- **rgba16**: 16-bit RGBA, 65K colors, high quality
- **rgba32**: 32-bit RGBA, 16M colors, highest quality
- **i8**: 8-bit intensity, 256 grayscale levels

### Directory Structure

Assets are organized by function:
- `*_static`: UI elements and interface components
- `*_jpn`: Japanese localization assets
- `*_nes`: English/NES-style assets
- `backgrounds`: Environmental textures
- `skyboxes`: Sky textures for outdoor scenes
- `kanji`: Japanese text rendering
