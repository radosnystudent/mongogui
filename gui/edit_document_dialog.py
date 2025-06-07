import json

from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class EditDocumentDialog(QDialog):
    def __init__(self, document: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Document")
        self.setMinimumSize(600, 400)
        self.document = document
        layout = QVBoxLayout(self)

        self.text_edit = QTextEdit(self)
        self.text_edit.setText(json.dumps(document, indent=2, default=str))
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

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
