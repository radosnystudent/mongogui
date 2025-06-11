#!/usr/bin/env python3
"""
Cross-platform launcher for MongoDB GUI Application

This script automatically detects the platform and runs the appropriate
startup script or launches the application directly.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def detect_platform() -> str:
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system in ["linux", "darwin"]:
        return "unix"
    else:
        return "unknown"


def run_command(command: list[str], shell: bool = False) -> bool:
    """Run a command and return success status. Only supports list[str] for command."""
    if shell:
        raise ValueError(
            "shell=True is not supported for run_command in this launcher."
        )
    try:
        result = subprocess.run(command, shell=False, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False
    except FileNotFoundError:
        return False


def main() -> None:
    """Main launcher function."""
    print("MongoDB GUI Application Launcher")
    print("================================")

    platform_type = detect_platform()
    print(f"Detected platform: {platform_type}")
    script_dir = Path(__file__).parent / "scripts"

    if try_run_platform_script(platform_type, script_dir):
        return

    print("Scripts failed or not found, running application directly...")
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", "venv"]):
            print("Failed to create virtual environment")
            sys.exit(1)

    python_exe, pip_exe = get_venv_executables(platform_type, venv_path)
    ensure_dependencies(pip_exe)
    run_application(python_exe)


def try_run_platform_script(platform_type: str, script_dir: Path) -> bool:
    """Try to run the platform-specific script. Returns True if successful."""
    if platform_type == "windows":
        powershell_script = script_dir / "run.ps1"
        print("Attempting to run PowerShell script...")
        if powershell_script.exists():
            if run_command(
                [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(powershell_script),
                ],
                shell=False,
            ):
                return True
        else:
            print(f"PowerShell script not found: {powershell_script}")
    elif platform_type == "unix":
        shell_script = script_dir / "run.sh"
        print("Attempting to run shell script...")
        if shell_script.exists():
            # nosec B103: Chmod setting a permissive mask 0o755 on file (shell_script).
            # This is required to make the script executable, not a security risk in this context.
            os.chmod(shell_script, 0o755)
            if run_command([str(shell_script)], shell=False):
                return True
    return False


def get_venv_executables(platform_type: str, venv_path: Path) -> tuple[Path, Path]:
    """Return the python and pip executables for the venv."""
    if platform_type == "windows":
        python_exe = venv_path / "Scripts" / "python.exe"
        pip_exe = venv_path / "Scripts" / "pip.exe"
    else:
        python_exe = venv_path / "bin" / "python"
        pip_exe = venv_path / "bin" / "pip"
    return python_exe, pip_exe


def ensure_dependencies(pip_exe: Path) -> None:
    """Ensure all dependencies are installed."""
    print("Checking dependencies...")
    try:
        import importlib.util

        for pkg in ["keyring", "pymongo", "PyQt5"]:
            if importlib.util.find_spec(pkg) is None:
                raise ImportError(f"{pkg} not found")
        print("Dependencies already installed")
    except ImportError:
        print("Installing dependencies...")
        if not run_command([str(pip_exe), "install", "-r", "requirements.txt"]):
            print("Failed to install dependencies")
            sys.exit(1)


def run_application(python_exe: Path) -> None:
    """Run the main application."""
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
