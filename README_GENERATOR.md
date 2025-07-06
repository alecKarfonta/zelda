# OoT Training Data Generator - Enhanced Command Line Interface

## 🎯 Overview

The OoT Training Data Generator now has a comprehensive command-line interface that makes it easy to generate authentic Ocarina of Time romhacking training data with extensive customization options.

## 🚀 Quick Start

### Basic Usage
```bash
# Generate 50 examples with default settings
python generate_oot_data.py --num-examples 50 --output training_data.jsonl

# Quick test generation (5 examples, reduced validation)
python generate_oot_data.py --num-examples 5 --quick --output test.jsonl
```

### Advanced Usage
```bash
# Generate 100 high-quality examples with custom settings
python generate_oot_data.py \
    --num-examples 100 \
    --output large_dataset.jsonl \
    --quality-threshold 8.0 \
    --authenticity-threshold 8.0 \
    --focus-categories enemy,npc \
    --focus-types actor_creation,ai_behavior \
    --complexity advanced \
    --verbose
```

## 📋 Available Options

### Basic Arguments
- `--num-examples, -n`: Number of examples to generate (default: 30, max: 1000)
- `--output, -o`: Output file path (default: `authentic_oot_training.jsonl`)
- `--api-key`: Anthropic API key (or set `ANTHROPIC_API_KEY` environment variable)
- `--model`: Anthropic model to use (default: `claude-3-5-sonnet-20241022`)

### OoT Source Analysis
- `--oot-path`: Path to OoT decompilation directory (default: `oot`)
- `--no-dynamic`: Disable dynamic source analysis (faster but less authentic)

### Quality Control
- `--quality-threshold`: Minimum quality score for acceptance (0-10, default: 7.0)
- `--authenticity-threshold`: Minimum authenticity score for acceptance (0-10, default: 7.0)

### Content Focus
- `--focus-categories`: Comma-separated list of actor categories (e.g., `enemy,npc,item`)
- `--focus-types`: Comma-separated list of example types (e.g., `actor_creation,animation_system`)
- `--complexity`: Force specific complexity level (`basic`, `intermediate`, `advanced`)

### Distribution Control
- `--complexity-distribution`: Complexity distribution weights (e.g., `basic:0.2,intermediate:0.5,advanced:0.3`)
- `--type-distribution`: Example type distribution weights (e.g., `actor_creation:0.25,animation_system:0.08`)

### Generation Settings
- `--quick`: Quick generation mode (reduced validation, faster generation)
- `--max-retries`: Maximum retries per example (default: 3)
- `--rate-limit`: Delay between API calls in seconds (default: 0.5)

### Output Options
- `--save-metadata`: Save detailed metadata and analytics
- `--format`: Output format (`jsonl` or `json`, default: `jsonl`)

### Logging and Debugging
- `--verbose, -v`: Enable verbose logging
- `--debug`: Enable debug logging
- `--quiet`: Suppress all output except errors

### Information Commands
- `--version`: Show program's version number
- `--list-types`: List available example types and exit
- `--list-categories`: List available actor categories and exit

## 📊 Available Example Types

The generator supports **18 different example types**:

### 🎭 Actor Systems
- `actor_creation`: Enemy, NPC, Item, Object actors
- `animation_system`: Skeletal animation, state machines, blend trees
- `collision_system`: Dynamic collision detection and response
- `interaction_system`: Dialogue, trading, quest systems

### 🎨 Visual & Audio
- `effect_system`: Particle effects, magic systems, visual enhancements
- `sound_system`: 3D audio, dynamic music, ambient sounds
- `ui_system`: User interface components and HUD elements

### 🧠 AI & Behavior
- `ai_behavior`: Pathfinding, decision making, state machines
- `combat_system`: Weapon systems, damage calculation, battle mechanics
- `environmental`: Weather, lighting, environmental effects

