#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "input_backend.h"

#ifdef __cplusplus
extern "C" {
#endif

// SDL2 specific includes
#include <SDL2/SDL.h>

// Maximum number of controllers supported
#define SDL_MAX_CONTROLLERS 4

// SDL2 controller state
typedef struct {
    SDL_GameController* controller;
    SDL_Joystick* joystick;
    SDL_Haptic* haptic;
    uint32_t device_id;
    bool is_open;
    bool supports_rumble;
    char name[256];
    char guid[64];
    uint32_t button_count;
    uint32_t axis_count;
    uint32_t hat_count;
    uint64_t last_input_time;
    RawControllerInput last_input;
} SDL_ControllerState;

// SDL2 backend data
typedef struct {
    SDL_ControllerState controllers[SDL_MAX_CONTROLLERS];
    uint32_t controller_count;
    bool is_initialized;
    InputBackendConfig config;
    
    // Input state tracking
    uint64_t frame_counter;
    uint32_t events_processed;
    
    // Debug information
    char debug_buffer[1024];
    bool debug_enabled;
} SDL_InputBackendData;

// SDL2 backend interface functions
bool SDL_InputBackend_Init(InputBackendConfig* config);
void SDL_InputBackend_Shutdown(void);

// Device management
uint32_t SDL_InputBackend_GetDeviceCount(void);
bool SDL_InputBackend_GetDeviceInfo(uint32_t device_index, ControllerDevice* info);
bool SDL_InputBackend_OpenDevice(uint32_t device_id);
void SDL_InputBackend_CloseDevice(uint32_t device_id);

// Input polling
bool SDL_InputBackend_PollInput(uint32_t device_id, RawControllerInput* input);
void SDL_InputBackend_PollAllDevices(void);

// Rumble/haptic feedback
bool SDL_InputBackend_SetRumble(uint32_t device_id, float low_freq, float high_freq, uint32_t duration_ms);
void SDL_InputBackend_StopRumble(uint32_t device_id);

// Configuration
bool SDL_InputBackend_SetDeadzone(uint32_t device_id, int8_t deadzone);
bool SDL_InputBackend_SetAxisSensitivity(uint32_t device_id, float sensitivity);

// Debug and diagnostics
void SDL_InputBackend_GetDebugInfo(char* buffer, uint32_t buffer_size);
bool SDL_InputBackend_TestDevice(uint32_t device_id);

// SDL2 utility functions
ControllerType SDL_InputBackend_DetectControllerType(const char* controller_name);
bool SDL_InputBackend_InitSDL(void);
void SDL_InputBackend_ProcessSDLEvents(void);

// Controller event callbacks
void SDL_InputBackend_OnControllerAdded(int device_index);
void SDL_InputBackend_OnControllerRemoved(int instance_id);
void SDL_InputBackend_OnControllerButtonDown(int instance_id, uint8_t button);
void SDL_InputBackend_OnControllerButtonUp(int instance_id, uint8_t button);
void SDL_InputBackend_OnControllerAxisMotion(int instance_id, uint8_t axis, int16_t value);

// Internal helper functions
SDL_ControllerState* SDL_InputBackend_GetControllerByDeviceId(uint32_t device_id);
SDL_ControllerState* SDL_InputBackend_GetControllerByInstanceId(int instance_id);
uint32_t SDL_InputBackend_GetNextDeviceId(void);
void SDL_InputBackend_UpdateControllerInfo(SDL_ControllerState* state);

// Backend creation function
InputBackend* InputBackend_CreateSDL2(void);

#ifdef __cplusplus
}
#endif 