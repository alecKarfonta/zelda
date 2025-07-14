#pragma once

#include "graphics/renderer_backend.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// OpenGL version requirements
#define OPENGL_VERSION_MAJOR 3
#define OPENGL_VERSION_MINOR 3

// OpenGL resource handles
typedef struct {
    uint32_t id;
    TextureType type;
    TextureFormat format;
    uint32_t width;
    uint32_t height;
    uint32_t depth;
    uint32_t mip_levels;
} OpenGLTexture;

typedef struct {
    uint32_t id;
    ShaderType type;
    bool compiled;
} OpenGLShader;

typedef struct {
    uint32_t id;
    uint32_t program_id;
    OpenGLShader* vertex_shader;
    OpenGLShader* fragment_shader;
    bool linked;
} OpenGLShaderProgram;

typedef struct {
    uint32_t id;
    BufferType type;
    uint32_t size;
    bool dynamic;
} OpenGLBuffer;

typedef struct {
    uint32_t id;
    uint32_t width;
    uint32_t height;
    OpenGLTexture** color_attachments;
    uint32_t color_count;
    OpenGLTexture* depth_attachment;
} OpenGLFramebuffer;

// OpenGL vertex array object
typedef struct {
    uint32_t id;
    VertexLayout layout;
    bool bound;
} OpenGLVertexArray;

// OpenGL backend state
typedef struct {
    // Context information
    int major_version;
    int minor_version;
    
    // Current render state
    RenderState current_state;
    
    // Bound resources
    OpenGLShaderProgram* current_program;
    OpenGLFramebuffer* current_framebuffer;
    OpenGLVertexArray* current_vertex_array;
    OpenGLBuffer* bound_buffers[4]; // One for each BufferType
    OpenGLTexture* bound_textures[16]; // Support up to 16 texture units
    
    // Default resources
    OpenGLFramebuffer* default_framebuffer;
    OpenGLVertexArray* default_vertex_array;
    
    // Statistics
    uint32_t draw_calls;
    uint32_t vertices;
    uint32_t triangles;
    
    // Debug mode
    bool debug_enabled;
    
    // N64 specific state
    struct {
        N64CombinerMode combiner_mode;
        uint32_t tile_descriptors[8];
        uint32_t texture_cache[8];
        bool fog_enabled;
        bool depth_test_enabled;
        bool alpha_test_enabled;
        float alpha_ref;
    } n64_state;
    
    // OpenGL extensions
    struct {
        bool vertex_array_object;
        bool texture_storage;
        bool debug_output;
        bool seamless_cube_map;
        bool texture_filter_anisotropic;
    } extensions;
} OpenGLBackendData;

// OpenGL utility functions
bool OpenGL_CheckExtension(const char* extension);
void OpenGL_CheckError(const char* operation);
const char* OpenGL_GetErrorString(uint32_t error);

// OpenGL resource management
OpenGLTexture* OpenGL_CreateTexture(TextureType type, TextureFormat format,
                                   uint32_t width, uint32_t height, uint32_t depth,
                                   uint32_t mip_levels);
void OpenGL_DestroyTexture(OpenGLTexture* texture);
void OpenGL_UpdateTexture(OpenGLTexture* texture, uint32_t level,
                         uint32_t x, uint32_t y, uint32_t width, uint32_t height,
                         const void* data);

OpenGLShader* OpenGL_CreateShader(ShaderType type, const char* source);
void OpenGL_DestroyShader(OpenGLShader* shader);

OpenGLShaderProgram* OpenGL_CreateShaderProgram(OpenGLShader* vertex_shader,
                                               OpenGLShader* fragment_shader);
void OpenGL_DestroyShaderProgram(OpenGLShaderProgram* program);

// OpenGL uniform functions
void OpenGL_SetUniformInt(OpenGLShaderProgram* program, const char* name, int value);
void OpenGL_SetUniformFloat(OpenGLShaderProgram* program, const char* name, float value);
void OpenGL_SetUniformVec2(OpenGLShaderProgram* program, const char* name, const float* value);
void OpenGL_SetUniformVec3(OpenGLShaderProgram* program, const char* name, const float* value);
void OpenGL_SetUniformVec4(OpenGLShaderProgram* program, const char* name, const float* value);
void OpenGL_SetUniformMat4(OpenGLShaderProgram* program, const char* name, const float* value);

OpenGLBuffer* OpenGL_CreateBuffer(BufferType type, uint32_t size,
                                 const void* data, bool dynamic);
void OpenGL_DestroyBuffer(OpenGLBuffer* buffer);
void OpenGL_UpdateBuffer(OpenGLBuffer* buffer, uint32_t offset,
                        uint32_t size, const void* data);

OpenGLFramebuffer* OpenGL_CreateFramebuffer(uint32_t width, uint32_t height,
                                           OpenGLTexture** color_attachments,
                                           uint32_t color_count,
                                           OpenGLTexture* depth_attachment);
void OpenGL_DestroyFramebuffer(OpenGLFramebuffer* framebuffer);

OpenGLVertexArray* OpenGL_CreateVertexArray(void);
void OpenGL_DestroyVertexArray(OpenGLVertexArray* vao);

// OpenGL N64 specific functions
void OpenGL_ConvertN64Texture(OpenGLBackendData* data, const N64Texture* tex, OpenGLTexture** output);
void OpenGL_SetN64Combiner(OpenGLBackendData* data, N64CombinerMode mode);

// OpenGL format conversion
uint32_t OpenGL_GetInternalFormat(TextureFormat format);
uint32_t OpenGL_GetFormat(TextureFormat format);
uint32_t OpenGL_GetType(TextureFormat format);
uint32_t OpenGL_GetBufferTarget(BufferType type);
uint32_t OpenGL_GetShaderType(ShaderType type);
uint32_t OpenGL_GetPrimitiveType(PrimitiveType type);

#ifdef __cplusplus
}
#endif 