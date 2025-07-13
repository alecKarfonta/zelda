#include "audio/audio_api.h"
#include "audio/n64_audio.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

// SDL2 headers for audio backend
#ifdef _WIN32
    #include <SDL2/SDL.h>
#else
    #include <SDL.h>
#endif

// Global audio state
typedef struct {
    bool initialized;
    AudioConfig config;
    AudioBackend current_backend;
    
    // SDL2 audio device
    SDL_AudioDeviceID audio_device;
    SDL_AudioSpec audio_spec;
    
    // Audio buffers
    AudioBuffer* active_buffers[256];
    uint32_t num_active_buffers;
    
    // Audio buffer to voice mapping
    struct {
        AudioBuffer* buffer;
        N64AudioVoice* voice;
        N64AudioBuffer* n64_buffer;
    } buffer_voice_map[256];
    uint32_t num_buffer_mappings;
    
    // Audio streams
    AudioStream* active_streams[64];
    uint32_t num_active_streams;
    
    // Master volume
    float master_volume;
    
    // Statistics
    uint32_t total_samples;
    float cpu_usage;
    
    // Debug mode
    bool debug_enabled;
    
    // Error handling
    char error_string[256];
} AudioState;

static AudioState g_audio_state = {0};

// Audio callback function for SDL2
static void Audio_SDL2_Callback(void* userdata, Uint8* stream, int len);

// Utility functions
static void Audio_SetError(const char* error) {
    if (error) {
        strncpy(g_audio_state.error_string, error, sizeof(g_audio_state.error_string) - 1);
        g_audio_state.error_string[sizeof(g_audio_state.error_string) - 1] = '\0';
    } else {
        g_audio_state.error_string[0] = '\0';
    }
}

static SDL_AudioFormat Audio_FormatToSDL(AudioFormat format) {
    switch (format) {
        case AUDIO_FORMAT_S8: return AUDIO_S8;
        case AUDIO_FORMAT_U8: return AUDIO_U8;
        case AUDIO_FORMAT_S16: return AUDIO_S16SYS;
        case AUDIO_FORMAT_U16: return AUDIO_U16SYS;
        case AUDIO_FORMAT_S32: return AUDIO_S32SYS;
        case AUDIO_FORMAT_F32: return AUDIO_F32SYS;
        default: return AUDIO_S16SYS;
    }
}

static AudioFormat Audio_SDLToFormat(SDL_AudioFormat format) {
    switch (format) {
        case AUDIO_S8: return AUDIO_FORMAT_S8;
        case AUDIO_U8: return AUDIO_FORMAT_U8;
        case AUDIO_S16SYS: return AUDIO_FORMAT_S16;
        case AUDIO_U16SYS: return AUDIO_FORMAT_U16;
        case AUDIO_S32SYS: return AUDIO_FORMAT_S32;
        case AUDIO_F32SYS: return AUDIO_FORMAT_F32;
        default: return AUDIO_FORMAT_S16;
    }
}

