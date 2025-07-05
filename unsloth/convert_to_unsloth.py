#!/usr/bin/env python3
"""
Convert OoT training data to Unsloth format
"""

import json
import re
from typing import Dict, List, Optional

def clean_jsonl_line(line: str) -> Dict:
    """Clean and parse a JSONL line, handling malformed JSON"""
    try:
        # Try direct JSON parsing first
        return json.loads(line)
    except json.JSONDecodeError:
        # Use regex extraction as fallback
        return extract_fields_regex(line)

def extract_fields_regex(line: str) -> Dict:
    """Extract fields using regex patterns"""
    patterns = {
        'instruction': r'"instruction":\s*"([^"]*)"',
        'input': r'"input":\s*(null|"[^"]*")',
        'output': r'"output":\s*"([^"]*)"',
        'technical_notes': r'"technical_notes":\s*"([^"]*)"'
    }
    
    result = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, line)
        if match:
            if field == 'input' and match.group(1) == 'null':
                result[field] = None
            else:
                result[field] = match.group(1)
    
    return result

def convert_to_unsloth_format(example: Dict) -> Dict:
    """Convert a training example to Unsloth format"""
    
    # Clean up the instruction
    instruction = example.get('instruction', '').strip()
    if instruction.endswith('",'):
        instruction = instruction[:-2]
    
    # Clean up the output
    output = example.get('output', '').strip()
    if output.endswith('",'):
        output = output[:-2]
    
    # Handle input field
    input_text = example.get('input')
    if input_text is None or input_text == 'null':
        input_text = ""
    else:
        input_text = input_text.strip()
        if input_text.endswith('",'):
            input_text = input_text[:-2]
    
    # Create Unsloth format
    unsloth_example = {
        "instruction": instruction,
        "input": input_text,
        "output": output
    }
    
    return unsloth_example

def main():
    """Convert the sample dataset to Unsloth format"""
    
    print("🔄 Converting OoT Training Data to Unsloth Format")
    print("=" * 50)
    
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
        
        # Parse the line
        example = clean_jsonl_line(line)
        
        # Convert to Unsloth format
        unsloth_example = convert_to_unsloth_format(example)
        unsloth_examples.append(unsloth_example)
    
    # Save in Unsloth format
    output_file = 'oot_training_unsloth.jsonl'
    with open(output_file, 'w') as f:
        for example in unsloth_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✅ Converted {len(unsloth_examples)} examples to {output_file}")
    
    # Show sample of converted format
    print("\n📋 Sample converted format:")
    print(json.dumps(unsloth_examples[0], indent=2, ensure_ascii=False))
    
    # Create a smaller test set for quick testing
    test_file = 'oot_training_unsloth_test.jsonl'
    with open(test_file, 'w') as f:
        for example in unsloth_examples[:3]:  # First 3 examples
            f.write(json.dumps(example, ensure_ascii=False) + '\n')
    
    print(f"✅ Created test set with 3 examples: {test_file}")

if __name__ == "__main__":
    main() 