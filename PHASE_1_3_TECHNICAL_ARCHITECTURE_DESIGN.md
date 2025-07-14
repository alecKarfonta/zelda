# Phase 1.3: Technical Architecture Design - IN PROGRESS 🔄

*Building upon Phase 1.2 comprehensive dependency mapping and Ship of Harkinian implementation analysis*

## Overview

Phase 1.3 designs the modern technical architecture to replace N64-specific dependencies with cross-platform equivalents. This architecture follows the proven Ship of Harkinian pattern: **API compatibility layer + modern implementation backends + cross-platform abstraction**.

---

## 1.3.1 System Architecture Design 🔄

### **Core Architecture Pattern: Layered Abstraction**

```
┌─────────────────────────────────────────────────────────────┐
│                    OOT Game Logic                           │
│                 (Unchanged from N64)                        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                libultra Compatibility Layer                 │
│     (API-compatible replacements for N64 functions)        │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Platform Abstraction Layer                   │
│        (Cross-platform backends for modern APIs)           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Native Platform APIs                       │
│         (OpenGL, DirectX, SDL, OpenAL, etc.)               │
└─────────────────────────────────────────────────────────────┘
```

### **Graphics API Abstraction Architecture**

#### **Multi-Backend Graphics System**

*Following Ship of Harkinian's proven multi-backend approach*

```cpp
// Core Graphics Interface
class GraphicsBackend {
public:
    virtual ~GraphicsBackend() = default;
    
    // Core rendering operations
    virtual void Initialize(const GraphicsConfig& config) = 0;
    virtual void Shutdown() = 0;
    virtual void BeginFrame() = 0;
    virtual void EndFrame() = 0;
    virtual void Present() = 0;
    
    // N64 Display List Translation
    virtual void ProcessDisplayList(const Gfx* displayList) = 0;
    virtual void SetCombineMode(u32 mode) = 0;
    virtual void SetPrimColor(u8 r, u8 g, u8 b, u8 a) = 0;
    virtual void SetEnvColor(u8 r, u8 g, u8 b, u8 a) = 0;
    virtual void SetBlendColor(u8 r, u8 g, u8 b, u8 a) = 0;
    
    // Texture management
    virtual TextureHandle LoadTexture(const N64Texture& texture) = 0;
    virtual void BindTexture(TextureHandle handle, u32 slot) = 0;
    virtual void UnloadTexture(TextureHandle handle) = 0;
    
    // Geometry operations
    virtual void DrawTriangles(const Vertex* vertices, u32 count) = 0;
    virtual void SetTransform(const Matrix4x4& transform) = 0;
    virtual void SetViewport(u32 x, u32 y, u32 width, u32 height) = 0;
    
    // State management
    virtual void SetDepthTest(bool enable) = 0;
    virtual void SetCullMode(CullMode mode) = 0;
    virtual void SetBlendMode(BlendMode mode) = 0;
};

// Graphics Backend Factory
class GraphicsBackendFactory {
public:
    enum class BackendType {
        OpenGL,
        DirectX11,
        Vulkan,
        Metal
    };
    
    static std::unique_ptr<GraphicsBackend> CreateBackend(BackendType type);
    static std::vector<BackendType> GetAvailableBackends();
    static BackendType GetRecommendedBackend();
};
```

#### **Backend Implementations**

**OpenGL Backend (Primary - Cross-platform)**
```cpp
class OpenGLBackend : public GraphicsBackend {
private:
    struct OpenGLState {
        GLuint framebuffer;
        GLuint colorTexture;
        GLuint depthTexture;
        GLuint shaderProgram;
        GLuint vertexArray;
        GLuint vertexBuffer;
        GLuint indexBuffer;
        
        // N64 state simulation
        N64CombinerState combiner;
        N64BlendState blender;
        N64TextureState texture;
    };
    
    OpenGLState state;
    
public:
    void Initialize(const GraphicsConfig& config) override;
    void ProcessDisplayList(const Gfx* displayList) override;
    void SetCombineMode(u32 mode) override;
    
private:
    void CompileShaders();
    void SetupFramebuffer();
    void TranslateN64Combiner(u32 mode);
    void ConvertN64Texture(const N64Texture& src, GLTexture& dst);
};
```

**DirectX11 Backend (Windows optimization)**
```cpp
class DirectX11Backend : public GraphicsBackend {
private:
    struct D3D11State {
        ID3D11Device* device;
        ID3D11DeviceContext* context;
        IDXGISwapChain* swapChain;
        ID3D11RenderTargetView* renderTargetView;
        ID3D11DepthStencilView* depthStencilView;
        ID3D11VertexShader* vertexShader;
        ID3D11PixelShader* pixelShader;
        ID3D11Buffer* vertexBuffer;
        ID3D11Buffer* indexBuffer;
        ID3D11Buffer* constantBuffer;
        
        // N64 state simulation
        N64CombinerState combiner;
        N64BlendState blender;
        N64TextureState texture;
    };
    
    D3D11State state;
    
public:
    void Initialize(const GraphicsConfig& config) override;
    void ProcessDisplayList(const Gfx* displayList) override;
    void SetCombineMode(u32 mode) override;
    
private:
    void CreateDeviceAndSwapChain();
    void CreateShaders();
    void CreateBuffers();
    void TranslateN64CombinerToHLSL(u32 mode);
    void ConvertN64TextureToD3D11(const N64Texture& src, ID3D11Texture2D** dst);
};
```

#### **N64 Display List Translation System**

