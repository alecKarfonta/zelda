#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// N64 Graphics Command Types (RDP/RSP)
typedef enum {
    // RSP Graphics Commands
    G_NOOP = 0x00,
    G_SETCIMG = 0x01,
    G_SETZIMG = 0x02,
    G_SETTIMG = 0x03,
    G_SETPRIMCOLOR = 0x04,
    G_SETBLENDCOLOR = 0x05,
    G_SETFOGCOLOR = 0x06,
    G_SETFILLCOLOR = 0x07,
    G_FILLRECT = 0x08,
    G_SETTILE = 0x09,
    G_LOADTILE = 0x0A,
    G_LOADBLOCK = 0x0B,
    G_SETTILESIZE = 0x0C,
    G_LOADTLUT = 0x0D,
    G_RDPSETOTHERMODE = 0x0E,
    G_SETPRIMDEPTH = 0x0F,
    G_SETSCISSOR = 0x10,
    G_SETCONVERT = 0x11,
    G_SETKEYR = 0x12,
    G_SETKEYGB = 0x13,
    G_RDPFULLSYNC = 0x14,
    G_RDPTILESYNC = 0x15,
    G_RDPPIPESYNC = 0x16,
    G_RDPLOADSYNC = 0x17,
    G_TEXRECTFLIP = 0x18,
    G_TEXRECT = 0x19,
    G_TRI1 = 0x1A,
    G_TRI2 = 0x1B,
    G_QUAD = 0x1C,
    // RSP Vertex Commands
    G_VTX = 0x84,
    G_MODIFYVTX = 0x85,
    G_CULLDL = 0x86,
    G_BRANCH_Z = 0x87,
    G_TRI1_LBL = 0x88,
    G_TRI2_LBL = 0x89,
    G_QUAD_LBL = 0x8A,
    G_SPECIAL_3 = 0x8B,
    G_SPECIAL_2 = 0x8C,
    G_SPECIAL_1 = 0x8D,
    G_DMA_IO = 0x8E,
    G_TEXTURE = 0x8F,
    G_POPMTX = 0x90,
    G_GEOMETRYMODE = 0x91,
    G_MTX = 0x92,
    G_MOVEWORD = 0x93,
    G_MOVEMEM = 0x94,
    G_LOAD_UCODE = 0x95,
    G_DL = 0x96,
    G_ENDDL = 0x97,
    G_SPNOOP = 0x98,
    G_RDPHALF_1 = 0x99,
    G_SETOTHERMODE_L = 0x9A,
    G_SETOTHERMODE_H = 0x9B,
    G_TEXRECT_WIDE = 0x9C,
    G_TEXRECTFLIP_WIDE = 0x9D,
    G_RDPHALF_2 = 0x9E,
    G_RDPHALF_CONT = 0x9F
} N64GraphicsCommand;

// N64 Texture Formats
typedef enum {
    G_IM_FMT_RGBA = 0,
    G_IM_FMT_YUV = 1,
    G_IM_FMT_CI = 2,
    G_IM_FMT_IA = 3,
    G_IM_FMT_I = 4
} N64TextureFormat;

// N64 Texture Sizes
typedef enum {
    G_IM_SIZ_4b = 0,
    G_IM_SIZ_8b = 1,
    G_IM_SIZ_16b = 2,
    G_IM_SIZ_32b = 3
} N64TextureSize;

// N64 Combiner Modes
typedef enum {
    G_CC_MODULATEI = 0,
    G_CC_MODULATEIA = 1,
    G_CC_MODULATEIDECALA = 2,
    G_CC_MODULATERGB = 3,
    G_CC_MODULATERGBA = 4,
    G_CC_MODULATERGBDECALA = 5,
    G_CC_DECALRGB = 6,
    G_CC_DECALRGBA = 7,
    G_CC_BLENDI = 8,
    G_CC_BLENDIA = 9,
    G_CC_BLENDIDECALA = 10,
    G_CC_BLENDRGBA = 11,
    G_CC_BLENDRGBDECALA = 12,
    G_CC_ADDRGB = 13,
    G_CC_ADDRGBDECALA = 14,
    G_CC_REFLECTRGB = 15,
    G_CC_REFLECTRGBDECALA = 16,
    G_CC_HILITERGB = 17,
    G_CC_HILITERGBA = 18,
    G_CC_HILITERGBDECALA = 19,
    G_CC_SHADERGB = 20,
    G_CC_SHADERGBA = 21,
    G_CC_SHADERGBDECALA = 22,
    G_CC_PRIMITIVE = 23,
    G_CC_SHADE = 24,
    G_CC_ENVIRONMENT = 25,
    G_CC_1 = 26,
    G_CC_0 = 27
} N64CombinerMode;

