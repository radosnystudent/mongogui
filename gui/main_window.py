from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem
from core.connection_manager import ConnectionManager
from core.mongo_client import MongoClientWrapper
from gui.connection_dialog import ConnectionDialog
import json
import re

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mongo Client")
        self.setGeometry(100, 100, 800, 600)

        # Core logic
        self.connection_manager = ConnectionManager()
        self.mongo_client = MongoClientWrapper()

        # State for pagination and display
        self.results = []
        self.current_page = 0
        self.page_size = 20
        self.last_query = None
        self.last_query_type = None  # 'find' or 'aggregate'
        self.last_collection = None
        self.display_mode = 'Pretty JSON'

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        connection_layout = QHBoxLayout()
        query_layout = QVBoxLayout()
        result_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()

        # Connection selection
        self.connection_combo = QComboBox()
        self.new_connection_btn = QPushButton("New Connection")
        connection_layout.addWidget(QLabel("Connection:"))
        connection_layout.addWidget(self.connection_combo)
        connection_layout.addWidget(self.new_connection_btn)

        # Query input
        self.query_input = QTextEdit()
        self.run_btn = QPushButton("Run")
        query_layout.addWidget(QLabel("Mongo Query (Studio3T syntax):"))
        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.run_btn)

        # Results display controls
        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Pretty JSON", "Table"])
        self.display_mode_combo.currentTextChanged.connect(self.change_display_mode)
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50"])
        self.page_size_combo.setCurrentText("20")
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.page_label = QLabel("Page 1")
        controls_layout.addWidget(QLabel("Display as:"))
        controls_layout.addWidget(self.display_mode_combo)
        controls_layout.addWidget(QLabel("Page size:"))
        controls_layout.addWidget(self.page_size_combo)
        controls_layout.addStretch()
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.page_label)
        controls_layout.addWidget(self.next_btn)

        # Results display
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_table = None  # Will be created as needed
        self.result_area_widget = QWidget()
        self.result_area_layout = QVBoxLayout()
        self.result_area_layout.setContentsMargins(0, 0, 0, 0)
        self.result_area_widget.setLayout(self.result_area_layout)
        self.result_area_layout.addWidget(self.result_display)
        result_layout.addLayout(controls_layout)
        result_layout.addWidget(self.result_area_widget)

        # Assemble main layout
        main_layout.addLayout(connection_layout)
        main_layout.addLayout(query_layout)
        main_layout.addLayout(result_layout)
        central_widget.setLayout(main_layout)

        # Signals
        self.new_connection_btn.clicked.connect(self.add_connection)
        self.connection_combo.currentIndexChanged.connect(self.connect_to_selected)
        self.run_btn.clicked.connect(self.run_query)
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)

        # Load connections
        self.load_connections()

    def load_connections(self):
        self.connection_combo.clear()
        self.connections = self.connection_manager.get_connections()
        for conn in self.connections:
            self.connection_combo.addItem(conn["name"])
        if self.connections:
            self.connect_to_selected()

    def add_connection(self):
        dialog = ConnectionDialog(self)
        if dialog.exec_() == dialog.Accepted:
            result = dialog.get_result()
            if result:
                name, db, ip, port, login, password, tls = result
                self.connection_manager.add_connection(name, db, ip, port, login, password, tls)
                self.load_connections()

    def connect_to_selected(self):
        idx = self.connection_combo.currentIndex()
        if idx < 0 or idx >= len(self.connections):
            return
        conn_meta = self.connections[idx]
        conn = self.connection_manager.get_connection_by_name(conn_meta["name"])
        ok, msg = self.mongo_client.connect(
            conn["ip"], conn["port"], conn["db"], conn.get("login", ""), conn.get("password", ""), conn.get("tls", False)
        )
        if not ok:
            QMessageBox.critical(self, "Connection Error", msg)
        else:
            self.result_display.setPlainText(f"Connected to {conn['name']} ({conn['db']}@{conn['ip']}:{conn['port']})")

    def run_query(self):
        text = self.query_input.toPlainText().strip()
        if not text:
            return
        # Get current connection to fetch db name
        idx = self.connection_combo.currentIndex()
        if idx < 0 or idx >= len(self.connections):
            self.result_display.setPlainText("No connection selected.")
            return
        conn_meta = self.connections[idx]
        conn = self.connection_manager.get_connection_by_name(conn_meta["name"])
        db_name = conn["db"]
        # Support Studio3T-like syntax: db.<collection>.find(<query>) or db.<collection>.aggregate([ ... ])
        pattern_find = r"^db\.([a-zA-Z0-9_]+)\.find\((.*)\)\s*$"
        pattern_agg = r"^db\.([a-zA-Z0-9_]+)\.aggregate\((.*)\)\s*$"
        match_find = re.match(pattern_find, text, re.DOTALL)
        match_agg = re.match(pattern_agg, text, re.DOTALL)
        if match_find:
            collection_name = match_find.group(1)
            query_str = match_find.group(2)
            try:
                query_dict = json.loads(query_str)
            except Exception as e:
                self.result_display.setPlainText(f"Invalid JSON in query: {e}")
                return
            ok, result = self.mongo_client.run_query(db_name, collection_name, query_dict)
        elif match_agg:
            collection_name = match_agg.group(1)
            pipeline_str = match_agg.group(2)
            try:
                pipeline = json.loads(pipeline_str)
                if not isinstance(pipeline, list):
                    raise ValueError("Pipeline must be a list")
            except Exception as e:
                self.result_display.setPlainText(f"Invalid JSON in aggregation pipeline: {e}")
                return
            ok, result = self.mongo_client.run_aggregate(db_name, collection_name, pipeline)
        else:
            self.result_display.setPlainText(
                "Invalid query syntax.\nUse: db.<collection>.find(<query>) or db.<collection>.aggregate([ ... ])\n" +
                "Example find: db.users.find({ \"name\": \"John\" })\n" +
                "Example aggregate: db.users.aggregate([ {\"$match\": {\"name\": \"John\"}}, {\"$lookup\": { ... }} ])"
            )
            return
        if ok:
            self.results = result
            self.current_page = 0
            self.last_query = text
            self.last_query_type = 'find' if match_find else 'aggregate'
            self.last_collection = collection_name
            self.display_results()
        else:
            self.result_display.setPlainText(f"Error: {result}")

    def change_display_mode(self, mode):
        self.display_mode = mode
        self.display_results()

    def change_page_size(self, size):
        self.page_size = int(size)
        self.current_page = 0
        self.display_results()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_results()

    def next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.results):
            self.current_page += 1
            self.display_results()

    def display_results(self):
        # Pagination
        total = len(self.results)
        if total == 0:
            self.page_label.setText("Page 0")
            # Remove table if present
            if self.result_table:
                self.result_area_layout.removeWidget(self.result_table)
                self.result_table.deleteLater()
                self.result_table = None
            # Ensure result_display is shown and only once
            if self.result_display.parent() is not self.result_area_widget:
                # Remove all widgets from result_area_layout
                while self.result_area_layout.count():
                    widget = self.result_area_layout.takeAt(0).widget()
                    if widget:
                        widget.setParent(None)
                self.result_area_layout.addWidget(self.result_display)
            self.result_display.setPlainText("No results.")
            return
        start = self.current_page * self.page_size
        end = min(start + self.page_size, total)
        page_results = self.results[start:end]
        self.page_label.setText(f"Page {self.current_page + 1} / {((total - 1) // self.page_size) + 1}")
        if self.display_mode == "Pretty JSON":
            # Remove table if present
            if self.result_table:
                self.result_area_layout.removeWidget(self.result_table)
                self.result_table.deleteLater()
                self.result_table = None
            # Ensure result_display is shown and only once
            if self.result_display.parent() is not self.result_area_widget:
                while self.result_area_layout.count():
                    widget = self.result_area_layout.takeAt(0).widget()
                    if widget:
                        widget.setParent(None)
                self.result_area_layout.addWidget(self.result_display)
            blocks = []
            for doc in page_results:
                blocks.append(json.dumps(doc, indent=2, default=str))
            self.result_display.setPlainText("\n---\n".join(blocks))
        elif self.display_mode == "Table":
            # Remove result_display if present
            if self.result_display.parent() is self.result_area_widget:
                self.result_area_layout.removeWidget(self.result_display)
            # Remove old table if present
            if self.result_table:
                self.result_area_layout.removeWidget(self.result_table)
                self.result_table.deleteLater()
                self.result_table = None
            # Collect all keys
            all_keys = set()
            for doc in page_results:
                all_keys.update(doc.keys())
            all_keys = sorted(all_keys)
            # Create table widget
            self.result_table = QTableWidget()
            self.result_table.setColumnCount(len(all_keys))
            self.result_table.setRowCount(len(page_results))
            self.result_table.setHorizontalHeaderLabels(all_keys)
            for row_idx, doc in enumerate(page_results):
                for col_idx, key in enumerate(all_keys):
                    val = doc.get(key, "")
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, default=str)
                    item = QTableWidgetItem(str(val))
                    self.result_table.setItem(row_idx, col_idx, item)
            # Ensure only the table is shown
            while self.result_area_layout.count():
                widget = self.result_area_layout.takeAt(0).widget()
                if widget:
                    widget.setParent(None)
            self.result_area_layout.addWidget(self.result_table)
