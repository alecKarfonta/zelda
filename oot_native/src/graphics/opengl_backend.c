#include "graphics/opengl_backend.h"
#include "graphics/opengl_shaders.h"
#include "graphics/n64_graphics.h"
#include <glad/glad.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Forward declarations
static bool OpenGL_InitBackend(RendererBackend* backend, GraphicsConfig* config);
static void OpenGL_ShutdownBackend(RendererBackend* backend);
static void OpenGL_BeginFrame(RendererBackend* backend);
static void OpenGL_EndFrame(RendererBackend* backend);
static void OpenGL_Present(RendererBackend* backend);

// Utility functions
bool OpenGL_CheckExtension(const char* extension) {
    const char* extensions = (const char*)glGetString(GL_EXTENSIONS);
    if (!extensions) return false;
    
    return strstr(extensions, extension) != NULL;
}

void OpenGL_CheckError(const char* operation) {
    GLenum error = glGetError();
    if (error != GL_NO_ERROR) {
        printf("OpenGL Error after %s: %s\n", operation, OpenGL_GetErrorString(error));
    }
}

const char* OpenGL_GetErrorString(uint32_t error) {
    switch (error) {
        case GL_NO_ERROR: return "No Error";
        case GL_INVALID_ENUM: return "Invalid Enum";
        case GL_INVALID_VALUE: return "Invalid Value";
        case GL_INVALID_OPERATION: return "Invalid Operation";
        case GL_OUT_OF_MEMORY: return "Out of Memory";
        case GL_INVALID_FRAMEBUFFER_OPERATION: return "Invalid Framebuffer Operation";
        default: return "Unknown Error";
    }
}

// Format conversion functions
uint32_t OpenGL_GetInternalFormat(TextureFormat format) {
    switch (format) {
        case TEXTURE_FORMAT_RGBA8: return GL_RGBA8;
        case TEXTURE_FORMAT_RGB8: return GL_RGB8;
        case TEXTURE_FORMAT_RG8: return GL_RG8;
        case TEXTURE_FORMAT_R8: return GL_R8;
        case TEXTURE_FORMAT_RGBA16F: return GL_RGBA16F;
        case TEXTURE_FORMAT_RGB16F: return GL_RGB16F;
        case TEXTURE_FORMAT_RG16F: return GL_RG16F;
        case TEXTURE_FORMAT_R16F: return GL_R16F;
        case TEXTURE_FORMAT_RGBA32F: return GL_RGBA32F;
        case TEXTURE_FORMAT_RGB32F: return GL_RGB32F;
        case TEXTURE_FORMAT_RG32F: return GL_RG32F;
        case TEXTURE_FORMAT_R32F: return GL_R32F;
        case TEXTURE_FORMAT_DEPTH24_STENCIL8: return GL_DEPTH24_STENCIL8;
        case TEXTURE_FORMAT_DEPTH32F: return GL_DEPTH_COMPONENT32F;
        case TEXTURE_FORMAT_DEPTH16: return GL_DEPTH_COMPONENT16;
        default: return GL_RGBA8;
    }
}

uint32_t OpenGL_GetFormat(TextureFormat format) {
    switch (format) {
        case TEXTURE_FORMAT_RGBA8:
        case TEXTURE_FORMAT_RGBA16F:
        case TEXTURE_FORMAT_RGBA32F:
            return GL_RGBA;
        case TEXTURE_FORMAT_RGB8:
        case TEXTURE_FORMAT_RGB16F:
        case TEXTURE_FORMAT_RGB32F:
            return GL_RGB;
        case TEXTURE_FORMAT_RG8:
        case TEXTURE_FORMAT_RG16F:
        case TEXTURE_FORMAT_RG32F:
            return GL_RG;
        case TEXTURE_FORMAT_R8:
        case TEXTURE_FORMAT_R16F:
        case TEXTURE_FORMAT_R32F:
            return GL_RED;
        case TEXTURE_FORMAT_DEPTH24_STENCIL8:
            return GL_DEPTH_STENCIL;
        case TEXTURE_FORMAT_DEPTH32F:
        case TEXTURE_FORMAT_DEPTH16:
            return GL_DEPTH_COMPONENT;
        default:
            return GL_RGBA;
    }
}

