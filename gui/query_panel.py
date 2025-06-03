from typing import TYPE_CHECKING, Any, Dict, List, Set

from PyQt5.QtWidgets import QTableWidgetItem, QTextEdit, QTreeWidgetItem

if TYPE_CHECKING:
    pass


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
    json_tree: Any

    def execute_query(self) -> None:
        if not self.mongo_client:
            self.result_display.setPlainText("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self.result_display.setPlainText("Please enter a query")
            return
        try:
            result = self.mongo_client.execute_query(query_text)
            if isinstance(result, list):
                self.results = result
                self.current_page = 0
                self.last_query = query_text
                self.display_results()
            else:
                self.result_display.setPlainText(f"Error: {result}")
        except Exception as e:
            self.result_display.setPlainText(f"Query error: {str(e)}")

    def display_results(self) -> None:
        if not self.results:
            self.result_display.setPlainText("No results")
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
        for row, doc in enumerate(results):
            for col, key in enumerate(columns):
                value = doc.get(key, "")
                self.data_table.setItem(row, col, QTableWidgetItem(str(value)))

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
