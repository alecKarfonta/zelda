# Dynamic Source Code Integration Plan for OoT Training Generator

## Overview

This plan describes how to leverage real OoT decompilation source code to dynamically generate authentic training examples, replacing hardcoded patterns with real, extracted data from the actual codebase.

## Phase 1: Source Code Analysis and Extraction System ✅ IMPLEMENTED

### 1.1 DynamicSourceAnalyzer Class

The core component that analyzes the OoT decompilation and extracts real patterns:

**Key Features:**
- **Source File Discovery**: Automatically finds and categorizes C/H files from the decompilation
- **Function Extraction**: Parses real function signatures with parameters and return types
- **Struct Parsing**: Extracts complete struct definitions with memory layout comments
- **Enum Extraction**: Parses enum definitions with all values
- **Constant Mining**: Extracts #define constants and macros
- **Example Harvesting**: Collects complete code patterns (init functions, collision setup, etc.)

**Source Categories Analyzed:**
```
oot/
├── src/code/              # Core engine functions
├── src/overlays/actors/   # All actor implementations  
├── src/overlays/effects/  # Effect systems
├── include/               # Header files with definitions
└── assets/                # Asset definitions
```

### 1.2 Real-Time Pattern Extraction

**Function Signatures:**
```c
// Extracted from actual source files
void EnItem00_Init(Actor* thisx, PlayState* play)
void EnItem00_Update(Actor* thisx, PlayState* play)
static ColliderCylinderInit sCylinderInit = { ... }
```

**Struct Definitions:**
```c
// Real struct with memory offsets from z_en_item00.h
typedef struct {
    /* 0x000 */ Actor actor;
    /* 0x14C */ s16 timer;
    /* 0x14E */ s16 actionState;
    /* 0x150 */ f32 scale;
} EnItem00; // size = 0x154
```

**Constants and Enums:**
```c
// Real constants from source
#define ITEM00_HEART_PIECE 0x06
#define ITEM00_RUPEE_BLUE 0x01
```

## Phase 2: Dynamic Validation System ✅ IMPLEMENTED

### 2.1 Enhanced StrictAuthenticityValidator

**Real Source Validation:**
- Validates function names against extracted function database
- Checks struct usage against real struct definitions
- Verifies constants match actual source values
- Reports specific files where violations occur

**Multi-Layer Validation:**
1. **Hardcoded Pattern Validation** (forbidden patterns, parameter order)
2. **Dynamic Source Validation** (function/struct existence)
3. **Architectural Validation** (proper usage patterns)
4. **Authenticity Scoring** (percentage of real vs fake elements)

### 2.2 Smart Fallback System

If dynamic analysis fails (missing OoT directory, file errors):
- Gracefully falls back to hardcoded validation
- Continues generation with reduced authenticity scoring
- Logs the fallback for user awareness

## Phase 3: Context-Aware Generation ✅ IMPLEMENTED

### 3.1 Dynamic Example Injection

**Actor Creation Examples:**
- Injects real `EnActor_Init` function from source
- Includes real collision setup patterns from specific actors
- Uses actual struct definitions with memory comments

**Code Explanation Examples:**
- Shows real struct definitions from headers
- Displays actual constant definitions with values
- References specific source files for context

**Feature Implementation Examples:**
- Lists real item constants (ITEM00_*) from source
- Shows authentic enum values from actual code
- Provides real function signatures for features

### 3.2 Smart Pattern Replacement

**Function Name Enhancement:**
```python
# Before: Generic placeholder
"void FuncName_Init(Actor* thisx, PlayState* play)"

# After: Real function from source
"void EnNpc_Init(Actor* thisx, PlayState* play)"  # From ovl_En_Npc
```

**Struct Name Enhancement:**
```python
# Before: Generic placeholder  
"typedef struct { ... } StructName;"

# After: Real struct from source
"typedef struct { ... } EnDekubaba;"  # From z_en_dekubaba.h
```

## Phase 4: Advanced Source Intelligence

### 4.1 Contextual Example Selection

**Smart Actor Matching:**
```python
# Request: "Create a collectible item actor"
# System finds: z_en_item00.c (real collectible implementation)
# Injects: Actual EnItem00 patterns and constants

# Request: "Create an enemy actor"  
# System finds: z_en_goma.c, z_en_wallmaster.c (real enemies)
# Injects: Real enemy patterns and collision setups
```

**Pattern-Based Learning:**
- Analyzes request type (collectible, enemy, NPC, object)
- Finds similar actors in source code
- Extracts and injects relevant patterns
- Provides file references for further study

### 4.2 Cross-Reference Validation

**Function Usage Validation:**
```python
# Validates: Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ITEM00, ...)
# Checks: ACTOR_EN_ITEM00 exists in real constants
# Verifies: Actor_Spawn signature matches source
# Result: ✅ Authentic - found in z_actor.c
```

**Struct Field Validation:**
```python
# Validates: this->actor.world.pos.x = 100.0f;
# Checks: Actor struct has 'world' field  
# Verifies: world has 'pos' field of type Vec3f
# Result: ✅ Authentic - matches actor.h definition
```

