#include "libultra/libultra_compat.h"
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sched.h>

/* ================================================================================================
 * THREADING SYSTEM IMPLEMENTATION
 * 
 * Provides N64-compatible threading functions using modern pthreads while maintaining
 * the cooperative threading semantics that OOT depends on.
 * ================================================================================================ */

// Global thread management state
static pthread_mutex_t thread_manager_mutex = PTHREAD_MUTEX_INITIALIZER;
static OSThread* active_thread = NULL;
static OSThread* thread_list_head = NULL;
static OSId next_thread_id = 1;
static bool threading_initialized = false;

// Thread-local storage for current thread context
static __thread OSThread* current_thread = NULL;

// ================================================================================================
// Internal Helper Functions
// ================================================================================================

// Initialize threading system
static void init_threading_system(void) {
    if (!threading_initialized) {
        pthread_mutex_lock(&thread_manager_mutex);
        if (!threading_initialized) {
            // Initialize global state
            active_thread = NULL;
            thread_list_head = NULL;
            next_thread_id = 1;
            threading_initialized = true;
        }
        pthread_mutex_unlock(&thread_manager_mutex);
    }
}

// Add thread to global thread list
static void add_to_thread_list(OSThread* thread) {
    pthread_mutex_lock(&thread_manager_mutex);
    thread->tlnext = thread_list_head;
    thread_list_head = thread;
    pthread_mutex_unlock(&thread_manager_mutex);
}

// Remove thread from global thread list
static void remove_from_thread_list(OSThread* thread) {
    pthread_mutex_lock(&thread_manager_mutex);
    if (thread_list_head == thread) {
        thread_list_head = thread->tlnext;
    } else {
        OSThread* current = thread_list_head;
        while (current && current->tlnext != thread) {
            current = current->tlnext;
        }
        if (current) {
            current->tlnext = thread->tlnext;
        }
    }
    pthread_mutex_unlock(&thread_manager_mutex);
}

