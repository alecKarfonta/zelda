# OoT Romhacking Training Data Generator

Advanced system for generating authentic training data for Ocarina of Time romhacking using real decompilation patterns.

## Features

- **Strict Authenticity Validation**: Uses real OoT decompilation source code
- **Dynamic Source Analysis**: Analyzes actual OoT source files
- **Multi-Pass Validation**: Validates against real OoT patterns
- **Diversity Injection**: Ensures varied content across categories

## Quick Start

```bash
# Install dependencies
pip install anthropic python-dotenv

# Set API key
export ANTHROPIC_API_KEY="your-api-key"

# Generate training data
python enhanced_authentic_generator.py --num-examples 50
```

## Usage

```python
from enhanced_authentic_generator import EnhancedOoTTrainingGenerator

generator = EnhancedOoTTrainingGenerator(oot_path="oot")
generator.generate_dataset(num_examples=50, output_file="training.jsonl")
```

## Architecture

- **DynamicSourceAnalyzer**: Analyzes real OoT source files
- **StrictAuthenticityValidator**: Enforces authentic patterns  
- **DiversityInjector**: Ensures varied content
- **EnhancedOoTTrainingGenerator**: Main generation system

## Output Format

JSONL format with instruction/output pairs for training.

## License

MIT License 