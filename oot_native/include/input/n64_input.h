#pragma once

#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// N64 controller button definitions (bitmask values)
#define N64_BUTTON_C_RIGHT     0x0001
#define N64_BUTTON_C_LEFT      0x0002
#define N64_BUTTON_C_DOWN      0x0004
#define N64_BUTTON_C_UP        0x0008
#define N64_BUTTON_R           0x0010
#define N64_BUTTON_L           0x0020
#define N64_BUTTON_D_RIGHT     0x0100
#define N64_BUTTON_D_LEFT      0x0200
#define N64_BUTTON_D_DOWN      0x0400
#define N64_BUTTON_D_UP        0x0800
#define N64_BUTTON_START       0x1000
#define N64_BUTTON_Z           0x2000
#define N64_BUTTON_B           0x4000
#define N64_BUTTON_A           0x8000

// N64 controller stick range
#define N64_STICK_MIN     -80
#define N64_STICK_MAX      80
#define N64_STICK_NEUTRAL   0

// N64 controller status flags
#define N64_CONTROLLER_CONNECTED    0x01
#define N64_CONTROLLER_RUMBLE_OK    0x02
#define N64_CONTROLLER_RUMBLE_ON    0x04

// N64 controller input structure (matches original hardware)
typedef struct {
    uint16_t button;        // Button bitmask
    int8_t stick_x;         // Analog stick X (-80 to 80)
    int8_t stick_y;         // Analog stick Y (-80 to 80)
    uint8_t status;         // Controller status flags
    uint8_t error_code;     // Controller error code
} N64ControllerInput;

// N64 controller state for all 4 controllers
typedef struct {
    N64ControllerInput controller[4];
    uint32_t frame_count;       // Frame counter for input timing
    bool valid;                 // True if input data is valid
} N64InputState;

// N64 button names for configuration
typedef enum {
    N64_BTN_A = 0,
    N64_BTN_B,
    N64_BTN_Z,
    N64_BTN_START,
    N64_BTN_L,
    N64_BTN_R,
    N64_BTN_C_UP,
    N64_BTN_C_DOWN,
    N64_BTN_C_LEFT,
    N64_BTN_C_RIGHT,
    N64_BTN_D_UP,
    N64_BTN_D_DOWN,
    N64_BTN_D_LEFT,
    N64_BTN_D_RIGHT,
    N64_BTN_COUNT
} N64ButtonType;

// N64 controller port
typedef enum {
    N64_PORT_1 = 0,
    N64_PORT_2,
    N64_PORT_3,
    N64_PORT_4,
    N64_PORT_COUNT
} N64ControllerPort;

// Helper functions for N64 input
static inline bool N64_IsButtonPressed(const N64ControllerInput* input, uint16_t button) {
    return (input->button & button) != 0;
}

static inline bool N64_IsStickInDeadzone(const N64ControllerInput* input, int8_t deadzone) {
    return (input->stick_x >= -deadzone && input->stick_x <= deadzone) &&
           (input->stick_y >= -deadzone && input->stick_y <= deadzone);
}

static inline float N64_GetStickXNormalized(const N64ControllerInput* input) {
    return (float)input->stick_x / 80.0f;
}

static inline float N64_GetStickYNormalized(const N64ControllerInput* input) {
    return (float)input->stick_y / 80.0f;
}

#ifdef __cplusplus
}
#endif 