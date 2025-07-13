#include "input/input_api.h"
#include "input/sdl_input_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>

// Global input system state
struct InputSystem {
    InputBackend* backend;
    InputConfig config;
    bool is_initialized;
    bool game_input_blocked;
    
    // N64 controller state
    N64InputState current_state;
    N64InputState previous_state;
    
    // Controller mapping
    uint32_t controller_device_mapping[N64_PORT_COUNT];  // Device ID for each port
    ControllerProfile profiles[N64_PORT_COUNT];
    
    // Event system
    InputEventCallback event_callbacks[INPUT_EVENT_COUNT];
    void* event_user_data[INPUT_EVENT_COUNT];
    
    // Debug and diagnostics
    bool debug_enabled;
    char debug_buffer[2048];
    uint32_t frame_count;
};

static struct InputSystem g_input_system = {0};

// Button name lookup table
static const char* g_button_names[N64_BTN_COUNT] = {
    "A", "B", "Z", "START", "L", "R",
    "C-Up", "C-Down", "C-Left", "C-Right",
    "D-Up", "D-Down", "D-Left", "D-Right"
};

// Port name lookup table
static const char* g_port_names[N64_PORT_COUNT] = {
    "Port 1", "Port 2", "Port 3", "Port 4"
};

// Controller type name lookup table
static const char* g_controller_type_names[CONTROLLER_TYPE_COUNT] = {
    "Unknown", "Xbox 360", "Xbox One", "PlayStation 3", "PlayStation 4",
    "PlayStation 5", "Nintendo Switch Pro", "N64", "Keyboard"
};

// Backend name lookup table
static const char* g_backend_names[INPUT_BACKEND_COUNT] = {
    "SDL2", "DirectInput", "XInput", "evdev"
};

