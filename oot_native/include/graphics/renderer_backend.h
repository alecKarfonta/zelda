#pragma once

#include "graphics_api.h"
#include "n64_graphics.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct RendererBackend RendererBackend;
typedef struct Texture Texture;
typedef struct Shader Shader;
typedef struct Buffer Buffer;
typedef struct Framebuffer Framebuffer;

// Buffer types
typedef enum {
    BUFFER_TYPE_VERTEX,
    BUFFER_TYPE_INDEX,
    BUFFER_TYPE_UNIFORM,
    BUFFER_TYPE_STAGING
} BufferType;

// Texture types
typedef enum {
    TEXTURE_TYPE_2D,
    TEXTURE_TYPE_CUBEMAP,
    TEXTURE_TYPE_ARRAY
} TextureType;

// Shader types
typedef enum {
    SHADER_TYPE_VERTEX,
    SHADER_TYPE_FRAGMENT,
    SHADER_TYPE_GEOMETRY,
    SHADER_TYPE_COMPUTE
} ShaderType;

// Primitive types
typedef enum {
    PRIMITIVE_TRIANGLES,
    PRIMITIVE_TRIANGLE_STRIP,
    PRIMITIVE_TRIANGLE_FAN,
    PRIMITIVE_LINES,
    PRIMITIVE_LINE_STRIP,
    PRIMITIVE_POINTS
} PrimitiveType;

// Blend modes
typedef enum {
    BLEND_MODE_NONE,
    BLEND_MODE_ALPHA,
    BLEND_MODE_ADDITIVE,
    BLEND_MODE_MULTIPLICATIVE,
    BLEND_MODE_CUSTOM
} BlendMode;

// Depth test modes
typedef enum {
    DEPTH_TEST_NEVER,
    DEPTH_TEST_LESS,
    DEPTH_TEST_EQUAL,
    DEPTH_TEST_LEQUAL,
    DEPTH_TEST_GREATER,
    DEPTH_TEST_NOTEQUAL,
    DEPTH_TEST_GEQUAL,
    DEPTH_TEST_ALWAYS
} DepthTestMode;

// Cull modes
typedef enum {
    CULL_MODE_NONE,
    CULL_MODE_FRONT,
    CULL_MODE_BACK,
    CULL_MODE_FRONT_AND_BACK
} CullMode;

// Texture format
typedef enum {
    TEXTURE_FORMAT_RGBA8,
    TEXTURE_FORMAT_RGB8,
    TEXTURE_FORMAT_RG8,
    TEXTURE_FORMAT_R8,
    TEXTURE_FORMAT_RGBA16F,
    TEXTURE_FORMAT_RGB16F,
    TEXTURE_FORMAT_RG16F,
    TEXTURE_FORMAT_R16F,
    TEXTURE_FORMAT_RGBA32F,
    TEXTURE_FORMAT_RGB32F,
    TEXTURE_FORMAT_RG32F,
    TEXTURE_FORMAT_R32F,
    TEXTURE_FORMAT_DEPTH24_STENCIL8,
    TEXTURE_FORMAT_DEPTH32F,
    TEXTURE_FORMAT_DEPTH16
} TextureFormat;

// Render state
typedef struct {
    BlendMode blend_mode;
    DepthTestMode depth_test;
    CullMode cull_mode;
    bool depth_write;
    bool alpha_test;
    float alpha_ref;
    bool scissor_test;
    struct {
        uint32_t x, y, width, height;
    } scissor_rect;
    struct {
        uint32_t x, y, width, height;
    } viewport;
} RenderState;

// Vertex attribute
typedef struct {
    uint32_t location;
    uint32_t size;
    uint32_t type;
    bool normalized;
    uint32_t stride;
    uint32_t offset;
} VertexAttribute;

// Vertex layout
typedef struct {
    VertexAttribute attributes[16];
    uint32_t attribute_count;
    uint32_t stride;
} VertexLayout;

// Draw command
typedef struct {
    PrimitiveType primitive;
    uint32_t first_vertex;
    uint32_t vertex_count;
    uint32_t first_index;
    uint32_t index_count;
    uint32_t instance_count;
} DrawCommand;

