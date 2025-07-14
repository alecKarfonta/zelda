#include "libultra/libultra_compat.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ================================================================================================
 * LIBULTRA SYSTEM INITIALIZATION AND COORDINATION
 * 
 * Main entry point for the libultra compatibility layer. Handles initialization and
 * shutdown of all subsystems.
 * ================================================================================================ */

// System initialization state
static bool libultra_initialized = false;
static pthread_mutex_t system_mutex = PTHREAD_MUTEX_INITIALIZER;

// External initialization functions
extern void osEventSystem_Initialize(void);
extern void osEventSystem_Shutdown(void);
extern void osTimingSystem_Shutdown(void);

// ================================================================================================
// Main System Functions
// ================================================================================================

// LibultraCompat_Initialize - Initialize the entire libultra compatibility layer
void LibultraCompat_Initialize(void) {
    pthread_mutex_lock(&system_mutex);
    
    if (libultra_initialized) {
        pthread_mutex_unlock(&system_mutex);
        return; // Already initialized
    }
    
    // Initialize all subsystems
    osEventSystem_Initialize();
    
    libultra_initialized = true;
    pthread_mutex_unlock(&system_mutex);
}

// LibultraCompat_Shutdown - Clean up the entire libultra compatibility layer
void LibultraCompat_Shutdown(void) {
    pthread_mutex_lock(&system_mutex);
    
    if (!libultra_initialized) {
        pthread_mutex_unlock(&system_mutex);
        return; // Not initialized
    }
    
    // Shutdown all subsystems
    osEventSystem_Shutdown();
    osTimingSystem_Shutdown();
    
    libultra_initialized = false;
    pthread_mutex_unlock(&system_mutex);
}

// ================================================================================================
// N64 System Initialization Functions
// ================================================================================================

// osInitialize - Main N64 system initialization
void osInitialize(void) {
    LibultraCompat_Initialize();
}

// __osInitialize_common - Common initialization
void __osInitialize_common(void) {
    LibultraCompat_Initialize();
}

// __osInitialize_autodetect - Auto-detection initialization
void __osInitialize_autodetect(void) {
    LibultraCompat_Initialize();
}

// ================================================================================================
// Math Functions (for compatibility with N64 libultra)
// ================================================================================================

// sinf - Sine function (using standard library)
f32 sinf(f32 x) {
    return (f32)sin((double)x);
}

// cosf - Cosine function (using standard library)
f32 cosf(f32 x) {
    return (f32)cos((double)x);
}

// sqrtf - Square root function (using standard library)
f32 sqrtf(f32 x) {
    return (f32)sqrt((double)x);
}

// ================================================================================================
// Controller/Input Stub Functions
// ================================================================================================

// osContInit - Initialize controllers
s32 osContInit(OSMesgQueue* mq, u8* bitpattern, OSContStatus* data) {
    // Stub implementation - assume 1 controller connected
    if (bitpattern) *bitpattern = 0x01; // Controller 0 connected
    
    if (data) {
        data[0].type = 0x0500; // Standard N64 controller
        data[0].status = 0x01; // Connected
        data[0].errno = 0;     // No error
        
        // Clear other controller slots
        for (int i = 1; i < MAXCONTROLLERS; i++) {
            data[i].type = 0;
            data[i].status = 0;
            data[i].errno = 0;
        }
    }
    
    return 0; // Success
}

// osContStartReadData - Start reading controller data
s32 osContStartReadData(OSMesgQueue* mq) {
    // Stub implementation - immediately signal completion
    if (mq) {
        osSendMesg(mq, NULL, OS_MESG_NOBLOCK);
    }
    return 0;
}

// osContGetReadData - Get controller data
void osContGetReadData(OSContPad* data) {
    // Stub implementation - return neutral controller state
    if (data) {
        for (int i = 0; i < MAXCONTROLLERS; i++) {
            data[i].button = 0;    // No buttons pressed
            data[i].stick_x = 0;   // Centered analog stick
            data[i].stick_y = 0;   // Centered analog stick
            data[i].errno = 0;     // No error
        }
    }
}

// osContSetCh - Set controller channel
s32 osContSetCh(u8 ch) {
    // Stub implementation - always succeed
    (void)ch; // Suppress unused parameter warning
    return 0;
}

// ================================================================================================
// Video Interface Stub Functions
// ================================================================================================

// osViSetMode - Set video mode
void osViSetMode(OSViMode* mode) {
    // Stub implementation
    (void)mode; // Suppress unused parameter warning
}

