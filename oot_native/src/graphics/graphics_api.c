#include "graphics/graphics_api.h"
#include "graphics/renderer_backend.h"
#include "graphics/n64_graphics.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Global graphics state
typedef struct {
    bool initialized;
    GraphicsConfig config;
    RendererBackend* current_backend;
    
    // Statistics
    uint32_t frame_count;
    uint32_t draw_calls;
    uint32_t vertices;
    uint32_t triangles;
    
    // Debug mode
    bool debug_enabled;
    
    // Error handling
    char error_string[256];
} GraphicsState;

static GraphicsState g_graphics_state = {0};

// Helper function to set error
static void Graphics_SetError(const char* error) {
    if (error) {
        strncpy(g_graphics_state.error_string, error, sizeof(g_graphics_state.error_string) - 1);
        g_graphics_state.error_string[sizeof(g_graphics_state.error_string) - 1] = '\0';
    } else {
        g_graphics_state.error_string[0] = '\0';
    }
}

// Graphics initialization
bool Graphics_Init(GraphicsConfig* config) {
    if (g_graphics_state.initialized) {
        Graphics_SetError("Graphics already initialized");
        return false;
    }
    
    if (!config) {
        Graphics_SetError("Invalid configuration");
        return false;
    }
    
    // Copy configuration
    g_graphics_state.config = *config;
    
    // Create the appropriate backend
    RendererBackend* backend = NULL;
    switch (config->backend) {
        case GRAPHICS_BACKEND_OPENGL:
            backend = Renderer_CreateOpenGLBackend();
            break;
        case GRAPHICS_BACKEND_DIRECTX11:
            backend = Renderer_CreateDirectX11Backend();
            break;
        case GRAPHICS_BACKEND_METAL:
            backend = Renderer_CreateMetalBackend();
            break;
        case GRAPHICS_BACKEND_VULKAN:
            backend = Renderer_CreateVulkanBackend();
            break;
        default:
            Graphics_SetError("Unsupported graphics backend");
            return false;
    }
    
    if (!backend) {
        Graphics_SetError("Failed to create renderer backend");
        return false;
    }
    
    // Initialize the backend
    if (!backend->init(backend, config)) {
        Graphics_SetError("Failed to initialize renderer backend");
        Renderer_DestroyBackend(backend);
        return false;
    }
    
    g_graphics_state.current_backend = backend;
    g_graphics_state.initialized = true;
    
    // Clear statistics
    g_graphics_state.frame_count = 0;
    g_graphics_state.draw_calls = 0;
    g_graphics_state.vertices = 0;
    g_graphics_state.triangles = 0;
    
    Graphics_SetError(NULL);
    return true;
}

void Graphics_Shutdown(void) {
    if (!g_graphics_state.initialized) {
        return;
    }
    
    if (g_graphics_state.current_backend) {
        g_graphics_state.current_backend->shutdown(g_graphics_state.current_backend);
        Renderer_DestroyBackend(g_graphics_state.current_backend);
        g_graphics_state.current_backend = NULL;
    }
    
    g_graphics_state.initialized = false;
    Graphics_SetError(NULL);
}

// Main graphics processing interface (Ship of Harkinian pattern)
void Graph_ProcessGfxCommands(GraphicsCommand* commands, uint32_t count) {
    if (!g_graphics_state.initialized || !g_graphics_state.current_backend) {
        return;
    }
    
    RendererBackend* backend = g_graphics_state.current_backend;
    
    // Process each command
    for (uint32_t i = 0; i < count; i++) {
        GraphicsCommand* cmd = &commands[i];
        
        if (g_graphics_state.debug_enabled) {
            printf("Processing N64 command: 0x%02X\n", cmd->opcode);
        }
        
        // Let the backend process the N64 command
        if (backend->process_n64_command) {
            backend->process_n64_command(backend, cmd);
        }
        
        // Update statistics based on command type
        switch (cmd->opcode) {
            case G_TRI1:
                g_graphics_state.draw_calls++;
                g_graphics_state.triangles++;
                g_graphics_state.vertices += 3;
                break;
            case G_TRI2:
                g_graphics_state.draw_calls++;
                g_graphics_state.triangles += 2;
                g_graphics_state.vertices += 6;
                break;
            case G_QUAD:
                g_graphics_state.draw_calls++;
                g_graphics_state.triangles += 2;
                g_graphics_state.vertices += 4;
                break;
        }
    }
}

void Graph_ProcessFrame(void) {
    if (!g_graphics_state.initialized || !g_graphics_state.current_backend) {
        return;
    }
    
    // Process frame with the current backend
    // This is called after Graph_ProcessGfxCommands to finalize the frame
    g_graphics_state.frame_count++;
}

// Resolution and display management
uint32_t OTRGetCurrentWidth(void) {
    return g_graphics_state.config.width;
}

uint32_t OTRGetCurrentHeight(void) {
    return g_graphics_state.config.height;
}

float OTRGetAspectRatio(void) {
    return g_graphics_state.config.aspect_ratio;
}