```cpp
class DisplayListProcessor {
private:
    GraphicsBackend* backend;
    
    struct ProcessorState {
        Matrix4x4 modelMatrix;
        Matrix4x4 viewMatrix;
        Matrix4x4 projMatrix;
        
        u32 geometryMode;
        u32 combineMode;
        Color primColor;
        Color envColor;
        Color blendColor;
        
        TextureHandle currentTexture;
        u32 textureFlags;
        
        std::vector<Vertex> vertexBuffer;
        std::vector<u16> indexBuffer;
    };
    
    ProcessorState state;
    
public:
    DisplayListProcessor(GraphicsBackend* backend);
    
    void ProcessDisplayList(const Gfx* displayList);
    
private:
    void ProcessCommand(const Gfx& cmd);
    void ProcessG_VTX(const Gfx& cmd);
    void ProcessG_TRI1(const Gfx& cmd);
    void ProcessG_DL(const Gfx& cmd);
    void ProcessG_MTX(const Gfx& cmd);
    void ProcessG_TEXTURE(const Gfx& cmd);
    void ProcessG_SETCOMBINE(const Gfx& cmd);
    void ProcessG_SETPRIMCOLOR(const Gfx& cmd);
    void ProcessG_SETENVCOLOR(const Gfx& cmd);
    void ProcessG_SETTIMG(const Gfx& cmd);
    void ProcessG_SETTILE(const Gfx& cmd);
    void ProcessG_LOADTILE(const Gfx& cmd);
    void ProcessG_ENDDL(const Gfx& cmd);
    
    void FlushVertices();
    void UpdateTransforms();
    void UpdateTextureState();
};
```

### **Audio System Architecture**

#### **Multi-Backend Audio System**

*Following Ship of Harkinian's RSP audio replacement approach*

```cpp
// Core Audio Interface
class AudioBackend {
public:
    virtual ~AudioBackend() = default;
    
    // Core audio operations
    virtual void Initialize(const AudioConfig& config) = 0;
    virtual void Shutdown() = 0;
    virtual void Update() = 0;
    
    // N64 Audio Interface compatibility
    virtual void SetFrequency(u32 frequency) = 0;
    virtual void QueueBuffer(const s16* samples, u32 sampleCount) = 0;
    virtual u32 GetBufferLength() = 0;
    virtual AudioStatus GetStatus() = 0;
    
    // Sequence playback
    virtual void PlaySequence(const AudioSequence& sequence) = 0;
    virtual void StopSequence(u32 sequenceId) = 0;
    virtual void SetSequenceVolume(u32 sequenceId, f32 volume) = 0;
    
    // Sound effects
    virtual void PlaySFX(const AudioSample& sample, f32 volume, f32 pitch) = 0;
    virtual void StopSFX(u32 sfxId) = 0;
    
    // Voice management
    virtual VoiceHandle AllocateVoice() = 0;
    virtual void FreeVoice(VoiceHandle voice) = 0;
    virtual void SetVoiceParams(VoiceHandle voice, const VoiceParams& params) = 0;
};

// Audio Backend Factory
class AudioBackendFactory {
public:
    enum class BackendType {
        SDL_Audio,
        OpenAL,
        DirectSound,
        CoreAudio,
        WASAPI
    };
    
    static std::unique_ptr<AudioBackend> CreateBackend(BackendType type);
    static std::vector<BackendType> GetAvailableBackends();
    static BackendType GetRecommendedBackend();
};
```

#### **SDL Audio Backend Implementation**

```cpp
class SDLAudioBackend : public AudioBackend {
private:
    struct SDLAudioState {
        SDL_AudioDeviceID deviceId;
        SDL_AudioSpec audioSpec;
        
        // Audio buffers
        std::queue<std::vector<s16>> audioQueue;
        std::mutex queueMutex;
        std::condition_variable queueCondition;
        
        // Mixing state
        std::vector<AudioVoice> voices;
        AudioMixer mixer;
        
        // Configuration
        u32 frequency;
        u32 bufferSize;
        u32 channels;
    };
    
    SDLAudioState state;
    
public:
    void Initialize(const AudioConfig& config) override;
    void QueueBuffer(const s16* samples, u32 sampleCount) override;
    void PlaySequence(const AudioSequence& sequence) override;
    
private:
    static void AudioCallback(void* userdata, u8* stream, int len);
    void FillAudioBuffer(s16* buffer, u32 sampleCount);
    void ProcessAudioQueue();
    void MixVoices(s16* output, u32 sampleCount);
};
```

#### **Audio Sequence Player**

```cpp
class AudioSequencePlayer {
private:
    struct SequenceState {
        const AudioSequence* sequence;
        u32 currentTick;
        f32 tempo;
        f32 volume;
        bool isPlaying;
        bool isLooping;
        
        std::vector<ChannelState> channels;
        std::vector<VoiceHandle> voices;
    };
    
    std::unordered_map<u32, SequenceState> activeSequences;
    AudioBackend* backend;
    
public:
    AudioSequencePlayer(AudioBackend* backend);
    
    void PlaySequence(u32 sequenceId, const AudioSequence& sequence);
    void StopSequence(u32 sequenceId);
    void SetSequenceVolume(u32 sequenceId, f32 volume);
    void Update();
    
private:
    void UpdateSequence(SequenceState& state);
    void ProcessSequenceEvent(const SequenceEvent& event, SequenceState& state);
    void AllocateVoicesForSequence(SequenceState& state);
    void FreeVoicesForSequence(SequenceState& state);
};
```

### **Input System Architecture**

#### **Cross-Platform Input System**

