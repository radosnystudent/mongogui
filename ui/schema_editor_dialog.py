"""
Dialog for editing or creating a collection schema JSON file.

Provides a PyQt5 dialog for editing, validating, and formatting collection schemas.
"""

import json

from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from ui.json_highlighter import JsonHighlighter
from ui.ui_utils import setup_dialog_layout


class SchemaEditorDialog(QDialog):
    """
    Dialog for editing or creating a collection schema JSON file.
    Provides validation, formatting, and user feedback for schema editing.
    """

    def __init__(self, parent: QWidget | None = None, initial_schema: str = "") -> None:
        """
        Initialize the SchemaEditorDialog.

        Args:
            parent: Optional parent QWidget.
            initial_schema: Initial schema JSON as a string.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Collection Schema (JSON)")
        self.resize(700, 550)  # Make dialog larger

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_schema)

        self.highlighter = JsonHighlighter(self.text_edit.document())

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet(
            "color: red; font-size: 15px; font-weight: bold;"
        )
        self.validation_label.setWordWrap(True)

        self.format_button = QPushButton("Format", self)
        self.save_button = QPushButton("Save", self)

        widgets = [self.text_edit, self.validation_label]
        button_widgets: list[QWidget] = [self.format_button, self.save_button]
        setup_dialog_layout(self, widgets, button_widgets)

        self.format_button.clicked.connect(self.format_json)
        self.save_button.clicked.connect(self.accept)
        self.text_edit.textChanged.connect(self.validate_json)
        self.validate_json()

    def get_schema(self) -> str:
        """
        Get the current schema as a string from the text edit widget.

        Returns:
            The schema as a string.
        """
        return self.text_edit.toPlainText()

    def accept(self) -> None:
        """
        Validate the schema JSON and accept the dialog if valid.
        Shows an error message if the JSON is invalid.
        """
        try:
            json.loads(self.get_schema())
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Error: {e}")
            return
        super().accept()

    def showEvent(self, a0: QShowEvent | None) -> None:
        """
        Format the JSON when the dialog is shown, if possible.
        """
        try:
            raw = self.text_edit.toPlainText()
            if raw.strip():
                obj = json.loads(raw)
                pretty = json.dumps(obj, indent=4, ensure_ascii=False)
                self.text_edit.setPlainText(pretty)
        except Exception:
            pass
        super().showEvent(a0)

    def format_json(self) -> None:
        """
        Format the JSON in the text edit widget for readability.
        Shows an error message if the JSON is invalid.
        """
        try:
            obj = json.loads(self.text_edit.toPlainText())
            pretty = json.dumps(obj, indent=4, ensure_ascii=False)
            self.text_edit.setPlainText(pretty)
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Error: {e}")

    def validate_json(self) -> None:
        """
        Validate the JSON in the text edit widget.
        Updates the validation label and enables/disables the save button.
        """
        try:
            json.loads(self.text_edit.toPlainText())
            self.validation_label.setText("")
            self.save_button.setEnabled(True)  # Enable "Save" button if JSON is valid
        except Exception as e:
            self.validation_label.setText(f"Invalid JSON: {e}")
            self.save_button.setEnabled(
                False
            )  # Disable "Save" button if JSON is invalid