bool OTRSetResolution(uint32_t width, uint32_t height) {
    if (!g_graphics_state.initialized) {
        Graphics_SetError("Graphics not initialized");
        return false;
    }
    
    if (width == 0 || height == 0) {
        Graphics_SetError("Invalid resolution");
        return false;
    }
    
    // Update configuration
    g_graphics_state.config.width = width;
    g_graphics_state.config.height = height;
    g_graphics_state.config.aspect_ratio = (float)width / (float)height;
    
    // Update backend viewport
    if (g_graphics_state.current_backend && g_graphics_state.current_backend->viewport) {
        g_graphics_state.current_backend->viewport(g_graphics_state.current_backend, 0, 0, width, height);
    }
    
    return true;
}

// Backend management
bool Graphics_SetBackend(GraphicsBackend backend) {
    if (!g_graphics_state.initialized) {
        Graphics_SetError("Graphics not initialized");
        return false;
    }
    
    if (g_graphics_state.config.backend == backend) {
        return true; // Already using this backend
    }
    
    // Create new backend
    RendererBackend* new_backend = NULL;
    switch (backend) {
        case GRAPHICS_BACKEND_OPENGL:
            new_backend = Renderer_CreateOpenGLBackend();
            break;
        case GRAPHICS_BACKEND_DIRECTX11:
            new_backend = Renderer_CreateDirectX11Backend();
            break;
        case GRAPHICS_BACKEND_METAL:
            new_backend = Renderer_CreateMetalBackend();
            break;
        case GRAPHICS_BACKEND_VULKAN:
            new_backend = Renderer_CreateVulkanBackend();
            break;
        default:
            Graphics_SetError("Unsupported graphics backend");
            return false;
    }
    
    if (!new_backend) {
        Graphics_SetError("Failed to create renderer backend");
        return false;
    }
    
    // Initialize new backend
    GraphicsConfig config = g_graphics_state.config;
    config.backend = backend;
    
    if (!new_backend->init(new_backend, &config)) {
        Graphics_SetError("Failed to initialize new renderer backend");
        Renderer_DestroyBackend(new_backend);
        return false;
    }
    
    // Shutdown old backend
    if (g_graphics_state.current_backend) {
        g_graphics_state.current_backend->shutdown(g_graphics_state.current_backend);
        Renderer_DestroyBackend(g_graphics_state.current_backend);
    }
    
    // Switch to new backend
    g_graphics_state.current_backend = new_backend;
    g_graphics_state.config = config;
    
    return true;
}

GraphicsBackend Graphics_GetCurrentBackend(void) {
    return g_graphics_state.config.backend;
}

RendererBackend* Graphics_GetRenderer(void) {
    return g_graphics_state.current_backend;
}

const char* Graphics_GetBackendName(GraphicsBackend backend) {
    switch (backend) {
        case GRAPHICS_BACKEND_OPENGL:
            return "OpenGL";
        case GRAPHICS_BACKEND_DIRECTX11:
            return "DirectX 11";
        case GRAPHICS_BACKEND_METAL:
            return "Metal";
        case GRAPHICS_BACKEND_VULKAN:
            return "Vulkan";
        default:
            return "Unknown";
    }
}

// Frame synchronization
void Graphics_BeginFrame(void) {
    if (!g_graphics_state.initialized || !g_graphics_state.current_backend) {
        return;
    }
    
    if (g_graphics_state.current_backend->begin_frame) {
        g_graphics_state.current_backend->begin_frame(g_graphics_state.current_backend);
    }
    
    // Reset per-frame statistics
    g_graphics_state.draw_calls = 0;
    g_graphics_state.vertices = 0;
    g_graphics_state.triangles = 0;
}

void Graphics_EndFrame(void) {
    if (!g_graphics_state.initialized || !g_graphics_state.current_backend) {
        return;
    }
    
    if (g_graphics_state.current_backend->end_frame) {
        g_graphics_state.current_backend->end_frame(g_graphics_state.current_backend);
    }
}

void Graphics_Present(void) {
    if (!g_graphics_state.initialized || !g_graphics_state.current_backend) {
        return;
    }
    
    if (g_graphics_state.current_backend->present) {
        g_graphics_state.current_backend->present(g_graphics_state.current_backend);
    }
}

// Debugging and profiling
void Graphics_EnableDebugMode(bool enabled) {
    g_graphics_state.debug_enabled = enabled;
    
    if (g_graphics_state.current_backend && g_graphics_state.current_backend->enable_debug) {
        g_graphics_state.current_backend->enable_debug(g_graphics_state.current_backend, enabled);
    }
}

void Graphics_GetStats(uint32_t* draw_calls, uint32_t* vertices, uint32_t* triangles) {
    if (draw_calls) {
        *draw_calls = g_graphics_state.draw_calls;
    }
    if (vertices) {
        *vertices = g_graphics_state.vertices;
    }
    if (triangles) {
        *triangles = g_graphics_state.triangles;
    }
}

// Error handling
const char* Graphics_GetErrorString(void) {
    return g_graphics_state.error_string;
}

void Graphics_ClearError(void) {
    Graphics_SetError(NULL);
} 