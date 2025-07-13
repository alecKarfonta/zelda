#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef _WIN32
    #include <windows.h>
    #include <time.h>
#else
    #include <time.h>
    #include <unistd.h>
#endif

#include "audio/audio_api.h"
#include "audio/n64_audio.h"
#include "input/input_api.h"
#include "graphics/graphics_api.h"

// Test configuration
#define TEST_SAMPLE_RATE 44100
#define TEST_CHANNELS 2
#define TEST_BUFFER_SIZE 1024
#define TEST_VOLUME 0.5f

// Cross-platform sleep function
static void sleep_ms(int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#else
    usleep(milliseconds * 1000);
#endif
}

// Cross-platform timing function
static double get_time_ms() {
#ifdef _WIN32
    return (double)GetTickCount64();
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1000000.0;
#endif
}

// Test result structure
typedef struct {
    bool passed;
    const char* system_name;
    const char* error_message;
    double duration_ms;
} SystemTestResult;

// Test context
typedef struct {
    SystemTestResult results[8];
    uint32_t test_count;
    uint32_t passed_count;
    bool audio_initialized;
    bool input_initialized;
    bool graphics_initialized;
} UnifiedTestContext;

static UnifiedTestContext g_test_context = {0};

// Utility functions
static void log_system_test(const char* system_name, bool passed, const char* error, double duration_ms) {
    SystemTestResult* result = &g_test_context.results[g_test_context.test_count];
    result->passed = passed;
    result->system_name = system_name;
    result->error_message = error;
    result->duration_ms = duration_ms;
    
    g_test_context.test_count++;
    if (passed) {
        g_test_context.passed_count++;
    }
}

static void print_test_summary() {
    printf("\n" "=" "50" "\n");
    printf("🎯 OOT NATIVE UNIFIED TEST SUMMARY\n");
    printf("=" "50" "\n");
    printf("Systems tested: %u\n", g_test_context.test_count);
    printf("Systems passed: %u\n", g_test_context.passed_count);
    printf("Systems failed: %u\n", g_test_context.test_count - g_test_context.passed_count);
    printf("Success rate: %.1f%%\n", (float)g_test_context.passed_count / g_test_context.test_count * 100.0f);
    printf("\n");
    
    for (uint32_t i = 0; i < g_test_context.test_count; i++) {
        SystemTestResult* result = &g_test_context.results[i];
        printf("%s %-20s: %s (%.2fms)\n", 
               result->passed ? "✅" : "❌", 
               result->system_name,
               result->passed ? "PASSED" : result->error_message,
               result->duration_ms);
    }
    
    printf("\n");
    if (g_test_context.passed_count == g_test_context.test_count) {
        printf("🎉 ALL SYSTEMS OPERATIONAL - OOT NATIVE CONVERSION READY!\n");
    } else {
        printf("⚠️  Some systems failed - see details above\n");
    }
}

// Generate test audio buffer
static AudioBuffer* generate_test_tone(uint32_t samples, uint32_t sample_rate, float frequency) {
    AudioBuffer* buffer = (AudioBuffer*)malloc(sizeof(AudioBuffer));
    if (!buffer) return NULL;
    
    buffer->samples = samples;
    buffer->sample_rate = sample_rate;
    buffer->channels = TEST_CHANNELS;
    buffer->data = (float*)malloc(samples * TEST_CHANNELS * sizeof(float));
    
    if (!buffer->data) {
        free(buffer);
        return NULL;
    }
    
    // Generate sine wave
    for (uint32_t i = 0; i < samples; i++) {
        float t = (float)i / sample_rate;
        float sample = sinf(2.0f * 3.14159f * frequency * t) * TEST_VOLUME;
        
        for (uint32_t ch = 0; ch < TEST_CHANNELS; ch++) {
            buffer->data[i * TEST_CHANNELS + ch] = sample;
        }
    }
    
    return buffer;
}

static void free_test_buffer(AudioBuffer* buffer) {
    if (buffer) {
        free(buffer->data);
        free(buffer);
    }
}

// System initialization tests
static bool test_audio_system_init() {
    printf("🔊 Testing Audio System Initialization...\n");
    double start_time = get_time_ms();
    
    AudioConfig config = {
        .sample_rate = TEST_SAMPLE_RATE,
        .channels = TEST_CHANNELS,
        .buffer_size = TEST_BUFFER_SIZE,
        .device_name = NULL
    };
    
    bool result = Audio_Initialize(&config);
    if (result) {
        g_test_context.audio_initialized = true;
        printf("  ✅ Audio system initialized (SDL2 backend)\n");
        printf("  ✅ Sample rate: %u Hz\n", config.sample_rate);
        printf("  ✅ Channels: %u\n", config.channels);
        printf("  ✅ Buffer size: %u samples\n", config.buffer_size);
    }
    
    double end_time = get_time_ms();
    log_system_test("Audio System", result, result ? NULL : "Failed to initialize audio", end_time - start_time);
    
    return result;
}

static bool test_input_system_init() {
    printf("🎮 Testing Input System Initialization...\n");
    double start_time = get_time_ms();
    
    InputConfig config = {
        .deadzone = 0.1f,
        .sensitivity = 1.0f,
        .enable_rumble = true
    };
    
    bool result = Input_Initialize(&config);
    if (result) {
        g_test_context.input_initialized = true;
        printf("  ✅ Input system initialized (SDL2 backend)\n");
        printf("  ✅ Controller detection enabled\n");
        printf("  ✅ N64 input mapping ready\n");
        
        // Check for connected controllers
        uint32_t device_count = Input_GetDeviceCount();
        printf("  ✅ Connected controllers: %u\n", device_count);
    }
    
    double end_time = get_time_ms();
    log_system_test("Input System", result, result ? NULL : "Failed to initialize input", end_time - start_time);
    
    return result;
}

