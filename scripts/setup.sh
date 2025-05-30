#!/bin/bash
# Setup script for MongoDB GUI project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}MongoDB GUI - Project Setup${NC}"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not in PATH${NC}"
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo -e "${RED}Error: pip is not installed or not in PATH${NC}"
    echo "Please install pip and try again."
    exit 1
fi

echo -e "${GREEN}✓ pip is available${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install production dependencies
echo -e "${YELLOW}Installing production dependencies...${NC}"
pip install -r requirements.txt

# Install development dependencies
echo -e "${YELLOW}Installing development dependencies...${NC}"
pip install -r requirements-dev.txt

echo ""
echo -e "${GREEN}Setup completed successfully!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the application: ./scripts/run.sh"
echo "3. For development commands: ./scripts/dev.sh help"
echo ""
echo -e "${YELLOW}Note: Make sure you have a MongoDB instance running to test the application.${NC}"
