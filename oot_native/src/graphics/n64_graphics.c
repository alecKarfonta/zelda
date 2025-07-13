#include "graphics/n64_graphics.h"
#include "graphics/graphics_api.h"
#include "graphics/renderer_backend.h"
#include "graphics/opengl_shaders.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <stddef.h>

// OpenGL headers for GL_FLOAT and other constants
#ifdef _WIN32
    #include <windows.h>
    #include <GL/gl.h>
#elif defined(__APPLE__)
    #include <OpenGL/gl.h>
#else
    #include <GL/gl.h>
#endif

// N64 Graphics State
typedef struct {
    // Texture state
    struct {
        uint32_t format;
        uint32_t size;
        uint32_t width;
        uint32_t height;
        uintptr_t addr;
        uint8_t palette;
    } texture_image;
    
    // Tile descriptors (8 tiles)
    struct {
        uint32_t format;
        uint32_t size;
        uint32_t line;
        uint32_t tmem_addr;
        uint32_t palette;
        uint32_t cm_s, cm_t;  // Clamp modes
        uint32_t mask_s, mask_t;  // Mask values
        uint32_t shift_s, shift_t;  // Shift values
        uint32_t uls, ult, lrs, lrt;  // Tile bounds
    } tiles[8];
    
    // Color state
    struct {
        uint8_t r, g, b, a;
        uint8_t minlod;
        uint8_t primitive_lod_frac;
    } primitive_color;
    
    struct {
        uint8_t r, g, b, a;
    } blend_color;
    
    struct {
        uint8_t r, g, b, a;
    } fog_color;
    
    uint32_t fill_color;
    
    // Combiner state
    N64CombinerMode combiner_mode;
    
    // Render modes
    uint32_t other_mode_hi;
    uint32_t other_mode_lo;
    
    // Geometry mode
    uint32_t geometry_mode;
    
    // Scissor rectangle
    struct {
        uint16_t ulx, uly, lrx, lry;
    } scissor;
    
    // Viewport
    struct {
        uint16_t ulx, uly, lrx, lry;
    } viewport;
    
    // Matrix stack
    N64Matrix matrix_stack[32];
    int matrix_stack_depth;
    
    // Vertex buffer
    N64Vertex vertex_buffer[64];
    int vertex_count;
    
    // Frame buffer info
    struct {
        uint32_t format;
        uint32_t size;
        uint32_t width;
        uintptr_t addr;
    } color_image;
    
    struct {
        uintptr_t addr;
    } depth_image;
    
} N64GraphicsState;

static N64GraphicsState g_n64_state = {0};

// Forward declaration to get current renderer backend
extern RendererBackend* Renderer_GetCurrentBackend(void);

// Utility functions
static uint32_t N64_RGBA16ToRGBA32(uint16_t rgba16) {
    uint8_t r = (rgba16 >> 11) & 0x1F;
    uint8_t g = (rgba16 >> 6) & 0x1F;
    uint8_t b = (rgba16 >> 1) & 0x1F;
    uint8_t a = rgba16 & 0x01;
    
    // Expand to 8-bit
    r = (r << 3) | (r >> 2);
    g = (g << 3) | (g >> 2);
    b = (b << 3) | (b >> 2);
    a = a ? 0xFF : 0x00;
    
    return (a << 24) | (b << 16) | (g << 8) | r;
}

static uint32_t N64_IA16ToRGBA32(uint16_t ia16) {
    uint8_t i = (ia16 >> 8) & 0xFF;
    uint8_t a = ia16 & 0xFF;
    
    return (a << 24) | (i << 16) | (i << 8) | i;
}

static uint32_t N64_IA8ToRGBA32(uint8_t ia8) {
    uint8_t i = (ia8 >> 4) & 0x0F;
    uint8_t a = ia8 & 0x0F;
    
    // Expand to 8-bit
    i = (i << 4) | i;
    a = (a << 4) | a;
    
    return (a << 24) | (i << 16) | (i << 8) | i;
}

