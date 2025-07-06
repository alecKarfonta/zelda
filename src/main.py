#!/usr/bin/env python3
"""
Main Entry Point for OoT Training Data Generator
"""

import argparse
import os

from generation.main_generator import EnhancedOoTTrainingGenerator
from core.logger import logger


def main():
    parser = argparse.ArgumentParser(description="Generate strictly authentic OoT training data with dynamic source analysis")
    parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY env var)")
    parser.add_argument("--num-examples", type=int, default=30, help="Number of examples to generate")
    parser.add_argument("--output", default="authentic_oot_training.jsonl", help="Output file")
    parser.add_argument("--oot-path", default="oot", help="Path to OoT decompilation directory")
    parser.add_argument("--no-dynamic", action="store_true", help="Disable dynamic source analysis")
    
    args = parser.parse_args()
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed. Use pip install python-dotenv")
    
    generator = EnhancedOoTTrainingGenerator(
        api_key=args.api_key,
        oot_path=args.oot_path, 
        use_dynamic_analysis=not args.no_dynamic
    )
    generator.generate_dataset(args.num_examples, args.output)


if __name__ == "__main__":
    main() 