#include "libultra/libultra_compat.h"
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

/* ================================================================================================
 * MESSAGE PASSING SYSTEM IMPLEMENTATION
 * 
 * This is the most critical part of the libultra compatibility layer. OOT uses message
 * queues extensively for inter-thread communication and event handling. This implementation
 * maintains N64 semantics while using modern pthread synchronization primitives.
 * ================================================================================================ */

// Global event message registration
static struct {
    OSMesgQueue* queue;
    OSMesg message;
    bool registered;
} event_handlers[OS_NUM_EVENTS];

static pthread_mutex_t event_system_mutex = PTHREAD_MUTEX_INITIALIZER;
static bool event_system_initialized = false;

// ================================================================================================
// Internal Helper Functions
// ================================================================================================

// Initialize the event system
static void init_event_system(void) {
    if (!event_system_initialized) {
        pthread_mutex_lock(&event_system_mutex);
        if (!event_system_initialized) {
            for (int i = 0; i < OS_NUM_EVENTS; i++) {
                event_handlers[i].queue = NULL;
                event_handlers[i].message = NULL;
                event_handlers[i].registered = false;
            }
            event_system_initialized = true;
        }
        pthread_mutex_unlock(&event_system_mutex);
    }
}

// ================================================================================================
// osCreateMesgQueue - Initialize a message queue
// ================================================================================================
void osCreateMesgQueue(OSMesgQueue* mq, OSMesg* msg, s32 count) {
    if (mq == NULL || msg == NULL || count <= 0) {
        return;
    }
    
    // Initialize the basic N64-compatible fields
    mq->mtqueue = NULL;      // Threads waiting to send
    mq->fullqueue = NULL;    // Threads waiting to receive
    mq->validCount = 0;      // Number of messages currently in queue
    mq->first = 0;           // Index of first message
    mq->msgCount = count;    // Maximum number of messages
    mq->msg = msg;           // Message buffer
    
    // Initialize modern synchronization primitives
    if (pthread_mutex_init(&mq->mutex, NULL) != 0) {
        return; // Failed to initialize mutex
    }
    
    if (pthread_cond_init(&mq->send_cond, NULL) != 0) {
        pthread_mutex_destroy(&mq->mutex);
        return; // Failed to initialize condition variable
    }
    
    if (pthread_cond_init(&mq->recv_cond, NULL) != 0) {
        pthread_mutex_destroy(&mq->mutex);
        pthread_cond_destroy(&mq->send_cond);
        return; // Failed to initialize condition variable
    }
    
    mq->initialized = true;
}

// ================================================================================================
// osSendMesg - Send a message to a queue
// ================================================================================================
s32 osSendMesg(OSMesgQueue* mq, OSMesg msg, s32 flag) {
    if (mq == NULL || !mq->initialized) {
        return -1; // Invalid queue
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    // Check if queue is full
    while (mq->validCount >= mq->msgCount) {
        if (flag == OS_MESG_NOBLOCK) {
            pthread_mutex_unlock(&mq->mutex);
            return -1; // Queue full and non-blocking
        }
        
        // Block until space becomes available
        pthread_cond_wait(&mq->send_cond, &mq->mutex);
    }
    
    // Add message to queue
    s32 index = (mq->first + mq->validCount) % mq->msgCount;
    mq->msg[index] = msg;
    mq->validCount++;
    
    // Wake up any threads waiting to receive
    pthread_cond_signal(&mq->recv_cond);
    
    pthread_mutex_unlock(&mq->mutex);
    return 0; // Success
}

// ================================================================================================
// osRecvMesg - Receive a message from a queue
// ================================================================================================
s32 osRecvMesg(OSMesgQueue* mq, OSMesg* msg, s32 flag) {
    if (mq == NULL || !mq->initialized) {
        return -1; // Invalid queue
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    // Check if queue is empty
    while (mq->validCount == 0) {
        if (flag == OS_MESG_NOBLOCK) {
            pthread_mutex_unlock(&mq->mutex);
            return -1; // Queue empty and non-blocking
        }
        
        // Block until message becomes available
        pthread_cond_wait(&mq->recv_cond, &mq->mutex);
    }
    
    // Get message from queue
    if (msg != NULL) {
        *msg = mq->msg[mq->first];
    }
    
    // Update queue state
    mq->first = (mq->first + 1) % mq->msgCount;
    mq->validCount--;
    
    // Wake up any threads waiting to send
    pthread_cond_signal(&mq->send_cond);
    
    pthread_mutex_unlock(&mq->mutex);
    return 0; // Success
}

// ================================================================================================
// osSetEventMesg - Register a message queue for system events
// ================================================================================================
void osSetEventMesg(OSEvent event, OSMesgQueue* mq, OSMesg msg) {
    if (event >= OS_NUM_EVENTS) {
        return; // Invalid event
    }
    
    init_event_system();
    
    pthread_mutex_lock(&event_system_mutex);
    
    event_handlers[event].queue = mq;
    event_handlers[event].message = msg;
    event_handlers[event].registered = (mq != NULL);
    
    pthread_mutex_unlock(&event_system_mutex);
}

// ================================================================================================
// Event System Helper Functions
// ================================================================================================

// Send an event message (internal function for system events)
void osEventMesg_Send(OSEvent event) {
    if (event >= OS_NUM_EVENTS) {
        return;
    }
    
    pthread_mutex_lock(&event_system_mutex);
    
    if (event_handlers[event].registered && event_handlers[event].queue != NULL) {
        // Send the event message (non-blocking)
        osSendMesg(event_handlers[event].queue, event_handlers[event].message, OS_MESG_NOBLOCK);
    }
    
    pthread_mutex_unlock(&event_system_mutex);
}

// ================================================================================================
// Message Queue Utility Functions
// ================================================================================================

// Check if message queue is empty
bool osMesgQueueEmpty(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return true;
    }
    
    pthread_mutex_lock(&mq->mutex);
    bool empty = (mq->validCount == 0);
    pthread_mutex_unlock(&mq->mutex);
    
    return empty;
}

// Check if message queue is full
bool osMesgQueueFull(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return true;
    }
    
    pthread_mutex_lock(&mq->mutex);
    bool full = (mq->validCount >= mq->msgCount);
    pthread_mutex_unlock(&mq->mutex);
    
    return full;
}

