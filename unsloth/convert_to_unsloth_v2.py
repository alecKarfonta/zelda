#!/usr/bin/env python3
"""
Convert OoT training data to Unsloth format - Improved version
"""

import json
import re
from typing import Dict, List, Optional

def extract_clean_fields(line: str) -> Dict:
    """Extract clean fields from the malformed JSONL line"""
    
    # Find the instruction field
    instruction_match = re.search(r'"instruction":\s*"([^"]*)"', line)
    instruction = instruction_match.group(1) if instruction_match else ""
    
    # Find the input field
    input_match = re.search(r'"input":\s*(null|"[^"]*")', line)
    input_text = None
    if input_match:
        if input_match.group(1) == 'null':
            input_text = ""
        else:
            input_text = input_match.group(1).strip('"')
    
    # Find the output field - this is the tricky part
    output_match = re.search(r'"output":\s*"([^"]*(?:\\"[^"]*)*)"', line)
    output = ""
    if output_match:
        output = output_match.group(1)
        # Clean up escaped characters
        output = output.replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
    
    return {
        "instruction": instruction,
        "input": input_text or "",
        "output": output
    }

def convert_to_unsloth_format(example: Dict) -> Dict:
    """Convert a training example to Unsloth format"""
    
    # Clean up the instruction
    instruction = example.get('instruction', '').strip()
    
    # Clean up the output
    output = example.get('output', '').strip()
    
    # Handle input field
    input_text = example.get('input', '')
    if input_text is None:
        input_text = ""
    
    # Create Unsloth format
    unsloth_example = {
        "instruction": instruction,
        "input": input_text,
        "output": output
    }
    
    return unsloth_example

def main():
    """Convert the sample dataset to Unsloth format"""
    
    print("🔄 Converting OoT Training Data to Unsloth Format (v2)")
    print("=" * 55)
    
    # Read the original JSONL file
    try:
        with open('sample_oot_training.jsonl', 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("❌ sample_oot_training.jsonl not found")
        return
    
    # Convert each example
    unsloth_examples = []
    for i, line in enumerate(lines, 1):
        print(f"Processing example {i}/{len(lines)}...")
        
        # Extract clean fields
        example = extract_clean_fields(line)
        
        # Convert to Unsloth format
        unsloth_example = convert_to_unsloth_format(example)
        unsloth_examples.append(unsloth_example)
    
    # Save in Unsloth format
    output_file = 'oot_training_unsloth_v2.jsonl'
    with open(output_file, 'w') as f:
        for example in unsloth_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✅ Converted {len(unsloth_examples)} examples to {output_file}")
    
    # Show sample of converted format
    print("\n📋 Sample converted format:")
    sample = unsloth_examples[0]
    print(f"Instruction: {sample['instruction'][:100]}...")
    print(f"Input: {sample['input'][:50] if sample['input'] else '(empty)'}")
    print(f"Output length: {len(sample['output'])} characters")
    
    # Create a smaller test set for quick testing
    test_file = 'oot_training_unsloth_test.jsonl'
    with open(test_file, 'w') as f:
        for example in unsloth_examples[:3]:  # First 3 examples
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✅ Created test set with 3 examples: {test_file}")
    
    # Show statistics
    print(f"\n📊 Dataset Statistics:")
    print(f"Total examples: {len(unsloth_examples)}")
    avg_instruction_len = sum(len(ex['instruction']) for ex in unsloth_examples) / len(unsloth_examples)
    avg_output_len = sum(len(ex['output']) for ex in unsloth_examples) / len(unsloth_examples)
    examples_with_input = sum(1 for ex in unsloth_examples if ex['input'])
    print(f"Average instruction length: {avg_instruction_len:.1f} characters")
    print(f"Average output length: {avg_output_len:.1f} characters")
    print(f"Examples with input: {examples_with_input}/{len(unsloth_examples)}")

if __name__ == "__main__":
    main() 