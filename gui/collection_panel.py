from typing import TYPE_CHECKING, Any, List, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from gui.index_dialog import IndexDialog

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTextEdit, QVBoxLayout


class CollectionPanelMixin:
    collection_layout: "QVBoxLayout"
    mongo_client: Any
    result_display: "QTextEdit"
    query_input: Any
    collection_tree: QTreeWidget  # Added collection_tree attribute

    def setup_collection_tree(self) -> None:
        self.collection_tree.setHeaderLabels(["Collections"])
        self.collection_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.collection_tree.customContextMenuRequested.connect(
            self.on_collection_tree_context_menu
        )
        self.collection_tree.itemClicked.connect(self.on_collection_tree_item_clicked)
        self.collection_tree.itemExpanded.connect(self.on_collection_tree_item_expanded)

    def load_collections(self) -> None:
        if not hasattr(self, "collection_tree") or self.collection_tree is None:
            return
        self.collection_tree.clear()
        if not self.mongo_client:
            return
        try:
            collections = self.mongo_client.list_collections()
            collections = sorted(collections)
            for collection_name in collections:
                col_item = QTreeWidgetItem([collection_name])
                col_item.setData(
                    0,
                    int(Qt.ItemDataRole.UserRole),
                    {"type": "collection", "name": collection_name},
                )
                # Add dummy child so arrow is always visible
                col_item.addChild(QTreeWidgetItem([""]))
                self.collection_tree.addTopLevelItem(col_item)
        except Exception as e:
            label = getattr(self, "db_info_label", None)
            if label:
                label.setText(f"Error loading collections: {str(e)}")
            else:
                print(f"Error loading collections: {str(e)}")

    def add_collection_widget(self, collection_name: str) -> None:
        collection_btn = QPushButton(collection_name)
        collection_btn.clicked.connect(
            lambda: self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        )
        self.collection_layout.addWidget(collection_btn)

    def on_collection_tree_item_expanded(self, item: QTreeWidgetItem) -> None:
        data = item.data(0, int(Qt.ItemDataRole.UserRole))
        if data and data.get("type") == "collection":
            first_child = item.child(0)
            if (
                item.childCount() == 1
                and first_child is not None
                and first_child.text(0) == ""
            ):
                item.takeChildren()
                collection_name = data["name"]
                if not self.mongo_client:
                    return
                indexes = self.mongo_client.list_indexes(collection_name)
                if isinstance(indexes, str):
                    QMessageBox.critical(self.collection_tree, "Error", indexes)
                    return
                for idx in indexes:
                    idx_name = idx.get("name", "")
                    idx_item = QTreeWidgetItem([f"{idx_name}"])
                    idx_item.setData(
                        0,
                        int(Qt.ItemDataRole.UserRole),
                        {"type": "index", "collection": collection_name, "index": idx},
                    )
                    item.addChild(idx_item)

    def on_collection_tree_item_clicked(
        self, item: QTreeWidgetItem, column: int
    ) -> None:
        data = item.data(0, int(Qt.ItemDataRole.UserRole))
        if data and data.get("type") == "collection":
            collection_name = data["name"]
            if hasattr(self, "query_input"):
                self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        # Don't reload indexes on click, only on expand

    def _handle_collection_context_menu(
        self,
        menu: QMenu,
        viewport: Optional[QWidget],
        pos: Any,
        data: dict,
    ) -> None:
        manage_action = menu.addAction("Manage indexes")
        if viewport is not None:
            action = menu.exec_(viewport.mapToGlobal(pos))
        else:
            action = menu.exec_(self.collection_tree.mapToGlobal(pos))
        if action == manage_action:
            self.show_add_index_dialog(data["name"])

    def _handle_index_context_menu(
        self,
        menu: QMenu,
        viewport: Optional[QWidget],
        pos: Any,
        data: dict,
    ) -> None:
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        if viewport is not None:
            action = menu.exec_(viewport.mapToGlobal(pos))
        else:
            action = menu.exec_(self.collection_tree.mapToGlobal(pos))
        if action == edit_action:
            self.show_edit_index_dialog(data["collection"], data["index"])
        elif action == delete_action:
            self.show_delete_index_dialog(data["collection"], data["index"])

    def on_collection_tree_context_menu(self, pos: Any) -> None:
        item = self.collection_tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, int(Qt.ItemDataRole.UserRole))
        menu = QMenu(self.collection_tree)
        viewport = self.collection_tree.viewport()
        if data and data.get("type") == "collection":
            self._handle_collection_context_menu(menu, viewport, pos, data)
        elif data and data.get("type") == "index":
            self._handle_index_context_menu(menu, viewport, pos, data)

    def _extract_index_options(self, data: dict) -> dict:
        # Helper to extract only non-None index options
        opts = [
            "name",
            "unique",
            "sparse",
            "hidden",
            "expireAfterSeconds",
            "partialFilterExpression",
        ]
        return {opt: data[opt] for opt in opts if data.get(opt) is not None}

    def show_add_index_dialog(self, collection_name: str) -> None:
        # Pass current indexes to IndexDialog so all (including _id_) are shown
        indexes = self.mongo_client.list_indexes(collection_name)
        if isinstance(indexes, str):
            QMessageBox.critical(self.collection_tree, "Error", indexes)
            return
        dlg = IndexDialog(indexes, self.collection_tree)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            data = dlg.get_index_data()
            if data:
                # Validate key format
                key = data["key"]
                if not (
                    isinstance(key, list)
                    and all(
                        isinstance(pair, (list, tuple)) and len(pair) == 2
                        for pair in key
                    )
                ):
                    QMessageBox.critical(
                        self.collection_tree,
                        "Error",
                        f"Index key must be a list of pairs, got: {key}",
                    )
                    return
                kwargs = self._extract_index_options(data)
                name = self.mongo_client.create_index(collection_name, key, **kwargs)
                if isinstance(name, str) and not name.startswith("Create index error"):
                    QMessageBox.information(
                        self.collection_tree,
                        "Index Created",
                        f"Index '{name}' created.",
                    )
                else:
                    QMessageBox.critical(self.collection_tree, "Error", str(name))
            # Only reload indexes for the expanded collection
            self.reload_collection_indexes_in_tree(collection_name)

    def reload_collection_indexes_in_tree(self, collection_name: str) -> None:
        # Find the collection item in the tree and reload its children (indexes)
        col_item = self._find_collection_item(collection_name)
        if not col_item:
            return
        self._clear_collection_children(col_item)
        indexes = self.mongo_client.list_indexes(collection_name)
        if isinstance(indexes, str):
            QMessageBox.critical(self.collection_tree, "Error", indexes)
            return
        self._add_index_items_to_collection(col_item, collection_name, indexes)
        if hasattr(col_item, "setExpanded"):
            col_item.setExpanded(True)

    def _find_collection_item(self, collection_name: str) -> Optional[QTreeWidgetItem]:
        for i in range(self.collection_tree.topLevelItemCount()):
            col_item = self.collection_tree.topLevelItem(i)
            if col_item is not None and col_item.text(0) == collection_name:
                return col_item
        return None

    def _clear_collection_children(self, col_item: QTreeWidgetItem) -> None:
        if hasattr(col_item, "takeChildren"):
            col_item.takeChildren()

    def _add_index_items_to_collection(
        self, col_item: QTreeWidgetItem, collection_name: str, indexes: List[dict]
    ) -> None:
        for idx in indexes:
            idx_name = idx.get("name", "")
            idx_item = QTreeWidgetItem([f"{idx_name}"])
            idx_item.setData(
                0,
                int(Qt.ItemDataRole.UserRole),
                {"type": "index", "collection": collection_name, "index": idx},
            )
            if hasattr(col_item, "addChild"):
                col_item.addChild(idx_item)

    def show_edit_index_dialog(self, collection_name: str, index_dict: dict) -> None:
        from gui.index_dialog import IndexEditDialog

        dlg = IndexEditDialog(index_dict, self.collection_tree)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.get_index_data()
            if data:
                update_result = self.mongo_client.update_index(
                    collection_name,
                    data["name"],
                    data["key"],
                    unique=data["unique"],
                )
                if update_result is True or (
                    isinstance(update_result, str)
                    and not update_result.startswith("Create index error")
                ):
                    QMessageBox.information(
                        self.collection_tree,
                        "Index Updated",
                        f"Index '{data['name']}' updated.",
                    )
                else:
                    QMessageBox.critical(
                        self.collection_tree, "Error", str(update_result)
                    )
            self.load_collections()

    def show_delete_index_dialog(self, collection_name: str, index_dict: dict) -> None:
        name = index_dict.get("name")
        if name:
            drop_result = self.mongo_client.drop_index(collection_name, name)
            if drop_result is True:
                QMessageBox.information(
                    self.collection_tree, "Index Removed", f"Index '{name}' removed."
                )
            else:
                QMessageBox.critical(self.collection_tree, "Error", str(drop_result))
            self.load_collections()