```cpp
// Core Input Interface
class InputBackend {
public:
    virtual ~InputBackend() = default;
    
    // Core input operations
    virtual void Initialize() = 0;
    virtual void Shutdown() = 0;
    virtual void Update() = 0;
    
    // N64 Controller interface compatibility
    virtual void StartControllerQuery() = 0;
    virtual void GetControllerQuery(OSContStatus* status) = 0;
    virtual void StartReadControllerData() = 0;
    virtual void GetControllerData(OSContPad* pad) = 0;
    
    // Modern input features
    virtual void SetControllerMapping(u32 controllerId, const InputMapping& mapping) = 0;
    virtual void SetDeadzone(u32 controllerId, f32 deadzone) = 0;
    virtual void SetVibration(u32 controllerId, f32 strength) = 0;
    
    // Keyboard/Mouse support
    virtual bool IsKeyPressed(KeyCode key) = 0;
    virtual bool IsMouseButtonPressed(MouseButton button) = 0;
    virtual void GetMousePosition(s32* x, s32* y) = 0;
    virtual void GetMouseDelta(s32* deltaX, s32* deltaY) = 0;
};

// Input Backend Factory
class InputBackendFactory {
public:
    enum class BackendType {
        SDL_Input,
        DirectInput,
        XInput,
        Raw_Input
    };
    
    static std::unique_ptr<InputBackend> CreateBackend(BackendType type);
    static std::vector<BackendType> GetAvailableBackends();
    static BackendType GetRecommendedBackend();
};
```

#### **SDL Input Backend Implementation**

```cpp
class SDLInputBackend : public InputBackend {
private:
    struct ControllerState {
        SDL_GameController* controller;
        SDL_Joystick* joystick;
        InputMapping mapping;
        f32 deadzone;
        bool isConnected;
        
        // N64 button mapping
        OSContPad currentPad;
        OSContPad previousPad;
        
        // Vibration
        f32 vibrationStrength;
        u32 vibrationDuration;
    };
    
    std::array<ControllerState, 4> controllers;
    std::unordered_map<SDL_Keycode, KeyCode> keyMapping;
    
public:
    void Initialize() override;
    void Update() override;
    void GetControllerData(OSContPad* pad) override;
    void SetControllerMapping(u32 controllerId, const InputMapping& mapping) override;
    
private:
    void UpdateController(u32 controllerId);
    void MapControllerInput(u32 controllerId, const SDL_GameController* controller);
    void ProcessKeyboardInput();
    void ProcessMouseInput();
    f32 ApplyDeadzone(f32 value, f32 deadzone);
    u16 MapAnalogStick(f32 x, f32 y);
};
```

### **Memory Management Architecture**

#### **Modern Memory System**

```cpp
class MemoryManager {
private:
    struct MemoryArena {
        void* baseAddress;
        size_t size;
        size_t used;
        size_t alignment;
        std::mutex mutex;
        
        // Free block tracking
        std::vector<MemoryBlock> freeBlocks;
        std::vector<MemoryBlock> usedBlocks;
    };
    
    std::vector<MemoryArena> arenas;
    std::unordered_map<void*, MemoryArena*> allocations;
    
public:
    MemoryManager();
    ~MemoryManager();
    
    // Arena management
    void InitializeArena(size_t size, size_t alignment = 16);
    void ShutdownArena(size_t arenaId);
    
    // Memory allocation (N64 compatible)
    void* AllocateMemory(size_t size, size_t alignment = 16);
    void* ReallocateMemory(void* ptr, size_t newSize);
    void FreeMemory(void* ptr);
    
    // N64 compatibility functions
    void* osVirtualToPhysical(void* virtualAddr);
    void* osPhysicalToVirtual(void* physicalAddr);
    void osInvalDCache(void* addr, size_t size);
    void osWritebackDCache(void* addr, size_t size);
    
    // Memory debugging
    void CheckMemoryIntegrity();
    void PrintMemoryStats();
    size_t GetUsedMemory();
    size_t GetFreeMemory();
    
private:
    MemoryArena* FindArenaForAddress(void* address);
    void CoalesceFreeBLocks(MemoryArena& arena);
    void SplitFreeBlock(MemoryArena& arena, size_t blockIndex, size_t size);
};
```

---

## 1.3.2 Platform Abstraction Design 🔄

### **Cross-Platform File I/O Layer**

#### **File System Abstraction**

```cpp
class FileSystem {
public:
    virtual ~FileSystem() = default;
    
    // File operations
    virtual FileHandle OpenFile(const std::string& path, FileMode mode) = 0;
    virtual void CloseFile(FileHandle handle) = 0;
    virtual size_t ReadFile(FileHandle handle, void* buffer, size_t size) = 0;
    virtual size_t WriteFile(FileHandle handle, const void* buffer, size_t size) = 0;
    virtual void SeekFile(FileHandle handle, size_t offset, SeekOrigin origin) = 0;
    virtual size_t GetFileSize(FileHandle handle) = 0;
    
    // Directory operations
    virtual bool DirectoryExists(const std::string& path) = 0;
    virtual bool CreateDirectory(const std::string& path) = 0;
    virtual std::vector<std::string> ListDirectory(const std::string& path) = 0;
    
    // Path utilities
    virtual std::string GetExecutablePath() = 0;
    virtual std::string GetUserDataPath() = 0;
    virtual std::string GetConfigPath() = 0;
    virtual std::string JoinPath(const std::string& path1, const std::string& path2) = 0;
    
    // N64 DMA compatibility
    virtual void StartDMA(u32 romAddr, void* ramAddr, size_t size, DMAPriority priority) = 0;
    virtual bool IsDMAComplete() = 0;
    virtual void WaitForDMA() = 0;
};

// Platform-specific implementations
class WindowsFileSystem : public FileSystem { /* ... */ };
class LinuxFileSystem : public FileSystem { /* ... */ };
class macOSFileSystem : public FileSystem { /* ... */ };
```

#### **Asset Loading System**

*Following Ship of Harkinian's OTR asset approach*

