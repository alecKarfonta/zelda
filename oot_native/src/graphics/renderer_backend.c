#include "graphics/renderer_backend.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Global backend management
static RendererBackend* g_current_backend = NULL;
static char g_error_string[256] = {0};

// Error management
const char* Renderer_GetErrorString(void) {
    return g_error_string;
}

void Renderer_ClearError(void) {
    g_error_string[0] = '\0';
}

static void Renderer_SetError(const char* error) {
    if (error) {
        strncpy(g_error_string, error, sizeof(g_error_string) - 1);
        g_error_string[sizeof(g_error_string) - 1] = '\0';
    } else {
        g_error_string[0] = '\0';
    }
}

// Backend support checking
bool Renderer_IsBackendSupported(GraphicsBackend backend) {
    switch (backend) {
        case GRAPHICS_BACKEND_OPENGL:
            return true; // OpenGL is always supported
        case GRAPHICS_BACKEND_DIRECTX11:
#ifdef _WIN32
            return true; // DirectX11 is supported on Windows
#else
            return false;
#endif
        case GRAPHICS_BACKEND_METAL:
#ifdef __APPLE__
            return true; // Metal is supported on macOS
#else
            return false;
#endif
        case GRAPHICS_BACKEND_VULKAN:
            return true; // Vulkan is cross-platform (stub for now)
        default:
            return false;
    }
}

const char* Renderer_GetBackendName(GraphicsBackend backend) {
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

// Backend management
RendererBackend* Renderer_GetCurrentBackend(void) {
    return g_current_backend;
}

bool Renderer_SetCurrentBackend(RendererBackend* backend) {
    if (!backend) {
        Renderer_SetError("Invalid backend");
        return false;
    }
    
    g_current_backend = backend;
    return true;
}

// DirectX11 backend stub
static bool DirectX11_InitStub(RendererBackend* backend, GraphicsConfig* config) {
    Renderer_SetError("DirectX11 backend not implemented yet");
    return false;
}

static void DirectX11_ShutdownStub(RendererBackend* backend) {
    // Stub implementation
}

static void DirectX11_ProcessN64CommandStub(RendererBackend* backend, const GraphicsCommand* cmd) {
    // Stub implementation
}

RendererBackend* Renderer_CreateDirectX11Backend(void) {
#ifdef _WIN32
    RendererBackend* backend = (RendererBackend*)malloc(sizeof(RendererBackend));
    if (!backend) {
        return NULL;
    }
    
    memset(backend, 0, sizeof(RendererBackend));
    
    backend->name = "DirectX 11";
    backend->type = GRAPHICS_BACKEND_DIRECTX11;
    backend->init = DirectX11_InitStub;
    backend->shutdown = DirectX11_ShutdownStub;
    backend->process_n64_command = DirectX11_ProcessN64CommandStub;
    
    return backend;
#else
    Renderer_SetError("DirectX11 not supported on this platform");
    return NULL;
#endif
}

// Metal backend stub
static bool Metal_InitStub(RendererBackend* backend, GraphicsConfig* config) {
    Renderer_SetError("Metal backend not implemented yet");
    return false;
}

static void Metal_ShutdownStub(RendererBackend* backend) {
    // Stub implementation
}

static void Metal_ProcessN64CommandStub(RendererBackend* backend, const GraphicsCommand* cmd) {
    // Stub implementation
}

RendererBackend* Renderer_CreateMetalBackend(void) {
#ifdef __APPLE__
    RendererBackend* backend = (RendererBackend*)malloc(sizeof(RendererBackend));
    if (!backend) {
        return NULL;
    }
    
    memset(backend, 0, sizeof(RendererBackend));
    
    backend->name = "Metal";
    backend->type = GRAPHICS_BACKEND_METAL;
    backend->init = Metal_InitStub;
    backend->shutdown = Metal_ShutdownStub;
    backend->process_n64_command = Metal_ProcessN64CommandStub;
    
    return backend;
#else
    Renderer_SetError("Metal not supported on this platform");
    return NULL;
#endif
}

// Vulkan backend stub
static bool Vulkan_InitStub(RendererBackend* backend, GraphicsConfig* config) {
    Renderer_SetError("Vulkan backend not implemented yet");
    return false;
}

static void Vulkan_ShutdownStub(RendererBackend* backend) {
    // Stub implementation
}

static void Vulkan_ProcessN64CommandStub(RendererBackend* backend, const GraphicsCommand* cmd) {
    // Stub implementation
}

RendererBackend* Renderer_CreateVulkanBackend(void) {
    RendererBackend* backend = (RendererBackend*)malloc(sizeof(RendererBackend));
    if (!backend) {
        return NULL;
    }
    
    memset(backend, 0, sizeof(RendererBackend));
    
    backend->name = "Vulkan";
    backend->type = GRAPHICS_BACKEND_VULKAN;
    backend->init = Vulkan_InitStub;
    backend->shutdown = Vulkan_ShutdownStub;
    backend->process_n64_command = Vulkan_ProcessN64CommandStub;
    
    return backend;
}

// Backend destruction
void Renderer_DestroyBackend(RendererBackend* backend) {
    if (!backend) {
        return;
    }
    
    // Clear current backend if this is it
    if (g_current_backend == backend) {
        g_current_backend = NULL;
    }
    
    free(backend);
} 