#!/usr/bin/env python3
"""
Generate a sample dataset of OoT training examples
"""

import os
import json
from training_generator import OoTTrainingDataGenerator, ExampleType

def generate_sample_dataset():
    """Generate 10 examples and save them for review"""
    print("🎯 Generating Sample OoT Training Dataset")
    print("=" * 50)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set")
        return
    
    generator = OoTTrainingDataGenerator(api_key)
    
    # Generate 10 examples with different types and complexities
    example_configs = [
        (ExampleType.CODE_EXPLANATION, "simple"),
        (ExampleType.FEATURE_IMPLEMENTATION, "intermediate"),
        (ExampleType.DEBUGGING_HELP, "simple"),
        (ExampleType.ARCHITECTURE_QUESTION, "intermediate"),
        (ExampleType.CODE_MODIFICATION, "advanced"),
        (ExampleType.CODE_EXPLANATION, "intermediate"),
        (ExampleType.FEATURE_IMPLEMENTATION, "advanced"),
        (ExampleType.DEBUGGING_HELP, "intermediate"),
        (ExampleType.ARCHITECTURE_QUESTION, "advanced"),
        (ExampleType.CODE_MODIFICATION, "intermediate"),
    ]
    
    examples = []
    
    for i, (example_type, complexity) in enumerate(example_configs):
        print(f"\n📝 Generating example {i+1}/10: {example_type.value} ({complexity})")
        
        try:
            example = generator.generate_training_example(example_type, complexity)
            
            if example.quality_score >= 6.0:
                examples.append(example)
                print(f"  ✅ Quality: {example.quality_score:.1f}")
                print(f"  📏 Output length: {len(example.output)} chars")
            else:
                print(f"  ❌ Low quality: {example.quality_score:.1f}, skipping")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Save examples
    if examples:
        save_examples(examples)
        print(f"\n🎉 Generated {len(examples)} high-quality examples")
    else:
        print("\n❌ No examples generated")

def save_examples(examples):
    """Save examples in multiple formats"""
    
    # Save as JSONL for training
    with open("sample_oot_training.jsonl", "w") as f:
        for example in examples:
            training_record = {
                "instruction": example.instruction,
                "output": example.output
            }
            if example.input:
                training_record["input"] = example.input
            f.write(json.dumps(training_record) + "\n")
    
    # Save detailed metadata
    metadata = {
        "total_examples": len(examples),
        "average_quality": sum(e.quality_score for e in examples) / len(examples),
        "type_distribution": {},
        "examples": []
    }
    
    for example in examples:
        example_type = example.example_type.value
        metadata["type_distribution"][example_type] = metadata["type_distribution"].get(example_type, 0) + 1
        
        metadata["examples"].append({
            "type": example_type,
            "quality_score": example.quality_score,
            "instruction": example.instruction,
            "input": example.input,
            "output_preview": example.output[:200] + "..." if len(example.output) > 200 else example.output,
            "validation_notes": example.validation_notes
        })
    
    with open("sample_oot_training_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    # Save individual examples for review
    for i, example in enumerate(examples):
        filename = f"example_{i+1:02d}_{example.example_type.value}.txt"
        with open(filename, "w") as f:
            f.write(f"Type: {example.example_type.value}\n")
            f.write(f"Quality Score: {example.quality_score:.1f}\n")
            f.write(f"Validation Notes: {example.validation_notes}\n")
            f.write("-" * 50 + "\n")
            f.write(f"Instruction: {example.instruction}\n")
            if example.input:
                f.write(f"Input: {example.input}\n")
            f.write(f"Output:\n{example.output}\n")
    
    print(f"📁 Saved files:")
    print(f"  - sample_oot_training.jsonl ({len(examples)} examples)")
    print(f"  - sample_oot_training_metadata.json (detailed analysis)")
    print(f"  - example_01.txt through example_{len(examples):02d}.txt (individual examples)")

def show_summary():
    """Show a summary of the generated examples"""
    try:
        with open("sample_oot_training_metadata.json", "r") as f:
            metadata = json.load(f)
        
        print("\n📊 Sample Dataset Summary:")
        print(f"Total examples: {metadata['total_examples']}")
        print(f"Average quality: {metadata['average_quality']:.1f}/10")
        print("\nType distribution:")
        for example_type, count in metadata["type_distribution"].items():
            print(f"  {example_type}: {count}")
        
        print("\nExample previews:")
        for i, example in enumerate(metadata["examples"][:3]):
            print(f"\n{i+1}. {example['type']} (Quality: {example['quality_score']:.1f})")
            print(f"   Instruction: {example['instruction'][:100]}...")
            print(f"   Output: {example['output_preview']}")
            
    except FileNotFoundError:
        print("❌ Metadata file not found")

if __name__ == "__main__":
    generate_sample_dataset()
    show_summary() 