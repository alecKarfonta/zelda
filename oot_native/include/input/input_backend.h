#pragma once

#include <stdint.h>
#include <stdbool.h>
#include "n64_input.h"

#ifdef __cplusplus
extern "C" {
#endif

// Forward declarations
typedef struct InputBackend InputBackend;
typedef struct InputSystem InputSystem;

// Input backend types
typedef enum {
    INPUT_BACKEND_SDL2,
    INPUT_BACKEND_DIRECTINPUT,
    INPUT_BACKEND_XINPUT,
    INPUT_BACKEND_EVDEV,
    INPUT_BACKEND_COUNT
} InputBackendType;

// Modern controller types
typedef enum {
    CONTROLLER_TYPE_UNKNOWN,
    CONTROLLER_TYPE_XBOX360,
    CONTROLLER_TYPE_XBOXONE,
    CONTROLLER_TYPE_PS3,
    CONTROLLER_TYPE_PS4,
    CONTROLLER_TYPE_PS5,
    CONTROLLER_TYPE_SWITCH_PRO,
    CONTROLLER_TYPE_N64,
    CONTROLLER_TYPE_KEYBOARD,
    CONTROLLER_TYPE_COUNT
} ControllerType;

// Controller device information
typedef struct {
    uint32_t device_id;
    ControllerType type;
    char name[256];
    char guid[64];
    bool supports_rumble;
    bool is_connected;
    uint32_t button_count;
    uint32_t axis_count;
    uint32_t hat_count;
} ControllerDevice;

// Raw controller input from backend
typedef struct {
    uint32_t device_id;
    uint32_t button_mask;       // Raw button bitmask
    int16_t axes[16];           // Raw axis values (-32768 to 32767)
    uint8_t hats[4];            // Hat/D-pad values
    bool is_connected;
    uint64_t timestamp;         // Input timestamp
} RawControllerInput;

// Backend configuration
typedef struct {
    InputBackendType backend_type;
    bool enable_rumble;
    bool enable_haptic;
    uint32_t poll_rate_hz;
    int8_t deadzone_threshold;
    float axis_sensitivity;
    bool enable_debug_logging;
} InputBackendConfig;

// Input backend function pointers (following graphics/audio backend pattern)
typedef struct InputBackend {
    // Backend identification
    InputBackendType type;
    const char* name;
    
    // Initialization and cleanup
    bool (*init)(InputBackendConfig* config);
    void (*shutdown)(void);
    
    // Device management
    uint32_t (*get_device_count)(void);
    bool (*get_device_info)(uint32_t device_index, ControllerDevice* info);
    bool (*open_device)(uint32_t device_id);
    void (*close_device)(uint32_t device_id);
    
    // Input polling
    bool (*poll_input)(uint32_t device_id, RawControllerInput* input);
    void (*poll_all_devices)(void);
    
    // Rumble/haptic feedback
    bool (*set_rumble)(uint32_t device_id, float low_freq, float high_freq, uint32_t duration_ms);
    void (*stop_rumble)(uint32_t device_id);
    
    // Configuration
    bool (*set_deadzone)(uint32_t device_id, int8_t deadzone);
    bool (*set_axis_sensitivity)(uint32_t device_id, float sensitivity);
    
    // Debug and diagnostics
    void (*get_debug_info)(char* buffer, uint32_t buffer_size);
    bool (*test_device)(uint32_t device_id);
    
    // Backend-specific data
    void* backend_data;
} InputBackend;

// Backend factory functions
InputBackend* InputBackend_CreateSDL2(void);
InputBackend* InputBackend_CreateDirectInput(void);
InputBackend* InputBackend_CreateXInput(void);
InputBackend* InputBackend_CreateEvdev(void);

// Backend management
InputBackend* InputBackend_Create(InputBackendType type);
void InputBackend_Destroy(InputBackend* backend);
const char* InputBackend_GetTypeName(InputBackendType type);

// Backend utility functions
bool InputBackend_IsBackendAvailable(InputBackendType type);
InputBackendType InputBackend_GetDefaultBackend(void);

#ifdef __cplusplus
}
#endif 