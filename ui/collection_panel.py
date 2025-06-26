import os
from typing import Any, cast

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.constants import SCHEMA_DIR
from ui.index_dialog import IndexDialog, IndexEditDialog
from ui.schema_editor_dialog import SchemaEditorDialog


class CollectionPanelMixin(QWidget):  # Make it inherit from QWidget
    collection_layout: QVBoxLayout
    mongo_client: Any
    result_display: QTextEdit | None = None
    query_input: Any
    collection_tree: QTreeWidget  # Added collection_tree attribute

    def __init__(self) -> None:
        super().__init__()
        self.collection_tree = QTreeWidget()
        self.setup_collection_tree()

    def setup_collection_tree(self) -> None:
        self.collection_tree.setColumnCount(1)
        self.collection_tree.setHeaderLabels(["Database/Collection"])
        self.collection_tree.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.collection_tree.customContextMenuRequested.connect(
            self.on_collection_tree_context_menu
        )
        self.collection_tree.itemClicked.connect(self.on_collection_tree_item_clicked)
        self.collection_tree.itemExpanded.connect(self.on_collection_tree_item_expanded)

    def add_database_collections(self, db_label: str, mongo_client: Any) -> None:
        # Add a top-level node for the database, with its collections as children
        db_item = QTreeWidgetItem([db_label])
        db_item.setData(
            0,
            Qt.ItemDataRole.UserRole + 1,
            {"type": "database", "db": db_label, "mongo_client": mongo_client},
        )
        try:
            collections = mongo_client.list_collections()
            collections = sorted(collections)
            for collection_name in collections:
                col_item = QTreeWidgetItem([collection_name])
                col_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole + 1,
                    {
                        "type": "collection",
                        "name": collection_name,
                        "db": db_label,
                        "mongo_client": mongo_client,
                    },
                )
                # Always add a dummy child for expand arrow
                dummy = QTreeWidgetItem([""])
                col_item.addChild(dummy)
                db_item.addChild(col_item)
            self.collection_tree.addTopLevelItem(db_item)
        except Exception:
            pass

    def clear_database_collections(self, db_label: str) -> None:
        # Remove the top-level node for a given database
        for i in range(self.collection_tree.topLevelItemCount()):
            item = self.collection_tree.topLevelItem(i)
            if item and item.text(0) == db_label:
                self.collection_tree.takeTopLevelItem(i)
                break

    def load_collections(self, mongo_client: Any) -> None:
        if not hasattr(self, "collection_tree") or self.collection_tree is None:
            return
        self.collection_tree.clear()
        if not mongo_client:
            return
        try:
            collections = mongo_client.list_collections()
            collections = sorted(collections)
            for collection_name in collections:
                col_item = QTreeWidgetItem([collection_name])
                col_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole + 1,
                    {
                        "type": "collection",
                        "name": collection_name,
                        "db": getattr(mongo_client, "current_db", "testdb"),
                    },
                )
                col_item.addChild(QTreeWidgetItem([""]))
                self.collection_tree.addTopLevelItem(col_item)
        except Exception:
            pass

    def add_collection_widget(self, collection_name: str) -> None:
        collection_btn = QPushButton(collection_name)
        collection_btn.clicked.connect(
            lambda: self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        )
        self.collection_layout.addWidget(collection_btn)

    def _get_mongo_client_for_item(self, item: QTreeWidgetItem) -> Any:
        current: QTreeWidgetItem | None = item
        while current is not None:
            data = current.data(0, Qt.ItemDataRole.UserRole + 1)
            # Try to get mongo_client from collection node first, then parent (database)
            if data and "mongo_client" in data:
                return data.get("mongo_client")
            current = current.parent()

    def on_collection_tree_item_expanded(self, item: QTreeWidgetItem) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if data and data.get("type") == "collection" and item.childCount() == 1:
            only_child = item.child(0)
            if only_child is not None and only_child.text(0) == "":
                item.takeChildren()
                mongo_client = self._get_mongo_client_for_item(item)
                if mongo_client is not None:
                    self.reload_collection_indexes_in_tree(item)

    def reload_collection_indexes_in_tree(
        self, col_item: QTreeWidgetItem | None
    ) -> None:
        if col_item is None:
            return
        client = self._get_mongo_client_for_item(col_item)
        if not client:
            return
        # Remove all children
        while col_item.childCount() > 0:
            child = col_item.child(0)
            if child is not None:
                col_item.removeChild(child)
            else:
                break
        collection_name = col_item.text(0)
        indexes_result = client.list_indexes(collection_name)
        if indexes_result.is_ok():
            indexes = indexes_result.value or []
        else:
            QMessageBox.critical(
                self.collection_tree, "Error", str(indexes_result.error)
            )
            return
        try:
            if indexes:
                for idx in indexes:
                    idx_name = idx.get("name", "")
                    idx_item = QTreeWidgetItem([idx_name])
                    idx_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole + 1,
                        {"type": "index", "collection": collection_name, "index": idx},
                    )
                    col_item.addChild(idx_item)
        except Exception:
            pass
        # Always add a dummy node if no real index children
        if col_item.childCount() == 0:
            col_item.addChild(QTreeWidgetItem([""]))
        if hasattr(col_item, "setExpanded"):
            col_item.setExpanded(True)

    def _add_index_items_to_collection(
        self, col_item: QTreeWidgetItem, collection_name: str, indexes: list[dict]
    ) -> None:
        # This method is now inlined in reload_collection_indexes_in_tree, but keep for compatibility if called elsewhere
        for idx in indexes:
            idx_name = idx.get("name", "")
            idx_item = QTreeWidgetItem(["Index", idx_name])
            idx_item.setData(
                0,
                Qt.ItemDataRole.UserRole + 1,
                {"type": "index", "collection": collection_name, "index": idx},
            )
            col_item.addChild(idx_item)

    def show_add_index_dialog(
        self, collection_name: str, item: QTreeWidgetItem | None = None
    ) -> None:
        col_item, mongo_client = self._resolve_collection_item_and_client(
            collection_name, item
        )
        if not mongo_client or col_item is None:
            QMessageBox.critical(
                self.collection_tree,
                "Error",
                "No MongoDB connection found for this collection.",
            )
            return
        indexes = mongo_client.list_indexes(collection_name)
        if isinstance(indexes, str):
            QMessageBox.critical(self.collection_tree, "Error", indexes)
            return
        self._handle_index_dialog_and_create(
            indexes, mongo_client, collection_name, col_item
        )

    def _find_collection_item_and_client(
        self, collection_name: str
    ) -> tuple[QTreeWidgetItem | None, Any | None]:
        for i in range(self.collection_tree.topLevelItemCount()):
            db_item = self.collection_tree.topLevelItem(i)
            if db_item is None:
                continue
            for j in range(db_item.childCount()):
                c_item = db_item.child(j)
                if c_item is not None and c_item.text(1) == collection_name:
                    client = self._get_mongo_client_for_item(c_item)
                    return c_item, client
        return None, None

    def _resolve_collection_item_and_client(
        self, collection_name: str, item: QTreeWidgetItem | None
    ) -> tuple[QTreeWidgetItem | None, Any | None]:
        if item is not None:
            return item, self._get_mongo_client_for_item(item)
        return self._find_collection_item_and_client(collection_name)

    def _handle_index_dialog_and_create(
        self,
        indexes: list,
        mongo_client: Any,
        collection_name: str,
        col_item: QTreeWidgetItem | None,
    ) -> None:
        dlg = IndexDialog(indexes, self)  # Change parent to self
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            data = dlg.get_index_data()
            if data and not self._validate_and_create_index(
                data, mongo_client, collection_name
            ):
                return
            if col_item is not None:
                self.reload_collection_indexes_in_tree(col_item)

    def _validate_and_create_index(
        self, index_data: dict, client: Any, collection_name: str
    ) -> bool:
        key = index_data["key"]
        if not (
            isinstance(key, list)
            and all(isinstance(pair, list | tuple) and len(pair) == 2 for pair in key)
        ):
            QMessageBox.critical(
                self.collection_tree,
                "Error",
                f"Index key must be a list of pairs, got: {key}",
            )
            return False
        kwargs = self._extract_index_options(index_data)
        name = client.create_index(collection_name, key, **kwargs)
        if isinstance(name, str) and not name.startswith("Create index error"):
            QMessageBox.information(
                self.collection_tree,
                "Index Created",
                f"Index '{name}' created.",
            )
        else:
            QMessageBox.critical(self.collection_tree, "Error", str(name))
            return False
        return True

    def _extract_index_options(self, data: dict) -> dict:
        # Minimal stub to fix mypy error; real logic can be implemented as needed
        return {k: v for k, v in data.items() if k not in ("key", "name")}

    def show_edit_index_dialog(self, collection_name: str, index_dict: dict) -> None:
        dlg = IndexEditDialog(index_dict, self)  # Change parent to self
        if dlg.exec() == QDialog.DialogCode.Accepted:
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

    def on_collection_tree_context_menu(self, pos: Any) -> None:
        item = self.collection_tree.itemAt(pos)
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        menu = QMenu(self.collection_tree)
        viewport = self.collection_tree.viewport()
        if data and data.get("type") == "collection":
            self._handle_collection_context_menu(menu, viewport, pos, data)
        elif data and data.get("type") == "index":
            self._handle_index_context_menu(menu, viewport, pos, data)

    def _handle_collection_context_menu(
        self, menu: QMenu, viewport: QWidget | None, pos: Any, data: dict
    ) -> None:
        manage_action = menu.addAction("Manage indexes")
        schema_action = menu.addAction("Edit schema (JSON)")
        action = menu.exec(
            viewport.mapToGlobal(pos)
            if viewport is not None
            else self.collection_tree.mapToGlobal(pos)
        )
        if action == manage_action:
            self.show_add_index_dialog(data["name"], item=None)
        elif action == schema_action:
            self.edit_collection_schema(data)

    def edit_collection_schema(self, data: dict) -> None:
        """Open dialog to edit or create the schema JSON for a collection."""
        db = data.get("db")
        collection = data.get("name")
        if not db or not collection:
            QMessageBox.warning(
                self.collection_tree, "Error", "Invalid collection info."
            )
            return
        os.makedirs(SCHEMA_DIR, exist_ok=True)
        schema_path = os.path.join(SCHEMA_DIR, f"{db}__{collection}.json")
        initial_schema = ""
        if os.path.exists(schema_path):
            try:
                with open(schema_path, encoding="utf-8") as f:
                    initial_schema = f.read()
            except Exception as e:
                QMessageBox.critical(
                    self.collection_tree, "Error reading schema file", str(e)
                )
                return
        dlg = SchemaEditorDialog(self, initial_schema)  # Change parent to self
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                with open(schema_path, "w", encoding="utf-8") as f:
                    f.write(dlg.get_schema())
                QMessageBox.information(
                    self.collection_tree,
                    "Schema Saved",
                    f"Schema for '{collection}' saved.",
                )
            except Exception as e:
                QMessageBox.critical(
                    self.collection_tree, "Error saving schema file", str(e)
                )

    def _handle_index_context_menu(
        self, menu: QMenu, viewport: QWidget | None, pos: Any, data: dict
    ) -> None:
        edit_action = menu.addAction("Edit")
        delete_action = menu.addAction("Delete")
        action = menu.exec(
            viewport.mapToGlobal(pos)
            if viewport is not None
            else self.collection_tree.mapToGlobal(pos)
        )
        if action == edit_action:
            self.show_edit_index_dialog(data["collection"], data["index"])
        elif action == delete_action:
            self.show_delete_index_dialog(data["collection"], data["index"])

    def on_collection_tree_item_clicked(
        self, item: QTreeWidgetItem, column: int
    ) -> None:
        # If MainWindow overrides this, call its version
        main_window = QApplication.activeWindow()
        if (
            main_window
            and hasattr(main_window, "add_query_tab")
            and hasattr(main_window, "on_collection_tree_item_clicked")
            and main_window.__class__.__name__ == "MainWindow"
        ):
            from ui.main_window import (
                MainWindow,
            )

            main_window_typed = cast(MainWindow, main_window)
            main_window_typed.on_collection_tree_item_clicked(item, column)
            return None
        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if data and data.get("type") == "collection":
            collection_name = data["name"]
            parent = item.parent()
            db_label = parent.text(0) if parent is not None else ""
            if hasattr(self, "query_input"):
                self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
            self.last_collection = collection_name
            self.last_db_label = db_label
            active_clients = getattr(self, "active_clients", None)
            if isinstance(active_clients, dict) and db_label in active_clients:
                self.mongo_client = active_clients[db_label]
        # Don't reload indexes on click, only on expand
