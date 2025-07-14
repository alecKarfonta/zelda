cmake_minimum_required(VERSION 3.16)
project(oot_native)

set(CMAKE_C_STANDARD 99)
set(CMAKE_CXX_STANDARD 17)

# Find required packages
find_package(OpenGL REQUIRED)

# SDL2 detection - handle both native and cross-compilation
if(WIN32 AND CMAKE_CROSSCOMPILING)
    # Windows cross-compilation - use manually set paths from toolchain
    message(STATUS "Using SDL2 from toolchain: ${SDL2_ROOT}")
    include_directories(${SDL2_INCLUDE_DIR})
    set(SDL2_LIBRARIES ${SDL2_LIBRARY} ${SDL2MAIN_LIBRARY})
else()
    # Native compilation - use pkg-config
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(SDL2 REQUIRED sdl2)
    include_directories(${SDL2_INCLUDE_DIRS})
endif()

# Include directories
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Graphics source files
set(GRAPHICS_SOURCES
    src/graphics/graphics_api.c
    src/graphics/renderer_backend.c
    src/graphics/opengl_backend.c
    src/graphics/opengl_resources.c
    src/graphics/opengl_shaders.c
    src/graphics/n64_graphics.c
    src/glad.c
)

# Audio source files
set(AUDIO_SOURCES
    src/audio/audio_api.c
    src/audio/n64_audio.c
)

# Input source files
set(INPUT_SOURCES
    src/input/input_api.c
    src/input/sdl_input_backend.c
)

# LibUltra compatibility layer source files
set(LIBULTRA_SOURCES
    src/libultra/memory_mgmt.c
    src/libultra/dma_functions.c
    src/libultra/threading.c
    src/libultra/message_system.c
    src/libultra/event_system.c
    src/libultra/timing.c
    src/libultra/libultra_system.c
)

# Test program
add_executable(test_graphics
    src/test_graphics.c
    ${GRAPHICS_SOURCES}
    ${AUDIO_SOURCES}
    ${INPUT_SOURCES}
)

# Force console subsystem for Windows
if(WIN32)
    set_target_properties(test_graphics PROPERTIES
        WIN32_EXECUTABLE FALSE
    )
endif()

# Link libraries
target_link_libraries(test_graphics
    ${OPENGL_LIBRARIES}
    ${SDL2_LIBRARIES}
)

# Platform-specific libraries
if(WIN32)
    target_link_libraries(test_graphics
        mingw32  # MinGW runtime
        ws2_32   # Windows sockets
        winmm    # Windows multimedia
        ole32    # OLE
        oleaut32 # OLE automation
        imm32    # Input method manager
        version  # Version info
    )
else()
    target_link_libraries(test_graphics
        m  # Math library (Unix)
    )
endif()

# Compiler flags
target_compile_options(test_graphics PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
)