// Default button mappings for different controller types
static void Input_LoadDefaultButtonMapping(N64ControllerPort port, ControllerType type) {
    ControllerProfile* profile = &g_input_system.profiles[port];
    
    // Clear existing mappings
    memset(profile->mappings, 0, sizeof(profile->mappings));
    profile->mapping_count = 0;
    
    // Set default values
    profile->stick_sensitivity = 1.0f;
    profile->stick_deadzone = 10;
    profile->enable_rumble = true;
    profile->controller_type = type;
    
    // Configure mappings based on controller type
    switch (type) {
        case CONTROLLER_TYPE_XBOX360:
        case CONTROLLER_TYPE_XBOXONE:
            // Xbox controller mapping (using SDL2 constants)
            profile->mappings[N64_BTN_A].mapped_button = SDL_CONTROLLER_BUTTON_A;
            profile->mappings[N64_BTN_B].mapped_button = SDL_CONTROLLER_BUTTON_X;
            profile->mappings[N64_BTN_Z].mapped_button = SDL_CONTROLLER_BUTTON_RIGHTSHOULDER;
            profile->mappings[N64_BTN_START].mapped_button = SDL_CONTROLLER_BUTTON_START;
            profile->mappings[N64_BTN_L].mapped_button = SDL_CONTROLLER_BUTTON_LEFTSHOULDER;
            profile->mappings[N64_BTN_R].mapped_axis = SDL_CONTROLLER_AXIS_TRIGGERRIGHT;
            profile->mappings[N64_BTN_R].is_axis_positive = true;
            profile->mappings[N64_BTN_R].axis_threshold = 0.5f;
            profile->mappings[N64_BTN_C_UP].mapped_button = SDL_CONTROLLER_BUTTON_Y;
            profile->mappings[N64_BTN_C_DOWN].mapped_button = SDL_CONTROLLER_BUTTON_B;
            profile->mappings[N64_BTN_C_LEFT].mapped_axis = SDL_CONTROLLER_AXIS_RIGHTX;
            profile->mappings[N64_BTN_C_LEFT].is_axis_positive = false;
            profile->mappings[N64_BTN_C_RIGHT].mapped_axis = SDL_CONTROLLER_AXIS_RIGHTX;
            profile->mappings[N64_BTN_C_RIGHT].is_axis_positive = true;
            profile->mappings[N64_BTN_D_UP].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_UP;
            profile->mappings[N64_BTN_D_DOWN].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_DOWN;
            profile->mappings[N64_BTN_D_LEFT].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_LEFT;
            profile->mappings[N64_BTN_D_RIGHT].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_RIGHT;
            profile->mapping_count = N64_BTN_COUNT;
            break;
            
        case CONTROLLER_TYPE_PS4:
        case CONTROLLER_TYPE_PS5:
            // PlayStation controller mapping
            profile->mappings[N64_BTN_A].mapped_button = SDL_CONTROLLER_BUTTON_A; // Cross
            profile->mappings[N64_BTN_B].mapped_button = SDL_CONTROLLER_BUTTON_X; // Square
            profile->mappings[N64_BTN_Z].mapped_button = SDL_CONTROLLER_BUTTON_RIGHTSHOULDER;
            profile->mappings[N64_BTN_START].mapped_button = SDL_CONTROLLER_BUTTON_START;
            profile->mappings[N64_BTN_L].mapped_button = SDL_CONTROLLER_BUTTON_LEFTSHOULDER;
            profile->mappings[N64_BTN_R].mapped_axis = SDL_CONTROLLER_AXIS_TRIGGERRIGHT;
            profile->mappings[N64_BTN_R].is_axis_positive = true;
            profile->mappings[N64_BTN_R].axis_threshold = 0.5f;
            profile->mappings[N64_BTN_C_UP].mapped_button = SDL_CONTROLLER_BUTTON_Y; // Triangle
            profile->mappings[N64_BTN_C_DOWN].mapped_button = SDL_CONTROLLER_BUTTON_B; // Circle
            profile->mappings[N64_BTN_C_LEFT].mapped_axis = SDL_CONTROLLER_AXIS_RIGHTX;
            profile->mappings[N64_BTN_C_LEFT].is_axis_positive = false;
            profile->mappings[N64_BTN_C_RIGHT].mapped_axis = SDL_CONTROLLER_AXIS_RIGHTX;
            profile->mappings[N64_BTN_C_RIGHT].is_axis_positive = true;
            profile->mappings[N64_BTN_D_UP].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_UP;
            profile->mappings[N64_BTN_D_DOWN].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_DOWN;
            profile->mappings[N64_BTN_D_LEFT].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_LEFT;
            profile->mappings[N64_BTN_D_RIGHT].mapped_button = SDL_CONTROLLER_BUTTON_DPAD_RIGHT;
            profile->mapping_count = N64_BTN_COUNT;
            break;
            
        default:
            // Generic controller mapping
            profile->mappings[N64_BTN_A].mapped_button = 0;
            profile->mappings[N64_BTN_B].mapped_button = 1;
            profile->mappings[N64_BTN_Z].mapped_button = 2;
            profile->mappings[N64_BTN_START].mapped_button = 3;
            profile->mapping_count = 4;
            break;
    }
    
    snprintf(profile->name, sizeof(profile->name), "Default %s", g_controller_type_names[type]);
}

// Event dispatch function
static void Input_DispatchEvent(const InputEvent* event) {
    if (event->type < INPUT_EVENT_COUNT && g_input_system.event_callbacks[event->type]) {
        g_input_system.event_callbacks[event->type](event, g_input_system.event_user_data[event->type]);
    }
}