// Audio initialization
bool Audio_Init(AudioConfig* config) {
    if (g_audio_state.initialized) {
        Audio_SetError("Audio already initialized");
        return false;
    }
    
    if (!config) {
        Audio_SetError("Invalid configuration");
        return false;
    }
    
    // Initialize SDL2 audio
    if (SDL_Init(SDL_INIT_AUDIO) < 0) {
        Audio_SetError("Failed to initialize SDL2 audio");
        return false;
    }
    
    // Copy configuration
    g_audio_state.config = *config;
    g_audio_state.current_backend = config->backend;
    g_audio_state.master_volume = config->master_volume;
    
    // Set up SDL2 audio specification
    SDL_AudioSpec desired_spec = {0};
    desired_spec.freq = config->sample_rate;
    desired_spec.format = Audio_FormatToSDL(config->format);
    desired_spec.channels = config->channels;
    desired_spec.samples = config->buffer_size;
    desired_spec.callback = Audio_SDL2_Callback;
    desired_spec.userdata = NULL;
    
    // Open audio device
    g_audio_state.audio_device = SDL_OpenAudioDevice(NULL, 0, &desired_spec, &g_audio_state.audio_spec, 0);
    if (g_audio_state.audio_device == 0) {
        Audio_SetError("Failed to open audio device");
        SDL_Quit();
        return false;
    }
    
    // Update config with actual obtained settings
    g_audio_state.config.sample_rate = g_audio_state.audio_spec.freq;
    g_audio_state.config.format = Audio_SDLToFormat(g_audio_state.audio_spec.format);
    g_audio_state.config.channels = g_audio_state.audio_spec.channels;
    g_audio_state.config.buffer_size = g_audio_state.audio_spec.samples;
    
    // Initialize N64 audio system
    if (!N64Audio_Init(g_audio_state.config.sample_rate, g_audio_state.config.buffer_size, 32)) {
        Audio_SetError("Failed to initialize N64 audio system");
        SDL_CloseAudioDevice(g_audio_state.audio_device);
        SDL_Quit();
        return false;
    }
    
    // Initialize buffer management
    g_audio_state.num_active_buffers = 0;
    g_audio_state.num_buffer_mappings = 0;
    g_audio_state.num_active_streams = 0;
    
    // Start audio playback
    SDL_PauseAudioDevice(g_audio_state.audio_device, 0);
    
    g_audio_state.initialized = true;
    Audio_SetError(NULL);
    
    if (g_audio_state.debug_enabled) {
        printf("Audio initialized: %d Hz, %d channels, %d samples buffer\n",
               g_audio_state.config.sample_rate,
               g_audio_state.config.channels,
               g_audio_state.config.buffer_size);
    }
    
    return true;
}

void Audio_Shutdown(void) {
    if (!g_audio_state.initialized) {
        return;
    }
    
    // Stop audio playback
    SDL_PauseAudioDevice(g_audio_state.audio_device, 1);
    
    // Free all active buffers
    for (uint32_t i = 0; i < g_audio_state.num_active_buffers; i++) {
        if (g_audio_state.active_buffers[i]) {
            AudioMgr_DestroyAudioBuffer(g_audio_state.active_buffers[i]);
        }
    }
    g_audio_state.num_active_buffers = 0;
    
    // Free all active streams
    for (uint32_t i = 0; i < g_audio_state.num_active_streams; i++) {
        if (g_audio_state.active_streams[i]) {
            free(g_audio_state.active_streams[i]);
        }
    }
    g_audio_state.num_active_streams = 0;
    
    // Shutdown N64 audio system
    N64Audio_Shutdown();
    
    // Close SDL2 audio
    SDL_CloseAudioDevice(g_audio_state.audio_device);
    SDL_Quit();
    
    g_audio_state.initialized = false;
    Audio_SetError(NULL);
}

// SDL2 audio callback
static void Audio_SDL2_Callback(void* userdata, Uint8* stream, int len) {
    if (!g_audio_state.initialized) {
        memset(stream, 0, len);
        return;
    }
    
    // Calculate number of samples
    uint32_t samples_per_channel = len / (g_audio_state.config.channels * Audio_GetFormatSize(g_audio_state.config.format));
    
    // Process N64 audio frame
    int16_t* output_left = (int16_t*)malloc(samples_per_channel * sizeof(int16_t));
    int16_t* output_right = (int16_t*)malloc(samples_per_channel * sizeof(int16_t));
    
    if (output_left && output_right) {
        // Clear buffers
        memset(output_left, 0, samples_per_channel * sizeof(int16_t));
        memset(output_right, 0, samples_per_channel * sizeof(int16_t));
        
        // Process N64 audio frame
        N64Audio_ProcessFrame(output_left, output_right, samples_per_channel);
        
        // Convert to output format and interleave
        if (g_audio_state.config.format == AUDIO_FORMAT_S16 && g_audio_state.config.channels == 2) {
            int16_t* output = (int16_t*)stream;
            for (uint32_t i = 0; i < samples_per_channel; i++) {
                output[i * 2] = (int16_t)(output_left[i] * g_audio_state.master_volume);
                output[i * 2 + 1] = (int16_t)(output_right[i] * g_audio_state.master_volume);
            }
        } else {
            // Handle other formats (simplified)
            memset(stream, 0, len);
        }
        
        // Update statistics
        g_audio_state.total_samples += samples_per_channel;
    } else {
        // Out of memory, output silence
        memset(stream, 0, len);
    }
    
    if (output_left) free(output_left);
    if (output_right) free(output_right);
}