### 🧩 Gameplay Systems
- `puzzle_system`: Logic puzzles, mechanical systems
- `custom_mechanics`: Unique gameplay features and mechanics
- `memory_management`: Memory allocation and optimization
- `optimization`: Performance improvements and efficiency

### 📚 Documentation & Tools
- `code_explanation`: Documentation and tutorials
- `feature_implementation`: Specific feature implementations
- `debugging_help`: Troubleshooting and debugging assistance
- `debugging_tools`: Development and debugging utilities

## 🎭 Available Actor Categories

The generator supports **8 different actor categories**:

- `enemy`: Hostile creatures and enemies
- `npc`: Non-player characters and friendly entities
- `item`: Collectible items and pickups
- `object`: Environmental objects and mechanisms
- `background`: Background elements and scenery
- `effect`: Visual and audio effects
- `player`: Player-related systems and mechanics
- `misc`: Miscellaneous and utility systems

## 🔧 Usage Examples

### Basic Generation
```bash
# Generate 50 examples with default settings
python generate_oot_data.py --num-examples 50

# Generate with custom output file
python generate_oot_data.py --num-examples 30 --output my_training_data.jsonl
```

### Quality-Focused Generation
```bash
# Generate high-quality examples with strict thresholds
python generate_oot_data.py \
    --num-examples 100 \
    --quality-threshold 8.0 \
    --authenticity-threshold 8.0 \
    --output high_quality_dataset.jsonl
```

### Content-Specific Generation
```bash
# Focus on enemy and NPC actors
python generate_oot_data.py \
    --num-examples 20 \
    --focus-categories enemy,npc \
    --focus-types actor_creation,ai_behavior \
    --complexity advanced \
    --output enemy_npc_dataset.jsonl
```

### Quick Testing
```bash
# Quick test with reduced validation
python generate_oot_data.py \
    --num-examples 5 \
    --quick \
    --output test_dataset.jsonl \
    --no-dynamic
```

### Custom Distribution
```bash
# Custom complexity distribution
python generate_oot_data.py \
    --num-examples 50 \
    --complexity-distribution "basic:0.3,intermediate:0.4,advanced:0.3" \
    --type-distribution "actor_creation:0.3,animation_system:0.1,collision_system:0.1" \
    --output custom_distribution.jsonl
```

### Verbose Generation with Metadata
```bash
# Generate with detailed logging and metadata
python generate_oot_data.py \
    --num-examples 25 \
    --verbose \
    --save-metadata \
    --output detailed_dataset.jsonl
```

## 📈 Output Files

### Training Data
- **Main output**: JSONL file with training examples
- **Format**: Each line is a JSON object with `instruction` and `output` fields
- **Example**:
```json
{"instruction": "Create an enemy actor with basic AI", "output": "// C code here..."}
```

### Metadata (with `--save-metadata`)
- **Analysis file**: `{output_name}_metadata.json`
- **Contains**: Generation statistics, quality metrics, diversity analysis
- **Example**:
```json
{
  "generation_config": {
    "num_examples": 50,
    "quality_threshold": 7.0,
    "authenticity_threshold": 7.0
  },
  "generation_stats": {
    "total_generated": 150,
    "total_accepted": 50,
    "total_rejected": 100
  },
  "diversity_metrics": {
    "actor_categories": {"enemy": 15, "npc": 12},
    "example_types": {"actor_creation": 25},
    "unique_scenarios": 45
  }
}
```

## 🔍 Quality Metrics

The generator provides comprehensive quality metrics:

### Quality Score (0-10)
- **Content length**: Longer, more detailed examples score higher
- **Code completeness**: Complete, compilable code scores higher
- **Function usage**: Real OoT functions boost scores
- **Authentic patterns**: Proper OoT patterns increase scores

### Authenticity Score (0-10)
- **Function signatures**: Correct `(Actor* thisx, PlayState* play)` format
- **Real functions**: Usage of actual OoT decompilation functions
- **Memory layouts**: Accurate struct sizes and offsets
- **Architectural patterns**: Proper OoT design patterns