uint32_t OpenGL_GetType(TextureFormat format) {
    switch (format) {
        case TEXTURE_FORMAT_RGBA8:
        case TEXTURE_FORMAT_RGB8:
        case TEXTURE_FORMAT_RG8:
        case TEXTURE_FORMAT_R8:
            return GL_UNSIGNED_BYTE;
        case TEXTURE_FORMAT_RGBA16F:
        case TEXTURE_FORMAT_RGB16F:
        case TEXTURE_FORMAT_RG16F:
        case TEXTURE_FORMAT_R16F:
            return GL_HALF_FLOAT;
        case TEXTURE_FORMAT_RGBA32F:
        case TEXTURE_FORMAT_RGB32F:
        case TEXTURE_FORMAT_RG32F:
        case TEXTURE_FORMAT_R32F:
        case TEXTURE_FORMAT_DEPTH32F:
            return GL_FLOAT;
        case TEXTURE_FORMAT_DEPTH24_STENCIL8:
            return GL_UNSIGNED_INT_24_8;
        case TEXTURE_FORMAT_DEPTH16:
            return GL_UNSIGNED_SHORT;
        default:
            return GL_UNSIGNED_BYTE;
    }
}

uint32_t OpenGL_GetBufferTarget(BufferType type) {
    switch (type) {
        case BUFFER_TYPE_VERTEX: return GL_ARRAY_BUFFER;
        case BUFFER_TYPE_INDEX: return GL_ELEMENT_ARRAY_BUFFER;
        case BUFFER_TYPE_UNIFORM: return GL_UNIFORM_BUFFER;
        case BUFFER_TYPE_STAGING: return GL_COPY_READ_BUFFER;
        default: return GL_ARRAY_BUFFER;
    }
}

uint32_t OpenGL_GetShaderType(ShaderType type) {
    switch (type) {
        case SHADER_TYPE_VERTEX: return GL_VERTEX_SHADER;
        case SHADER_TYPE_FRAGMENT: return GL_FRAGMENT_SHADER;
        case SHADER_TYPE_GEOMETRY: return GL_GEOMETRY_SHADER;
        case SHADER_TYPE_COMPUTE: return GL_COMPUTE_SHADER;
        default: return GL_VERTEX_SHADER;
    }
}

uint32_t OpenGL_GetPrimitiveType(PrimitiveType type) {
    switch (type) {
        case PRIMITIVE_TRIANGLES: return GL_TRIANGLES;
        case PRIMITIVE_TRIANGLE_STRIP: return GL_TRIANGLE_STRIP;
        case PRIMITIVE_TRIANGLE_FAN: return GL_TRIANGLE_FAN;
        case PRIMITIVE_LINES: return GL_LINES;
        case PRIMITIVE_LINE_STRIP: return GL_LINE_STRIP;
        case PRIMITIVE_POINTS: return GL_POINTS;
        default: return GL_TRIANGLES;
    }
}

// Initialize OpenGL with GLAD
static bool OpenGL_InitBackend(RendererBackend* backend, GraphicsConfig* config) {
    if (!backend || !config) {
        return false;
    }
    
    // Initialize GLAD to load OpenGL function pointers
    if (!gladLoadGL()) {
        printf("Failed to initialize GLAD\n");
        return false;
    }
    
    // Check OpenGL version
    printf("OpenGL Version: %s\n", (const char*)glGetString(GL_VERSION));
    printf("OpenGL Renderer: %s\n", (const char*)glGetString(GL_RENDERER));
    printf("OpenGL Vendor: %s\n", (const char*)glGetString(GL_VENDOR));
    printf("GLSL Version: %s\n", (const char*)glGetString(GL_SHADING_LANGUAGE_VERSION));
    
    // Create backend data
    OpenGLBackendData* data = (OpenGLBackendData*)malloc(sizeof(OpenGLBackendData));
    if (!data) {
        return false;
    }
    memset(data, 0, sizeof(OpenGLBackendData));
    
    // Initialize backend data
    data->major_version = OPENGL_VERSION_MAJOR;
    data->minor_version = OPENGL_VERSION_MINOR;
    
    // Check for extensions
    data->extensions.vertex_array_object = OpenGL_CheckExtension("GL_ARB_vertex_array_object");
    data->extensions.texture_storage = OpenGL_CheckExtension("GL_ARB_texture_storage");
    data->extensions.debug_output = OpenGL_CheckExtension("GL_ARB_debug_output");
    data->extensions.seamless_cube_map = OpenGL_CheckExtension("GL_ARB_seamless_cube_map");
    data->extensions.texture_filter_anisotropic = OpenGL_CheckExtension("GL_EXT_texture_filter_anisotropic");
    
    // Create default vertex array
    if (data->extensions.vertex_array_object) {
        data->default_vertex_array = OpenGL_CreateVertexArray();
        if (!data->default_vertex_array) {
            free(data);
            return false;
        }
    }
    
    // Set default state
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LEQUAL);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    glFrontFace(GL_CCW);
    
    // Set viewport
    glViewport(0, 0, config->width, config->height);
    
    backend->backend_data = data;
    
    // Initialize shader manager
    if (!ShaderManager_Init(data)) {
        printf("Failed to initialize shader manager\n");
        if (data->default_vertex_array) {
            OpenGL_DestroyVertexArray(data->default_vertex_array);
        }
        free(data);
        return false;
    }
    
    OpenGL_CheckError("Backend initialization");
    return true;
}

