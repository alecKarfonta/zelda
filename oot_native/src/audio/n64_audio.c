#include "audio/n64_audio.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

// Global N64 Audio State
typedef struct {
    bool initialized;
    uint32_t sample_rate;
    uint32_t buffer_size;
    uint32_t num_voices;
    float master_volume;
    bool debug_enabled;
    
    // Voice pool
    N64AudioVoice voices[N64_AUDIO_MAX_VOICES];
    bool voice_allocated[N64_AUDIO_MAX_VOICES];
    uint32_t active_voices;
    
    // Mixer state
    N64AudioMixer mixer;
    
    // Statistics
    uint32_t total_samples_processed;
    float cpu_usage;
    float peak_level;
    
    // Error handling
    char error_string[256];
} N64AudioState;

static N64AudioState g_n64_audio_state = {0};

// ADPCM decoding tables
static const int16_t adpcm_step_table[89] = {
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17,
    19, 21, 23, 25, 28, 31, 34, 37, 41, 45,
    50, 55, 60, 66, 73, 80, 88, 97, 107, 118,
    130, 143, 157, 173, 190, 209, 230, 253, 279, 307,
    337, 371, 408, 449, 494, 544, 598, 658, 724, 796,
    876, 963, 1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066,
    2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358,
    5894, 6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
    15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794, 32767
};

static const int16_t adpcm_index_table[16] = {
    -1, -1, -1, -1, 2, 4, 6, 8,
    -1, -1, -1, -1, 2, 4, 6, 8
};

// Utility functions
static void N64Audio_SetError(const char* error) {
    if (error) {
        strncpy(g_n64_audio_state.error_string, error, sizeof(g_n64_audio_state.error_string) - 1);
        g_n64_audio_state.error_string[sizeof(g_n64_audio_state.error_string) - 1] = '\0';
    } else {
        g_n64_audio_state.error_string[0] = '\0';
    }
}

static int16_t N64Audio_ClampSample(int32_t sample) {
    if (sample > 32767) return 32767;
    if (sample < -32768) return -32768;
    return (int16_t)sample;
}

static float N64Audio_LinearInterpolate(float a, float b, float t) {
    return a + t * (b - a);
}

// RSP Audio Function Implementations

// Environment Mixer - handles reverb and environmental audio effects
void aEnvMixerImpl(int16_t* input_left, int16_t* input_right, 
                   int16_t* output_left, int16_t* output_right,
                   uint32_t num_samples, float reverb_gain, float reverb_delay) {
    if (!input_left || !input_right || !output_left || !output_right) {
        return;
    }
    
    // Simple reverb implementation using a delay buffer
    static int16_t delay_buffer_left[4096] = {0};
    static int16_t delay_buffer_right[4096] = {0};
    static uint32_t delay_index = 0;
    
    uint32_t delay_samples = (uint32_t)(reverb_delay * g_n64_audio_state.sample_rate);
    delay_samples = delay_samples % 4096;
    
    for (uint32_t i = 0; i < num_samples; i++) {
        // Get delayed samples
        uint32_t delayed_index = (delay_index + 4096 - delay_samples) % 4096;
        int16_t delayed_left = delay_buffer_left[delayed_index];
        int16_t delayed_right = delay_buffer_right[delayed_index];
        
        // Apply reverb
        int32_t reverb_left = (int32_t)(delayed_left * reverb_gain);
        int32_t reverb_right = (int32_t)(delayed_right * reverb_gain);
        
        // Mix with input
        int32_t mixed_left = input_left[i] + reverb_left;
        int32_t mixed_right = input_right[i] + reverb_right;
        
        // Clamp and store output
        output_left[i] = N64Audio_ClampSample(mixed_left);
        output_right[i] = N64Audio_ClampSample(mixed_right);
        
        // Update delay buffer
        delay_buffer_left[delay_index] = input_left[i];
        delay_buffer_right[delay_index] = input_right[i];
        delay_index = (delay_index + 1) % 4096;
    }
}