### Diversity Metrics
- **Actor categories**: Distribution across 8 categories
- **Example types**: Coverage of 18 different types
- **Unique scenarios**: Number of distinct instructions
- **Complexity levels**: Distribution across basic/intermediate/advanced

## 🚨 Troubleshooting

### Common Issues

**Import Errors**
```bash
# Solution: Use the wrapper script
python generate_oot_data.py --help
```

**API Key Issues**
```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-api-key-here"
python generate_oot_data.py --num-examples 5
```

**OoT Path Issues**
```bash
# Use --no-dynamic for testing without OoT decompilation
python generate_oot_data.py --num-examples 5 --no-dynamic
```

**Quality Issues**
```bash
# Lower thresholds for testing
python generate_oot_data.py --num-examples 10 --quality-threshold 5.0 --authenticity-threshold 5.0
```

### Debug Mode
```bash
# Enable debug logging for detailed information
python generate_oot_data.py --num-examples 5 --debug
```

## 📚 Advanced Features

### Dynamic Temperature Management
The generator automatically adjusts temperature based on:
- **Diversity needs**: Increases temperature for underrepresented categories
- **Complexity levels**: Adjusts for basic/intermediate/advanced content
- **Example types**: Creative types get higher temperature

### Multi-Pass Validation
Each example goes through multiple validation passes:
1. **Feedback pattern validation**: Checks for common LLM issues
2. **Function signature validation**: Ensures correct OoT patterns
3. **Architectural validation**: Verifies proper OoT design
4. **Source-based validation**: Cross-references with real decompilation
5. **Quality scoring**: Final quality and authenticity assessment

### Diversity Injection
The system ensures varied content through:
- **Category distribution**: Balanced actor category coverage
- **Type distribution**: Weighted example type selection
- **Complexity distribution**: Mix of basic/intermediate/advanced
- **Scenario uniqueness**: Avoids repetitive instructions

## 🎯 Best Practices

### For Production Use
```bash
# High-quality dataset for training
python generate_oot_data.py \
    --num-examples 500 \
    --quality-threshold 8.0 \
    --authenticity-threshold 8.0 \
    --save-metadata \
    --verbose \
    --output production_dataset.jsonl
```

### For Testing
```bash
# Quick validation of the system
python generate_oot_data.py \
    --num-examples 10 \
    --quick \
    --no-dynamic \
    --output test_validation.jsonl
```

### For Specific Content
```bash
# Focus on a specific area
python generate_oot_data.py \
    --num-examples 50 \
    --focus-categories enemy \
    --focus-types ai_behavior,combat_system \
    --complexity advanced \
    --output enemy_ai_dataset.jsonl
```

## 🔄 Migration from Old Command

### Old Command
```bash
python3 -c "from src.generation.main_generator import EnhancedOoTTrainingGenerator; gen = EnhancedOoTTrainingGenerator(); gen.generate_dataset(20, 'large_generation_20.jsonl')"
```

### New Command
```bash
python generate_oot_data.py --num-examples 20 --output large_generation_20.jsonl
```

## 📊 Performance Tips

- **Use `--quick`** for faster generation during development
- **Use `--no-dynamic`** if you don't have OoT decompilation
- **Start with small numbers** (5-10) for testing
- **Use `--verbose`** to monitor generation progress
- **Use `--save-metadata`** to analyze generation statistics

## 🎉 Success!

The new command-line interface provides:

✅ **Easy to use**: Simple commands with comprehensive help  
✅ **Highly configurable**: Extensive customization options  
✅ **Quality focused**: Built-in quality control and validation  
✅ **Diversity aware**: Automatic content variety management  
✅ **Production ready**: Robust error handling and logging  
✅ **Well documented**: Comprehensive help and examples  

No more complex Python one-liners - just simple, powerful commands! 