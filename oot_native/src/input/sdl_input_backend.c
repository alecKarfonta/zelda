#include "input/sdl_input_backend.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Global SDL2 backend data
static SDL_InputBackendData g_sdl_backend_data = {0};

// SDL2 backend function implementations
bool SDL_InputBackend_Init(InputBackendConfig* config) {
    if (g_sdl_backend_data.is_initialized) {
        return false;
    }
    
    // Initialize SDL2
    if (!SDL_InputBackend_InitSDL()) {
        return false;
    }
    
    // Copy configuration
    if (config) {
        memcpy(&g_sdl_backend_data.config, config, sizeof(InputBackendConfig));
    } else {
        // Default configuration
        g_sdl_backend_data.config.backend_type = INPUT_BACKEND_SDL2;
        g_sdl_backend_data.config.enable_rumble = true;
        g_sdl_backend_data.config.enable_haptic = true;
        g_sdl_backend_data.config.poll_rate_hz = 60;
        g_sdl_backend_data.config.deadzone_threshold = 10;
        g_sdl_backend_data.config.axis_sensitivity = 1.0f;
        g_sdl_backend_data.config.enable_debug_logging = false;
    }
    
    // Initialize controller states
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        SDL_ControllerState* state = &g_sdl_backend_data.controllers[i];
        memset(state, 0, sizeof(SDL_ControllerState));
        state->device_id = UINT32_MAX;
        state->is_open = false;
    }
    
    g_sdl_backend_data.controller_count = 0;
    g_sdl_backend_data.is_initialized = true;
    g_sdl_backend_data.frame_counter = 0;
    g_sdl_backend_data.events_processed = 0;
    
    printf("SDL2 input backend initialized\n");
    return true;
}

void SDL_InputBackend_Shutdown(void) {
    if (!g_sdl_backend_data.is_initialized) {
        return;
    }
    
    // Close all controllers
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        SDL_ControllerState* state = &g_sdl_backend_data.controllers[i];
        if (state->is_open) {
            if (state->haptic) {
                SDL_HapticClose(state->haptic);
            }
            if (state->controller) {
                SDL_GameControllerClose(state->controller);
            }
            state->is_open = false;
        }
    }
    
    // Shutdown SDL2 joystick subsystem
    SDL_QuitSubSystem(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER | SDL_INIT_HAPTIC);
    
    memset(&g_sdl_backend_data, 0, sizeof(SDL_InputBackendData));
    
    printf("SDL2 input backend shutdown\n");
}

uint32_t SDL_InputBackend_GetDeviceCount(void) {
    return SDL_NumJoysticks();
}

bool SDL_InputBackend_GetDeviceInfo(uint32_t device_index, ControllerDevice* info) {
    if (!info || device_index >= SDL_NumJoysticks()) {
        return false;
    }
    
    // Get basic joystick info
    const char* name = SDL_JoystickNameForIndex(device_index);
    SDL_JoystickGUID guid = SDL_JoystickGetDeviceGUID(device_index);
    
    // Fill device info
    info->device_id = device_index;
    info->type = SDL_InputBackend_DetectControllerType(name);
    strncpy(info->name, name ? name : "Unknown Controller", sizeof(info->name) - 1);
    info->name[sizeof(info->name) - 1] = '\0';
    
    // Convert GUID to string
    SDL_JoystickGetGUIDString(guid, info->guid, sizeof(info->guid));
    
    info->supports_rumble = SDL_IsGameController(device_index);
    info->is_connected = true;
    
    // Get button/axis counts
    if (SDL_IsGameController(device_index)) {
        info->button_count = SDL_CONTROLLER_BUTTON_MAX;
        info->axis_count = SDL_CONTROLLER_AXIS_MAX;
        info->hat_count = 0;
    } else {
        // For non-game controllers, we need to open temporarily to get counts
        SDL_Joystick* joy = SDL_JoystickOpen(device_index);
        if (joy) {
            info->button_count = SDL_JoystickNumButtons(joy);
            info->axis_count = SDL_JoystickNumAxes(joy);
            info->hat_count = SDL_JoystickNumHats(joy);
            SDL_JoystickClose(joy);
        } else {
            info->button_count = 0;
            info->axis_count = 0;
            info->hat_count = 0;
        }
    }
    
    return true;
}

