#include "libultra/libultra_compat.h"
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <stdlib.h>

/* ================================================================================================
 * DMA AND CACHE MANAGEMENT IMPLEMENTATION
 * 
 * N64 DMA operations are replaced with simple memory operations since modern systems
 * don't require explicit DMA management. Cache operations are no-ops since modern
 * operating systems handle cache coherency automatically.
 * ================================================================================================ */

// DMA operation state
static pthread_mutex_t dma_mutex = PTHREAD_MUTEX_INITIALIZER;
static volatile bool dma_in_progress = false;
static volatile int dma_status = 0;

// ================================================================================================
// osPiStartDma - Start a DMA transfer (simplified to memcpy)
// ================================================================================================
void osPiStartDma(void* dest, void* src, size_t size) {
    if (dest == NULL || src == NULL || size == 0) {
        return;
    }
    
    pthread_mutex_lock(&dma_mutex);
    
    // Set DMA in progress flag
    dma_in_progress = true;
    
    // Perform the "DMA" operation (just a memory copy in our case)
    memcpy(dest, src, size);
    
    // DMA operation complete
    dma_in_progress = false;
    dma_status = 0; // Success
    
    pthread_mutex_unlock(&dma_mutex);
}

// ================================================================================================
// osPiGetStatus - Get DMA status
// ================================================================================================
s32 osPiGetStatus(void) {
    pthread_mutex_lock(&dma_mutex);
    s32 status = dma_in_progress ? 1 : 0; // 1 = busy, 0 = idle
    pthread_mutex_unlock(&dma_mutex);
    return status;
}

// ================================================================================================
// Cache Management Functions (No-ops on modern systems)
// ================================================================================================

// osWritebackDCache - Write back data cache to memory
void osWritebackDCache(void* vaddr, s32 nbytes) {
    // No-op: Modern operating systems handle cache coherency automatically
    (void)vaddr;   // Suppress unused parameter warning
    (void)nbytes;  // Suppress unused parameter warning
}

// osInvalDCache - Invalidate data cache
void osInvalDCache(void* vaddr, s32 nbytes) {
    // No-op: Modern operating systems handle cache coherency automatically
    (void)vaddr;   // Suppress unused parameter warning
    (void)nbytes;  // Suppress unused parameter warning
}

// osWritebackDCacheAll - Write back entire data cache
void osWritebackDCacheAll(void) {
    // No-op: Modern operating systems handle cache coherency automatically
}

// osInvalICache - Invalidate instruction cache
void osInvalICache(void* vaddr, s32 nbytes) {
    // No-op: Modern operating systems handle cache coherency automatically
    (void)vaddr;   // Suppress unused parameter warning
    (void)nbytes;  // Suppress unused parameter warning
}

// ================================================================================================
// DMA Helper Functions for Extended Functionality
// ================================================================================================

// Check if any DMA operation is in progress
bool osPiIsBusy(void) {
    pthread_mutex_lock(&dma_mutex);
    bool busy = dma_in_progress;
    pthread_mutex_unlock(&dma_mutex);
    return busy;
}

// Wait for DMA operation to complete
void osPiWaitForCompletion(void) {
    // Simple polling loop - in real implementation this would be more sophisticated
    while (osPiIsBusy()) {
        // Small delay to avoid busy waiting
        usleep(1); // 1 microsecond
    }
}

// Async DMA operation with callback (extension)
typedef void (*DMACallback)(void* user_data);

struct AsyncDMAOp {
    void* dest;
    void* src;
    size_t size;
    DMACallback callback;
    void* user_data;
};

static void* async_dma_thread(void* arg) {
    struct AsyncDMAOp* op = (struct AsyncDMAOp*)arg;
    
    // Perform the DMA operation
    osPiStartDma(op->dest, op->src, op->size);
    
    // Call completion callback if provided
    if (op->callback) {
        op->callback(op->user_data);
    }
    
    // Clean up
    free(op);
    return NULL;
}

// Start an asynchronous DMA operation (extension)
void osPiStartDmaAsync(void* dest, void* src, size_t size, DMACallback callback, void* user_data) {
    struct AsyncDMAOp* op = malloc(sizeof(struct AsyncDMAOp));
    if (op == NULL) {
        return; // Memory allocation failed
    }
    
    op->dest = dest;
    op->src = src;
    op->size = size;
    op->callback = callback;
    op->user_data = user_data;
    
    pthread_t thread;
    if (pthread_create(&thread, NULL, async_dma_thread, op) != 0) {
        free(op);
        return; // Thread creation failed
    }
    
    // Detach thread so it cleans up automatically
    pthread_detach(thread);
} 