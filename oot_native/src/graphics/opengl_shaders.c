#include "graphics/opengl_shaders.h"
#include "graphics/opengl_backend.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// Global shader manager instance
static ShaderManager g_shader_manager = {0};

// Default vertex shader - handles N64 vertex format
const char* g_vertex_shader_basic = 
    "#version 330 core\n"
    "layout (location = 0) in vec3 aPosition;\n"
    "layout (location = 1) in vec2 aTexCoord;\n"
    "layout (location = 2) in vec4 aColor;\n"
    "\n"
    "uniform mat4 uProjection;\n"
    "uniform mat4 uModelView;\n"
    "uniform mat4 uTransform;\n"
    "\n"
    "out vec2 vTexCoord;\n"
    "out vec4 vColor;\n"
    "\n"
    "void main() {\n"
    "    gl_Position = uProjection * uModelView * uTransform * vec4(aPosition, 1.0);\n"
    "    vTexCoord = aTexCoord;\n"
    "    vColor = aColor;\n"
    "}\n";

// Basic color fragment shader - for untextured primitives
const char* g_fragment_shader_color = 
    "#version 330 core\n"
    "in vec4 vColor;\n"
    "\n"
    "uniform vec4 uPrimitiveColor;\n"
    "uniform float uAlphaRef;\n"
    "\n"
    "out vec4 fragColor;\n"
    "\n"
    "void main() {\n"
    "    vec4 color = vColor * uPrimitiveColor;\n"
    "    \n"
    "    // Simple alpha test\n"
    "    if (color.a < uAlphaRef) {\n"
    "        discard;\n"
    "    }\n"
    "    \n"
    "    fragColor = color;\n"
    "}\n";

// Basic texture fragment shader - for textured primitives
const char* g_fragment_shader_texture = 
    "#version 330 core\n"
    "in vec2 vTexCoord;\n"
    "in vec4 vColor;\n"
    "\n"
    "uniform sampler2D uTexture0;\n"
    "uniform vec4 uPrimitiveColor;\n"
    "uniform float uAlphaRef;\n"
    "uniform bool uUseTexture;\n"
    "\n"
    "out vec4 fragColor;\n"
    "\n"
    "void main() {\n"
    "    vec4 texColor = vec4(1.0);\n"
    "    \n"
    "    if (uUseTexture) {\n"
    "        texColor = texture(uTexture0, vTexCoord);\n"
    "    }\n"
    "    \n"
    "    vec4 color = vColor * uPrimitiveColor * texColor;\n"
    "    \n"
    "    // Simple alpha test\n"
    "    if (color.a < uAlphaRef) {\n"
    "        discard;\n"
    "    }\n"
    "    \n"
    "    fragColor = color;\n"
    "}\n";

// Shader manager functions
bool ShaderManager_Init(OpenGLBackendData* backend_data) {
    if (g_shader_manager.initialized) {
        return true;
    }
    
    if (!backend_data) {
        printf("ShaderManager_Init: Invalid backend data\n");
        return false;
    }
    
    // Initialize shader manager
    memset(&g_shader_manager, 0, sizeof(ShaderManager));
    g_shader_manager.backend_data = backend_data;
    
    // Load default shaders
    if (!ShaderManager_LoadDefaultShaders()) {
        printf("ShaderManager_Init: Failed to load default shaders\n");
        return false;
    }
    
    g_shader_manager.initialized = true;
    printf("Shader manager initialized successfully\n");
    return true;
}

void ShaderManager_Shutdown(void) {
    if (!g_shader_manager.initialized) {
        return;
    }
    
    // Free all shader programs
    for (int i = 0; i < SHADER_PROGRAM_COUNT; i++) {
        ShaderProgramEntry* entry = &g_shader_manager.programs[i];
        if (entry->is_loaded) {
            if (entry->program) {
                OpenGL_DestroyShaderProgram(entry->program);
            }
            if (entry->vertex_shader) {
                OpenGL_DestroyShader(entry->vertex_shader);
            }
            if (entry->fragment_shader) {
                OpenGL_DestroyShader(entry->fragment_shader);
            }
        }
    }
    
    memset(&g_shader_manager, 0, sizeof(ShaderManager));
    printf("Shader manager shutdown complete\n");
}

// Shader compilation utilities
OpenGLShader* ShaderManager_CompileShader(ShaderType type, const char* source) {
    if (!source) {
        printf("ShaderManager_CompileShader: NULL source\n");
        return NULL;
    }
    
    OpenGLShader* shader = OpenGL_CreateShader(type, source);
    if (!shader) {
        printf("ShaderManager_CompileShader: Failed to compile %s shader\n", 
               ShaderManager_GetShaderTypeName(type));
        return NULL;
    }
    
    printf("Compiled %s shader successfully\n", ShaderManager_GetShaderTypeName(type));
    return shader;
}

OpenGLShaderProgram* ShaderManager_LinkProgram(OpenGLShader* vertex, OpenGLShader* fragment) {
    if (!vertex || !fragment) {
        printf("ShaderManager_LinkProgram: Invalid shaders\n");
        return NULL;
    }
    
    OpenGLShaderProgram* program = OpenGL_CreateShaderProgram(vertex, fragment);
    if (!program || !program->linked) {
        printf("ShaderManager_LinkProgram: Failed to link shader program\n");
        return NULL;
    }
    
    printf("Linked shader program successfully\n");
    return program;
}

