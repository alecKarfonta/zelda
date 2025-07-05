#!/usr/bin/env python3
"""
Example usage script for the OoT Training Data Generator

This script demonstrates how to use the generator in various ways
and shows expected output formats.
"""

import os
import json
from oot_training_generator import OoTTrainingDataGenerator, ExampleType

def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable")
        return
    
    generator = OoTTrainingDataGenerator(api_key)
    
    # Generate a single example
    example = generator.generate_training_example(
        ExampleType.CODE_EXPLANATION, 
        complexity="intermediate"
    )
    
    print(f"Generated example:")
    print(f"Type: {example.example_type.value}")
    print(f"Quality Score: {example.quality_score:.1f}")
    print(f"Instruction: {example.instruction}")
    print(f"Output: {example.output[:200]}...")
    print()

def example_batch_generation():
    """Example of generating a small batch with specific parameters"""
    print("=== Batch Generation Example ===")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable")
        return
    
    generator = OoTTrainingDataGenerator(api_key)
    
    # Generate 10 examples of different types
    examples = []
    for example_type in [ExampleType.FEATURE_IMPLEMENTATION, ExampleType.DEBUGGING_HELP]:
        for complexity in ["simple", "intermediate"]:
            example = generator.generate_training_example(example_type, complexity)
            if example.quality_score >= 6.0:
                examples.append(example)
                print(f"✓ {example_type.value} ({complexity}): Quality {example.quality_score:.1f}")
            else:
                print(f"✗ {example_type.value} ({complexity}): Quality {example.quality_score:.1f} - Skipped")
    
    print(f"\nGenerated {len(examples)} high-quality examples")

def show_expected_outputs():
    """Show examples of expected output formats"""
    print("=== Expected Output Examples ===")
    
    # Code Explanation Example
    print("\n1. Code Explanation Example:")
    code_explanation = {
        "instruction": "Explain what this OoT actor update function does",
        "input": "void EnItem00_Update(Actor* thisx, PlayState* play) {\n    EnItem00* this = (EnItem00*)thisx;\n    this->actor.world.rot.y += 0x400;\n    Actor_MoveXZGravity(&this->actor);\n}",
        "output": "This function updates a collectible item actor each frame. It rotates the item around its Y-axis (0x400 units per frame, creating a spinning effect) and applies physics movement including gravity and XZ-plane motion. The Actor_MoveXZGravity function handles collision detection and applies the actor's velocity to its position while accounting for gravity on the Y-axis."
    }
    print(json.dumps(code_explanation, indent=2))
    
    # Feature Implementation Example  
    print("\n2. Feature Implementation Example:")
    feature_implementation = {
        "instruction": "Create an actor that spawns a healing fairy when Link's health is low",
        "output": "Here's a complete implementation of a health monitor actor that spawns healing fairies:\n\n```c\n#include \"z64.h\"\n#include \"macros.h\"\n\ntypedef struct {\n    Actor actor;\n    s16 timer;\n    u8 fairySpawned;\n} EnHealthFairy;\n\nvoid EnHealthFairy_Init(Actor* thisx, PlayState* play) {\n    EnHealthFairy* this = (EnHealthFairy*)thisx;\n    this->timer = 0;\n    this->fairySpawned = 0;\n    this->actor.flags |= ACTOR_FLAG_UPDATE_WHILE_CULLED;\n}\n\nvoid EnHealthFairy_Update(Actor* thisx, PlayState* play) {\n    EnHealthFairy* this = (EnHealthFairy*)thisx;\n    Player* player = GET_PLAYER(play);\n    \n    if (player->actor.health <= 16 && !this->fairySpawned) { // 1 heart or less\n        // Spawn fairy near player\n        Actor_Spawn(&play->actorCtx, play, ACTOR_EN_ELF, \n                   player->actor.world.pos.x, \n                   player->actor.world.pos.y + 50.0f,\n                   player->actor.world.pos.z, 0, 0, 0, 0);\n        this->fairySpawned = 1;\n        this->timer = 1800; // 30 second cooldown\n    }\n    \n    if (this->timer > 0) {\n        this->timer--;\n        if (this->timer == 0) {\n            this->fairySpawned = 0;\n        }\n    }\n}\n```\n\nThis actor continuously monitors the player's health and spawns a healing fairy when health drops to 1 heart or less, with a 30-second cooldown to prevent spam."
    }
    print(json.dumps(feature_implementation, indent=2))
    
    # Debugging Help Example
    print("\n3. Debugging Help Example:")
    debugging_help = {
        "instruction": "My custom actor crashes when I try to access its variables. Here's the code:",
        "input": "void MyActor_Init(Actor* thisx, PlayState* play) {\n    MyActor* this = (MyActor*)thisx;\n    this->customData->value = 100;\n    this->customData->initialized = 1;\n}",
        "output": "The crash occurs because `this->customData` is an uninitialized pointer. You're trying to dereference a NULL or garbage pointer value. Here's the corrected code:\n\n```c\nvoid MyActor_Init(Actor* thisx, PlayState* play) {\n    MyActor* this = (MyActor*)thisx;\n    \n    // Option 1: Allocate memory for customData\n    this->customData = ZELDA_ARENA_MALLOC(sizeof(CustomDataStruct), __FILE__, __LINE__);\n    if (this->customData == NULL) {\n        // Handle allocation failure\n        Actor_Kill(&this->actor);\n        return;\n    }\n    \n    // Now safe to access\n    this->customData->value = 100;\n    this->customData->initialized = 1;\n    \n    // Option 2: If customData should be part of the actor struct:\n    // Define it directly in the MyActor struct instead of as a pointer\n}\n\nvoid MyActor_Destroy(Actor* thisx, PlayState* play) {\n    MyActor* this = (MyActor*)thisx;\n    if (this->customData != NULL) {\n        ZELDA_ARENA_FREE(this->customData, __FILE__, __LINE__);\n    }\n}\n```\n\nAlways initialize pointers before use and remember to free allocated memory in the destructor."
    }
    print(json.dumps(debugging_help, indent=2))

def generate_sample_dataset():
    """Generate a small sample dataset for testing"""
    print("=== Generating Sample Dataset ===")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Set ANTHROPIC_API_KEY environment variable")
        return
    
    generator = OoTTrainingDataGenerator(api_key)
    
    # Generate small dataset for testing
    generator.generate_dataset(
        num_examples=10,
        output_file="sample_oot_training.jsonl"
    )
    
    print("Sample dataset generated: sample_oot_training.jsonl")
    
    # Show some statistics
    try:
        with open("sample_oot_training_metadata.json", 'r') as f:
            metadata = json.load(f)
            
        print(f"\nDataset Statistics:")
        print(f"Total examples: {metadata['total_examples']}")
        print(f"Average quality: {metadata['average_quality']:.1f}")
        print(f"Type distribution:")
        for example_type, count in metadata['type_distribution'].items():
            print(f"  {example_type}: {count}")
            
    except FileNotFoundError:
        print("Metadata file not found")

if __name__ == "__main__":
    print("OoT Training Data Generator - Usage Examples")
    print("==========================================")
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set the ANTHROPIC_API_KEY environment variable")
        print("export ANTHROPIC_API_KEY='your_api_key_here'")
        exit(1)
    
    # Run examples
    show_expected_outputs()
    print("\n" + "="*50 + "\n")
    
    # Uncomment to run live examples (requires API key)
    # example_basic_usage()
    # example_batch_generation() 
    # generate_sample_dataset()
    
    print("\nTo run live examples, uncomment the function calls at the bottom of this script")
    print("Make sure your ANTHROPIC_API_KEY environment variable is set")