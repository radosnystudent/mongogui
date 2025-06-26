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
    QMenu,
    QMessageBox,
    QProxyStyle,
    QPushButton,
    QStyle,
    QStyleOption,
    QTableWidget,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.connection_widgets import ConnectionWidgetsMixin
from ui.query_panel import QueryPanelMixin
from ui.query_tab import QueryTabWidget
from ui.ui_utils import set_minimum_heights

NO_DB_CONNECTION_MSG = "No database connection"


class TreeProxyStyle(QProxyStyle):
    """Custom style proxy to control tree branch indicator appearance in PyQt6."""

    def __init__(self, style: QStyle | None = None) -> None:
        """Initialize with optional base style."""
        super().__init__(style)
        # Define a bright indicator color for maximum visibility
        # Use white for arrow indicators - clean and visible against dark background
        self.indicator_color = QColor("#FFFFFF")
        self.indicator_size = 4  # Smaller size to match Connection Manager window

    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption | None,
        painter: QPainter | None,
        widget: QWidget | None = None,
    ) -> None:
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

    def pixelMetric(
        self,
        metric: QStyle.PixelMetric,
        option: QStyleOption | None = None,
        widget: QWidget | None = None,
    ) -> int:
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
        self._table_row_docs: list[dict[str, Any]] = []
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
        # self._table_row_docs: list[dict[str, Any]] = []  # REMOVE this duplicate
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

            # Set up context menu for right-clicks
            self.collection_tree.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )
            self.collection_tree.customContextMenuRequested.connect(
                self.on_collection_tree_context_menu
            )

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

        # Start the application in maximized mode (fullscreen but with window decorations)
        self.showMaximized()

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
        self,
        collection_name: str | None = None,
        db_label: str | None = None,
        mongo_client: Any = None,
    ) -> None:
        # If mongo_client is explicitly provided, use it
        # Otherwise, try to get it from active_clients
        active_db_label = db_label

        if mongo_client is None:
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
        # Get the item data to extract the mongo_client and other information
        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not data:
            return

        # Extract mongo_client directly from the item data
        mongo_client = data.get("mongo_client")
        collection_name = data.get("name")
        db_name = data.get("db")

        # Use the parent item to get the db_label for display purposes
        parent_db_item = item.parent()
        db_label = parent_db_item.text(0) if parent_db_item else db_name

        # Pass both collection name and db_label to add_query_tab
        # along with the actual mongo_client instance
        self.add_query_tab(
            collection_name=collection_name,
            db_label=db_label,
            mongo_client=mongo_client,
        )

    def _handle_index_click(self, item: QTreeWidgetItem, item_name: str) -> None:
        """Handles clicks on index items in the collection tree."""
        coll_item = item.parent()
        if not coll_item:
            return

        db_item = coll_item.parent()
        if not db_item:
            return

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

    def on_collection_tree_context_menu(self, pos: Any) -> None:
        """Handle right-click context menu on collection tree items."""
        item = self.collection_tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole + 1)
        if not data:
            return

        menu = QMenu(self.collection_tree)
        viewport = self.collection_tree.viewport()

        # Store the current item for use in context menu actions
        self.current_context_item = item

        if data.get("type") == "collection":
            self._handle_collection_context_menu(menu, viewport, pos, data)
        elif data.get("type") == "index":
            self._handle_index_context_menu(menu, viewport, pos, data)

    def _handle_collection_context_menu(
        self, menu: QMenu, viewport: QWidget | None, pos: Any, data: dict
    ) -> None:
        """Handle context menu for collection items."""
        manage_indexes_action = menu.addAction("Manage indexes")
        schema_action = menu.addAction("Edit schema (JSON)")

        action = menu.exec(
            viewport.mapToGlobal(pos)
            if viewport is not None
            else self.collection_tree.mapToGlobal(pos)
        )

        if action == manage_indexes_action:
            self.show_index_dialog(data)
        elif action == schema_action:
            self.show_schema_editor_dialog(data)

    def _handle_index_context_menu(
        self, menu: QMenu, viewport: QWidget | None, pos: Any, data: dict
    ) -> None:
        """Handle context menu for index items."""
        edit_action = menu.addAction("Edit index")
        delete_action = menu.addAction("Delete index")

        action = menu.exec(
            viewport.mapToGlobal(pos)
            if viewport is not None
            else self.collection_tree.mapToGlobal(pos)
        )

        if action == edit_action:
            self.edit_index(data, self.current_context_item)
        elif action == delete_action:
            self.delete_index(data, self.current_context_item)

    def show_index_dialog(self, data: dict) -> None:
        """Show the index management dialog."""
        collection_name = data.get("name")
        # db_name not used in this method
        mongo_client = data.get("mongo_client")

        if not collection_name or not mongo_client:
            QMessageBox.warning(self, "Error", "Collection information is incomplete.")
            return

        from ui.index_dialog import IndexDialog

        # Get the indexes for the collection
        result = mongo_client.list_indexes(collection_name)
        indexes = result.unwrap() if result.is_ok() else []

        dialog = IndexDialog(indexes=indexes, parent=self)
        dialog.exec()

    def show_schema_editor_dialog(self, data: dict) -> None:
        """Show the schema editor dialog."""
        collection_name = data.get("name")
        db_name = data.get("db")

        if not collection_name or not db_name:
            QMessageBox.warning(self, "Error", "Collection information is incomplete.")
            return

        import os

        from ui.schema_editor_dialog import SchemaEditorDialog

        # Schema files are stored in the schemas directory with format db__collection.json
        schema_filename = f"{db_name}__{collection_name}.json"
        schema_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas"
        )
        schema_path = os.path.join(schema_dir, schema_filename)

        initial_schema = "{}"
        if os.path.exists(schema_path):
            try:
                with open(schema_path) as f:
                    initial_schema = f.read()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to read schema file: {e}")

        dialog = SchemaEditorDialog(parent=self, initial_schema=initial_schema)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schema_json = dialog.get_schema()
            if schema_json:
                # Create schemas directory if it doesn't exist
                os.makedirs(schema_dir, exist_ok=True)
                try:
                    with open(schema_path, "w") as f:
                        f.write(schema_json)
                    QMessageBox.information(
                        self, "Success", f"Schema saved for {collection_name}"
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to save schema: {e}")

    def edit_index(self, data: dict, item: QTreeWidgetItem) -> None:
        """Edit an existing index."""
        index = data.get("index")
        collection_name = data.get("collection")
        index_name = data.get("name")

        if not index or not collection_name or not index_name:
            QMessageBox.warning(self, "Error", "Index information is incomplete.")
            return

        # Get the parent item (collection) to access its data
        parent_item = item.parent()
        if not parent_item:
            QMessageBox.warning(self, "Error", "Cannot determine parent collection.")
            return

        collection_data = parent_item.data(0, Qt.ItemDataRole.UserRole + 1)
        # Unused variable but kept with comment to show intent
        _ = collection_data.get("db")
        mongo_client = collection_data.get("mongo_client")

        if not mongo_client:
            QMessageBox.warning(
                self, "Error", "MongoDB client not found for this collection."
            )
            return

        from ui.index_dialog import IndexDialog

        # Get the indexes for the collection
        result = mongo_client.list_indexes(collection_name)
        indexes = result.unwrap() if result.is_ok() else []

        dialog = IndexDialog(indexes=indexes, parent=self)
        dialog.exec()

    def delete_index(self, data: dict, item: QTreeWidgetItem) -> None:
        """Delete an index."""
        index_name = data.get("name")
        collection_name = data.get("collection")

        if not index_name or not collection_name:
            QMessageBox.warning(self, "Error", "Index information is incomplete.")
            return

        # Get the parent item (collection) to access its data
        parent_item = item.parent()
        if not parent_item:
            QMessageBox.warning(self, "Error", "Cannot determine parent collection.")
            return

        collection_data = parent_item.data(0, Qt.ItemDataRole.UserRole + 1)
        db_name = collection_data.get("db")  # Needed for refresh_collection_indexes
        mongo_client = collection_data.get("mongo_client")

        if not mongo_client:
            QMessageBox.warning(
                self, "Error", "MongoDB client not found for this collection."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the index '{index_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = mongo_client.drop_index(collection_name, index_name)
            if result is True:
                QMessageBox.information(
                    self, "Success", f"Index '{index_name}' deleted successfully."
                )
                # Refresh the collection's indexes
                self.refresh_collection_indexes(db_name, collection_name, mongo_client)
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete index: {result}")

    def refresh_collection_indexes(
        self, db_name: str, collection_name: str, mongo_client: Any
    ) -> None:
        """Refresh the indexes for a collection in the tree."""
        collection_item = self._find_collection_item(db_name, collection_name)
        if not collection_item:
            return

        # Clear existing indexes
        collection_item.takeChildren()

        # Add indexes for the collection
        self._add_indexes_to_collection_item(
            collection_item, collection_name, mongo_client
        )

    def _find_collection_item(
        self, db_name: str, collection_name: str
    ) -> QTreeWidgetItem | None:
        """Find a collection item in the tree by database and collection names."""
        for i in range(self.collection_tree.topLevelItemCount()):
            db_item = self.collection_tree.topLevelItem(i)
            if not db_item or db_item.text(0) != db_name:
                continue

            for j in range(db_item.childCount()):
                coll_item = db_item.child(j)
                if coll_item and coll_item.text(0) == collection_name:
                    return coll_item

        return None

    def _add_indexes_to_collection_item(
        self, collection_item: QTreeWidgetItem, collection_name: str, mongo_client: Any
    ) -> None:
        """Add index items to a collection item."""
        result = mongo_client.list_indexes(collection_name)
        if not result.is_ok():
            return

        indexes = result.unwrap()
        for index in indexes:
            index_item = self._create_index_item(index, collection_name)
            collection_item.addChild(index_item)
            # Keep index nodes collapsed by default
            index_item.setExpanded(False)

    def _create_index_item(self, index: dict, collection_name: str) -> QTreeWidgetItem:
        """Create a tree widget item for an index."""
        index_name = index.get("name", "unnamed")
        index_info = self._format_index_info(index_name, index)

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
        return index_item

    def _format_index_info(self, index_name: str, index: dict) -> str:
        """Format the index information for display."""
        index_info = index_name
        if "key" in index:
            # Format the key information
            key_info = [f"{k}: {v}" for k, v in index["key"].items()]
            index_info = f"{index_info} ({', '.join(key_info)})"
        return index_info

    def on_row_selected(self) -> None:
        """Handle table row selection."""
        pass  # Implement row selection handling if needed

    def open_connection_manager_window(self) -> None:
        """Open the connection manager window."""
        from ui.connection_manager_window import ConnectionManagerWindow

        dialog = ConnectionManagerWindow()
        dialog.exec()

    def add_database_collections(self, db_label: str, mongo_client: Any) -> None:
        """
        Add a top-level node for the database, with its collections as children.
        Override the mixin's method to set proper expansion state for database nodes.
        """
        # Add a top-level node for the database, with its collections as children
        db_item = QTreeWidgetItem([db_label])
        db_item.setData(
            0,
            Qt.ItemDataRole.UserRole + 1,
            {"type": "database", "db": db_label, "mongo_client": mongo_client},
        )
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
                        "db": db_label,
                        "mongo_client": mongo_client,
                    },
                )
                # Always add a dummy child for expand arrow
                dummy = QTreeWidgetItem([""])
                col_item.addChild(dummy)
                db_item.addChild(col_item)
                # Ensure collections are collapsed by default
                col_item.setExpanded(False)

            # Add the database item to the tree
            self.collection_tree.addTopLevelItem(db_item)

            # Ensure database nodes are expanded by default
            db_item.setExpanded(True)

        except Exception as e:
            print(f"Error adding database collections: {e}")

    def reload_collection_indexes_in_tree(
        self, col_item: QTreeWidgetItem | None
    ) -> None:
        """
        Reload the indexes for a collection in the tree.
        Override the mixin's method to ensure collections stay collapsed.
        """
        if col_item is None:
            return
        client = self._get_mongo_client_for_item(col_item)
        if not client:
            return
        # Remove all children
        while col_item.childCount() > 0:
            child = col_item.child(0)
            if child is not None:
                col_item.removeChild(child)
            else:
                break
        collection_name = col_item.text(0)
        indexes_result = client.list_indexes(collection_name)
        if indexes_result.is_ok():
            indexes = indexes_result.value or []
        else:
            QMessageBox.critical(
                self.collection_tree, "Error", str(indexes_result.error)
            )
            return
        try:
            if indexes:
                for idx in indexes:
                    idx_name = idx.get("name", "")
                    idx_item = QTreeWidgetItem([idx_name])
                    idx_item.setData(
                        0,
                        Qt.ItemDataRole.UserRole + 1,
                        {"type": "index", "collection": collection_name, "index": idx},
                    )
                    idx_item.setExpanded(False)  # Keep indexes collapsed by default
                    col_item.addChild(idx_item)
        except Exception as e:
            print(f"Error reloading collection indexes: {e}")

        # Always add a dummy node if no real index children
        if col_item.childCount() == 0:
            col_item.addChild(QTreeWidgetItem([""]))

        # Different from the mixin: DON'T expand the collection
        # if hasattr(col_item, "setExpanded"):
        #     col_item.setExpanded(True)  # Keep collections expanded by default

    def _get_mongo_client_for_item(self, item: QTreeWidgetItem) -> Any:
        """Helper method to get the mongo client from a tree item."""
        current: QTreeWidgetItem | None = item
        while current is not None:
            data = current.data(0, Qt.ItemDataRole.UserRole + 1)
            # Try to get mongo_client from collection node first, then parent (database)
            if data and "mongo_client" in data:
                return data.get("mongo_client")
            current = current.parent()
        return None
