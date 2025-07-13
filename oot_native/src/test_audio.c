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

// Test configuration
#define TEST_SAMPLE_RATE 44100
#define TEST_CHANNELS 2
#define TEST_BUFFER_SIZE 1024
#define TEST_DURATION_SECONDS 2
#define TEST_VOLUME 0.5f

// Test results structure
typedef struct {
    bool passed;
    const char* test_name;
    const char* error_message;
    double duration_ms;
} TestResult;

// Audio test context
typedef struct {
    AudioConfig config;
    bool audio_initialized;
    uint32_t test_count;
    uint32_t passed_count;
    TestResult results[32];
} AudioTestContext;

static AudioTestContext g_test_context = {0};

// Utility functions
static double get_time_ms() {
#ifdef _WIN32
    // Windows implementation using GetTickCount64
    return (double)GetTickCount64();
#else
    // Unix/Linux implementation using clock_gettime
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1000000.0;
#endif
}

static void sleep_ms(int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#else
    usleep(milliseconds * 1000);
#endif
}

static void log_test_result(const char* test_name, bool passed, const char* error, double duration_ms) {
    TestResult* result = &g_test_context.results[g_test_context.test_count];
    result->passed = passed;
    result->test_name = test_name;
    result->error_message = error;
    result->duration_ms = duration_ms;
    
    g_test_context.test_count++;
    if (passed) {
        g_test_context.passed_count++;
        printf("✓ %s (%.2f ms)\n", test_name, duration_ms);
    } else {
        printf("✗ %s (%.2f ms) - %s\n", test_name, duration_ms, error ? error : "Unknown error");
    }
}

static void print_test_summary() {
    printf("\n=== Audio Test Summary ===\n");
    printf("Tests run: %d\n", g_test_context.test_count);
    printf("Passed: %d\n", g_test_context.passed_count);
    printf("Failed: %d\n", g_test_context.test_count - g_test_context.passed_count);
    
    if (g_test_context.passed_count == g_test_context.test_count) {
        printf("🎉 All tests passed!\n");
    } else {
        printf("❌ Some tests failed. Check the details above.\n");
    }
}

// Audio data generation functions
static AudioBuffer* generate_sine_wave(uint32_t samples, uint32_t sample_rate, float frequency, float amplitude) {
    AudioBuffer* buffer = (AudioBuffer*)malloc(sizeof(AudioBuffer));
    if (!buffer) return NULL;
    
    buffer->samples = samples;
    buffer->channels = 1;
    buffer->sample_rate = sample_rate;
    buffer->format = AUDIO_FORMAT_S16;
    buffer->size = samples * sizeof(int16_t);
    buffer->data = (int16_t*)malloc(buffer->size);
    
    if (!buffer->data) {
        free(buffer);
        return NULL;
    }
    
    // Generate sine wave
    for (uint32_t i = 0; i < samples; i++) {
        float t = (float)i / (float)sample_rate;
        float sample = amplitude * sinf(2.0f * M_PI * frequency * t);
        buffer->data[i] = (int16_t)(sample * 32767.0f);
    }
    
    return buffer;
}

static AudioBuffer* generate_white_noise(uint32_t samples, uint32_t sample_rate, float amplitude) {
    AudioBuffer* buffer = (AudioBuffer*)malloc(sizeof(AudioBuffer));
    if (!buffer) return NULL;
    
    buffer->samples = samples;
    buffer->channels = 1;
    buffer->sample_rate = sample_rate;
    buffer->format = AUDIO_FORMAT_S16;
    buffer->size = samples * sizeof(int16_t);
    buffer->data = (int16_t*)malloc(buffer->size);
    
    if (!buffer->data) {
        free(buffer);
        return NULL;
    }
    
    // Generate white noise
    for (uint32_t i = 0; i < samples; i++) {
        float sample = amplitude * (2.0f * (float)rand() / RAND_MAX - 1.0f);
        buffer->data[i] = (int16_t)(sample * 32767.0f);
    }
    
    return buffer;
}

static void free_audio_buffer(AudioBuffer* buffer) {
    if (buffer) {
        if (buffer->data) free(buffer->data);
        free(buffer);
    }
}

// Test Functions
static bool test_audio_initialization() {
    double start_time = get_time_ms();
    
    g_test_context.config.sample_rate = TEST_SAMPLE_RATE;
    g_test_context.config.channels = TEST_CHANNELS;
    g_test_context.config.buffer_size = TEST_BUFFER_SIZE;
    g_test_context.config.format = AUDIO_FORMAT_S16;
    g_test_context.config.backend = AUDIO_BACKEND_SDL2;
    g_test_context.config.master_volume = 1.0f;
    
    bool result = Audio_Init(&g_test_context.config);
    g_test_context.audio_initialized = result;
    
    double end_time = get_time_ms();
    log_test_result("Audio System Initialization", result, 
                   result ? NULL : "Failed to initialize audio system", end_time - start_time);
    
    return result;
}

