#include "libultra/libultra_compat.h"
#include <pthread.h>
#include <signal.h>
#include <sys/time.h>
#include <unistd.h>

/* ================================================================================================
 * EVENT SYSTEM AND INTERRUPT MANAGEMENT IMPLEMENTATION
 * 
 * Handles N64 event system and interrupt management in a modern environment.
 * Events are simulated using timers and signals where appropriate.
 * ================================================================================================ */

// External function from message_system.c
extern void osEventMesg_Send(OSEvent event);

// Interrupt mask state
static u32 current_interrupt_mask = 0xFFFFFFFF;
static pthread_mutex_t interrupt_mutex = PTHREAD_MUTEX_INITIALIZER;

// VI (Video Interface) event handling
static OSMesgQueue* vi_event_queue = NULL;
static OSMesg vi_event_message = NULL;
static u32 vi_retrace_count = 0;
static bool vi_event_enabled = false;
static pthread_t vi_thread;
static bool vi_thread_running = false;

// Timer for VI events (60 FPS)
static struct itimerval vi_timer;

// ================================================================================================
// Interrupt Management Functions
// ================================================================================================

// osDisableInt - Disable interrupts (returns previous mask)
u32 osDisableInt(void) {
    pthread_mutex_lock(&interrupt_mutex);
    u32 previous_mask = current_interrupt_mask;
    current_interrupt_mask = 0; // Disable all interrupts
    pthread_mutex_unlock(&interrupt_mutex);
    return previous_mask;
}

// osRestoreInt - Restore interrupt mask
void osRestoreInt(u32 mask) {
    pthread_mutex_lock(&interrupt_mutex);
    current_interrupt_mask = mask;
    pthread_mutex_unlock(&interrupt_mutex);
}

// osSetIntMask - Set interrupt mask
void osSetIntMask(u32 mask) {
    pthread_mutex_lock(&interrupt_mutex);
    current_interrupt_mask = mask;
    pthread_mutex_unlock(&interrupt_mutex);
}

// Check if interrupts are enabled for a specific event
static bool are_interrupts_enabled(OSEvent event) {
    pthread_mutex_lock(&interrupt_mutex);
    bool enabled = (current_interrupt_mask & (1 << event)) != 0;
    pthread_mutex_unlock(&interrupt_mutex);
    return enabled;
}

// ================================================================================================
// VI (Video Interface) Event System
// ================================================================================================

// VI thread function - generates V-sync events
static void* vi_event_thread(void* arg) {
    (void)arg; // Suppress unused parameter warning
    
    while (vi_thread_running) {
        // Sleep for 1/60th of a second (16.67ms)
        usleep(16667); // 16.667 milliseconds
        
        if (vi_event_enabled && vi_event_queue != NULL) {
            // Check if VI interrupts are enabled
            if (are_interrupts_enabled(OS_EVENT_VI)) {
                // Send VI event message
                osSendMesg(vi_event_queue, vi_event_message, OS_MESG_NOBLOCK);
                
                // Also send to global event system
                osEventMesg_Send(OS_EVENT_VI);
            }
        }
    }
    
    return NULL;
}

// osViSetEvent - Set up VI event notification
void osViSetEvent(OSMesgQueue* mq, OSMesg msg, u32 retraceCount) {
    vi_event_queue = mq;
    vi_event_message = msg;
    vi_retrace_count = retraceCount;
    vi_event_enabled = (mq != NULL);
    
    // Start VI thread if not already running
    if (vi_event_enabled && !vi_thread_running) {
        vi_thread_running = true;
        if (pthread_create(&vi_thread, NULL, vi_event_thread, NULL) != 0) {
            vi_thread_running = false;
            vi_event_enabled = false;
        }
    }
}

// ================================================================================================
// Other Hardware Event Simulation
// ================================================================================================

// Signal handler for timer-based events
static void timer_signal_handler(int sig) {
    if (sig == SIGALRM) {
        // Timer interrupt occurred
        if (are_interrupts_enabled(OS_EVENT_COUNTER)) {
            osEventMesg_Send(OS_EVENT_COUNTER);
        }
    }
}

// AI (Audio Interface) event simulation
static pthread_t ai_thread;
static bool ai_thread_running = false;
static OSMesgQueue* ai_event_queue = NULL;
static OSMesg ai_event_message = NULL;

static void* ai_event_thread(void* arg) {
    (void)arg; // Suppress unused parameter warning
    
    while (ai_thread_running) {
        // Audio buffer processing simulation (varies based on sample rate)
        usleep(5333); // ~187.5 Hz for audio events
        
        if (ai_event_queue != NULL && are_interrupts_enabled(OS_EVENT_AI)) {
            osSendMesg(ai_event_queue, ai_event_message, OS_MESG_NOBLOCK);
            osEventMesg_Send(OS_EVENT_AI);
        }
    }
    
    return NULL;
}

