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


class EditDocumentDialog(QDialog):
    def __init__(self, document: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Document")
        self.setMinimumSize(700, 500)
        self.document = document
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setText(json.dumps(document, indent=2, default=str))
        layout.addWidget(self.text_edit)

        self.highlighter = JsonHighlighter(self.text_edit.document())

        self.validation_label = QLabel("")
        self.validation_label.setStyleSheet(
            "color: red; font-size: 15px; font-weight: bold;"
        )
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        button_layout = QHBoxLayout()
        self.format_btn = QPushButton("Format")
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.format_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.format_btn.clicked.connect(self.format_json)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.text_edit.textChanged.connect(self.validate_json)
        self.validate_json()

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

    def get_edited_document(self) -> dict | None:
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
        try:
            raw = self.text_edit.toPlainText()
            if raw.strip():
                obj = json.loads(raw)
                pretty = json.dumps(obj, indent=4, ensure_ascii=False)
                self.text_edit.setPlainText(pretty)
        except Exception:
            pass
        super().showEvent(a0)