// Get number of messages in queue
s32 osMesgQueueCount(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return -1;
    }
    
    pthread_mutex_lock(&mq->mutex);
    s32 count = mq->validCount;
    pthread_mutex_unlock(&mq->mutex);
    
    return count;
}

// Get maximum capacity of queue
s32 osMesgQueueCapacity(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return -1;
    }
    
    return mq->msgCount;
}

// Clear all messages from queue
void osMesgQueueClear(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return;
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    mq->validCount = 0;
    mq->first = 0;
    
    // Wake up all threads waiting to send (they can now proceed)
    pthread_cond_broadcast(&mq->send_cond);
    
    pthread_mutex_unlock(&mq->mutex);
}

// Destroy a message queue and clean up resources
void osMesgQueueDestroy(OSMesgQueue* mq) {
    if (mq == NULL || !mq->initialized) {
        return;
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    // Wake up all waiting threads
    pthread_cond_broadcast(&mq->send_cond);
    pthread_cond_broadcast(&mq->recv_cond);
    
    mq->initialized = false;
    mq->validCount = 0;
    mq->msgCount = 0;
    mq->msg = NULL;
    
    pthread_mutex_unlock(&mq->mutex);
    
    // Clean up synchronization primitives
    pthread_mutex_destroy(&mq->mutex);
    pthread_cond_destroy(&mq->send_cond);
    pthread_cond_destroy(&mq->recv_cond);
}

// ================================================================================================
// Advanced Message Functions (Extensions)
// ================================================================================================

// Send message with timeout (extension)
s32 osSendMesgTimeout(OSMesgQueue* mq, OSMesg msg, s32 timeout_ms) {
    if (mq == NULL || !mq->initialized) {
        return -1;
    }
    
    struct timespec timeout;
    clock_gettime(CLOCK_REALTIME, &timeout);
    timeout.tv_sec += timeout_ms / 1000;
    timeout.tv_nsec += (timeout_ms % 1000) * 1000000;
    if (timeout.tv_nsec >= 1000000000) {
        timeout.tv_sec++;
        timeout.tv_nsec -= 1000000000;
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    while (mq->validCount >= mq->msgCount) {
        int result = pthread_cond_timedwait(&mq->send_cond, &mq->mutex, &timeout);
        if (result == ETIMEDOUT) {
            pthread_mutex_unlock(&mq->mutex);
            return -1; // Timeout
        }
    }
    
    // Add message to queue
    s32 index = (mq->first + mq->validCount) % mq->msgCount;
    mq->msg[index] = msg;
    mq->validCount++;
    
    pthread_cond_signal(&mq->recv_cond);
    pthread_mutex_unlock(&mq->mutex);
    
    return 0;
}

// Receive message with timeout (extension)
s32 osRecvMesgTimeout(OSMesgQueue* mq, OSMesg* msg, s32 timeout_ms) {
    if (mq == NULL || !mq->initialized) {
        return -1;
    }
    
    struct timespec timeout;
    clock_gettime(CLOCK_REALTIME, &timeout);
    timeout.tv_sec += timeout_ms / 1000;
    timeout.tv_nsec += (timeout_ms % 1000) * 1000000;
    if (timeout.tv_nsec >= 1000000000) {
        timeout.tv_sec++;
        timeout.tv_nsec -= 1000000000;
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    while (mq->validCount == 0) {
        int result = pthread_cond_timedwait(&mq->recv_cond, &mq->mutex, &timeout);
        if (result == ETIMEDOUT) {
            pthread_mutex_unlock(&mq->mutex);
            return -1; // Timeout
        }
    }
    
    // Get message from queue
    if (msg != NULL) {
        *msg = mq->msg[mq->first];
    }
    
    mq->first = (mq->first + 1) % mq->msgCount;
    mq->validCount--;
    
    pthread_cond_signal(&mq->send_cond);
    pthread_mutex_unlock(&mq->mutex);
    
    return 0;
}

// ================================================================================================
// osJamMesg - Send a message to the front of a queue (high priority)
// ================================================================================================
s32 osJamMesg(OSMesgQueue* mq, OSMesg msg, s32 flag) {
    if (!mq || !mq->msg) {
        return -1;
    }
    
    pthread_mutex_lock(&mq->mutex);
    
    // If queue is full, handle based on flag
    if (mq->validCount >= mq->msgCount) {
        if (flag == OS_MESG_NOBLOCK) {
            pthread_mutex_unlock(&mq->mutex);
            return -1;
        }
        // For blocking, wait for space (simplified)
        while (mq->validCount >= mq->msgCount) {
            pthread_cond_wait(&mq->send_cond, &mq->mutex);
        }
    }
    
    // Shift all messages one position to the right
    for (s32 i = mq->validCount; i > 0; i--) {
        s32 src_index = (mq->first + i - 1) % mq->msgCount;
        s32 dst_index = (mq->first + i) % mq->msgCount;
        mq->msg[dst_index] = mq->msg[src_index];
    }
    
    // Insert message at front
    mq->msg[mq->first] = msg;
    mq->validCount++;
    
    pthread_cond_signal(&mq->recv_cond);
    pthread_mutex_unlock(&mq->mutex);
    
    return 0;
} 