// ================================================================================================
// System Event Functions
// ================================================================================================

// Initialize the event system
static bool event_system_initialized = false;

void osEventSystem_Initialize(void) {
    if (event_system_initialized) {
        return;
    }
    
    // Set up signal handler for timer events
    signal(SIGALRM, timer_signal_handler);
    
    // Initialize interrupt mask (all enabled)
    current_interrupt_mask = 0xFFFFFFFF;
    
    event_system_initialized = true;
}

// Shutdown the event system
void osEventSystem_Shutdown(void) {
    if (!event_system_initialized) {
        return;
    }
    
    // Stop VI thread
    if (vi_thread_running) {
        vi_thread_running = false;
        pthread_join(vi_thread, NULL);
    }
    
    // Stop AI thread
    if (ai_thread_running) {
        ai_thread_running = false;
        pthread_join(ai_thread, NULL);
    }
    
    event_system_initialized = false;
}

// ================================================================================================
// Hardware-Specific Event Functions
// ================================================================================================

// Simulate SP (Signal Processor) events
void osEventSP_Done(void) {
    if (are_interrupts_enabled(OS_EVENT_SP)) {
        osEventMesg_Send(OS_EVENT_SP);
    }
}

// Simulate DP (Display Processor) events
void osEventDP_Done(void) {
    if (are_interrupts_enabled(OS_EVENT_DP)) {
        osEventMesg_Send(OS_EVENT_DP);
    }
}

// Simulate PI (Peripheral Interface) events
void osEventPI_Done(void) {
    if (are_interrupts_enabled(OS_EVENT_PI)) {
        osEventMesg_Send(OS_EVENT_PI);
    }
}

// Simulate SI (Serial Interface) events (controller)
void osEventSI_Done(void) {
    if (are_interrupts_enabled(OS_EVENT_SI)) {
        osEventMesg_Send(OS_EVENT_SI);
    }
}

// ================================================================================================
// Software Event Generation
// ================================================================================================

// Generate software interrupt 1
void osEventSW1_Generate(void) {
    if (are_interrupts_enabled(OS_EVENT_SW1)) {
        osEventMesg_Send(OS_EVENT_SW1);
    }
}

// Generate software interrupt 2
void osEventSW2_Generate(void) {
    if (are_interrupts_enabled(OS_EVENT_SW2)) {
        osEventMesg_Send(OS_EVENT_SW2);
    }
}

// Generate cartridge interrupt
void osEventCart_Generate(void) {
    if (are_interrupts_enabled(OS_EVENT_CART)) {
        osEventMesg_Send(OS_EVENT_CART);
    }
}

// Generate fault event
void osEventFault_Generate(void) {
    if (are_interrupts_enabled(OS_EVENT_FAULT)) {
        osEventMesg_Send(OS_EVENT_FAULT);
    }
}

// Generate pre-NMI event
void osEventPreNMI_Generate(void) {
    if (are_interrupts_enabled(OS_EVENT_PRENMI)) {
        osEventMesg_Send(OS_EVENT_PRENMI);
    }
}

// ================================================================================================
// Event System Status Functions
// ================================================================================================

// Check if a specific event type is enabled
bool osIsEventEnabled(OSEvent event) {
    return are_interrupts_enabled(event);
}

// Get current interrupt mask
u32 osGetIntMask(void) {
    pthread_mutex_lock(&interrupt_mutex);
    u32 mask = current_interrupt_mask;
    pthread_mutex_unlock(&interrupt_mutex);
    return mask;
}

// Enable specific event
void osEnableEvent(OSEvent event) {
    if (event >= OS_NUM_EVENTS) {
        return;
    }
    
    pthread_mutex_lock(&interrupt_mutex);
    current_interrupt_mask |= (1 << event);
    pthread_mutex_unlock(&interrupt_mutex);
}

// Disable specific event
void osDisableEvent(OSEvent event) {
    if (event >= OS_NUM_EVENTS) {
        return;
    }
    
    pthread_mutex_lock(&interrupt_mutex);
    current_interrupt_mask &= ~(1 << event);
    pthread_mutex_unlock(&interrupt_mutex);
}

// ================================================================================================
// AI Event Setup Functions
// ================================================================================================

// Set up AI event notification
void osAiSetEvent(OSMesgQueue* mq, OSMesg msg) {
    ai_event_queue = mq;
    ai_event_message = msg;
    
    // Start AI thread if not already running and we have a queue
    if (mq != NULL && !ai_thread_running) {
        ai_thread_running = true;
        if (pthread_create(&ai_thread, NULL, ai_event_thread, NULL) != 0) {
            ai_thread_running = false;
        }
    } else if (mq == NULL && ai_thread_running) {
        // Stop AI thread if queue is being cleared
        ai_thread_running = false;
        pthread_join(ai_thread, NULL);
    }
} 