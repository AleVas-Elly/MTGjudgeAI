#!/bin/bash

# MTG AI Judge - Single Command Setup Script
# Works on macOS and Linux

echo "🔮 Starting MTG AI Judge Professional Setup..."

# 1. Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

# 2. Install dependencies
echo "📦 Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 3. Initialize data (Rulebook, Index, B&R Sync)
echo "🧠 Initialising data and rulebook indexes..."
python -m src.data_setup

echo "✨ Setup complete! You can now run the Judge with: python -m src.main"
