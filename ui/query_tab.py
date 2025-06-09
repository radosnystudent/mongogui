from collections.abc import Callable
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTextEdit,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from ui.query_panel import QueryPanelMixin
from ui.ui_utils import set_minimum_heights


class QueryTabWidget(QWidget, QueryPanelMixin):
    """
    A single query tab containing query input, controls, and results for a collection.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        collection_name: str | None = None,
        db_label: str | None = None,
        mongo_client: Any = None,
        on_close: Callable[[QWidget], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.collection_name = collection_name
        self.db_label = db_label
        self.mongo_client = mongo_client
        self.on_close = on_close
        self.current_page = 0
        self.page_size = 50
        self.results: list[dict[str, Any]] = []
        self.last_query = ""
        self.last_collection = collection_name or ""
        self.last_db_label = db_label or ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Query input
        query_label = QLabel("Query:")
        layout.addWidget(query_label)
        self.query_input = QTextEdit()
        self.query_input.setFixedHeight(100)
        self.query_input.setPlaceholderText(
            f"Enter MongoDB query (e.g., db.{self.collection_name or 'collection'}.find({{}}))"
        )
        layout.addWidget(self.query_input)
        # Query controls
        query_controls = QHBoxLayout()
        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self.execute_query)
        query_controls.addWidget(execute_btn)
        explain_btn = QPushButton("Explain")
        explain_btn.setToolTip("Show query plan and index usage for this query")
        explain_btn.clicked.connect(self.execute_explain)
        query_controls.addWidget(explain_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_query)
        query_controls.addWidget(clear_btn)
        query_controls.addStretch()
        close_btn = QPushButton("Close Tab")
        close_btn.clicked.connect(self._close_tab)
        query_controls.addWidget(close_btn)
        layout.addLayout(query_controls)
        # Results label
        results_label = QLabel("Results:")
        layout.addSpacing(30)
        layout.addWidget(results_label)
        # Navigation
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
        layout.addLayout(nav_layout)
        # Results area
        results_splitter = QSplitter()
        results_splitter.setOrientation(Qt.Orientation.Vertical)
        self.data_table = QTableWidget()
        results_splitter.addWidget(self.data_table)
        self.json_tree = QTreeWidget()
        self.json_tree.setHeaderLabels(["Key", "Value"])
        results_splitter.addWidget(self.json_tree)
        self.json_tree.hide()
        self.setup_query_panel_signals()
        results_splitter.setSizes([400, 200])
        layout.addWidget(results_splitter, stretch=1)
        set_minimum_heights(self)
        self.setLayout(layout)

    def _close_tab(self) -> None:
        if self.on_close:
            self.on_close(self)

    def set_mongo_client(self, mongo_client: Any) -> None:
        self.mongo_client = mongo_client

    def set_collection(self, collection_name: str, db_label: str) -> None:
        self.collection_name = collection_name
        self.last_collection = collection_name
        self.db_label = db_label
        self.last_db_label = db_label
        self.query_input.setPlaceholderText(
            f"Enter MongoDB query (e.g., db.{collection_name}.find({{}}))"
        )

    # Optionally, override execute_query to use the correct mongo_client/collection
    # ...existing code for QueryPanelMixin methods...

    def display_results(self) -> None:
        self._reset_ui_for_query_results()
        self.setup_query_panel_signals()
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
        self.display_tree_results(page_results)