// Renderer backend interface
typedef struct RendererBackend {
    // Backend identification
    const char* name;
    GraphicsBackend type;
    
    // Initialization and cleanup
    bool (*init)(RendererBackend* backend, GraphicsConfig* config);
    void (*shutdown)(RendererBackend* backend);
    
    // Frame management
    void (*begin_frame)(RendererBackend* backend);
    void (*end_frame)(RendererBackend* backend);
    void (*present)(RendererBackend* backend);
    
    // Resource management
    Texture* (*create_texture)(RendererBackend* backend, TextureType type, TextureFormat format,
                              uint32_t width, uint32_t height, uint32_t depth, uint32_t mip_levels);
    void (*destroy_texture)(RendererBackend* backend, Texture* texture);
    void (*update_texture)(RendererBackend* backend, Texture* texture, uint32_t level,
                          uint32_t x, uint32_t y, uint32_t width, uint32_t height,
                          const void* data);
    
    Shader* (*create_shader)(RendererBackend* backend, ShaderType type, const char* source);
    void (*destroy_shader)(RendererBackend* backend, Shader* shader);
    
    Buffer* (*create_buffer)(RendererBackend* backend, BufferType type, uint32_t size,
                           const void* data, bool dynamic);
    void (*destroy_buffer)(RendererBackend* backend, Buffer* buffer);
    void (*update_buffer)(RendererBackend* backend, Buffer* buffer, uint32_t offset,
                         uint32_t size, const void* data);
    
    Framebuffer* (*create_framebuffer)(RendererBackend* backend, uint32_t width, uint32_t height,
                                      Texture** color_attachments, uint32_t color_count,
                                      Texture* depth_attachment);
    void (*destroy_framebuffer)(RendererBackend* backend, Framebuffer* framebuffer);
    
    // State management
    void (*set_render_state)(RendererBackend* backend, const RenderState* state);
    void (*set_vertex_layout)(RendererBackend* backend, const VertexLayout* layout);
    void (*bind_texture)(RendererBackend* backend, uint32_t slot, Texture* texture);
    void (*bind_shader)(RendererBackend* backend, Shader* vertex_shader, Shader* fragment_shader);
    void (*bind_buffer)(RendererBackend* backend, BufferType type, Buffer* buffer);
    void (*bind_framebuffer)(RendererBackend* backend, Framebuffer* framebuffer);
    
    // Uniform management
    void (*set_uniform_int)(RendererBackend* backend, const char* name, int value);
    void (*set_uniform_float)(RendererBackend* backend, const char* name, float value);
    void (*set_uniform_vec2)(RendererBackend* backend, const char* name, const float* value);
    void (*set_uniform_vec3)(RendererBackend* backend, const char* name, const float* value);
    void (*set_uniform_vec4)(RendererBackend* backend, const char* name, const float* value);
    void (*set_uniform_mat4)(RendererBackend* backend, const char* name, const float* value);
    
    // Drawing
    void (*draw)(RendererBackend* backend, const DrawCommand* command);
    void (*draw_indexed)(RendererBackend* backend, const DrawCommand* command);
    void (*clear)(RendererBackend* backend, bool color, bool depth, bool stencil,
                 float r, float g, float b, float a, float depth_val, uint8_t stencil_val);
    
    // Utility functions
    void (*viewport)(RendererBackend* backend, uint32_t x, uint32_t y, uint32_t width, uint32_t height);
    void (*scissor)(RendererBackend* backend, uint32_t x, uint32_t y, uint32_t width, uint32_t height);
    
    // N64 specific functions
    void (*process_n64_command)(RendererBackend* backend, const GraphicsCommand* cmd);
    void (*convert_n64_texture)(RendererBackend* backend, const N64Texture* tex, Texture** output);
    void (*set_n64_combiner)(RendererBackend* backend, N64CombinerMode mode);
    
    // Debug and profiling
    void (*enable_debug)(RendererBackend* backend, bool enabled);
    void (*get_stats)(RendererBackend* backend, uint32_t* draw_calls, uint32_t* vertices, uint32_t* triangles);
    
    // Backend-specific data
    void* backend_data;
} RendererBackend;

// Backend factory functions
RendererBackend* Renderer_CreateOpenGLBackend(void);
RendererBackend* Renderer_CreateDirectX11Backend(void);
RendererBackend* Renderer_CreateMetalBackend(void);
RendererBackend* Renderer_CreateVulkanBackend(void);
void Renderer_DestroyBackend(RendererBackend* backend);

// Backend management
bool Renderer_IsBackendSupported(GraphicsBackend backend);
const char* Renderer_GetBackendName(GraphicsBackend backend);
RendererBackend* Renderer_GetCurrentBackend(void);
bool Renderer_SetCurrentBackend(RendererBackend* backend);

// Utility functions
const char* Renderer_GetErrorString(void);
void Renderer_ClearError(void);

#ifdef __cplusplus
}
#endif 