static void OpenGL_ShutdownBackend(RendererBackend* backend) {
    if (!backend || !backend->backend_data) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    
    // Shutdown shader manager
    ShaderManager_Shutdown();
    
    // Clean up default resources
    if (data->default_vertex_array) {
        OpenGL_DestroyVertexArray(data->default_vertex_array);
    }
    
    free(data);
    backend->backend_data = NULL;
}

static void OpenGL_BeginFrame(RendererBackend* backend) {
    if (!backend || !backend->backend_data) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    
    // Reset statistics
    data->draw_calls = 0;
    data->vertices = 0;
    data->triangles = 0;
    
    // Clear the framebuffer
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    
    OpenGL_CheckError("Begin frame");
}

static void OpenGL_EndFrame(RendererBackend* backend) {
    if (!backend || !backend->backend_data) {
        return;
    }
    
    // Flush any pending OpenGL commands
    glFlush();
    
    OpenGL_CheckError("End frame");
}

static void OpenGL_Present(RendererBackend* backend) {
    if (!backend || !backend->backend_data) {
        return;
    }
    
    // Platform-specific buffer swap would go here
    // This is typically handled by the window system (SDL, GLFW, etc.)
    
    OpenGL_CheckError("Present");
}

// Core rendering functions
static void OpenGL_Draw(RendererBackend* backend, const DrawCommand* command) {
    if (!backend || !command) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    GLenum primitive = OpenGL_GetPrimitiveType(command->primitive);
    
    if (command->instance_count > 1) {
        // TODO: Implement instanced rendering
        glDrawArraysInstanced(primitive, command->first_vertex, command->vertex_count, command->instance_count);
    } else {
        glDrawArrays(primitive, command->first_vertex, command->vertex_count);
    }
    
    data->draw_calls++;
    data->vertices += command->vertex_count;
    if (command->primitive == PRIMITIVE_TRIANGLES) {
        data->triangles += command->vertex_count / 3;
    }
    
    OpenGL_CheckError("Draw");
}

static void OpenGL_DrawIndexed(RendererBackend* backend, const DrawCommand* command) {
    if (!backend || !command) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    GLenum primitive = OpenGL_GetPrimitiveType(command->primitive);
    
    if (command->instance_count > 1) {
        // TODO: Implement instanced indexed rendering
        glDrawElementsInstanced(primitive, command->index_count, GL_UNSIGNED_SHORT, 
                               (void*)(command->first_index * sizeof(uint16_t)), command->instance_count);
    } else {
        glDrawElements(primitive, command->index_count, GL_UNSIGNED_SHORT, 
                      (void*)(command->first_index * sizeof(uint16_t)));
    }
    
    data->draw_calls++;
    data->vertices += command->index_count;
    if (command->primitive == PRIMITIVE_TRIANGLES) {
        data->triangles += command->index_count / 3;
    }
    
    OpenGL_CheckError("Draw indexed");
}

static void OpenGL_Clear(RendererBackend* backend, bool color, bool depth, bool stencil,
                        float r, float g, float b, float a, float depth_val, uint8_t stencil_val) {
    if (!backend) {
        return;
    }
    
    GLbitfield mask = 0;
    
    if (color) {
        glClearColor(r, g, b, a);
        mask |= GL_COLOR_BUFFER_BIT;
    }
    
    if (depth) {
        glClearDepth(depth_val);
        mask |= GL_DEPTH_BUFFER_BIT;
    }
    
    if (stencil) {
        glClearStencil(stencil_val);
        mask |= GL_STENCIL_BUFFER_BIT;
    }
    
    if (mask != 0) {
        glClear(mask);
    }
    
    OpenGL_CheckError("Clear");
}

