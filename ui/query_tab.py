import json
import re
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from ui.query_builder_dialog import QueryBuilderDialog
from ui.query_panel import QueryPanelMixin
from ui.ui_utils import set_minimum_heights
from utils.error_handling import handle_exception


class QueryTabWidget(QWidget, QueryPanelMixin):
    """
    A single query tab containing query input, controls, and results for a collection.
    Provides UI and logic for executing queries and displaying results.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        collection_name: str | None = None,
        db_label: str | None = None,
        mongo_client: Any = None,
        on_close: Callable[[QWidget], None] | None = None,
    ) -> None:
        """
        Initialize the QueryTabWidget.

        Args:
            parent: Parent QWidget.
            collection_name: Name of the MongoDB collection.
            db_label: Label for the database.
            mongo_client: MongoDB client instance.
            on_close: Callback for when the tab is closed.
        """
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
        """
        Set up the UI layout and widgets for the query tab.
        """
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

        # Query Builder button
        query_builder_btn = QPushButton("🔧 Query Builder")
        query_builder_btn.setToolTip("Open visual query builder")
        query_builder_btn.clicked.connect(self.open_query_builder)
        query_controls.addWidget(query_builder_btn)

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
        # Results section
        results_label = QLabel("Results:")
        layout.addSpacing(30)
        layout.addWidget(results_label)
        self.result_count_label = QLabel("")
        layout.addWidget(self.result_count_label)

        # Navigation
        self.nav_controls_widget = QWidget()
        nav_layout = QHBoxLayout(self.nav_controls_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
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
        # Page size selector
        self.page_size_label = QLabel("Page size:")
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["10", "20", "50", "100", "200"])
        self.page_size_combo.setCurrentText(str(self.page_size))
        self.page_size_combo.setToolTip("Results per page")
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)
        nav_layout.addWidget(self.page_size_label)
        nav_layout.addWidget(self.page_size_combo)
        self.page_size_picker = (
            self.page_size_combo
        )  # For QueryPanelMixin show/hide logic
        layout.addWidget(self.nav_controls_widget)

        # View Switcher Container
        self.view_switch_widget = QWidget()
        view_switch_layout = QHBoxLayout(self.view_switch_widget)
        view_switch_layout.setContentsMargins(0, 0, 0, 0)
        self.view_as_label = QLabel("View as:")
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Tree View", "Table View"])
        self.view_mode_combo.setCurrentIndex(0)  # Default to Tree View
        self.view_mode_combo.setToolTip("Select results view mode")
        self.view_mode_combo.currentIndexChanged.connect(self._on_view_mode_changed)
        view_switch_layout.addStretch()
        view_switch_layout.addWidget(self.view_as_label)
        view_switch_layout.addWidget(self.view_mode_combo)
        self.view_as_picker = (
            self.view_mode_combo
        )  # For QueryPanelMixin show/hide logic
        layout.addWidget(self.view_switch_widget)

        # Results area
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
        """Close the query tab, triggering the on_close callback if set."""
        if self.on_close:
            self.on_close(self)

    def set_mongo_client(self, mongo_client: Any) -> None:
        """
        Set the MongoDB client instance.

        Args:
            mongo_client: MongoDB client instance.
        """
        self.mongo_client = mongo_client

    def _load_schema_for_collection(
        self, db_label: str, collection_name: str
    ) -> list[str]:
        """Load schema fields from a file or infer from collection."""
        import json
        import os

        schema_fields = []
        schema_path = os.path.join("schemas", f"{db_label}__{collection_name}.json")

        # Try to load from file
        try:
            if os.path.exists(schema_path):
                with open(schema_path) as f:
                    schema = json.load(f)
                    schema_fields = list(
                        schema.keys()
                    )  # Just get top-level field names
        except Exception as e:
            handle_exception(e)

        # Try to infer from collection if needed
        if not schema_fields and self.mongo_client:
            schema_fields = self._infer_schema_from_collection(collection_name)

        # Add _id field if not already present
        if "_id" not in schema_fields:
            schema_fields.insert(0, "_id")

        return schema_fields

    def _infer_schema_from_collection(self, collection_name: str) -> list[str]:
        """Infer schema fields from a sample document in the collection."""
        schema_fields = []
        try:
            # Get a sample document to infer fields
            result = self.mongo_client.execute_query(
                f"db.{collection_name}.findOne({{}})", page=0, page_size=1
            )
            if result.is_ok and result.unwrap():
                # Extract field names from the document
                sample_doc = (
                    result.unwrap()[0]
                    if isinstance(result.unwrap(), list)
                    else result.unwrap()
                )
                schema_fields = list(sample_doc.keys())  # Get field names from sample
        except Exception:
            pass
        return schema_fields

    def set_collection(self, collection_name: str, db_label: str) -> None:
        """Set the current collection and update the query builder."""
        self.collection_name = collection_name
        self.db_label = db_label
        self.last_collection = collection_name
        self.last_db_label = db_label

        # Update window title
        parent = self.parent()
        if parent and isinstance(parent, QTabWidget):
            parent.setTabText(parent.indexOf(self), collection_name)

        # Update query input with new collection name
        if hasattr(self, "query_input"):
            self.query_input.setPlainText(f"db.{collection_name}.find({{}})")
            self.query_input.setPlaceholderText(
                f"Enter MongoDB query (e.g., db.{collection_name}.find({{}}))"
            )

    def execute_query(self) -> None:
        """
        Execute the query entered in the query input field.

        This method retrieves the query text, validates it, and sends it to the
        MongoDB client for execution. The results are then processed and displayed
        in the results area.
        """
        if not self.mongo_client:
            self._set_db_info_label("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self._set_db_info_label("Please enter a query")
            return
        try:
            result = self.mongo_client.execute_query(
                query_text,
                page=self.current_page,
                page_size=self.page_size,
            )
            if result.is_ok:
                self.results = result.unwrap()
                self.last_query = query_text
                self.display_results()
            else:
                self._set_db_info_label(f"Error: {result.unwrap_err()}")
        except Exception as e:
            from PyQt6.QtWidgets import QWidget

            parent_widget = self.parent()
            if isinstance(parent_widget, QWidget):
                handle_exception(e, parent=parent_widget, title="Query Error")
            else:
                handle_exception(e, parent=None, title="Query Error")
            self._set_db_info_label(f"Query error: {str(e)}")

    def next_page(self) -> None:
        """
        Navigate to the next page of results and execute the query.
        """
        self.current_page += 1
        self.execute_query()

    def previous_page(self) -> None:
        """
        Navigate to the previous page of results and execute the query.
        """
        if self.current_page > 0:
            self.current_page -= 1
            self.execute_query()

    def _on_page_size_changed(self, value: str) -> None:
        """
        Handle changes to the page size selector.

        Args:
            value: New page size as a string.
        """
        try:
            new_size = int(value)
            if new_size != self.page_size:
                self.page_size = new_size
                self.current_page = 0
                self.execute_query()
        except Exception:
            pass

    def _on_view_mode_changed(self, idx: int) -> None:
        """
        Change the results view mode (Tree View or Table View).

        Args:
            idx: Index of the selected view mode.
        """
        self.results_stack.setCurrentIndex(idx)

    def display_results(self) -> None:
        """
        Display the query results in the results area.

        This method updates the UI to show the results of the executed query,
        including pagination controls and result views (tree or table).
        """
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
        """
        Parse the query and cursor position to extract the field path for suggestions.

        Returns:
            A list of field path components.
        """
        text = self.query_input.toPlainText()
        cursor = self.query_input.textCursor()
        pos = cursor.position()
        before = text[:pos]

        # Try to find the last field path before the cursor, e.g. {"documents. or {documents.documentId.
        m = re.search(r"\{[^{}]*?([\w\.]+\.)?$", before)
        if m:
            path_str = m.group(1)
            if path_str:
                return [p for p in path_str.strip(".").split(".") if p]
        return []

    def _show_schema_suggestions(self) -> None:
        """
        Show schema suggestions for the fields in the query.

        This method analyzes the current query and cursor position to provide
        autocomplete suggestions for MongoDB document fields.
        """
        db = self.db_label or self.last_db_label
        collection = self.collection_name or self.last_collection
        # If collection is not set, try to extract from query input
        if not collection:
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
        """
        Show the suggestion popup with the given list of suggestions.

        Args:
            suggestions: List of field path suggestions.
        """
        self._suggestion_popup.clear()
        self._suggestion_popup.addItems(suggestions)
        cursor_rect = self.query_input.cursorRect()
        popup_pos = self.query_input.mapToGlobal(cursor_rect.bottomLeft())
        self._suggestion_popup.move(popup_pos)
        self._suggestion_popup.setCurrentRow(0)
        self._suggestion_popup.show()
        self._popup_shown = True

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        """
        Filter events for the query input field to provide custom behavior.

        Args:
            a0: The object that the event is directed to.
            a1: The event itself.

        Returns:
            True if the event was handled, False otherwise.
        """
        if a0 is not self.query_input:
            return super().eventFilter(a0, a1)
        if not isinstance(a1, QKeyEvent) or a1.type() != QEvent.Type.KeyPress:
            return super().eventFilter(a0, a1)

        key = a1.key()
        if key == Qt.Key.Key_F1:
            self._show_schema_suggestions()
            return True
        if not self._popup_shown:
            return super().eventFilter(a0, a1)

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
        return super().eventFilter(a0, a1)

    def _insert_suggestion(self, item: QListWidgetItem | None) -> None:
        """
        Insert the selected suggestion into the query input field.

        Args:
            item: The QListWidgetItem representing the selected suggestion.
        """
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
        """Hide the suggestion popup."""
        self._suggestion_popup.hide()
        self._popup_shown = False

    def open_query_builder(self) -> None:
        """Open the query builder dialog for visual query building."""
        schema_fields = self._get_schema_fields_for_query_builder()
        dialog = QueryBuilderDialog(schema_fields, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._process_query_builder_result(dialog)

    def _get_schema_fields_for_query_builder(self) -> list[str]:
        """Get schema fields for the query builder dialog."""
        if self.db_label and self.collection_name:
            schema_fields = self._load_schema_for_collection(
                self.db_label, self.collection_name
            )
        else:
            schema_fields = []

        # Ensure we have at least the _id field
        if not schema_fields:
            schema_fields = ["_id"]

        return schema_fields

    def _process_query_builder_result(self, dialog: QueryBuilderDialog) -> None:
        """Process the result from the query builder dialog."""
        built_filter = dialog.get_built_query()
        if not built_filter:
            return

        options = dialog.get_query_options()
        full_query = self._build_mongodb_query_string(built_filter, options)
        self.query_input.setText(full_query)

    def _build_mongodb_query_string(
        self, filter_query: str, options: dict[str, Any]
    ) -> str:
        """Build a complete MongoDB query string with filter and options."""
        query_parts = []

        # Start with the base find query
        collection_name = self.collection_name or "collection"
        query_parts.append(f"db.{collection_name}.find({filter_query})")

        # Add query options
        self._add_query_options_to_parts(query_parts, options)

        return "".join(query_parts)

    def _add_query_options_to_parts(
        self, query_parts: list[str], options: dict[str, Any]
    ) -> None:
        """Add sort, limit, and skip options to the query parts list."""
        if "sort" in options:
            sort_str = json.dumps(options["sort"])
            query_parts.append(f".sort({sort_str})")

        if "limit" in options:
            query_parts.append(f".limit({options['limit']})")

        if "skip" in options:
            query_parts.append(f".skip({options['skip']})")
