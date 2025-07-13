#!/bin/bash

# OOT Native Graphics Test Build Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== OOT Native Graphics Test Build Script ===${NC}"

# Check if we're in the right directory
if [ ! -f "CMakeLists.txt" ]; then
    echo -e "${RED}Error: CMakeLists.txt not found. Please run this script from the oot_native directory.${NC}"
    exit 1
fi

# Create build directory
BUILD_DIR="build"
if [ ! -d "$BUILD_DIR" ]; then
    echo -e "${YELLOW}Creating build directory...${NC}"
    mkdir -p "$BUILD_DIR"
fi

# Change to build directory
cd "$BUILD_DIR"

# Configure with CMake
echo -e "${YELLOW}Configuring with CMake...${NC}"
cmake -DCMAKE_BUILD_TYPE=Debug ..

# Build the project
echo -e "${YELLOW}Building project...${NC}"
make -j$(nproc)

# Check if build was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "${BLUE}Generated executable: ${BUILD_DIR}/test_graphics${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  ./test_graphics                # Interactive test (shows window with triangles)"
    echo "  ./test_graphics performance    # Performance test (1000 frames)"
    echo "  ./test_graphics stress         # Stress test (100 triangles per frame)"
    echo ""
    echo -e "${YELLOW}Audio Test Suite:${NC}"
    echo "  ./test_audio                   # Run all audio tests (default)"
    echo "  ./test_audio basic             # Run basic functionality tests"
    echo "  ./test_audio playback          # Run audio playback tests"
    echo "  ./test_audio performance       # Run performance benchmarks"
    echo "  ./test_audio interactive       # Run interactive audio test (requires user input)"
    echo ""
    echo -e "${BLUE}You can also use these make targets:${NC}"
    echo "  make run_test                  # Run interactive test"
    echo "  make run_performance_test      # Run performance test"
    echo "  make run_stress_test           # Run stress test"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi 