"""
Dialog for editing a MongoDB document in JSON format.

Provides a PyQt5 dialog for editing, validating, and formatting a document.
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
        widgets = [self.text_edit, self.validation_label]
        button_widgets: list[QWidget] = [self.format_btn, self.save_btn, self.cancel_btn]
        setup_dialog_layout(self, widgets, button_widgets)

        self.format_btn.clicked.connect(self.format_json)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.text_edit.textChanged.connect(self.validate_json)
        self.validate_json()

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
        Updates the validation label with errors if present.
        """
        try:
            json.loads(self.text_edit.toPlainText())
            self.validation_label.setText("")
        except Exception as e:
            self.validation_label.setText(f"Invalid JSON: {e}")

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