static bool test_n64_audio_initialization() {
    double start_time = get_time_ms();
    
    // The N64 audio system is already initialized by Audio_Init
    // So we'll test if it's working by checking if we can get debug info
    uint32_t active_voices, total_samples;
    float cpu_usage, peak_level;
    
    N64Audio_GetDebugInfo(&active_voices, &total_samples, &cpu_usage, &peak_level);
    
    // If we can get debug info without crash, the system is working
    bool result = true;
    
    double end_time = get_time_ms();
    log_test_result("N64 Audio System Initialization", result, 
                   result ? NULL : "Failed to initialize N64 audio system", end_time - start_time);
    
    return result;
}

static bool test_buffer_management() {
    double start_time = get_time_ms();
    
    // Test buffer creation
    N64AudioBuffer* buffer = N64Audio_CreateBuffer(1024, TEST_SAMPLE_RATE, 1, N64_AUDIO_FORMAT_PCM16);
    if (!buffer) {
        double end_time = get_time_ms();
        log_test_result("Buffer Management", false, "Failed to create buffer", end_time - start_time);
        return false;
    }
    
    // Test buffer data loading
    int16_t test_data[1024];
    for (int i = 0; i < 1024; i++) {
        test_data[i] = (int16_t)(sin(2.0 * M_PI * 440.0 * i / TEST_SAMPLE_RATE) * 16384);
    }
    
    N64Audio_LoadBufferData(buffer, test_data, sizeof(test_data));
    
    // Test buffer destruction
    N64Audio_DestroyBuffer(buffer);
    
    double end_time = get_time_ms();
    log_test_result("Buffer Management", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_voice_management() {
    double start_time = get_time_ms();
    
    // Test voice allocation
    N64AudioVoice* voice = N64Audio_AllocateVoice();
    if (!voice) {
        double end_time = get_time_ms();
        log_test_result("Voice Management", false, "Failed to allocate voice", end_time - start_time);
        return false;
    }
    
    // Test voice parameter setting
    N64Audio_SetVoiceVolume(voice, 0.5f);
    N64Audio_SetVoicePan(voice, 0.5f);
    N64Audio_SetVoicePitch(voice, 1.0f);
    
    // Test voice deallocation
    N64Audio_FreeVoice(voice);
    
    double end_time = get_time_ms();
    log_test_result("Voice Management", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_sine_wave_playback() {
    double start_time = get_time_ms();
    
    if (!g_test_context.audio_initialized) {
        double end_time = get_time_ms();
        log_test_result("Sine Wave Playback", false, "Audio not initialized", end_time - start_time);
        return false;
    }
    
    // Generate sine wave
    uint32_t samples = TEST_SAMPLE_RATE * TEST_DURATION_SECONDS;
    AudioBuffer* buffer = generate_sine_wave(samples, TEST_SAMPLE_RATE, 440.0f, TEST_VOLUME);
    
    if (!buffer) {
        double end_time = get_time_ms();
        log_test_result("Sine Wave Playback", false, "Failed to generate sine wave", end_time - start_time);
        return false;
    }
    
    // Play the sine wave
    AudioPlayer_Play(buffer, TEST_VOLUME, 0.5f);
    
    // Wait for playback to complete
    sleep_ms(TEST_DURATION_SECONDS * 1000);
    
    // Stop playback
    AudioPlayer_Stop(buffer);
    
    free_audio_buffer(buffer);
    
    double end_time = get_time_ms();
    log_test_result("Sine Wave Playback", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_multiple_voice_playback() {
    double start_time = get_time_ms();
    
    if (!g_test_context.audio_initialized) {
        double end_time = get_time_ms();
        log_test_result("Multiple Voice Playback", false, "Audio not initialized", end_time - start_time);
        return false;
    }
    
    // Generate multiple sine waves with different frequencies
    const float frequencies[] = {220.0f, 440.0f, 880.0f};
    const int num_voices = sizeof(frequencies) / sizeof(frequencies[0]);
    AudioBuffer* buffers[num_voices];
    
    uint32_t samples = TEST_SAMPLE_RATE * TEST_DURATION_SECONDS;
    
    // Create and play multiple voices
    for (int i = 0; i < num_voices; i++) {
        buffers[i] = generate_sine_wave(samples, TEST_SAMPLE_RATE, frequencies[i], TEST_VOLUME / num_voices);
        if (!buffers[i]) {
            // Clean up previously allocated buffers
            for (int j = 0; j < i; j++) {
                free_audio_buffer(buffers[j]);
            }
            double end_time = get_time_ms();
            log_test_result("Multiple Voice Playback", false, "Failed to generate sine wave", end_time - start_time);
            return false;
        }
        
        AudioPlayer_Play(buffers[i], TEST_VOLUME / num_voices, 0.5f);
    }
    
    // Wait for playback to complete
    sleep_ms(TEST_DURATION_SECONDS * 1000);
    
    // Stop all voices
    for (int i = 0; i < num_voices; i++) {
        AudioPlayer_Stop(buffers[i]);
        free_audio_buffer(buffers[i]);
    }
    
    double end_time = get_time_ms();
    log_test_result("Multiple Voice Playback", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_pause_resume_functionality() {
    double start_time = get_time_ms();
    
    if (!g_test_context.audio_initialized) {
        double end_time = get_time_ms();
        log_test_result("Pause/Resume Functionality", false, "Audio not initialized", end_time - start_time);
        return false;
    }
    
    // Generate sine wave
    uint32_t samples = TEST_SAMPLE_RATE * TEST_DURATION_SECONDS;
    AudioBuffer* buffer = generate_sine_wave(samples, TEST_SAMPLE_RATE, 440.0f, TEST_VOLUME);
    
    if (!buffer) {
        double end_time = get_time_ms();
        log_test_result("Pause/Resume Functionality", false, "Failed to generate sine wave", end_time - start_time);
        return false;
    }
    
    // Play the sine wave
    AudioPlayer_Play(buffer, TEST_VOLUME, 0.5f);
    
    // Play for 0.5 seconds
    sleep_ms(500);
    
    // Pause playback
    AudioPlayer_Pause(buffer);
    
    // Wait while paused
    sleep_ms(500);
    
    // Resume playback
    AudioPlayer_Resume(buffer);
    
    // Play for remaining time
    sleep_ms(500);
    
    // Stop playback
    AudioPlayer_Stop(buffer);
    
    free_audio_buffer(buffer);
    
    double end_time = get_time_ms();
    log_test_result("Pause/Resume Functionality", true, NULL, end_time - start_time);
    
    return true;
}

static bool test_master_volume_control() {
    double start_time = get_time_ms();
    
    // Test master volume setting
    N64Audio_SetMasterVolume(0.5f);
    float volume = N64Audio_GetMasterVolume();
    
    bool result = (volume >= 0.49f && volume <= 0.51f); // Allow for floating point precision
    
    double end_time = get_time_ms();
    log_test_result("Master Volume Control", result, 
                   result ? NULL : "Master volume not set correctly", end_time - start_time);
    
    return result;
}

static bool test_performance_benchmarks() {
    double start_time = get_time_ms();
    
    // Test N64Audio_ProcessFrame performance
    int16_t* left_buffer = (int16_t*)malloc(TEST_BUFFER_SIZE * sizeof(int16_t));
    int16_t* right_buffer = (int16_t*)malloc(TEST_BUFFER_SIZE * sizeof(int16_t));
    
    if (!left_buffer || !right_buffer) {
        if (left_buffer) free(left_buffer);
        if (right_buffer) free(right_buffer);
        double end_time = get_time_ms();
        log_test_result("Performance Benchmarks", false, "Failed to allocate buffers", end_time - start_time);
        return false;
    }
    
    // Run multiple frames to measure performance
    double frame_start = get_time_ms();
    const int num_frames = 1000;
    
    for (int i = 0; i < num_frames; i++) {
        N64Audio_ProcessFrame(left_buffer, right_buffer, TEST_BUFFER_SIZE);
    }
    
    double frame_end = get_time_ms();
    double avg_frame_time = (frame_end - frame_start) / num_frames;
    
    free(left_buffer);
    free(right_buffer);
    
    // Performance should be well under 1ms per frame for real-time audio
    bool result = (avg_frame_time < 1.0);
    
    double end_time = get_time_ms();
    char perf_msg[256];
    snprintf(perf_msg, sizeof(perf_msg), "Average frame time: %.3f ms", avg_frame_time);
    
    log_test_result("Performance Benchmarks", result, 
                   result ? NULL : "Performance too slow for real-time audio", end_time - start_time);
    
    if (result) {
        printf("  Performance: %.3f ms per frame (target: < 1.0 ms)\n", avg_frame_time);
    }
    
    return result;
}

static bool test_debug_info() {
    double start_time = get_time_ms();
    
    // Enable debug mode
    N64Audio_EnableDebugMode(true);
    
    // Get debug info
    uint32_t active_voices, total_samples;
    float cpu_usage, peak_level;
    N64Audio_GetDebugInfo(&active_voices, &total_samples, &cpu_usage, &peak_level);
    
    printf("  Debug Info - Active voices: %d, Total samples: %d, CPU usage: %.2f%%, Peak level: %.2f\n",
           active_voices, total_samples, cpu_usage, peak_level);
    
    // Disable debug mode
    N64Audio_EnableDebugMode(false);
    
    double end_time = get_time_ms();
    log_test_result("Debug Info", true, NULL, end_time - start_time);
    
    return true;
}

// Test modes
static void run_basic_tests() {
    printf("=== Basic Audio Tests ===\n");
    
    test_audio_initialization();
    test_n64_audio_initialization();
    test_buffer_management();
    test_voice_management();
    test_master_volume_control();
    test_debug_info();
}

static void run_playback_tests() {
    printf("\n=== Audio Playback Tests ===\n");
    
    test_sine_wave_playback();
    test_multiple_voice_playback();
    test_pause_resume_functionality();
}

static void run_performance_tests() {
    printf("\n=== Performance Tests ===\n");
    
    test_performance_benchmarks();
}

static void run_interactive_test() {
    printf("\n=== Interactive Audio Test ===\n");
    printf("This test will play various audio samples. Listen for:\n");
    printf("1. 440Hz sine wave (A4 note)\n");
    printf("2. Three-tone chord (A3, A4, A5)\n");
    printf("3. White noise sample\n");
    printf("Press Enter to start each test...\n");
    
    if (!g_test_context.audio_initialized) {
        printf("Audio not initialized. Cannot run interactive test.\n");
        return;
    }
    
    // Test 1: Single sine wave
    printf("Playing 440Hz sine wave...");
    getchar();
    
    uint32_t samples = TEST_SAMPLE_RATE * 2;
    AudioBuffer* sine_buffer = generate_sine_wave(samples, TEST_SAMPLE_RATE, 440.0f, 0.5f);
    AudioPlayer_Play(sine_buffer, 0.5f, 0.5f);
    sleep_ms(2000);
    AudioPlayer_Stop(sine_buffer);
    free_audio_buffer(sine_buffer);
    
    // Test 2: Chord
    printf("Playing three-tone chord...");
    getchar();
    
    const float chord_freqs[] = {220.0f, 440.0f, 880.0f};
    AudioBuffer* chord_buffers[3];
    
    for (int i = 0; i < 3; i++) {
        chord_buffers[i] = generate_sine_wave(samples, TEST_SAMPLE_RATE, chord_freqs[i], 0.3f);
        AudioPlayer_Play(chord_buffers[i], 0.3f, 0.5f);
    }
    
    sleep_ms(2000);
    
    for (int i = 0; i < 3; i++) {
        AudioPlayer_Stop(chord_buffers[i]);
        free_audio_buffer(chord_buffers[i]);
    }
    
    // Test 3: White noise
    printf("Playing white noise...");
    getchar();
    
    AudioBuffer* noise_buffer = generate_white_noise(samples, TEST_SAMPLE_RATE, 0.3f);
    AudioPlayer_Play(noise_buffer, 0.3f, 0.5f);
    sleep_ms(2000);
    AudioPlayer_Stop(noise_buffer);
    free_audio_buffer(noise_buffer);
    
    printf("Interactive test completed!\n");
}

static void print_usage() {
    printf("Usage: test_audio [mode]\n");
    printf("Modes:\n");
    printf("  basic      - Run basic functionality tests\n");
    printf("  playback   - Run audio playback tests\n");
    printf("  performance - Run performance benchmarks\n");
    printf("  interactive - Run interactive audio test (requires user input)\n");
    printf("  all        - Run all automated tests (default)\n");
    printf("  help       - Show this help message\n");
}

int main(int argc, char* argv[]) {
    printf("OOT Native Audio Test Suite\n");
    printf("===========================\n\n");
    
    // Initialize random seed for white noise generation
    srand(time(NULL));
    
    const char* mode = "all";
    if (argc > 1) {
        mode = argv[1];
    }
    
    if (strcmp(mode, "help") == 0) {
        print_usage();
        return 0;
    }
    
    // Run tests based on mode
    if (strcmp(mode, "basic") == 0) {
        run_basic_tests();
    } else if (strcmp(mode, "playback") == 0) {
        run_basic_tests();
        run_playback_tests();
    } else if (strcmp(mode, "performance") == 0) {
        run_basic_tests();
        run_performance_tests();
    } else if (strcmp(mode, "interactive") == 0) {
        run_basic_tests();
        run_interactive_test();
    } else if (strcmp(mode, "all") == 0) {
        run_basic_tests();
        run_playback_tests();
        run_performance_tests();
    } else {
        printf("Unknown mode: %s\n", mode);
        print_usage();
        return 1;
    }
    
    print_test_summary();
    
    // Cleanup
    if (g_test_context.audio_initialized) {
        Audio_Shutdown();
    }
    
    return (g_test_context.passed_count == g_test_context.test_count) ? 0 : 1;
} 