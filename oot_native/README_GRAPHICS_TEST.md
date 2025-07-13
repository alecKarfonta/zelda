# OOT Native Graphics Test

## Overview

This test program validates the graphics implementation for the OOT Native project. It demonstrates that the complete rendering pipeline works correctly, from N64 graphics commands to actual triangle rendering on screen.

## What's Implemented

✅ **Complete Graphics Pipeline**:
- OpenGL backend with all function pointers connected
- N64 graphics command processing (G_TRI1, G_TRI2, G_QUAD, G_VTX, G_SETPRIMCOLOR, etc.)
- Vertex batching system for efficient rendering
- Shader system with N64-compatible vertex/fragment shaders
- Full rendering state management

✅ **Test Features**:
- Interactive window showing colored triangles
- Performance testing (1000 frames)
- Stress testing (100 triangles per frame)
- Real-time graphics stats and debugging

## Prerequisites

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install libsdl2-dev libgl1-mesa-dev
```

### Fedora/RHEL
```bash
sudo dnf install cmake gcc make pkg-config
sudo dnf install SDL2-devel mesa-libGL-devel
```

### Arch Linux
```bash
sudo pacman -S cmake gcc make pkg-config
sudo pacman -S sdl2 mesa
```

## Building and Running

### Quick Start
```bash
cd oot_native
chmod +x build.sh
./build.sh
```

### Manual Build
```bash
cd oot_native
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Debug ..
make -j$(nproc)
```

### Running Tests

#### Interactive Test (Default)
```bash
./test_graphics
```
- Shows a window with three colored triangles (red, green, blue)
- Press **ESC** to exit
- Real-time rendering using the complete graphics pipeline

#### Performance Test
```bash
./test_graphics performance
```
- Renders 1000 frames and measures FPS
- Tests sustained performance of the graphics system
- Outputs: frame time, average FPS, total render time

#### Stress Test
```bash
./test_graphics stress
```
- Renders 100 triangles per frame for 60 frames
- Tests vertex batching system performance
- Outputs: triangles per second, total triangles rendered

## What You Should See

### Interactive Test
- **Window**: 800x600 OpenGL window with blue background
- **Triangles**: Three colored triangles arranged horizontally
  - Red triangle (center)
  - Green triangle (right)
  - Blue triangle (left)
- **Console Output**: 
  - OpenGL version and renderer info
  - Graphics system initialization messages
  - Triangle submission confirmations

### Performance Test
```
=== PERFORMANCE TEST ===
Rendered 1000 frames in 16.67 seconds
Average FPS: 60.00
Frame time: 16.67 ms
```

### Stress Test
```
=== STRESS TEST ===
Stress test: 100 triangles per frame for 60 frames
Total triangles rendered: 6000
Time taken: 1.00 seconds
Triangles per second: 6000
```

## Expected Console Output

```
=== OOT Native Graphics Test ===
SDL and OpenGL initialized successfully
OpenGL Version: 4.6.0 NVIDIA 535.154.05
OpenGL Vendor: NVIDIA Corporation
OpenGL Renderer: NVIDIA GeForce RTX 3080/PCIe/SSE2
Graphics system initialized successfully
Compiled vertex shader successfully
Compiled fragment shader successfully
Linked shader program successfully
Loaded default shaders successfully
Shader manager initialized successfully
Initialized vertex batch system
N64 graphics system initialized
Starting main loop - press ESC to exit
```

## Architecture Validation

This test validates the complete graphics architecture:

1. **SDL2 Window Creation** → OpenGL context setup
2. **Graphics API Initialization** → Backend creation and setup
3. **N64 Graphics System** → Command processing and state management
4. **Shader System** → Vertex/fragment shader compilation and linking
5. **Vertex Batching** → Efficient triangle accumulation and rendering
6. **OpenGL Backend** → All function pointers connected to implementations

## Troubleshooting

### Build Issues

**SDL2 not found**:
```bash
# Ubuntu/Debian
sudo apt-get install libsdl2-dev

# Fedora/RHEL
sudo dnf install SDL2-devel

# Arch
sudo pacman -S sdl2
```

**OpenGL not found**:
```bash
# Ubuntu/Debian
sudo apt-get install libgl1-mesa-dev

# Fedora/RHEL
sudo dnf install mesa-libGL-devel

# Arch
sudo pacman -S mesa
```

### Runtime Issues

**Window doesn't appear**:
- Check that you have a display server running (X11 or Wayland)
- Try running: `export DISPLAY=:0`

**OpenGL errors**:
- Ensure your GPU supports OpenGL 3.3 or higher
- Update your graphics drivers

**No triangles visible**:
- Check console output for shader compilation errors
- Verify that vertex data is being processed

## Testing Integration

This test program demonstrates:
- ✅ Complete graphics pipeline from N64 commands to pixels
- ✅ Proper separation of concerns (N64 → Backend → OpenGL)
- ✅ Efficient vertex batching system
- ✅ Shader compilation and management
- ✅ Multi-platform compatibility

## Next Steps

With this foundation working, you can:
1. **Add texture support** - Load and bind N64 textures
2. **Implement matrix transformations** - Add MVP matrix support
3. **Add more N64 commands** - Rectangle rendering, texture rectangles
4. **Integrate with game data** - Load actual OOT display lists
5. **Add more graphics backends** - DirectX11, Vulkan, Metal

The architecture is solid and ready for these enhancements!

## Performance Expectations

On a modern system, you should see:
- **Interactive Test**: 60+ FPS with VSync enabled
- **Performance Test**: 60+ FPS average over 1000 frames
- **Stress Test**: 5000+ triangles per second

Lower performance indicates potential issues with the graphics pipeline or system configuration.

## Contact/Issues

If you encounter issues:
1. Check the console output for error messages
2. Verify all dependencies are installed
3. Ensure your graphics drivers are up to date
4. Try running with `MESA_DEBUG=1` for additional OpenGL debugging 