static uint32_t N64_IA4ToRGBA32(uint8_t ia4) {
    uint8_t i = (ia4 >> 1) & 0x07;
    uint8_t a = ia4 & 0x01;
    
    // Expand to 8-bit
    i = (i << 5) | (i << 2) | (i >> 1);
    a = a ? 0xFF : 0x00;
    
    return (a << 24) | (i << 16) | (i << 8) | i;
}

static uint32_t N64_I8ToRGBA32(uint8_t i8) {
    return (0xFF << 24) | (i8 << 16) | (i8 << 8) | i8;
}

static uint32_t N64_I4ToRGBA32(uint8_t i4) {
    uint8_t i = (i4 << 4) | i4;
    return (0xFF << 24) | (i << 16) | (i << 8) | i;
}

// N64 texture format conversion
void N64Graphics_ConvertTexture(N64Texture* tex, uint8_t* output) {
    if (!tex || !output) {
        return;
    }
    
    uint32_t* output32 = (uint32_t*)output;
    uint8_t* input = (uint8_t*)tex->addr;
    
    // Convert based on format and size
    switch (tex->fmt) {
        case G_IM_FMT_RGBA:
            if (tex->siz == G_IM_SIZ_16b) {
                // RGBA16
                uint16_t* input16 = (uint16_t*)input;
                for (int i = 0; i < tex->width * tex->height; i++) {
                    output32[i] = N64_RGBA16ToRGBA32(input16[i]);
                }
            } else if (tex->siz == G_IM_SIZ_32b) {
                // RGBA32
                memcpy(output, input, tex->width * tex->height * 4);
            }
            break;
            
        case G_IM_FMT_YUV:
            // YUV format - convert to RGB
            // TODO: Implement YUV to RGB conversion
            break;
            
        case G_IM_FMT_CI:
            // Color indexed - need palette lookup
            // TODO: Implement palette lookup
            break;
            
        case G_IM_FMT_IA:
            if (tex->siz == G_IM_SIZ_16b) {
                // IA16
                uint16_t* input16 = (uint16_t*)input;
                for (int i = 0; i < tex->width * tex->height; i++) {
                    output32[i] = N64_IA16ToRGBA32(input16[i]);
                }
            } else if (tex->siz == G_IM_SIZ_8b) {
                // IA8
                for (int i = 0; i < tex->width * tex->height; i++) {
                    output32[i] = N64_IA8ToRGBA32(input[i]);
                }
            } else if (tex->siz == G_IM_SIZ_4b) {
                // IA4
                for (int i = 0; i < tex->width * tex->height; i++) {
                    uint8_t ia4 = (i & 1) ? (input[i/2] & 0x0F) : (input[i/2] >> 4);
                    output32[i] = N64_IA4ToRGBA32(ia4);
                }
            }
            break;
            
        case G_IM_FMT_I:
            if (tex->siz == G_IM_SIZ_8b) {
                // I8
                for (int i = 0; i < tex->width * tex->height; i++) {
                    output32[i] = N64_I8ToRGBA32(input[i]);
                }
            } else if (tex->siz == G_IM_SIZ_4b) {
                // I4
                for (int i = 0; i < tex->width * tex->height; i++) {
                    uint8_t i4 = (i & 1) ? (input[i/2] & 0x0F) : (input[i/2] >> 4);
                    output32[i] = N64_I4ToRGBA32(i4);
                }
            }
            break;
            
        default:
            // Unknown format - fill with magenta for debugging
            for (int i = 0; i < tex->width * tex->height; i++) {
                output32[i] = 0xFF00FF; // Magenta
            }
            break;
    }
}

