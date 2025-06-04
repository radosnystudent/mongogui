import re
from typing import Any, Callable, Dict, List, Optional, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.connection_manager import ConnectionManager
from core.mongo_client import MongoClientWrapper
from gui.collection_panel import CollectionPanelMixin
from gui.connection_widgets import ConnectionWidgetsMixin
from gui.constants import EDIT_DOCUMENT_ACTION, EDIT_DOCUMENT_TITLE
from gui.edit_document_dialog import EditDocumentDialog
from gui.query_panel import QueryPanelMixin
from gui.ui_utils import set_minimum_heights

bson_dumps: Optional[Callable[..., str]]
try:
    from bson.json_util import dumps as _bson_dumps

    bson_dumps = _bson_dumps
except ImportError:
    bson_dumps = None


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
        self.mongo_client: Optional[MongoClientWrapper] = None
        self.current_connection: Optional[Dict[str, Any]] = None
        self.current_page = 0
        self.page_size = 50
        self.results: List[Dict[str, Any]] = []
        self.last_query = ""
        self.last_query_type = ""
        self.last_collection = ""
        self.data_table: Optional[QTableWidget] = None
        self.json_tree: Optional[QTreeWidget] = None

        self.setup_ui()

        # Load connections at startup
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

        # Connection controls
        connection_label = QLabel("Connections:")
        left_layout.addWidget(connection_label)

        # Connection list area
        self.connection_scroll = QScrollArea()
        self.connection_widget = QWidget()
        self.connection_layout = QVBoxLayout(self.connection_widget)
        self.connection_scroll.setWidget(self.connection_widget)
        self.connection_scroll.setWidgetResizable(True)
        left_layout.addWidget(self.connection_scroll)

        # Add connection button
        add_conn_btn = QPushButton("Add Connection")
        add_conn_btn.clicked.connect(self.add_connection)
        left_layout.addWidget(add_conn_btn)

        # Database info
        self.db_info_label = QLabel("No connection selected")
        self.db_info_label.setWordWrap(True)  # Allow long messages to wrap
        left_layout.addWidget(self.db_info_label)

        # Hidden result display for test compatibility
        self.result_display = QTextEdit()
        self.result_display.setObjectName("result_display")
        self.result_display.setVisible(False)
        left_layout.addWidget(self.result_display)

        # Collection list
        self.collection_scroll = QScrollArea()
        self.collection_widget = QWidget()
        self.collection_layout = QVBoxLayout(self.collection_widget)
        self.collection_layout.setSpacing(0)  # Remove all spacing between buttons
        self.collection_layout.setContentsMargins(0, 0, 0, 0)
        self.collection_scroll.setWidget(self.collection_widget)
        self.collection_scroll.setWidgetResizable(True)
        left_layout.addWidget(self.collection_scroll)

        main_layout.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Query input
        query_label = QLabel("Query:")
        right_layout.addWidget(query_label)

        self.query_input = QTextEdit()
        self.query_input.setFixedHeight(100)
        self.query_input.setPlaceholderText(
            "Enter MongoDB query (e.g., db.collection.find({}))"
        )
        right_layout.addWidget(self.query_input)

        # Query controls
        query_controls = QHBoxLayout()

        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_query)
        query_controls.addWidget(execute_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_query)
        query_controls.addWidget(clear_btn)

        query_controls.addStretch()
        right_layout.addLayout(query_controls)

        # Results display
        results_label = QLabel("Results:")
        # Add spacing above Results label
        right_layout.addSpacing(30)
        right_layout.addWidget(results_label)

        # Results navigation
        nav_layout = QHBoxLayout()

        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)
        nav_layout.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1")
        nav_layout.addWidget(self.page_label)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        nav_layout.addWidget(self.next_btn)

        nav_layout.addStretch()

        self.result_count_label = QLabel("")
        nav_layout.addWidget(self.result_count_label)

        right_layout.addLayout(nav_layout)

        # Results area using splitter
        results_splitter = QSplitter()
        results_splitter.setOrientation(Qt.Orientation.Vertical)

        # Table view
        self.data_table = QTableWidget()
        results_splitter.addWidget(self.data_table)

        # JSON tree view
        self.json_tree = QTreeWidget()
        self.json_tree.setHeaderLabels(["Key", "Value"])
        results_splitter.addWidget(self.json_tree)
        self.json_tree.hide()

        results_splitter.setSizes([400, 200])
        right_layout.addWidget(results_splitter, stretch=1)

        right_panel.setLayout(right_layout)
        main_layout.addWidget(right_panel, stretch=1)

    def execute_query(self) -> None:
        if not self.mongo_client:
            self.db_info_label.setText("No database connection")
            self.result_display.setPlainText("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self.db_info_label.setText("Please enter a query")
            self.result_display.setPlainText("Please enter a query")
            return
        # Extract collection name from query (e.g., db.collection.find(...))

        match = re.search(r"db\.(\w+)\.", query_text)
        if match:
            self.last_collection = match.group(1)
        try:
            result = self.mongo_client.execute_query(query_text)
            if isinstance(result, list):
                self.results = result
                self.current_page = 0
                self.last_query = query_text
                self.display_results()
            else:
                self.db_info_label.setText(f"Error: {result}")
                self.result_display.setPlainText(f"Error: {result}")
        except Exception as e:
            self.db_info_label.setText(f"Query error: {str(e)}")
            self.result_display.setPlainText(f"Query error: {str(e)}")

    def display_results(self) -> None:
        if not self.results:
            self.result_display.setPlainText("No results")
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

        # For test compatibility, show all documents as text in result_display
        if page_results:
            if bson_dumps is not None:
                self.result_display.setPlainText(
                    "\n".join(bson_dumps(doc, indent=2) for doc in page_results)
                )
            else:
                import json

                self.result_display.setPlainText(
                    "\n".join(json.dumps(doc) for doc in page_results)
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
        self.data_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.show_table_context_menu)

        self._table_row_docs = []  # Store docs for context menu
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
            # Store doc in item using setData with Qt.ItemDataRole
            doc_item.setData(0, int(Qt.ItemDataRole.UserRole), doc)
        self.json_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.json_tree.customContextMenuRequested.connect(self.show_tree_context_menu)

    def show_tree_context_menu(self, pos: Any) -> None:
        if not self.json_tree:
            return
        item = self.json_tree.itemAt(pos)
        if item and item.parent() is None:  # Only top-level items
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
            from core.utils import convert_to_object_id

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

    def resizeEvent(self, a0: Any) -> None:
        super().resizeEvent(a0)
        set_minimum_heights(self)
