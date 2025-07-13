#include "graphics/opengl_backend.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// OpenGL headers (platform-specific)
#ifdef _WIN32
    #include <windows.h>
    #include <GL/gl.h>
    #include <GL/glext.h>
#elif defined(__APPLE__)
    #include <OpenGL/OpenGL.h>
    #include <OpenGL/gl3.h>
#else
    #include <GL/gl.h>
    #include <GL/glext.h>
#endif

// External OpenGL function pointers (declared in opengl_backend.c)
#ifndef __APPLE__
extern PFNGLGENBUFFERSPROC glGenBuffers;
extern PFNGLBINDBUFFERPROC glBindBuffer;
extern PFNGLBUFFERDATAPROC glBufferData;
extern PFNGLBUFFERSUBDATAPROC glBufferSubData;
extern PFNGLDELETEBUFFERSPROC glDeleteBuffers;
extern PFNGLGENVERTEXARRAYSPROC glGenVertexArrays;
extern PFNGLBINDVERTEXARRAYPROC glBindVertexArray;
extern PFNGLDELETEVERTEXARRAYSPROC glDeleteVertexArrays;
extern PFNGLENABLEVERTEXATTRIBARRAYPROC glEnableVertexAttribArray;
extern PFNGLVERTEXATTRIBPOINTERPROC glVertexAttribPointer;
extern PFNGLGENFRAMEBUFFERSPROC glGenFramebuffers;
extern PFNGLBINDFRAMEBUFFERPROC glBindFramebuffer;
extern PFNGLFRAMEBUFFERTEXTURE2DPROC glFramebufferTexture2D;
extern PFNGLCHECKFRAMEBUFFERSTATUSPROC glCheckFramebufferStatus;
extern PFNGLDELETEFRAMEBUFFERSPROC glDeleteFramebuffers;
// extern PFNGLACTIVETEXTUREPROC glActiveTexture; // Available in OpenGL 1.3+ core profile
extern PFNGLGENERATEMIPMAPPROC glGenerateMipmap;
extern PFNGLCREATESHADERPROC glCreateShader;
extern PFNGLSHADERSOURCEPROC glShaderSource;
extern PFNGLCOMPILESHADERPROC glCompileShader;
extern PFNGLGETSHADERIVPROC glGetShaderiv;
extern PFNGLGETSHADERINFOLOGPROC glGetShaderInfoLog;
extern PFNGLDELETESHADERPROC glDeleteShader;
extern PFNGLCREATEPROGRAMPROC glCreateProgram;
extern PFNGLATTACHSHADERPROC glAttachShader;
extern PFNGLLINKPROGRAMPROC glLinkProgram;
extern PFNGLGETPROGRAMIVPROC glGetProgramiv;
extern PFNGLGETPROGRAMINFOLOGPROC glGetProgramInfoLog;
extern PFNGLVALIDATEPROGRAMPROC glValidateProgram;
extern PFNGLUSEPROGRAMPROC glUseProgram;
extern PFNGLDELETEPROGRAMPROC glDeleteProgram;
extern PFNGLGETUNIFORMLOCATIONPROC glGetUniformLocation;
extern PFNGLUNIFORM1IPROC glUniform1i;
extern PFNGLUNIFORM1FPROC glUniform1f;
extern PFNGLUNIFORM2FVPROC glUniform2fv;
extern PFNGLUNIFORM3FVPROC glUniform3fv;
extern PFNGLUNIFORM4FVPROC glUniform4fv;
extern PFNGLUNIFORMMATRIX4FVPROC glUniformMatrix4fv;
#endif