// N64 vertex conversion
void N64Graphics_ConvertVertex(N64Vertex* vtx, float* output) {
    if (!vtx || !output) {
        return;
    }
    
    // Convert position (fixed point to float)
    output[0] = (float)vtx->x / 4.0f;  // X
    output[1] = (float)vtx->y / 4.0f;  // Y
    output[2] = (float)vtx->z / 4.0f;  // Z
    output[3] = 1.0f;                  // W
    
    // Convert texture coordinates (fixed point to float)
    output[4] = (float)vtx->tc[0] / 32.0f;  // U
    output[5] = (float)vtx->tc[1] / 32.0f;  // V
    
    // Convert color (integer to float)
    output[6] = (float)vtx->cn[0] / 255.0f;  // R
    output[7] = (float)vtx->cn[1] / 255.0f;  // G
    output[8] = (float)vtx->cn[2] / 255.0f;  // B
    output[9] = (float)vtx->cn[3] / 255.0f;  // A
}

// N64 matrix conversion
void N64Graphics_ConvertMatrix(N64Matrix* mtx, float* output) {
    if (!mtx || !output) {
        return;
    }
    
    // Convert from N64 fixed point matrix to float matrix
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            output[i * 4 + j] = (float)mtx->m[i][j] / 65536.0f;
        }
    }
}

// Triangle submission for rendering
typedef struct {
    float position[3];    // X, Y, Z
    float texcoord[2];    // U, V  
    float color[4];       // R, G, B, A
} OpenGLVertex;

// Vertex batching system for efficient rendering
#define MAX_BATCH_VERTICES 3000  // 1000 triangles max
#define MAX_BATCH_TRIANGLES 1000

typedef struct {
    OpenGLVertex vertices[MAX_BATCH_VERTICES];
    uint32_t vertex_count;
    uint32_t triangle_count;
    Buffer* vertex_buffer;
    bool buffer_dirty;
} VertexBatch;

static VertexBatch g_vertex_batch = {0};

// Vertex batching functions
static void N64Graphics_InitVertexBatch(void) {
    RendererBackend* backend = Renderer_GetCurrentBackend();
    if (!backend) {
        return;
    }
    
    memset(&g_vertex_batch, 0, sizeof(VertexBatch));
    
    // Create reusable vertex buffer
    g_vertex_batch.vertex_buffer = backend->create_buffer(backend, BUFFER_TYPE_VERTEX,
                                                         sizeof(g_vertex_batch.vertices), 
                                                         NULL, true); // Dynamic buffer
    
    if (!g_vertex_batch.vertex_buffer) {
        printf("Failed to create vertex batch buffer\n");
        return;
    }
    
    printf("Initialized vertex batch system\n");
}