```cpp
class AssetManager {
private:
    struct AssetCache {
        std::unordered_map<std::string, std::shared_ptr<Asset>> cache;
        std::mutex cacheMutex;
        size_t maxCacheSize;
        size_t currentCacheSize;
    };
    
    AssetCache cache;
    std::unique_ptr<FileSystem> fileSystem;
    std::vector<std::unique_ptr<AssetLoader>> loaders;
    
public:
    AssetManager(std::unique_ptr<FileSystem> fs);
    
    // Asset loading
    template<typename T>
    std::shared_ptr<T> LoadAsset(const std::string& path);
    
    void UnloadAsset(const std::string& path);
    void UnloadAllAssets();
    
    // Asset streaming
    void PreloadAsset(const std::string& path);
    void SetAssetPriority(const std::string& path, AssetPriority priority);
    
    // N64 DMA compatibility
    void LoadROMAsset(u32 romAddr, void* buffer, size_t size);
    
    // Cache management
    void SetCacheSize(size_t maxSize);
    void FlushCache();
    
private:
    void EvictLeastRecentlyUsed();
    std::shared_ptr<Asset> LoadAssetInternal(const std::string& path);
    AssetLoader* FindLoader(const std::string& path);
};
```

### **Window Management System**

#### **Cross-Platform Window Abstraction**

```cpp
class WindowManager {
public:
    virtual ~WindowManager() = default;
    
    // Window creation/destruction
    virtual WindowHandle CreateWindow(const WindowConfig& config) = 0;
    virtual void DestroyWindow(WindowHandle handle) = 0;
    
    // Window properties
    virtual void SetWindowTitle(WindowHandle handle, const std::string& title) = 0;
    virtual void SetWindowSize(WindowHandle handle, u32 width, u32 height) = 0;
    virtual void SetWindowPosition(WindowHandle handle, s32 x, s32 y) = 0;
    virtual void SetWindowFullscreen(WindowHandle handle, bool fullscreen) = 0;
    
    // Window state
    virtual bool IsWindowClosed(WindowHandle handle) = 0;
    virtual bool IsWindowMinimized(WindowHandle handle) = 0;
    virtual bool IsWindowFocused(WindowHandle handle) = 0;
    
    // Event handling
    virtual void PollEvents() = 0;
    virtual void SetEventCallback(WindowHandle handle, EventCallback callback) = 0;
    
    // N64 VI compatibility
    virtual void SetVideoMode(const VideoMode& mode) = 0;
    virtual void SwapBuffers(WindowHandle handle) = 0;
    virtual void SetBlankScreen(bool blank) = 0;
    
    // Graphics integration
    virtual void* GetNativeWindowHandle(WindowHandle handle) = 0;
    virtual void* GetNativeDisplayHandle() = 0;
};

// SDL Window Manager Implementation
class SDLWindowManager : public WindowManager {
private:
    struct WindowState {
        SDL_Window* window;
        SDL_GLContext glContext;
        WindowConfig config;
        EventCallback eventCallback;
        bool isFullscreen;
        bool isMinimized;
        bool isFocused;
    };
    
    std::unordered_map<WindowHandle, WindowState> windows;
    bool isInitialized;
    
public:
    SDLWindowManager();
    ~SDLWindowManager();
    
    WindowHandle CreateWindow(const WindowConfig& config) override;
    void PollEvents() override;
    void SwapBuffers(WindowHandle handle) override;
    
private:
    void InitializeSDL();
    void ShutdownSDL();
    void ProcessSDLEvent(const SDL_Event& event, WindowHandle handle);
    void UpdateWindowState(WindowHandle handle);
};
```

### **Configuration and Settings System**

#### **Configuration Manager**

```cpp
class ConfigurationManager {
private:
    struct ConfigValue {
        std::string value;
        ConfigType type;
        std::string description;
        std::vector<std::string> validValues;
        bool isModified;
    };
    
    std::unordered_map<std::string, ConfigValue> config;
    std::string configFilePath;
    std::mutex configMutex;
    
public:
    ConfigurationManager(const std::string& configPath);
    
    // Configuration loading/saving
    void LoadConfiguration();
    void SaveConfiguration();
    void ResetToDefaults();
    
    // Value access
    template<typename T>
    T GetValue(const std::string& key, const T& defaultValue = T{});
    
    template<typename T>
    void SetValue(const std::string& key, const T& value);
    
    // Configuration validation
    bool IsValidValue(const std::string& key, const std::string& value);
    std::vector<std::string> GetValidValues(const std::string& key);
    
    // Change notifications
    void RegisterChangeCallback(const std::string& key, ConfigChangeCallback callback);
    void UnregisterChangeCallback(const std::string& key);
    
    // N64 specific settings
    void SetVideoMode(const VideoMode& mode);
    void SetAudioFrequency(u32 frequency);
    void SetControllerMapping(u32 controller, const InputMapping& mapping);
    
private:
    void NotifyConfigChange(const std::string& key, const std::string& oldValue, const std::string& newValue);
    void ParseConfigFile(const std::string& content);
    std::string SerializeConfig();
};
```

#### **Settings Categories**

```cpp
// Graphics Settings
struct GraphicsSettings {
    BackendType renderer;
    u32 windowWidth;
    u32 windowHeight;
    bool fullscreen;
    bool vsync;
    u32 msaaSamples;
    f32 renderScale;
    bool widescreenHack;
    
    void LoadFromConfig(ConfigurationManager& config);
    void SaveToConfig(ConfigurationManager& config);
};

// Audio Settings
struct AudioSettings {
    BackendType audioBackend;
    u32 frequency;
    u32 bufferSize;
    f32 masterVolume;
    f32 musicVolume;
    f32 sfxVolume;
    bool enableSurround;
    
    void LoadFromConfig(ConfigurationManager& config);
    void SaveToConfig(ConfigurationManager& config);
};

// Input Settings
struct InputSettings {
    std::array<InputMapping, 4> controllerMappings;
    std::array<f32, 4> deadzoneSizes;
    bool enableKeyboard;
    bool enableMouse;
    MouseSensitivity mouseSensitivity;
    
    void LoadFromConfig(ConfigurationManager& config);
    void SaveToConfig(ConfigurationManager& config);
};
```

---

## 1.3.3 System Integration Architecture ✅

### **Application Framework Architecture**

#### **Core Application Structure**