# Platform-specific compiler flags
if(NOT WIN32)
    target_compile_options(test_graphics PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# Add debug information
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(test_graphics PRIVATE -g -O0)
else()
    target_compile_options(test_graphics PRIVATE -O2)
endif()

# Additional targets for different test modes
add_custom_target(run_test
    COMMAND ./test_graphics
    DEPENDS test_graphics
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

add_custom_target(run_performance_test
    COMMAND ./test_graphics performance
    DEPENDS test_graphics
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

add_custom_target(run_stress_test
    COMMAND ./test_graphics stress
    DEPENDS test_graphics
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

add_custom_target(run_input_test
    COMMAND ./test_input
    DEPENDS test_input
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

add_custom_target(run_input_interactive_test
    COMMAND ./test_input interactive
    DEPENDS test_input
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

add_custom_target(run_input_rumble_test
    COMMAND ./test_input rumble
    DEPENDS test_input
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

# Audio Test Executable
add_executable(test_audio
    src/test_audio.c
    ${AUDIO_SOURCES}
    ${INPUT_SOURCES}
)
target_link_libraries(test_audio
    ${OPENGL_LIBRARIES}
    ${SDL2_LIBRARIES}
)

# Platform-specific libraries for test_audio
if(WIN32)
    target_link_libraries(test_audio
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(test_audio
        ${CMAKE_DL_LIBS}
        m # math library
    )
endif()

# Input Test Executable
add_executable(test_input
    src/test_input.c
    ${INPUT_SOURCES}
)
target_link_libraries(test_input
    ${SDL2_LIBRARIES}
)

# Platform-specific libraries for test_input
if(WIN32)
    target_link_libraries(test_input
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(test_input
        m # math library
    )
endif()

# Compiler flags for input test
target_compile_options(test_input PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
)

# Platform-specific compiler flags for test_input
if(NOT WIN32)
    target_compile_options(test_input PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# Unified Test Executable
add_executable(test_unified
    src/test_unified.c
    ${GRAPHICS_SOURCES}
    ${AUDIO_SOURCES}
    ${INPUT_SOURCES}
)

# Force console subsystem for Windows
if(WIN32)
    set_target_properties(test_unified PROPERTIES
        WIN32_EXECUTABLE FALSE
        LINK_FLAGS "-Wl,--subsystem,console"
    )
endif()

# Link libraries
target_link_libraries(test_unified
    ${OPENGL_LIBRARIES}
    ${SDL2_LIBRARIES}
)

# Platform-specific libraries for test_unified
if(WIN32)
    target_link_libraries(test_unified
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(test_unified
        ${CMAKE_DL_LIBS}
        m # math library
    )
endif()

# Compiler flags for unified test
target_compile_options(test_unified PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
)

# Platform-specific compiler flags for test_unified
if(NOT WIN32)
    target_compile_options(test_unified PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# LibUltra Test Executable
add_executable(test_libultra
    src/test_libultra.c
    ${LIBULTRA_SOURCES}
)

# Force console subsystem for Windows
if(WIN32)
    set_target_properties(test_libultra PROPERTIES
        WIN32_EXECUTABLE FALSE
        LINK_FLAGS "-Wl,--subsystem,console"
    )
endif()

# Link libraries for libultra test
target_link_libraries(test_libultra
    pthread  # POSIX threads
)

# Platform-specific libraries for test_libultra
if(WIN32)
    target_link_libraries(test_libultra
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(test_libultra
        ${CMAKE_DL_LIBS}
        m # math library
        rt # real-time extensions (for clock_gettime)
    )
endif()

# Compiler flags for libultra test
target_compile_options(test_libultra PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
    -pthread  # Enable pthread support
)

# Add custom target to run libultra tests
add_custom_target(run_libultra_test
    COMMAND ./test_libultra
    DEPENDS test_libultra
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
)

# Main Native Game Loop (OOT Integration Foundation)
add_executable(main_native
    src/main_native.c
    ${GRAPHICS_SOURCES}
    ${AUDIO_SOURCES}
    ${INPUT_SOURCES}
    ${LIBULTRA_SOURCES}
)

# Force console subsystem for Windows
if(WIN32)
    set_target_properties(main_native PROPERTIES
        WIN32_EXECUTABLE FALSE
        LINK_FLAGS "-Wl,--subsystem,console"
    )
endif()

# Link libraries for main_native
target_link_libraries(main_native
    ${OPENGL_LIBRARIES}
    ${SDL2_LIBRARIES}
    pthread  # POSIX threads
)

# Platform-specific libraries for main_native
if(WIN32)
    target_link_libraries(main_native
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(main_native
        ${CMAKE_DL_LIBS}
        m # math library
        rt # real-time extensions (for clock_gettime)
    )
endif()

# Compiler flags for main_native
target_compile_options(main_native PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
    -pthread  # Enable pthread support
)

# Platform-specific compiler flags for main_native
if(NOT WIN32)
    target_compile_options(main_native PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# Simplified Native Game Loop Test (LibUltra integration only)
add_executable(main_native_simple
    src/main_native_simple.c
    ${LIBULTRA_SOURCES}
)

# Advanced Native Game Loop Test (with all systems once OpenGL is fixed)
add_executable(main_native_test
    src/main_native_simple.c
    ${AUDIO_SOURCES}
    ${INPUT_SOURCES}
    ${LIBULTRA_SOURCES}
)

# Force console subsystem for Windows
if(WIN32)
    set_target_properties(main_native_simple PROPERTIES
        WIN32_EXECUTABLE FALSE
        LINK_FLAGS "-Wl,--subsystem,console"
    )
endif()

# Link libraries for main_native_simple
target_link_libraries(main_native_simple
    ${SDL2_LIBRARIES}
    pthread  # POSIX threads
)

# Platform-specific libraries for main_native_simple
if(WIN32)
    target_link_libraries(main_native_simple
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(main_native_simple
        ${CMAKE_DL_LIBS}
        m # math library
        rt # real-time extensions (for clock_gettime)
    )
endif()

# Compiler flags for main_native_simple
target_compile_options(main_native_simple PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
    -pthread  # Enable pthread support
)

# Platform-specific compiler flags for main_native_simple
if(NOT WIN32)
    target_compile_options(main_native_simple PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# Link libraries for main_native_test (audio + input + libultra)
target_link_libraries(main_native_test
    ${SDL2_LIBRARIES}
    pthread  # POSIX threads
)

# Platform-specific libraries for main_native_test
if(WIN32)
    target_link_libraries(main_native_test
        mingw32 ws2_32 winmm ole32 oleaut32 imm32 version
    )
else()
    target_link_libraries(main_native_test
        ${CMAKE_DL_LIBS}
        m # math library
        rt # real-time extensions (for clock_gettime)
    )
endif()

# Compiler flags for main_native_test
target_compile_options(main_native_test PRIVATE
    -Wall
    -Wextra
    -Wno-unused-parameter
    -Wno-unused-variable
    -Wno-unused-function
    -pthread  # Enable pthread support
)

# Platform-specific compiler flags for main_native_test
if(NOT WIN32)
    target_compile_options(main_native_test PRIVATE ${SDL2_CFLAGS_OTHER})
endif()

# Installation
install(TARGETS test_graphics test_audio test_input test_unified test_libultra main_native main_native_simple main_native_test
    RUNTIME DESTINATION bin
)

# Print configuration info
message(STATUS "OOT Native Graphics Test Configuration:")
message(STATUS "  OpenGL Libraries: ${OPENGL_LIBRARIES}")
message(STATUS "  SDL2 Libraries: ${SDL2_LIBRARIES}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C Standard: ${CMAKE_C_STANDARD}")
message(STATUS "  CXX Standard: ${CMAKE_CXX_STANDARD}") 