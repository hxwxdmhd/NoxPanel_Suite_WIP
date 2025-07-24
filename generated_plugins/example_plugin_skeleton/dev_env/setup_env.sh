#!/bin/bash
# Development environment setup for plugin

echo "Setting up development environment..."

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov flake8 black mypy

echo "Development environment setup complete!"
echo "Activate with: source venv/bin/activate"