// Thread wrapper function
static void* thread_wrapper(void* arg) {
    OSThread* thread = (OSThread*)arg;
    current_thread = thread;
    
    pthread_mutex_lock(&thread->state_mutex);
    thread->state = OS_STATE_RUNNING;
    pthread_mutex_unlock(&thread->state_mutex);
    
    // Run the thread entry point
    if (thread->entry_point) {
        thread->entry_point(thread->arg);
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    thread->state = OS_STATE_STOPPED;
    thread->active = false;
    pthread_mutex_unlock(&thread->state_mutex);
    
    return NULL;
}

// ================================================================================================
// osCreateThread - Create a new thread
// ================================================================================================
void osCreateThread(OSThread* thread, OSId id, void (*entry)(void*), void* arg, void* sp, OSPri pri) {
    if (thread == NULL || entry == NULL) {
        return;
    }
    
    init_threading_system();
    
    // Initialize thread structure
    memset(thread, 0, sizeof(OSThread));
    
    pthread_mutex_lock(&thread_manager_mutex);
    thread->id = (id != 0) ? id : next_thread_id++;
    pthread_mutex_unlock(&thread_manager_mutex);
    
    thread->priority = pri;
    thread->entry_point = entry;
    thread->arg = arg;
    thread->stack_pointer = sp; // Not used in modern implementation
    thread->state = OS_STATE_STOPPED;
    thread->flags = 0;
    thread->fp = 0;
    thread->thprof = NULL;
    thread->next = NULL;
    thread->queue = NULL;
    thread->tlnext = NULL;
    thread->active = false;
    
    // Initialize pthread mutex
    if (pthread_mutex_init(&thread->state_mutex, NULL) != 0) {
        return; // Failed to initialize mutex
    }
    
    // Add to global thread list
    add_to_thread_list(thread);
}

// ================================================================================================
// osStartThread - Start a thread
// ================================================================================================
void osStartThread(OSThread* thread) {
    if (thread == NULL) {
        return;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    
    if (thread->state != OS_STATE_STOPPED) {
        pthread_mutex_unlock(&thread->state_mutex);
        return; // Thread already started
    }
    
    thread->state = OS_STATE_RUNNABLE;
    thread->active = true;
    
    // Create the actual pthread
    pthread_attr_t attr;
    pthread_attr_init(&attr);
    
    // Set priority (approximate mapping from N64 to POSIX)
    struct sched_param param;
    param.sched_priority = (thread->priority * 99) / 255; // Map 0-255 to 0-99
    pthread_attr_setschedparam(&attr, &param);
    
    if (pthread_create(&thread->pthread_id, &attr, thread_wrapper, thread) != 0) {
        // Failed to create thread
        thread->state = OS_STATE_STOPPED;
        thread->active = false;
    }
    
    pthread_attr_destroy(&attr);
    pthread_mutex_unlock(&thread->state_mutex);
}

// ================================================================================================
// osStopThread - Stop a thread
// ================================================================================================
void osStopThread(OSThread* thread) {
    if (thread == NULL) {
        return;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    
    if (thread->state == OS_STATE_STOPPED || !thread->active) {
        pthread_mutex_unlock(&thread->state_mutex);
        return; // Thread already stopped
    }
    
    thread->state = OS_STATE_STOPPED;
    thread->active = false;
    
    // Cancel the pthread if it's running
    if (thread->pthread_id != 0) {
        pthread_cancel(thread->pthread_id);
        pthread_join(thread->pthread_id, NULL);
        thread->pthread_id = 0;
    }
    
    pthread_mutex_unlock(&thread->state_mutex);
}

// ================================================================================================
// osDestroyThread - Destroy a thread and clean up resources
// ================================================================================================
void osDestroyThread(OSThread* thread) {
    if (thread == NULL) {
        return;
    }
    
    // Stop the thread first
    osStopThread(thread);
    
    // Remove from thread list
    remove_from_thread_list(thread);
    
    // Clean up mutex
    pthread_mutex_destroy(&thread->state_mutex);
    
    // Clear the structure
    memset(thread, 0, sizeof(OSThread));
}

// ================================================================================================
// osYieldThread - Yield execution to other threads
// ================================================================================================
void osYieldThread(void) {
    // Simple yield - let other threads run
    sched_yield();
    
    // Small sleep to ensure other threads get time
    usleep(1000); // 1ms
}

// ================================================================================================
// Thread Query Functions
// ================================================================================================

// osGetActiveThread - Get currently active thread
OSThread* osGetActiveThread(void) {
    return current_thread;
}

// osGetThreadId - Get thread ID
s32 osGetThreadId(OSThread* thread) {
    if (thread == NULL) {
        return -1;
    }
    return thread->id;
}

// osGetThreadPri - Get thread priority
OSPri osGetThreadPri(OSThread* thread) {
    if (thread == NULL) {
        return -1;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    OSPri priority = thread->priority;
    pthread_mutex_unlock(&thread->state_mutex);
    
    return priority;
}

// osSetThreadPri - Set thread priority
OSPri osSetThreadPri(OSThread* thread, OSPri priority) {
    if (thread == NULL) {
        return -1;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    OSPri old_priority = thread->priority;
    thread->priority = priority;
    
    // Update pthread priority if thread is running
    if (thread->active && thread->pthread_id != 0) {
        struct sched_param param;
        param.sched_priority = (priority * 99) / 255; // Map 0-255 to 0-99
        pthread_setschedparam(thread->pthread_id, SCHED_OTHER, &param);
    }
    
    pthread_mutex_unlock(&thread->state_mutex);
    
    return old_priority;
}

// ================================================================================================
// Advanced Thread Management Functions
// ================================================================================================

// Get thread state
u16 osGetThreadState(OSThread* thread) {
    if (thread == NULL) {
        return 0;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    u16 state = thread->state;
    pthread_mutex_unlock(&thread->state_mutex);
    
    return state;
}

// Check if thread is active
bool osIsThreadActive(OSThread* thread) {
    if (thread == NULL) {
        return false;
    }
    
    pthread_mutex_lock(&thread->state_mutex);
    bool active = thread->active;
    pthread_mutex_unlock(&thread->state_mutex);
    
    return active;
}

// Wait for thread to complete
void osJoinThread(OSThread* thread) {
    if (thread == NULL || !thread->active) {
        return;
    }
    
    if (thread->pthread_id != 0) {
        pthread_join(thread->pthread_id, NULL);
    }
}

// Get number of active threads
s32 osGetActiveThreadCount(void) {
    s32 count = 0;
    
    pthread_mutex_lock(&thread_manager_mutex);
    OSThread* current = thread_list_head;
    while (current) {
        if (current->active) {
            count++;
        }
        current = current->tlnext;
    }
    pthread_mutex_unlock(&thread_manager_mutex);
    
    return count;
} 