// Convert raw input to N64 controller input
static void Input_ConvertRawToN64(uint32_t device_id, const RawControllerInput* raw_input, N64ControllerInput* n64_input) {
    // Find the port this device is mapped to
    N64ControllerPort port = N64_PORT_COUNT;
    for (int i = 0; i < N64_PORT_COUNT; i++) {
        if (g_input_system.controller_device_mapping[i] == device_id) {
            port = i;
            break;
        }
    }
    
    if (port >= N64_PORT_COUNT) {
        return; // Device not mapped to any port
    }
    
    ControllerProfile* profile = &g_input_system.profiles[port];
    
    // Clear N64 input
    memset(n64_input, 0, sizeof(N64ControllerInput));
    n64_input->status = N64_CONTROLLER_CONNECTED;
    
    // Process button mappings
    for (int i = 0; i < N64_BTN_COUNT; i++) {
        const ButtonMapping* mapping = &profile->mappings[i];
        bool button_active = false;
        
        if (mapping->mapped_axis >= 0) {
            // Axis mapping
            if (mapping->mapped_axis < 16) {
                int16_t axis_value = raw_input->axes[mapping->mapped_axis];
                float normalized_value = axis_value / 32767.0f;
                
                if (mapping->is_axis_positive) {
                    button_active = normalized_value > mapping->axis_threshold;
                } else {
                    button_active = normalized_value < -mapping->axis_threshold;
                }
            }
        } else {
            // Button mapping
            button_active = (raw_input->button_mask & (1 << mapping->mapped_button)) != 0;
        }
        
        if (button_active) {
            switch (i) {
                case N64_BTN_A: n64_input->button |= N64_BUTTON_A; break;
                case N64_BTN_B: n64_input->button |= N64_BUTTON_B; break;
                case N64_BTN_Z: n64_input->button |= N64_BUTTON_Z; break;
                case N64_BTN_START: n64_input->button |= N64_BUTTON_START; break;
                case N64_BTN_L: n64_input->button |= N64_BUTTON_L; break;
                case N64_BTN_R: n64_input->button |= N64_BUTTON_R; break;
                case N64_BTN_C_UP: n64_input->button |= N64_BUTTON_C_UP; break;
                case N64_BTN_C_DOWN: n64_input->button |= N64_BUTTON_C_DOWN; break;
                case N64_BTN_C_LEFT: n64_input->button |= N64_BUTTON_C_LEFT; break;
                case N64_BTN_C_RIGHT: n64_input->button |= N64_BUTTON_C_RIGHT; break;
                case N64_BTN_D_UP: n64_input->button |= N64_BUTTON_D_UP; break;
                case N64_BTN_D_DOWN: n64_input->button |= N64_BUTTON_D_DOWN; break;
                case N64_BTN_D_LEFT: n64_input->button |= N64_BUTTON_D_LEFT; break;
                case N64_BTN_D_RIGHT: n64_input->button |= N64_BUTTON_D_RIGHT; break;
            }
        }
    }
    
    // Process analog stick (assume first two axes are left stick)
    if (raw_input->axes[0] != 0 || raw_input->axes[1] != 0) {
        float stick_x = raw_input->axes[0] / 32767.0f * profile->stick_sensitivity;
        float stick_y = raw_input->axes[1] / 32767.0f * profile->stick_sensitivity;
        
        // Apply deadzone
        if (fabsf(stick_x) < profile->stick_deadzone / 80.0f) stick_x = 0.0f;
        if (fabsf(stick_y) < profile->stick_deadzone / 80.0f) stick_y = 0.0f;
        
        // Convert to N64 range
        n64_input->stick_x = (int8_t)(stick_x * 80.0f);
        n64_input->stick_y = (int8_t)(stick_y * 80.0f);
        
        // Clamp to N64 range
        if (n64_input->stick_x < N64_STICK_MIN) n64_input->stick_x = N64_STICK_MIN;
        if (n64_input->stick_x > N64_STICK_MAX) n64_input->stick_x = N64_STICK_MAX;
        if (n64_input->stick_y < N64_STICK_MIN) n64_input->stick_y = N64_STICK_MIN;
        if (n64_input->stick_y > N64_STICK_MAX) n64_input->stick_y = N64_STICK_MAX;
    }
    
    // Set rumble status
    if (profile->enable_rumble) {
        n64_input->status |= N64_CONTROLLER_RUMBLE_OK;
    }
}

