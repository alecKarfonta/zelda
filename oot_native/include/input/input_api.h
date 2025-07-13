#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "n64_input.h"
#include "input_backend.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct InputSystem InputSystem;

// Input configuration
typedef struct {
    InputBackendType backend;
    bool enable_rumble;
    bool enable_haptic;
    uint32_t poll_rate_hz;
    int8_t deadzone_threshold;
    float axis_sensitivity;
    bool enable_debug_logging;
    
    // Enhancement features
    bool enable_multiple_controllers;
    bool enable_keyboard_controller;
    bool enable_auto_mapping;
    bool enable_runtime_config;
} InputConfig;

// Button mapping structure
typedef struct {
    uint32_t device_id;
    N64ButtonType n64_button;
    uint32_t mapped_button;     // Device-specific button index
    int8_t mapped_axis;         // Axis index (-1 if not axis)
    bool is_axis_positive;      // True for positive axis direction
    float axis_threshold;       // Threshold for axis-to-button mapping
} ButtonMapping;

// Controller mapping profile
typedef struct {
    char name[64];
    ControllerType controller_type;
    ButtonMapping mappings[N64_BTN_COUNT];
    float stick_sensitivity;
    int8_t stick_deadzone;
    bool enable_rumble;
    uint32_t mapping_count;
} ControllerProfile;

// Input system initialization
bool Input_Init(InputConfig* config);
void Input_Shutdown(void);

// Main input processing (Ship of Harkinian pattern)
void Input_ProcessFrame(void);
const N64InputState* Input_GetCurrentState(void);
const N64ControllerInput* Input_GetController(N64ControllerPort port);

// Controller abstraction layer (SoH-style functions)
bool Controller_ShouldRumble(N64ControllerPort port);
void Controller_BlockGameInput(bool block);
void Controller_UnblockGameInput(void);
bool Controller_IsGameInputBlocked(void);

// Controller management
uint32_t Input_GetControllerCount(void);
bool Input_GetControllerInfo(uint32_t index, ControllerDevice* info);
bool Input_ConnectController(uint32_t device_id, N64ControllerPort port);
void Input_DisconnectController(N64ControllerPort port);
bool Input_IsControllerConnected(N64ControllerPort port);

// Button mapping system
bool Input_LoadControllerProfile(const char* profile_name, N64ControllerPort port);
bool Input_SaveControllerProfile(const char* profile_name, N64ControllerPort port);
bool Input_SetButtonMapping(N64ControllerPort port, N64ButtonType n64_button, uint32_t device_button);
bool Input_SetAxisMapping(N64ControllerPort port, N64ButtonType n64_button, int8_t axis, bool positive, float threshold);
bool Input_ClearButtonMapping(N64ControllerPort port, N64ButtonType n64_button);
const ButtonMapping* Input_GetButtonMapping(N64ControllerPort port, N64ButtonType n64_button);

// Configuration management
bool Input_SetDeadzone(N64ControllerPort port, int8_t deadzone);
bool Input_SetSensitivity(N64ControllerPort port, float sensitivity);
bool Input_SetRumbleEnabled(N64ControllerPort port, bool enabled);
int8_t Input_GetDeadzone(N64ControllerPort port);
float Input_GetSensitivity(N64ControllerPort port);
bool Input_IsRumbleEnabled(N64ControllerPort port);

// Rumble/haptic feedback
bool Input_SetRumble(N64ControllerPort port, float intensity, uint32_t duration_ms);
void Input_StopRumble(N64ControllerPort port);
void Input_StopAllRumble(void);

// Backend management
bool Input_SetBackend(InputBackendType backend);
InputBackendType Input_GetCurrentBackend(void);
const char* Input_GetBackendName(InputBackendType backend);
bool Input_IsBackendAvailable(InputBackendType backend);

// Utility functions
const char* Input_GetButtonName(N64ButtonType button);
const char* Input_GetPortName(N64ControllerPort port);
const char* Input_GetControllerTypeName(ControllerType type);

// Debug and diagnostics
void Input_EnableDebugMode(bool enabled);
bool Input_IsDebugModeEnabled(void);
void Input_GetDebugInfo(char* buffer, uint32_t buffer_size);
void Input_PrintControllerInfo(N64ControllerPort port);

// Configuration file management
bool Input_LoadConfig(const char* config_file);
bool Input_SaveConfig(const char* config_file);
bool Input_ResetToDefaults(void);

// Auto-mapping utilities
bool Input_AutoMapController(uint32_t device_id, N64ControllerPort port);
bool Input_DetectControllerType(uint32_t device_id, ControllerType* type);
bool Input_LoadDefaultProfile(ControllerType type, N64ControllerPort port);

// Event system for input changes
typedef enum {
    INPUT_EVENT_CONTROLLER_CONNECTED,
    INPUT_EVENT_CONTROLLER_DISCONNECTED,
    INPUT_EVENT_BUTTON_PRESSED,
    INPUT_EVENT_BUTTON_RELEASED,
    INPUT_EVENT_STICK_MOVED,
    INPUT_EVENT_RUMBLE_STARTED,
    INPUT_EVENT_RUMBLE_STOPPED,
    INPUT_EVENT_COUNT
} InputEventType;

typedef struct {
    InputEventType type;
    N64ControllerPort port;
    uint32_t device_id;
    union {
        struct { N64ButtonType button; } button_event;
        struct { int8_t x, y; } stick_event;
        struct { float intensity; uint32_t duration; } rumble_event;
    } data;
    uint64_t timestamp;
} InputEvent;

typedef void (*InputEventCallback)(const InputEvent* event, void* user_data);

// Event system
bool Input_RegisterEventCallback(InputEventType type, InputEventCallback callback, void* user_data);
void Input_UnregisterEventCallback(InputEventType type, InputEventCallback callback);
void Input_ClearAllEventCallbacks(void);

#ifdef __cplusplus
}
#endif 