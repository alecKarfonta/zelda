#ifndef LIBULTRA_COMPAT_H
#define LIBULTRA_COMPAT_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <pthread.h>
#include <semaphore.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ================================================================================================
 * LIBULTRA COMPATIBILITY LAYER FOR OOT NATIVE
 * 
 * This header provides API-compatible replacements for all libultra functions and types
 * needed by the OOT decompiled source code. The implementation uses modern cross-platform
 * libraries (pthread, SDL2, etc.) while maintaining exact libultra semantics.
 * ================================================================================================ */

// ================================================================================================
// BASIC TYPES (from ultratypes.h)
// ================================================================================================

typedef signed char            s8;
typedef unsigned char          u8;
typedef signed short int       s16;
typedef unsigned short int     u16;
typedef signed long            s32;
typedef unsigned long          u32;
typedef signed long long int   s64;
typedef unsigned long long int u64;

typedef volatile u8  vu8;
typedef volatile u16 vu16;
typedef volatile u32 vu32;
typedef volatile s8  vs8;
typedef volatile s16 vs16;
typedef volatile s32 vs32;

typedef float  f32;
typedef double f64;

// Matrix types
typedef float MtxF_t[4][4];
typedef union MtxF {
    MtxF_t mf;
    struct {
        float xx, yx, zx, wx,
              xy, yy, zy, wy,
              xz, yz, zz, wz,
              xw, yw, zw, ww;
    };
} MtxF;

// ================================================================================================
// MESSAGE SYSTEM TYPES AND CONSTANTS
// ================================================================================================

#define OS_MESG_NOBLOCK         0
#define OS_MESG_BLOCK           1

#define OS_NUM_EVENTS           15

#define OS_EVENT_SW1            0
#define OS_EVENT_SW2            1
#define OS_EVENT_CART           2
#define OS_EVENT_COUNTER        3
#define OS_EVENT_SP             4
#define OS_EVENT_SI             5
#define OS_EVENT_AI             6
#define OS_EVENT_VI             7
#define OS_EVENT_PI             8
#define OS_EVENT_DP             9
#define OS_EVENT_CPU_BREAK      10
#define OS_EVENT_SP_BREAK       11
#define OS_EVENT_FAULT          12
#define OS_EVENT_THREADSTATUS   13
#define OS_EVENT_PRENMI         14

typedef void* OSMesg;
typedef u32 OSEvent;

// Forward declaration for circular dependency
struct OSThread;

// Modern implementation of N64 message queue
typedef struct OSMesgQueue {
    struct OSThread* mtqueue;      // Threads waiting to send
    struct OSThread* fullqueue;    // Threads waiting to receive
    s32 validCount;                // Number of messages in queue
    s32 first;                     // Index of first message
    s32 msgCount;                  // Maximum number of messages
    OSMesg* msg;                   // Message buffer
    
    // Modern implementation fields
    pthread_mutex_t mutex;         // Thread safety
    pthread_cond_t send_cond;      // Condition for senders
    pthread_cond_t recv_cond;      // Condition for receivers
    bool initialized;              // Initialization flag
} OSMesgQueue;

// ================================================================================================
// THREADING SYSTEM TYPES AND CONSTANTS  
// ================================================================================================

#define OS_PRIORITY_MAX      255
#define OS_PRIORITY_VIMGR    254
#define OS_PRIORITY_RMON     250
#define OS_PRIORITY_RMONSPIN 200
#define OS_PRIORITY_PIMGR    150
#define OS_PRIORITY_SIMGR    140
#define OS_PRIORITY_APPMAX   127
#define OS_PRIORITY_IDLE       0

#define OS_STATE_STOPPED    1
#define OS_STATE_RUNNABLE   2
#define OS_STATE_RUNNING    4
#define OS_STATE_WAITING    8

#define OS_FLAG_CPU_BREAK   1
#define OS_FLAG_FAULT       2

typedef s32 OSPri;
typedef s32 OSId;

typedef struct OSThread {
    struct OSThread* next;         // Next thread in queue
    OSPri priority;                // Thread priority
    struct OSThread** queue;       // Queue this thread is in
    struct OSThread* tlnext;       // Next in thread list
    u16 state;                     // Thread state (STOPPED, RUNNABLE, etc.)
    u16 flags;                     // Thread flags
    OSId id;                       // Thread ID
    s32 fp;                        // Floating point flag
    void* thprof;                  // Thread profile (unused)
    
    // Modern implementation fields
    pthread_t pthread_id;          // POSIX thread ID
    void (*entry_point)(void*);    // Thread entry function
    void* arg;                     // Thread argument
    void* stack_pointer;           // Stack pointer (unused in modern implementation)
    bool active;                   // Whether thread is active
    pthread_mutex_t state_mutex;   // Mutex for state changes
} OSThread;

// ================================================================================================
// TIMING SYSTEM TYPES
// ================================================================================================

typedef u64 OSTime;

