"""
Main application window for the MongoDB GUI.
"""

# This module defines the MainWindow class and related UI logic for the main application window.
# All UI logic is separated from business logic and database operations.

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProxyStyle,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from db.mongo_client import MongoClientWrapper
from ui.connection_manager_window import ConnectionManagerWindow
from ui.connection_widgets import ConnectionWidgetsMixin
from ui.edit_document_dialog import EditDocumentDialog
from ui.query_panel import QueryPanelMixin
from ui.query_tab import QueryTabWidget
from ui.ui_utils import set_minimum_heights
from utils.error_handling import handle_exception

NO_DB_CONNECTION_MSG = "No database connection"


class TreeProxyStyle(QProxyStyle):
    """Custom style proxy to control tree branch indicator appearance in PyQt6."""

    def __init__(self, style=None):
        """Initialize with optional base style."""
        super().__init__(style)
        # Define a bright indicator color for maximum visibility
        # Use white for arrow indicators - clean and visible against dark background
        self.indicator_color = QColor("#FFFFFF")
        self.indicator_size = 4  # Smaller size to match Connection Manager window

    def drawPrimitive(self, element, option, painter, widget=None):
        """Draw custom branch indicators for tree items."""
        # Handle tree branch indicators
        if element == QStyle.PrimitiveElement.PE_IndicatorBranch:
            if option is not None and painter is not None:
                rect = option.rect
                state = option.state

                # Check if this item has children
                has_children = bool(state & QStyle.StateFlag.State_Children)

                if has_children:
                    # Save painter state
                    painter.save()
                    painter.setRenderHint(
                        QPainter.RenderHint.Antialiasing
                    )  # Set up a thinner pen for smaller arrows
                    painter.setPen(QPen(self.indicator_color, 1.0))

                    # Calculate center position
                    center_x = rect.x() + rect.width() // 2
                    center_y = rect.y() + rect.height() // 2
                    size = self.indicator_size

                    # Check if the node is expanded or collapsed
                    is_open = bool(state & QStyle.StateFlag.State_Open)

                    # Draw arrow based on expanded/collapsed state
                    if is_open:
                        # Draw downward-pointing arrow (V shape)
                        # Don't use fill for arrow shapes
                        painter.setBrush(Qt.BrushStyle.NoBrush)

                        # Make the downward arrow a bit wider than tall for better proportions
                        painter.drawLine(
                            center_x - size - 1,
                            center_y - size // 2,
                            center_x,
                            center_y + size,
                        )  # Left diagonal
                        painter.drawLine(
                            center_x,
                            center_y + size,
                            center_x + size + 1,
                            center_y - size // 2,
                        )  # Right diagonal

                    else:
                        # Draw rightward-pointing arrow (> shape)
                        # Don't use fill for arrow shapes
                        painter.setBrush(Qt.BrushStyle.NoBrush)

                        # Make the right arrow a bit taller than wide for better proportions
                        painter.drawLine(
                            center_x - size // 2,
                            center_y - size - 1,
                            center_x + size,
                            center_y,
                        )  # Top diagonal
                        painter.drawLine(
                            center_x - size // 2,
                            center_y + size + 1,
                            center_x + size,
                            center_y,
                        )  # Bottom diagonal

                    # Restore painter state
                    painter.restore()
                    return  # Void return

        # For other elements, use the base style
        super().drawPrimitive(element, option, painter, widget)

    def pixelMetric(self, metric, option=None, widget=None):
        """Adjust indicator sizes for better visibility."""
        if metric == QStyle.PixelMetric.PM_TreeViewIndentation:
            # Use smaller indentation to match Connection Manager style
            return 20
        return super().pixelMetric(metric, option, widget)

    # No additional overrides needed


