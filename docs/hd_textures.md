# HD Textures

This document describes the requirements and format for HD textures in the Zelda OoT decompilation project.

## Overview

The HD texture system allows replacing original textures with higher resolution versions. The system automatically slices large HD textures into smaller chunks that can be efficiently loaded by the N64.

## File Format

HD textures should be provided as PNG files with either a `.ss` or `.hd` extension. For example:
- `nintendo_rogo_static.ss`
- `nintendo_rogo_static.hd`

## Texture Requirements

1. **Dimensions**
   - HD texture dimensions must be exact multiples of the original texture dimensions
   - The scale factor must be consistent in both width and height
   - Common scale factors are 2x, 3x, or 4x
   - Example: If original is 256×128, HD version could be 768×384 (3x scale)

2. **Slicing**
   - HD textures are automatically sliced into smaller chunks
   - Default slice size is 64×32 pixels
   - Texture dimensions must be multiples of the slice size
   - Slices are arranged in a 2D array accessed as `texture_name_hd_slices[y][x]`

3. **Color Format**
   - PNG format with appropriate color depth matching original texture
   - For N64 logo: 8-bit grayscale (i8 format)
   - Other formats: Match original texture format (i4, i8, ia4, ia8, ia16, rgba16, rgba32)

## Example: Nintendo Logo

The Nintendo logo texture provides a good example of the requirements:

- Original texture: 256×128 pixels
- HD texture: 768×128 pixels (3x horizontal scale)
- Format: 8-bit grayscale (i8)
- Slicing: Creates 4×12 array of 64×32 slices

## Adding New HD Textures

1. Create your HD texture following the requirements above
2. Place the file in the appropriate texture directory with `.ss` or `.hd` extension
3. The build system will automatically:
   - Validate the texture dimensions
   - Slice into appropriate chunks
   - Generate necessary header and implementation files
   - Link the HD texture into the ROM

## Validation

The texture slicer tool performs several validations:

1. Checks that HD dimensions are multiples of original dimensions
2. Verifies the scale factor is consistent
3. Ensures dimensions are multiples of slice size
4. Validates color format matches original

## Command Line Options

The texture slicer supports several options for customization:

```
slice_hd_texture <input_file> [options]
  --target-width=N    Target slice width (default: 64)
  --target-height=N   Target slice height (default: 32)
  --original-width=N  Original texture width for validation
  --original-height=N Original texture height for validation
  --scale=N          Expected scale factor (default: 3)
```

## Implementation Details

The HD texture system uses a weak symbol fallback mechanism:

```c
// Fallback when HD texture is not present
__attribute__((weak)) u8* texture_name_hd_slices[height][width];
```

This allows the game to gracefully fall back to the original texture if no HD version is provided. 