// Resampler - converts between different sample rates
void aResampleImpl(int16_t* input, int16_t* output,
                   uint32_t input_samples, uint32_t output_samples,
                   uint32_t input_rate, uint32_t output_rate) {
    if (!input || !output || input_samples == 0 || output_samples == 0) {
        return;
    }
    
    float ratio = (float)input_samples / (float)output_samples;
    
    for (uint32_t i = 0; i < output_samples; i++) {
        float src_pos = i * ratio;
        uint32_t src_index = (uint32_t)src_pos;
        float frac = src_pos - src_index;
        
        if (src_index >= input_samples - 1) {
            output[i] = input[input_samples - 1];
        } else {
            // Linear interpolation
            float sample_a = (float)input[src_index];
            float sample_b = (float)input[src_index + 1];
            float interpolated = N64Audio_LinearInterpolate(sample_a, sample_b, frac);
            output[i] = (int16_t)interpolated;
        }
    }
}

// ADPCM Decoder - decompresses ADPCM audio data
void aADPCMdecImpl(N64ADPCMState* state, int16_t* output, uint32_t num_samples) {
    if (!state || !output || num_samples == 0) {
        return;
    }
    
    for (uint32_t i = 0; i < num_samples; i++) {
        if (state->position >= state->length) {
            output[i] = 0;
            continue;
        }
        
        // Get 4-bit ADPCM sample
        uint8_t adpcm_sample;
        if (state->position & 1) {
            adpcm_sample = state->data[state->position / 2] & 0x0F;
        } else {
            adpcm_sample = (state->data[state->position / 2] >> 4) & 0x0F;
        }
        
        // Decode ADPCM
        int16_t step = adpcm_step_table[state->index];
        int32_t diff = step >> 3;
        
        if (adpcm_sample & 4) diff += step;
        if (adpcm_sample & 2) diff += step >> 1;
        if (adpcm_sample & 1) diff += step >> 2;
        
        if (adpcm_sample & 8) {
            state->prev_sample -= diff;
        } else {
            state->prev_sample += diff;
        }
        
        // Clamp sample
        if (state->prev_sample > 32767) state->prev_sample = 32767;
        if (state->prev_sample < -32768) state->prev_sample = -32768;
        
        // Update index
        state->index += adpcm_index_table[adpcm_sample];
        if (state->index < 0) state->index = 0;
        if (state->index > 88) state->index = 88;
        
        output[i] = state->prev_sample;
        state->position++;
    }
}

// Audio Mixer - mixes multiple audio sources
void aMixImpl(N64AudioVoice* voices, uint32_t num_voices,
              int16_t* output_left, int16_t* output_right,
              uint32_t num_samples) {
    if (!voices || !output_left || !output_right || num_samples == 0) {
        return;
    }
    
    // Clear output buffers
    memset(output_left, 0, num_samples * sizeof(int16_t));
    memset(output_right, 0, num_samples * sizeof(int16_t));
    
    // Mix all active voices
    for (uint32_t v = 0; v < num_voices; v++) {
        N64AudioVoice* voice = &voices[v];
        
        if (!voice->is_active || !voice->buffer || voice->is_paused) {
            continue;
        }
        
        for (uint32_t i = 0; i < num_samples; i++) {
            // Check if we've reached the end of the buffer
            if (voice->position >= voice->buffer->samples) {
                if (voice->buffer->is_looping) {
                    voice->position = voice->buffer->loop_start;
                } else {
                    voice->is_active = false;
                    break;
                }
            }
            
            // Get sample from buffer
            int16_t sample = voice->buffer->data[voice->position];
            
            // Apply volume
            int32_t scaled_sample = (int32_t)(sample * voice->volume);
            
            // Apply panning
            int32_t left_sample = (int32_t)(scaled_sample * (1.0f - voice->pan));
            int32_t right_sample = (int32_t)(scaled_sample * voice->pan);
            
            // Mix into output
            int32_t mixed_left = output_left[i] + left_sample;
            int32_t mixed_right = output_right[i] + right_sample;
            
            // Clamp and store
            output_left[i] = N64Audio_ClampSample(mixed_left);
            output_right[i] = N64Audio_ClampSample(mixed_right);
            
            // Advance position
            voice->position += voice->increment;
        }
    }
}