static void OpenGL_Viewport(RendererBackend* backend, uint32_t x, uint32_t y, uint32_t width, uint32_t height) {
    if (!backend) {
        return;
    }
    
    glViewport(x, y, width, height);
    OpenGL_CheckError("Viewport");
}

static void OpenGL_Scissor(RendererBackend* backend, uint32_t x, uint32_t y, uint32_t width, uint32_t height) {
    if (!backend) {
        return;
    }
    
    glScissor(x, y, width, height);
    OpenGL_CheckError("Scissor");
}

// Binding functions
static void OpenGL_BindTexture(RendererBackend* backend, uint32_t slot, Texture* texture) {
    if (!backend) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    glActiveTexture(GL_TEXTURE0 + slot);
    
    if (texture) {
        OpenGLTexture* gl_texture = (OpenGLTexture*)texture;
        GLenum target = (gl_texture->type == TEXTURE_TYPE_CUBEMAP) ? GL_TEXTURE_CUBE_MAP : GL_TEXTURE_2D;
        glBindTexture(target, gl_texture->id);
        
        if (slot < 16) {
            data->bound_textures[slot] = gl_texture;
        }
    } else {
        glBindTexture(GL_TEXTURE_2D, 0);
        glBindTexture(GL_TEXTURE_CUBE_MAP, 0);
        
        if (slot < 16) {
            data->bound_textures[slot] = NULL;
        }
    }
    
    OpenGL_CheckError("Bind texture");
}

static void OpenGL_BindShader(RendererBackend* backend, Shader* vertex_shader, Shader* fragment_shader) {
    if (!backend) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    if (vertex_shader && fragment_shader) {
        OpenGLShader* gl_vertex = (OpenGLShader*)vertex_shader;
        OpenGLShader* gl_fragment = (OpenGLShader*)fragment_shader;
        
        // Create or find shader program
        OpenGLShaderProgram* program = OpenGL_CreateShaderProgram(gl_vertex, gl_fragment);
        if (program && program->linked) {
            glUseProgram(program->program_id);
            data->current_program = program;
        }
    } else {
        glUseProgram(0);
        data->current_program = NULL;
    }
    
    OpenGL_CheckError("Bind shader");
}

static void OpenGL_BindBuffer(RendererBackend* backend, BufferType type, Buffer* buffer) {
    if (!backend) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    GLenum target = OpenGL_GetBufferTarget(type);
    
    if (buffer) {
        OpenGLBuffer* gl_buffer = (OpenGLBuffer*)buffer;
        glBindBuffer(target, gl_buffer->id);
        
        if (type < 4) {
            data->bound_buffers[type] = gl_buffer;
        }
    } else {
        glBindBuffer(target, 0);
        
        if (type < 4) {
            data->bound_buffers[type] = NULL;
        }
    }
    
    OpenGL_CheckError("Bind buffer");
}

static void OpenGL_BindFramebuffer(RendererBackend* backend, Framebuffer* framebuffer) {
    if (!backend) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    if (framebuffer) {
        OpenGLFramebuffer* gl_framebuffer = (OpenGLFramebuffer*)framebuffer;
        glBindFramebuffer(GL_FRAMEBUFFER, gl_framebuffer->id);
        data->current_framebuffer = gl_framebuffer;
    } else {
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        data->current_framebuffer = data->default_framebuffer;
    }
    
    OpenGL_CheckError("Bind framebuffer");
}

// Uniform management functions
static void OpenGL_BackendSetUniformInt(RendererBackend* backend, const char* name, int value) {
    if (!backend || !name) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformInt(data->current_program, name, value);
}

static void OpenGL_BackendSetUniformFloat(RendererBackend* backend, const char* name, float value) {
    if (!backend || !name) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformFloat(data->current_program, name, value);
}

static void OpenGL_BackendSetUniformVec2(RendererBackend* backend, const char* name, const float* value) {
    if (!backend || !name || !value) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformVec2(data->current_program, name, value);
}

static void OpenGL_BackendSetUniformVec3(RendererBackend* backend, const char* name, const float* value) {
    if (!backend || !name || !value) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformVec3(data->current_program, name, value);
}

static void OpenGL_BackendSetUniformVec4(RendererBackend* backend, const char* name, const float* value) {
    if (!backend || !name || !value) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformVec4(data->current_program, name, value);
}