bool SDL_InputBackend_OpenDevice(uint32_t device_id) {
    if (device_id >= SDL_NumJoysticks()) {
        return false;
    }
    
    // Find an available controller slot
    SDL_ControllerState* state = NULL;
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        if (!g_sdl_backend_data.controllers[i].is_open) {
            state = &g_sdl_backend_data.controllers[i];
            break;
        }
    }
    
    if (!state) {
        printf("No available controller slots\n");
        return false;
    }
    
    // Try to open as game controller first
    if (SDL_IsGameController(device_id)) {
        state->controller = SDL_GameControllerOpen(device_id);
        if (state->controller) {
            state->joystick = SDL_GameControllerGetJoystick(state->controller);
        }
    } else {
        // Open as regular joystick
        state->joystick = SDL_JoystickOpen(device_id);
    }
    
    if (!state->joystick) {
        printf("Failed to open device %u: %s\n", device_id, SDL_GetError());
        return false;
    }
    
    // Initialize haptic feedback if available
    if (g_sdl_backend_data.config.enable_haptic && SDL_JoystickIsHaptic(state->joystick)) {
        state->haptic = SDL_HapticOpenFromJoystick(state->joystick);
        if (state->haptic) {
            if (SDL_HapticRumbleInit(state->haptic) != 0) {
                SDL_HapticClose(state->haptic);
                state->haptic = NULL;
            } else {
                state->supports_rumble = true;
            }
        }
    }
    
    // Update controller info
    state->device_id = device_id;
    state->is_open = true;
    SDL_InputBackend_UpdateControllerInfo(state);
    
    g_sdl_backend_data.controller_count++;
    
    printf("Opened controller: %s (device %u)\n", state->name, device_id);
    return true;
}

void SDL_InputBackend_CloseDevice(uint32_t device_id) {
    SDL_ControllerState* state = SDL_InputBackend_GetControllerByDeviceId(device_id);
    if (!state || !state->is_open) {
        return;
    }
    
    // Close haptic
    if (state->haptic) {
        SDL_HapticClose(state->haptic);
        state->haptic = NULL;
    }
    
    // Close controller/joystick
    if (state->controller) {
        SDL_GameControllerClose(state->controller);
        state->controller = NULL;
    } else if (state->joystick) {
        SDL_JoystickClose(state->joystick);
    }
    
    state->joystick = NULL;
    state->is_open = false;
    state->device_id = UINT32_MAX;
    
    g_sdl_backend_data.controller_count--;
    
    printf("Closed controller device %u\n", device_id);
}

bool SDL_InputBackend_PollInput(uint32_t device_id, RawControllerInput* input) {
    SDL_ControllerState* state = SDL_InputBackend_GetControllerByDeviceId(device_id);
    if (!state || !state->is_open || !input) {
        return false;
    }
    
    // Clear input
    memset(input, 0, sizeof(RawControllerInput));
    input->device_id = device_id;
    input->is_connected = SDL_JoystickGetAttached(state->joystick);
    input->timestamp = SDL_GetTicks64();
    
    if (state->controller) {
        // Game controller interface
        for (int i = 0; i < SDL_CONTROLLER_BUTTON_MAX; i++) {
            if (SDL_GameControllerGetButton(state->controller, i)) {
                input->button_mask |= (1 << i);
            }
        }
        
        // Get axis values
        for (int i = 0; i < SDL_CONTROLLER_AXIS_MAX && i < 16; i++) {
            input->axes[i] = SDL_GameControllerGetAxis(state->controller, i);
        }
    } else if (state->joystick) {
        // Regular joystick interface
        int num_buttons = SDL_JoystickNumButtons(state->joystick);
        for (int i = 0; i < num_buttons && i < 32; i++) {
            if (SDL_JoystickGetButton(state->joystick, i)) {
                input->button_mask |= (1 << i);
            }
        }
        
        // Get axis values
        int num_axes = SDL_JoystickNumAxes(state->joystick);
        for (int i = 0; i < num_axes && i < 16; i++) {
            input->axes[i] = SDL_JoystickGetAxis(state->joystick, i);
        }
        
        // Get hat values
        int num_hats = SDL_JoystickNumHats(state->joystick);
        for (int i = 0; i < num_hats && i < 4; i++) {
            input->hats[i] = SDL_JoystickGetHat(state->joystick, i);
        }
    }
    
    // Store last input
    memcpy(&state->last_input, input, sizeof(RawControllerInput));
    state->last_input_time = input->timestamp;
    
    return true;
}

