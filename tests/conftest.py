"""
Configuration for pytest.
This file is automatically loaded by pytest.
"""
import os
import sys
from collections.abc import Generator

import pytest
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest before tests are run."""
    # Force Qt API to be PyQt6
    os.environ["PYTEST_QT_API"] = "pyqt6"

    # For headless environments in CI
    if os.environ.get("CI"):
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Debug info
    print(f"Python version: {sys.version}")
    print(f"Using pytest-qt API: {os.environ.get('PYTEST_QT_API', 'not set')}")


@pytest.fixture
def qapp(
    qapp_args: list[str],
) -> Generator[QApplication | QCoreApplication, None, None]:
    """Override the default qapp fixture to ensure proper setup."""

    app = QApplication.instance()
    if app is None:
        app = QApplication(qapp_args)

    yield app

    app.quit()
