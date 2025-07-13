#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// N64 Audio Sample Formats
typedef enum {
    N64_AUDIO_FORMAT_ADPCM,
    N64_AUDIO_FORMAT_PCM16,
    N64_AUDIO_FORMAT_PCM8,
    N64_AUDIO_FORMAT_COUNT
} N64AudioFormat;

// N64 Audio Buffer Structure
typedef struct {
    int16_t* data;
    uint32_t size;
    uint32_t samples;
    uint32_t sample_rate;
    uint32_t channels;
    N64AudioFormat format;
    bool is_looping;
    uint32_t loop_start;
    uint32_t loop_end;
} N64AudioBuffer;

// N64 ADPCM State
typedef struct {
    int16_t prev_sample;
    int16_t index;
    int16_t header;
    uint8_t* data;
    uint32_t position;
    uint32_t length;
} N64ADPCMState;

// N64 Audio Mixer State
typedef struct {
    int16_t* left_buffer;
    int16_t* right_buffer;
    uint32_t buffer_size;
    uint32_t sample_rate;
    uint32_t num_voices;
    float master_volume;
    bool reverb_enabled;
    float reverb_gain;
    float reverb_delay;
} N64AudioMixer;

// N64 Audio Voice
typedef struct {
    N64AudioBuffer* buffer;
    uint32_t position;
    uint32_t increment;
    float volume;
    float pan;
    bool is_active;
    bool is_paused;
    N64ADPCMState adpcm_state;
} N64AudioVoice;

// N64 Audio Envelope
typedef struct {
    uint32_t attack_time;
    uint32_t decay_time;
    uint32_t sustain_level;
    uint32_t release_time;
    uint32_t current_level;
    uint32_t target_level;
    uint32_t state;
    uint32_t counter;
} N64AudioEnvelope;

// N64 RSP Audio Functions (Ship of Harkinian replacements)

// Environment Mixer - handles reverb and environmental audio effects
void aEnvMixerImpl(int16_t* input_left, int16_t* input_right, 
                   int16_t* output_left, int16_t* output_right,
                   uint32_t num_samples, float reverb_gain, float reverb_delay);

// Resampler - converts between different sample rates
void aResampleImpl(int16_t* input, int16_t* output,
                   uint32_t input_samples, uint32_t output_samples,
                   uint32_t input_rate, uint32_t output_rate);

// ADPCM Decoder - decompresses ADPCM audio data
void aADPCMdecImpl(N64ADPCMState* state, int16_t* output, uint32_t num_samples);

// Audio Mixer - mixes multiple audio sources
void aMixImpl(N64AudioVoice* voices, uint32_t num_voices,
              int16_t* output_left, int16_t* output_right,
              uint32_t num_samples);

// Buffer Load/Save - memory management for audio buffers
void aLoadBufferImpl(N64AudioBuffer* buffer, void* data, uint32_t size);
void aSaveBufferImpl(N64AudioBuffer* buffer, void* data, uint32_t size);

// Audio interpolation functions
void aInterpImpl(int16_t* input, int16_t* output, uint32_t num_samples, float ratio);
void aFilterImpl(int16_t* input, int16_t* output, uint32_t num_samples, float cutoff);

// Audio effects
void aChorusImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                 float delay, float depth, float rate);
void aFlangerImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                  float delay, float depth, float rate);
void aDistortionImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                     float drive, float level);

// N64 Audio System Functions

// Initialize N64 audio system
bool N64Audio_Init(uint32_t sample_rate, uint32_t buffer_size, uint32_t num_voices);
void N64Audio_Shutdown(void);

// Voice management
N64AudioVoice* N64Audio_AllocateVoice(void);
void N64Audio_FreeVoice(N64AudioVoice* voice);
void N64Audio_PlayVoice(N64AudioVoice* voice, N64AudioBuffer* buffer);
void N64Audio_StopVoice(N64AudioVoice* voice);
void N64Audio_SetVoiceVolume(N64AudioVoice* voice, float volume);
void N64Audio_SetVoicePan(N64AudioVoice* voice, float pan);
void N64Audio_SetVoicePitch(N64AudioVoice* voice, float pitch);

// Buffer management
N64AudioBuffer* N64Audio_CreateBuffer(uint32_t samples, uint32_t sample_rate,
                                      uint32_t channels, N64AudioFormat format);
void N64Audio_DestroyBuffer(N64AudioBuffer* buffer);
void N64Audio_LoadBufferData(N64AudioBuffer* buffer, void* data, uint32_t size);

// Mixer control
void N64Audio_SetMasterVolume(float volume);
float N64Audio_GetMasterVolume(void);
void N64Audio_EnableReverb(bool enabled);
void N64Audio_SetReverbParameters(float gain, float delay);

// Audio processing
void N64Audio_ProcessFrame(int16_t* output_left, int16_t* output_right, uint32_t num_samples);
void N64Audio_MixVoices(N64AudioVoice* voices, uint32_t num_voices,
                        int16_t* output_left, int16_t* output_right,
                        uint32_t num_samples);

// ADPCM utilities
void N64Audio_InitADPCMState(N64ADPCMState* state, uint8_t* data, uint32_t length);
void N64Audio_DecodeADPCM(N64ADPCMState* state, int16_t* output, uint32_t num_samples);

// Audio format conversion
void N64Audio_ConvertToFloat(int16_t* input, float* output, uint32_t num_samples);
void N64Audio_ConvertFromFloat(float* input, int16_t* output, uint32_t num_samples);
void N64Audio_ConvertSampleRate(int16_t* input, int16_t* output,
                                uint32_t input_samples, uint32_t output_samples);

// Audio debugging
void N64Audio_EnableDebugMode(bool enabled);
void N64Audio_GetDebugInfo(uint32_t* active_voices, uint32_t* total_samples,
                           float* cpu_usage, float* peak_level);

// N64 Audio Constants
#define N64_AUDIO_SAMPLE_RATE_32KHZ     32000
#define N64_AUDIO_SAMPLE_RATE_22KHZ     22050
#define N64_AUDIO_SAMPLE_RATE_16KHZ     16000
#define N64_AUDIO_SAMPLE_RATE_11KHZ     11025
#define N64_AUDIO_SAMPLE_RATE_8KHZ      8000

#define N64_AUDIO_MAX_VOICES            64
#define N64_AUDIO_BUFFER_SIZE           1024
#define N64_AUDIO_NUM_BUFFERS           3

#define N64_AUDIO_ADPCM_BLOCK_SIZE      9
#define N64_AUDIO_ADPCM_SAMPLES_PER_BLOCK 16

// N64 Audio Envelope States
#define N64_AUDIO_ENV_ATTACK            0
#define N64_AUDIO_ENV_DECAY             1
#define N64_AUDIO_ENV_SUSTAIN           2
#define N64_AUDIO_ENV_RELEASE           3
#define N64_AUDIO_ENV_IDLE              4

#ifdef __cplusplus
}
#endif 