# 🎮 OoT Romhacking Training Data Generator

> **Advanced AI-powered system for generating authentic training data for Ocarina of Time romhacking using real decompilation patterns and strict authenticity validation.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/alecKarfonta/zelda)
[![OoT Decomp](https://img.shields.io/badge/OoT-Decompilation-orange.svg)](https://github.com/zeldaret/oot)

## 🎯 Overview

This project generates high-quality training examples for OoT romhacking by leveraging real decompilation source code to ensure all generated examples follow authentic patterns. The system uses advanced AI techniques combined with strict validation to create training data that accurately represents real OoT development patterns.

### ✨ Key Features

- **🔍 Dynamic Source Analysis**: Analyzes actual OoT decompilation source files to extract real function signatures, struct definitions, and architectural patterns
- **🎯 Strict Authenticity Validation**: Uses real OoT decompilation source code to ensure all generated examples follow authentic patterns
- **🔄 Multi-Pass Validation**: Validates examples against real OoT patterns with progressive correction and refinement
- **🎨 Diversity Injection**: Ensures varied and interesting content across different actor categories and example types
- **📊 Quality Control**: Comprehensive scoring system with authenticity focus and automatic refinement

## 🏗️ Architecture

### Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **DynamicSourceAnalyzer** | Analyzes real OoT source files | Extracts function signatures, structs, enums, constants |
| **StrictAuthenticityValidator** | Enforces authentic patterns | Validates against real OoT functions and architectural patterns |
| **DiversityInjector** | Ensures varied content | Generates diverse scenarios across actor categories |
| **EnhancedOoTTrainingGenerator** | Main generation system | Orchestrates validation, refinement, and quality control |

### Example Categories

The system generates examples across **19 different categories**:

#### 🎭 Actor Systems
- **Actor Creation**: Enemy, NPC, Item, Object actors
- **Animation System**: Skeletal animation, state machines, blend trees
- **Collision System**: Dynamic collision detection and response
- **Interaction System**: Dialogue, trading, quest systems

#### 🎨 Visual & Audio
- **Effect System**: Particle effects, magic systems, visual enhancements
- **Sound System**: 3D audio, dynamic music, ambient sounds
- **UI System**: User interface components and HUD elements

#### 🧠 AI & Behavior
- **AI Behavior**: Pathfinding, decision making, state machines
- **Combat System**: Weapon systems, damage calculation, battle mechanics
- **Environmental**: Weather, lighting, environmental effects

#### 🧩 Gameplay Systems
- **Puzzle System**: Logic puzzles, mechanical systems
- **Custom Mechanics**: Unique gameplay features and mechanics
- **Memory Management**: Memory allocation and optimization
- **Optimization**: Performance improvements and efficiency

#### 📚 Documentation & Tools
- **Code Explanation**: Documentation and tutorials
- **Feature Implementation**: Specific feature implementations
- **Debugging Help**: Troubleshooting and debugging assistance
- **Debugging Tools**: Development and debugging utilities

## 🚀 Quick Start

### Prerequisites

1. **OoT Decompilation**: Clone the OoT decompilation repository
   ```bash
   git clone https://github.com/zeldaret/oot.git
   ```

2. **Python Dependencies**: Install required packages
   ```bash
   pip install anthropic python-dotenv
   ```

3. **API Key**: Set your Anthropic API key
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

### Basic Usage

```python
from generator import EnhancedOoTTrainingGenerator

# Initialize generator with OoT decompilation path
generator = EnhancedOoTTrainingGenerator(
    oot_path="oot",  # Path to OoT decompilation
    use_dynamic_analysis=True  # Enable real source analysis
)

# Generate training dataset
generator.generate_dataset(
    num_examples=50,
    output_file="authentic_oot_training.jsonl"
)
```

### Command Line Usage

```bash
python generator.py \
    --num-examples 50 \
    --output authentic_oot_training.jsonl \
    --oot-path oot \
    --api-key your-api-key
```

## 🔧 Advanced Features

### Dynamic Source Analysis

The system can analyze real OoT decompilation source files to extract:

- **Function Signatures**: Real function names and signatures from actual source
- **Struct Definitions**: Complete struct definitions with memory offsets
- **Enum Definitions**: Real enum values and constants
- **Constants**: #define constants and macros from headers
- **Examples**: Complete code examples from specific patterns

### Quality Control System

#### Validation Process

1. **Function Signature Validation**: Ensures all functions use authentic OoT signatures
2. **Architectural Validation**: Validates against real OoT architectural patterns
3. **Source-Based Validation**: Checks against actual decompilation source code
4. **Quality Scoring**: Calculates quality and authenticity scores
5. **Refinement**: Attempts to improve low-quality examples

#### Acceptance Criteria

- **Quality Score**: ≥ 6.0 (balanced for good acceptance rate)
- **Authenticity Score**: ≥ 6.0 (ensures authentic patterns)
- **Minimum Length**: > 100 characters of meaningful code
- **Diversity Bonus**: Applied for underrepresented categories

### Diversity Tracking

The system tracks diversity across:

- **Actor Categories**: Enemy, NPC, Item, Object, Background, Effect, Player, Misc
- **Example Types**: 19 different example categories
- **Complexity Levels**: Basic, Intermediate, Advanced
- **Unique Scenarios**: Ensures varied instruction content

## 📊 Output Format

Generated examples are saved in JSONL format:

```json
{
  "instruction": "Create a skeletal warrior that teleports behind the player for surprise attacks",
  "output": "```c\n// Authentic OoT actor implementation\ntypedef struct {\n    /* 0x000 */ Actor actor;\n    /* 0x14C */ s16 actionState;\n    /* 0x14E */ s16 timer;\n    /* 0x150 */ ColliderCylinder collider;\n} EnSkeletalWarrior;\n\nvoid EnSkeletalWarrior_Init(Actor* thisx, PlayState* play) {\n    EnSkeletalWarrior* this = (EnSkeletalWarrior*)thisx;\n    \n    // Authentic collision setup\n    Collider_InitCylinder(play, &this->collider);\n    Collider_SetCylinder(play, &this->collider, &this->actor, &sCylinderInit);\n    \n    // Authentic actor setup\n    Actor_SetScale(&this->actor, 0.01f);\n    Actor_SetFocus(&this->actor, 50.0f);\n    \n    this->actionState = 0;\n    this->timer = 0;\n}\n```"
}
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for generation | Yes |

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--api-key` | Anthropic API key (alternative to environment variable) | None |
| `--num-examples` | Number of examples to generate | 30 |
| `--output` | Output file path | `authentic_oot_training.jsonl` |
| `--oot-path` | Path to OoT decompilation directory | `oot` |
| `--no-dynamic` | Disable dynamic source analysis | False |

## 🎯 Authenticity Enforcement

### Real OoT Patterns

The system enforces authentic patterns from actual OoT decompilation:

- **Function Signatures**: `FuncName(Actor* thisx, PlayState* play)` (correct parameter order)
- **Position Access**: `actor.world.pos` instead of `actor.pos`
- **Collectibles**: Use `EnItem00` with appropriate parameters (not custom actors)
- **Collision**: Authentic collision setup patterns from `z_collision_check.c`
- **Memory Layout**: Proper struct definitions with memory offsets

### Forbidden Patterns

The system rejects non-authentic patterns:

- ❌ `GlobalContext` usage (use `PlayState` instead)
- ❌ Wrong parameter order: `FuncName(PlayState* play, Actor* thisx)`
- ❌ Direct position access: `actor.pos` (use `actor.world.pos`)
- ❌ Custom heart piece actors (use `EnItem00` with `ITEM00_HEART_PIECE`)

## 📈 Performance & Statistics

### Generation Metrics

- **Acceptance Rate**: ~60-70% (with quality thresholds)
- **Processing Speed**: ~2-3 examples per minute
- **Memory Usage**: ~500MB for typical generation runs
- **Output Quality**: High authenticity scores (≥6.0)

### Diversity Achievements

- **Actor Categories**: 8/8 categories covered
- **Example Types**: 19/19 types represented
- **Complexity Levels**: Balanced distribution across basic/intermediate/advanced
- **Unique Scenarios**: 100+ unique instruction variations

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/zelda.git
   cd zelda
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set up OoT decompilation**
   ```bash
   git clone https://github.com/zeldaret/oot.git
   ```
5. **Configure your API key**
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   ```

### Contribution Guidelines

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes**
3. **Add tests if applicable**
4. **Update documentation**
5. **Submit a pull request**

### Areas for Contribution

- **New Example Types**: Add support for additional categories
- **Enhanced Validation**: Improve authenticity checking
- **Performance Optimization**: Speed up generation process
- **Documentation**: Improve guides and examples
- **Bug Fixes**: Report and fix issues

## 📚 Documentation

### Additional Resources

- **[SYSTEM_SUMMARY.md](SYSTEM_SUMMARY.md)**: Detailed system architecture
- **[DATASET_SUMMARY.md](DATASET_SUMMARY.md)**: Dataset generation statistics
- **[DIVERSITY_IMPROVEMENTS.md](DIVERSITY_IMPROVEMENTS.md)**: Diversity enhancement strategies
- **[UNSLOTH_INTEGRATION_GUIDE.md](UNSLOTH_INTEGRATION_GUIDE.md)**: Integration with Unsloth framework

### Example Files

- **[example_01_code_explanation.txt](example_01_code_explanation.txt)**: Code explanation examples
- **[example_02_feature_implementation.txt](example_02_feature_implementation.txt)**: Feature implementation examples
- **[example_03_debugging_help.txt](example_03_debugging_help.txt)**: Debugging assistance examples

## 🐛 Troubleshooting

### Common Issues

#### API Key Issues
```bash
# Ensure your API key is set
export ANTHROPIC_API_KEY="your-actual-api-key"
```

#### OoT Decompilation Issues
```bash
# Make sure OoT decompilation is properly cloned
git clone https://github.com/zeldaret/oot.git
```

#### Memory Issues
```bash
# Reduce batch size for memory-constrained systems
python generator.py --num-examples 10
```

#### Quality Issues
- Check that your OoT decompilation is up to date
- Ensure you have sufficient API credits
- Verify your internet connection for API calls

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OoT Decompilation Team**: For providing the authentic source code
- **Anthropic**: For providing the Claude API for generation
- **OoT Romhacking Community**: For inspiration and feedback
- **Contributors**: Everyone who has helped improve this project

## 📞 Support

For issues, questions, or contributions:

1. **Check existing issues**: [GitHub Issues](https://github.com/alecKarfonta/zelda/issues)
2. **Create a new issue**: Provide detailed information about your problem
3. **Join the community**: Connect with other OoT romhackers

---

**Note**: This system requires access to the OoT decompilation source code and an Anthropic API key to function properly. Make sure you have both before attempting to use the generator.

**Happy Romhacking! 🎮** 