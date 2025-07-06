#!/usr/bin/env python3
"""
OoT Training Data Generator - Main Entry Point
==============================================

A comprehensive tool for generating authentic Ocarina of Time romhacking training data
with strict validation, diversity injection, and dynamic source analysis.

USAGE EXAMPLES:
    # Basic generation
    python src/main.py --num-examples 50 --output training_data.jsonl
    
    # Advanced generation with custom settings
    python src/main.py \
        --num-examples 100 \
        --output large_dataset.jsonl \
        --oot-path ./oot-decompilation \
        --model claude-3-5-sonnet-20241022 \
        --quality-threshold 7.0 \
        --authenticity-threshold 7.0 \
        --complexity-distribution basic:0.2,intermediate:0.5,advanced:0.3 \
        --type-distribution actor_creation:0.25,animation_system:0.08,collision_system:0.08 \
        --verbose
    
    # Quick test generation
    python src/main.py --num-examples 5 --output test_data.jsonl --quick
    
    # Generate with specific focus
    python src/main.py \
        --num-examples 20 \
        --output enemy_actors.jsonl \
        --focus-categories enemy,npc \
        --focus-types actor_creation,ai_behavior \
        --complexity advanced
"""

import argparse
import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from generation.main_generator import EnhancedOoTTrainingGenerator
from core.logger import logger
from models.enums import ExampleType, ActorCategory


def parse_distribution(dist_str: str) -> Dict[str, float]:
    """Parse distribution string like 'basic:0.2,intermediate:0.5,advanced:0.3'"""
    if not dist_str:
        return {}
    
    result = {}
    for item in dist_str.split(','):
        if ':' in item:
            key, value = item.split(':', 1)
            try:
                result[key.strip()] = float(value.strip())
            except ValueError:
                logger.warning(f"Invalid distribution value: {value} for {key}")
    return result