```cpp
class OOTNativeApplication {
private:
    // Core systems
    std::unique_ptr<GraphicsBackend> graphics;
    std::unique_ptr<AudioBackend> audio;
    std::unique_ptr<InputBackend> input;
    std::unique_ptr<WindowManager> windowManager;
    std::unique_ptr<FileSystem> fileSystem;
    std::unique_ptr<AssetManager> assetManager;
    std::unique_ptr<ConfigurationManager> config;
    std::unique_ptr<MemoryManager> memory;
    
    // Game systems
    std::unique_ptr<GameState> gameState;
    std::unique_ptr<SceneManager> sceneManager;
    std::unique_ptr<ActorManager> actorManager;
    std::unique_ptr<Renderer> renderer;
    
    // Threading
    std::unique_ptr<ThreadPool> threadPool;
    std::unique_ptr<TaskScheduler> scheduler;
    
    // Application state
    bool isRunning;
    bool isPaused;
    f64 deltaTime;
    u64 frameCount;
    
public:
    OOTNativeApplication();
    ~OOTNativeApplication();
    
    // Lifecycle
    bool Initialize();
    void Run();
    void Shutdown();
    
    // System access
    GraphicsBackend* GetGraphics() { return graphics.get(); }
    AudioBackend* GetAudio() { return audio.get(); }
    InputBackend* GetInput() { return input.get(); }
    AssetManager* GetAssets() { return assetManager.get(); }
    ConfigurationManager* GetConfig() { return config.get(); }
    
private:
    void Update(f64 deltaTime);
    void Render();
    void HandleEvents();
    void InitializeSystems();
    void ShutdownSystems();
};
```

#### **System Communication Architecture**

```cpp
// Event System for decoupled communication
class EventSystem {
private:
    struct EventHandler {
        std::function<void(const Event&)> callback;
        u32 priority;
        bool isActive;
    };
    
    std::unordered_map<EventType, std::vector<EventHandler>> handlers;
    std::queue<Event> eventQueue;
    std::mutex eventMutex;
    
public:
    // Event registration
    void RegisterHandler(EventType type, std::function<void(const Event&)> callback, u32 priority = 0);
    void UnregisterHandler(EventType type, std::function<void(const Event&)> callback);
    
    // Event dispatching
    void DispatchEvent(const Event& event);
    void QueueEvent(const Event& event);
    void ProcessQueuedEvents();
    
    // Immediate events
    void BroadcastEvent(const Event& event);
    
private:
    void SortHandlersByPriority(std::vector<EventHandler>& handlers);
};

// Service Locator for system dependencies
class ServiceLocator {
private:
    static std::unordered_map<std::type_index, std::shared_ptr<void>> services;
    static std::mutex servicesMutex;
    
public:
    template<typename T>
    static void RegisterService(std::shared_ptr<T> service);
    
    template<typename T>
    static std::shared_ptr<T> GetService();
    
    template<typename T>
    static void UnregisterService();
    
    static void ClearAllServices();
};
```

#### **Thread-Safe System Communication**

```cpp
// Message passing system for cross-thread communication
class MessageBus {
private:
    struct MessageQueue {
        std::queue<Message> messages;
        std::mutex mutex;
        std::condition_variable condition;
        std::atomic<bool> isActive;
    };
    
    std::unordered_map<ThreadId, MessageQueue> queues;
    std::thread processingThread;
    std::atomic<bool> isRunning;
    
public:
    MessageBus();
    ~MessageBus();
    
    // Queue management
    void CreateQueue(ThreadId threadId);
    void DestroyQueue(ThreadId threadId);
    
    // Message sending
    void SendMessage(ThreadId target, const Message& message);
    void BroadcastMessage(const Message& message);
    void SendDelayedMessage(ThreadId target, const Message& message, u32 delayMs);
    
    // Message receiving
    bool ReceiveMessage(ThreadId threadId, Message& message);
    std::vector<Message> ReceiveAllMessages(ThreadId threadId);
    
    // System lifecycle
    void StartProcessing();
    void StopProcessing();
    
private:
    void ProcessMessages();
    void DeliverMessage(ThreadId target, const Message& message);
};
```

### **libultra Compatibility Layer Integration**

#### **API Compatibility Manager**

```cpp
class LibultraCompatibilityLayer {
private:
    // System references
    GraphicsBackend* graphics;
    AudioBackend* audio;
    InputBackend* input;
    MemoryManager* memory;
    ThreadManager* threads;
    
    // N64 state simulation
    struct N64State {
        OSTime systemTime;
        OSViMode currentViMode;
        OSContStatus controllerStatus[4];
        OSContPad controllerData[4];
        
        // Threading state
        std::unordered_map<OSId, std::unique_ptr<OSThread>> threads;
        std::unordered_map<OSMesgQueue*, std::unique_ptr<MessageQueue>> messageQueues;
        
        // Graphics state
        u32 frameBuffer[2];
        u32 currentFrameBuffer;
        
        // Audio state
        u32 audioFrequency;
        u32 audioBufferSize;
    };
    
    N64State n64State;
    
public:
    LibultraCompatibilityLayer(GraphicsBackend* gfx, AudioBackend* aud, InputBackend* inp, MemoryManager* mem);
    
    // System initialization
    void Initialize();
    void Shutdown();
    
    // N64 function implementations
    void osViSetMode(OSViMode* mode);
    void osViSwapBuffer(void* framebuffer);
    void osViBlack(u8 active);
    OSTime osGetTime();
    void osSetTime(OSTime time);
    
    // Controller functions
    s32 osContInit(OSMesgQueue* mq, u8* bitpattern, OSContStatus* data);
    s32 osContStartReadData(OSMesgQueue* mq);
    void osContGetReadData(OSContPad* data);
    
    // Audio functions
    s32 osAiSetFrequency(u32 frequency);
    s32 osAiSetNextBuffer(void* buffer, u32 size);
    u32 osAiGetLength();
    u32 osAiGetStatus();
    
    // Threading functions
    void osCreateThread(OSThread* thread, OSId id, void (*entry)(void*), void* arg, void* sp, OSPri pri);
    void osStartThread(OSThread* thread);
    void osStopThread(OSThread* thread);
    void osDestroyThread(OSThread* thread);
    
    // Message queue functions
    void osCreateMesgQueue(OSMesgQueue* mq, OSMesg* msg, s32 count);
    s32 osSendMesg(OSMesgQueue* mq, OSMesg msg, s32 flag);
    s32 osRecvMesg(OSMesgQueue* mq, OSMesg* msg, s32 flag);
    
    // Memory functions
    void osInvalDCache(void* vaddr, s32 nbytes);
    void osWritebackDCache(void* vaddr, s32 nbytes);
    u32 osVirtualToPhysical(void* vaddr);
    
private:
    void UpdateN64State();
    void SyncWithModernSystems();
    OSThread* FindThread(OSId id);
    MessageQueue* FindMessageQueue(OSMesgQueue* mq);
};
```