// Public API implementation
bool Input_Init(InputConfig* config) {
    if (g_input_system.is_initialized) {
        return false; // Already initialized
    }
    
    // Copy configuration
    if (config) {
        memcpy(&g_input_system.config, config, sizeof(InputConfig));
    } else {
        // Default configuration
        g_input_system.config.backend = INPUT_BACKEND_SDL2;
        g_input_system.config.enable_rumble = true;
        g_input_system.config.enable_haptic = true;
        g_input_system.config.poll_rate_hz = 60;
        g_input_system.config.deadzone_threshold = 10;
        g_input_system.config.axis_sensitivity = 1.0f;
        g_input_system.config.enable_debug_logging = false;
        g_input_system.config.enable_multiple_controllers = true;
        g_input_system.config.enable_keyboard_controller = true;
        g_input_system.config.enable_auto_mapping = true;
        g_input_system.config.enable_runtime_config = true;
    }
    
    // Create backend
    g_input_system.backend = InputBackend_Create(g_input_system.config.backend);
    if (!g_input_system.backend) {
        printf("Failed to create input backend\n");
        return false;
    }
    
    // Initialize backend
    InputBackendConfig backend_config = {
        .backend_type = g_input_system.config.backend,
        .enable_rumble = g_input_system.config.enable_rumble,
        .enable_haptic = g_input_system.config.enable_haptic,
        .poll_rate_hz = g_input_system.config.poll_rate_hz,
        .deadzone_threshold = g_input_system.config.deadzone_threshold,
        .axis_sensitivity = g_input_system.config.axis_sensitivity,
        .enable_debug_logging = g_input_system.config.enable_debug_logging
    };
    
    if (!g_input_system.backend->init(&backend_config)) {
        printf("Failed to initialize input backend\n");
        InputBackend_Destroy(g_input_system.backend);
        g_input_system.backend = NULL;
        return false;
    }
    
    // Initialize controller mappings
    for (int i = 0; i < N64_PORT_COUNT; i++) {
        g_input_system.controller_device_mapping[i] = UINT32_MAX; // No device mapped
        Input_LoadDefaultButtonMapping(i, CONTROLLER_TYPE_UNKNOWN);
    }
    
    // Initialize input state
    memset(&g_input_system.current_state, 0, sizeof(N64InputState));
    memset(&g_input_system.previous_state, 0, sizeof(N64InputState));
    g_input_system.current_state.valid = true;
    g_input_system.previous_state.valid = true;
    
    g_input_system.is_initialized = true;
    g_input_system.game_input_blocked = false;
    g_input_system.frame_count = 0;
    
    printf("Input system initialized with %s backend\n", g_input_system.backend->name);
    return true;
}

void Input_Shutdown(void) {
    if (!g_input_system.is_initialized) {
        return;
    }
    
    // Shutdown backend
    if (g_input_system.backend) {
        g_input_system.backend->shutdown();
        InputBackend_Destroy(g_input_system.backend);
        g_input_system.backend = NULL;
    }
    
    // Clear state
    memset(&g_input_system, 0, sizeof(InputSystem));
    
    printf("Input system shutdown\n");
}

void Input_ProcessFrame(void) {
    if (!g_input_system.is_initialized || !g_input_system.backend) {
        return;
    }
    
    // Store previous state
    memcpy(&g_input_system.previous_state, &g_input_system.current_state, sizeof(N64InputState));
    
    // Poll all devices
    g_input_system.backend->poll_all_devices();
    
    // Process input for each mapped controller
    for (int port = 0; port < N64_PORT_COUNT; port++) {
        uint32_t device_id = g_input_system.controller_device_mapping[port];
        if (device_id == UINT32_MAX) {
            // No device mapped to this port
            memset(&g_input_system.current_state.controller[port], 0, sizeof(N64ControllerInput));
            continue;
        }
        
        // Get raw input from backend
        RawControllerInput raw_input;
        if (g_input_system.backend->poll_input(device_id, &raw_input)) {
            // Convert to N64 input
            Input_ConvertRawToN64(device_id, &raw_input, &g_input_system.current_state.controller[port]);
        } else {
            // Device not available
            memset(&g_input_system.current_state.controller[port], 0, sizeof(N64ControllerInput));
        }
    }
    
    // Update frame count
    g_input_system.current_state.frame_count = ++g_input_system.frame_count;
    
    // Block game input if requested
    if (g_input_system.game_input_blocked) {
        for (int i = 0; i < N64_PORT_COUNT; i++) {
            memset(&g_input_system.current_state.controller[i], 0, sizeof(N64ControllerInput));
        }
    }
}