static void OpenGL_BackendSetUniformMat4(RendererBackend* backend, const char* name, const float* value) {
    if (!backend || !name || !value) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data || !data->current_program) {
        return;
    }
    
    OpenGL_SetUniformMat4(data->current_program, name, value);
}

// Render state and vertex layout functions
static void OpenGL_SetRenderState(RendererBackend* backend, const RenderState* state) {
    if (!backend || !state) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    // Blend mode
    switch (state->blend_mode) {
        case BLEND_MODE_NONE:
            glDisable(GL_BLEND);
            break;
        case BLEND_MODE_ALPHA:
            glEnable(GL_BLEND);
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
            break;
        case BLEND_MODE_ADDITIVE:
            glEnable(GL_BLEND);
            glBlendFunc(GL_SRC_ALPHA, GL_ONE);
            break;
        case BLEND_MODE_MULTIPLICATIVE:
            glEnable(GL_BLEND);
            glBlendFunc(GL_DST_COLOR, GL_ZERO);
            break;
        default:
            break;
    }
    
    // Depth test
    if (state->depth_test != DEPTH_TEST_ALWAYS) {
        glEnable(GL_DEPTH_TEST);
        
        GLenum depth_func = GL_LEQUAL;
        switch (state->depth_test) {
            case DEPTH_TEST_NEVER: depth_func = GL_NEVER; break;
            case DEPTH_TEST_LESS: depth_func = GL_LESS; break;
            case DEPTH_TEST_EQUAL: depth_func = GL_EQUAL; break;
            case DEPTH_TEST_LEQUAL: depth_func = GL_LEQUAL; break;
            case DEPTH_TEST_GREATER: depth_func = GL_GREATER; break;
            case DEPTH_TEST_NOTEQUAL: depth_func = GL_NOTEQUAL; break;
            case DEPTH_TEST_GEQUAL: depth_func = GL_GEQUAL; break;
            case DEPTH_TEST_ALWAYS: depth_func = GL_ALWAYS; break;
        }
        glDepthFunc(depth_func);
    } else {
        glDisable(GL_DEPTH_TEST);
    }
    
    // Depth write
    glDepthMask(state->depth_write ? GL_TRUE : GL_FALSE);
    
    // Cull mode
    switch (state->cull_mode) {
        case CULL_MODE_NONE:
            glDisable(GL_CULL_FACE);
            break;
        case CULL_MODE_FRONT:
            glEnable(GL_CULL_FACE);
            glCullFace(GL_FRONT);
            break;
        case CULL_MODE_BACK:
            glEnable(GL_CULL_FACE);
            glCullFace(GL_BACK);
            break;
        case CULL_MODE_FRONT_AND_BACK:
            glEnable(GL_CULL_FACE);
            glCullFace(GL_FRONT_AND_BACK);
            break;
    }
    
    // Alpha test (deprecated in core profile, would need shader implementation)
    if (state->alpha_test) {
        // TODO: Implement alpha test in shader
    }
    
    // Scissor test
    if (state->scissor_test) {
        glEnable(GL_SCISSOR_TEST);
        glScissor(state->scissor_rect.x, state->scissor_rect.y, 
                 state->scissor_rect.width, state->scissor_rect.height);
    } else {
        glDisable(GL_SCISSOR_TEST);
    }
    
    // Store current state
    data->current_state = *state;
    
    OpenGL_CheckError("Set render state");
}

static void OpenGL_SetVertexLayout(RendererBackend* backend, const VertexLayout* layout) {
    if (!backend || !layout) {
        return;
    }
    
    OpenGLBackendData* data = (OpenGLBackendData*)backend->backend_data;
    if (!data) {
        return;
    }
    
    // Bind vertex array if available
    if (data->current_vertex_array) {
        glBindVertexArray(data->current_vertex_array->id);
    }
    
    // Set up vertex attributes
    for (uint32_t i = 0; i < layout->attribute_count; i++) {
        const VertexAttribute* attr = &layout->attributes[i];
        
        glEnableVertexAttribArray(attr->location);
        
        GLenum type = GL_FLOAT;
        switch (attr->type) {
            case GL_BYTE: type = GL_BYTE; break;
            case GL_UNSIGNED_BYTE: type = GL_UNSIGNED_BYTE; break;
            case GL_SHORT: type = GL_SHORT; break;
            case GL_UNSIGNED_SHORT: type = GL_UNSIGNED_SHORT; break;
            case GL_INT: type = GL_INT; break;
            case GL_UNSIGNED_INT: type = GL_UNSIGNED_INT; break;
            case GL_FLOAT: type = GL_FLOAT; break;
            default: type = GL_FLOAT; break;
        }
        
        glVertexAttribPointer(attr->location, attr->size, type, 
                            attr->normalized ? GL_TRUE : GL_FALSE,
                            attr->stride, (void*)(uintptr_t)attr->offset);
    }
    
    OpenGL_CheckError("Set vertex layout");
}