// Texture management
OpenGLTexture* OpenGL_CreateTexture(TextureType type, TextureFormat format,
                                   uint32_t width, uint32_t height, uint32_t depth,
                                   uint32_t mip_levels) {
    OpenGLTexture* texture = (OpenGLTexture*)malloc(sizeof(OpenGLTexture));
    if (!texture) {
        return NULL;
    }
    
    memset(texture, 0, sizeof(OpenGLTexture));
    
    // Set texture properties
    texture->type = type;
    texture->format = format;
    texture->width = width;
    texture->height = height;
    texture->depth = depth;
    texture->mip_levels = mip_levels;
    
    // Generate OpenGL texture
    glGenTextures(1, &texture->id);
    if (texture->id == 0) {
        free(texture);
        return NULL;
    }
    
    // Determine texture target
    GLenum target;
    switch (type) {
        case TEXTURE_TYPE_2D:
            target = GL_TEXTURE_2D;
            break;
        case TEXTURE_TYPE_CUBEMAP:
            target = GL_TEXTURE_CUBE_MAP;
            break;
        case TEXTURE_TYPE_ARRAY:
            target = GL_TEXTURE_2D_ARRAY;
            break;
        default:
            target = GL_TEXTURE_2D;
            break;
    }
    
    // Bind texture and set parameters
    glBindTexture(target, texture->id);
    
    // Set texture filtering
    glTexParameteri(target, GL_TEXTURE_MIN_FILTER, mip_levels > 1 ? GL_LINEAR_MIPMAP_LINEAR : GL_LINEAR);
    glTexParameteri(target, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    
    // Set texture wrapping
    glTexParameteri(target, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(target, GL_TEXTURE_WRAP_T, GL_REPEAT);
    
    // Allocate texture storage
    GLenum internal_format = OpenGL_GetInternalFormat(format);
    GLenum pixel_format = OpenGL_GetFormat(format);
    GLenum pixel_type = OpenGL_GetType(format);
    
    if (type == TEXTURE_TYPE_2D) {
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, pixel_format, pixel_type, NULL);
    } else if (type == TEXTURE_TYPE_CUBEMAP) {
        for (int i = 0; i < 6; i++) {
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, internal_format, width, height, 0, pixel_format, pixel_type, NULL);
        }
    }
    
    // Generate mipmaps if requested
    if (mip_levels > 1) {
        glGenerateMipmap(target);
    }
    
    glBindTexture(target, 0);
    
    OpenGL_CheckError("Texture creation");
    return texture;
}

void OpenGL_DestroyTexture(OpenGLTexture* texture) {
    if (!texture) {
        return;
    }
    
    if (texture->id != 0) {
        glDeleteTextures(1, &texture->id);
    }
    
    free(texture);
}

void OpenGL_UpdateTexture(OpenGLTexture* texture, uint32_t level,
                         uint32_t x, uint32_t y, uint32_t width, uint32_t height,
                         const void* data) {
    if (!texture || !data) {
        return;
    }
    
    GLenum target = (texture->type == TEXTURE_TYPE_CUBEMAP) ? GL_TEXTURE_CUBE_MAP : GL_TEXTURE_2D;
    GLenum pixel_format = OpenGL_GetFormat(texture->format);
    GLenum pixel_type = OpenGL_GetType(texture->format);
    
    glBindTexture(target, texture->id);
    
    if (texture->type == TEXTURE_TYPE_2D) {
        glTexSubImage2D(GL_TEXTURE_2D, level, x, y, width, height, pixel_format, pixel_type, data);
    }
    
    glBindTexture(target, 0);
    
    OpenGL_CheckError("Texture update");
}

// Shader management
OpenGLShader* OpenGL_CreateShader(ShaderType type, const char* source) {
    if (!source) {
        return NULL;
    }
    
    OpenGLShader* shader = (OpenGLShader*)malloc(sizeof(OpenGLShader));
    if (!shader) {
        return NULL;
    }
    
    memset(shader, 0, sizeof(OpenGLShader));
    
    shader->type = type;
    shader->id = glCreateShader(OpenGL_GetShaderType(type));
    
    if (shader->id == 0) {
        free(shader);
        return NULL;
    }
    
    // Set shader source and compile
    glShaderSource(shader->id, 1, &source, NULL);
    glCompileShader(shader->id);
    
    // Check compilation status
    GLint compiled = 0;
    glGetShaderiv(shader->id, GL_COMPILE_STATUS, &compiled);
    
    if (!compiled) {
        GLint info_len = 0;
        glGetShaderiv(shader->id, GL_INFO_LOG_LENGTH, &info_len);
        
        if (info_len > 0) {
            char* info_log = (char*)malloc(info_len);
            glGetShaderInfoLog(shader->id, info_len, NULL, info_log);
            printf("Shader compilation error: %s\n", info_log);
            free(info_log);
        }
        
        glDeleteShader(shader->id);
        free(shader);
        return NULL;
    }
    
    shader->compiled = true;
    
    OpenGL_CheckError("Shader creation");
    return shader;
}

