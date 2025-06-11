from collections.abc import Callable
from typing import Any

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QStackedWidget,
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
        # Always set placeholder
        self.query_input.setPlaceholderText(
            f"Enter MongoDB query (e.g., db.{self.collection_name or 'collection'}.find({{}}))"
        )
        # Set initial query if collection_name is provided
        if self.collection_name:
            self.query_input.setText(f"db.{self.collection_name}.find({{}})")
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
        # Page size selector
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setToolTip("Results per page")
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        nav_layout.addWidget(QLabel("Page size:"))
        nav_layout.addWidget(self.page_size_combo)
        layout.addLayout(nav_layout)
        # Results area
        view_switch_layout = QHBoxLayout()
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Tree View", "Table View"])
        self.view_mode_combo.setCurrentIndex(0)  # Default to Tree View
        self.view_mode_combo.setToolTip("Select results view mode")
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        view_switch_layout.addStretch()
        view_switch_layout.addWidget(QLabel("View as:"))
        view_switch_layout.addWidget(self.view_mode_combo)
        layout.addLayout(view_switch_layout)

        results_splitter = QSplitter()
        results_splitter.setOrientation(Qt.Orientation.Vertical)
        self.results_stack = QStackedWidget()
        self.data_table = QTableWidget()
        self.json_tree = QTreeWidget()
        self.json_tree.setHeaderLabels(["Key", "Value"])
        self.results_stack.addWidget(self.json_tree)  # index 0: Tree View
        self.results_stack.addWidget(self.data_table)  # index 1: Table View
        results_splitter.addWidget(self.results_stack)
        self.setup_query_panel_signals()
        results_splitter.setSizes([400, 200])
        layout.addWidget(results_splitter, stretch=1)
        set_minimum_heights(self)
        self.setLayout(layout)

        self._suggestion_popup = QListWidget(self)
        self._suggestion_popup.setWindowFlags(
            self._suggestion_popup.windowFlags() | Qt.WindowType.Popup
        )
        self._suggestion_popup.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._suggestion_popup.setMouseTracking(True)
        self._suggestion_popup.hide()
        self._suggestion_popup.itemClicked.connect(self._insert_suggestion)
        self.query_input.installEventFilter(self)
        self._popup_shown = False

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

    def execute_query(self) -> None:
        if not self.mongo_client:
            self._set_db_info_label("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self._set_db_info_label("Please enter a query")
            return
        try:
            # Use server-side pagination
            result = self.mongo_client.execute_query(
                query_text,
                page=self.current_page,
                page_size=self.page_size,
            )
            if isinstance(result, list):
                self.results = result
                self.last_query = query_text
                self.display_results()
            else:
                self._set_db_info_label(f"Error: {result}")
        except Exception as e:
            self._set_db_info_label(f"Query error: {str(e)}")

    def next_page(self) -> None:
        self.current_page += 1
        self.execute_query()

    def previous_page(self) -> None:
        if self.current_page > 0:
            self.current_page -= 1
            self.execute_query()

    def _on_page_size_changed(self, value: str) -> None:
        try:
            new_size = int(value)
            if new_size != self.page_size:
                self.page_size = new_size
                self.current_page = 0
                self.execute_query()
        except Exception:
            pass

    def _on_view_mode_changed(self, idx: int) -> None:
        self.results_stack.setCurrentIndex(idx)

    def display_results(self) -> None:
        self._reset_ui_for_query_results()
        self.setup_query_panel_signals()
        if not self.results:
            if self.data_table:
                self.data_table.setRowCount(0)
            if getattr(self, "json_tree", None):
                self.json_tree.clear()
                self.json_tree.hide()
            self.page_label.setText(f"Page {self.current_page + 1}")
            self.result_count_label.setText("No results")
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(False)
            return
        # Show all results for this page (already paginated)
        page_results = self.results
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(len(page_results) == self.page_size)
        self.page_label.setText(f"Page {self.current_page + 1}")
        self.result_count_label.setText(f"Showing {len(page_results)} results")
        # Always update both views, but show only the selected one
        self.display_tree_results(page_results)
        self.display_table_results(page_results)
        self.results_stack.setCurrentIndex(self.view_mode_combo.currentIndex())
        # Hide the unused view for accessibility
        self.json_tree.setVisible(self.view_mode_combo.currentIndex() == 0)
        self.data_table.setVisible(self.view_mode_combo.currentIndex() == 1)

    def _get_field_path_at_cursor(self) -> list[str]:
        """Parse the query and cursor position to extract the field path for suggestions."""
        text = self.query_input.toPlainText()
        cursor = self.query_input.textCursor()
        pos = cursor.position()
        before = text[:pos]
        import re

        # Try to find the last field path before the cursor, e.g. {"documents. or {documents.documentId.
        m = re.search(r"\{[^{}]*?([\w\.]+\.)?$", before)
        if m:
            path_str = m.group(1)
            if path_str:
                return [p for p in path_str.strip(".").split(".") if p]
        return []

    def _show_schema_suggestions(self) -> None:
        db = self.db_label or self.last_db_label
        collection = self.collection_name or self.last_collection
        # If collection is not set, try to extract from query input
        if not collection:
            import re

            text = self.query_input.toPlainText()
            m = re.search(r"db\.(\w+)\.find", text)
            if m:
                collection = m.group(1)
        if not db or not collection:
            self._hide_suggestion_popup()
            return
        path = self._get_field_path_at_cursor()
        suggestions = self.get_collection_schema_fields(db, collection, path)
        if suggestions:
            self._show_suggestion_popup(suggestions)
        else:
            self._hide_suggestion_popup()

    def _show_suggestion_popup(self, suggestions: list[str]) -> None:
        """Show the suggestion popup with the given list of suggestions."""
        self._suggestion_popup.clear()
        self._suggestion_popup.addItems(suggestions)
        cursor_rect = self.query_input.cursorRect()
        popup_pos = self.query_input.mapToGlobal(cursor_rect.bottomLeft())
        self._suggestion_popup.move(popup_pos)
        self._suggestion_popup.setCurrentRow(0)
        self._suggestion_popup.show()
        self._popup_shown = True

    # PyQt5 expects the argument names to be a0 and a1 for eventFilter, but for clarity, we alias them internally.
    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        watched = a0
        event = a1
        if watched is not self.query_input:
            return super().eventFilter(watched, event)
        if event is None or event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)
        if not isinstance(event, QKeyEvent):
            return super().eventFilter(watched, event)

        key = event.key()
        if key == Qt.Key.Key_F1:
            self._show_schema_suggestions()
            return True
        if not self._popup_shown:
            return super().eventFilter(watched, event)

        if key in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            self._suggestion_popup.setFocus()
            current_row = self._suggestion_popup.currentRow()
            if key == Qt.Key.Key_Down:
                new_row = min(current_row + 1, self._suggestion_popup.count() - 1)
            else:  # key == Qt.Key.Key_Up
                new_row = max(current_row - 1, 0)
            self._suggestion_popup.setCurrentRow(new_row)
            self._hide_suggestion_popup()
            return True
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self._suggestion_popup.currentItem()
            if current:
                self._insert_suggestion(current)
                return True
        return super().eventFilter(watched, event)

    def _insert_suggestion(self, item: QListWidgetItem | None) -> None:
        if item is None:
            return
        suggestion = item.text()
        cursor = self.query_input.textCursor()
        # Insert at cursor position, add quotes if not present
        if not (suggestion.startswith('"') or suggestion.startswith("'")):
            suggestion = f'"{suggestion}"'
        cursor.insertText(suggestion)
        self._hide_suggestion_popup()

    def _hide_suggestion_popup(self) -> None:
        self._suggestion_popup.hide()
        self._popup_shown = False
