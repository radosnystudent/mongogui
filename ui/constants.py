import os

"""
Constants for UI elements and configuration in the MongoDB GUI.

This module defines constants used throughout the UI layer of the MongoDB GUI application.
"""

# Default window size
DEFAULT_WINDOW_WIDTH: int = 1200
DEFAULT_WINDOW_HEIGHT: int = 800

# UI labels
LABEL_CONNECT: str = "Connect"
LABEL_DISCONNECT: str = "Disconnect"
LABEL_ADD_DB: str = "Add Database"
LABEL_REMOVE_DB: str = "Remove Database"

# Error messages
ERROR_UI_LOAD_FAILED: str = "Failed to load UI component."

# Add more UI constants as needed for consistency and maintainability.

EDIT_DOCUMENT_ACTION = "Edit Document"
EDIT_DOCUMENT_TITLE = EDIT_DOCUMENT_ACTION

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schemas")

APP_TITLE = "MongoDB GUI"
DEFAULT_WIDGET_WIDTH = 300
DEFAULT_WIDGET_HEIGHT = 100