static void N64Graphics_FlushVertexBatch(void) {
    RendererBackend* backend = Renderer_GetCurrentBackend();
    if (!backend || g_vertex_batch.vertex_count == 0) {
        return;
    }
    
    if (!g_vertex_batch.vertex_buffer) {
        printf("No vertex buffer available for batch flush\n");
        return;
    }
    
    // Update vertex buffer with accumulated vertices
    backend->update_buffer(backend, g_vertex_batch.vertex_buffer, 0, 
                          g_vertex_batch.vertex_count * sizeof(OpenGLVertex),
                          g_vertex_batch.vertices);
    
    // Set up vertex layout for N64 vertices (reuse from single triangle function)
    VertexLayout layout = {0};
    layout.attribute_count = 3;
    layout.stride = sizeof(OpenGLVertex);
    
    layout.attributes[0].location = 0;
    layout.attributes[0].size = 3;
    layout.attributes[0].type = GL_FLOAT;
    layout.attributes[0].normalized = false;
    layout.attributes[0].stride = sizeof(OpenGLVertex);
    layout.attributes[0].offset = offsetof(OpenGLVertex, position);
    
    layout.attributes[1].location = 1;
    layout.attributes[1].size = 2;
    layout.attributes[1].type = GL_FLOAT;
    layout.attributes[1].normalized = false;
    layout.attributes[1].stride = sizeof(OpenGLVertex);
    layout.attributes[1].offset = offsetof(OpenGLVertex, texcoord);
    
    layout.attributes[2].location = 2;
    layout.attributes[2].size = 4;
    layout.attributes[2].type = GL_FLOAT;
    layout.attributes[2].normalized = false;
    layout.attributes[2].stride = sizeof(OpenGLVertex);
    layout.attributes[2].offset = offsetof(OpenGLVertex, color);
    
    // Set render state
    RenderState render_state = {0};
    render_state.blend_mode = BLEND_MODE_ALPHA;
    render_state.depth_test = DEPTH_TEST_LEQUAL;
    render_state.cull_mode = CULL_MODE_BACK;
    render_state.depth_write = true;
    render_state.alpha_test = false;
    render_state.alpha_ref = 0.0f;
    render_state.scissor_test = false;
    
    // Use basic color shader
    if (!ShaderManager_UseProgram(SHADER_PROGRAM_BASIC_COLOR)) {
        printf("Failed to use basic color shader for batch\n");
        return;
    }
    
    // Set uniforms
    float identity_matrix[16] = {
        1.0f, 0.0f, 0.0f, 0.0f,
        0.0f, 1.0f, 0.0f, 0.0f,
        0.0f, 0.0f, 1.0f, 0.0f,
        0.0f, 0.0f, 0.0f, 1.0f
    };
    
    backend->set_uniform_mat4(backend, "uProjection", identity_matrix);
    backend->set_uniform_mat4(backend, "uModelView", identity_matrix);
    backend->set_uniform_mat4(backend, "uTransform", identity_matrix);
    
    float primitive_color[4] = {
        (float)g_n64_state.primitive_color.r / 255.0f,
        (float)g_n64_state.primitive_color.g / 255.0f,
        (float)g_n64_state.primitive_color.b / 255.0f,
        (float)g_n64_state.primitive_color.a / 255.0f
    };
    backend->set_uniform_vec4(backend, "uPrimitiveColor", primitive_color);
    backend->set_uniform_float(backend, "uAlphaRef", 0.1f);
    
    // Set state and draw
    backend->set_render_state(backend, &render_state);
    backend->set_vertex_layout(backend, &layout);
    backend->bind_buffer(backend, BUFFER_TYPE_VERTEX, g_vertex_batch.vertex_buffer);
    
    DrawCommand draw_cmd = {0};
    draw_cmd.primitive = PRIMITIVE_TRIANGLES;
    draw_cmd.first_vertex = 0;
    draw_cmd.vertex_count = g_vertex_batch.vertex_count;
    draw_cmd.instance_count = 1;
    
    backend->draw(backend, &draw_cmd);
    
    printf("Flushed vertex batch: %d vertices (%d triangles)\n", 
           g_vertex_batch.vertex_count, g_vertex_batch.triangle_count);
    
    // Reset batch
    g_vertex_batch.vertex_count = 0;
    g_vertex_batch.triangle_count = 0;
    g_vertex_batch.buffer_dirty = false;
}

static void N64Graphics_DestroyVertexBatch(void) {
    RendererBackend* backend = Renderer_GetCurrentBackend();
    if (!backend) {
        return;
    }
    
    // Flush any remaining vertices
    N64Graphics_FlushVertexBatch();
    
    // Clean up vertex buffer
    if (g_vertex_batch.vertex_buffer) {
        backend->destroy_buffer(backend, g_vertex_batch.vertex_buffer);
        g_vertex_batch.vertex_buffer = NULL;
    }
    
    memset(&g_vertex_batch, 0, sizeof(VertexBatch));
    printf("Destroyed vertex batch system\n");
}

