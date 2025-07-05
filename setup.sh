#!/bin/bash

# OoT Training Data Generator Setup Script
# This script sets up the environment for generating training data

echo "🔗 OoT Romhack Training Data Generator Setup"
echo "============================================"

# Check Python version
echo "Checking Python version..."
python3 --version || {
    echo "❌ Python 3 is required but not installed"
    exit 1
}

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv oot_training_env

# Activate virtual environment
echo "Activating virtual environment..."
source oot_training_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install anthropic

# Create directories
echo "Creating project directories..."
mkdir -p data/training
mkdir -p data/metadata
mkdir -p examples

# Download the main script files
echo "Setting up project files..."

# Create a simple requirements.txt
cat > requirements.txt << EOF
anthropic>=0.25.0
EOF

# Create a .env template
cat > .env.template << EOF
# Copy this file to .env and add your API key
ANTHROPIC_API_KEY=
EOF

# Create a simple config file
cat > config.json << EOF
{
  "default_model": "claude-3-5-sonnet-20241022",
  "default_examples": 50,
  "quality_threshold": 6.0,
  "output_directory": "data/training"
}
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.template to .env and add your Anthropic API key"
echo "2. Activate the virtual environment: source oot_training_env/bin/activate"
echo "3. Run the generator: python oot_training_generator.py --api-key YOUR_KEY"
echo ""
echo "Example usage:"
echo "  python training_generator.py --api-key sk-... --num-examples 20 --output data/training/oot_samples.jsonl"
echo ""
echo "For more information, see the usage guide in the documentation."