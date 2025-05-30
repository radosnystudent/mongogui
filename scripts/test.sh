#!/bin/bash
# Test runner script for MongoDB GUI project

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

# Function to show help
show_help() {
    echo -e "${GREEN}MongoDB GUI Test Runner${NC}"
    echo "Usage: ./scripts/test.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo -e "  ${CYAN}-c, --coverage${NC}    Run tests with coverage report"
    echo -e "  ${CYAN}-v, --verbose${NC}     Run tests in verbose mode"
    echo -e "  ${CYAN}-t, --test TEST${NC}   Run specific test file or function"
    echo -e "  ${CYAN}-h, --help${NC}        Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./scripts/test.sh                           # Run all tests"
    echo "  ./scripts/test.sh -c                        # Run with coverage"
    echo "  ./scripts/test.sh -v                        # Run in verbose mode"
    echo "  ./scripts/test.sh -t test_connection_manager # Run specific test file"
    echo "  ./scripts/test.sh -c -v                     # Run with coverage and verbose"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
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

# Update python version check or shebang if present
# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term --cov-report=xml"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD tests/test_$SPECIFIC_TEST.py"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

echo -e "${GREEN}Running tests...${NC}"
echo -e "${CYAN}Command: $PYTEST_CMD${NC}"
echo ""

# Run the tests
$PYTEST_CMD

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${CYAN}Coverage report generated:${NC}"
        echo "  - HTML: htmlcov/index.html"
        echo "  - XML: coverage.xml"
        echo "  - Terminal output above"
    fi
else
    echo ""
    echo -e "${RED}✗ Some tests failed!${NC}"
    exit 1
fi
