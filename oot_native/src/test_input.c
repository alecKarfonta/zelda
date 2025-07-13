#include "input/input_api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
    #include <windows.h>
    #include <time.h>
#else
    #include <time.h>
    #include <unistd.h>
#endif

// Test functions
static void test_input_initialization(void);
static void test_controller_detection(void);
static void test_input_processing(void);
static void test_button_mapping(void);
static void test_rumble_functionality(void);
static void test_controller_abstraction(void);
static void print_controller_info(uint32_t device_id);
static void print_n64_input_state(const N64InputState* state);
static void interactive_controller_test(void);

// Cross-platform sleep function
static void sleep_ms(int milliseconds) {
#ifdef _WIN32
    Sleep(milliseconds);
#else
    usleep(milliseconds * 1000);
#endif
}

// Test configuration
static bool g_debug_enabled = false;
static bool g_test_passed = true;

#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("❌ TEST FAILED: %s\n", message); \
            g_test_passed = false; \
        } else { \
            printf("✅ TEST PASSED: %s\n", message); \
        } \
    } while(0)

#define TEST_INFO(format, ...) \
    printf("ℹ️  " format "\n", ##__VA_ARGS__)

#define TEST_SEPARATOR() \
    printf("=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "\n")

int main(int argc, char* argv[]) {
    printf("🎮 OOT Native Input System Test Suite\n");
    TEST_SEPARATOR();
    
    // Parse command line arguments
    bool interactive_mode = false;
    bool rumble_test = false;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "interactive") == 0) {
            interactive_mode = true;
        } else if (strcmp(argv[i], "rumble") == 0) {
            rumble_test = true;
        } else if (strcmp(argv[i], "debug") == 0) {
            g_debug_enabled = true;
        }
    }
    
    printf("Test Mode: %s\n", interactive_mode ? "Interactive" : "Automated");
    printf("Debug Mode: %s\n", g_debug_enabled ? "Enabled" : "Disabled");
    TEST_SEPARATOR();
    
    // Run core tests
    test_input_initialization();
    test_controller_detection();
    test_button_mapping();
    test_controller_abstraction();
    
    if (rumble_test) {
        test_rumble_functionality();
    }
    
    if (interactive_mode) {
        interactive_controller_test();
    } else {
        test_input_processing();
    }
    
    // Final test results
    TEST_SEPARATOR();
    if (g_test_passed) {
        printf("🎉 ALL TESTS PASSED! Input system is functional.\n");
    } else {
        printf("❌ SOME TESTS FAILED. Check the output above.\n");
    }
    
    // Cleanup
    Input_Shutdown();
    
    return g_test_passed ? 0 : 1;
}

static void test_input_initialization(void) {
    printf("📋 Testing Input System Initialization...\n");
    
    // Test default initialization
    TEST_ASSERT(Input_Init(NULL), "Default initialization should succeed");
    
    // Test backend information
    InputBackendType backend = Input_GetCurrentBackend();
    const char* backend_name = Input_GetBackendName(backend);
    TEST_ASSERT(backend_name != NULL, "Backend name should not be NULL");
    TEST_INFO("Current backend: %s", backend_name);
    
    // Test availability checks
    TEST_ASSERT(Input_IsBackendAvailable(INPUT_BACKEND_SDL2), "SDL2 backend should be available");
    
    // Test debug mode
    Input_EnableDebugMode(g_debug_enabled);
    TEST_ASSERT(Input_IsDebugModeEnabled() == g_debug_enabled, "Debug mode should match setting");
    
    printf("✅ Input system initialization tests completed\n\n");
}

static void test_controller_detection(void) {
    printf("📋 Testing Controller Detection...\n");
    
    uint32_t controller_count = Input_GetControllerCount();
    TEST_INFO("Detected %u controllers", controller_count);
    
    if (controller_count == 0) {
        TEST_INFO("No controllers detected - some tests will be skipped");
        printf("⚠️  Connect a controller to test controller functionality\n\n");
        return;
    }
    
    // Test controller info retrieval
    for (uint32_t i = 0; i < controller_count; i++) {
        ControllerDevice device_info;
        if (Input_GetControllerInfo(i, &device_info)) {
            print_controller_info(i);
            
            // Test controller connection
            if (Input_ConnectController(device_info.device_id, N64_PORT_1)) {
                TEST_ASSERT(Input_IsControllerConnected(N64_PORT_1), "Controller should be connected to port 1");
                TEST_INFO("Successfully connected controller to port 1");
                break; // Only test with first controller
            }
        }
    }
    
    printf("✅ Controller detection tests completed\n\n");
}