static void N64Graphics_AddTriangleToBatch(uint8_t v0, uint8_t v1, uint8_t v2) {
    // Check if batch is full
    if (g_vertex_batch.vertex_count + 3 > MAX_BATCH_VERTICES) {
        N64Graphics_FlushVertexBatch();
    }
    
    // Validate vertex indices
    if (v0 >= g_n64_state.vertex_count || v1 >= g_n64_state.vertex_count || v2 >= g_n64_state.vertex_count) {
        printf("Invalid vertex indices for batch: v%d v%d v%d (max: %d)\n", v0, v1, v2, g_n64_state.vertex_count);
        return;
    }
    
    // Add triangle vertices to batch
    uint8_t indices[3] = {v0, v1, v2};
    for (int i = 0; i < 3; i++) {
        N64Vertex* n64_vtx = &g_n64_state.vertex_buffer[indices[i]];
        OpenGLVertex* gl_vtx = &g_vertex_batch.vertices[g_vertex_batch.vertex_count];
        
        // Convert position (N64 fixed point to float)
        gl_vtx->position[0] = (float)n64_vtx->x / 4.0f;
        gl_vtx->position[1] = (float)n64_vtx->y / 4.0f;
        gl_vtx->position[2] = (float)n64_vtx->z / 4.0f;
        
        // Convert texture coordinates (N64 fixed point to float)
        gl_vtx->texcoord[0] = (float)n64_vtx->tc[0] / 32.0f;
        gl_vtx->texcoord[1] = (float)n64_vtx->tc[1] / 32.0f;
        
        // Convert color (integer to float)
        gl_vtx->color[0] = (float)n64_vtx->cn[0] / 255.0f;
        gl_vtx->color[1] = (float)n64_vtx->cn[1] / 255.0f;
        gl_vtx->color[2] = (float)n64_vtx->cn[2] / 255.0f;
        gl_vtx->color[3] = (float)n64_vtx->cn[3] / 255.0f;
        
        g_vertex_batch.vertex_count++;
    }
    
    g_vertex_batch.triangle_count++;
    g_vertex_batch.buffer_dirty = true;
}

static void N64Graphics_SubmitTriangle(uint8_t v0, uint8_t v1, uint8_t v2) {
    // Use the efficient vertex batching system
    N64Graphics_AddTriangleToBatch(v0, v1, v2);
}

