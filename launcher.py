#!/usr/bin/env python3
"""
Cross-platform launcher for MongoDB GUI Application

This script automatically detects the platform and runs the appropriate
startup script or launches the application directly.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def detect_platform():
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system in ["linux", "darwin"]:
        return "unix"
    else:
        return "unknown"


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)


def run_command(command, shell=False):
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=shell, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def main():
    """Main launcher function."""
    print("MongoDB GUI Application Launcher")
    print("================================")
    
    # Check Python version
    check_python_version()
    
    # Detect platform
    platform_type = detect_platform()
    print(f"Detected platform: {platform_type}")    
    # Get script directory
    script_dir = Path(__file__).parent / "scripts"
    
    if platform_type == "windows":
        # Use PowerShell script for Windows
        powershell_script = script_dir / "run.ps1"
        
        print("Attempting to run PowerShell script...")
        if powershell_script.exists():
            if run_command(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(powershell_script)], shell=False):
                return
        else:
            print(f"PowerShell script not found: {powershell_script}")
                
    elif platform_type == "unix":
        # Try shell script
        shell_script = script_dir / "run.sh"
        
        print("Attempting to run shell script...")
        if shell_script.exists():
            # Make executable
            os.chmod(shell_script, 0o755)
            if run_command([str(shell_script)], shell=False):
                return
    
    # Fallback: run directly
    print("Scripts failed or not found, running application directly...")
    
    # Check if virtual environment exists
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", "venv"]):
            print("Failed to create virtual environment")
            sys.exit(1)
    
    # Determine Python executable in venv
    if platform_type == "windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    
    # Install dependencies if needed
    print("Checking dependencies...")
    try:
        import PyQt5
        import pymongo
        import keyring
        print("Dependencies already installed")
    except ImportError:
        print("Installing dependencies...")
        if not run_command([str(pip_exe), "install", "-r", "requirements.txt"]):
            print("Failed to install dependencies")
            sys.exit(1)
    
    # Run the application
    print("Starting MongoDB GUI...")
    try:
        subprocess.run([str(python_exe), "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Application failed to start: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