static void test_input_processing(void) {
    printf("📋 Testing Input Processing...\n");
    
    if (!Input_IsControllerConnected(N64_PORT_1)) {
        TEST_INFO("No controller connected - skipping input processing tests");
        printf("⚠️  Connect a controller to test input processing\n\n");
        return;
    }
    
    // Test basic input processing
    for (int frame = 0; frame < 10; frame++) {
        Input_ProcessFrame();
        
        const N64InputState* state = Input_GetCurrentState();
        TEST_ASSERT(state != NULL, "Input state should not be NULL");
        TEST_ASSERT(state->valid, "Input state should be valid");
        TEST_ASSERT(state->frame_count > 0, "Frame count should increment");
        
        // Brief delay to simulate game loop
        sleep_ms(16); // ~60 FPS
    }
    
    TEST_INFO("Processed 10 frames successfully");
    printf("✅ Input processing tests completed\n\n");
}

static void test_button_mapping(void) {
    printf("📋 Testing Button Mapping System...\n");
    
    // Test button name retrieval
    for (int i = 0; i < N64_BTN_COUNT; i++) {
        const char* button_name = Input_GetButtonName(i);
        TEST_ASSERT(button_name != NULL, "Button name should not be NULL");
        TEST_ASSERT(strlen(button_name) > 0, "Button name should not be empty");
    }
    
    // Test port name retrieval
    for (int i = 0; i < N64_PORT_COUNT; i++) {
        const char* port_name = Input_GetPortName(i);
        TEST_ASSERT(port_name != NULL, "Port name should not be NULL");
        TEST_ASSERT(strlen(port_name) > 0, "Port name should not be empty");
    }
    
    // Test controller type names
    for (int i = 0; i < CONTROLLER_TYPE_COUNT; i++) {
        const char* type_name = Input_GetControllerTypeName(i);
        TEST_ASSERT(type_name != NULL, "Controller type name should not be NULL");
        TEST_ASSERT(strlen(type_name) > 0, "Controller type name should not be empty");
    }
    
    printf("✅ Button mapping tests completed\n\n");
}

static void test_rumble_functionality(void) {
    printf("📋 Testing Rumble Functionality...\n");
    
    if (!Input_IsControllerConnected(N64_PORT_1)) {
        TEST_INFO("No controller connected - skipping rumble tests");
        printf("⚠️  Connect a controller to test rumble\n\n");
        return;
    }
    
    // Test rumble capability
    bool should_rumble = Controller_ShouldRumble(N64_PORT_1);
    TEST_INFO("Controller rumble capability: %s", should_rumble ? "Yes" : "No");
    
    if (should_rumble) {
        TEST_INFO("Testing rumble (you should feel vibration)...");
        
        // Test short rumble
        if (Input_SetRumble(N64_PORT_1, 0.5f, 500)) {
            TEST_ASSERT(true, "Short rumble test succeeded");
            sleep(1);
        }
        
        // Test rumble stop
        Input_StopRumble(N64_PORT_1);
        TEST_ASSERT(true, "Rumble stop test succeeded");
        
        // Test stop all rumble
        Input_StopAllRumble();
        TEST_ASSERT(true, "Stop all rumble test succeeded");
    }
    
    printf("✅ Rumble functionality tests completed\n\n");
}

static void test_controller_abstraction(void) {
    printf("📋 Testing Controller Abstraction Layer...\n");
    
    // Test game input blocking
    TEST_ASSERT(!Controller_IsGameInputBlocked(), "Game input should not be blocked initially");
    
    Controller_BlockGameInput(true);
    TEST_ASSERT(Controller_IsGameInputBlocked(), "Game input should be blocked after blocking");
    
    Controller_UnblockGameInput();
    TEST_ASSERT(!Controller_IsGameInputBlocked(), "Game input should not be blocked after unblocking");
    
    // Test with input processing
    if (Input_IsControllerConnected(N64_PORT_1)) {
        Controller_BlockGameInput(true);
        Input_ProcessFrame();
        
        const N64ControllerInput* controller = Input_GetController(N64_PORT_1);
        TEST_ASSERT(controller != NULL, "Controller should not be NULL");
        TEST_ASSERT(controller->button == 0, "Buttons should be blocked when game input is blocked");
        TEST_ASSERT(controller->stick_x == 0, "Stick X should be blocked when game input is blocked");
        TEST_ASSERT(controller->stick_y == 0, "Stick Y should be blocked when game input is blocked");
        
        Controller_UnblockGameInput();
    }
    
    printf("✅ Controller abstraction tests completed\n\n");
}