const N64InputState* Input_GetCurrentState(void) {
    return &g_input_system.current_state;
}

const N64ControllerInput* Input_GetController(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT) {
        return NULL;
    }
    return &g_input_system.current_state.controller[port];
}

// Controller abstraction layer (Ship of Harkinian pattern)
bool Controller_ShouldRumble(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT) {
        return false;
    }
    
    const N64ControllerInput* controller = &g_input_system.current_state.controller[port];
    return (controller->status & N64_CONTROLLER_RUMBLE_OK) != 0;
}

void Controller_BlockGameInput(bool block) {
    g_input_system.game_input_blocked = block;
}

void Controller_UnblockGameInput(void) {
    g_input_system.game_input_blocked = false;
}

bool Controller_IsGameInputBlocked(void) {
    return g_input_system.game_input_blocked;
}

// Controller management
uint32_t Input_GetControllerCount(void) {
    if (!g_input_system.backend) {
        return 0;
    }
    return g_input_system.backend->get_device_count();
}

bool Input_GetControllerInfo(uint32_t index, ControllerDevice* info) {
    if (!g_input_system.backend || !info) {
        return false;
    }
    return g_input_system.backend->get_device_info(index, info);
}

bool Input_ConnectController(uint32_t device_id, N64ControllerPort port) {
    if (port >= N64_PORT_COUNT || !g_input_system.backend) {
        return false;
    }
    
    // Open device
    if (!g_input_system.backend->open_device(device_id)) {
        return false;
    }
    
    // Map device to port
    g_input_system.controller_device_mapping[port] = device_id;
    
    // Try to auto-detect controller type and load default profile
    if (g_input_system.config.enable_auto_mapping) {
        ControllerDevice device_info;
        if (g_input_system.backend->get_device_info(device_id, &device_info)) {
            Input_LoadDefaultButtonMapping(port, device_info.type);
        }
    }
    
    printf("Controller connected: device %u mapped to port %d\n", device_id, port);
    return true;
}

void Input_DisconnectController(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT) {
        return;
    }
    
    uint32_t device_id = g_input_system.controller_device_mapping[port];
    if (device_id != UINT32_MAX && g_input_system.backend) {
        g_input_system.backend->close_device(device_id);
        g_input_system.controller_device_mapping[port] = UINT32_MAX;
        printf("Controller disconnected from port %d\n", port);
    }
}

bool Input_IsControllerConnected(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT) {
        return false;
    }
    return g_input_system.controller_device_mapping[port] != UINT32_MAX;
}

// Utility functions
const char* Input_GetButtonName(N64ButtonType button) {
    if (button >= N64_BTN_COUNT) {
        return "Unknown";
    }
    return g_button_names[button];
}

const char* Input_GetPortName(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT) {
        return "Unknown";
    }
    return g_port_names[port];
}

const char* Input_GetControllerTypeName(ControllerType type) {
    if (type >= CONTROLLER_TYPE_COUNT) {
        return "Unknown";
    }
    return g_controller_type_names[type];
}

const char* Input_GetBackendName(InputBackendType backend) {
    if (backend >= INPUT_BACKEND_COUNT) {
        return "Unknown";
    }
    return g_backend_names[backend];
}

// Debug functions
void Input_EnableDebugMode(bool enabled) {
    g_input_system.debug_enabled = enabled;
}

bool Input_IsDebugModeEnabled(void) {
    return g_input_system.debug_enabled;
}

