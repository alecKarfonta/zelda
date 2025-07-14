#include "libultra/libultra_compat.h"
#include <stdlib.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <unistd.h>

/* ================================================================================================
 * MEMORY MANAGEMENT IMPLEMENTATION
 * 
 * Provides N64-compatible memory management functions using modern allocation techniques.
 * Maintains API compatibility while leveraging modern virtual memory systems.
 * ================================================================================================ */

// Global memory size (cached for osGetMemSize)
static u32 g_total_memory_size = 0;

// Simple arena allocator for N64 compatibility
typedef struct MemoryBlock {
    struct MemoryBlock* next;
    size_t size;
    bool free;
} MemoryBlock;

// ================================================================================================
// osGetMemSize - Returns available system memory
// ================================================================================================
u32 osGetMemSize(void) {
    if (g_total_memory_size == 0) {
        // Get system memory information
        #ifdef __linux__
        struct sysinfo info;
        if (sysinfo(&info) == 0) {
            // Return total RAM in bytes (N64 had 4MB, modern systems have GB)
            // Cap at reasonable value to maintain N64-like behavior
            u64 total_ram = (u64)info.totalram * info.mem_unit;
            if (total_ram > 0x10000000) { // Cap at 256MB for N64 compatibility
                g_total_memory_size = 0x10000000; // 256MB
            } else {
                g_total_memory_size = (u32)total_ram;
            }
        } else {
            // Fallback: assume 128MB available
            g_total_memory_size = 0x8000000; // 128MB
        }
        #else
        // Cross-platform fallback
        long pages = sysconf(_SC_PHYS_PAGES);
        long page_size = sysconf(_SC_PAGE_SIZE);
        if (pages > 0 && page_size > 0) {
            u64 total_ram = (u64)pages * page_size;
            if (total_ram > 0x10000000) { // Cap at 256MB
                g_total_memory_size = 0x10000000;
            } else {
                g_total_memory_size = (u32)total_ram;
            }
        } else {
            g_total_memory_size = 0x8000000; // 128MB fallback
        }
        #endif
    }
    
    return g_total_memory_size;
}

// ================================================================================================
// osCreateHeap - Initialize a heap allocator
// ================================================================================================
void* osCreateHeap(OSHeap* heap, void* base, size_t size) {
    if (heap == NULL || size == 0) {
        return NULL;
    }
    
    // Initialize the heap structure
    bool allocated_by_us = false;
    if (base == NULL) {
        // If no base provided, allocate memory
        base = malloc(size);
        if (base == NULL) {
            return NULL;
        }
        allocated_by_us = true;
    }
    
    heap->base = base;
    heap->size = size;
    heap->used = 0;
    
    // Initialize mutex for thread safety
    if (pthread_mutex_init(&heap->mutex, NULL) != 0) {
        if (allocated_by_us && base != NULL) {
            free(base);
        }
        return NULL;
    }
    
    // Initialize the first free block
    MemoryBlock* first_block = (MemoryBlock*)base;
    first_block->next = NULL;
    first_block->size = size - sizeof(MemoryBlock);
    first_block->free = true;
    
    return base;
}

// ================================================================================================
// osDestroyHeap - Clean up a heap allocator
// ================================================================================================
void osDestroyHeap(OSHeap* heap) {
    if (heap == NULL) {
        return;
    }
    
    pthread_mutex_lock(&heap->mutex);
    
    // Don't free the base memory - let the caller handle that
    // since they may have provided their own buffer
    heap->base = NULL;
    heap->size = 0;
    heap->used = 0;
    
    pthread_mutex_unlock(&heap->mutex);
    pthread_mutex_destroy(&heap->mutex);
}