// N64 command processing
void N64Graphics_ProcessCommand(GraphicsCommand* cmd) {
    if (!cmd) {
        return;
    }
    
    switch (cmd->opcode) {
        case G_SETCIMG:
            // Set color image
            g_n64_state.color_image.format = cmd->params.setcimg.fmt;
            g_n64_state.color_image.size = cmd->params.setcimg.siz;
            g_n64_state.color_image.width = cmd->params.setcimg.width;
            g_n64_state.color_image.addr = cmd->params.setcimg.addr;
            break;
            
        case G_SETZIMG:
            // Set depth image
            g_n64_state.depth_image.addr = cmd->params.setzimg.addr;
            break;
            
        case G_SETTIMG:
            // Set texture image
            g_n64_state.texture_image.format = cmd->params.settimg.fmt;
            g_n64_state.texture_image.size = cmd->params.settimg.siz;
            g_n64_state.texture_image.width = cmd->params.settimg.width;
            g_n64_state.texture_image.addr = cmd->params.settimg.addr;
            break;
            
        case G_SETPRIMCOLOR:
            // Set primitive color
            g_n64_state.primitive_color.r = cmd->params.setprimcolor.r;
            g_n64_state.primitive_color.g = cmd->params.setprimcolor.g;
            g_n64_state.primitive_color.b = cmd->params.setprimcolor.b;
            g_n64_state.primitive_color.a = cmd->params.setprimcolor.a;
            g_n64_state.primitive_color.minlod = cmd->params.setprimcolor.minlod;
            g_n64_state.primitive_color.primitive_lod_frac = cmd->params.setprimcolor.primitive_lod_frac;
            break;
            
        case G_SETBLENDCOLOR:
            // Set blend color
            g_n64_state.blend_color.r = cmd->params.setblendcolor.r;
            g_n64_state.blend_color.g = cmd->params.setblendcolor.g;
            g_n64_state.blend_color.b = cmd->params.setblendcolor.b;
            g_n64_state.blend_color.a = cmd->params.setblendcolor.a;
            break;
            
        case G_SETFOGCOLOR:
            // Set fog color
            g_n64_state.fog_color.r = cmd->params.setfogcolor.r;
            g_n64_state.fog_color.g = cmd->params.setfogcolor.g;
            g_n64_state.fog_color.b = cmd->params.setfogcolor.b;
            g_n64_state.fog_color.a = cmd->params.setfogcolor.a;
            break;
            
        case G_SETFILLCOLOR:
            // Set fill color
            g_n64_state.fill_color = cmd->params.setfillcolor.color;
            break;
            
        case G_FILLRECT:
            // Fill rectangle
            // TODO: Implement rectangle filling
            break;
            
        case G_SETTILE:
            // Set tile descriptor
            {
                uint8_t tile = cmd->params.settile.tile;
                if (tile < 8) {
                    g_n64_state.tiles[tile].format = cmd->params.settile.fmt;
                    g_n64_state.tiles[tile].size = cmd->params.settile.siz;
                    g_n64_state.tiles[tile].line = cmd->params.settile.line;
                    g_n64_state.tiles[tile].tmem_addr = cmd->params.settile.tmem;
                    g_n64_state.tiles[tile].palette = cmd->params.settile.palette;
                    g_n64_state.tiles[tile].cm_s = cmd->params.settile.cms;
                    g_n64_state.tiles[tile].cm_t = cmd->params.settile.cmt;
                    g_n64_state.tiles[tile].mask_s = cmd->params.settile.masks;
                    g_n64_state.tiles[tile].mask_t = cmd->params.settile.maskt;
                    g_n64_state.tiles[tile].shift_s = cmd->params.settile.shifts;
                    g_n64_state.tiles[tile].shift_t = cmd->params.settile.shiftt;
                }
            }
            break;
            
        case G_LOADTILE:
            // Load tile
            // TODO: Implement tile loading
            break;
            
        case G_LOADBLOCK:
            // Load block
            // TODO: Implement block loading
            break;
            
        case G_SETTILESIZE:
            // Set tile size
            {
                uint8_t tile = cmd->params.settilesize.tile;
                if (tile < 8) {
                    g_n64_state.tiles[tile].uls = cmd->params.settilesize.uls;
                    g_n64_state.tiles[tile].ult = cmd->params.settilesize.ult;
                    g_n64_state.tiles[tile].lrs = cmd->params.settilesize.lrs;
                    g_n64_state.tiles[tile].lrt = cmd->params.settilesize.lrt;
                }
            }
            break;
            
        case G_SETSCISSOR:
            // Set scissor rectangle
            g_n64_state.scissor.ulx = cmd->params.setscissor.ulx;
            g_n64_state.scissor.uly = cmd->params.setscissor.uly;
            g_n64_state.scissor.lrx = cmd->params.setscissor.lrx;
            g_n64_state.scissor.lry = cmd->params.setscissor.lry;
            break;
            
        case G_RDPSETOTHERMODE:
            // Set other mode
            g_n64_state.other_mode_hi = cmd->params.rdpsetothermode.modehi;
            g_n64_state.other_mode_lo = cmd->params.rdpsetothermode.modelo;
            break;
            
        case G_GEOMETRYMODE:
            // Set geometry mode
            g_n64_state.geometry_mode &= ~cmd->params.geometrymode.clear;
            g_n64_state.geometry_mode |= cmd->params.geometrymode.set;
            break;
            
        case G_VTX:
            // Load vertices
            {
                uint8_t n = cmd->params.vtx.n;
                uint8_t vbidx = cmd->params.vtx.vbidx;
                uintptr_t addr = cmd->params.vtx.addr;
                
                // Load vertices from address
                N64Vertex* vertices = (N64Vertex*)addr;
                for (int i = 0; i < n && (vbidx + i) < 64; i++) {
                    g_n64_state.vertex_buffer[vbidx + i] = vertices[i];
                }
                
                g_n64_state.vertex_count = vbidx + n;
            }
            break;
            
        case G_TRI1:
            // Draw triangle
            {
                uint8_t v0 = cmd->params.tri1.v0;
                uint8_t v1 = cmd->params.tri1.v1;
                uint8_t v2 = cmd->params.tri1.v2;
                
                N64Graphics_SubmitTriangle(v0, v1, v2);
            }
            break;
            
        case G_TRI2:
            // Draw two triangles
            {
                uint8_t v0 = cmd->params.tri2.v0;
                uint8_t v1 = cmd->params.tri2.v1;
                uint8_t v2 = cmd->params.tri2.v2;
                uint8_t v3 = cmd->params.tri2.v3;
                uint8_t v4 = cmd->params.tri2.v4;
                uint8_t v5 = cmd->params.tri2.v5;
                
                N64Graphics_SubmitTriangle(v0, v1, v2);
                N64Graphics_SubmitTriangle(v3, v4, v5);
            }
            break;
            
        case G_QUAD:
            // Draw quad (as two triangles)
            {
                uint8_t v0 = cmd->params.quad.v0;
                uint8_t v1 = cmd->params.quad.v1;
                uint8_t v2 = cmd->params.quad.v2;
                uint8_t v3 = cmd->params.quad.v3;
                
                // Submit quad as two triangles: (v0,v1,v2) and (v0,v2,v3)
                N64Graphics_SubmitTriangle(v0, v1, v2);
                N64Graphics_SubmitTriangle(v0, v2, v3);
            }
            break;
            
        case G_TEXRECT:
            // Draw textured rectangle
            // TODO: Implement textured rectangle
            break;
            
        case G_TEXRECTFLIP:
            // Draw flipped textured rectangle
            // TODO: Implement flipped textured rectangle
            break;
            
        case G_RDPFULLSYNC:
            // Full sync - wait for RDP to finish
            // TODO: Implement sync
            break;
            
        case G_RDPTILESYNC:
            // Tile sync
            // TODO: Implement tile sync
            break;
            
        case G_RDPPIPESYNC:
            // Pipe sync
            // TODO: Implement pipe sync
            break;
            
        case G_RDPLOADSYNC:
            // Load sync
            // TODO: Implement load sync
            break;
            
        case G_ENDDL:
            // End display list
            printf("End display list\n");
            break;
            
        default:
            // Unknown command
            printf("Unknown N64 command: 0x%02X\n", cmd->opcode);
            break;
    }
}