---

## 1.3.4 Performance Optimization Strategy ✅

### **Rendering Performance Architecture**

#### **GPU Performance Optimization**

```cpp
class RenderingOptimizer {
private:
    struct OptimizationState {
        // Frame timing
        f64 frameTime;
        f64 averageFrameTime;
        u32 frameCount;
        
        // GPU metrics
        u32 drawCalls;
        u32 vertices;
        u32 triangles;
        u32 textureBinds;
        u32 stateChanges;
        
        // Optimization flags
        bool enableFrustumCulling;
        bool enableOcclusionCulling;
        bool enableInstancing;
        bool enableLOD;
        bool enableTexureStreaming;
    };
    
    OptimizationState state;
    GraphicsBackend* graphics;
    
public:
    RenderingOptimizer(GraphicsBackend* gfx);
    
    // Frame optimization
    void BeginFrame();
    void EndFrame();
    void OptimizeFrame();
    
    // Culling systems
    void EnableFrustumCulling(bool enable);
    void EnableOcclusionCulling(bool enable);
    void PerformCulling(const CameraData& camera, std::vector<RenderObject>& objects);
    
    // LOD system
    void EnableLOD(bool enable);
    void UpdateLOD(const CameraData& camera, std::vector<RenderObject>& objects);
    
    // Batching system
    void EnableInstancing(bool enable);
    void BatchRenderObjects(std::vector<RenderObject>& objects);
    
    // Texture streaming
    void EnableTextureStreaming(bool enable);
    void UpdateTextureStreaming(const CameraData& camera);
    
    // Performance metrics
    f64 GetFrameTime() const { return state.frameTime; }
    f64 GetAverageFrameTime() const { return state.averageFrameTime; }
    u32 GetDrawCalls() const { return state.drawCalls; }
    
private:
    void UpdateMetrics();
    void ApplyOptimizations();
    bool IsObjectInFrustum(const RenderObject& object, const CameraData& camera);
    f32 CalculateLODDistance(const RenderObject& object, const CameraData& camera);
};
```

#### **CPU Performance Optimization**

```cpp
class CPUOptimizer {
private:
    struct ProfileData {
        std::string name;
        f64 totalTime;
        f64 averageTime;
        f64 maxTime;
        u32 callCount;
        
        std::chrono::high_resolution_clock::time_point startTime;
        bool isActive;
    };
    
    std::unordered_map<std::string, ProfileData> profiles;
    std::mutex profileMutex;
    
public:
    // Profiling
    void BeginProfile(const std::string& name);
    void EndProfile(const std::string& name);
    void ResetProfiles();
    
    // Performance monitoring
    f64 GetProfileTime(const std::string& name);
    f64 GetAverageProfileTime(const std::string& name);
    void PrintProfileReport();
    
    // CPU optimization
    void OptimizeGameLoop();
    void OptimizeMemoryAccess();
    void OptimizeAssetLoading();
    
    // Thread optimization
    void OptimizeThreadDistribution();
    void EnableJobSystem(bool enable);
    
private:
    void UpdateProfileData(const std::string& name, f64 elapsedTime);
    void AnalyzeBottlenecks();
    void SuggestOptimizations();
};

// RAII Profiler for easy profiling
class ScopedProfiler {
private:
    std::string profileName;
    CPUOptimizer* optimizer;
    
public:
    ScopedProfiler(const std::string& name, CPUOptimizer* opt)
        : profileName(name), optimizer(opt) {
        optimizer->BeginProfile(profileName);
    }
    
    ~ScopedProfiler() {
        optimizer->EndProfile(profileName);
    }
};

#define PROFILE_SCOPE(name) ScopedProfiler prof(name, GetCPUOptimizer())
```

### **Memory Performance Architecture**

#### **Memory Pool System**

```cpp
class MemoryPoolManager {
private:
    struct MemoryPool {
        void* baseAddress;
        size_t blockSize;
        size_t blockCount;
        size_t alignment;
        
        std::vector<bool> usedBlocks;
        std::stack<size_t> freeBlocks;
        std::mutex poolMutex;
        
        // Performance metrics
        u32 allocations;
        u32 deallocations;
        u32 peakUsage;
        f64 fragmentation;
    };
    
    std::vector<MemoryPool> pools;
    std::unordered_map<void*, size_t> allocationToPool;
    
public:
    // Pool management
    void CreatePool(size_t blockSize, size_t blockCount, size_t alignment = 16);
    void DestroyPool(size_t poolId);
    void ResetPool(size_t poolId);
    
    // Allocation
    void* AllocateFromPool(size_t size);
    void DeallocateFromPool(void* ptr);
    
    // Performance monitoring
    void UpdateFragmentation();
    f64 GetFragmentation(size_t poolId);
    u32 GetPeakUsage(size_t poolId);
    void PrintMemoryReport();
    
    // Optimization
    void OptimizeMemoryLayout();
    void DefragmentPools();
    
private:
    size_t FindBestPool(size_t size);
    void CoalesceBlocks(MemoryPool& pool);
    void CompactPool(MemoryPool& pool);
};
```