// osViSetSpecialFeatures - Set special video features
void osViSetSpecialFeatures(u32 func) {
    // Stub implementation
    (void)func; // Suppress unused parameter warning
}

// osViSwapBuffer - Swap video buffers
void osViSwapBuffer(void* framebuffer) {
    // Stub implementation
    (void)framebuffer; // Suppress unused parameter warning
}

// osViBlack - Black out screen
void osViBlack(u8 active) {
    // Stub implementation
    (void)active; // Suppress unused parameter warning
}

// osViRepeatLine - Set line repeat mode
void osViRepeatLine(u8 active) {
    // Stub implementation
    (void)active; // Suppress unused parameter warning
}

// osViSetXScale - Set horizontal scale
void osViSetXScale(f32 scale) {
    // Stub implementation
    (void)scale; // Suppress unused parameter warning
}

// osViSetYScale - Set vertical scale
void osViSetYScale(f32 scale) {
    // Stub implementation
    (void)scale; // Suppress unused parameter warning
}

// osViGetCurrentFramebuffer - Get current framebuffer
u32* osViGetCurrentFramebuffer(void) {
    return NULL; // Stub implementation
}

// osViGetNextFramebuffer - Get next framebuffer
u32* osViGetNextFramebuffer(void) {
    return NULL; // Stub implementation
}

// ================================================================================================
// Audio Interface Stub Functions
// ================================================================================================

// osAiSetFrequency - Set audio frequency
s32 osAiSetFrequency(u32 frequency) {
    // Stub implementation - always succeed
    (void)frequency; // Suppress unused parameter warning
    return 0;
}

// osAiSetNextBuffer - Set next audio buffer
s32 osAiSetNextBuffer(void* buffer, u32 size) {
    // Stub implementation - always succeed
    (void)buffer; // Suppress unused parameter warning
    (void)size;   // Suppress unused parameter warning
    return 0;
}

// osAiGetLength - Get audio buffer length
u32 osAiGetLength(void) {
    return 0; // Stub implementation
}

// osAiGetStatus - Get audio status
u32 osAiGetStatus(void) {
    return 0; // Stub implementation - not busy
}

// ================================================================================================
// System Status Functions
// ================================================================================================

// Check if libultra compatibility layer is initialized
bool LibultraCompat_IsInitialized(void) {
    pthread_mutex_lock(&system_mutex);
    bool initialized = libultra_initialized;
    pthread_mutex_unlock(&system_mutex);
    return initialized;
}

// Get version information
const char* LibultraCompat_GetVersion(void) {
    return "OOT Native LibUltra Compatibility Layer v1.0";
}

// Get system information
typedef struct {
    bool timing_system_active;
    bool event_system_active;
    s32 active_thread_count;
    u32 memory_usage;
} LibultraSystemInfo;

void LibultraCompat_GetSystemInfo(LibultraSystemInfo* info) {
    if (info == NULL) {
        return;
    }
    
    memset(info, 0, sizeof(LibultraSystemInfo));
    
    if (libultra_initialized) {
        info->timing_system_active = true;
        info->event_system_active = true;
        // Additional system info could be populated here
    }
}

// ================================================================================================
// osCartRomInit - Initialize cartridge ROM access
// ================================================================================================
OSPiHandle* osCartRomInit(void) {
    static OSPiHandle cart_handle = {
        .next = NULL,
        .type = 0,
        .latency = 0,
        .pageSize = 0,
        .relDuration = 0,
        .pulse = 0,
        .domain = 1,
        .baseAddress = 0x10000000,
        .speed = 0,
        .transferModeType = 0
    };
    
    return &cart_handle;
}

// ================================================================================================
// RSP Task Management Functions
// ================================================================================================
static OSTask* current_rsp_task = NULL;
static bool rsp_task_yielded = false;

void osSpTaskLoad(OSTask* task) {
    current_rsp_task = task;
    rsp_task_yielded = false;
}

s32 osSpTaskYielded(OSTask* task) {
    (void)task; // Unused parameter
    return rsp_task_yielded ? 1 : 0;
}

void osSpTaskYield(void) {
    rsp_task_yielded = true;
}

void osSpTaskStartGo(OSTask* task) {
    current_rsp_task = task;
    rsp_task_yielded = false;
    // In a real implementation, this would start RSP execution
    // For compatibility, we just simulate completion
}

// ================================================================================================
// osAfterPreNMI - Check if system is after pre-NMI state
// ================================================================================================
s32 osAfterPreNMI(void) {
    // In modern systems, there's no NMI (Non-Maskable Interrupt) concept
    // Return 0 to indicate normal operation
    return 0;
} 