void OpenGL_DestroyShader(OpenGLShader* shader) {
    if (!shader) {
        return;
    }
    
    if (shader->id != 0) {
        glDeleteShader(shader->id);
    }
    
    free(shader);
}

// Shader program management
OpenGLShaderProgram* OpenGL_CreateShaderProgram(OpenGLShader* vertex_shader,
                                               OpenGLShader* fragment_shader) {
    if (!vertex_shader || !fragment_shader) {
        return NULL;
    }
    
    OpenGLShaderProgram* program = (OpenGLShaderProgram*)malloc(sizeof(OpenGLShaderProgram));
    if (!program) {
        return NULL;
    }
    
    memset(program, 0, sizeof(OpenGLShaderProgram));
    
    program->vertex_shader = vertex_shader;
    program->fragment_shader = fragment_shader;
    program->program_id = glCreateProgram();
    
    if (program->program_id == 0) {
        free(program);
        return NULL;
    }
    
    // Attach shaders
    glAttachShader(program->program_id, vertex_shader->id);
    glAttachShader(program->program_id, fragment_shader->id);
    
    // Link program
    glLinkProgram(program->program_id);
    
    // Check link status
    GLint linked = 0;
    glGetProgramiv(program->program_id, GL_LINK_STATUS, &linked);
    
    if (!linked) {
        GLint info_len = 0;
        glGetProgramiv(program->program_id, GL_INFO_LOG_LENGTH, &info_len);
        
        if (info_len > 0) {
            char* info_log = (char*)malloc(info_len);
            glGetProgramInfoLog(program->program_id, info_len, NULL, info_log);
            printf("Program link error: %s\n", info_log);
            free(info_log);
        }
        
        glDeleteProgram(program->program_id);
        free(program);
        return NULL;
    }
    
    program->linked = true;
    
    OpenGL_CheckError("Shader program creation");
    return program;
}

void OpenGL_DestroyShaderProgram(OpenGLShaderProgram* program) {
    if (!program) {
        return;
    }
    
    if (program->program_id != 0) {
        glDeleteProgram(program->program_id);
    }
    
    free(program);
}

// Buffer management
OpenGLBuffer* OpenGL_CreateBuffer(BufferType type, uint32_t size,
                                 const void* data, bool dynamic) {
    OpenGLBuffer* buffer = (OpenGLBuffer*)malloc(sizeof(OpenGLBuffer));
    if (!buffer) {
        return NULL;
    }
    
    memset(buffer, 0, sizeof(OpenGLBuffer));
    
    buffer->type = type;
    buffer->size = size;
    buffer->dynamic = dynamic;
    
    glGenBuffers(1, &buffer->id);
    if (buffer->id == 0) {
        free(buffer);
        return NULL;
    }
    
    GLenum target = OpenGL_GetBufferTarget(type);
    GLenum usage = dynamic ? GL_DYNAMIC_DRAW : GL_STATIC_DRAW;
    
    glBindBuffer(target, buffer->id);
    glBufferData(target, size, data, usage);
    glBindBuffer(target, 0);
    
    OpenGL_CheckError("Buffer creation");
    return buffer;
}

void OpenGL_DestroyBuffer(OpenGLBuffer* buffer) {
    if (!buffer) {
        return;
    }
    
    if (buffer->id != 0) {
        glDeleteBuffers(1, &buffer->id);
    }
    
    free(buffer);
}

void OpenGL_UpdateBuffer(OpenGLBuffer* buffer, uint32_t offset,
                        uint32_t size, const void* data) {
    if (!buffer || !data) {
        return;
    }
    
    GLenum target = OpenGL_GetBufferTarget(buffer->type);
    
    glBindBuffer(target, buffer->id);
    glBufferSubData(target, offset, size, data);
    glBindBuffer(target, 0);
    
    OpenGL_CheckError("Buffer update");
}