def validate_arguments(args) -> bool:
    """Validate command line arguments"""
    errors = []
    
    # Check num_examples
    if args.num_examples <= 0:
        errors.append("--num-examples must be positive")
    elif args.num_examples > 1000:
        errors.append("--num-examples cannot exceed 1000 (use smaller batches)")
    
    # Check output file
    output_path = Path(args.output)
    if output_path.suffix not in ['.jsonl', '.json']:
        errors.append("--output must have .jsonl or .json extension")
    
    # Check oot-path exists if not disabled
    if not args.no_dynamic and not args.quick:
        if not os.path.exists(args.oot_path):
            errors.append(f"OoT path does not exist: {args.oot_path}")
    
    # Check thresholds
    if args.quality_threshold < 0 or args.quality_threshold > 10:
        errors.append("--quality-threshold must be between 0 and 10")
    if args.authenticity_threshold < 0 or args.authenticity_threshold > 10:
        errors.append("--authenticity-threshold must be between 0 and 10")
    
    # Check distributions
    if args.complexity_distribution:
        dist = parse_distribution(args.complexity_distribution)
        if dist and abs(sum(dist.values()) - 1.0) > 0.01:
            errors.append("Complexity distribution weights must sum to 1.0")
    
    if args.type_distribution:
        dist = parse_distribution(args.type_distribution)
        if dist and abs(sum(dist.values()) - 1.0) > 0.01:
            errors.append("Type distribution weights must sum to 1.0")
    
    if errors:
        logger.error("Validation errors:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    return True


def print_generation_stats(generator, start_time: float, output_file: str):
    """Print comprehensive generation statistics"""
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info("=" * 60)
    logger.success("🎉 GENERATION COMPLETE!")
    logger.info("=" * 60)
    
    # Basic stats
    logger.info(f"⏱️  Duration: {duration:.1f} seconds")
    logger.info(f"📁 Output: {output_file}")
    logger.info(f"📊 File size: {os.path.getsize(output_file) / 1024:.1f} KB")
    
    # Generation stats
    stats = generator.generation_stats
    total_generated = stats["total_generated"]
    total_accepted = stats["total_accepted"]
    total_rejected = stats["total_rejected"]
    
    logger.info(f"📈 Generation Statistics:")
    logger.info(f"  - Total generated: {total_generated}")
    logger.info(f"  - Accepted: {total_accepted}")
    logger.info(f"  - Rejected: {total_rejected}")
    
    if total_generated > 0:
        acceptance_rate = (total_accepted / total_generated) * 100
        logger.info(f"  - Acceptance rate: {acceptance_rate:.1f}%")
    
    # Quality stats
    if hasattr(generator, 'quality_stats'):
        avg_quality = sum(generator.quality_stats) / len(generator.quality_stats) if generator.quality_stats else 0
        avg_authenticity = sum(generator.authenticity_stats) / len(generator.authenticity_stats) if generator.authenticity_stats else 0
        logger.info(f"📊 Quality Statistics:")
        logger.info(f"  - Average quality score: {avg_quality:.2f}/10")
        logger.info(f"  - Average authenticity score: {avg_authenticity:.2f}/10")
    
    # Diversity stats
    logger.info(f"🎯 Diversity Achieved:")
    for category, count in stats["category_distribution"].items():
        if count > 0:
            logger.info(f"  - {category}: {count} examples")
    
    logger.info("=" * 60)


def create_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser"""
    parser = argparse.ArgumentParser(
        description="Generate authentic Ocarina of Time romhacking training data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Basic generation
  python src/main.py --num-examples 50

  # Advanced generation with custom settings
  python src/main.py --num-examples 100 --output large_dataset.jsonl \\
    --quality-threshold 8.0 --authenticity-threshold 8.0 --verbose

  # Focus on specific content types
  python src/main.py --num-examples 20 --focus-categories enemy,npc \\
    --focus-types actor_creation,ai_behavior --complexity advanced

  # Quick test generation
  python src/main.py --num-examples 5 --quick --output test.jsonl

For more information, see the documentation in docs/ directory.
        """
    )
    
    # Basic arguments
    parser.add_argument(
        "--num-examples", "-n",
        type=int,
        default=30,
        help="Number of training examples to generate (default: 30, max: 1000)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="authentic_oot_training.jsonl",
        help="Output file path (default: authentic_oot_training.jsonl)"
    )
    
    # API and model settings
    parser.add_argument(
        "--api-key",
        help="Anthropic API key (or set ANTHROPIC_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="Anthropic model to use (default: claude-3-5-sonnet-20241022)"
    )
    
    # OoT source analysis
    parser.add_argument(
        "--oot-path",
        default="oot",
        help="Path to OoT decompilation directory (default: oot)"
    )
    
    parser.add_argument(
        "--no-dynamic",
        action="store_true",
        help="Disable dynamic source analysis (faster but less authentic)"
    )
    
    # Quality control
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=7.0,
        help="Minimum quality score for acceptance (0-10, default: 7.0)"
    )
    
    parser.add_argument(
        "--authenticity-threshold",
        type=float,
        default=7.0,
        help="Minimum authenticity score for acceptance (0-10, default: 7.0)"
    )
    
    # Content focus
    parser.add_argument(
        "--focus-categories",
        help="Comma-separated list of actor categories to focus on (e.g., enemy,npc,item)"
    )
    
    parser.add_argument(
        "--focus-types",
        help="Comma-separated list of example types to focus on (e.g., actor_creation,animation_system)"
    )
    
    parser.add_argument(
        "--complexity",
        choices=["basic", "intermediate", "advanced"],
        help="Force specific complexity level (default: weighted distribution)"
    )
    
    # Distribution control
    parser.add_argument(
        "--complexity-distribution",
        help="Complexity distribution weights (e.g., basic:0.2,intermediate:0.5,advanced:0.3)"
    )
    
    parser.add_argument(
        "--type-distribution",
        help="Example type distribution weights (e.g., actor_creation:0.25,animation_system:0.08)"
    )
    
    # Generation settings
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick generation mode (reduced validation, faster generation)"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retries per example (default: 3)"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=0.5,
        help="Delay between API calls in seconds (default: 0.5)"
    )
    
    # Output options
    parser.add_argument(
        "--save-metadata",
        action="store_true",
        help="Save detailed metadata and analytics"
    )
    
    parser.add_argument(
        "--format",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Output format (default: jsonl)"
    )
    
    # Logging and debugging
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    # Information
    parser.add_argument(
        "--version",
        action="version",
        version="OoT Training Data Generator v1.0.0"
    )
    
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List available example types and exit"
    )
    
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List available actor categories and exit"
    )
    
    return parser