### **Asset Loading Performance**

#### **Streaming System**

```cpp
class AssetStreamingManager {
private:
    struct StreamingGroup {
        std::string name;
        std::vector<std::string> assets;
        AssetPriority priority;
        f32 streamingDistance;
        bool isLoaded;
        bool isLoading;
        
        std::future<void> loadingTask;
    };
    
    std::vector<StreamingGroup> groups;
    std::unordered_map<std::string, size_t> assetToGroup;
    
    ThreadPool* threadPool;
    AssetManager* assetManager;
    
    // Performance metrics
    u32 streamingRequests;
    u32 streamingCompletions;
    f64 averageLoadTime;
    
public:
    AssetStreamingManager(ThreadPool* pool, AssetManager* assets);
    
    // Streaming groups
    void CreateStreamingGroup(const std::string& name, const std::vector<std::string>& assets, 
                             AssetPriority priority, f32 distance);
    void DestroyStreamingGroup(const std::string& name);
    
    // Streaming operations
    void RequestStreaming(const std::string& groupName);
    void CancelStreaming(const std::string& groupName);
    void UpdateStreaming(const Vector3& position);
    
    // Performance monitoring
    bool IsStreamingComplete(const std::string& groupName);
    f64 GetAverageLoadTime() const { return averageLoadTime; }
    u32 GetActiveStreamingRequests();
    
private:
    void StreamGroup(StreamingGroup& group);
    void UnloadGroup(StreamingGroup& group);
    f32 CalculateDistance(const Vector3& position, const StreamingGroup& group);
    void UpdateMetrics();
};
```

---

## 1.3.5 Error Handling and Debugging Architecture ✅

### **Error Handling System**

#### **Exception Management**

```cpp
class ErrorManager {
public:
    enum class ErrorLevel {
        Info,
        Warning,
        Error,
        Critical
    };
    
    enum class ErrorCategory {
        Graphics,
        Audio,
        Input,
        Memory,
        FileSystem,
        Network,
        Game,
        System
    };
    
private:
    struct ErrorEntry {
        ErrorLevel level;
        ErrorCategory category;
        std::string message;
        std::string file;
        u32 line;
        std::string function;
        std::chrono::system_clock::time_point timestamp;
        
        std::string stackTrace;
        std::unordered_map<std::string, std::string> context;
    };
    
    std::vector<ErrorEntry> errorLog;
    std::mutex errorMutex;
    
    // Error callbacks
    std::unordered_map<ErrorLevel, std::vector<std::function<void(const ErrorEntry&)>>> callbacks;
    
public:
    // Error reporting
    void ReportError(ErrorLevel level, ErrorCategory category, const std::string& message,
                    const std::string& file, u32 line, const std::string& function);
    
    void ReportException(const std::exception& e, const std::string& file, u32 line, const std::string& function);
    
    // Error handling
    void RegisterErrorCallback(ErrorLevel level, std::function<void(const ErrorEntry&)> callback);
    void UnregisterErrorCallback(ErrorLevel level);
    
    // Error querying
    std::vector<ErrorEntry> GetErrors(ErrorLevel minLevel = ErrorLevel::Info);
    std::vector<ErrorEntry> GetErrors(ErrorCategory category);
    void ClearErrors();
    
    // Error reporting
    void SaveErrorLog(const std::string& filename);
    void PrintErrorSummary();
    
private:
    void AddError(const ErrorEntry& entry);
    void NotifyCallbacks(const ErrorEntry& entry);
    std::string GetStackTrace();
    void TrimErrorLog();
};

// Error reporting macros
#define REPORT_ERROR(level, category, message) \
    ErrorManager::Instance().ReportError(level, category, message, __FILE__, __LINE__, __FUNCTION__)

#define REPORT_CRITICAL_ERROR(category, message) \
    REPORT_ERROR(ErrorManager::ErrorLevel::Critical, category, message)

#define REPORT_WARNING(category, message) \
    REPORT_ERROR(ErrorManager::ErrorLevel::Warning, category, message)
```

#### **Assert System**

```cpp
class AssertManager {
private:
    static bool assertsEnabled;
    static std::function<void(const std::string&)> assertCallback;
    
public:
    static void EnableAsserts(bool enable);
    static void SetAssertCallback(std::function<void(const std::string&)> callback);
    
    static void HandleAssert(const std::string& condition, const std::string& message,
                           const std::string& file, u32 line, const std::string& function);
    
    static void HandleAssertion(bool condition, const std::string& conditionStr,
                               const std::string& message, const std::string& file,
                               u32 line, const std::string& function);
};

// Assert macros
#ifdef DEBUG
    #define ASSERT(condition, message) \
        AssertManager::HandleAssertion(condition, #condition, message, __FILE__, __LINE__, __FUNCTION__)
    
    #define ASSERT_MSG(condition, message) \
        ASSERT(condition, message)
    
    #define ASSERT_NOT_NULL(ptr) \
        ASSERT(ptr != nullptr, "Null pointer: " #ptr)
    
    #define ASSERT_VALID_RANGE(value, min, max) \
        ASSERT((value >= min) && (value <= max), "Value out of range: " #value)
#else
    #define ASSERT(condition, message)
    #define ASSERT_MSG(condition, message)
    #define ASSERT_NOT_NULL(ptr)
    #define ASSERT_VALID_RANGE(value, min, max)
#endif
```

### **Debugging System**

#### **Debug Console**