// ================================================================================================
// osHeapAlloc - Allocate memory from a heap
// ================================================================================================
void* osHeapAlloc(OSHeap* heap, size_t size) {
    if (heap == NULL || size == 0 || heap->base == NULL) {
        return NULL;
    }
    
    // Align size to 8-byte boundary (N64 compatibility)
    size = (size + 7) & ~7;
    
    pthread_mutex_lock(&heap->mutex);
    
    MemoryBlock* current = (MemoryBlock*)heap->base;
    MemoryBlock* best_fit = NULL;
    size_t best_fit_size = SIZE_MAX;
    
    // Find the best fit free block
    while (current != NULL) {
        if (current->free && current->size >= size) {
            if (current->size < best_fit_size) {
                best_fit = current;
                best_fit_size = current->size;
            }
        }
        current = current->next;
    }
    
    if (best_fit == NULL) {
        pthread_mutex_unlock(&heap->mutex);
        return NULL; // No suitable block found
    }
    
    // Split the block if it's significantly larger than needed
    if (best_fit->size > size + sizeof(MemoryBlock) + 32) {
        MemoryBlock* new_block = (MemoryBlock*)((u8*)best_fit + sizeof(MemoryBlock) + size);
        new_block->next = best_fit->next;
        new_block->size = best_fit->size - size - sizeof(MemoryBlock);
        new_block->free = true;
        
        best_fit->next = new_block;
        best_fit->size = size;
    }
    
    best_fit->free = false;
    heap->used += best_fit->size + sizeof(MemoryBlock);
    
    pthread_mutex_unlock(&heap->mutex);
    
    // Return pointer after the block header
    return (u8*)best_fit + sizeof(MemoryBlock);
}

// ================================================================================================
// osHeapFree - Free memory from a heap
// ================================================================================================
void osHeapFree(OSHeap* heap, void* ptr) {
    if (heap == NULL || ptr == NULL || heap->base == NULL) {
        return;
    }
    
    pthread_mutex_lock(&heap->mutex);
    
    // Get the block header
    MemoryBlock* block = (MemoryBlock*)((u8*)ptr - sizeof(MemoryBlock));
    
    // Verify the pointer is within the heap bounds
    if ((u8*)block < (u8*)heap->base || 
        (u8*)block >= (u8*)heap->base + heap->size) {
        pthread_mutex_unlock(&heap->mutex);
        return; // Invalid pointer
    }
    
    // Mark block as free
    if (!block->free) {
        block->free = true;
        heap->used -= block->size + sizeof(MemoryBlock);
        
        // Coalesce with next block if it's free
        while (block->next != NULL && block->next->free) {
            MemoryBlock* next_block = block->next;
            block->size += next_block->size + sizeof(MemoryBlock);
            block->next = next_block->next;
        }
        
        // Coalesce with previous block if it's free
        MemoryBlock* current = (MemoryBlock*)heap->base;
        while (current != NULL && current->next != block) {
            if (current->free && (u8*)current + sizeof(MemoryBlock) + current->size == (u8*)block) {
                current->size += block->size + sizeof(MemoryBlock);
                current->next = block->next;
                break;
            }
            current = current->next;
        }
    }
    
    pthread_mutex_unlock(&heap->mutex);
}

// ================================================================================================
// Debug/Info Functions
// ================================================================================================

// Get heap usage statistics (extension for debugging)
void osHeapGetStats(OSHeap* heap, size_t* total_size, size_t* used_size, size_t* free_size) {
    if (heap == NULL || heap->base == NULL) {
        if (total_size) *total_size = 0;
        if (used_size) *used_size = 0;
        if (free_size) *free_size = 0;
        return;
    }
    
    pthread_mutex_lock(&heap->mutex);
    
    if (total_size) *total_size = heap->size;
    if (used_size) *used_size = heap->used;
    if (free_size) *free_size = heap->size - heap->used;
    
    pthread_mutex_unlock(&heap->mutex);
}

// ================================================================================================
// osVirtualToPhysical - Convert virtual address to physical address
// ================================================================================================
void* osVirtualToPhysical(void* virtualAddr) {
    // In modern systems, we use identity mapping (virtual == physical for user space)
    // This is a simplified implementation for N64 compatibility
    return virtualAddr;
}

// ================================================================================================
// osPhysicalToVirtual - Convert physical address to virtual address
// ================================================================================================
void* osPhysicalToVirtual(void* physicalAddr) {
    // In modern systems, we use identity mapping (physical == virtual for user space)
    // This is a simplified implementation for N64 compatibility
    return physicalAddr;
} 