// Main audio processing interface (Ship of Harkinian pattern)
void AudioPlayer_Play(AudioBuffer* buffer, float volume, float pan) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    // Allocate N64 voice
    N64AudioVoice* voice = N64Audio_AllocateVoice();
    if (!voice) {
        Audio_SetError("No available voices");
        return;
    }
    
    // Create N64 audio buffer
    N64AudioBuffer* n64_buffer = N64Audio_CreateBuffer(buffer->samples, buffer->sample_rate, buffer->channels, N64_AUDIO_FORMAT_PCM16);
    if (!n64_buffer) {
        N64Audio_FreeVoice(voice);
        Audio_SetError("Failed to create N64 audio buffer");
        return;
    }
    
    // Load buffer data
    N64Audio_LoadBufferData(n64_buffer, buffer->data, buffer->size);
    
    // Set voice parameters
    N64Audio_SetVoiceVolume(voice, volume);
    N64Audio_SetVoicePan(voice, pan);
    
    // Play voice
    N64Audio_PlayVoice(voice, n64_buffer);
    
    // Add to active buffers
    if (g_audio_state.num_active_buffers < 256) {
        g_audio_state.active_buffers[g_audio_state.num_active_buffers++] = buffer;
    }
    
    // Register buffer-voice mapping
    if (g_audio_state.num_buffer_mappings < 256) {
        g_audio_state.buffer_voice_map[g_audio_state.num_buffer_mappings].buffer = buffer;
        g_audio_state.buffer_voice_map[g_audio_state.num_buffer_mappings].voice = voice;
        g_audio_state.buffer_voice_map[g_audio_state.num_buffer_mappings].n64_buffer = n64_buffer;
        g_audio_state.num_buffer_mappings++;
    }
    
    if (g_audio_state.debug_enabled) {
        printf("Playing audio buffer: %d samples, %.2f volume, %.2f pan\n",
               buffer->samples, volume, pan);
    }
}

void AudioPlayer_Stop(AudioBuffer* buffer) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    // Find and stop the associated voice
    for (uint32_t i = 0; i < g_audio_state.num_buffer_mappings; i++) {
        if (g_audio_state.buffer_voice_map[i].buffer == buffer) {
            // Stop the voice
            N64Audio_StopVoice(g_audio_state.buffer_voice_map[i].voice);
            
            // Free the voice
            N64Audio_FreeVoice(g_audio_state.buffer_voice_map[i].voice);
            
            // Destroy the N64 buffer
            N64Audio_DestroyBuffer(g_audio_state.buffer_voice_map[i].n64_buffer);
            
            // Remove mapping by moving last mapping to this position
            g_audio_state.buffer_voice_map[i] = g_audio_state.buffer_voice_map[g_audio_state.num_buffer_mappings - 1];
            g_audio_state.num_buffer_mappings--;
            break;
        }
    }
    
    // Find and remove from active buffers
    for (uint32_t i = 0; i < g_audio_state.num_active_buffers; i++) {
        if (g_audio_state.active_buffers[i] == buffer) {
            // Move last buffer to this position
            g_audio_state.active_buffers[i] = g_audio_state.active_buffers[g_audio_state.num_active_buffers - 1];
            g_audio_state.num_active_buffers--;
            break;
        }
    }
    
    if (g_audio_state.debug_enabled) {
        printf("Stopped audio buffer\n");
    }
}

void AudioPlayer_Pause(AudioBuffer* buffer) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    // Find and pause the associated voice
    for (uint32_t i = 0; i < g_audio_state.num_buffer_mappings; i++) {
        if (g_audio_state.buffer_voice_map[i].buffer == buffer) {
            g_audio_state.buffer_voice_map[i].voice->is_paused = true;
            if (g_audio_state.debug_enabled) {
                printf("Paused audio buffer\n");
            }
            return;
        }
    }
    
    if (g_audio_state.debug_enabled) {
        printf("Audio buffer not found for pause\n");
    }
}

void AudioPlayer_Resume(AudioBuffer* buffer) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    // Find and resume the associated voice
    for (uint32_t i = 0; i < g_audio_state.num_buffer_mappings; i++) {
        if (g_audio_state.buffer_voice_map[i].buffer == buffer) {
            g_audio_state.buffer_voice_map[i].voice->is_paused = false;
            if (g_audio_state.debug_enabled) {
                printf("Resumed audio buffer\n");
            }
            return;
        }
    }
    
    if (g_audio_state.debug_enabled) {
        printf("Audio buffer not found for resume\n");
    }
}