void SDL_InputBackend_PollAllDevices(void) {
    // Process SDL events
    SDL_InputBackend_ProcessSDLEvents();
    
    // Poll all open controllers
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        SDL_ControllerState* state = &g_sdl_backend_data.controllers[i];
        if (state->is_open) {
            RawControllerInput input;
            SDL_InputBackend_PollInput(state->device_id, &input);
        }
    }
    
    g_sdl_backend_data.frame_counter++;
}

bool SDL_InputBackend_SetRumble(uint32_t device_id, float low_freq, float high_freq, uint32_t duration_ms) {
    SDL_ControllerState* state = SDL_InputBackend_GetControllerByDeviceId(device_id);
    if (!state || !state->is_open || !state->supports_rumble) {
        return false;
    }
    
    if (state->haptic) {
        // Use haptic rumble
        float strength = (low_freq + high_freq) * 0.5f;
        if (strength > 1.0f) strength = 1.0f;
        if (strength < 0.0f) strength = 0.0f;
        
        return SDL_HapticRumblePlay(state->haptic, strength, duration_ms) == 0;
    } else if (state->controller) {
        // Use game controller rumble (SDL 2.0.9+)
        uint16_t low = (uint16_t)(low_freq * 65535.0f);
        uint16_t high = (uint16_t)(high_freq * 65535.0f);
        
        return SDL_GameControllerRumble(state->controller, low, high, duration_ms) == 0;
    }
    
    return false;
}

void SDL_InputBackend_StopRumble(uint32_t device_id) {
    SDL_ControllerState* state = SDL_InputBackend_GetControllerByDeviceId(device_id);
    if (!state || !state->is_open) {
        return;
    }
    
    if (state->haptic) {
        SDL_HapticRumbleStop(state->haptic);
    } else if (state->controller) {
        SDL_GameControllerRumble(state->controller, 0, 0, 0);
    }
}

bool SDL_InputBackend_SetDeadzone(uint32_t device_id, int8_t deadzone) {
    // SDL2 doesn't have per-device deadzone setting
    // This would be handled at the input conversion level
    return true;
}

bool SDL_InputBackend_SetAxisSensitivity(uint32_t device_id, float sensitivity) {
    // SDL2 doesn't have per-device sensitivity setting
    // This would be handled at the input conversion level
    return true;
}

void SDL_InputBackend_GetDebugInfo(char* buffer, uint32_t buffer_size) {
    if (!buffer || buffer_size == 0) {
        return;
    }
    
    snprintf(buffer, buffer_size,
        "SDL2 Input Backend Debug Info:\n"
        "Initialized: %s\n"
        "Available Devices: %d\n"
        "Open Controllers: %u\n"
        "Frame Counter: %lu\n"
        "Events Processed: %u\n",
        g_sdl_backend_data.is_initialized ? "Yes" : "No",
        SDL_NumJoysticks(),
        g_sdl_backend_data.controller_count,
        (unsigned long)g_sdl_backend_data.frame_counter,
        g_sdl_backend_data.events_processed
    );
}

bool SDL_InputBackend_TestDevice(uint32_t device_id) {
    SDL_ControllerState* state = SDL_InputBackend_GetControllerByDeviceId(device_id);
    if (!state || !state->is_open) {
        return false;
    }
    
    return SDL_JoystickGetAttached(state->joystick);
}