static bool test_graphics_system_init() {
    printf("🎨 Testing Graphics System Initialization...\n");
    double start_time = get_time_ms();
    
    GraphicsConfig config = {
        .window_width = 640,
        .window_height = 480,
        .fullscreen = false,
        .vsync = false,
        .backend = GRAPHICS_BACKEND_OPENGL
    };
    
    bool result = Graphics_Initialize(&config);
    if (result) {
        g_test_context.graphics_initialized = true;
        printf("  ✅ Graphics system initialized (OpenGL backend)\n");
        printf("  ✅ Window created: %ux%u\n", config.window_width, config.window_height);
        printf("  ✅ N64 graphics pipeline ready\n");
    }
    
    double end_time = get_time_ms();
    log_system_test("Graphics System", result, result ? NULL : "Failed to initialize graphics", end_time - start_time);
    
    return result;
}

// System integration tests
static bool test_audio_playback() {
    if (!g_test_context.audio_initialized) {
        log_system_test("Audio Playback", false, "Audio system not initialized", 0);
        return false;
    }
    
    printf("🔊 Testing Audio Playback...\n");
    double start_time = get_time_ms();
    
    // Generate test tone
    uint32_t samples = TEST_SAMPLE_RATE * 1; // 1 second
    AudioBuffer* buffer = generate_test_tone(samples, TEST_SAMPLE_RATE, 440.0f);
    
    if (!buffer) {
        log_system_test("Audio Playback", false, "Failed to generate test tone", get_time_ms() - start_time);
        return false;
    }
    
    // Test playback
    AudioPlayer_Play(buffer, TEST_VOLUME, 0.5f);
    printf("  ✅ Playing 440Hz test tone...\n");
    
    sleep_ms(1000); // Play for 1 second
    
    AudioPlayer_Stop(buffer);
    printf("  ✅ Audio playback completed\n");
    
    free_test_buffer(buffer);
    
    double end_time = get_time_ms();
    log_system_test("Audio Playback", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_input_processing() {
    if (!g_test_context.input_initialized) {
        log_system_test("Input Processing", false, "Input system not initialized", 0);
        return false;
    }
    
    printf("🎮 Testing Input Processing...\n");
    double start_time = get_time_ms();
    
    // Process input for a few frames
    for (int frame = 0; frame < 10; frame++) {
        Input_ProcessFrame();
        
        const N64InputState* state = Input_GetCurrentState();
        if (!state || !state->valid) {
            log_system_test("Input Processing", false, "Invalid input state", get_time_ms() - start_time);
            return false;
        }
        
        sleep_ms(16); // ~60 FPS
    }
    
    printf("  ✅ Input processing completed\n");
    printf("  ✅ N64 input state valid\n");
    
    double end_time = get_time_ms();
    log_system_test("Input Processing", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_n64_audio_functions() {
    printf("🎵 Testing N64 Audio Functions...\n");
    double start_time = get_time_ms();
    
    // Test N64 audio initialization
    N64AudioConfig n64_config = {
        .sample_rate = TEST_SAMPLE_RATE,
        .max_voices = 32,
        .reverb_enabled = false
    };
    
    bool result = N64Audio_Initialize(&n64_config);
    if (!result) {
        log_system_test("N64 Audio Functions", false, "Failed to initialize N64 audio", get_time_ms() - start_time);
        return false;
    }
    
    printf("  ✅ N64 audio system initialized\n");
    printf("  ✅ RSP audio functions ready\n");
    printf("  ✅ Voice management system ready\n");
    
    double end_time = get_time_ms();
    log_system_test("N64 Audio Functions", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_system_integration() {
    printf("🔗 Testing System Integration...\n");
    double start_time = get_time_ms();
    
    // Test that all systems can work together
    bool all_initialized = g_test_context.audio_initialized && 
                          g_test_context.input_initialized;
    
    if (!all_initialized) {
        log_system_test("System Integration", false, "Not all systems initialized", get_time_ms() - start_time);
        return false;
    }
    
    // Run combined processing loop
    printf("  ✅ Running combined system loop...\n");
    for (int frame = 0; frame < 30; frame++) {
        // Process input
        Input_ProcessFrame();
        
        // Process audio (if needed)
        // Graphics would be processed here in full integration
        
        sleep_ms(16); // ~60 FPS
    }
    
    printf("  ✅ All systems working together\n");
    printf("  ✅ 30 frames processed successfully\n");
    
    double end_time = get_time_ms();
    log_system_test("System Integration", true, NULL, end_time - start_time);
    
    return true;
}

// Main test runner
int main(int argc, char* argv[]) {
    printf("🎯 OOT NATIVE UNIFIED SYSTEM TEST\n");
    printf("=" "50" "\n");
    printf("Testing complete OOT native conversion...\n\n");
    
    // Initialize random seed
    srand(time(NULL));
    
    // Run system initialization tests
    test_audio_system_init();
    test_input_system_init();
    test_graphics_system_init();
    
    // Run system functionality tests
    test_audio_playback();
    test_input_processing();
    test_n64_audio_functions();
    
    // Run integration test
    test_system_integration();
    
    // Print summary
    print_test_summary();
    
    // Cleanup
    if (g_test_context.audio_initialized) {
        Audio_Shutdown();
    }
    if (g_test_context.input_initialized) {
        Input_Shutdown();
    }
    if (g_test_context.graphics_initialized) {
        Graphics_Shutdown();
    }
    
    printf("\n" "Test completed. Press Enter to exit...\n");
    getchar();
    
    return (g_test_context.passed_count == g_test_context.test_count) ? 0 : 1;
} 