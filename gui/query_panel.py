from typing import Any, Callable, Dict, List, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QMenu,
    QMessageBox,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidgetItem,
    QWidget,
)

from gui.constants import EDIT_DOCUMENT_ACTION, EDIT_DOCUMENT_TITLE
from gui.edit_document_dialog import EditDocumentDialog


class QueryPanelMixin:
    mongo_client: Any
    result_display: "QTextEdit"
    query_input: Any
    data_table: Any
    prev_btn: Any
    next_btn: Any
    page_label: Any
    result_count_label: Any
    results: List[Dict[str, Any]]
    current_page: int
    page_size: int
    last_query: str
    last_collection: str
    json_tree: Any
    _table_signals_connected: bool = False
    _tree_signals_connected: bool = False

    def execute_query(self) -> None:
        if not self.mongo_client:
            self._set_db_info_label("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self._set_db_info_label("Please enter a query")
            return
        try:
            result = self.mongo_client.execute_query(query_text)
            if isinstance(result, list):
                self.results = result
                self.current_page = 0
                self.last_query = query_text
                self.display_results()
            else:
                self._set_db_info_label(f"Error: {result}")
        except Exception as e:
            self._set_db_info_label(f"Query error: {str(e)}")

    def _set_db_info_label(self, text: str) -> None:
        label = getattr(self, "db_info_label", None)
        if label and hasattr(label, "setText"):
            label.setText(text)

    def display_results(self) -> None:
        self.setup_query_panel_signals()  # Ensure context menus are always connected
        if not self.results:
            if self.data_table:
                self.data_table.setRowCount(0)
            if getattr(self, "json_tree", None):
                self.json_tree.clear()
                self.json_tree.hide()
            return
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.results))
        page_results = self.results[start_idx:end_idx]
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end_idx < len(self.results))
        self.page_label.setText(f"Page {self.current_page + 1}")
        self.result_count_label.setText(
            f"Showing {start_idx + 1}-{end_idx} of {len(self.results)} results"
        )
        self.display_table_results(page_results)
        # Show JSON tree view
        if getattr(self, "json_tree", None):
            self.json_tree.clear()
            for idx, doc in enumerate(page_results, start=start_idx + 1):
                doc_item = self._add_tree_item(f"Document {idx}", doc)
                self.json_tree.addTopLevelItem(doc_item)
            self.json_tree.expandToDepth(1)
            self.json_tree.show()
        self.result_display.hide()

    def _add_tree_item(self, key: str, value: Any) -> QTreeWidgetItem:
        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), ""])
            for k, v in value.items():
                child = self._add_tree_item(k, v)
                item.addChild(child)
            return item
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), f"[{len(value)} items]"])
            for idx, v in enumerate(value):
                child = self._add_tree_item(f"[{idx}]", v)
                item.addChild(child)
            return item
        else:
            return QTreeWidgetItem([str(key), str(value)])

    def _setup_context_menu_signal(
        self,
        widget: str,
        signal_name: str,
        handler: Callable[[Any], None],
        flag_name: str,
    ) -> None:
        if not hasattr(self, widget) or getattr(self, widget) is None:
            return
        w = getattr(self, widget)
        w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if getattr(self, flag_name, False):
            getattr(w, signal_name).disconnect(handler)
        getattr(w, signal_name).connect(handler)
        setattr(self, flag_name, True)

    def setup_query_panel_signals(self) -> None:
        """Connect context menu signals for table and tree widgets, ensuring old signals are disconnected."""
        self._setup_context_menu_signal(
            "data_table",
            "customContextMenuRequested",
            self.show_table_context_menu,
            "_table_signals_connected",
        )
        self._setup_context_menu_signal(
            "json_tree",
            "customContextMenuRequested",
            self.show_tree_context_menu,
            "_tree_signals_connected",
        )

    def display_table_results(self, results: List[Dict[str, Any]]) -> None:
        if not results or not self.data_table:
            return
        all_keys: Set[str] = set()
        for doc in results:
            all_keys.update(doc.keys())
        columns = sorted(all_keys)
        self.data_table.setColumnCount(len(columns))
        self.data_table.setRowCount(len(results))
        self.data_table.setHorizontalHeaderLabels(columns)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_row_docs = []
        for row, doc in enumerate(results):
            self._table_row_docs.append(doc)
            for col, key in enumerate(columns):
                value = doc.get(key, "")
                self.data_table.setItem(row, col, QTableWidgetItem(str(value)))

    def show_table_context_menu(self, pos: Any) -> None:
        if not self.data_table:
            return
        index = self.data_table.indexAt(pos)
        if not index.isValid():
            return
        doc = (
            self._table_row_docs[index.row()]
            if hasattr(self, "_table_row_docs")
            and index.row() < len(self._table_row_docs)
            else None
        )
        if doc:
            menu = QMenu(self.data_table)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = (
                self.data_table.viewport()
                if hasattr(self.data_table, "viewport")
                else None
            )
            global_pos = (
                viewport.mapToGlobal(pos)
                if viewport
                else self.data_table.mapToGlobal(pos)
            )
            action = menu.exec_(global_pos)
            if action == edit_action:
                self.edit_document(doc)

    def display_tree_results(self, results: List[Dict[str, Any]]) -> None:
        if not self.json_tree:
            return
        if not results:
            self.json_tree.clear()
            self.json_tree.hide()
            return
        self.json_tree.clear()
        self.json_tree.show()
        for idx, doc in enumerate(results):
            doc_id = doc.get("_id", f"Document {idx + 1}")
            doc_item = QTreeWidgetItem(self.json_tree, [str(doc_id), ""])
            self.add_tree_item(doc_item, doc)
            doc_item.setExpanded(False)
            doc_item.setData(0, int(Qt.ItemDataRole.UserRole), doc)
        self.json_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def show_tree_context_menu(self, pos: Any) -> None:
        if not self.json_tree:
            return
        item = self.json_tree.itemAt(pos)
        if item and item.parent() is None:
            menu = QMenu(self.json_tree)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = (
                self.json_tree.viewport()
                if hasattr(self.json_tree, "viewport")
                else None
            )
            global_pos = (
                viewport.mapToGlobal(pos)
                if viewport
                else self.json_tree.mapToGlobal(pos)
            )
            action = menu.exec_(global_pos)
            if action == edit_action:
                doc = item.data(0, int(Qt.ItemDataRole.UserRole))
                if doc:
                    self.edit_document(doc)

    def edit_document(self, document: dict) -> None:
        # Use self if it's a QWidget, otherwise try to get parent or pass None
        parent = self if isinstance(self, QWidget) else None
        dialog = EditDocumentDialog(document, parent)
        if dialog.exec_() == QDialog.Accepted:
            edited_doc = dialog.get_edited_document()
            if edited_doc is not None:
                self.update_document_in_db(edited_doc)

    def update_document_in_db(self, edited_doc: dict) -> None:
        if not self.mongo_client or "_id" not in edited_doc:
            QMessageBox.warning(
                None,
                EDIT_DOCUMENT_TITLE,
                "Cannot update document: missing _id or no DB connection.",
            )
            return
        try:
            collection = getattr(self, "last_collection", None)
            if not collection:
                QMessageBox.warning(
                    None, EDIT_DOCUMENT_TITLE, "Cannot determine collection for update."
                )
                return
            result = self.mongo_client.update_document(
                collection, edited_doc["_id"], edited_doc
            )
            if result:
                QMessageBox.information(
                    None, EDIT_DOCUMENT_TITLE, "Document updated successfully."
                )
                self.execute_query()
            else:
                QMessageBox.warning(
                    None, EDIT_DOCUMENT_TITLE, "Document update failed."
                )
        except Exception as e:
            QMessageBox.critical(
                None, EDIT_DOCUMENT_TITLE, f"Error updating document: {e}"
            )

    def add_tree_item(self, parent: QTreeWidgetItem, data: Dict[str, Any]) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                child = QTreeWidgetItem(parent, [key, ""])
                self.add_tree_item(child, value)
            elif isinstance(value, list):
                child = QTreeWidgetItem(parent, [key, f"Array ({len(value)})"])
                for item in value:
                    if isinstance(item, dict):
                        self.add_tree_item(child, item)
                    else:
                        QTreeWidgetItem(child, ["", str(item)])
            else:
                QTreeWidgetItem(parent, [key, str(value)])

    def clear_query(self) -> None:
        self.query_input.clear()

    def previous_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.display_results()

    def next_page(self) -> None:
        if (self.current_page + 1) * self.page_size < len(self.results):
            self.current_page += 1
            self.display_results()

    def execute_explain(self) -> None:
        """Run the current query with explain and display the plan."""
        if not self.mongo_client:
            self._set_db_info_label("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self._set_db_info_label("Please enter a query")
            return
        try:
            result = self.mongo_client.execute_query(query_text, explain=True)
            self.display_explain_result(result)
        except Exception as e:
            self._set_db_info_label(f"Explain error: {str(e)}")

    def display_explain_result(self, result: Any) -> None:
        """Display the explain plan as a tree in the Results section and hide the result_display box."""
        if not self.json_tree:
            return
        self.json_tree.clear()
        self.json_tree.show()
        self.result_display.hide()  # Always hide the array/text box for explain
        if isinstance(result, dict):
            root_item = QTreeWidgetItem(self.json_tree, ["Explain Plan", ""])
            self._add_tree_item_to_tree(root_item, result)
            root_item.setExpanded(True)
        else:
            QTreeWidgetItem(self.json_tree, ["Result", str(result)])

    def _add_tree_item_to_tree(self, parent: QTreeWidgetItem, value: Any) -> None:
        # Refactored to reduce cognitive complexity
        if isinstance(value, dict):
            for k, v in value.items():
                self._add_tree_child(parent, k, v)
        elif isinstance(value, list):
            for idx, v in enumerate(value):
                self._add_tree_child(parent, f"[{idx}]", v)

    def _add_tree_child(self, parent: QTreeWidgetItem, key: str, value: Any) -> None:
        if isinstance(value, (dict, list)):
            child = QTreeWidgetItem([str(key), ""])
            parent.addChild(child)
            self._add_tree_item_to_tree(child, value)
        else:
            child = QTreeWidgetItem([str(key), str(value)])
            parent.addChild(child)