void Input_GetDebugInfo(char* buffer, uint32_t buffer_size) {
    if (!buffer || buffer_size == 0) {
        return;
    }
    
    snprintf(buffer, buffer_size,
        "Input System Debug Info:\n"
        "Backend: %s\n"
        "Frame Count: %u\n"
        "Game Input Blocked: %s\n"
        "Controllers Connected: %u\n"
        "Port Mappings: [%u, %u, %u, %u]\n",
        g_input_system.backend ? g_input_system.backend->name : "None",
        g_input_system.frame_count,
        g_input_system.game_input_blocked ? "Yes" : "No",
        Input_GetControllerCount(),
        g_input_system.controller_device_mapping[0],
        g_input_system.controller_device_mapping[1],
        g_input_system.controller_device_mapping[2],
        g_input_system.controller_device_mapping[3]
    );
}

// Stub implementations for remaining functions
bool Input_SetRumble(N64ControllerPort port, float intensity, uint32_t duration_ms) {
    if (port >= N64_PORT_COUNT || !g_input_system.backend) {
        return false;
    }
    
    uint32_t device_id = g_input_system.controller_device_mapping[port];
    if (device_id == UINT32_MAX) {
        return false;
    }
    
    return g_input_system.backend->set_rumble(device_id, intensity, intensity, duration_ms);
}

void Input_StopRumble(N64ControllerPort port) {
    if (port >= N64_PORT_COUNT || !g_input_system.backend) {
        return;
    }
    
    uint32_t device_id = g_input_system.controller_device_mapping[port];
    if (device_id != UINT32_MAX) {
        g_input_system.backend->stop_rumble(device_id);
    }
}

void Input_StopAllRumble(void) {
    for (int i = 0; i < N64_PORT_COUNT; i++) {
        Input_StopRumble(i);
    }
}

InputBackendType Input_GetCurrentBackend(void) {
    return g_input_system.config.backend;
}

bool Input_IsBackendAvailable(InputBackendType backend) {
    return InputBackend_IsBackendAvailable(backend);
}

// Backend factory functions
InputBackend* InputBackend_Create(InputBackendType type) {
    switch (type) {
        case INPUT_BACKEND_SDL2:
            return InputBackend_CreateSDL2();
        case INPUT_BACKEND_DIRECTINPUT:
            return InputBackend_CreateDirectInput();
        case INPUT_BACKEND_XINPUT:
            return InputBackend_CreateXInput();
        case INPUT_BACKEND_EVDEV:
            return InputBackend_CreateEvdev();
        default:
            return NULL;
    }
}

void InputBackend_Destroy(InputBackend* backend) {
    if (backend) {
        free(backend);
    }
}

const char* InputBackend_GetTypeName(InputBackendType type) {
    if (type >= INPUT_BACKEND_COUNT) {
        return "Unknown";
    }
    return g_backend_names[type];
}

bool InputBackend_IsBackendAvailable(InputBackendType type) {
    switch (type) {
        case INPUT_BACKEND_SDL2:
            return true; // SDL2 is always available if compiled in
        case INPUT_BACKEND_DIRECTINPUT:
            #ifdef _WIN32
                return true;
            #else
                return false;
            #endif
        case INPUT_BACKEND_XINPUT:
            #ifdef _WIN32
                return true;
            #else
                return false;
            #endif
        case INPUT_BACKEND_EVDEV:
            #ifdef __linux__
                return true;
            #else
                return false;
            #endif
        default:
            return false;
    }
}

InputBackendType InputBackend_GetDefaultBackend(void) {
    #ifdef _WIN32
        return INPUT_BACKEND_XINPUT;
    #elif defined(__linux__)
        return INPUT_BACKEND_SDL2;
    #elif defined(__APPLE__)
        return INPUT_BACKEND_SDL2;
    #else
        return INPUT_BACKEND_SDL2;
    #endif
}

// Stub implementations for non-SDL2 backends
InputBackend* InputBackend_CreateDirectInput(void) {
    printf("DirectInput backend not implemented\n");
    return NULL;
}

InputBackend* InputBackend_CreateXInput(void) {
    printf("XInput backend not implemented\n");
    return NULL;
}

InputBackend* InputBackend_CreateEvdev(void) {
    printf("evdev backend not implemented\n");
    return NULL;
} 