// Framebuffer management
OpenGLFramebuffer* OpenGL_CreateFramebuffer(uint32_t width, uint32_t height,
                                           OpenGLTexture** color_attachments,
                                           uint32_t color_count,
                                           OpenGLTexture* depth_attachment) {
    OpenGLFramebuffer* framebuffer = (OpenGLFramebuffer*)malloc(sizeof(OpenGLFramebuffer));
    if (!framebuffer) {
        return NULL;
    }
    
    memset(framebuffer, 0, sizeof(OpenGLFramebuffer));
    
    framebuffer->width = width;
    framebuffer->height = height;
    framebuffer->color_count = color_count;
    framebuffer->depth_attachment = depth_attachment;
    
    // Allocate color attachments array
    if (color_count > 0) {
        framebuffer->color_attachments = (OpenGLTexture**)malloc(color_count * sizeof(OpenGLTexture*));
        if (!framebuffer->color_attachments) {
            free(framebuffer);
            return NULL;
        }
        
        for (uint32_t i = 0; i < color_count; i++) {
            framebuffer->color_attachments[i] = color_attachments[i];
        }
    }
    
    glGenFramebuffers(1, &framebuffer->id);
    if (framebuffer->id == 0) {
        if (framebuffer->color_attachments) {
            free(framebuffer->color_attachments);
        }
        free(framebuffer);
        return NULL;
    }
    
    glBindFramebuffer(GL_FRAMEBUFFER, framebuffer->id);
    
    // Attach color textures
    for (uint32_t i = 0; i < color_count; i++) {
        if (color_attachments[i]) {
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + i,
                                  GL_TEXTURE_2D, color_attachments[i]->id, 0);
        }
    }
    
    // Attach depth texture
    if (depth_attachment) {
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                              GL_TEXTURE_2D, depth_attachment->id, 0);
    }
    
    // Check framebuffer completeness
    GLenum status = glCheckFramebufferStatus(GL_FRAMEBUFFER);
    if (status != GL_FRAMEBUFFER_COMPLETE) {
        printf("Framebuffer incomplete: 0x%x\n", status);
        glDeleteFramebuffers(1, &framebuffer->id);
        if (framebuffer->color_attachments) {
            free(framebuffer->color_attachments);
        }
        free(framebuffer);
        glBindFramebuffer(GL_FRAMEBUFFER, 0);
        return NULL;
    }
    
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    
    OpenGL_CheckError("Framebuffer creation");
    return framebuffer;
}

void OpenGL_DestroyFramebuffer(OpenGLFramebuffer* framebuffer) {
    if (!framebuffer) {
        return;
    }
    
    if (framebuffer->id != 0) {
        glDeleteFramebuffers(1, &framebuffer->id);
    }
    
    if (framebuffer->color_attachments) {
        free(framebuffer->color_attachments);
    }
    
    free(framebuffer);
}

// Vertex array management
OpenGLVertexArray* OpenGL_CreateVertexArray(void) {
    OpenGLVertexArray* vao = (OpenGLVertexArray*)malloc(sizeof(OpenGLVertexArray));
    if (!vao) {
        return NULL;
    }
    
    memset(vao, 0, sizeof(OpenGLVertexArray));
    
    glGenVertexArrays(1, &vao->id);
    if (vao->id == 0) {
        free(vao);
        return NULL;
    }
    
    OpenGL_CheckError("Vertex array creation");
    return vao;
}

void OpenGL_DestroyVertexArray(OpenGLVertexArray* vao) {
    if (!vao) {
        return;
    }
    
    if (vao->id != 0) {
        glDeleteVertexArrays(1, &vao->id);
    }
    
    free(vao);
}

// Uniform management
void OpenGL_SetUniformInt(OpenGLShaderProgram* program, const char* name, int value) {
    if (!program || !name) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniform1i(location, value);
    }
}

void OpenGL_SetUniformFloat(OpenGLShaderProgram* program, const char* name, float value) {
    if (!program || !name) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniform1f(location, value);
    }
}

void OpenGL_SetUniformVec2(OpenGLShaderProgram* program, const char* name, const float* value) {
    if (!program || !name || !value) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniform2fv(location, 1, value);
    }
}

void OpenGL_SetUniformVec3(OpenGLShaderProgram* program, const char* name, const float* value) {
    if (!program || !name || !value) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniform3fv(location, 1, value);
    }
}

void OpenGL_SetUniformVec4(OpenGLShaderProgram* program, const char* name, const float* value) {
    if (!program || !name || !value) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniform4fv(location, 1, value);
    }
}

void OpenGL_SetUniformMat4(OpenGLShaderProgram* program, const char* name, const float* value) {
    if (!program || !name || !value) {
        return;
    }
    
    GLint location = glGetUniformLocation(program->program_id, name);
    if (location != -1) {
        glUniformMatrix4fv(location, 1, GL_FALSE, value);
    }
} 