// Default shader creation
OpenGLShaderProgram* ShaderManager_CreateBasicColorProgram(void) {
    // Compile vertex shader
    OpenGLShader* vertex = ShaderManager_CompileShader(SHADER_TYPE_VERTEX, g_vertex_shader_basic);
    if (!vertex) {
        return NULL;
    }
    
    // Compile fragment shader
    OpenGLShader* fragment = ShaderManager_CompileShader(SHADER_TYPE_FRAGMENT, g_fragment_shader_color);
    if (!fragment) {
        OpenGL_DestroyShader(vertex);
        return NULL;
    }
    
    // Link program
    OpenGLShaderProgram* program = ShaderManager_LinkProgram(vertex, fragment);
    if (!program) {
        OpenGL_DestroyShader(vertex);
        OpenGL_DestroyShader(fragment);
        return NULL;
    }
    
    return program;
}

OpenGLShaderProgram* ShaderManager_CreateBasicTextureProgram(void) {
    // Compile vertex shader
    OpenGLShader* vertex = ShaderManager_CompileShader(SHADER_TYPE_VERTEX, g_vertex_shader_basic);
    if (!vertex) {
        return NULL;
    }
    
    // Compile fragment shader
    OpenGLShader* fragment = ShaderManager_CompileShader(SHADER_TYPE_FRAGMENT, g_fragment_shader_texture);
    if (!fragment) {
        OpenGL_DestroyShader(vertex);
        return NULL;
    }
    
    // Link program
    OpenGLShaderProgram* program = ShaderManager_LinkProgram(vertex, fragment);
    if (!program) {
        OpenGL_DestroyShader(vertex);
        OpenGL_DestroyShader(fragment);
        return NULL;
    }
    
    return program;
}

// Shader program management
bool ShaderManager_LoadDefaultShaders(void) {
    // Load basic color shader
    ShaderProgramEntry* color_entry = &g_shader_manager.programs[SHADER_PROGRAM_BASIC_COLOR];
    color_entry->type = SHADER_PROGRAM_BASIC_COLOR;
    color_entry->vertex_shader = ShaderManager_CompileShader(SHADER_TYPE_VERTEX, g_vertex_shader_basic);
    color_entry->fragment_shader = ShaderManager_CompileShader(SHADER_TYPE_FRAGMENT, g_fragment_shader_color);
    
    if (!color_entry->vertex_shader || !color_entry->fragment_shader) {
        printf("Failed to compile basic color shaders\n");
        return false;
    }
    
    color_entry->program = ShaderManager_LinkProgram(color_entry->vertex_shader, color_entry->fragment_shader);
    if (!color_entry->program) {
        printf("Failed to link basic color program\n");
        return false;
    }
    color_entry->is_loaded = true;
    
    // Load basic texture shader
    ShaderProgramEntry* texture_entry = &g_shader_manager.programs[SHADER_PROGRAM_BASIC_TEXTURE];
    texture_entry->type = SHADER_PROGRAM_BASIC_TEXTURE;
    texture_entry->vertex_shader = ShaderManager_CompileShader(SHADER_TYPE_VERTEX, g_vertex_shader_basic);
    texture_entry->fragment_shader = ShaderManager_CompileShader(SHADER_TYPE_FRAGMENT, g_fragment_shader_texture);
    
    if (!texture_entry->vertex_shader || !texture_entry->fragment_shader) {
        printf("Failed to compile basic texture shaders\n");
        return false;
    }
    
    texture_entry->program = ShaderManager_LinkProgram(texture_entry->vertex_shader, texture_entry->fragment_shader);
    if (!texture_entry->program) {
        printf("Failed to link basic texture program\n");
        return false;
    }
    texture_entry->is_loaded = true;
    
    // Set default program to basic color
    g_shader_manager.current_program = color_entry;
    
    printf("Loaded default shaders successfully\n");
    return true;
}

OpenGLShaderProgram* ShaderManager_GetProgram(ShaderProgramType type) {
    if (type >= SHADER_PROGRAM_COUNT) {
        return NULL;
    }
    
    ShaderProgramEntry* entry = &g_shader_manager.programs[type];
    if (!entry->is_loaded) {
        return NULL;
    }
    
    return entry->program;
}

bool ShaderManager_UseProgram(ShaderProgramType type) {
    if (type >= SHADER_PROGRAM_COUNT) {
        return false;
    }
    
    ShaderProgramEntry* entry = &g_shader_manager.programs[type];
    if (!entry->is_loaded || !entry->program) {
        return false;
    }
    
    glUseProgram(entry->program->program_id);
    g_shader_manager.current_program = entry;
    
    OpenGL_CheckError("Use shader program");
    return true;
}

OpenGLShaderProgram* ShaderManager_GetCurrentProgram(void) {
    if (!g_shader_manager.current_program) {
        return NULL;
    }
    
    return g_shader_manager.current_program->program;
}

// Utility functions
const char* ShaderManager_GetShaderTypeName(ShaderType type) {
    switch (type) {
        case SHADER_TYPE_VERTEX: return "vertex";
        case SHADER_TYPE_FRAGMENT: return "fragment";
        case SHADER_TYPE_GEOMETRY: return "geometry";
        case SHADER_TYPE_COMPUTE: return "compute";
        default: return "unknown";
    }
}

const char* ShaderManager_GetProgramTypeName(ShaderProgramType type) {
    switch (type) {
        case SHADER_PROGRAM_BASIC_COLOR: return "basic_color";
        case SHADER_PROGRAM_BASIC_TEXTURE: return "basic_texture";
        case SHADER_PROGRAM_N64_COMBINER: return "n64_combiner";
        default: return "unknown";
    }
} 