void AudioPlayer_SetVolume(AudioBuffer* buffer, float volume) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    buffer->volume = volume;
    
    if (g_audio_state.debug_enabled) {
        printf("Set audio buffer volume: %.2f\n", volume);
    }
}

void AudioPlayer_SetPan(AudioBuffer* buffer, float pan) {
    if (!g_audio_state.initialized || !buffer) {
        return;
    }
    
    buffer->pan = pan;
    
    if (g_audio_state.debug_enabled) {
        printf("Set audio buffer pan: %.2f\n", pan);
    }
}

// Audio manager interface (Ship of Harkinian pattern)
AudioBuffer* AudioMgr_CreateNextAudioBuffer(uint32_t samples, uint32_t channels, uint32_t sample_rate) {
    if (!g_audio_state.initialized) {
        return NULL;
    }
    
    AudioBuffer* buffer = (AudioBuffer*)malloc(sizeof(AudioBuffer));
    if (!buffer) {
        Audio_SetError("Failed to allocate audio buffer");
        return NULL;
    }
    
    memset(buffer, 0, sizeof(AudioBuffer));
    
    // Calculate buffer size
    uint32_t format_size = Audio_GetFormatSize(g_audio_state.config.format);
    uint32_t buffer_size = samples * channels * format_size;
    
    // Allocate buffer data
    buffer->data = (int16_t*)malloc(buffer_size);
    if (!buffer->data) {
        free(buffer);
        Audio_SetError("Failed to allocate audio buffer data");
        return NULL;
    }
    
    // Set buffer properties
    buffer->size = buffer_size;
    buffer->samples = samples;
    buffer->channels = channels;
    buffer->sample_rate = sample_rate;
    buffer->format = g_audio_state.config.format;
    buffer->is_looping = false;
    buffer->volume = 1.0f;
    buffer->pan = 0.5f;
    
    // Clear buffer data
    memset(buffer->data, 0, buffer_size);
    
    if (g_audio_state.debug_enabled) {
        printf("Created audio buffer: %d samples, %d channels, %d Hz\n",
               samples, channels, sample_rate);
    }
    
    return buffer;
}

void AudioMgr_DestroyAudioBuffer(AudioBuffer* buffer) {
    if (!buffer) {
        return;
    }
    
    if (buffer->data) {
        free(buffer->data);
    }
    
    free(buffer);
    
    if (g_audio_state.debug_enabled) {
        printf("Destroyed audio buffer\n");
    }
}

void AudioMgr_ProcessAudioFrame(void) {
    if (!g_audio_state.initialized) {
        return;
    }
    
    // This is called by the SDL2 callback automatically
    // No additional processing needed here
}

void AudioMgr_SetMasterVolume(float volume) {
    g_audio_state.master_volume = volume;
    N64Audio_SetMasterVolume(volume);
    
    if (g_audio_state.debug_enabled) {
        printf("Set master volume: %.2f\n", volume);
    }
}

float AudioMgr_GetMasterVolume(void) {
    return g_audio_state.master_volume;
}

// Audio format utilities
uint32_t Audio_GetFormatSize(AudioFormat format) {
    switch (format) {
        case AUDIO_FORMAT_S8:
        case AUDIO_FORMAT_U8:
            return 1;
        case AUDIO_FORMAT_S16:
        case AUDIO_FORMAT_U16:
            return 2;
        case AUDIO_FORMAT_S32:
        case AUDIO_FORMAT_F32:
            return 4;
        default:
            return 2;
    }
}

const char* Audio_GetFormatName(AudioFormat format) {
    switch (format) {
        case AUDIO_FORMAT_S8: return "S8";
        case AUDIO_FORMAT_U8: return "U8";
        case AUDIO_FORMAT_S16: return "S16";
        case AUDIO_FORMAT_U16: return "U16";
        case AUDIO_FORMAT_S32: return "S32";
        case AUDIO_FORMAT_F32: return "F32";
        default: return "Unknown";
    }
}