// Buffer Load/Save - memory management for audio buffers
void aLoadBufferImpl(N64AudioBuffer* buffer, void* data, uint32_t size) {
    if (!buffer || !data || size == 0) {
        return;
    }
    
    // Allocate buffer if needed
    if (!buffer->data || buffer->size < size) {
        if (buffer->data) {
            free(buffer->data);
        }
        buffer->data = (int16_t*)malloc(size);
        if (!buffer->data) {
            N64Audio_SetError("Failed to allocate audio buffer");
            return;
        }
        buffer->size = size;
    }
    
    // Copy data
    memcpy(buffer->data, data, size);
    buffer->samples = size / sizeof(int16_t);
}

void aSaveBufferImpl(N64AudioBuffer* buffer, void* data, uint32_t size) {
    if (!buffer || !data || !buffer->data || size == 0) {
        return;
    }
    
    uint32_t copy_size = (buffer->size < size) ? buffer->size : size;
    memcpy(data, buffer->data, copy_size);
}

// Audio interpolation functions
void aInterpImpl(int16_t* input, int16_t* output, uint32_t num_samples, float ratio) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    for (uint32_t i = 0; i < num_samples; i++) {
        float src_pos = i * ratio;
        uint32_t src_index = (uint32_t)src_pos;
        float frac = src_pos - src_index;
        
        if (src_index >= num_samples - 1) {
            output[i] = input[num_samples - 1];
        } else {
            float sample_a = (float)input[src_index];
            float sample_b = (float)input[src_index + 1];
            float interpolated = N64Audio_LinearInterpolate(sample_a, sample_b, frac);
            output[i] = (int16_t)interpolated;
        }
    }
}

void aFilterImpl(int16_t* input, int16_t* output, uint32_t num_samples, float cutoff) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    // Simple low-pass filter
    static float prev_output = 0.0f;
    float alpha = cutoff;
    
    for (uint32_t i = 0; i < num_samples; i++) {
        float current_input = (float)input[i];
        float filtered = alpha * current_input + (1.0f - alpha) * prev_output;
        output[i] = (int16_t)filtered;
        prev_output = filtered;
    }
}

// Audio effects
void aChorusImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                 float delay, float depth, float rate) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    // Simple chorus effect
    static int16_t delay_buffer[8192] = {0};
    static uint32_t delay_index = 0;
    static float lfo_phase = 0.0f;
    
    uint32_t base_delay = (uint32_t)(delay * g_n64_audio_state.sample_rate);
    base_delay = base_delay % 8192;
    
    for (uint32_t i = 0; i < num_samples; i++) {
        // Calculate modulated delay
        float lfo = sinf(lfo_phase) * depth;
        uint32_t modulated_delay = base_delay + (uint32_t)(lfo * g_n64_audio_state.sample_rate);
        modulated_delay = modulated_delay % 8192;
        
        // Get delayed sample
        uint32_t delayed_index = (delay_index + 8192 - modulated_delay) % 8192;
        int16_t delayed_sample = delay_buffer[delayed_index];
        
        // Mix with input
        int32_t mixed = input[i] + (delayed_sample >> 1);
        output[i] = N64Audio_ClampSample(mixed);
        
        // Update delay buffer
        delay_buffer[delay_index] = input[i];
        delay_index = (delay_index + 1) % 8192;
        
        // Update LFO
        lfo_phase += rate * 2.0f * M_PI / g_n64_audio_state.sample_rate;
        if (lfo_phase >= 2.0f * M_PI) lfo_phase -= 2.0f * M_PI;
    }
}

void aFlangerImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                  float delay, float depth, float rate) {
    // Similar to chorus but with different parameters
    aChorusImpl(input, output, num_samples, delay * 0.1f, depth, rate);
}

void aDistortionImpl(int16_t* input, int16_t* output, uint32_t num_samples,
                     float drive, float level) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    for (uint32_t i = 0; i < num_samples; i++) {
        float sample = (float)input[i] / 32768.0f;
        
        // Apply drive
        sample *= drive;
        
        // Soft clipping
        if (sample > 1.0f) sample = 1.0f;
        if (sample < -1.0f) sample = -1.0f;
        sample = tanhf(sample);
        
        // Apply level
        sample *= level;
        
        output[i] = (int16_t)(sample * 32767.0f);
    }
}