// Utility function implementations
ControllerType SDL_InputBackend_DetectControllerType(const char* controller_name) {
    if (!controller_name) {
        return CONTROLLER_TYPE_UNKNOWN;
    }
    
    // Convert to lowercase for comparison
    char name_lower[256];
    strncpy(name_lower, controller_name, sizeof(name_lower) - 1);
    name_lower[sizeof(name_lower) - 1] = '\0';
    
    for (int i = 0; name_lower[i]; i++) {
        if (name_lower[i] >= 'A' && name_lower[i] <= 'Z') {
            name_lower[i] = name_lower[i] - 'A' + 'a';
        }
    }
    
    // Check for known controller types
    if (strstr(name_lower, "xbox 360") || strstr(name_lower, "xbox360")) {
        return CONTROLLER_TYPE_XBOX360;
    }
    if (strstr(name_lower, "xbox one") || strstr(name_lower, "xboxone")) {
        return CONTROLLER_TYPE_XBOXONE;
    }
    if (strstr(name_lower, "ps3") || strstr(name_lower, "playstation 3")) {
        return CONTROLLER_TYPE_PS3;
    }
    if (strstr(name_lower, "ps4") || strstr(name_lower, "playstation 4") || strstr(name_lower, "dualshock 4")) {
        return CONTROLLER_TYPE_PS4;
    }
    if (strstr(name_lower, "ps5") || strstr(name_lower, "playstation 5") || strstr(name_lower, "dualsense")) {
        return CONTROLLER_TYPE_PS5;
    }
    if (strstr(name_lower, "switch") || strstr(name_lower, "pro controller")) {
        return CONTROLLER_TYPE_SWITCH_PRO;
    }
    
    return CONTROLLER_TYPE_UNKNOWN;
}

bool SDL_InputBackend_InitSDL(void) {
    // Initialize SDL2 subsystems
    if (SDL_InitSubSystem(SDL_INIT_JOYSTICK | SDL_INIT_GAMECONTROLLER | SDL_INIT_HAPTIC) != 0) {
        printf("Failed to initialize SDL2 input subsystems: %s\n", SDL_GetError());
        return false;
    }
    
    // Enable joystick events
    SDL_JoystickEventState(SDL_ENABLE);
    SDL_GameControllerEventState(SDL_ENABLE);
    
    printf("SDL2 input subsystems initialized\n");
    return true;
}

void SDL_InputBackend_ProcessSDLEvents(void) {
    SDL_Event event;
    while (SDL_PollEvent(&event)) {
        switch (event.type) {
            case SDL_CONTROLLERDEVICEADDED:
                SDL_InputBackend_OnControllerAdded(event.cdevice.which);
                break;
                
            case SDL_CONTROLLERDEVICEREMOVED:
                SDL_InputBackend_OnControllerRemoved(event.cdevice.which);
                break;
                
            case SDL_CONTROLLERBUTTONDOWN:
                SDL_InputBackend_OnControllerButtonDown(event.cbutton.which, event.cbutton.button);
                break;
                
            case SDL_CONTROLLERBUTTONUP:
                SDL_InputBackend_OnControllerButtonUp(event.cbutton.which, event.cbutton.button);
                break;
                
            case SDL_CONTROLLERAXISMOTION:
                SDL_InputBackend_OnControllerAxisMotion(event.caxis.which, event.caxis.axis, event.caxis.value);
                break;
                
            default:
                break;
        }
        
        g_sdl_backend_data.events_processed++;
    }
}

// Event callback implementations
void SDL_InputBackend_OnControllerAdded(int device_index) {
    printf("Controller added: device index %d\n", device_index);
}

void SDL_InputBackend_OnControllerRemoved(int instance_id) {
    printf("Controller removed: instance ID %d\n", instance_id);
}

void SDL_InputBackend_OnControllerButtonDown(int instance_id, uint8_t button) {
    if (g_sdl_backend_data.config.enable_debug_logging) {
        printf("Button down: instance %d, button %d\n", instance_id, button);
    }
}