bool Audio_IsFormatSupported(AudioFormat format) {
    return format >= AUDIO_FORMAT_S8 && format < AUDIO_FORMAT_COUNT;
}

// Audio backend management
bool Audio_SetBackend(AudioBackend backend) {
    if (!g_audio_state.initialized) {
        Audio_SetError("Audio not initialized");
        return false;
    }
    
    if (g_audio_state.current_backend == backend) {
        return true;
    }
    
    // For now, only SDL2 is supported
    if (backend != AUDIO_BACKEND_SDL2) {
        Audio_SetError("Backend not supported");
        return false;
    }
    
    g_audio_state.current_backend = backend;
    return true;
}

AudioBackend Audio_GetCurrentBackend(void) {
    return g_audio_state.current_backend;
}

const char* Audio_GetBackendName(AudioBackend backend) {
    switch (backend) {
        case AUDIO_BACKEND_SDL2: return "SDL2";
        case AUDIO_BACKEND_OPENAL: return "OpenAL";
        case AUDIO_BACKEND_WASAPI: return "WASAPI";
        case AUDIO_BACKEND_PULSE: return "PulseAudio";
        case AUDIO_BACKEND_ALSA: return "ALSA";
        default: return "Unknown";
    }
}

// Device management functions
AudioDevice* Audio_GetDefaultDevice(void) {
    // For SDL2, we don't have separate device objects
    // Return a dummy pointer to indicate default device
    return (AudioDevice*)1;  // Non-null pointer
}

AudioDevice* Audio_GetDevice(const char* name) {
    // For SDL2 backend, we don't have device selection
    // Return the default device
    return Audio_GetDefaultDevice();
}

const char* Audio_GetDeviceName(AudioDevice* device) {
    // For SDL2, return the default device name
    return "Default Audio Device";
}

uint32_t Audio_GetDeviceCount(void) {
    // For SDL2, we'll just return 1 for the default device
    return 1;
}

const char* Audio_GetDeviceNameByIndex(uint32_t index) {
    if (index == 0) {
        return "Default Audio Device";
    }
    return NULL;
}

// Audio effects functions
void Audio_EnableReverb(bool enabled) {
    N64Audio_EnableReverb(enabled);
}

void Audio_SetReverbPreset(const char* preset) {
    // Set reverb parameters based on preset
    if (!preset) return;
    
    if (strcmp(preset, "hall") == 0) {
        N64Audio_SetReverbParameters(0.5f, 0.2f);
    } else if (strcmp(preset, "room") == 0) {
        N64Audio_SetReverbParameters(0.3f, 0.1f);
    } else if (strcmp(preset, "cathedral") == 0) {
        N64Audio_SetReverbParameters(0.7f, 0.5f);
    } else if (strcmp(preset, "off") == 0) {
        N64Audio_EnableReverb(false);
        return;
    }
    
    N64Audio_EnableReverb(true);
}

void Audio_EnableEqualizer(bool enabled) {
    // EQ functionality not implemented in N64 audio system
    // This is a placeholder for future implementation
    if (g_audio_state.debug_enabled) {
        printf("Equalizer %s (not implemented)\n", enabled ? "enabled" : "disabled");
    }
}

void Audio_SetEqualizerBand(uint32_t band, float gain) {
    // EQ functionality not implemented in N64 audio system
    // This is a placeholder for future implementation
    if (g_audio_state.debug_enabled) {
        printf("Set EQ band %d to %.2f dB (not implemented)\n", band, gain);
    }
}

// Audio debugging and profiling
void Audio_EnableDebugMode(bool enabled) {
    g_audio_state.debug_enabled = enabled;
    N64Audio_EnableDebugMode(enabled);
    
    if (enabled) {
        printf("Audio debug mode enabled\n");
    }
}

void Audio_GetStats(uint32_t* active_buffers, uint32_t* total_samples, float* cpu_usage) {
    if (active_buffers) {
        *active_buffers = g_audio_state.num_active_buffers;
    }
    if (total_samples) {
        *total_samples = g_audio_state.total_samples;
    }
    if (cpu_usage) {
        *cpu_usage = g_audio_state.cpu_usage;
    }
}

// Error handling
const char* Audio_GetErrorString(void) {
    return g_audio_state.error_string;
}

void Audio_ClearError(void) {
    Audio_SetError(NULL);
} 