// N64 Audio System Functions

bool N64Audio_Init(uint32_t sample_rate, uint32_t buffer_size, uint32_t num_voices) {
    if (g_n64_audio_state.initialized) {
        N64Audio_SetError("N64 audio already initialized");
        return false;
    }
    
    // Initialize state
    g_n64_audio_state.sample_rate = sample_rate;
    g_n64_audio_state.buffer_size = buffer_size;
    g_n64_audio_state.num_voices = (num_voices > N64_AUDIO_MAX_VOICES) ? N64_AUDIO_MAX_VOICES : num_voices;
    g_n64_audio_state.master_volume = 1.0f;
    g_n64_audio_state.debug_enabled = false;
    g_n64_audio_state.active_voices = 0;
    
    // Initialize voice pool
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        g_n64_audio_state.voice_allocated[i] = false;
        memset(&g_n64_audio_state.voices[i], 0, sizeof(N64AudioVoice));
    }
    
    // Initialize mixer
    g_n64_audio_state.mixer.buffer_size = buffer_size;
    g_n64_audio_state.mixer.sample_rate = sample_rate;
    g_n64_audio_state.mixer.num_voices = num_voices;
    g_n64_audio_state.mixer.master_volume = 1.0f;
    g_n64_audio_state.mixer.reverb_enabled = false;
    g_n64_audio_state.mixer.reverb_gain = 0.3f;
    g_n64_audio_state.mixer.reverb_delay = 0.1f;
    
    // Allocate mixer buffers
    g_n64_audio_state.mixer.left_buffer = (int16_t*)malloc(buffer_size * sizeof(int16_t));
    g_n64_audio_state.mixer.right_buffer = (int16_t*)malloc(buffer_size * sizeof(int16_t));
    
    if (!g_n64_audio_state.mixer.left_buffer || !g_n64_audio_state.mixer.right_buffer) {
        N64Audio_SetError("Failed to allocate mixer buffers");
        return false;
    }
    
    g_n64_audio_state.initialized = true;
    N64Audio_SetError(NULL);
    
    return true;
}

void N64Audio_Shutdown(void) {
    if (!g_n64_audio_state.initialized) {
        return;
    }
    
    // Free mixer buffers
    if (g_n64_audio_state.mixer.left_buffer) {
        free(g_n64_audio_state.mixer.left_buffer);
        g_n64_audio_state.mixer.left_buffer = NULL;
    }
    
    if (g_n64_audio_state.mixer.right_buffer) {
        free(g_n64_audio_state.mixer.right_buffer);
        g_n64_audio_state.mixer.right_buffer = NULL;
    }
    
    // Free all allocated voices
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        if (g_n64_audio_state.voice_allocated[i]) {
            N64Audio_FreeVoice(&g_n64_audio_state.voices[i]);
        }
    }
    
    g_n64_audio_state.initialized = false;
}

// Voice management
N64AudioVoice* N64Audio_AllocateVoice(void) {
    if (!g_n64_audio_state.initialized) {
        return NULL;
    }
    
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        if (!g_n64_audio_state.voice_allocated[i]) {
            g_n64_audio_state.voice_allocated[i] = true;
            g_n64_audio_state.active_voices++;
            
            N64AudioVoice* voice = &g_n64_audio_state.voices[i];
            memset(voice, 0, sizeof(N64AudioVoice));
            voice->volume = 1.0f;
            voice->pan = 0.5f;
            voice->increment = 1;
            
            return voice;
        }
    }
    
    return NULL;
}

void N64Audio_FreeVoice(N64AudioVoice* voice) {
    if (!voice || !g_n64_audio_state.initialized) {
        return;
    }
    
    // Find voice in pool
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        if (&g_n64_audio_state.voices[i] == voice) {
            g_n64_audio_state.voice_allocated[i] = false;
            g_n64_audio_state.active_voices--;
            memset(voice, 0, sizeof(N64AudioVoice));
            break;
        }
    }
}

