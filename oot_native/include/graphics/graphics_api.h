#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Include N64 graphics types
#include "n64_graphics.h"

// Forward declarations
typedef struct GraphicsContext GraphicsContext;
typedef struct DisplayList DisplayList;
typedef struct RendererBackend RendererBackend;

// Graphics backend types
typedef enum {
    GRAPHICS_BACKEND_OPENGL,
    GRAPHICS_BACKEND_DIRECTX11,
    GRAPHICS_BACKEND_METAL,
    GRAPHICS_BACKEND_VULKAN,
    GRAPHICS_BACKEND_COUNT
} GraphicsBackend;

// Graphics configuration
typedef struct {
    uint32_t width;
    uint32_t height;
    float aspect_ratio;
    bool vsync;
    bool fullscreen;
    GraphicsBackend backend;
    uint32_t msaa_samples;
    bool hdr_enabled;
} GraphicsConfig;

// Graphics initialization
bool Graphics_Init(GraphicsConfig* config);
void Graphics_Shutdown(void);

// Main graphics processing interface (Ship of Harkinian pattern)
void Graph_ProcessGfxCommands(GraphicsCommand* commands, uint32_t count);
void Graph_ProcessFrame(void);

// Resolution and display management
uint32_t OTRGetCurrentWidth(void);
uint32_t OTRGetCurrentHeight(void);
float OTRGetAspectRatio(void);
bool OTRSetResolution(uint32_t width, uint32_t height);

// Backend management
bool Graphics_SetBackend(GraphicsBackend backend);
GraphicsBackend Graphics_GetCurrentBackend(void);
RendererBackend* Graphics_GetRenderer(void);
const char* Graphics_GetBackendName(GraphicsBackend backend);

// Frame synchronization
void Graphics_BeginFrame(void);
void Graphics_EndFrame(void);
void Graphics_Present(void);

// Debugging and profiling
void Graphics_EnableDebugMode(bool enabled);
void Graphics_GetStats(uint32_t* draw_calls, uint32_t* vertices, uint32_t* triangles);



#ifdef __cplusplus
}
#endif 