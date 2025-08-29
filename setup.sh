#!/bin/bash
# Setup script for Website Monitor

echo "Setting up Website Monitor..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check for GROQ_API_KEY
if [ -z "$GROQ_API_KEY" ]; then
    echo "Warning: GROQ_API_KEY environment variable not set"
    echo "Please get your API key from: https://console.groq.com/"
    echo "Then set it with: export GROQ_API_KEY=your_api_key_here"
    echo ""
fi

echo "Setup complete!"
echo ""
echo "To run the monitor:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Set your API key: export GROQ_API_KEY=your_api_key_here"  
echo "3. Run the script: python website_monitor.py"
