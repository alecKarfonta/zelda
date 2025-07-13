#include "graphics/graphics_api.h"
#include "graphics/n64_graphics.h"
#include "graphics/opengl_backend.h"
#include "graphics/opengl_shaders.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// For Windows console applications, tell SDL we handle main ourselves
#ifdef _WIN32
#define SDL_MAIN_HANDLED
#endif

// SDL2 for window creation and OpenGL context
#include <SDL2/SDL.h>
#include <GL/gl.h>

// Test window dimensions
#define TEST_WINDOW_WIDTH 800
#define TEST_WINDOW_HEIGHT 600

// Global test state
static SDL_Window* g_window = NULL;
static SDL_GLContext g_gl_context = NULL;
static RendererBackend* g_renderer = NULL;

// Sample N64 vertex data for testing
static N64Vertex test_vertices[] = {
    // Triangle 1 - Red triangle
    { .x = 0,   .y = 100,  .z = 0,   .flag = 0, .tc = {0, 0},     .cn = {255, 0, 0, 255} },
    { .x = -87, .y = -50,  .z = 0,   .flag = 0, .tc = {0, 32},    .cn = {255, 0, 0, 255} },
    { .x = 87,  .y = -50,  .z = 0,   .flag = 0, .tc = {32, 32},   .cn = {255, 0, 0, 255} },
    
    // Triangle 2 - Green triangle
    { .x = 200, .y = 100,  .z = 0,   .flag = 0, .tc = {0, 0},     .cn = {0, 255, 0, 255} },
    { .x = 113, .y = -50,  .z = 0,   .flag = 0, .tc = {0, 32},    .cn = {0, 255, 0, 255} },
    { .x = 287, .y = -50,  .z = 0,   .flag = 0, .tc = {32, 32},   .cn = {0, 255, 0, 255} },
    
    // Triangle 3 - Blue triangle
    { .x = -200, .y = 100, .z = 0,   .flag = 0, .tc = {0, 0},     .cn = {0, 0, 255, 255} },
    { .x = -287, .y = -50, .z = 0,   .flag = 0, .tc = {0, 32},    .cn = {0, 0, 255, 255} },
    { .x = -113, .y = -50, .z = 0,   .flag = 0, .tc = {32, 32},   .cn = {0, 0, 255, 255} },
};

// Sample N64 graphics commands for testing
static GraphicsCommand test_commands[6];

// Initialize test commands at runtime
static void init_test_commands(void) {
    // Set primitive color to white
    test_commands[0].opcode = G_SETPRIMCOLOR;
    test_commands[0].params.setprimcolor = (typeof(test_commands[0].params.setprimcolor)){255, 255, 255, 255, 0, 0};
    
    // Load vertices
    test_commands[1].opcode = G_VTX;
    test_commands[1].params.vtx = (typeof(test_commands[1].params.vtx)){.n = 9, .vbidx = 0, .addr = (uintptr_t)test_vertices};
    
    // Draw three triangles
    test_commands[2].opcode = G_TRI1;
    test_commands[2].params.tri1 = (typeof(test_commands[2].params.tri1)){.v0 = 0, .v1 = 1, .v2 = 2, .flag = 0};
    
    test_commands[3].opcode = G_TRI1;
    test_commands[3].params.tri1 = (typeof(test_commands[3].params.tri1)){.v0 = 3, .v1 = 4, .v2 = 5, .flag = 0};
    
    test_commands[4].opcode = G_TRI1;
    test_commands[4].params.tri1 = (typeof(test_commands[4].params.tri1)){.v0 = 6, .v1 = 7, .v2 = 8, .flag = 0};
    
    // End display list
    test_commands[5].opcode = G_ENDDL;
}