// Error handling
const char* N64Audio_GetErrorString(void) {
    return g_n64_audio_state.error_string;
}

// ========================================
// MISSING FUNCTION IMPLEMENTATIONS
// ========================================

// Buffer Management Functions
N64AudioBuffer* N64Audio_CreateBuffer(uint32_t samples, uint32_t sample_rate, uint32_t channels, N64AudioFormat format) {
    if (!g_n64_audio_state.initialized) {
        N64Audio_SetError("Audio system not initialized");
        return NULL;
    }
    
    if (samples == 0 || sample_rate == 0 || channels == 0) {
        N64Audio_SetError("Invalid buffer parameters");
        return NULL;
    }
    
    N64AudioBuffer* buffer = (N64AudioBuffer*)malloc(sizeof(N64AudioBuffer));
    if (!buffer) {
        N64Audio_SetError("Failed to allocate buffer structure");
        return NULL;
    }
    
    // Calculate buffer size based on format and channels
    uint32_t sample_size = (format == N64_AUDIO_FORMAT_PCM16) ? 2 : 1;
    uint32_t total_size = samples * channels * sample_size;
    
    buffer->data = (int16_t*)malloc(total_size);
    if (!buffer->data) {
        free(buffer);
        N64Audio_SetError("Failed to allocate buffer data");
        return NULL;
    }
    
    // Initialize buffer structure
    buffer->size = total_size;
    buffer->samples = samples;
    buffer->sample_rate = sample_rate;
    buffer->channels = channels;
    buffer->format = format;
    buffer->is_looping = false;
    buffer->loop_start = 0;
    buffer->loop_end = samples;
    
    // Clear buffer data
    memset(buffer->data, 0, total_size);
    
    return buffer;
}

void N64Audio_DestroyBuffer(N64AudioBuffer* buffer) {
    if (!buffer) {
        return;
    }
    
    // Stop all voices using this buffer
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        if (g_n64_audio_state.voice_allocated[i] && 
            g_n64_audio_state.voices[i].buffer == buffer) {
            N64Audio_StopVoice(&g_n64_audio_state.voices[i]);
        }
    }
    
    // Free buffer data and structure
    if (buffer->data) {
        free(buffer->data);
    }
    free(buffer);
}

void N64Audio_LoadBufferData(N64AudioBuffer* buffer, void* data, uint32_t size) {
    if (!buffer || !data || size == 0) {
        N64Audio_SetError("Invalid buffer load parameters");
        return;
    }
    
    // Ensure we don't exceed buffer capacity
    uint32_t copy_size = (size < buffer->size) ? size : buffer->size;
    
    // Copy data to buffer
    memcpy(buffer->data, data, copy_size);
    
    // If we copied less than the buffer size, clear the rest
    if (copy_size < buffer->size) {
        memset((char*)buffer->data + copy_size, 0, buffer->size - copy_size);
    }
}

// Voice Management Functions
void N64Audio_PlayVoice(N64AudioVoice* voice, N64AudioBuffer* buffer) {
    if (!voice || !buffer || !g_n64_audio_state.initialized) {
        N64Audio_SetError("Invalid voice play parameters");
        return;
    }
    
    // Stop voice if it's already playing
    if (voice->is_active) {
        N64Audio_StopVoice(voice);
    }
    
    // Initialize voice with buffer
    voice->buffer = buffer;
    voice->position = 0;
    voice->increment = (buffer->sample_rate * 65536) / g_n64_audio_state.sample_rate; // Fixed-point increment
    voice->is_active = true;
    voice->is_paused = false;
    
    // Initialize ADPCM state if needed
    if (buffer->format == N64_AUDIO_FORMAT_ADPCM) {
        N64Audio_InitADPCMState(&voice->adpcm_state, (uint8_t*)buffer->data, buffer->size);
    }
}

void N64Audio_StopVoice(N64AudioVoice* voice) {
    if (!voice) {
        return;
    }
    
    voice->is_active = false;
    voice->is_paused = false;
    voice->buffer = NULL;
    voice->position = 0;
    
    // Reset ADPCM state
    memset(&voice->adpcm_state, 0, sizeof(N64ADPCMState));
}

