# MongoDB GUI Scripts

This directory contains shell scripts for managing the MongoDB GUI project on Linux/macOS systems.

## Scripts Overview

### 🚀 `run.sh`

Main application launcher script.

```bash
./scripts/run.sh
```

- Creates virtual environment if needed
- Installs dependencies automatically
- Launches the MongoDB GUI application

### 🛠️ `dev.sh`

Development task runner with multiple commands.

```bash
./scripts/dev.sh <command>
```

**Available commands:**

- `install` - Install production dependencies
- `install-dev` - Install development dependencies
- `format` - Format code with Black
- `format-check` - Check code formatting
- `lint` - Lint code with Ruff
- `lint-fix` - Lint and auto-fix issues
- `type-check` - Run MyPy type checking
- `security` - Run Bandit security checks
- `test` - Run pytest tests
- `test-cov` - Run tests with coverage
- `build` - Build the package
- `clean` - Clean build artifacts
- `all` - Run all quality checks
- `dev-setup` - Set up development environment

### 📦 `setup.sh`

Initial project setup script.

```bash
./scripts/setup.sh
```

- Checks Python version compatibility
- Creates virtual environment
- Installs all dependencies
- Prepares the project for development

### 🧪 `test.sh`

Advanced test runner with options.

```bash
./scripts/test.sh [OPTIONS]
```

**Options:**

- `-c, --coverage` - Run with coverage report
- `-v, --verbose` - Verbose test output
- `-t, --test TEST` - Run specific test file
- `-h, --help` - Show help

**Examples:**

```bash
./scripts/test.sh                           # Run all tests
./scripts/test.sh -c                        # Run with coverage
./scripts/test.sh -v                        # Verbose mode
./scripts/test.sh -t connection_manager     # Specific test
./scripts/test.sh -c -v                     # Coverage + verbose
```

### 🏗️ `build.sh`

Package building and distribution script.

```bash
./scripts/build.sh [OPTIONS]
```

**Options:**

- `-c, --clean` - Clean before building
- `-d, --dist` - Build both source and wheel
- `-w, --wheel` - Build wheel only
- `-s, --source` - Build source only
- `-h, --help` - Show help

**Examples:**

```bash
./scripts/build.sh -d           # Build distributions
./scripts/build.sh -c -w        # Clean and build wheel
./scripts/build.sh -s           # Source distribution only
```

## Prerequisites

### System Requirements

- **Linux/macOS**: These scripts are designed for Unix-like systems
- **Python 3.8+**: Required for the application
- **pip**: Python package installer
- **Bash**: Shell interpreter (usually pre-installed)

### Package Dependencies

The scripts will automatically install:

- **Production**: PyQt5, pymongo, keyring
- **Development**: pytest, mypy, ruff, black, bandit, build

## Quick Start

1. **Initial Setup** (first time only):

   ```bash
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

2. **Run the Application**:

   ```bash
   ./scripts/run.sh
   ```

3. **Development Workflow**:

   ```bash
   # Make code changes
   ./scripts/dev.sh format      # Format code
   ./scripts/dev.sh lint        # Check linting
   ./scripts/dev.sh type-check  # Type checking
   ./scripts/dev.sh test        # Run tests
   ```

4. **Build for Distribution**:
   ```bash
   ./scripts/build.sh -d
   ```

## Script Permissions

Make scripts executable after cloning:

```bash
chmod +x scripts/*.sh
```

Or make individual scripts executable:

```bash
chmod +x scripts/run.sh
chmod +x scripts/dev.sh
chmod +x scripts/setup.sh
chmod +x scripts/test.sh
chmod +x scripts/build.sh
```

## Virtual Environment

All scripts automatically:

- Create a virtual environment (`venv/`) if it doesn't exist
- Activate the virtual environment
- Install required dependencies

The virtual environment is shared across all scripts for consistency.

## Error Handling

All scripts include:

- ✅ Dependency checking
- ✅ Virtual environment management
- ✅ Colored output for better readability
- ✅ Proper error codes and messages
- ✅ Help documentation

## Integration with CI/CD

These scripts are designed to work well in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Setup and test
  run: |
    ./scripts/setup.sh
    ./scripts/test.sh -c
    ./scripts/build.sh -d
```

## Customization

Scripts can be easily modified for your specific needs:

- Edit color schemes in the color variables section
- Add new commands to `dev.sh`
- Modify dependency lists
- Add custom build steps to `build.sh`

## Troubleshooting

### Permission Denied

```bash
chmod +x scripts/*.sh
```

### Python Not Found

Ensure Python 3.8+ is installed and available as `python3`:

```bash
python3 --version
```

### Virtual Environment Issues

Delete and recreate the virtual environment:

```bash
rm -rf venv/
./scripts/setup.sh
```

### Dependencies Not Installing

Check your internet connection and pip configuration:

```bash
pip install --upgrade pip
./scripts/setup.sh
```

## Compatibility

These scripts are tested on:

- ✅ Ubuntu 20.04+
- ✅ Debian 10+
- ✅ CentOS 8+
- ✅ macOS 10.15+
- ✅ Arch Linux
- ✅ WSL (Windows Subsystem for Linux)

For Windows users, use the original PowerShell scripts or WSL with these shell scripts.