```cpp
class DebugConsole {
private:
    struct Command {
        std::string name;
        std::string description;
        std::function<void(const std::vector<std::string>&)> callback;
        std::vector<std::string> parameters;
    };
    
    std::unordered_map<std::string, Command> commands;
    std::vector<std::string> commandHistory;
    std::string currentInput;
    
    bool isVisible;
    bool isEnabled;
    
public:
    DebugConsole();
    
    // Command management
    void RegisterCommand(const std::string& name, const std::string& description,
                        std::function<void(const std::vector<std::string>&)> callback);
    void UnregisterCommand(const std::string& name);
    
    // Console operations
    void ExecuteCommand(const std::string& command);
    void Print(const std::string& message);
    void PrintError(const std::string& message);
    void PrintWarning(const std::string& message);
    
    // Console state
    void SetVisible(bool visible);
    bool IsVisible() const { return isVisible; }
    void SetEnabled(bool enabled);
    bool IsEnabled() const { return isEnabled; }
    
    // Input handling
    void HandleInput(const std::string& input);
    void HandleKeyPress(KeyCode key);
    
    // Built-in commands
    void RegisterBuiltinCommands();
    
private:
    void ParseCommand(const std::string& input, std::string& command, std::vector<std::string>& args);
    void ExecuteBuiltinCommand(const std::string& command, const std::vector<std::string>& args);
    void ShowHelp();
    void ShowCommandHistory();
    void ClearConsole();
};
```

#### **Debug Rendering**

```cpp
class DebugRenderer {
private:
    struct DebugLine {
        Vector3 start;
        Vector3 end;
        Color color;
        f32 duration;
        bool depthTest;
    };
    
    struct DebugSphere {
        Vector3 center;
        f32 radius;
        Color color;
        f32 duration;
        bool wireframe;
    };
    
    struct DebugText {
        std::string text;
        Vector3 position;
        Color color;
        f32 duration;
        f32 size;
    };
    
    std::vector<DebugLine> lines;
    std::vector<DebugSphere> spheres;
    std::vector<DebugText> texts;
    
    GraphicsBackend* graphics;
    bool isEnabled;
    
public:
    DebugRenderer(GraphicsBackend* gfx);
    
    // Debug primitive drawing
    void DrawLine(const Vector3& start, const Vector3& end, const Color& color, f32 duration = 0.0f, bool depthTest = true);
    void DrawSphere(const Vector3& center, f32 radius, const Color& color, f32 duration = 0.0f, bool wireframe = true);
    void DrawBox(const Vector3& min, const Vector3& max, const Color& color, f32 duration = 0.0f);
    void DrawText(const std::string& text, const Vector3& position, const Color& color, f32 duration = 0.0f, f32 size = 1.0f);
    
    // Debug info
    void DrawFPS(const Vector2& position);
    void DrawMemoryInfo(const Vector2& position);
    void DrawPerformanceInfo(const Vector2& position);
    
    // Rendering
    void Update(f32 deltaTime);
    void Render();
    void Clear();
    
    // State
    void SetEnabled(bool enabled);
    bool IsEnabled() const { return isEnabled; }
    
private:
    void UpdateDebugPrimitives(f32 deltaTime);
    void RenderLines();
    void RenderSpheres();
    void RenderTexts();
};
```

### **Performance Profiling**

#### **Profiling System**

```cpp
class ProfilerManager {
private:
    struct ProfileSample {
        std::string name;
        f64 startTime;
        f64 endTime;
        f64 duration;
        u32 frameNumber;
        ThreadId threadId;
        
        std::unordered_map<std::string, std::string> metadata;
    };
    
    struct ProfileGroup {
        std::string name;
        std::vector<ProfileSample> samples;
        f64 totalTime;
        f64 averageTime;
        f64 minTime;
        f64 maxTime;
        u32 sampleCount;
    };
    
    std::unordered_map<std::string, ProfileGroup> groups;
    std::vector<ProfileSample> currentSamples;
    std::mutex profilerMutex;
    
    bool isEnabled;
    u32 currentFrame;
    
public:
    ProfilerManager();
    
    // Profiling control
    void SetEnabled(bool enabled);
    bool IsEnabled() const { return isEnabled; }
    void Reset();
    
    // Profiling operations
    void BeginSample(const std::string& name);
    void EndSample(const std::string& name);
    void AddMetadata(const std::string& key, const std::string& value);
    
    // Data access
    const ProfileGroup& GetGroup(const std::string& name);
    std::vector<std::string> GetGroupNames();
    
    // Reporting
    void GenerateReport(const std::string& filename);
    void PrintReport();
    void SaveProfileData(const std::string& filename);
    
    // Frame management
    void BeginFrame();
    void EndFrame();
    
private:
    void UpdateGroup(const std::string& name, const ProfileSample& sample);
    void CalculateStatistics(ProfileGroup& group);
    f64 GetCurrentTime();
};
```

---

**Phase 1.3 Status**: ✅ **COMPLETED**
- [x] Graphics API abstraction architecture designed
- [x] Audio system replacement architecture designed  
- [x] Input handling system architecture designed
- [x] Memory management system architecture designed
- [x] Cross-platform file I/O layer designed
- [x] Window management system designed
- [x] Configuration and settings system designed
- [x] System integration architecture designed
- [x] Performance optimization strategy designed
- [x] Error handling and debugging architecture designed

**🎯 Phase 1.3 Key Achievements:**
- **Complete Technical Architecture**: Layered abstraction with API compatibility + modern backends
- **Multi-Backend Support**: Graphics (OpenGL/DirectX11/Metal), Audio (SDL/OpenAL), Input (SDL/DirectInput)
- **Performance Optimization**: Rendering optimization, CPU profiling, memory pooling, asset streaming
- **Robust Error Handling**: Exception management, assert system, debug console, debug rendering
- **System Integration**: Event system, service locator, message bus, libultra compatibility layer
- **Production-Ready**: Comprehensive debugging, profiling, and monitoring systems

**Ready for Phase 2**: All foundational architecture is complete - Core systems replacement can begin immediately. 