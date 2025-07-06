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
        --enable-compilation \
        --verbose
    
    # For parsing and analysis, use parse_logs.py instead:
    python parse_logs.py --summary --input large_generation_20.jsonl
    python parse_logs.py --conform
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for the wrapper script"""
    
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