void N64Audio_SetVoiceVolume(N64AudioVoice* voice, float volume) {
    if (!voice) {
        return;
    }
    
    // Clamp volume to valid range
    voice->volume = (volume < 0.0f) ? 0.0f : (volume > 1.0f) ? 1.0f : volume;
}

void N64Audio_SetVoicePan(N64AudioVoice* voice, float pan) {
    if (!voice) {
        return;
    }
    
    // Clamp pan to valid range (0.0 = left, 0.5 = center, 1.0 = right)
    voice->pan = (pan < 0.0f) ? 0.0f : (pan > 1.0f) ? 1.0f : pan;
}

void N64Audio_SetVoicePitch(N64AudioVoice* voice, float pitch) {
    if (!voice || !voice->buffer) {
        return;
    }
    
    // Clamp pitch to reasonable range
    pitch = (pitch < 0.1f) ? 0.1f : (pitch > 4.0f) ? 4.0f : pitch;
    
    // Calculate new increment based on pitch
    voice->increment = (uint32_t)((voice->buffer->sample_rate * pitch * 65536) / g_n64_audio_state.sample_rate);
}

// Master Volume Functions
void N64Audio_SetMasterVolume(float volume) {
    if (!g_n64_audio_state.initialized) {
        return;
    }
    
    // Clamp volume to valid range
    g_n64_audio_state.master_volume = (volume < 0.0f) ? 0.0f : (volume > 1.0f) ? 1.0f : volume;
}

float N64Audio_GetMasterVolume(void) {
    return g_n64_audio_state.master_volume;
}

// Reverb Functions
void N64Audio_EnableReverb(bool enabled) {
    if (!g_n64_audio_state.initialized) {
        return;
    }
    
    g_n64_audio_state.mixer.reverb_enabled = enabled;
}

void N64Audio_SetReverbParameters(float gain, float delay) {
    if (!g_n64_audio_state.initialized) {
        return;
    }
    
    g_n64_audio_state.mixer.reverb_gain = (gain < 0.0f) ? 0.0f : (gain > 1.0f) ? 1.0f : gain;
    g_n64_audio_state.mixer.reverb_delay = (delay < 0.0f) ? 0.0f : delay;
}

// Main Audio Processing Function
void N64Audio_ProcessFrame(int16_t* output_left, int16_t* output_right, uint32_t num_samples) {
    if (!g_n64_audio_state.initialized || !output_left || !output_right || num_samples == 0) {
        return;
    }
    
    // Clear output buffers
    memset(output_left, 0, num_samples * sizeof(int16_t));
    memset(output_right, 0, num_samples * sizeof(int16_t));
    
    // Process each active voice
    for (uint32_t i = 0; i < N64_AUDIO_MAX_VOICES; i++) {
        if (!g_n64_audio_state.voice_allocated[i] || !g_n64_audio_state.voices[i].is_active) {
            continue;
        }
        
        N64AudioVoice* voice = &g_n64_audio_state.voices[i];
        if (!voice->buffer || voice->is_paused) {
            continue;
        }
        
        // Process voice samples
        for (uint32_t sample = 0; sample < num_samples; sample++) {
            if (voice->position >= (voice->buffer->samples * 65536)) {
                // Handle looping
                if (voice->buffer->is_looping) {
                    voice->position = voice->buffer->loop_start * 65536;
                } else {
                    voice->is_active = false;
                    break;
                }
            }
            
            // Get sample from buffer
            int16_t sample_value = 0;
            uint32_t buffer_index = voice->position >> 16;
            
            if (buffer_index < voice->buffer->samples) {
                if (voice->buffer->format == N64_AUDIO_FORMAT_ADPCM) {
                    // Decode ADPCM sample
                    N64Audio_DecodeADPCM(&voice->adpcm_state, &sample_value, 1);
                } else {
                    // Direct PCM sample
                    sample_value = voice->buffer->data[buffer_index * voice->buffer->channels];
                }
            }
            
            // Apply voice volume
            float float_sample = (float)sample_value * voice->volume;
            
            // Apply panning
            float left_gain = 1.0f - voice->pan;
            float right_gain = voice->pan;
            
            // Mix into output buffers
            int32_t left_output = (int32_t)(float_sample * left_gain);
            int32_t right_output = (int32_t)(float_sample * right_gain);
            
            // Clamp and mix
            output_left[sample] = N64Audio_ClampSample(output_left[sample] + left_output);
            output_right[sample] = N64Audio_ClampSample(output_right[sample] + right_output);
            
            // Advance position
            voice->position += voice->increment;
        }
    }
    
    // Apply master volume
    for (uint32_t i = 0; i < num_samples; i++) {
        output_left[i] = N64Audio_ClampSample((int32_t)(output_left[i] * g_n64_audio_state.master_volume));
        output_right[i] = N64Audio_ClampSample((int32_t)(output_right[i] * g_n64_audio_state.master_volume));
    }
    
    // Apply reverb if enabled
    if (g_n64_audio_state.mixer.reverb_enabled) {
        aEnvMixerImpl(output_left, output_right, output_left, output_right, 
                     num_samples, g_n64_audio_state.mixer.reverb_gain, 
                     g_n64_audio_state.mixer.reverb_delay);
    }
    
    // Update statistics
    g_n64_audio_state.total_samples_processed += num_samples;
}

