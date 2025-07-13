#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct AudioSystem AudioSystem;
typedef struct AudioDevice AudioDevice;

// Audio formats
typedef enum {
    AUDIO_FORMAT_S8,
    AUDIO_FORMAT_U8,
    AUDIO_FORMAT_S16,
    AUDIO_FORMAT_U16,
    AUDIO_FORMAT_S32,
    AUDIO_FORMAT_F32,
    AUDIO_FORMAT_COUNT
} AudioFormat;

// Audio backend types
typedef enum {
    AUDIO_BACKEND_SDL2,
    AUDIO_BACKEND_OPENAL,
    AUDIO_BACKEND_WASAPI,
    AUDIO_BACKEND_PULSE,
    AUDIO_BACKEND_ALSA,
    AUDIO_BACKEND_COUNT
} AudioBackend;

// Audio configuration
typedef struct {
    AudioBackend backend;
    AudioFormat format;
    uint32_t sample_rate;
    uint32_t channels;
    uint32_t buffer_size;
    uint32_t num_buffers;
    bool enable_effects;
    bool enable_hq_resampling;
    float master_volume;
} AudioConfig;

// Audio buffer structure
typedef struct {
    int16_t* data;
    uint32_t size;
    uint32_t samples;
    uint32_t channels;
    uint32_t sample_rate;
    AudioFormat format;
    bool is_looping;
    float volume;
    float pan;
} AudioBuffer;

// Audio stream structure
typedef struct {
    AudioBuffer* buffers;
    uint32_t buffer_count;
    uint32_t current_buffer;
    bool is_playing;
    bool is_paused;
    float volume;
    float pan;
    uint32_t position;
} AudioStream;

// Audio initialization
bool Audio_Init(AudioConfig* config);
void Audio_Shutdown(void);

// Main audio processing interface (Ship of Harkinian pattern)
void AudioPlayer_Play(AudioBuffer* buffer, float volume, float pan);
void AudioPlayer_Stop(AudioBuffer* buffer);
void AudioPlayer_Pause(AudioBuffer* buffer);
void AudioPlayer_Resume(AudioBuffer* buffer);
void AudioPlayer_SetVolume(AudioBuffer* buffer, float volume);
void AudioPlayer_SetPan(AudioBuffer* buffer, float pan);

// Audio manager interface (Ship of Harkinian pattern)
AudioBuffer* AudioMgr_CreateNextAudioBuffer(uint32_t samples, uint32_t channels, uint32_t sample_rate);
void AudioMgr_DestroyAudioBuffer(AudioBuffer* buffer);
void AudioMgr_ProcessAudioFrame(void);
void AudioMgr_SetMasterVolume(float volume);
float AudioMgr_GetMasterVolume(void);

// Audio device management
AudioDevice* Audio_GetDefaultDevice(void);
AudioDevice* Audio_GetDevice(const char* name);
const char* Audio_GetDeviceName(AudioDevice* device);
uint32_t Audio_GetDeviceCount(void);
const char* Audio_GetDeviceNameByIndex(uint32_t index);

// Audio format utilities
uint32_t Audio_GetFormatSize(AudioFormat format);
const char* Audio_GetFormatName(AudioFormat format);
bool Audio_IsFormatSupported(AudioFormat format);

// Audio backend management
bool Audio_SetBackend(AudioBackend backend);
AudioBackend Audio_GetCurrentBackend(void);
const char* Audio_GetBackendName(AudioBackend backend);

// Audio effects
void Audio_EnableReverb(bool enabled);
void Audio_SetReverbPreset(const char* preset);
void Audio_EnableEqualizer(bool enabled);
void Audio_SetEqualizerBand(uint32_t band, float gain);

// Audio debugging and profiling
void Audio_EnableDebugMode(bool enabled);
void Audio_GetStats(uint32_t* active_buffers, uint32_t* total_samples, float* cpu_usage);

// Error handling
const char* Audio_GetErrorString(void);
void Audio_ClearError(void);

#ifdef __cplusplus
}
#endif 