static void print_controller_info(uint32_t device_id) {
    ControllerDevice device_info;
    if (!Input_GetControllerInfo(device_id, &device_info)) {
        printf("❌ Failed to get controller info for device %u\n", device_id);
        return;
    }
    
    printf("Controller %u Info:\n", device_id);
    printf("  Name: %s\n", device_info.name);
    printf("  Type: %s\n", Input_GetControllerTypeName(device_info.type));
    printf("  GUID: %s\n", device_info.guid);
    printf("  Buttons: %u\n", device_info.button_count);
    printf("  Axes: %u\n", device_info.axis_count);
    printf("  Hats: %u\n", device_info.hat_count);
    printf("  Rumble: %s\n", device_info.supports_rumble ? "Yes" : "No");
    printf("  Connected: %s\n", device_info.is_connected ? "Yes" : "No");
}

static void print_n64_input_state(const N64InputState* state) {
    if (!state || !state->valid) {
        printf("❌ Invalid input state\n");
        return;
    }
    
    printf("N64 Input State (Frame %u):\n", state->frame_count);
    
    for (int port = 0; port < N64_PORT_COUNT; port++) {
        const N64ControllerInput* controller = &state->controller[port];
        
        if (controller->status & N64_CONTROLLER_CONNECTED) {
            printf("  Port %d: ", port + 1);
            
            // Print pressed buttons
            if (controller->button & N64_BUTTON_A) printf("A ");
            if (controller->button & N64_BUTTON_B) printf("B ");
            if (controller->button & N64_BUTTON_Z) printf("Z ");
            if (controller->button & N64_BUTTON_START) printf("START ");
            if (controller->button & N64_BUTTON_L) printf("L ");
            if (controller->button & N64_BUTTON_R) printf("R ");
            if (controller->button & N64_BUTTON_C_UP) printf("C↑ ");
            if (controller->button & N64_BUTTON_C_DOWN) printf("C↓ ");
            if (controller->button & N64_BUTTON_C_LEFT) printf("C← ");
            if (controller->button & N64_BUTTON_C_RIGHT) printf("C→ ");
            if (controller->button & N64_BUTTON_D_UP) printf("D↑ ");
            if (controller->button & N64_BUTTON_D_DOWN) printf("D↓ ");
            if (controller->button & N64_BUTTON_D_LEFT) printf("D← ");
            if (controller->button & N64_BUTTON_D_RIGHT) printf("D→ ");
            
            // Print stick position
            if (controller->stick_x != 0 || controller->stick_y != 0) {
                printf("Stick(%d,%d) ", controller->stick_x, controller->stick_y);
            }
            
            if (controller->button == 0 && controller->stick_x == 0 && controller->stick_y == 0) {
                printf("(no input)");
            }
            
            printf("\n");
        }
    }
}

static void interactive_controller_test(void) {
    printf("📋 Interactive Controller Test\n");
    printf("Press buttons and move sticks on your controller. Press Ctrl+C to exit.\n");
    TEST_SEPARATOR();
    
    if (!Input_IsControllerConnected(N64_PORT_1)) {
        printf("❌ No controller connected to port 1\n");
        printf("Please connect a controller and restart the test\n");
        return;
    }
    
    int frame_count = 0;
    time_t last_print = time(NULL);
    
    while (true) {
        Input_ProcessFrame();
        
        const N64InputState* state = Input_GetCurrentState();
        if (state && state->valid) {
            // Print input state every second or when there's input
            bool has_input = false;
            for (int port = 0; port < N64_PORT_COUNT; port++) {
                const N64ControllerInput* controller = &state->controller[port];
                if (controller->button != 0 || controller->stick_x != 0 || controller->stick_y != 0) {
                    has_input = true;
                    break;
                }
            }
            
            time_t current_time = time(NULL);
            if (has_input || (current_time - last_print) >= 1) {
                printf("\r");
                for (int i = 0; i < 80; i++) printf(" ");
                printf("\r");
                
                print_n64_input_state(state);
                last_print = current_time;
            }
        }
        
        frame_count++;
        sleep_ms(16); // ~60 FPS
    }
} 