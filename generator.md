# OoT Romhack Training Data Generator - Usage Guide

## Overview

This script leverages Claude to generate high-quality training data for fine-tuning language models on Ocarina of Time romhacking tasks. It uses a multi-layer validation system to ensure examples are technically accurate and useful.

## Features

- **6 Example Types**: Code explanation, feature implementation, debugging help, architecture questions, conversational, and code modification
- **3 Validation Layers**: Technical accuracy, usefulness assessment, and quality scoring
- **Context-Aware Generation**: Uses OoT-specific knowledge about actors, player systems, scenes, and debugging
- **Multiple Output Formats**: JSONL for training, detailed metadata for analysis
- **Quality Filtering**: Only keeps examples with quality scores ≥ 6.0/10

## Installation

```bash
pip install anthropic
```

## Basic Usage

```bash
python oot_training_generator.py \
    --api-key your_anthropic_api_key \
    --num-examples 100 \
    --output oot_training_data.jsonl
```

## Command Line Options

- `--api-key`: Your Anthropic API key (required)
- `--num-examples`: Number of examples to generate (default: 50)
- `--output`: Output file path (default: oot_training_data.jsonl)
- `--model`: Claude model to use (default: claude-3-5-sonnet-20241022)

## Example Types Generated

### 1. Code Explanation
**Purpose**: Teach the model to explain OoT functions and code patterns

**Example Format**:
```json
{
  "instruction": "Explain what this OoT actor initialization function does",
  "input": "void EnItem00_Init(Actor* thisx, GlobalContext* globalCtx) {...}",
  "output": "This function initializes a collectible item actor..."
}
```

### 2. Feature Implementation
**Purpose**: Generate complete implementations for requested features

**Example Format**:
```json
{
  "instruction": "Create an actor that makes Link move twice as fast",
  "output": "To modify Link's movement speed, you need to edit the player actor's velocity calculations. Here's the implementation:\n\n```c\nvoid Player_UpdateMovement(Player* this, PlayState* play) {...}"
}
```

### 3. Debugging Help
**Purpose**: Identify and fix common romhacking problems

**Example Format**:
```json
{
  "instruction": "My custom actor crashes when spawning. Here's the code:",
  "input": "void MyActor_Init(Actor* thisx, PlayState* play) {...}",
  "output": "The crash is caused by accessing an uninitialized pointer. You need to allocate memory first..."
}
```

### 4. Architecture Questions
**Purpose**: Explain how OoT's game systems work

**Example Format**:
```json
{
  "instruction": "How does the Z-targeting system work in OoT?",
  "output": "The Z-targeting system works through several components: 1. Actor Flags, 2. Distance Checking, 3. Camera Focus..."
}
```

### 5. Code Modification
**Purpose**: Modify existing code to add new functionality

**Example Format**:
```json
{
  "instruction": "Modify this code to add a speed boost when wearing specific boots",
  "input": "void Player_UpdateMovement(Player* this, PlayState* play) {...}",
  "output": "Here's the modified code with speed boost functionality..."
}
```

## Quality Validation Process

### Layer 1: Technical Accuracy
- Validates OoT function names and signatures
- Checks memory addresses and data structures
- Verifies C syntax and assembly code
- Ensures realistic implementation approaches

### Layer 2: Usefulness Assessment
- Evaluates clarity and completeness
- Assesses practical value for romhackers
- Checks appropriate level of detail
- Measures teaching value

### Layer 3: Quality Scoring
- Base score calculation (0-10)
- Bonuses for code examples, proper terminology
- Penalties for technical issues or low usefulness
- Filters out examples below 6.0 threshold

## Context Templates

The script uses specialized context templates:

- **Actor System**: Memory layout, lifecycle functions, categories
- **Player System**: Movement, Z-targeting, state management
- **Scene System**: Rooms, objects, asset loading
- **Debugging**: Common issues and solutions
- **ASM Patches**: Low-level modifications

## Output Files

### Training Data (`oot_training_data.jsonl`)
Ready-to-use JSONL format for Unsloth training:
```jsonl
{"instruction": "...", "input": "...", "output": "..."}
{"instruction": "...", "output": "..."}
```

### Metadata (`oot_training_data_metadata.json`)
Detailed analysis and quality metrics:
```json
{
  "total_examples": 85,
  "average_quality": 7.2,
  "type_distribution": {
    "code_explanation": 15,
    "feature_implementation": 14,
    "debugging_help": 12,
    "architecture_question": 10,
    "code_modification": 18,
    "conversational": 16
  }
}
```

## Customization Options

### Adding New Example Types
```python
# In _load_example_templates()
ExampleType.NEW_TYPE: [
    {
        "instruction_template": "Your template here",
        "context_types": ["relevant_context"],
        "complexity": ["simple", "intermediate", "advanced"]
    }
]
```

### Custom Context Templates
```python
# In _load_context_templates()
"new_context": """
Your specialized OoT knowledge here...
"""
```

### Adjusting Quality Thresholds
```python
# In generate_dataset()
if example.quality_score >= 7.0:  # Raise for higher quality
    examples.append(example)
```

## Best Practices

1. **Start Small**: Generate 20-50 examples first to test quality
2. **Monitor Quality**: Check the metadata file for average quality scores
3. **Balance Types**: Ensure good distribution across example types
4. **Review Samples**: Manually review a few examples for accuracy
5. **Iterate**: Adjust templates and thresholds based on results

## Troubleshooting

### Low Quality Scores
- Check API model version (newer models typically perform better)
- Adjust complexity levels in templates
- Review and improve context templates

### API Rate Limits
- Increase sleep time between requests
- Use exponential backoff (already implemented)
- Consider using different API keys for parallel generation

### Parsing Errors
- Ensure Claude's response format is consistent
- Check JSON structure in generated examples
- Adjust parsing regex patterns if needed

## Integration with Unsloth

The generated JSONL file can be directly used with Unsloth:

```python
from datasets import load_dataset

# Load your generated dataset
dataset = load_dataset("json", data_files="oot_training_data.jsonl", split="train")

# Format for Unsloth (if using Alpaca format)
def format_prompts(examples):
    instructions = examples["instruction"]
    inputs = examples.get("input", [""] * len(instructions))
    outputs = examples["output"]
    texts = []
    
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        text = alpaca_prompt.format(instruction, input_text, output) + tokenizer.eos_token
        texts.append(text)
    
    return {"text": texts}

dataset = dataset.map(format_prompts, batched=True)
```

## Expected Results

With default settings, you should expect:
- **Quality Distribution**: 60-80% of generated examples pass quality threshold
- **Technical Accuracy**: 85-95% for code examples with validation
- **Variety**: Good distribution across all example types
- **Realism**: Examples based on actual OoT decompilation patterns

## Cost Estimation

For generating 100 examples:
- **API Calls**: ~300-400 total (generation + validation)
- **Tokens**: ~40,000-60,000 input tokens, ~20,000-30,000 output tokens
- **Estimated Cost**: $3-5 USD with Claude 3.5 Sonnet pricing

## Future Enhancements

- **Multi-turn Conversations**: Support for chat-based training data
- **Cross-validation**: Multiple models validating each other's examples
- **Specialized Domains**: Music system, graphics programming, save data
- **Difficulty Progression**: Examples that build on each other
- **Community Integration**: Pull real questions from Discord/forums