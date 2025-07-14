#include "libultra/libultra_compat.h"
#include <time.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>

/* ================================================================================================
 * TIMING SYSTEM IMPLEMENTATION
 * 
 * Provides N64-compatible timing functions using modern high-resolution clocks.
 * Maintains cycle-accurate timing where possible while adapting to modern hardware.
 * ================================================================================================ */

// N64 had a 93.75 MHz CPU clock, we'll simulate this for compatibility
#define N64_CPU_FREQUENCY 93750000ULL
#define NANOSECONDS_PER_SECOND 1000000000ULL

// System timing state
static struct timespec system_start_time;
static OSTime base_time = 0;
static bool timing_initialized = false;
static pthread_mutex_t timing_mutex = PTHREAD_MUTEX_INITIALIZER;

// Timer management
static OSTimer* active_timers = NULL;
static pthread_mutex_t timer_mutex = PTHREAD_MUTEX_INITIALIZER;

// ================================================================================================
// Internal Helper Functions
// ================================================================================================

// Initialize timing system
static void init_timing_system(void) {
    if (!timing_initialized) {
        pthread_mutex_lock(&timing_mutex);
        if (!timing_initialized) {
            clock_gettime(CLOCK_MONOTONIC, &system_start_time);
            base_time = 0;
            timing_initialized = true;
        }
        pthread_mutex_unlock(&timing_mutex);
    }
}

// Convert timespec to N64 time units (simulated CPU cycles)
static OSTime timespec_to_os_time(const struct timespec* ts) {
    OSTime nanoseconds = (OSTime)ts->tv_sec * NANOSECONDS_PER_SECOND + ts->tv_nsec;
    // Convert nanoseconds to simulated N64 CPU cycles
    return (nanoseconds * N64_CPU_FREQUENCY) / NANOSECONDS_PER_SECOND;
}

// Convert N64 time units to milliseconds for modern timing
static u32 os_time_to_milliseconds(OSTime os_time) {
    // Convert simulated N64 cycles back to nanoseconds, then to milliseconds
    u64 nanoseconds = (os_time * NANOSECONDS_PER_SECOND) / N64_CPU_FREQUENCY;
    return (u32)(nanoseconds / 1000000);
}

// Timer thread function
static void* timer_thread_func(void* arg) {
    OSTimer* timer = (OSTimer*)arg;
    
    pthread_mutex_lock(&timer->timer_mutex);
    
    while (timer->active) {
        // Calculate sleep time in milliseconds
        u32 sleep_ms = os_time_to_milliseconds(timer->interval);
        
        pthread_mutex_unlock(&timer->timer_mutex);
        
        // Sleep for the interval
        if (sleep_ms > 0) {
            usleep(sleep_ms * 1000); // usleep takes microseconds
        } else {
            usleep(1000); // Minimum 1ms sleep
        }
        
        pthread_mutex_lock(&timer->timer_mutex);
        
        if (timer->active && timer->mq != NULL) {
            // Send timer message
            osSendMesg(timer->mq, timer->msg, OS_MESG_NOBLOCK);
            
            // Update timer value
            timer->value += timer->interval;
            
            // For one-shot timers, deactivate after first fire
            if (timer->interval == 0) {
                timer->active = false;
            }
        }
    }
    
    pthread_mutex_unlock(&timer->timer_mutex);
    return NULL;
}

// ================================================================================================
// osGetTime - Get current system time
// ================================================================================================
OSTime osGetTime(void) {
    init_timing_system();
    
    struct timespec current_time;
    clock_gettime(CLOCK_MONOTONIC, &current_time);
    
    // Calculate elapsed time since system start
    struct timespec elapsed;
    elapsed.tv_sec = current_time.tv_sec - system_start_time.tv_sec;
    elapsed.tv_nsec = current_time.tv_nsec - system_start_time.tv_nsec;
    
    // Handle nanosecond underflow
    if (elapsed.tv_nsec < 0) {
        elapsed.tv_sec--;
        elapsed.tv_nsec += NANOSECONDS_PER_SECOND;
    }
    
    pthread_mutex_lock(&timing_mutex);
    OSTime os_time = base_time + timespec_to_os_time(&elapsed);
    pthread_mutex_unlock(&timing_mutex);
    
    return os_time;
}

// ================================================================================================
// osSetTime - Set system time base
// ================================================================================================
void osSetTime(OSTime time) {
    init_timing_system();
    
    pthread_mutex_lock(&timing_mutex);
    
    // Update the base time and reset the start time
    base_time = time;
    clock_gettime(CLOCK_MONOTONIC, &system_start_time);
    
    pthread_mutex_unlock(&timing_mutex);
}

// ================================================================================================
// osGetCount - Get CPU cycle count (high-resolution counter)
// ================================================================================================
u32 osGetCount(void) {
    // Return lower 32 bits of the high-resolution time
    OSTime full_time = osGetTime();
    return (u32)(full_time & 0xFFFFFFFF);
}