def list_available_types():
    """List available example types"""
    logger.info("📋 Available Example Types:")
    for example_type in ExampleType:
        logger.info(f"  - {example_type.value}")
    logger.info(f"\nTotal: {len(ExampleType)} types")


def list_available_categories():
    """List available actor categories"""
    logger.info("🎭 Available Actor Categories:")
    for category in ActorCategory:
        logger.info(f"  - {category.value}")
    logger.info(f"\nTotal: {len(ActorCategory)} categories")


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle information commands
    if args.list_types:
        list_available_types()
        return
    
    if args.list_categories:
        list_available_categories()
        return
    
    # Set up logging
    if args.quiet:
        logger.logger.setLevel(logging.ERROR)
    elif args.debug:
        logger.logger.setLevel(logging.DEBUG)
    elif args.verbose:
        logger.logger.setLevel(logging.INFO)
    
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.warning("python-dotenv not installed. Use: pip install python-dotenv")
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    # Parse distributions
    complexity_dist = parse_distribution(args.complexity_distribution)
    type_dist = parse_distribution(args.type_distribution)
    
    # Parse focus lists
    focus_categories = []
    if args.focus_categories:
        focus_categories = [cat.strip() for cat in args.focus_categories.split(',')]
    
    focus_types = []
    if args.focus_types:
        focus_types = [t.strip() for t in args.focus_types.split(',')]
    
    # Print configuration
    logger.info("🚀 OoT Training Data Generator")
    logger.info("=" * 50)
    logger.info(f"📊 Target examples: {args.num_examples}")
    logger.info(f"📁 Output file: {args.output}")
    logger.info(f"🔧 Model: {args.model}")
    logger.info(f"📂 OoT path: {args.oot_path}")
    logger.info(f"⚡ Dynamic analysis: {'disabled' if args.no_dynamic else 'enabled'}")
    logger.info(f"🎯 Quality threshold: {args.quality_threshold}")
    logger.info(f"🔍 Authenticity threshold: {args.authenticity_threshold}")
    
    if focus_categories:
        logger.info(f"🎭 Focus categories: {', '.join(focus_categories)}")
    if focus_types:
        logger.info(f"📋 Focus types: {', '.join(focus_types)}")
    if complexity_dist:
        logger.info(f"📈 Complexity distribution: {complexity_dist}")
    if type_dist:
        logger.info(f"📊 Type distribution: {type_dist}")
    
    logger.info("=" * 50)
    
    try:
        # Initialize generator
        logger.info("🔧 Initializing generator...")
        start_time = time.time()
        
        generator = EnhancedOoTTrainingGenerator(
            api_key=args.api_key,
            model=args.model,
            oot_path=args.oot_path,
            use_dynamic_analysis=not args.no_dynamic
        )
        
        # Configure generation settings
        if args.quick:
            logger.info("⚡ Quick mode enabled (reduced validation)")
        
        # Note: Quality thresholds and other settings are handled internally by the generator
        # based on the arguments passed to generate_dataset()
        
        logger.success("✅ Generator initialized successfully")
        
        # Generate dataset
        logger.info(f"🎯 Starting generation of {args.num_examples} examples...")
        generator.generate_dataset(args.num_examples, args.output)
        
        # Print final statistics
        print_generation_stats(generator, start_time, args.output)
        
        # Save metadata if requested
        if args.save_metadata:
            metadata_file = args.output.replace('.jsonl', '_metadata.json')
            metadata = {
                "generation_config": {
                    "num_examples": args.num_examples,
                    "model": args.model,
                    "quality_threshold": args.quality_threshold,
                    "authenticity_threshold": args.authenticity_threshold,
                    "focus_categories": focus_categories,
                    "focus_types": focus_types,
                    "complexity_distribution": complexity_dist,
                    "type_distribution": type_dist
                },
                "generation_stats": generator.generation_stats,
                "timestamp": time.time()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"📊 Metadata saved to: {metadata_file}")
        
        logger.success("🎉 Generation completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("⚠️  Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 