// Test functions
static bool Test_InitSDL(void) {
#ifdef _WIN32
    // Required when using SDL_MAIN_HANDLED
    SDL_SetMainReady();
#endif
    
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL initialization failed: %s\n", SDL_GetError());
        return false;
    }
    
    // Set OpenGL attributes
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
    SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 24);
    
    // Create window
    g_window = SDL_CreateWindow("OOT Native Graphics Test",
                               SDL_WINDOWPOS_UNDEFINED,
                               SDL_WINDOWPOS_UNDEFINED,
                               TEST_WINDOW_WIDTH,
                               TEST_WINDOW_HEIGHT,
                               SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN);
    
    if (!g_window) {
        printf("Window creation failed: %s\n", SDL_GetError());
        return false;
    }
    
    // Create OpenGL context
    g_gl_context = SDL_GL_CreateContext(g_window);
    if (!g_gl_context) {
        printf("OpenGL context creation failed: %s\n", SDL_GetError());
        return false;
    }
    
    // Enable vsync
    SDL_GL_SetSwapInterval(1);
    
    printf("SDL and OpenGL initialized successfully\n");
    printf("OpenGL Version: %s\n", glGetString(GL_VERSION));
    printf("OpenGL Vendor: %s\n", glGetString(GL_VENDOR));
    printf("OpenGL Renderer: %s\n", glGetString(GL_RENDERER));
    
    return true;
}

static bool Test_InitGraphics(void) {
    // Initialize graphics API
    GraphicsConfig config = {
        .width = TEST_WINDOW_WIDTH,
        .height = TEST_WINDOW_HEIGHT,
        .fullscreen = false,
        .vsync = true,
        .backend = GRAPHICS_BACKEND_OPENGL
    };
    
    if (!Graphics_Init(&config)) {
        printf("Graphics API initialization failed\n");
        return false;
    }
    
    // Get renderer backend
    g_renderer = Graphics_GetRenderer();
    if (!g_renderer) {
        printf("Failed to get renderer backend\n");
        return false;
    }
    
    // Initialize N64 graphics system
    N64Graphics_Init();
    
    printf("Graphics system initialized successfully\n");
    return true;
}

static void Test_RenderFrame(void) {
    // Begin frame
    N64Graphics_BeginFrame();
    
    // Clear screen
    g_renderer->clear(g_renderer, true, true, false, 0.2f, 0.3f, 0.4f, 1.0f, 1.0f, 0);
    
    // Set viewport
    g_renderer->viewport(g_renderer, 0, 0, TEST_WINDOW_WIDTH, TEST_WINDOW_HEIGHT);
    
    // Process test commands
    for (size_t i = 0; i < 6; i++) {
        N64Graphics_ProcessCommand(&test_commands[i]);
    }
    
    // End frame
    N64Graphics_EndFrame();
    
    // Present
    g_renderer->present(g_renderer);
}

static void Test_Cleanup(void) {
    // Shutdown graphics
    N64Graphics_Shutdown();
    Graphics_Shutdown();
    
    // Cleanup SDL
    if (g_gl_context) {
        SDL_GL_DeleteContext(g_gl_context);
        g_gl_context = NULL;
    }
    
    if (g_window) {
        SDL_DestroyWindow(g_window);
        g_window = NULL;
    }
    
    SDL_Quit();
    printf("Test cleanup complete\n");
}

static void Test_RunMainLoop(void) {
    bool running = true;
    SDL_Event event;
    
    printf("Starting main loop - press ESC to exit\n");
    
    while (running) {
        // Handle events
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_QUIT:
                    running = false;
                    break;
                    
                case SDL_KEYDOWN:
                    if (event.key.keysym.sym == SDLK_ESCAPE) {
                        running = false;
                    }
                    break;
            }
        }
        
        // Render frame
        Test_RenderFrame();
        
        // Swap buffers
        SDL_GL_SwapWindow(g_window);
    }
}

