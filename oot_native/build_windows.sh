#!/bin/bash

echo "=== OOT Native Windows Cross-Compilation Build Script ==="

# Set build configuration
BUILD_TYPE=${1:-Release}
BUILD_DIR="build_windows"

echo "Build type: $BUILD_TYPE"
echo "Build directory: $BUILD_DIR"

# Clean previous build
if [ -d "$BUILD_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
fi

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with Windows toolchain
echo "Configuring for Windows x64..."
cmake \
    -DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/windows-x64.cmake \
    -DCMAKE_BUILD_TYPE=$BUILD_TYPE \
    -DCMAKE_VERBOSE_MAKEFILE=ON \
    ..

if [ $? -ne 0 ]; then
    echo "❌ CMake configuration failed!"
    exit 1
fi

# Build
echo "Building Windows executables..."
make -j$(nproc)

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ Windows build completed successfully!"

# Copy SDL2.dll to build directory
echo "Copying SDL2.dll..."
cp ../deps/windows/SDL2/x86_64-w64-mingw32/bin/SDL2.dll .

# List generated executables
echo ""
echo "Generated Windows executables:"
ls -la *.exe

echo ""
echo "📦 Windows build is ready!"
echo "Copy the following files to Windows:"
echo "  - *.exe (executables)"
echo "  - SDL2.dll (required runtime)"
echo ""
echo "Usage on Windows:"
echo "  test_graphics.exe"
echo "  test_graphics.exe performance"
echo "  test_graphics.exe stress"
echo "  test_input.exe"
echo "  test_input.exe interactive"
echo "  test_audio.exe" 