// Process display list
void N64Graphics_ProcessDisplayList(uintptr_t addr) {
    if (addr == 0) {
        return;
    }
    
    GraphicsCommand* commands = (GraphicsCommand*)addr;
    
    // Process commands until we hit an end marker
    for (int i = 0; i < 1000; i++) {  // Safety limit
        GraphicsCommand* cmd = &commands[i];
        
        N64Graphics_ProcessCommand(cmd);
        
        if (cmd->opcode == G_ENDDL) {
            break;
        }
    }
}

// N64 graphics system lifecycle functions
void N64Graphics_Init(void) {
    memset(&g_n64_state, 0, sizeof(N64GraphicsState));
    
    // Initialize vertex batch system
    N64Graphics_InitVertexBatch();
    
    printf("N64 graphics system initialized\n");
}

void N64Graphics_Shutdown(void) {
    // Destroy vertex batch system
    N64Graphics_DestroyVertexBatch();
    
    memset(&g_n64_state, 0, sizeof(N64GraphicsState));
    printf("N64 graphics system shutdown\n");
}

void N64Graphics_BeginFrame(void) {
    // Reset frame state
    g_n64_state.vertex_count = 0;
    g_n64_state.matrix_stack_depth = 0;
    
    // Clear any pending vertex batch
    N64Graphics_FlushVertexBatch();
}

void N64Graphics_EndFrame(void) {
    // Flush any remaining vertices in the batch
    N64Graphics_FlushVertexBatch();
} 