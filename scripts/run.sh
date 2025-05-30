#!/bin/bash
# Shell script to run the MongoDB GUI application

echo "Starting MongoDB GUI Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python -c "import PyQt5; import pymongo; import keyring" &>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Update python version check or shebang if present

# Run the application
echo "Launching MongoDB GUI..."
python main.py