void SDL_InputBackend_OnControllerButtonUp(int instance_id, uint8_t button) {
    if (g_sdl_backend_data.config.enable_debug_logging) {
        printf("Button up: instance %d, button %d\n", instance_id, button);
    }
}

void SDL_InputBackend_OnControllerAxisMotion(int instance_id, uint8_t axis, int16_t value) {
    if (g_sdl_backend_data.config.enable_debug_logging && abs(value) > 1000) {
        printf("Axis motion: instance %d, axis %d, value %d\n", instance_id, axis, value);
    }
}

// Helper function implementations
SDL_ControllerState* SDL_InputBackend_GetControllerByDeviceId(uint32_t device_id) {
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        if (g_sdl_backend_data.controllers[i].device_id == device_id) {
            return &g_sdl_backend_data.controllers[i];
        }
    }
    return NULL;
}

SDL_ControllerState* SDL_InputBackend_GetControllerByInstanceId(int instance_id) {
    for (int i = 0; i < SDL_MAX_CONTROLLERS; i++) {
        SDL_ControllerState* state = &g_sdl_backend_data.controllers[i];
        if (state->is_open && state->joystick) {
            if (SDL_JoystickInstanceID(state->joystick) == instance_id) {
                return state;
            }
        }
    }
    return NULL;
}

uint32_t SDL_InputBackend_GetNextDeviceId(void) {
    static uint32_t next_id = 0;
    return next_id++;
}

void SDL_InputBackend_UpdateControllerInfo(SDL_ControllerState* state) {
    if (!state || !state->joystick) {
        return;
    }
    
    // Update controller name
    const char* name = NULL;
    if (state->controller) {
        name = SDL_GameControllerName(state->controller);
    } else {
        name = SDL_JoystickName(state->joystick);
    }
    
    if (name) {
        strncpy(state->name, name, sizeof(state->name) - 1);
        state->name[sizeof(state->name) - 1] = '\0';
    } else {
        strcpy(state->name, "Unknown Controller");
    }
    
    // Update GUID
    SDL_JoystickGUID guid = SDL_JoystickGetGUID(state->joystick);
    SDL_JoystickGetGUIDString(guid, state->guid, sizeof(state->guid));
    
    // Update button/axis counts
    if (state->controller) {
        state->button_count = SDL_CONTROLLER_BUTTON_MAX;
        state->axis_count = SDL_CONTROLLER_AXIS_MAX;
        state->hat_count = 0;
    } else {
        state->button_count = SDL_JoystickNumButtons(state->joystick);
        state->axis_count = SDL_JoystickNumAxes(state->joystick);
        state->hat_count = SDL_JoystickNumHats(state->joystick);
    }
}

// Backend creation function
InputBackend* InputBackend_CreateSDL2(void) {
    InputBackend* backend = malloc(sizeof(InputBackend));
    if (!backend) {
        return NULL;
    }
    
    // Initialize function pointers
    backend->type = INPUT_BACKEND_SDL2;
    backend->name = "SDL2";
    backend->init = SDL_InputBackend_Init;
    backend->shutdown = SDL_InputBackend_Shutdown;
    backend->get_device_count = SDL_InputBackend_GetDeviceCount;
    backend->get_device_info = SDL_InputBackend_GetDeviceInfo;
    backend->open_device = SDL_InputBackend_OpenDevice;
    backend->close_device = SDL_InputBackend_CloseDevice;
    backend->poll_input = SDL_InputBackend_PollInput;
    backend->poll_all_devices = SDL_InputBackend_PollAllDevices;
    backend->set_rumble = SDL_InputBackend_SetRumble;
    backend->stop_rumble = SDL_InputBackend_StopRumble;
    backend->set_deadzone = SDL_InputBackend_SetDeadzone;
    backend->set_axis_sensitivity = SDL_InputBackend_SetAxisSensitivity;
    backend->get_debug_info = SDL_InputBackend_GetDebugInfo;
    backend->test_device = SDL_InputBackend_TestDevice;
    backend->backend_data = &g_sdl_backend_data;
    
    return backend;
} 