// Graphics Command Structure
typedef struct {
    uint8_t opcode;
    uint8_t length;
    union {
        struct {
            uint32_t w0;
            uint32_t w1;
        } raw;
        struct {
            uint16_t fmt;
            uint16_t siz;
            uint16_t width;
            uintptr_t addr;
        } setcimg;
        struct {
            uint16_t fmt;
            uint16_t siz;
            uint16_t width;
            uintptr_t addr;
        } setzimg;
        struct {
            uint16_t fmt;
            uint16_t siz;
            uint16_t width;
            uintptr_t addr;
        } settimg;
        struct {
            uint8_t r, g, b, a;
            uint8_t minlod;
            uint8_t primitive_lod_frac;
        } setprimcolor;
        struct {
            uint8_t r, g, b, a;
        } setblendcolor;
        struct {
            uint8_t r, g, b, a;
        } setfogcolor;
        struct {
            uint32_t color;
        } setfillcolor;
        struct {
            uint16_t ulx, uly, lrx, lry;
        } fillrect;
        struct {
            uint8_t tile;
            uint8_t fmt;
            uint8_t siz;
            uint16_t line;
            uint32_t tmem;
            uint8_t palette;
            uint8_t cmt, cms;
            uint8_t maskt, masks;
            uint8_t shiftt, shifts;
        } settile;
        struct {
            uint8_t tile;
            uint16_t uls, ult, lrs, lrt;
        } loadtile;
        struct {
            uint8_t tile;
            uint16_t uls, ult, lrs, dxt;
        } loadblock;
        struct {
            uint8_t tile;
            uint16_t uls, ult, lrs, lrt;
        } settilesize;
        struct {
            uint8_t tile;
            uint16_t count;
        } loadtlut;
        struct {
            uint32_t modehi;
            uint32_t modelo;
        } rdpsetothermode;
        struct {
            uint16_t z;
            uint16_t dz;
        } setprimdepth;
        struct {
            uint16_t ulx, uly, lrx, lry;
        } setscissor;
        struct {
            int32_t k0, k1, k2, k3, k4, k5;
        } setconvert;
        struct {
            uint8_t cR, cG, cB;
            uint8_t sR, sG, sB;
            uint8_t wR, wG, wB;
        } setkeyr;
        struct {
            uint8_t cR, cG, cB;
            uint8_t sR, sG, sB;
            uint8_t wR, wG, wB;
        } setkeygb;
        struct {
            uint8_t tile;
            uint16_t ulx, uly, lrx, lry;
            uint16_t s, t;
            uint16_t dsdx, dtdy;
        } texrect;
        struct {
            uint8_t tile;
            uint16_t ulx, uly, lrx, lry;
            uint16_t s, t;
            uint16_t dsdx, dtdy;
        } texrectflip;
        struct {
            uint8_t v0, v1, v2;
            uint8_t flag;
        } tri1;
        struct {
            uint8_t v0, v1, v2;
            uint8_t flag;
            uint8_t v3, v4, v5;
            uint8_t flag2;
        } tri2;
        struct {
            uint8_t v0, v1, v2, v3;
            uint8_t flag;
        } quad;
        struct {
            uint8_t vbidx;
            uint8_t n;
            uintptr_t addr;
        } vtx;
        struct {
            uint8_t where;
            uint8_t vtx;
            uint32_t val;
        } modifyvtx;
        struct {
            uint8_t vstart;
            uint8_t vend;
        } culldl;
        struct {
            uintptr_t addr;
        } branch_z;
        struct {
            uint8_t tile;
            uint8_t level;
            uint8_t on;
        } texture;
        struct {
            uint8_t n;
        } popmtx;
        struct {
            uint32_t clear;
            uint32_t set;
        } geometrymode;
        struct {
            uint8_t param;
            uint8_t len;
            uintptr_t addr;
        } mtx;
        struct {
            uint8_t type;
            uint16_t offset;
            uint32_t data;
        } moveword;
        struct {
            uint8_t type;
            uint16_t len;
            uintptr_t addr;
        } movemem;
        struct {
            uintptr_t addr;
        } load_ucode;
        struct {
            uint8_t param;
            uintptr_t addr;
        } dl;
        struct {
            uint32_t type;
            uintptr_t addr;
        } dma_io;
        struct {
            uint32_t hi;
            uint32_t lo;
        } rdphalf;
        struct {
            uint32_t modehi;
            uint32_t modelo;
        } setothermode_l;
        struct {
            uint32_t modehi;
            uint32_t modelo;
        } setothermode_h;
    } params;
} GraphicsCommand;

// N64 Vertex Structure
typedef struct {
    int16_t x, y, z;
    int16_t flag;
    int16_t tc[2];
    uint8_t cn[4];
} N64Vertex;

// N64 Matrix Structure
typedef struct {
    int32_t m[4][4];
} N64Matrix;

// N64 Light Structure
typedef struct {
    uint8_t col[3];
    uint8_t pad1;
    uint8_t colc[3];
    uint8_t pad2;
    int8_t dir[3];
    uint8_t pad3;
} N64Light;

// N64 Texture Structure
typedef struct {
    uintptr_t addr;
    uint16_t width;
    uint16_t height;
    uint8_t fmt;
    uint8_t siz;
    uint8_t palette;
    uint8_t flags;
} N64Texture;

// Function declarations for N64 graphics processing
void N64Graphics_ProcessCommand(GraphicsCommand* cmd);
void N64Graphics_ProcessDisplayList(uintptr_t addr);
void N64Graphics_ConvertTexture(N64Texture* tex, uint8_t* output);
void N64Graphics_ConvertVertex(N64Vertex* vtx, float* output);
void N64Graphics_ConvertMatrix(N64Matrix* mtx, float* output);

// N64 graphics system lifecycle
void N64Graphics_Init(void);
void N64Graphics_Shutdown(void);
void N64Graphics_BeginFrame(void);
void N64Graphics_EndFrame(void);

#ifdef __cplusplus
}
#endif 