// Voice Mixing Function
void N64Audio_MixVoices(N64AudioVoice* voices, uint32_t num_voices,
                        int16_t* output_left, int16_t* output_right,
                        uint32_t num_samples) {
    if (!voices || !output_left || !output_right || num_samples == 0) {
        return;
    }
    
    // Use the existing aMixImpl function
    aMixImpl(voices, num_voices, output_left, output_right, num_samples);
}

// ADPCM Functions
void N64Audio_InitADPCMState(N64ADPCMState* state, uint8_t* data, uint32_t length) {
    if (!state || !data) {
        return;
    }
    
    state->prev_sample = 0;
    state->index = 0;
    state->header = 0;
    state->data = data;
    state->position = 0;
    state->length = length;
}

void N64Audio_DecodeADPCM(N64ADPCMState* state, int16_t* output, uint32_t num_samples) {
    if (!state || !output || num_samples == 0) {
        return;
    }
    
    // Use the existing aADPCMdecImpl function
    aADPCMdecImpl(state, output, num_samples);
}

// Format Conversion Functions
void N64Audio_ConvertToFloat(int16_t* input, float* output, uint32_t num_samples) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    for (uint32_t i = 0; i < num_samples; i++) {
        output[i] = (float)input[i] / 32768.0f;
    }
}

void N64Audio_ConvertFromFloat(float* input, int16_t* output, uint32_t num_samples) {
    if (!input || !output || num_samples == 0) {
        return;
    }
    
    for (uint32_t i = 0; i < num_samples; i++) {
        float sample = input[i] * 32768.0f;
        output[i] = N64Audio_ClampSample((int32_t)sample);
    }
}

void N64Audio_ConvertSampleRate(int16_t* input, int16_t* output,
                                uint32_t input_samples, uint32_t output_samples) {
    if (!input || !output || input_samples == 0 || output_samples == 0) {
        return;
    }
    
    // Use the existing aResampleImpl function
    aResampleImpl(input, output, input_samples, output_samples, 
                  input_samples, output_samples);
}

// Debug Functions
void N64Audio_EnableDebugMode(bool enabled) {
    g_n64_audio_state.debug_enabled = enabled;
}

void N64Audio_GetDebugInfo(uint32_t* active_voices, uint32_t* total_samples,
                           float* cpu_usage, float* peak_level) {
    if (active_voices) {
        *active_voices = g_n64_audio_state.active_voices;
    }
    if (total_samples) {
        *total_samples = g_n64_audio_state.total_samples_processed;
    }
    if (cpu_usage) {
        *cpu_usage = g_n64_audio_state.cpu_usage;
    }
    if (peak_level) {
        *peak_level = g_n64_audio_state.peak_level;
    }
} 