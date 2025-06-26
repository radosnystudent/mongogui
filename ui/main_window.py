"""
Main application window for the MongoDB GUI.
"""

# This module defines the MainWindow class and related UI logic for the main application window.
# All UI logic is separated from business logic and database operations.
# Use composition and the Observer pattern for state management.

from typing import Any, cast

from PyQt6.QtCore import Qt, QEvent, QObject
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from db.connection_manager import ConnectionManager
from ui.collection_panel import CollectionPanelMixin
from ui.connection_manager_window import ConnectionManagerWindow
from ui.connection_widgets import ConnectionWidgetsMixin
from ui.edit_document_dialog import EditDocumentDialog
from ui.query_panel import QueryPanelMixin
from ui.query_tab import QueryTabWidget
from ui.ui_utils import set_minimum_heights
from utils.error_handling import handle_exception
from utils.state_manager import StateManager, StateObserver

NO_DB_CONNECTION_MSG = "No database connection"


class MainWindow(QMainWindow, ConnectionWidgetsMixin):
    """Main application window for the MongoDB GUI."""

    def __init__(self) -> None:
        """Initialize the main window and UI components."""
        super().__init__()
        self.setWindowTitle("MongoDB GUI")
        self.setMinimumSize(800, 600)

        # Initialize state
        self.results: list[dict[str, Any]] = []
        self.last_query = ""
        self.last_query_type = ""
        self.last_collection: str = ""
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Initialize widgets
        self.data_table: QTableWidget | None = None
        self.json_tree: QTreeWidget | None = None
        self.query_tabs = QTabWidget()
        self.query_tabs.setTabsClosable(True)
        self.query_tabs.tabCloseRequested.connect(self._close_query_tab)
        self.query_tabs.setMovable(True)

        # Set up connection section
        self.connection_widget = QWidget()
        main_layout.addWidget(self.connection_widget)
        layout = QVBoxLayout()
        self.connection_widget.setLayout(layout)
        self.connection_layout = layout  # Store reference after setup

        # Add query tabs
        main_layout.addWidget(self.query_tabs)

        # Initialize panels
        self.query_panel = QueryPanelMixin()
        self.collection_panel = CollectionPanelMixin()
        ConnectionWidgetsMixin.__init__(self)

        # Complete setup
        self.setup_data_table()
        self.setup_ui()

    def setup_data_table(self) -> None:
        """Set up the data table widget."""
        self.data_table = QTableWidget()
        self.data_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        if self.data_table is not None:  # Help type checker
            self.data_table.setMinimumHeight(200)
            self.data_table.itemSelectionChanged.connect(self.on_row_selected)

    def setup_ui(self) -> None:
        """Additional UI setup after initialization."""
        if isinstance(self.centralWidget(), QWidget):
            if widget := self.centralWidget():
                set_minimum_heights(widget)

    def add_query_tab(
        self, collection_name: str | None = None, db_label: str | None = None
    ) -> None:
        mongo_client = None
        active_db_label = db_label

        if (
            active_db_label
            and hasattr(self, "active_clients")
            and active_db_label in self.active_clients
        ):
            mongo_client = self.active_clients[active_db_label]
        elif not active_db_label and self.mongo_client:
            mongo_client = self.mongo_client

        # Prevent opening a tab if no client is resolved, unless it's the initial state without any tabs.
        is_initial_empty_state = not self.query_tabs.count() and not (
            hasattr(self, "active_clients") and self.active_clients
        )
        if not mongo_client and not is_initial_empty_state:
            QMessageBox.warning(self, "No Connection", NO_DB_CONNECTION_MSG)
            return

        # If mongo_client is still None here, it means we are in the initial empty state or a connection is missing.
        # QueryTabWidget can handle a None mongo_client initially.

        # Only set collection_name to None for DB-level tabs (when collection_name is not provided)
        actual_collection_name_for_tab = collection_name if collection_name else None
        tab_title = f"Query - {active_db_label}" if active_db_label else "New Query"
        if collection_name and active_db_label and collection_name != active_db_label:
            tab_title = f"{collection_name} - {active_db_label}"

        tab = QueryTabWidget(
            parent=None,
            collection_name=actual_collection_name_for_tab,
            db_label=active_db_label,
            mongo_client=mongo_client,
            on_close=self._close_query_tab_by_widget,
        )

        self.query_tabs.addTab(tab, tab_title)
        self.query_tabs.setCurrentWidget(tab)

    def _close_query_tab(self, index: int) -> None:
        widget = self.query_tabs.widget(index)
        if widget:
            self._close_query_tab_by_widget(widget)

    def _close_query_tab_by_widget(self, widget: QWidget) -> None:
        index = self.query_tabs.indexOf(widget)
        if index != -1:
            self.query_tabs.removeTab(index)
            widget.deleteLater()

    def _handle_database_click(self, item_name: str) -> None:
        """
        Handle clicks on database items in the collection tree.

        Args:
            item_name (str): The name of the database item clicked.
        """
        self.add_query_tab(db_label=item_name, collection_name=None)

    def _handle_collection_click(self, item: QTreeWidgetItem) -> None:
        """Handles clicks on collection items in the collection tree."""
        parent_db_item = item.parent()
        if parent_db_item:
            db_label = parent_db_item.text(0)
            collection_name = item.text(1) if item.columnCount() > 1 else item.text(0)
            self.add_query_tab(collection_name=collection_name, db_label=db_label)
        else:
            collection_name = item.text(1) if item.columnCount() > 1 else item.text(0)
            self.add_query_tab(collection_name=collection_name)

    def _handle_index_click(self, item: QTreeWidgetItem, item_name: str) -> None:
        """Handles clicks on index items in the collection tree."""
        coll_item = item.parent()
        if not coll_item:
            return

        coll_data = coll_item.data(0, Qt.ItemDataRole.UserRole + 1)
        collection_name_for_index = (
            coll_data.get("name") if coll_data else "Unknown Collection"
        )

        db_item = coll_item.parent()
        if not db_item:
            return

        db_label_for_index = db_item.text(0)
        QMessageBox.information(
            self,
            "Index Clicked",
            f"Index: {item_name}\nCollection: {collection_name_for_index}\nDatabase: {db_label_for_index}",
        )

    def on_collection_tree_item_clicked(
        self, item: QTreeWidgetItem, column: int
    ) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not data:
            return

        item_type = data.get("type")
        item_name = data.get("name")

        action_map = {
            "database": lambda: self._handle_database_click(item_name),
            "collection": lambda: self._handle_collection_click(item),
            "index": lambda: self._handle_index_click(item, item_name),
        }

        if item_type in action_map:
            action_map[item_type]()

        # Context menu logic
        if item_type in ["collection", "index"]:
            self.collection_panel.collection_tree.setCurrentItem(item)
        else:
            self.collection_panel.collection_tree.clearSelection()

    def execute_query(self) -> None:
        """
        Delegate query execution to the current QueryTabWidget, or show warning if none selected.
        """
        current_tab = self.query_tabs.currentWidget()
        if not isinstance(current_tab, QueryTabWidget):
            QMessageBox.warning(self, "No Query Tab", "No query tab selected.")
            return
        current_tab.execute_query()

    def display_results(self) -> None:
        """
        Display query results in the current tab or fallback to main window table/tree.
        """
        current_tab = self.query_tabs.currentWidget()
        if isinstance(current_tab, QueryTabWidget):
            current_tab.display_results()
            return
        elif not self.results:
            QMessageBox.information(self, "No Results", "No results to display.")
            return
        # Fallback: display results in main window widgets
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
        self.display_tree_results(page_results)

    def display_table_results(self, results: list[dict[str, Any]]) -> None:
        if not results or not self.data_table:
            return

        all_keys: set[str] = set()
        for doc in results:
            all_keys.update(doc.keys())
        columns = sorted(all_keys)
        self.data_table.setColumnCount(len(columns))
        self.data_table.setRowCount(len(results))
        self.data_table.setHorizontalHeaderLabels(columns)
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self._table_row_docs = []  # Store docs for context menu
        for row, doc in enumerate(results):
            self._table_row_docs.append(doc)
            for col, key in enumerate(columns):
                value = doc.get(key, "")
                item = QTableWidgetItem(str(value))
                self.data_table.setItem(row, col, item)

    def display_tree_results(self, results: list[dict[str, Any]]) -> None:
        if not self.json_tree:
            return
        if not results:
            self.json_tree.clear()
            return
        self.json_tree.clear()
        self.json_tree.show()
        for idx, doc in enumerate(results):
            root = QTreeWidgetItem([f"Document {idx + 1}"])
            self.add_tree_item(root, doc)
            self.json_tree.addTopLevelItem(root)

    def edit_document(self, document: dict) -> None:
        dialog = EditDocumentDialog(document, parent=self.centralWidget())
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if edited_doc := dialog.get_edited_document():
                self.update_document_in_db(edited_doc)

    def update_document_in_db(self, edited_doc: dict) -> None:
        if not self.mongo_client or "_id" not in edited_doc:
            QMessageBox.warning(
                self, "Update Error", "No MongoDB client or missing _id."
            )
            return
        try:
            result = self.mongo_client.update_document(
                self.last_collection, edited_doc["_id"], edited_doc
            )
            if result:
                QMessageBox.information(self, "Success", "Document updated.")
                self.display_results()
            else:
                QMessageBox.warning(self, "Update Failed", "Document update failed.")
        except Exception as e:
            handle_exception(e, self)

    def add_tree_item(self, parent: QTreeWidgetItem, data: dict[str, Any]) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                child = QTreeWidgetItem([str(key)])
                self.add_tree_item(child, value)
                parent.addChild(child)
            else:
                child = QTreeWidgetItem([str(key), str(value)])
                parent.addChild(child)

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

    def resizeEvent(self, a0: Any) -> None:
        super().resizeEvent(a0)
        set_minimum_heights(self)

    def open_connection_manager_window(self) -> None:
        dlg = ConnectionManagerWindow()
        dlg.exec()

    def on_state_changed(self, state: dict[str, Any]) -> None:
        """Handle state changes as a StateObserver."""
        # Update state from StateManager
        # Example: update UI or internal state based on state dict
        pass

    def set_mongo_client(self, mongo_client: Any) -> None:
        self.mongo_client = mongo_client

    def get_mongo_client(self) -> Any:
        return self.mongo_client

    def set_active_clients(self, active_clients: dict[str, Any]) -> None:
        self.active_clients = active_clients

    def get_active_clients(self) -> dict[str, Any]:
        return self.active_clients

    # Example usage in methods:
    def connect_to_database(self, connection_name: str) -> None:
        # Explicitly call the mixin method to avoid recursion
        ConnectionWidgetsMixin.connect_to_database(self, connection_name)

    def on_row_selected(self) -> None:
        """Handle table row selection."""
        pass  # Implement row selection handling if needed