// N64 command processing - delegate to N64Graphics system
static void OpenGL_ProcessN64Command(RendererBackend* backend, const GraphicsCommand* cmd) {
    if (!backend || !cmd) {
        return;
    }
    
    // Set this backend as the current backend for N64 processing
    Renderer_SetCurrentBackend(backend);
    
    // Delegate to the N64 graphics processing system
    N64Graphics_ProcessCommand((GraphicsCommand*)cmd);
}

// Create OpenGL backend
RendererBackend* Renderer_CreateOpenGLBackend(void) {
    RendererBackend* backend = (RendererBackend*)malloc(sizeof(RendererBackend));
    if (!backend) {
        return NULL;
    }
    
    memset(backend, 0, sizeof(RendererBackend));
    
    // Set backend identification
    backend->name = "OpenGL";
    backend->type = GRAPHICS_BACKEND_OPENGL;
    
    // Set function pointers
    backend->init = OpenGL_InitBackend;
    backend->shutdown = OpenGL_ShutdownBackend;
    backend->begin_frame = OpenGL_BeginFrame;
    backend->end_frame = OpenGL_EndFrame;
    backend->present = OpenGL_Present;
    
    // Resource management - connect to actual implementations
    backend->create_texture = (Texture* (*)(RendererBackend*, TextureType, TextureFormat, uint32_t, uint32_t, uint32_t, uint32_t))OpenGL_CreateTexture;
    backend->destroy_texture = (void (*)(RendererBackend*, Texture*))OpenGL_DestroyTexture;
    backend->update_texture = (void (*)(RendererBackend*, Texture*, uint32_t, uint32_t, uint32_t, uint32_t, uint32_t, const void*))OpenGL_UpdateTexture;
    
    backend->create_shader = (Shader* (*)(RendererBackend*, ShaderType, const char*))OpenGL_CreateShader;
    backend->destroy_shader = (void (*)(RendererBackend*, Shader*))OpenGL_DestroyShader;
    
    backend->create_buffer = (Buffer* (*)(RendererBackend*, BufferType, uint32_t, const void*, bool))OpenGL_CreateBuffer;
    backend->destroy_buffer = (void (*)(RendererBackend*, Buffer*))OpenGL_DestroyBuffer;
    backend->update_buffer = (void (*)(RendererBackend*, Buffer*, uint32_t, uint32_t, const void*))OpenGL_UpdateBuffer;
    
    backend->create_framebuffer = (Framebuffer* (*)(RendererBackend*, uint32_t, uint32_t, Texture**, uint32_t, Texture*))OpenGL_CreateFramebuffer;
    backend->destroy_framebuffer = (void (*)(RendererBackend*, Framebuffer*))OpenGL_DestroyFramebuffer;
    
    // State management
    backend->set_render_state = OpenGL_SetRenderState;
    backend->set_vertex_layout = OpenGL_SetVertexLayout;
    backend->bind_texture = OpenGL_BindTexture;
    backend->bind_shader = OpenGL_BindShader;
    backend->bind_buffer = OpenGL_BindBuffer;
    backend->bind_framebuffer = OpenGL_BindFramebuffer;
    
    // Uniform management
    backend->set_uniform_int = OpenGL_BackendSetUniformInt;
    backend->set_uniform_float = OpenGL_BackendSetUniformFloat;
    backend->set_uniform_vec2 = OpenGL_BackendSetUniformVec2;
    backend->set_uniform_vec3 = OpenGL_BackendSetUniformVec3;
    backend->set_uniform_vec4 = OpenGL_BackendSetUniformVec4;
    backend->set_uniform_mat4 = OpenGL_BackendSetUniformMat4;
    
    // Drawing
    backend->draw = OpenGL_Draw;
    backend->draw_indexed = OpenGL_DrawIndexed;
    backend->clear = OpenGL_Clear;
    
    // Utility functions
    backend->viewport = OpenGL_Viewport;
    backend->scissor = OpenGL_Scissor;
    
    // N64 specific functions
    backend->process_n64_command = OpenGL_ProcessN64Command;
    
    return backend;
} 