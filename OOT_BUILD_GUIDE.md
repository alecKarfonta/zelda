# OoT Build and Compilation Testing Guide

## Overview
This guide explains how to set up the full Ocarina of Time decompilation project and test C code compilation with the actual game environment.

## Prerequisites

### Required Tools
```bash
# Install MIPS toolchain
sudo apt update
sudo apt install -y binutils-mips-linux-gnu gcc-mips-linux-gnu

# Install Python dependencies
python3 -m venv oot_env
source oot_env/bin/activate
pip install -r requirements.txt
```

### Required ROM
You need the NTSC 1.2 version of Ocarina of Time ROM:
- File: `oot_rom.v64` (Nintendo 64 ROM format)
- Place in: `oot/baseroms/ntsc-1.2/baserom.v64`

## Building the OoT Project

### 1. Set Up the Build Environment
```bash
cd oot
make setup VERSION=ntsc-1.2
```

### 2. Build the Project
```bash
make VERSION=ntsc-1.2 -j4
```

This will:
- Extract assets from the ROM
- Generate header files and type definitions
- Create the complete build environment
- Compile all source files

### 3. Verify the Build
```bash
# Check that the build completed successfully
ls -la build/ntsc-1.2/

# Verify header files are available
ls -la include/
```

## Testing C Code Compilation

### 1. Run the Compilation Test
```bash
cd ..
python3 test_compilation.py
```

### 2. Analyze Results
The compiler will test all generated C code snippets and provide:
- Success/failure rates
- Detailed error messages
- Compilation reports

### 3. Review Compilation Reports
```bash
# View detailed compilation reports
cat large_generation_20_compilation_report.txt
cat test_generation_5_compilation_report.txt
```

## Understanding Compilation Results

### Success Indicators
- **12.4% success rate** for large dataset
- **9.7% success rate** for test dataset
- Successful compilations indicate code that follows OoT conventions

### Common Error Categories

#### 1. Missing Type Definitions
```
error: unknown type name 'PlayState'
error: unknown type name 'Actor'
error: unknown type name 'EnForestGuard'
```
**Solution**: Include proper OoT headers and type definitions

#### 2. Missing Function Declarations
```
error: implicit declaration of function 'Actor_WorldDistXZToActor'
error: implicit declaration of function 'Collider_InitCylinder'
```
**Solution**: Add function prototypes or include appropriate headers

#### 3. Missing Constants
```
error: 'COLTYPE_NONE' undeclared
error: 'COLTYPE_HIT0' undeclared
```
**Solution**: Define missing constants or include proper header files

#### 4. Syntax Errors
```
error: expected ')' before '&' token
error: expected identifier or '(' before 'if'
```
**Solution**: Fix structural issues in generated code

## Improving Code Generation

### 1. Include Proper Headers
Generated code should include:
```c
#include "global.h"
#include "z64actor.h"
#include "z64collision.h"
#include "z64math.h"
```

### 2. Use Correct Type Definitions
- Use `PlayState*` instead of undefined types
- Include proper actor structure definitions
- Use correct enum values and constants

### 3. Follow OoT Conventions
- Use proper function naming patterns
- Include correct parameter types
- Follow established coding patterns

## Integration with Training Data Generator

### Enable Compilation Testing
```bash
python3 generate_oot_data.py \
    --num-examples 50 \
    --output test_with_compilation.jsonl \
    --enable-compilation \
    --verbose
```

### Monitor Compilation Results
The generator will:
1. Generate training examples
2. Extract C code snippets
3. Attempt compilation with OoT environment
4. Report success rates and errors
5. Save detailed compilation reports

## Troubleshooting

### Build Issues
```bash
# Clean and rebuild
cd oot
make clean
make setup VERSION=ntsc-1.2
make VERSION=ntsc-1.2 -j4
```

### Compilation Issues
```bash
# Check MIPS toolchain
which mips-linux-gnu-gcc

# Verify Python environment
source oot_env/bin/activate
python3 --version
```

### ROM Issues
- Ensure ROM is NTSC 1.2 version
- Verify ROM hash matches expected values
- Check ROM file permissions

## Next Steps

1. **Improve Code Generation**: Use compilation results to enhance the training data generator
2. **Add More Headers**: Include additional OoT headers for better compilation success
3. **Fix Common Patterns**: Address recurring compilation errors in generated code
4. **Expand Testing**: Test with different code categories and complexity levels

## Files Generated

- `large_generation_20_compilation_report.txt`: Detailed compilation results
- `test_generation_5_compilation_report.txt`: Test dataset compilation results
- `COMPILATION_ANALYSIS.md`: Analysis of compilation patterns and issues
- `OOT_BUILD_GUIDE.md`: This build guide

## Success Metrics

- **Target Success Rate**: >50% for basic code snippets
- **Compilation Speed**: <1 second per snippet
- **Error Coverage**: Comprehensive error reporting
- **Integration**: Seamless integration with training data generation 