// Performance test function
static void Test_Performance(void) {
    printf("\n=== PERFORMANCE TEST ===\n");
    
    const int num_frames = 1000;
    uint32_t start_time = SDL_GetTicks();
    
    for (int i = 0; i < num_frames; i++) {
        Test_RenderFrame();
    }
    
    uint32_t end_time = SDL_GetTicks();
    float elapsed = (end_time - start_time) / 1000.0f;
    float fps = num_frames / elapsed;
    
    printf("Rendered %d frames in %.2f seconds\n", num_frames, elapsed);
    printf("Average FPS: %.2f\n", fps);
    printf("Frame time: %.2f ms\n", (elapsed * 1000.0f) / num_frames);
}

// Stress test function
static void Test_StressTest(void) {
    printf("\n=== STRESS TEST ===\n");
    
    // Create many triangles
    const int num_triangles = 100;
    GraphicsCommand* stress_commands = malloc(sizeof(GraphicsCommand) * (num_triangles + 2));
    
    // Set primitive color
    stress_commands[0].opcode = G_SETPRIMCOLOR;
    stress_commands[0].params.setprimcolor = (typeof(stress_commands[0].params.setprimcolor)){255, 255, 255, 255, 0, 0};
    
    // Load vertices
    stress_commands[1].opcode = G_VTX;
    stress_commands[1].params.vtx = (typeof(stress_commands[1].params.vtx)){.n = 9, .vbidx = 0, .addr = (uintptr_t)test_vertices};
    
    // Add many triangles
    for (int i = 0; i < num_triangles; i++) {
        stress_commands[i + 2].opcode = G_TRI1;
        stress_commands[i + 2].params.tri1 = (typeof(stress_commands[i + 2].params.tri1)){
            .v0 = (uint8_t)(i % 3),
            .v1 = (uint8_t)((i + 1) % 3),
            .v2 = (uint8_t)((i + 2) % 3),
            .flag = 0
        };
    }
    
    // End display list
    stress_commands[num_triangles + 1].opcode = G_ENDDL;
    
    // Test performance
    uint32_t start_time = SDL_GetTicks();
    
    for (int frame = 0; frame < 60; frame++) {
        N64Graphics_BeginFrame();
        g_renderer->clear(g_renderer, true, true, false, 0.1f, 0.1f, 0.1f, 1.0f, 1.0f, 0);
        
        for (int i = 0; i < num_triangles + 2; i++) {
            N64Graphics_ProcessCommand(&stress_commands[i]);
        }
        
        N64Graphics_EndFrame();
        g_renderer->present(g_renderer);
    }
    
    uint32_t end_time = SDL_GetTicks();
    float elapsed = (end_time - start_time) / 1000.0f;
    
    printf("Stress test: %d triangles per frame for 60 frames\n", num_triangles);
    printf("Total triangles rendered: %d\n", num_triangles * 60);
    printf("Time taken: %.2f seconds\n", elapsed);
    printf("Triangles per second: %.0f\n", (num_triangles * 60) / elapsed);
    
    free(stress_commands);
}

// Main test function
int main(int argc, char* argv[]) {
    printf("=== OOT Native Graphics Test ===\n");
    
    // Initialize test commands
    init_test_commands();
    
    // Initialize SDL
    if (!Test_InitSDL()) {
        Test_Cleanup();
        return 1;
    }
    
    // Initialize graphics
    if (!Test_InitGraphics()) {
        Test_Cleanup();
        return 1;
    }
    
    // Run tests based on command line arguments
    if (argc > 1) {
        if (strcmp(argv[1], "performance") == 0) {
            Test_Performance();
        } else if (strcmp(argv[1], "stress") == 0) {
            Test_StressTest();
        } else {
            printf("Unknown test: %s\n", argv[1]);
            printf("Available tests: performance, stress\n");
        }
    } else {
        // Run interactive test
        Test_RunMainLoop();
    }
    
    // Cleanup
    Test_Cleanup();
    
    printf("Test completed successfully\n");
    return 0;
} 