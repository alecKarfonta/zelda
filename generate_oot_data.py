#!/usr/bin/env python3
"""
OoT Training Data Generator - Easy Wrapper Script
================================================

This script provides an easy way to run the OoT training data generator
without having to remember the PYTHONPATH and virtual environment setup.

USAGE:
    python generate_oot_data.py --num-examples 50 --output training_data.jsonl
    
    # Quick test
    python generate_oot_data.py --num-examples 5 --quick --output test.jsonl
    
    # Advanced generation
    python generate_oot_data.py \
        --num-examples 100 \
        --output large_dataset.jsonl \
        --quality-threshold 8.0 \
        --authenticity-threshold 8.0 \
        --focus-categories enemy,npc \
        --focus-types actor_creation,ai_behavior \
        --complexity advanced \
        --verbose
    
    # Generate summary analysis
    python generate_oot_data.py --summary --input large_generation_20.jsonl
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from collections import defaultdict

def flatten_nested_structures(entry):
    """Flatten nested JSON structures within the output field."""
    if 'output' in entry:
        output = entry['output']
        
        # Check if output contains a nested JSON structure
        if isinstance(output, str) and output.strip().startswith('{'):
            try:
                nested_data = json.loads(output)
                
                # If nested data has instruction and output, use those
                if 'instruction' in nested_data and 'output' in nested_data:
                    entry['instruction'] = nested_data['instruction']
                    entry['output'] = nested_data['output']
                    print(f"Flattened nested structure: {nested_data['instruction'][:50]}...")
                    
            except json.JSONDecodeError:
                # If it's not valid JSON, keep the original output
                pass
    
    return entry

def analyze_jsonl(jsonl_file):
    """Analyze the JSONL file and extract key information."""
    entries = []
    actor_stats = defaultdict(int)
    function_stats = defaultdict(int)
    category_stats = defaultdict(int)
    
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                
                # Handle nested JSON structures in output field
                entry = flatten_nested_structures(entry)
                
                instruction = entry.get('instruction', '')
                output = entry.get('output', '')
                
                # Extract actors
                actor_pattern = r'En([A-Z][a-zA-Z]+)'
                actors = re.findall(actor_pattern, output)
                
                # Extract functions
                func_pattern = r'void ([A-Za-z_]+)\([^)]*\)'
                functions = re.findall(func_pattern, output)
                
                # Categorize by instruction keywords
                instruction_lower = instruction.lower()
                if 'actor' in instruction_lower or 'creation' in instruction_lower:
                    category = 'Actor Systems'
                elif 'animation' in instruction_lower or 'anim' in instruction_lower:
                    category = 'Animation'
                elif 'physics' in instruction_lower or 'cloth' in instruction_lower:
                    category = 'Physics'
                elif 'ai' in instruction_lower or 'behavior' in instruction_lower:
                    category = 'AI & Behavior'
                elif 'combat' in instruction_lower or 'enemy' in instruction_lower:
                    category = 'Combat'
                elif 'puzzle' in instruction_lower or 'door' in instruction_lower:
                    category = 'Puzzle'
                elif 'sound' in instruction_lower or 'voice' in instruction_lower:
                    category = 'Sound'
                elif 'memory' in instruction_lower or 'optimization' in instruction_lower:
                    category = 'Memory & Optimization'
                elif 'debug' in instruction_lower or 'error' in instruction_lower:
                    category = 'Debug & Error Handling'
                elif 'equipment' in instruction_lower or 'inventory' in instruction_lower:
                    category = 'Equipment & Inventory'
                else:
                    category = 'Other'
                
                category_stats[category] += 1
                
                for actor in actors:
                    actor_stats[actor] += 1
                
                for func in functions:
                    function_stats[func] += 1
                
                entries.append({
                    'line': line_num,
                    'instruction': instruction,
                    'actors': list(set(actors)),
                    'functions': list(set(functions)),
                    'category': category
                })
                
            except Exception as e:
                print(f"Error processing line {line_num}: {e}")
    
    return entries, actor_stats, function_stats, category_stats

def print_final_summary(entries, actor_stats, function_stats, category_stats):
    """Print a comprehensive final summary."""
    print("=" * 100)
    print("FINAL SUMMARY: ZELDA OOT ACTOR SYSTEM GENERATION ANALYSIS")
    print("=" * 100)
    print()
    
    # Overall statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 50)
    print(f"Total Entries: {len(entries)}")
    print(f"Unique Actor Types: {len(actor_stats)}")
    print(f"Unique Functions: {len(function_stats)}")
    print(f"Categories: {len(category_stats)}")
    print()
    
    # Category breakdown
    print("📂 CATEGORY BREAKDOWN")
    print("-" * 50)
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"{category:25} | {count:2d} entries")
    print()
    
    # Top actors
    print("🎭 TOP ACTOR TYPES")
    print("-" * 50)
    for actor, count in sorted(actor_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{actor:20} | {count:2d} occurrences")
    print()
    
    # Top functions
    print("🔧 TOP FUNCTIONS")
    print("-" * 50)
    for func, count in sorted(function_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{func:25} | {count:2d} occurrences")
    print()
    
    # Detailed breakdown
    print("📋 DETAILED ENTRY BREAKDOWN")
    print("-" * 100)
    
    for i, entry in enumerate(entries, 1):
        print(f"\n{i:2d}. Line {entry['line']:2d} | {entry['category']}")
        print(f"    Instruction: {entry['instruction'][:70]}{'...' if len(entry['instruction']) > 70 else ''}")
        print(f"    Actors: {', '.join(entry['actors']) if entry['actors'] else 'None'}")
        print(f"    Functions: {', '.join(entry['functions'][:3])}{'...' if len(entry['functions']) > 3 else ''}")
    
    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

def run_summary_analysis(input_file):
    """Run summary analysis on a JSONL file."""
    try:
        entries, actor_stats, function_stats, category_stats = analyze_jsonl(input_file)
        print_final_summary(entries, actor_stats, function_stats, category_stats)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found!")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main entry point for the wrapper script"""
    
    # Check if summary mode is requested
    if '--summary' in sys.argv:
        # Extract input file from arguments
        input_file = "large_generation_20.jsonl"  # default
        for i, arg in enumerate(sys.argv):
            if arg == '--input' and i + 1 < len(sys.argv):
                input_file = sys.argv[i + 1]
                break
        
        print(f"📊 Running summary analysis on: {input_file}")
        run_summary_analysis(input_file)
        return
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        # Try to activate virtual environment
        venv_paths = [
            script_dir / "venv" / "bin" / "activate",
            script_dir / "oot_training_env" / "bin" / "activate",
        ]
        
        venv_activated = False
        for venv_path in venv_paths:
            if venv_path.exists():
                print(f"🔧 Activating virtual environment: {venv_path}")
                # Source the virtual environment and run the main script
                cmd = f"source {venv_path} && PYTHONPATH={script_dir} python {script_dir}/src/main.py"
                cmd += " " + " ".join(sys.argv[1:])
                
                # Use bash to run the command
                result = subprocess.run(cmd, shell=True, executable='/bin/bash')
                sys.exit(result.returncode)
        
        if not venv_activated:
            print("❌ No virtual environment found!")
            print("Please create a virtual environment first:")
            print("  python -m venv venv")
            print("  source venv/bin/activate")
            print("  pip install -r requirements.txt")
            sys.exit(1)
    else:
        # We're already in a virtual environment, just run the main script
        cmd = f"PYTHONPATH={script_dir} python {script_dir}/src/main.py"
        cmd += " " + " ".join(sys.argv[1:])
        
        result = subprocess.run(cmd, shell=True)
        sys.exit(result.returncode)

if __name__ == "__main__":
    main() 