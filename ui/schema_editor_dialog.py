"""
Dialog for editing or creating a collection schema JSON file.
"""

import json

from PyQt5.QtGui import QShowEvent
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.json_highlighter import JsonHighlighter


class SchemaEditorDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, initial_schema: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Collection Schema (JSON)")
        self.resize(700, 550)  # Make dialog larger
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(initial_schema)
        layout.addWidget(self.text_edit)

        self.highlighter = JsonHighlighter(self.text_edit.document())

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet(
            "color: red; font-size: 15px; font-weight: bold;"
        )
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        btn_layout = QHBoxLayout()
        self.format_button = QPushButton("Format", self)
        self.format_button.clicked.connect(self.format_json)
        btn_layout.addWidget(self.format_button)
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)
        btn_layout.addWidget(self.save_button)
        layout.addLayout(btn_layout)

        self.text_edit.textChanged.connect(self.validate_json)
        self.validate_json()

    def get_schema(self) -> str:
        return self.text_edit.toPlainText()

    def accept(self) -> None:
        try:
            json.loads(self.get_schema())
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Error: {e}")
            return
        super().accept()

    def showEvent(self, a0: QShowEvent | None) -> None:
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
        try:
            obj = json.loads(self.text_edit.toPlainText())
            pretty = json.dumps(obj, indent=4, ensure_ascii=False)
            self.text_edit.setPlainText(pretty)
        except Exception as e:
            QMessageBox.critical(self, "Invalid JSON", f"Error: {e}")

    def validate_json(self) -> None:
        try:
            json.loads(self.text_edit.toPlainText())
            self.validation_label.setText("")
        except Exception as e:
            self.validation_label.setText(f"Invalid JSON: {e}")
