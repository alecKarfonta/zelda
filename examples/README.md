# Examples

This folder contains example outputs and sample data for the Zelda OoT Actor System tools.

## Files

### `large_generation_20_conformed.jsonl`
- **Description**: Sample conformed JSONL file with flattened instruction/output pairs
- **Source**: Generated from `large_generation_20.jsonl` using the parser's `--conform` option
- **Purpose**: Demonstrates the parser's ability to flatten nested JSON structures into clean, single-level instruction/output pairs
- **Content**: 20 examples of Zelda OoT actor implementations with various features:
  - Actor creation systems
  - Animation systems
  - Physics-based cloth simulation
  - Memory management
  - Sound optimization
  - Combat systems
  - Puzzle mechanics
  - NPC AI behaviors

## Usage

This example file can be used to:
1. **Test the parser**: Run `python parse_logs.py --summary --input examples/large_generation_20_conformed.jsonl`
2. **Demonstrate flattening**: Compare with the original nested structure
3. **Training data**: Use as a sample dataset for model training
4. **Documentation**: Show the expected output format for the parser

## Format

Each line in the JSONL file contains a JSON object with:
- `instruction`: The prompt/request for the actor implementation
- `output`: The complete C code implementation following OoT conventions

The conformed format ensures all entries are flat instruction/output pairs without nested JSON structures. 