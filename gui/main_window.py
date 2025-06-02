from typing import Any, Dict, List, Optional, Set

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
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
    QMenu,
    QMessageBox,
)

from core.connection_manager import ConnectionManager
from core.mongo_client import MongoClientWrapper
from gui.connection_dialog import ConnectionDialog
from gui.connection_widgets import ConnectionWidgetsMixin
from gui.query_panel import QueryPanelMixin
from gui.collection_panel import CollectionPanelMixin
from gui.ui_utils import set_minimum_heights
from gui.edit_document_dialog import EditDocumentDialog

EDIT_DOCUMENT_ACTION = "Edit Document"
EDIT_DOCUMENT_TITLE = EDIT_DOCUMENT_ACTION


class MainWindow(QMainWindow, ConnectionWidgetsMixin, QueryPanelMixin, CollectionPanelMixin):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MongoDB GUI")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize components
        self.conn_manager = ConnectionManager()
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
        left_layout.addWidget(self.db_info_label)

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

    def load_connections(self) -> None:  # Clear existing connection widgets
        while self.connection_layout.count():
            child = self.connection_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()

        # Load connections from manager
        connections = self.conn_manager.get_connections()
        for conn in connections:
            self.add_connection_widget(conn)

    def add_connection_widget(self, conn: Dict[str, Any]) -> None:
        conn_widget = QWidget()
        conn_layout = QVBoxLayout(conn_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(10)

        # Connection name and info
        name_label = QLabel(f"<b>{conn['name']}</b>")
        name_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        name_label.customContextMenuRequested.connect(
            lambda pos, n=conn["name"]: self.show_connection_context_menu(pos, n, name_label)
        )
        conn_layout.addWidget(name_label)

        info_label = QLabel(f"{conn['ip']}:{conn['port']}")
        conn_layout.addWidget(info_label)

        # Connect button only
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.connect_to_database(conn["name"]))
        conn_layout.addWidget(connect_btn)

        conn_layout.addStretch(1)
        self.connection_layout.addWidget(conn_widget)

    def show_connection_context_menu(self, pos, name, widget):
        menu = QMenu(widget)
        edit_action = menu.addAction("Edit")
        duplicate_action = menu.addAction("Duplicate")
        remove_action = menu.addAction("Remove")
        action = menu.exec_(widget.mapToGlobal(pos))
        if action == edit_action:
            self.edit_connection(name)
        elif action == duplicate_action:
            self.duplicate_connection(name)
        elif action == remove_action:
            self.remove_connection(name)

    def connect_to_database(self, connection_name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(connection_name)
        if not conn_data:
            self.db_info_label.setText(f"Connection '{connection_name}' not found")
            return

        try:
            self.mongo_client = MongoClientWrapper()
            success = self.mongo_client.connect(
                conn_data["ip"],
                conn_data["port"],
                conn_data["db"],
                conn_data.get("login"),
                conn_data.get("password"),
                conn_data.get("tls", False),
            )

            if success:
                self.current_connection = conn_data
                self.db_info_label.setText(f"Connected to: {connection_name}")
                self.load_collections()
            else:
                self.db_info_label.setText(f"Failed to connect to {connection_name}")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Connection error: {str(e)}")

    def load_collections(self) -> None:
        if not self.mongo_client:
            return  # Clear existing collection widgets
        while self.collection_layout.count():
            child = self.collection_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()

        try:
            collections = self.mongo_client.list_collections()
            # Sort collections alphabetically
            collections = sorted(collections)
            for collection_name in collections:
                self.add_collection_widget(collection_name)
            self.collection_layout.addStretch(1)
        except Exception as e:
            self.db_info_label.setPlainText(f"Error loading collections: {str(e)}")

    def add_collection_widget(self, collection_name: str) -> None:
        collection_btn = QPushButton(collection_name)
        collection_btn.clicked.connect(
            lambda: self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        )
        self.collection_layout.addWidget(collection_btn)

    def execute_query(self) -> None:
        if not self.mongo_client:
            self.db_info_label.setPlainText("No database connection")
            return

        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self.db_info_label.setPlainText("Please enter a query")
            return

        try:
            # Parse and execute query
            result = self.mongo_client.execute_query(query_text)

            if isinstance(result, list):
                self.results = result
                self.current_page = 0
                self.last_query = query_text
                self.display_results()
            else:
                self.db_info_label.setPlainText(f"Error: {result}")
        except Exception as e:
            self.db_info_label.setPlainText(f"Query error: {str(e)}")

    def display_results(self) -> None:
        if not self.results:
            # Remove reference to self.result_display
            # self.result_display.setPlainText("No results")
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

    def show_table_context_menu(self, pos):
        if not self.data_table:
            return
        index = self.data_table.indexAt(pos)
        if not index.isValid():
            return
        doc = self._table_row_docs[index.row()] if hasattr(self, '_table_row_docs') and index.row() < len(self._table_row_docs) else None
        if doc:
            menu = QMenu(self.data_table)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = self.data_table.viewport() if hasattr(self.data_table, 'viewport') else None
            global_pos = viewport.mapToGlobal(pos) if viewport else self.data_table.mapToGlobal(pos)
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

    def show_tree_context_menu(self, pos):
        if not self.json_tree:
            return
        item = self.json_tree.itemAt(pos)
        if item and item.parent() is None:  # Only top-level items
            menu = QMenu(self.json_tree)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = self.json_tree.viewport() if hasattr(self.json_tree, 'viewport') else None
            global_pos = viewport.mapToGlobal(pos) if viewport else self.json_tree.mapToGlobal(pos)
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
        if not self.mongo_client or '_id' not in edited_doc:
            QMessageBox.warning(self, EDIT_DOCUMENT_TITLE, "Cannot update document: missing _id or no DB connection.")
            return
        try:
            # Use the current collection (parsed from last_query or last_collection)
            collection = self.last_collection
            if not collection:
                QMessageBox.warning(self, EDIT_DOCUMENT_TITLE, "Cannot determine collection for update.")
                return
            result = self.mongo_client.update_document(collection, edited_doc['_id'], edited_doc)
            if result:
                QMessageBox.information(self, EDIT_DOCUMENT_TITLE, "Document updated successfully.")
                self.execute_query()  # Refresh results
            else:
                QMessageBox.warning(self, EDIT_DOCUMENT_TITLE, "Document update failed.")
        except Exception as e:
            QMessageBox.critical(self, EDIT_DOCUMENT_TITLE, f"Error updating document: {e}")

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

    def resizeEvent(self, a0) -> None:
        super().resizeEvent(a0)
        set_minimum_heights(self)

    def edit_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            self.db_info_label.setText(f"Connection '{name}' not found")
            return
        dialog = ConnectionDialog(self)
        # Pre-fill dialog fields
        dialog.name_input.setText(conn_data["name"])
        dialog.db_input.setText(conn_data["db"])
        dialog.ip_input.setText(conn_data["ip"])
        dialog.port_input.setText(str(conn_data["port"]))
        dialog.login_input.setText(conn_data.get("login", ""))
        dialog.password_input.setText(conn_data.get("password", ""))
        dialog.tls_checkbox.setChecked(conn_data.get("tls", False))
        if dialog.exec_() == ConnectionDialog.Accepted:
            result = dialog.get_result()
            if result:
                new_name, db, ip, port, login, password, tls = result
                try:
                    port_int = int(port)
                    self.conn_manager.update_connection(
                        name, db, ip, port_int, login, password, tls, new_name=new_name
                    )
                    self.load_connections()
                except ValueError:
                    QMessageBox.critical(self, "Edit Error", "Error: Invalid port number")

    def duplicate_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            self.db_info_label.setText(f"Connection '{name}' not found")
            return
        # Remove credentials from the copy (user can edit after creation)
        conn_data = dict(conn_data)
        conn_data["login"] = conn_data.get("login", "")
        conn_data["password"] = conn_data.get("password", "")
        # Generate a unique name for the duplicate
        base_name = name
        if base_name.endswith(")"):
            # Remove trailing (Copy X) or (Copy)
            import re
            base_name = re.sub(r" \(Copy( \d+)?\)$", "", base_name)
        new_name = f"{base_name} (Copy)"
        existing_names = {c["name"] for c in self.conn_manager.get_connections()}
        copy_idx = 2
        while new_name in existing_names:
            new_name = f"{base_name} (Copy {copy_idx})"
            copy_idx += 1
        # Save the duplicated connection
        try:
            self.conn_manager.add_connection(
                new_name,
                conn_data["db"],
                conn_data["ip"],
                conn_data["port"],
                conn_data.get("login", ""),
                conn_data.get("password", ""),
                conn_data.get("tls", False),
            )
            self.load_connections()
            self.db_info_label.setText(f"Duplicated connection as '{new_name}'")
        except Exception as e:
            QMessageBox.critical(self, "Duplicate Error", f"Failed to duplicate: {e}")

    def add_connection(self) -> None:
        dialog = ConnectionDialog(self)
        if dialog.exec_() == ConnectionDialog.Accepted:
            result = dialog.get_result()
            if result:
                name, db, ip, port, login, password, tls = result
                try:
                    port_int = int(port)
                    self.conn_manager.add_connection(
                        name, db, ip, port_int, login, password, tls
                    )
                    self.load_connections()
                except ValueError:
                    self.db_info_label.setPlainText("Error: Invalid port number")

    def remove_connection(self, name: str) -> None:
        self.conn_manager.remove_connection(name)
        self.load_connections()
