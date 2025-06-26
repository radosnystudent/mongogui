"""
Dialog for editing a MongoDB document in JSON format.

Provides a PyQt6 dialog for editing, validating, and formatting a document.
"""

import json
from typing import cast

from PyQt6.QtGui import QShowEvent
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from ui.json_highlighter import JsonHighlighter
from ui.ui_utils import setup_dialog_layout


class EditDocumentDialog(QDialog):
    """
    Dialog for editing a MongoDB document in JSON format.
    Provides validation, formatting, and user feedback for editing documents.
    """

    def __init__(self, document: dict, parent: QWidget | None = None) -> None:
        """
        Initialize the EditDocumentDialog.

        Args:
            document: The document to edit.
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Document")
        self.setMinimumSize(700, 500)
        self.document = document

        # Create widgets
        self.text_edit = QTextEdit(self)
        self.text_edit.setText(json.dumps(document, indent=2, default=str))
        self.highlighter = JsonHighlighter(self.text_edit.document())

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet(
            "color: red; font-size: 15px; font-weight: bold;"
        )
        self.validation_label.setWordWrap(True)

        self.format_btn = QPushButton("Format")
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")

        # Set up layout using helper
        widgets = cast(list[QWidget], [self.text_edit, self.validation_label])
        button_widgets = cast(
            list[QWidget],
            [self.format_btn, self.save_btn, self.cancel_btn],
        )
        setup_dialog_layout(self, widgets, button_widgets)

        # Connect signals
        self.format_btn.clicked.connect(self.format_document)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.text_edit.textChanged.connect(self.validate_document)
        self.validate_document()

    def format_document(self) -> None:
        """Format the document text with proper JSON indentation."""
        try:
            text = self.text_edit.toPlainText()
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2, default=str)
            self.text_edit.setText(formatted)
            self.validate_document()
        except json.JSONDecodeError as e:
            self.validation_label.setText(f"Invalid JSON: {str(e)}")

    def validate_document(self) -> bool:
        """Validate the document text as proper JSON."""
        try:
            text = self.text_edit.toPlainText()
            json.loads(text)
            self.validation_label.setText("")
            return True
        except json.JSONDecodeError as e:
            self.validation_label.setText(f"Invalid JSON: {str(e)}")
            return False

    def get_edited_document(self) -> dict | None:
        """
        Get the edited document as a dictionary if valid JSON, else None.
        Shows an error message if parsing fails.

        Returns:
            The edited document as a dict, or None if invalid.
        """
        try:
            self._edited_doc = json.loads(self.text_edit.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Error parsing JSON: {e}")
            return None
        return (
            self._edited_doc
            if isinstance(self._edited_doc, dict) or self._edited_doc is None
            else None
        )

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Handle the dialog show event."""
        super().showEvent(a0)
        self.text_edit.setFocus()
