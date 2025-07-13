# CMake Toolchain file for Windows x64 cross-compilation using MinGW
# Usage: cmake -DCMAKE_TOOLCHAIN_FILE=cmake/toolchains/windows-x64.cmake ..

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

# Cross-compilation tools
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)

# Target system root
set(CMAKE_FIND_ROOT_PATH 
    /usr/x86_64-w64-mingw32
    ${CMAKE_CURRENT_LIST_DIR}/../../deps/windows/SDL2/x86_64-w64-mingw32
)

# Adjust the default behavior of the FIND_XXX() commands:
# search programs in the host environment
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
# search headers and libraries in the target environment
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

# Windows-specific settings
set(CMAKE_SYSTEM_VERSION 10.0)
set(CMAKE_CROSSCOMPILING TRUE)

# Use static linking to avoid DLL dependencies where possible
set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++")
set(CMAKE_SHARED_LINKER_FLAGS "-static-libgcc -static-libstdc++")

# OpenGL and other Windows libraries
set(OPENGL_LIBRARIES opengl32)

# Windows-specific compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DWIN32 -D_WIN32")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DWIN32 -D_WIN32")

# Ensure we link against Windows console subsystem
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -mconsole -Wl,--subsystem,console")

# Set file extensions
set(CMAKE_EXECUTABLE_SUFFIX ".exe")
set(CMAKE_SHARED_LIBRARY_SUFFIX ".dll")
set(CMAKE_STATIC_LIBRARY_SUFFIX ".a")

# SDL2 specific configuration
set(SDL2_ROOT ${CMAKE_CURRENT_LIST_DIR}/../../deps/windows/SDL2/x86_64-w64-mingw32)
set(SDL2_INCLUDE_DIR ${SDL2_ROOT}/include)
set(SDL2_LIBRARY ${SDL2_ROOT}/lib/libSDL2.dll.a)
set(SDL2MAIN_LIBRARY ${SDL2_ROOT}/lib/libSDL2main.a)
# Include both SDL2 and SDL2main for flexibility
set(SDL2_LIBRARIES ${SDL2_LIBRARY} ${SDL2MAIN_LIBRARY})
set(SDL2_DLL ${SDL2_ROOT}/bin/SDL2.dll)

# Tell CMake where to find SDL2
set(ENV{SDL2DIR} ${SDL2_ROOT}) 