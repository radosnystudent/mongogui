from collections.abc import Callable
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
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
from db.mongo_client import MongoClientWrapper
from db.utils import convert_to_object_id  # Moved import to top
from ui.collection_panel import CollectionPanelMixin
from ui.connection_widgets import ConnectionWidgetsMixin
from ui.constants import EDIT_DOCUMENT_TITLE
from ui.edit_document_dialog import EditDocumentDialog
from ui.query_panel import QueryPanelMixin
from ui.query_tab import QueryTabWidget
from ui.ui_utils import set_minimum_heights

bson_dumps: Callable[..., str] | None
try:
    from bson.json_util import dumps as _bson_dumps

    bson_dumps = _bson_dumps
except ImportError:
    bson_dumps = None

NO_DB_CONNECTION_MSG = "No database connection"


class MainWindow(
    QMainWindow, ConnectionWidgetsMixin, QueryPanelMixin, CollectionPanelMixin
):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MongoDB GUI")
        self.setGeometry(100, 100, 1200, 800)

        # Instantiate ConnectionManager
        self.conn_manager = ConnectionManager()

        # Initialize components
        self.mongo_client: MongoClientWrapper | None = None
        self.current_connection: dict[str, Any] | None = None
        self.current_page = 0
        self.page_size = 50
        self.results: list[dict[str, Any]] = []
        self.last_query = ""
        self.last_query_type = ""
        self.last_collection: str = ""  # keep as str for mixin compatibility
        self.data_table: QTableWidget | None = None
        self.json_tree: QTreeWidget | None = None
        self.query_tabs = QTabWidget()
        self.query_tabs.setTabsClosable(True)
        self.query_tabs.tabCloseRequested.connect(self._close_query_tab)
        self.query_tabs.setMovable(True)

        from PyQt5.QtWidgets import QVBoxLayout

        self.connection_layout = QVBoxLayout()

        self.setup_ui()
        self.load_connections()

    def setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left panel for connections
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)

        # Add 'Connections' button to open the connection manager window
        open_conn_mgr_btn = QPushButton("Connections")
        open_conn_mgr_btn.clicked.connect(self.open_connection_manager_window)
        left_layout.addWidget(open_conn_mgr_btn)

        # Collection tree (replaces old button list)
        from PyQt5.QtWidgets import QTreeWidget

        self.collection_tree = QTreeWidget()
        self.collection_tree.setMinimumHeight(200)
        left_layout.addWidget(self.collection_tree)
        self.setup_collection_tree()  # Provided by CollectionPanelMixin

        main_layout.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Add query tabs widget
        right_layout.addWidget(self.query_tabs, stretch=1)

        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, stretch=1)

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
        elif (
            not active_db_label and self.mongo_client
        ):  # Fallback for a general connection
            mongo_client = self.mongo_client
            if self.current_connection:
                active_db_label = self.current_connection.get("label")

        # Prevent opening a tab if no client is resolved, unless it's the initial state without any tabs.
        is_initial_empty_state = not self.query_tabs.count() and not (
            hasattr(self, "active_clients") and self.active_clients
        )
        if not mongo_client and not is_initial_empty_state:
            QMessageBox.information(
                self, "New Query Tab", "Please connect to a database first."
            )
            return

        # If mongo_client is still None here, it means we are in the initial empty state or a connection is missing.
        # QueryTabWidget can handle a None mongo_client initially.

        actual_collection_name_for_tab = None  # Always open DB-level tabs
        tab_title = f"Query - {active_db_label}" if active_db_label else "New Query"
        if collection_name and active_db_label and collection_name != active_db_label:
            # This case should ideally not be hit if we always open DB tabs
            # but kept for robustness if collection_name is passed for other reasons.
            # Forcing DB level tab for now.
            pass  # tab_title already set for DB level

        tab = QueryTabWidget(
            parent=self,
            collection_name=actual_collection_name_for_tab,  # Explicitly None for DB context
            db_label=active_db_label,
            mongo_client=mongo_client,
            on_close=self._close_query_tab_by_widget,
        )

        self.query_tabs.addTab(tab, tab_title)
        self.query_tabs.setCurrentWidget(tab)

    def _close_query_tab(self, index: int) -> None:
        widget = self.query_tabs.widget(index)
        if widget:
            self.query_tabs.removeTab(index)
            widget.deleteLater()

    def _close_query_tab_by_widget(self, widget: QWidget) -> None:
        index = self.query_tabs.indexOf(widget)
        if index != -1:
            self._close_query_tab(index)

    def _handle_database_click(self, item_name: str) -> None:
        """Handles clicks on database items in the collection tree."""
        self.add_query_tab(db_label=item_name, collection_name=None)

    def _handle_collection_click(self, item: QTreeWidgetItem) -> None:
        """Handles clicks on collection items in the collection tree."""
        parent_db_item = item.parent()
        if parent_db_item:
            db_label = parent_db_item.text(0)
            self.add_query_tab(db_label=db_label, collection_name=None)
        else:
            QMessageBox.warning(
                self,
                "Error",
                "Could not determine database for the selected collection.",
            )

    def _handle_index_click(self, item: QTreeWidgetItem, item_name: str) -> None:
        """Handles clicks on index items in the collection tree."""
        coll_item = item.parent()
        if not coll_item:
            QMessageBox.warning(
                self, "Error", "Could not determine collection for the selected index."
            )
            return

        coll_data = coll_item.data(0, int(Qt.ItemDataRole.UserRole))
        collection_name_for_index = (
            coll_data.get("name") if coll_data else "Unknown Collection"
        )

        db_item = coll_item.parent()
        if not db_item:
            QMessageBox.warning(
                self, "Error", "Could not determine database for the selected index."
            )
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
        data = item.data(0, int(Qt.ItemDataRole.UserRole))
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
            self.collection_tree.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            self.collection_tree.customContextMenuRequested.connect(
                lambda pos: self.show_collection_context_menu(item, pos)
            )
        else:
            self.collection_tree.setContextMenuPolicy(
                Qt.ContextMenuPolicy.DefaultContextMenu
            )

    def execute_query(self) -> None:
        current_tab = self.query_tabs.currentWidget()
        if not isinstance(current_tab, QueryTabWidget):
            QMessageBox.warning(self, "Query Error", "No active query tab selected.")
            return

        # Delegate query execution to the current QueryTabWidget
        # The QueryTabWidget itself should handle getting the mongo_client and db_label
        current_tab.execute_query()

        # The following logic for displaying results in MainWindow might be redundant
        # if QueryTabWidget handles its own display. Review and remove if necessary.
        # For now, we assume QueryTabWidget updates its own UI.
        # If MainWindow needs to react to results (e.g. status bar), signals/slots would be better.

    # display_results, display_table_results, display_tree_results, edit_document,
    # update_document_in_db, add_tree_item, clear_query, previous_page, next_page
    # are primarily for the QueryPanelMixin and should ideally be managed by QueryTabWidget.
    # MainWindow might not need its own implementations if QueryTabWidget is self-contained.
    # For now, let's leave them but note they might become obsolete or need refactoring.

    def display_results(self) -> None:
        # This method in MainWindow might be deprecated if QueryTabWidget handles its own display.
        # Forwarding to current tab for now, or consider removing.
        current_tab = self.query_tabs.currentWidget()
        if isinstance(current_tab, QueryTabWidget):
            # current_tab.display_results() # QueryTabWidget.display_results will be called by its own execute_query
            pass  # Results are displayed within the tab itself.
        elif not self.results:  # Fallback for old direct execution path (if any)
            if self.data_table:
                self.data_table.setRowCount(0)
            return

        # Calculate pagination
        start_idx = self.current_page * self.page_size
        end_idx = min(start_idx + self.page_size, len(self.results))
        page_results = self.results[start_idx:end_idx]

        # Update navigation controls
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(end_idx < len(self.results))
        self.page_label.setText(f"Page {self.current_page + 1}")
        self.result_count_label.setText(
            f"Showing {start_idx + 1}-{end_idx} of {len(self.results)} results"
        )

        # Display in table format
        self.display_table_results(page_results)

        # Display in tree format
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
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self._table_row_docs = []  # Store docs for context menu
        for row, doc in enumerate(results):
            self._table_row_docs.append(doc)
            for col, key in enumerate(columns):
                value = doc.get(key, "")
                self.data_table.setItem(row, col, QTableWidgetItem(str(value)))

    def display_tree_results(self, results: list[dict[str, Any]]) -> None:
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
            # Store doc in item using setData with Qt.ItemDataRole
            doc_item.setData(0, int(Qt.ItemDataRole.UserRole), doc)

    def edit_document(self, document: dict) -> None:
        dialog = EditDocumentDialog(document, self)
        if dialog.exec_() == QDialog.Accepted:
            edited_doc = dialog.get_edited_document()
            if edited_doc is not None:
                self.update_document_in_db(edited_doc)

    def update_document_in_db(self, edited_doc: dict) -> None:
        # Update document in DB using self.mongo_client
        if not self.mongo_client or "_id" not in edited_doc:
            QMessageBox.warning(
                self,
                EDIT_DOCUMENT_TITLE,
                "Cannot update document: missing _id or no DB connection.",
            )
            return
        try:
            # Use the current collection (parsed from last_query or last_collection)
            collection = self.last_collection
            if not collection:
                QMessageBox.warning(
                    self, EDIT_DOCUMENT_TITLE, "Cannot determine collection for update."
                )
                return
            # Convert _id to ObjectId if possible
            edited_doc["_id"] = convert_to_object_id(edited_doc["_id"])
            result = self.mongo_client.update_document(
                collection, edited_doc["_id"], edited_doc
            )
            if result:
                QMessageBox.information(
                    self, EDIT_DOCUMENT_TITLE, "Document updated successfully."
                )
                self.execute_query()  # Refresh results
            else:
                QMessageBox.warning(
                    self, EDIT_DOCUMENT_TITLE, "Document update failed."
                )
        except Exception as e:
            QMessageBox.critical(
                self, EDIT_DOCUMENT_TITLE, f"Error updating document: {e}"
            )

    def add_tree_item(self, parent: QTreeWidgetItem, data: dict[str, Any]) -> None:
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

    def resizeEvent(self, a0: Any) -> None:
        super().resizeEvent(a0)
        set_minimum_heights(self)

    def open_connection_manager_window(self) -> None:
        from ui.connection_manager_window import ConnectionManagerWindow

        dlg = ConnectionManagerWindow(self)
        dlg.connection_selected.connect(self.connect_to_database)
        dlg.exec_()
        # Optionally: reload connections if changed
        self.load_connections()