class MainWindow(QMainWindow, ConnectionWidgetsMixin):
    """Main application window for the MongoDB GUI."""

    def __init__(self) -> None:
        """Initialize the main window and UI components."""
        QMainWindow.__init__(self)  # Initialize main window first
        ConnectionWidgetsMixin.__init__(self)  # Initialize mixin after

        # We'll configure styles in _configure_collection_tree instead

        # Initialize state
        self.current_page = 0
        self.page_size = 10
        self.mongo_client = None
        self.active_clients = {}
        self._table_row_docs = []
        self.prev_btn = None
        self.next_btn = None
        self.page_label = None
        self.result_count_label = None
        self.db_info_label = None
        self.query_input = None

        # Create and configure the collection tree with custom style
        self.collection_tree = QTreeWidget()

        # Create a proper style object for the entire application once
        # This ensures consistent styling across the application
        from PyQt6.QtWidgets import QApplication

        base_style = QApplication.style()
        self.tree_style = TreeProxyStyle(base_style)

        # Apply the style to the collection tree
        self.collection_tree.setStyle(self.tree_style)

        # Configure the collection tree
        self._configure_collection_tree()

        # Initialize connection manager early
        from db.connection_manager import ConnectionManager

        self.conn_manager = ConnectionManager()

        self.setWindowTitle("MongoDB GUI")
        self.setMinimumSize(800, 600)

        # Initialize required attributes
        self.results: list[dict[str, Any]] = []
        self.last_query = ""
        self.last_query_type = ""
        self.last_collection: str = ""
        self.current_page = 0
        self.page_size = 10
        self.mongo_client = None
        self.active_clients = {}
        self._table_row_docs = []
        self.prev_btn = None
        self.next_btn = None
        self.page_label = None
        self.result_count_label = None
        self.db_info_label = None
        self.query_input = None

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Changed to horizontal layout

        # Initialize widgets
        self.data_table = QTableWidget()
        self.json_tree = QTreeWidget()
        self.query_tabs = QTabWidget()
        self.query_tabs.setTabsClosable(True)
        self.query_tabs.tabCloseRequested.connect(self._close_query_tab)
        self.query_tabs.setMovable(True)

        # Create left panel for database/collection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # Add Connections button
        connections_button = QPushButton("Connections")
        connections_button.clicked.connect(self.open_connection_manager_window)
        connections_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
        """
        )
        # Button is now properly styled

        left_layout.addWidget(connections_button)
        left_layout.addSpacing(
            10
        )  # Increased spacing between button and section label for better separation

        # Create a label for the database/collection section
        db_section_label = QLabel("Database/Collection")
        db_section_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-weight: bold;
                padding: 5px;
                background-color: #3d3d3d;
                border-radius: 3px;
            }
        """
        )
        left_layout.addWidget(db_section_label)
        left_layout.addSpacing(10)  # Add spacing after the section label

        # Add collection tree with proper configuration
        if hasattr(self, "collection_tree"):
            # Configure the tree widget
            self.collection_tree.setHeaderHidden(True)  # Hide the header
            self.collection_tree.setColumnCount(1)
            self.collection_tree.setMinimumHeight(200)
            self.collection_tree.setIndentation(
                20
            )  # Set smaller indentation to match Connection Manager
            self.collection_tree.setMinimumWidth(250)  # Set minimum width for tree
            self.collection_tree.setAlternatingRowColors(False)
            self.collection_tree.setAnimated(True)
            self.collection_tree.setExpandsOnDoubleClick(True)

            # Configure tree view decorations
            self.collection_tree.setRootIsDecorated(True)
            self.collection_tree.setItemsExpandable(True)
            self.collection_tree.setAutoExpandDelay(-1)  # Disable auto-expand
            self.collection_tree.setUniformRowHeights(True)

            # Set custom tree indicators
            from PyQt6.QtCore import QSize

            self.collection_tree.setIconSize(QSize(16, 16))

            left_layout.addWidget(self.collection_tree)

        # Add left panel to main layout
        main_layout.addWidget(left_panel)

        # Add spacing between left and right panels (the vertical divider)
        main_layout.addSpacing(10)  # Add moderate spacing between panels

        # Create right panel for query
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Add a spacer at the top to match the Connections button height in the left panel
        invisible_spacer = QWidget()
        invisible_spacer.setFixedHeight(connections_button.sizeHint().height())
        invisible_spacer.setVisible(True)  # Make it take up space but be invisible
        right_layout.addWidget(invisible_spacer)
        right_layout.addSpacing(
            10
        )  # Increased spacing between sections for better visual separation

        # Add query section label
        query_label = QLabel("Query")
        query_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-weight: bold;
                padding: 5px;
                background-color: #3d3d3d;
                border-radius: 3px;
            }
        """
        )
        right_layout.addWidget(query_label)
        right_layout.addSpacing(10)  # Add spacing after the section label

        # Add query tabs
        right_layout.addWidget(self.query_tabs)

        # Add right panel to main layout
        main_layout.addWidget(right_panel)

        # Set stretch factors to maintain proportions (30% left, 0% spacing, 70% right)
        main_layout.setStretch(0, 30)  # Left panel
        main_layout.setStretch(1, 0)  # Spacing (should not stretch)
        main_layout.setStretch(2, 70)  # Right panel

        # Set dark theme style only, indicators are handled by TreeProxyStyle
        # Don't add duplicate stylesheet here, it's already set in _configure_collection_tree
        # And don't add the tree widget twice - it's already added above

        # Initialize connection manager and panels
        from db.connection_manager import (
            ConnectionManager,  # Local import to avoid circular dependencies
        )

        self.conn_manager = ConnectionManager()
        self.query_panel = QueryPanelMixin()

        # Complete setup
        self.setup_data_table()
        self.setup_ui()

        # Connect tree click signals
        self.collection_tree.itemClicked.connect(self.on_collection_tree_item_clicked)

    def _configure_collection_tree(self) -> None:
        """Configure the collection tree widget with proper settings and styling."""
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QPalette

        # Basic tree configuration - essential settings first
        self.collection_tree.setColumnCount(1)
        self.collection_tree.setHeaderHidden(True)
        self.collection_tree.setMinimumHeight(200)
        self.collection_tree.setMinimumWidth(250)

        # Configure tree behavior
        self.collection_tree.setAnimated(True)
        self.collection_tree.setExpandsOnDoubleClick(True)

        # These settings are critical for showing branch indicators
        self.collection_tree.setRootIsDecorated(True)  # Show decorations at root level
        self.collection_tree.setItemsExpandable(True)  # Allow items to be expanded

        # Ensure all tree items are collapsed by default when added to the tree
        self.collection_tree.setAutoExpandDelay(-1)  # Disable auto-expand

        # Important visual settings for indicators
        self.collection_tree.setIndentation(
            20
        )  # Smaller indentation to match Connection Manager style
        self.collection_tree.setUniformRowHeights(True)  # Consistent row heights

        # Set icon size explicitly - helps with branch indicators
        self.collection_tree.setIconSize(QSize(16, 16))

        # Set dark theme colors via palette
        palette = self.collection_tree.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#2d2d2d"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#3d3d3d"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        self.collection_tree.setPalette(palette)

        # Very minimal stylesheet that won't interfere with branch indicators
        # The key is to avoid styling ::branch or other elements that affect indicators
        self.collection_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            QTreeWidget::item {
                color: #ffffff;
                padding: 2px;
            }
            QTreeWidget::item:selected {
                background-color: #3d3d3d;
            }
        """
        )

    def setup_data_table(self) -> None:
        """Set up the data table widget."""
        self.data_table = QTableWidget()
        self.data_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.data_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
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
            self.collection_tree.setCurrentItem(item)
        else:
            self.collection_tree.clearSelection()

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
        self.data_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
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
        """Connect to a database."""
        try:
            conn_data = self.conn_manager.get_connection_by_name(connection_name)
            if conn_data:
                # Create MongoDB client wrapper
                mongo_client = MongoClientWrapper()

                # Get the database name from connection data
                database = conn_data.get("database", "admin")

                if mongo_client.connect(
                    ip=conn_data.get("host", "localhost"),
                    port=conn_data.get("port", 27017),
                    db=database,  # Use the actual database name
                    login=conn_data.get("username"),
                    password=conn_data.get("password"),
                    tls=False,
                ):
                    self.mongo_client = mongo_client
                    # Store client in active clients dictionary
                    self.active_clients[connection_name] = mongo_client

                    # Add the database node first
                    db_item = QTreeWidgetItem([database])
                    db_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole + 1,
                        {
                            "type": "database",
                            "name": database,
                            "mongo_client": mongo_client,
                        },
                    )
                    self.collection_tree.addTopLevelItem(db_item)

                    # Then load its collections
                    try:
                        collections = mongo_client.list_collections()
                        collections = sorted(collections)
                        for collection_name in collections:
                            col_item = QTreeWidgetItem([collection_name])
                            col_item.setData(
                                0,
                                Qt.ItemDataRole.UserRole + 1,
                                {
                                    "type": "collection",
                                    "name": collection_name,
                                    "db": database,
                                    "mongo_client": mongo_client,
                                },
                            )
                            db_item.addChild(col_item)

                            # Add indexes for the collection
                            result = mongo_client.list_indexes(collection_name)
                            if result.is_ok():
                                indexes = result.unwrap()
                                for index in indexes:
                                    index_name = index.get("name", "unnamed")
                                    index_info = index_name
                                    if "key" in index:
                                        # Format the key information
                                        key_info = [
                                            f"{k}: {v}" for k, v in index["key"].items()
                                        ]
                                        index_info = (
                                            f"{index_info} ({', '.join(key_info)})"
                                        )

                                    index_item = QTreeWidgetItem([index_info])
                                    index_item.setData(
                                        0,
                                        Qt.ItemDataRole.UserRole + 1,
                                        {
                                            "type": "index",
                                            "name": index_name,
                                            "collection": collection_name,
                                            "index": index,
                                        },
                                    )
                                    # Set a slightly different background for index items
                                    col_item.addChild(index_item)
                                    # Keep index nodes collapsed by default
                                    index_item.setExpanded(False)

                        # Expand database nodes to show collections, but keep collection nodes collapsed
                        db_item.setExpanded(True)
                        for i in range(db_item.childCount()):
                            child = db_item.child(i)
                            if child:
                                child.setExpanded(False)

                    except Exception as e:
                        handle_exception(e, self)
                else:
                    raise Exception("Failed to connect to MongoDB")
        except Exception as e:
            handle_exception(e, self)

    def on_row_selected(self) -> None:
        """Handle table row selection."""
        pass  # Implement row selection handling if needed


# We're now using TreeProxyStyle for drawing indicators
# Instead of the event filter approach
