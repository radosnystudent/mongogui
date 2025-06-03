from typing import TYPE_CHECKING, Any

from PyQt5.QtWidgets import QPushButton

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTextEdit, QVBoxLayout


class CollectionPanelMixin:
    collection_layout: "QVBoxLayout"
    mongo_client: Any
    result_display: "QTextEdit"
    query_input: Any

    def load_collections(self) -> None:
        if not self.mongo_client:
            return
        while self.collection_layout.count():
            child = self.collection_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        try:
            collections = self.mongo_client.list_collections()
            collections = sorted(collections)
            for collection_name in collections:
                self.add_collection_widget(collection_name)
            self.collection_layout.addStretch(1)
        except Exception as e:
            # Use print as fallback if db_info_label is not present or not a QLabel
            label = getattr(self, "db_info_label", None)
            if label and hasattr(label, "setPlainText"):
                label.setPlainText(f"Error loading collections: {str(e)}")
            else:
                print(f"Error loading collections: {str(e)}")

    def add_collection_widget(self, collection_name: str) -> None:
        collection_btn = QPushButton(collection_name)
        collection_btn.clicked.connect(
            lambda: self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        )
        self.collection_layout.addWidget(collection_btn)