// ================================================================================================
// osSetTimer - Set up a timer
// ================================================================================================
void osSetTimer(OSTimer* timer, OSTime countdown, OSTime interval, OSMesgQueue* mq, OSMesg msg) {
    if (timer == NULL) {
        return;
    }
    
    // Stop timer if it's already active
    osStopTimer(timer);
    
    // Initialize timer structure
    pthread_mutex_lock(&timer_mutex);
    
    timer->next = active_timers;
    timer->prev = NULL;
    if (active_timers) {
        active_timers->prev = timer;
    }
    active_timers = timer;
    
    timer->interval = interval;
    timer->value = countdown;
    timer->mq = mq;
    timer->msg = msg;
    timer->active = true;
    
    pthread_mutex_unlock(&timer_mutex);
    
    // Initialize timer mutex
    if (pthread_mutex_init(&timer->timer_mutex, NULL) != 0) {
        timer->active = false;
        return;
    }
    
    // Create timer thread
    if (pthread_create(&timer->timer_thread, NULL, timer_thread_func, timer) != 0) {
        pthread_mutex_destroy(&timer->timer_mutex);
        timer->active = false;
        return;
    }
}

// ================================================================================================
// osStopTimer - Stop a timer
// ================================================================================================
void osStopTimer(OSTimer* timer) {
    if (timer == NULL || !timer->active) {
        return;
    }
    
    pthread_mutex_lock(&timer->timer_mutex);
    timer->active = false;
    pthread_mutex_unlock(&timer->timer_mutex);
    
    // Wait for timer thread to finish
    if (timer->timer_thread != 0) {
        pthread_join(timer->timer_thread, NULL);
        timer->timer_thread = 0;
    }
    
    // Clean up mutex
    pthread_mutex_destroy(&timer->timer_mutex);
    
    // Remove from active timer list
    pthread_mutex_lock(&timer_mutex);
    
    if (timer->prev) {
        timer->prev->next = timer->next;
    } else {
        active_timers = timer->next;
    }
    
    if (timer->next) {
        timer->next->prev = timer->prev;
    }
    
    timer->next = NULL;
    timer->prev = NULL;
    
    pthread_mutex_unlock(&timer_mutex);
}

// ================================================================================================
// Extended Timing Functions
// ================================================================================================

// Get high-resolution timestamp in nanoseconds
u64 osGetTimeNanoseconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u64)ts.tv_sec * NANOSECONDS_PER_SECOND + ts.tv_nsec;
}

// Get timestamp in milliseconds
u64 osGetTimeMilliseconds(void) {
    return osGetTimeNanoseconds() / 1000000;
}

// Get timestamp in microseconds
u64 osGetTimeMicroseconds(void) {
    return osGetTimeNanoseconds() / 1000;
}

// Sleep for specified time in OS time units
void osSleep(OSTime time) {
    u32 sleep_ms = os_time_to_milliseconds(time);
    if (sleep_ms > 0) {
        usleep(sleep_ms * 1000);
    }
}

// Sleep for specified milliseconds
void osSleepMs(u32 milliseconds) {
    if (milliseconds > 0) {
        usleep(milliseconds * 1000);
    }
}

// Sleep for specified microseconds
void osSleepUs(u32 microseconds) {
    if (microseconds > 0) {
        usleep(microseconds);
    }
}

// ================================================================================================
// Performance Timing Functions
// ================================================================================================

// Performance counter for benchmarking
typedef struct {
    OSTime start_time;
    OSTime total_time;
    u32 sample_count;
    bool running;
} OSPerfCounter;

// Start performance measurement
void osPerfCounterStart(OSPerfCounter* counter) {
    if (counter == NULL) {
        return;
    }
    
    counter->start_time = osGetTime();
    counter->running = true;
}

// Stop performance measurement and accumulate
void osPerfCounterStop(OSPerfCounter* counter) {
    if (counter == NULL || !counter->running) {
        return;
    }
    
    OSTime elapsed = osGetTime() - counter->start_time;
    counter->total_time += elapsed;
    counter->sample_count++;
    counter->running = false;
}

// Get average time per sample
OSTime osPerfCounterGetAverage(OSPerfCounter* counter) {
    if (counter == NULL || counter->sample_count == 0) {
        return 0;
    }
    
    return counter->total_time / counter->sample_count;
}

// Reset performance counter
void osPerfCounterReset(OSPerfCounter* counter) {
    if (counter == NULL) {
        return;
    }
    
    counter->start_time = 0;
    counter->total_time = 0;
    counter->sample_count = 0;
    counter->running = false;
}

// ================================================================================================
// Timing System Cleanup
// ================================================================================================

// Clean up timing system
void osTimingSystem_Shutdown(void) {
    if (!timing_initialized) {
        return;
    }
    
    // Stop all active timers
    pthread_mutex_lock(&timer_mutex);
    OSTimer* current = active_timers;
    while (current) {
        OSTimer* next = current->next;
        osStopTimer(current);
        current = next;
    }
    active_timers = NULL;
    pthread_mutex_unlock(&timer_mutex);
    
    timing_initialized = false;
} 