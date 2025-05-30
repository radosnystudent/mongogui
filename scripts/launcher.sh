#!/bin/bash
# Cross-platform launcher script for MongoDB GUI

# Detect the operating system
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    MSYS*)      MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: $MACHINE"

# Check if we're on a Unix-like system
if [[ "$MACHINE" == "Linux" || "$MACHINE" == "Mac" ]]; then
    echo "Using shell scripts for Unix-like system..."
    
    # Make scripts executable if they aren't already
    chmod +x scripts/*.sh 2>/dev/null || true
    
    # Update python version check or shebang if present
    for script in scripts/*.sh; do
        if grep -q -E 'python[[:space:]]+([2-9][0-9]*\.[0-9]+|[0-9]+\.[0-9]+)' "$script"; then
            sed -i.bak -E 's/python[[:space:]]+([2-9][0-9]*\.[0-9]+|[0-9]+\.[0-9]+)/python3.11/' "$script"
            echo "Updated Python version in $script"
        fi
    done
    
    # Run the application
    ./scripts/run.sh
    
elif [[ "$MACHINE" == "Cygwin" || "$MACHINE" == "MinGw" ]]; then
    echo "Detected Windows environment in Unix shell..."
    echo "You can use either:"
    echo "1. ./scripts/run.sh (if in WSL/MSYS2/Cygwin)"
    echo "2. scripts/run.ps1 (PowerShell)"
    echo "3. scripts/run.bat (Command Prompt)"
    
    # Try to use the shell script
    chmod +x scripts/*.sh 2>/dev/null || true
    ./scripts/run.sh
    
else
    echo "Unknown or Windows system detected."
    echo "Please use one of these scripts directly:"
    echo "- scripts/run.ps1 (PowerShell)"
    echo "- scripts/run.bat (Command Prompt)"
    echo "- scripts/run.sh (WSL/Linux)"
fi