typedef struct OSTimer {
    struct OSTimer* next;          // Next timer in list
    struct OSTimer* prev;          // Previous timer in list
    OSTime interval;               // Timer interval
    OSTime value;                  // Current timer value
    OSMesgQueue* mq;               // Message queue to notify
    OSMesg msg;                    // Message to send
    
    // Modern implementation fields
    pthread_t timer_thread;        // Timer thread
    bool active;                   // Whether timer is active
    pthread_mutex_t timer_mutex;   // Timer state mutex
} OSTimer;

// ================================================================================================
// MEMORY MANAGEMENT TYPES
// ================================================================================================

typedef struct OSHeap {
    void* base;                    // Base address of heap
    size_t size;                   // Size of heap
    size_t used;                   // Amount of heap used
    pthread_mutex_t mutex;         // Heap access mutex
} OSHeap;

// ================================================================================================
// CONTROLLER/INPUT TYPES
// ================================================================================================

#define MAXCONTROLLERS 4

typedef struct OSContStatus {
    u16 type;                      // Controller type
    u8 status;                     // Controller status  
    u8 errno;                      // Error number
} OSContStatus;

typedef struct OSContPad {
    u16 button;                    // Button state
    s8 stick_x;                    // Analog stick X
    s8 stick_y;                    // Analog stick Y
    u8 errno;                      // Error number
} OSContPad;

// ================================================================================================
// GRAPHICS/VIDEO TYPES
// ================================================================================================

typedef struct OSViMode {
    u32 type;                      // Video mode type
    struct {
        u16 h_video;
        u16 v_video;
        u16 h_start;
        u16 v_start;
        u16 h_sync;
        u16 v_sync;
    } comRegs;
    u32 fldRegs[2][13];           // Field registers
    void* unk;                     // Unknown field
} OSViMode;

// ================================================================================================
// AUDIO TYPES
// ================================================================================================

typedef struct OSAudioSpec {
    u32 frequency;                 // Audio frequency
    u32 samples;                   // Samples per frame
    u32 channels;                  // Number of channels
} OSAudioSpec;

// ================================================================================================
// CARTRIDGE/ROM TYPES
// ================================================================================================

typedef struct OSPiHandle {
    struct OSPiHandle* next;
    u8 type;
    u8 latency;
    u8 pageSize;
    u8 relDuration;
    u8 pulse;
    u32 domain;
    u32 baseAddress;
    u32 speed;
    u32 transferModeType;
} OSPiHandle;

// ================================================================================================
// RSP TASK TYPES
// ================================================================================================

typedef struct OSTask {
    u32 type;
    u32 flags;
    u64* ucode_boot;
    u32 ucode_boot_size;
    u64* ucode;
    u32 ucode_size;
    u64* ucode_data;
    u32 ucode_data_size;
    u64* dram_stack;
    u32 dram_stack_size;
    u64* output_buff;
    u64* output_buff_size;
    u64* data_ptr;
    u32 data_size;
    u64* yield_data_ptr;
    u32 yield_data_size;
} OSTask;

// Task types
#define M_GFXTASK    1
#define M_AUDTASK    2
#define M_VJDPTASK   3
#define M_NULTASK    4

// Task flags  
#define OS_SC_NEEDS_RSP    0x0001
#define OS_SC_NEEDS_RDP    0x0002
#define OS_SC_LAST_TASK    0x0004
#define OS_SC_YIELD        0x0010
#define OS_SC_YIELDED      0x0020

// ================================================================================================
// CONSTANTS
// ================================================================================================

// N64 CPU frequency for timing calculations
#define N64_CPU_FREQUENCY 93750000ULL

// ================================================================================================
// FUNCTION DECLARATIONS
// ================================================================================================

// Message System Functions
void osCreateMesgQueue(OSMesgQueue* mq, OSMesg* msg, s32 count);
s32 osSendMesg(OSMesgQueue* mq, OSMesg msg, s32 flag);
s32 osRecvMesg(OSMesgQueue* mq, OSMesg* msg, s32 flag);
s32 osJamMesg(OSMesgQueue* mq, OSMesg msg, s32 flag);
void osSetEventMesg(OSEvent event, OSMesgQueue* mq, OSMesg msg);

// Threading Functions
void osCreateThread(OSThread* thread, OSId id, void (*entry)(void*), void* arg, void* sp, OSPri pri);
void osStartThread(OSThread* thread);
void osStopThread(OSThread* thread);
void osDestroyThread(OSThread* thread);
void osYieldThread(void);
OSThread* osGetActiveThread(void);
s32 osGetThreadId(OSThread* thread);
OSPri osGetThreadPri(OSThread* thread);
OSPri osSetThreadPri(OSThread* thread, OSPri priority);

// Timing Functions
OSTime osGetTime(void);
void osSetTime(OSTime time);
u32 osGetCount(void);
void osSetTimer(OSTimer* timer, OSTime countdown, OSTime interval, OSMesgQueue* mq, OSMesg msg);
void osStopTimer(OSTimer* timer);

