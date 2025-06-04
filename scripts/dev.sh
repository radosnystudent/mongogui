#!/bin/bash
# Shell script for MongoDB GUI project development tasks

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to show help
show_help() {
    echo -e "${GREEN}Available commands:${NC}"
    echo -e "  ${CYAN}install${NC}        Install production dependencies"
    echo -e "  ${CYAN}install-dev${NC}    Install development dependencies"
    echo -e "  ${CYAN}format${NC}         Format code with Black"
    echo -e "  ${CYAN}format-check${NC}   Check code formatting with Black"
    echo -e "  ${CYAN}lint${NC}           Lint code with Ruff"
    echo -e "  ${CYAN}lint-fix${NC}       Lint and fix code with Ruff"
    echo -e "  ${CYAN}type-check${NC}     Run type checking with Mypy"
    echo -e "  ${CYAN}security${NC}       Run security checks with Bandit"
    echo -e "  ${CYAN}test${NC}           Run tests with pytest"
    echo -e "  ${CYAN}test-cov${NC}       Run tests with coverage"
    echo -e "  ${CYAN}build${NC}          Build the package"
    echo -e "  ${CYAN}clean${NC}          Clean build artifacts"
    echo -e "  ${CYAN}all${NC}            Run all checks"
    echo -e "  ${CYAN}all-checks${NC}     Run lint, mypy, format-check, and tests"
    echo -e "  ${CYAN}dev-setup${NC}      Set up development environment"
    echo ""
    echo -e "${YELLOW}Usage: ./scripts/dev.sh <command>${NC}"
}

# Function to install production dependencies
install_prod() {
    echo -e "${GREEN}Installing production dependencies...${NC}"
    pip install -r requirements.txt
}

# Function to install development dependencies
install_dev() {
    echo -e "${GREEN}Installing development dependencies...${NC}"
    pip install -r requirements.txt -r requirements-dev.txt
}

# Function to format code
format_code() {
    echo -e "${GREEN}Formatting code with Black...${NC}"
    black .
}

# Function to check code formatting
check_format() {
    echo -e "${GREEN}Checking code formatting with Black...${NC}"
    black --check .
}

# Function to lint code
lint_code() {
    echo -e "${GREEN}Linting code with Ruff...${NC}"
    ruff check .
}

# Function to lint and fix code
lint_fix() {
    echo -e "${GREEN}Linting and fixing code with Ruff...${NC}"
    ruff check --fix .
}

# Function to run type checking
type_check() {
    echo -e "${GREEN}Running type checking with Mypy...${NC}"
    mypy .
}

# Function to run security checks
security_check() {
    echo -e "${GREEN}Running security checks with Bandit...${NC}"
    bandit -r . -f json -o bandit-report.json
    bandit -r .
}

# Function to run tests
run_tests() {
    echo -e "${GREEN}Running tests with pytest...${NC}"
    pytest
}

# Function to run tests with coverage
run_tests_cov() {
    echo -e "${GREEN}Running tests with coverage...${NC}"
    pytest --cov=. --cov-report=html --cov-report=term
}

# Function to build package
build_package() {
    echo -e "${GREEN}Building package...${NC}"
    python -m build
}

# Function to clean artifacts
clean_artifacts() {
    echo -e "${GREEN}Cleaning build artifacts...${NC}"
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    rm -rf .mypy_cache/
    rm -rf .pytest_cache/
    rm -rf .ruff_cache/
    rm -rf htmlcov/
    rm -f .coverage
    rm -f bandit-report.json
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
}

# Function to run all checks
run_all() {
    echo -e "${GREEN}Running all checks...${NC}"
    format_code
    lint_code
    type_check
    security_check
    run_tests
}

# Function to run all static checks and tests
all_checks() {
    echo -e "${GREEN}Running all static checks and tests...${NC}"
    lint_code
    type_check
    check_format
    run_tests
}

# Function to set up development environment
dev_setup() {
    echo -e "${GREEN}Setting up development environment...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    install_dev
    echo -e "${GREEN}Development environment setup complete!${NC}"
    echo -e "${YELLOW}Run './scripts/dev.sh help' to see available commands.${NC}"
}

# Main script logic
case "${1:-help}" in
    "help")
        show_help
        ;;
    "install")
        install_prod
        ;;
    "install-dev")
        install_dev
        ;;
    "format")
        format_code
        ;;
    "format-check")
        check_format
        ;;
    "lint")
        lint_code
        ;;
    "lint-fix")
        lint_fix
        ;;
    "type-check")
        type_check
        ;;
    "security")
        security_check
        ;;
    "test")
        run_tests
        ;;
    "test-cov")
        run_tests_cov
        ;;
    "build")
        build_package
        ;;
    "clean")
        clean_artifacts
        ;;
    "all")
        run_all
        ;;
    "all-checks")
        all_checks
        ;;
    "dev-setup")
        dev_setup
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_help
        exit 1
        ;;
esac

# Update python version check or shebang if present
