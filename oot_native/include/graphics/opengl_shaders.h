#pragma once

#include "graphics/opengl_backend.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Shader types for N64 rendering
typedef enum {
    SHADER_PROGRAM_BASIC_COLOR,     // Basic colored vertices (no texture)
    SHADER_PROGRAM_BASIC_TEXTURE,   // Basic textured rendering
    SHADER_PROGRAM_N64_COMBINER,    // N64 combiner mode emulation
    SHADER_PROGRAM_COUNT
} ShaderProgramType;

// Default shader source strings
extern const char* g_vertex_shader_basic;
extern const char* g_fragment_shader_color;
extern const char* g_fragment_shader_texture;

// Shader program management
typedef struct {
    ShaderProgramType type;
    OpenGLShaderProgram* program;
    OpenGLShader* vertex_shader;
    OpenGLShader* fragment_shader;
    bool is_loaded;
} ShaderProgramEntry;

// Global shader manager
typedef struct {
    bool initialized;
    ShaderProgramEntry programs[SHADER_PROGRAM_COUNT];
    ShaderProgramEntry* current_program;
    OpenGLBackendData* backend_data;
} ShaderManager;

// Shader manager functions
bool ShaderManager_Init(OpenGLBackendData* backend_data);
void ShaderManager_Shutdown(void);

// Shader program management
bool ShaderManager_LoadDefaultShaders(void);
OpenGLShaderProgram* ShaderManager_GetProgram(ShaderProgramType type);
bool ShaderManager_UseProgram(ShaderProgramType type);
OpenGLShaderProgram* ShaderManager_GetCurrentProgram(void);

// Default shader creation
OpenGLShaderProgram* ShaderManager_CreateBasicColorProgram(void);
OpenGLShaderProgram* ShaderManager_CreateBasicTextureProgram(void);

// Shader compilation utilities
OpenGLShader* ShaderManager_CompileShader(ShaderType type, const char* source);
OpenGLShaderProgram* ShaderManager_LinkProgram(OpenGLShader* vertex, OpenGLShader* fragment);

// Utility functions
const char* ShaderManager_GetShaderTypeName(ShaderType type);
const char* ShaderManager_GetProgramTypeName(ShaderProgramType type);

#ifdef __cplusplus
}
#endif 