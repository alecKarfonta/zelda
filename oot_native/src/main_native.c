/*
 * OOT Native Main Game Loop
 * 
 * This file replaces the N64 boot sequence (boot_main.c -> idle.c -> main.c -> graph.c)
 * with a modern native implementation that integrates OOT's GameState system with 
 * our SDL2/OpenGL/Audio/Input backends.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <SDL2/SDL.h>

// Our native backend systems
#include "graphics/graphics_api.h"
#include "audio/audio_api.h"
#include "input/input_api.h"
#include "input/input_backend.h"

// LibUltra compatibility layer
#include "libultra/libultra_compat.h"

// Forward declarations for OOT game system integration
// These will be implemented as we progress through the integration
typedef struct GameState GameState;
typedef struct GraphicsContext GraphicsContext;
typedef void (*GameStateFunc)(GameState* gameState);

// Mock GameState structure (simplified version for initial integration)
typedef struct GameState {
    GraphicsContext* gfxCtx;
    GameStateFunc main;
    GameStateFunc destroy;
    GameStateFunc init;
    u32 size;
    // Input input[4]; // TODO: Connect to our input system
    u32 running;
    u32 frames;
    u32 inPreNMIState;
} GameState;

// Mock GraphicsContext (will be integrated with our graphics backend)
typedef struct GraphicsContext {
    // Will be connected to our OpenGL backend
    void* native_renderer; // Pointer to our RendererBackend
    u32 width;
    u32 height;
    bool vsync_enabled;
} GraphicsContext;

// Game timing configuration
#define TARGET_FPS 60
#define FRAME_TIME_MS (1000 / TARGET_FPS)
#define FRAME_TIME_US (FRAME_TIME_MS * 1000)

// Global state
static bool g_game_running = false;
static SDL_Window* g_window = NULL;
static GraphicsContext g_graphics_context = {0};

// Game state management (simplified version of OOT's system)
static GameState* g_current_game_state = NULL;

// ================================================================================================
// Native System Initialization
// ================================================================================================

static bool initialize_native_systems(void) {
    printf("=== OOT Native: Initializing Systems ===\n");
    
    // Initialize SDL2
    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMECONTROLLER) < 0) {
        printf("ERROR: Failed to initialize SDL2: %s\n", SDL_GetError());
        return false;
    }
    
    // Create window
    g_window = SDL_CreateWindow(
        "The Legend of Zelda: Ocarina of Time (Native)",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 480,
        SDL_WINDOW_OPENGL | SDL_WINDOW_RESIZABLE
    );
    
    if (!g_window) {
        printf("ERROR: Failed to create window: %s\n", SDL_GetError());
        return false;
    }
    
    // Initialize graphics system
    GraphicsConfig graphics_config = {
        .width = 640,
        .height = 480,
        .aspect_ratio = 640.0f / 480.0f,
        .vsync = true,
        .fullscreen = false,
        .backend = GRAPHICS_BACKEND_OPENGL,
        .msaa_samples = 0,
        .hdr_enabled = false
    };
    
    if (!Graphics_Init(&graphics_config)) {
        printf("ERROR: Failed to initialize graphics system\n");
        return false;
    }
    
    // Initialize audio system
    AudioConfig audio_config = {
        .backend = AUDIO_BACKEND_SDL2,
        .format = AUDIO_FORMAT_S16,
        .sample_rate = 44100,
        .channels = 2,
        .buffer_size = 1024,
        .num_buffers = 4,
        .enable_effects = false,
        .enable_hq_resampling = false,
        .master_volume = 1.0f
    };
    
    if (!Audio_Init(&audio_config)) {
        printf("ERROR: Failed to initialize audio system\n");
        return false;
    }
    
    // Initialize input system
    InputConfig input_config = {
        .backend = INPUT_BACKEND_SDL2,
        .enable_rumble = true,
        .enable_haptic = true,
        .poll_rate_hz = 120,
        .deadzone_threshold = 10,
        .axis_sensitivity = 1.0f,
        .enable_debug_logging = false,
        .enable_multiple_controllers = true,
        .enable_keyboard_controller = true,
        .enable_auto_mapping = true,
        .enable_runtime_config = true
    };
    
    if (!Input_Init(&input_config)) {
        printf("ERROR: Failed to initialize input system\n");
        return false;
    }
    
    // Initialize LibUltra compatibility layer
    LibultraCompat_Initialize();
    
    printf("✅ All native systems initialized successfully\n");
    return true;
}

static void shutdown_native_systems(void) {
    printf("=== OOT Native: Shutting Down Systems ===\n");
    
    LibultraCompat_Shutdown();
    Input_Shutdown();
    Audio_Shutdown();
    Graphics_Shutdown();
    
    if (g_window) {
        SDL_DestroyWindow(g_window);
        g_window = NULL;
    }
    
    SDL_Quit();
    printf("✅ All native systems shut down\n");
}

// ================================================================================================
// Mock Game State Implementation (temporary for testing)
// ================================================================================================

static void mock_game_main(GameState* gameState) {
    // This is a placeholder - will be replaced with actual OOT Play_Main integration
    static int frame_count = 0;
    frame_count++;
    
    // Simple test: exit after 300 frames (5 seconds at 60 FPS)
    if (frame_count > 300) {
        printf("Mock game completed (%d frames)\n", frame_count);
        gameState->running = false;
    }
    
    // Test our graphics system with a simple frame
    Graphics_BeginFrame();
    // Note: Graphics_Clear not available in current API - will be added later
    Graphics_EndFrame();
}

static void mock_game_destroy(GameState* gameState) {
    printf("Mock game destroy called\n");
    // Cleanup will be added here
}

static void mock_game_init(GameState* gameState) {
    printf("Mock game initialized\n");
    gameState->main = mock_game_main;
    gameState->destroy = mock_game_destroy;
    gameState->running = true;
    gameState->frames = 0;
}

// ================================================================================================
// Native Game Loop (replaces Graph_ThreadEntry)
// ================================================================================================

static void native_game_loop(void) {
    printf("=== OOT Native: Starting Game Loop ===\n");
    
    // Initialize mock game state (will be replaced with actual OOT game states)
    GameState mock_state = {0};
    mock_state.gfxCtx = &g_graphics_context;
    g_current_game_state = &mock_state;
    
    // Initialize the game state (equivalent to GameState_Init)
    mock_game_init(g_current_game_state);
    
    u64 last_frame_time = osGetTimeNanoseconds();
    u64 frame_accumulator = 0;
    u32 fps_counter = 0;
    u64 fps_timer = last_frame_time;
    
    g_game_running = true;
    
    while (g_game_running && g_current_game_state && g_current_game_state->running) {
        u64 current_time = osGetTimeNanoseconds();
        u64 delta_time = current_time - last_frame_time;
        last_frame_time = current_time;
        
        frame_accumulator += delta_time;
        
        // Handle SDL events
        SDL_Event event;
        while (SDL_PollEvent(&event)) {
            switch (event.type) {
                case SDL_QUIT:
                    g_game_running = false;
                    break;
                    
                case SDL_KEYDOWN:
                    if (event.key.keysym.sym == SDLK_ESCAPE) {
                        g_game_running = false;
                    }
                    break;
                    
                default:
                    // Note: Input_ProcessEvent not available - events handled by Input_ProcessFrame
                    break;
            }
        }
        
        // Update input state
        Input_ProcessFrame();
        
        // Process game frame at target FPS
        if (frame_accumulator >= (1000000000ULL / TARGET_FPS)) {
            // Update game state (equivalent to GameState_Update)
            if (g_current_game_state->main) {
                g_current_game_state->main(g_current_game_state);
            }
            
            g_current_game_state->frames++;
            frame_accumulator -= (1000000000ULL / TARGET_FPS);
            fps_counter++;
        }
        
        // Update audio
        AudioMgr_ProcessAudioFrame();
        
        // FPS tracking
        if (current_time - fps_timer >= 1000000000ULL) { // 1 second
            printf("FPS: %u, Game Frames: %u\n", fps_counter, g_current_game_state->frames);
            fps_counter = 0;
            fps_timer = current_time;
        }
        
        // Small sleep to prevent 100% CPU usage
        osSleepUs(100);
    }
    
    // Cleanup game state (equivalent to GameState_Destroy)
    if (g_current_game_state && g_current_game_state->destroy) {
        g_current_game_state->destroy(g_current_game_state);
    }
    
    printf("=== OOT Native: Game Loop Ended ===\n");
}

// ================================================================================================
// Main Entry Point (replaces bootproc and Main_ThreadEntry)
// ================================================================================================

int main(int argc, char* argv[]) {
    printf("=== The Legend of Zelda: Ocarina of Time (Native) ===\n");
    printf("Replacing N64 emulation with native execution...\n\n");
    
    // Initialize all native systems
    if (!initialize_native_systems()) {
        printf("ERROR: Failed to initialize native systems\n");
        return 1;
    }
    
    // Run the main game loop
    native_game_loop();
    
    // Shutdown all systems
    shutdown_native_systems();
    
    printf("\n=== OOT Native: Clean Exit ===\n");
    return 0;
}

// ================================================================================================
// Integration Notes for Next Steps
// ================================================================================================

/*
 * NEXT INTEGRATION STEPS:
 * 
 * 1. Replace mock_game_* functions with actual OOT game state integration:
 *    - Connect to Play_Init, Play_Main, Play_Destroy from z_play.c
 *    - Integrate the full GameStateOverlay system from gamestate_table.h
 *    - Connect to the actual GameState structure from game.h
 * 
 * 2. Connect GraphicsContext to our OpenGL backend:
 *    - Replace mock GraphicsContext with real OOT GraphicsContext
 *    - Connect OOT's display list processing to our N64Graphics_ProcessCommands
 *    - Integrate scene rendering with our graphics pipeline
 * 
 * 3. Connect Input system:
 *    - Map our Input_GetState() to OOT's Input structure
 *    - Connect N64 controller buttons to modern controller mapping
 *    - Handle analog stick and trigger inputs
 * 
 * 4. Connect Audio system:
 *    - Integrate OOT's audio calls with our N64Audio_* functions
 *    - Connect sound effects and music playback
 *    - Handle audio streaming and mixing
 * 
 * 5. Memory management adaptation:
 *    - Connect OOT's arena allocators to our heap management
 *    - Handle scene loading and asset management
 *    - Integrate save system with modern file I/O
 * 
 * 6. Timing adaptation:
 *    - Handle frame rate independence (20 FPS -> 60+ FPS)
 *    - Adapt game logic timing and animation systems
 *    - Ensure consistent physics and game behavior
 */ 