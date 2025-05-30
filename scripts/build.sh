#!/bin/bash
# Build and package script for MongoDB GUI project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
CLEAN=false
DISTRIBUTION=false
WHEEL=false
SOURCE=false

# Function to show help
show_help() {
    echo -e "${GREEN}MongoDB GUI Build Script${NC}"
    echo "Usage: ./scripts/build.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo -e "  ${CYAN}-c, --clean${NC}       Clean build artifacts before building"
    echo -e "  ${CYAN}-d, --dist${NC}        Build both source and wheel distributions"
    echo -e "  ${CYAN}-w, --wheel${NC}       Build wheel distribution only"
    echo -e "  ${CYAN}-s, --source${NC}      Build source distribution only"
    echo -e "  ${CYAN}-h, --help${NC}        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/build.sh -d           # Build both distributions"
    echo "  ./scripts/build.sh -c -w        # Clean and build wheel"
    echo "  ./scripts/build.sh -s           # Build source only"
}

# Function to clean build artifacts
clean_build() {
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    echo -e "${GREEN}✓ Build artifacts cleaned${NC}"
}

# Function to run quality checks
run_checks() {
    echo -e "${YELLOW}Running quality checks...${NC}"
    
    # Type checking
    echo -e "${CYAN}Running MyPy type checking...${NC}"
    if ! mypy .; then
        echo -e "${RED}✗ Type checking failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Type checking passed${NC}"
    
    # Linting
    echo -e "${CYAN}Running Ruff linting...${NC}"
    if ! ruff check .; then
        echo -e "${RED}✗ Linting failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Linting passed${NC}"
    
    # Tests
    echo -e "${CYAN}Running tests...${NC}"
    if ! pytest tests/ -q; then
        echo -e "${RED}✗ Tests failed${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Tests passed${NC}"
    
    return 0
}

# Function to build package
build_package() {
    local build_args=""
    
    if [ "$WHEEL" = true ]; then
        build_args="--wheel"
    elif [ "$SOURCE" = true ]; then
        build_args="--sdist"
    fi
    
    echo -e "${YELLOW}Building package...${NC}"
    if python -m build $build_args; then
        echo -e "${GREEN}✓ Package built successfully${NC}"
        
        echo ""
        echo -e "${CYAN}Build artifacts:${NC}"
        ls -la dist/
        
        return 0
    else
        echo -e "${RED}✗ Package build failed${NC}"
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -d|--dist)
            DISTRIBUTION=true
            shift
            ;;
        -w|--wheel)
            WHEEL=true
            shift
            ;;
        -s|--source)
            SOURCE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Set default if no build type specified
if [ "$DISTRIBUTION" = false ] && [ "$WHEEL" = false ] && [ "$SOURCE" = false ]; then
    DISTRIBUTION=true
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Virtual environment not activated. Attempting to activate...${NC}"
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"
    else
        echo -e "${RED}Error: Virtual environment not found. Run './scripts/setup.sh' first.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}MongoDB GUI Build Process${NC}"
echo "=========================="

# Clean if requested
if [ "$CLEAN" = true ]; then
    clean_build
fi

# Run quality checks
if ! run_checks; then
    echo -e "${RED}Quality checks failed. Build aborted.${NC}"
    exit 1
fi

# Build package
if ! build_package; then
    exit 1
fi

echo ""
echo -e "${GREEN}Build completed successfully!${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  - Test the package: pip install dist/*.whl"
echo "  - Upload to PyPI: twine upload dist/*"
echo "  - Create GitHub release with the build artifacts"

# Update python version check or shebang if present
# ...existing code...
