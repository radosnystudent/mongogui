from typing import Any, Dict, List, Optional, Set

from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.connection_manager import ConnectionManager
from core.mongo_client import MongoClientWrapper
from gui.connection_dialog import ConnectionDialog


class MainWindow(QMainWindow):
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

        # Table view
        self.data_table = QTableWidget()
        results_splitter.addWidget(self.data_table)

        # Raw JSON view
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        results_splitter.addWidget(self.result_display)

        results_splitter.setSizes([600, 400])
        right_layout.addWidget(results_splitter)

        main_layout.addWidget(right_panel)

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
        conn_layout.setContentsMargins(5, 5, 5, 5)

        # Connection name and info
        name_label = QLabel(f"<b>{conn['name']}</b>")
        conn_layout.addWidget(name_label)

        info_label = QLabel(f"{conn['ip']}:{conn['port']}")
        conn_layout.addWidget(info_label)

        # Connect button
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.connect_to_database(conn["name"]))
        conn_layout.addWidget(connect_btn)

        self.connection_layout.addWidget(conn_widget)

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
                    self.result_display.setPlainText("Error: Invalid port number")

    def connect_to_database(self, connection_name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(connection_name)
        if not conn_data:
            self.result_display.setPlainText(
                f"Connection '{connection_name}' not found"
            )
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
                self.result_display.setPlainText(f"Connected to {connection_name}")
            else:
                self.result_display.setPlainText(
                    f"Failed to connect to {connection_name}"
                )
        except Exception as e:
            self.result_display.setPlainText(f"Connection error: {str(e)}")

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
            for collection_name in collections:
                self.add_collection_widget(collection_name)
        except Exception as e:
            self.result_display.setPlainText(f"Error loading collections: {str(e)}")

    def add_collection_widget(self, collection_name: str) -> None:
        collection_btn = QPushButton(collection_name)
        collection_btn.clicked.connect(
            lambda: self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
        )
        self.collection_layout.addWidget(collection_btn)

    def execute_query(self) -> None:
        if not self.mongo_client:
            self.result_display.setPlainText("No database connection")
            return

        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self.result_display.setPlainText("Please enter a query")
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
                self.result_display.setPlainText(f"Error: {result}")
        except Exception as e:
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

        # Display raw JSON
        import json

        self.result_display.setPlainText(
            json.dumps(page_results, indent=2, default=str)
        )

    def display_table_results(self, results: List[Dict[str, Any]]) -> None:
        if not results or not self.data_table:
            return

        # Get all unique keys from all documents
        all_keys: Set[str] = set()
        for doc in results:
            all_keys.update(doc.keys())

        # Convert to sorted list for consistent column ordering
        columns = sorted(all_keys)

        # Set up table
        self.data_table.setColumnCount(len(columns))
        self.data_table.setRowCount(len(results))
        self.data_table.setHorizontalHeaderLabels(columns)

        # Populate table
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