// Memory Management Functions
u32 osGetMemSize(void);
void* osCreateHeap(OSHeap* heap, void* base, size_t size);
void osDestroyHeap(OSHeap* heap);
void* osHeapAlloc(OSHeap* heap, size_t size);
void osHeapFree(OSHeap* heap, void* ptr);

// DMA and Cache Functions  
void osPiStartDma(void* dest, void* src, size_t size);
s32 osPiGetStatus(void);
void osWritebackDCache(void* vaddr, s32 nbytes);
void osInvalDCache(void* vaddr, s32 nbytes);
void osWritebackDCacheAll(void);
void osInvalICache(void* vaddr, s32 nbytes);

// Controller Functions
s32 osContInit(OSMesgQueue* mq, u8* bitpattern, OSContStatus* data);
s32 osContStartReadData(OSMesgQueue* mq);
void osContGetReadData(OSContPad* data);
s32 osContSetCh(u8 ch);

// Video Interface Functions
void osViSetMode(OSViMode* mode);
void osViSetSpecialFeatures(u32 func);
void osViSwapBuffer(void* framebuffer);
void osViBlack(u8 active);
void osViRepeatLine(u8 active);
void osViSetXScale(f32 scale);
void osViSetYScale(f32 scale);
u32* osViGetCurrentFramebuffer(void);
u32* osViGetNextFramebuffer(void);
void osViSetEvent(OSMesgQueue* mq, OSMesg msg, u32 retraceCount);

// Audio Interface Functions
s32 osAiSetFrequency(u32 frequency);
s32 osAiSetNextBuffer(void* buffer, u32 size);
u32 osAiGetLength(void);
u32 osAiGetStatus(void);

// System Functions
void osInitialize(void);
void __osInitialize_common(void);
void __osInitialize_autodetect(void);

// Interrupt Management Functions
u32 osDisableInt(void);
void osRestoreInt(u32 mask);
void osSetIntMask(u32 mask);
s32 osAfterPreNMI(void);

// Math Functions (for compatibility)
f32 sinf(f32 x);
f32 cosf(f32 x);
f32 sqrtf(f32 x);

// Memory Translation Functions
void* osVirtualToPhysical(void* vaddr);
void* osPhysicalToVirtual(void* paddr);

// Cartridge/ROM Functions
OSPiHandle* osCartRomInit(void);

// RSP Task Functions
void osSpTaskLoad(OSTask* task);
void osSpTaskStartGo(OSTask* task);
void osSpTaskYield(void);
s32 osSpTaskYielded(OSTask* task);

// ================================================================================================
// INITIALIZATION FUNCTION
// ================================================================================================

// Call this once to initialize the libultra compatibility layer
void LibultraCompat_Initialize(void);
void LibultraCompat_Shutdown(void);

// System status functions
bool LibultraCompat_IsInitialized(void);
const char* LibultraCompat_GetVersion(void);

// Event system internal functions
void osEventMesg_Send(OSEvent event);
void osEventSystem_Initialize(void);
void osEventSystem_Shutdown(void);
void osTimingSystem_Shutdown(void);

// Extended message queue functions
bool osMesgQueueEmpty(OSMesgQueue* mq);
bool osMesgQueueFull(OSMesgQueue* mq);
s32 osMesgQueueCount(OSMesgQueue* mq);
s32 osMesgQueueCapacity(OSMesgQueue* mq);
void osMesgQueueClear(OSMesgQueue* mq);
void osMesgQueueDestroy(OSMesgQueue* mq);
s32 osSendMesgTimeout(OSMesgQueue* mq, OSMesg msg, s32 timeout_ms);
s32 osRecvMesgTimeout(OSMesgQueue* mq, OSMesg* msg, s32 timeout_ms);

// Extended timing functions
u64 osGetTimeNanoseconds(void);
u64 osGetTimeMilliseconds(void);
u64 osGetTimeMicroseconds(void);
void osSleep(OSTime time);
void osSleepMs(u32 milliseconds);
void osSleepUs(u32 microseconds);

// Extended threading functions
u16 osGetThreadState(OSThread* thread);
bool osIsThreadActive(OSThread* thread);
void osJoinThread(OSThread* thread);
s32 osGetActiveThreadCount(void);

// Extended interrupt management
bool osIsEventEnabled(OSEvent event);
u32 osGetIntMask(void);
void osEnableEvent(OSEvent event);
void osDisableEvent(OSEvent event);

// Extended DMA functions
bool osPiIsBusy(void);
void osPiWaitForCompletion(void);

// Extended memory functions
void osHeapGetStats(OSHeap* heap, size_t* total_size, size_t* used_size, size_t* free_size);

// Extended RSP functions
OSTask* osSpGetCurrentTask(void);
bool osSpIsBusy(void);
void osSpClearTask(void);

#ifdef __cplusplus
}
#endif

#endif // LIBULTRA_COMPAT_H 