## Phase 5: Implementation Features

### 5.1 Performance Optimizations

**Caching System:**
- Parses source files once at startup
- Caches extracted patterns in memory
- Avoids re-parsing during generation
- ~2-3 second startup cost for major speed gains

**Incremental Analysis:**
- Only analyzes files that changed
- Tracks file modification times
- Supports hot-reloading during development

### 5.2 Error Handling and Reporting

**Graceful Degradation:**
- Missing OoT directory → Falls back to hardcoded validation
- Parse errors → Skips problematic files, continues with others
- Memory issues → Reduces cache size, continues operation

**Detailed Logging:**
```
🔍 Analyzing OoT decompilation source files...
   📁 Analyzed 486 files
   🔧 Found 2,847 functions  
   📊 Found 312 structs
   📋 Found 89 enums
   🔧 Found 1,456 constants
✅ Dynamic source analysis initialized successfully
```

### 5.3 Usage Examples

**Basic Usage (Auto-detects oot/ directory):**
```bash
python enhanced_authentic_generator.py --num-examples 50
```

**Custom OoT Path:**
```bash
python enhanced_authentic_generator.py --oot-path /path/to/zelda/oot --num-examples 30
```

**Disable Dynamic Analysis (Fallback Mode):**
```bash
python enhanced_authentic_generator.py --no-dynamic --num-examples 20
```

## Phase 6: Quality Improvements

### 6.1 Authenticity Metrics

**Enhanced Scoring:**
- **Function Authenticity**: % of functions that exist in real source
- **Struct Authenticity**: % of structs that match real definitions  
- **Constant Authenticity**: % of constants that match real values
- **Pattern Authenticity**: Usage of real code patterns vs generic

**Rejection Criteria:**
- < 70% function authenticity → Rejected
- Uses forbidden patterns → Rejected  
- Wrong parameter order → Rejected
- Non-existent structs → Rejected

### 6.2 Training Data Quality

**Before Dynamic Integration:**
```json
{
  "instruction": "Create a heart piece actor",
  "output": "// Generic heart piece with placeholder names\nvoid ActorName_Init(Actor* thisx, PlayState* play) {\n  // Generic initialization\n}"
}
```

**After Dynamic Integration:**
```json
{
  "instruction": "Create a heart piece actor",  
  "output": "// Use EnItem00 with ITEM00_HEART_PIECE (from z_en_item00.c)\nvoid EnItem00_Init(Actor* thisx, PlayState* play) {\n  EnItem00* this = (EnItem00*)thisx;\n  // Real initialization pattern from source\n  Actor_SetScale(&this->actor, 0.01f);\n  this->actor.params = ITEM00_HEART_PIECE;\n}"
}
```

## Phase 7: Future Enhancements

### 7.1 Advanced Pattern Recognition

**Code Flow Analysis:**
- Track how real actors handle state transitions
- Extract common animation patterns
- Learn real memory management patterns
- Understand authentic error handling

**Asset Integration:**
- Parse object files (object_*.xml) for real asset references
- Extract display list patterns from assets
- Validate texture and model usage against real assets

### 7.2 Interactive Learning

**Source Explorer Mode:**
```bash
python enhanced_authentic_generator.py --explore
# Interactive mode:
# > search functions "Collider"
# > show struct Actor
# > find examples "heart piece"
# > validate code "my_code.c"
```

**Real-Time Feedback:**
```python
# As user types code, provide real-time validation:
def validate_live(code_snippet):
    issues = source_analyzer.validate_against_real_source(code_snippet)
    suggestions = source_analyzer.suggest_improvements(code_snippet)
    return {"issues": issues, "suggestions": suggestions}
```

## Benefits Summary

### ✅ **Immediate Benefits**
1. **100% Authentic Function Names**: Only uses functions that exist in real OoT source
2. **Real Struct Layouts**: Generates code with actual memory offsets and field names  
3. **Verified Constants**: Uses real #define values from the decompilation
4. **Authentic Examples**: Injects real code patterns from actual actor implementations
5. **Smart Validation**: Catches non-authentic patterns that would break in real romhacks

### ✅ **Quality Improvements**
1. **Higher Acceptance Rate**: More examples pass strict validation
2. **Better Training Data**: Examples that actually work in real development
3. **Reduced Hallucination**: Less likely to generate non-existent functions/structs
4. **Educational Value**: Examples reference real files for learning
5. **Maintainability**: Automatically stays current with OoT decompilation updates

### ✅ **Development Benefits**
1. **Zero Manual Maintenance**: No need to update hardcoded function lists
2. **Scalable**: Automatically discovers new patterns as decompilation progresses
3. **Extensible**: Easy to add new analysis patterns and validation rules
4. **Debuggable**: Clear error messages with source file references
5. **Flexible**: Works with any OoT decompilation fork or version

This implementation transforms the training generator from a static, hardcoded system into a dynamic, intelligent system that learns directly from the real OoT source code, ensuring maximum authenticity and educational value. 