"""
Enhanced Query Builder Dialog with both Find queries and Aggregation pipelines.
Combines the existing filter builder with the new aggregation pipeline builder.
"""

import json
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ui.aggregation_pipeline_builder import AggregationPipelineBuilder
from ui.query_template_manager import QueryTemplate, QueryTemplateManager
from ui.template_management_dialog import TemplateManagementDialog


class EnhancedQueryBuilderDialog(QDialog):
    """
    Enhanced Query Builder Dialog with support for both Find queries and Aggregation pipelines.
    """

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.built_query = ""
        self.query_type = "find"  # 'find' or 'aggregate'

        # Initialize template manager
        self.template_manager = QueryTemplateManager()

        self.setWindowTitle("MongoDB Query Builder")
        self.setModal(True)
        self.resize(900, 700)
        self.setMinimumSize(800, 600)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the main UI with tabs for different query types."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("MongoDB Query Builder")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ddd; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Build MongoDB queries visually using either Find queries with filters or Aggregation pipelines."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaa; font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(desc_label)

        # Tab widget for different query types
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #3a3a3a;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ddd;
                border: 1px solid #555;
                padding: 8px 16px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #4a6741;
                border-bottom: 1px solid #4a6741;
            }
            QTabBar::tab:hover {
                background-color: #505050;
            }
        """
        )

        # Find Query Tab
        self.find_tab = QWidget()
        self.find_builder = self._create_find_query_builder()
        find_layout = QVBoxLayout(self.find_tab)
        find_layout.setContentsMargins(10, 10, 10, 10)
        find_layout.addWidget(self.find_builder)

        self.tab_widget.addTab(self.find_tab, "🔍 Find Query")

        # Aggregation Pipeline Tab
        self.aggregate_tab = QWidget()
        self.pipeline_builder = AggregationPipelineBuilder(self.fields)
        aggregate_layout = QVBoxLayout(self.aggregate_tab)
        aggregate_layout.setContentsMargins(10, 10, 10, 10)
        aggregate_layout.addWidget(self.pipeline_builder)

        self.tab_widget.addTab(self.aggregate_tab, "🔧 Aggregation Pipeline")

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        layout.addWidget(self.tab_widget, stretch=1)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Template management buttons
        save_template_btn = QPushButton("💾 Save Template")
        save_template_btn.setToolTip("Save current query as a template")
        save_template_btn.clicked.connect(self._save_template)
        save_template_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a5a6a;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a6a7a;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(save_template_btn)

        load_template_btn = QPushButton("📂 Load Template")
        load_template_btn.setToolTip("Load a saved query template")
        load_template_btn.clicked.connect(self._load_template)
        load_template_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #5a4a6a;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6a5a7a;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(load_template_btn)

        manage_templates_btn = QPushButton("🗂️ Manage")
        manage_templates_btn.setToolTip("Manage saved templates")
        manage_templates_btn.clicked.connect(self._manage_templates)
        manage_templates_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6a5a4a;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7a6a5a;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(manage_templates_btn)

        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setToolTip("Clear the current query builder")
        clear_btn.clicked.connect(self._clear_current_builder)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #505050;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setToolTip("Cancel and close dialog")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #505050;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(cancel_btn)

        # Build Query button
        self.build_btn = QPushButton("Build Query")
        self.build_btn.setToolTip("Build the query and insert into main window")
        self.build_btn.clicked.connect(self._build_and_accept)
        self.build_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a6741;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a7751;
                border-color: #666;
            }
        """
        )
        button_layout.addWidget(self.build_btn)

        layout.addLayout(button_layout)

        # Set dialog style
        self.setStyleSheet(
            """
            QDialog {
                background-color: #3a3a3a;
                color: #ddd;
            }
        """
        )

    def _create_find_query_builder(self) -> QWidget:
        """Create the find query builder widget."""
        # Create a container widget to hold the find builder components
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a simplified version of the find query builder
        # We'll reuse the components from QueryBuilderDialog but integrate them here
        from PyQt6.QtWidgets import QComboBox, QLineEdit, QScrollArea

        from ui.query_builder_dialog import (
            ConditionGroup,
        )

        # Add Group button
        add_group_btn = QPushButton("+ Add Group")
        add_group_btn.setToolTip("Add a new condition group")
        add_group_btn.clicked.connect(self._add_find_group)
        add_group_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
                border-color: #666;
            }
        """
        )
        layout.addWidget(add_group_btn)

        # Scroll area for groups
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background-color: #2e2e2e;
                border: 2px solid #555;
                border-radius: 8px;
            }
        """
        )

        # Groups container
        self.find_groups_widget = QWidget()
        self.find_groups_layout = QVBoxLayout(self.find_groups_widget)
        self.find_groups_layout.setContentsMargins(10, 10, 10, 10)
        self.find_groups_layout.setSpacing(8)
        self.find_groups_layout.addStretch()

        scroll.setWidget(self.find_groups_widget)
        layout.addWidget(scroll, stretch=1)

        # Sort/Limit/Skip Controls
        controls_group = QWidget()
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        # Sort controls
        sort_container = QWidget()
        sort_layout = QHBoxLayout(sort_container)
        sort_layout.setContentsMargins(0, 0, 0, 0)

        sort_label = QLabel("Sort by:")
        sort_layout.addWidget(sort_label)

        self.sort_field_combo = QComboBox()
        self.sort_field_combo.setEditable(True)
        self.sort_field_combo.addItems([""] + self.fields)
        self.sort_field_combo.setToolTip("Select field to sort by (optional)")
        sort_layout.addWidget(self.sort_field_combo)

        self.sort_direction_combo = QComboBox()
        self.sort_direction_combo.addItems(["Ascending", "Descending"])
        self.sort_direction_combo.setToolTip("Sort direction")
        sort_layout.addWidget(self.sort_direction_combo)

        sort_layout.addStretch()
        controls_layout.addWidget(sort_container)

        # Limit/Skip controls
        limit_container = QWidget()
        limit_layout = QHBoxLayout(limit_container)
        limit_layout.setContentsMargins(0, 0, 0, 0)

        limit_label = QLabel("Limit:")
        limit_layout.addWidget(limit_label)

        self.limit_input = QLineEdit()
        self.limit_input.setPlaceholderText("Max documents (optional)")
        self.limit_input.setFixedWidth(100)
        self.limit_input.setToolTip("Maximum number of documents to return")
        limit_layout.addWidget(self.limit_input)

        skip_label = QLabel("Skip:")
        limit_layout.addWidget(skip_label)

        self.skip_input = QLineEdit()
        self.skip_input.setPlaceholderText("Skip documents (optional)")
        self.skip_input.setFixedWidth(100)
        self.skip_input.setToolTip("Number of documents to skip")
        limit_layout.addWidget(self.skip_input)

        limit_layout.addStretch()
        controls_layout.addWidget(limit_container)

        layout.addWidget(controls_group)

        # Initialize with one root group
        self.find_root_group: ConditionGroup | None = None
        self._create_find_root_group()

        return container

    def _create_find_root_group(self) -> None:
        """Create the initial root group for find queries."""
        from ui.query_builder_dialog import ConditionGroup

        self.find_root_group = ConditionGroup(self.fields)
        # Remove the remove button from root group
        remove_btn = self.find_root_group.findChild(QPushButton)
        if remove_btn and remove_btn.text() == "×":
            remove_btn.setVisible(False)

        self.find_groups_layout.insertWidget(0, self.find_root_group)

    def _add_find_group(self) -> None:
        """Add a new top-level group to find query builder."""
        from ui.query_builder_dialog import ConditionGroup, LogicalOperatorWidget

        # If we already have groups, add a logical operator first
        if self.find_groups_layout.count() > 1:  # > 1 because of the stretch
            operator = LogicalOperatorWidget()
            self.find_groups_layout.insertWidget(
                self.find_groups_layout.count() - 1, operator
            )

        # Add new group
        group = ConditionGroup(self.fields)
        group.removed.connect(lambda: self._remove_find_group(group))
        self.find_groups_layout.insertWidget(self.find_groups_layout.count() - 1, group)

        self.find_groups_widget.updateGeometry()

    def _remove_find_group(self, group: QWidget) -> None:
        """Remove a top-level group from find query builder."""
        # Don't remove if it's the only group
        if self.find_groups_layout.count() <= 2:  # 1 group + 1 stretch
            return

        self._remove_associated_operator_for_group(group)
        self._remove_group_widget(group)

    def _remove_associated_operator_for_group(self, target_group: QWidget) -> None:
        """Remove the logical operator associated with a group."""
        group_index = self._find_group_index_in_layout(target_group)
        if group_index > 0:
            prev_item = self.find_groups_layout.itemAt(group_index - 1)
            if prev_item:
                widget = prev_item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

    def _find_group_index_in_layout(self, target_group: QWidget) -> int:
        """Find the index of a group in the layout."""
        for i in range(self.find_groups_layout.count()):
            item = self.find_groups_layout.itemAt(i)
            if item and item.widget() == target_group:
                return i
        return -1

    def _remove_group_widget(self, group: QWidget) -> None:
        """Remove the group widget from the layout."""
        group.setParent(None)
        group.deleteLater()
        self.find_groups_widget.updateGeometry()

    def _on_tab_changed(self, index: int) -> None:
        """Handle tab change to update query type."""
        if index == 0:
            self.query_type = "find"
        elif index == 1:
            self.query_type = "aggregate"

    def _clear_current_builder(self) -> None:
        """Clear the currently active query builder."""
        if self.query_type == "find":
            self._clear_find_builder()
        elif self.query_type == "aggregate":
            self.pipeline_builder.clear_pipeline()

    def _clear_find_builder(self) -> None:
        """Clear the find query builder."""
        # Remove all groups except one
        while self.find_groups_layout.count() > 1:
            item = self.find_groups_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

        # Create a new root group
        self._create_find_root_group()

        # Clear sort/limit/skip fields
        self.sort_field_combo.setCurrentText("")
        self.limit_input.clear()
        self.skip_input.clear()

    def _build_and_accept(self) -> None:
        """Build the appropriate query type and accept the dialog."""
        try:
            if self.query_type == "find":
                self.built_query = self._build_find_query()
            elif self.query_type == "aggregate":
                self.built_query = self._build_aggregate_query()

            if self.built_query:
                self.accept()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Query Build Error", f"Error building query: {str(e)}"
            )

    def _build_find_query(self) -> str:
        """Build a find query from the filter builder."""
        if not self.find_root_group:
            return "{}"

        all_groups = self._collect_all_find_groups()
        if not all_groups:
            return "{}"

        return self._build_filter_query_from_groups(all_groups)

    def _collect_all_find_groups(self) -> list[dict[str, Any]]:
        """Collect all valid group conditions from find builder."""
        all_groups = []

        # Add root group conditions
        if self.find_root_group:
            root_conditions = self.find_root_group.get_conditions()
            if root_conditions:
                all_groups.append(root_conditions)

        # Add other top-level groups
        self._add_additional_find_groups(all_groups)
        return all_groups

    def _add_additional_find_groups(self, all_groups: list[dict[str, Any]]) -> None:
        """Add additional top-level groups to the collection."""

        for i in range(self.find_groups_layout.count()):
            item = self.find_groups_layout.itemAt(i)
            if not item:
                continue

            widget = item.widget()
            if self._is_valid_additional_group(widget):
                # We've validated it's a ConditionGroup via isinstance check
                group_conditions = widget.get_conditions()  # type: ignore[union-attr]
                if group_conditions:
                    all_groups.append(group_conditions)

    def _is_valid_additional_group(self, widget: QWidget | None) -> bool:
        """Check if widget is a valid additional condition group."""
        from ui.query_builder_dialog import ConditionGroup

        return bool(
            widget
            and isinstance(widget, ConditionGroup)
            and widget != self.find_root_group
        )

    def _build_filter_query_from_groups(self, all_groups: list[dict[str, Any]]) -> str:
        """Build the final filter query from collected groups."""
        if len(all_groups) == 1:
            return json.dumps(all_groups[0])

        return self._build_multi_group_query(all_groups)

    def _build_multi_group_query(self, all_groups: list[dict[str, Any]]) -> str:
        """Build query for multiple groups with logical operators."""
        operators = self._find_logical_operators_in_layout()

        if operators:
            query = {operators[0]: all_groups}
        else:
            query = {"$and": all_groups}

        return json.dumps(query)

    def _find_logical_operators_in_layout(self) -> list[str]:
        """Find all logical operators in the find query layout."""
        from ui.query_builder_dialog import LogicalOperatorWidget

        operators = []
        for i in range(self.find_groups_layout.count()):
            item = self.find_groups_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and isinstance(widget, LogicalOperatorWidget):
                    operators.append(widget.get_operator())
        return operators

    def _build_aggregate_query(self) -> str:
        """Build an aggregation pipeline query."""
        pipeline = self.pipeline_builder.get_pipeline()
        if not pipeline:
            return "[]"
        return json.dumps(pipeline)

    def get_built_query(self) -> str:
        """Get the built query string."""
        return self.built_query

    def get_query_type(self) -> str:
        """Get the type of query ('find' or 'aggregate')."""
        return self.query_type

    def get_query_options(self) -> dict[str, Any]:
        """Get additional query options (only for find queries)."""
        if self.query_type != "find":
            return {}

        options: dict[str, Any] = {}

        try:
            self._add_sort_option(options)
            self._add_limit_option(options)
            self._add_skip_option(options)
        except Exception:
            pass

        return options

    def _add_sort_option(self, options: dict[str, Any]) -> None:
        """Add sort option to query options if valid."""
        from ui.query_builder_dialog import validate_field_name

        sort_field = self.sort_field_combo.currentText().strip()
        if sort_field and validate_field_name(sort_field):
            sort_direction = (
                1 if self.sort_direction_combo.currentText() == "Ascending" else -1
            )
            options["sort"] = {sort_field: sort_direction}

    def _add_limit_option(self, options: dict[str, Any]) -> None:
        """Add limit option to query options if valid."""
        from ui.query_builder_dialog import MAX_LIMIT_VALUE

        limit_text = self.limit_input.text().strip()
        if not limit_text:
            return

        try:
            limit_value = int(limit_text)
            if 0 < limit_value <= MAX_LIMIT_VALUE:
                options["limit"] = limit_value
        except (ValueError, OverflowError):
            pass

    def _add_skip_option(self, options: dict[str, Any]) -> None:
        """Add skip option to query options if valid."""
        from ui.query_builder_dialog import MAX_SKIP_VALUE

        skip_text = self.skip_input.text().strip()
        if not skip_text:
            return

        try:
            skip_value = int(skip_text)
            if 0 <= skip_value <= MAX_SKIP_VALUE:
                options["skip"] = skip_value
        except (ValueError, OverflowError):
            pass

    def _save_template(self) -> None:
        """Save the current query as a template."""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        # Get current query data
        if self.query_type == "find":
            query_data = {
                "type": "find",
                "filters": self._get_filter_data(),
                "options": self.get_query_options(),
            }
        else:
            query_data = {
                "type": "aggregate",
                "pipeline": self.pipeline_builder.get_pipeline(),
            }

        # If no data, show message
        if not query_data.get("filters") and not query_data.get("pipeline"):
            QMessageBox.information(
                self,
                "No Query Data",
                "Please build a query before saving it as a template.",
            )
            return

        # Get template name from user
        name, ok = QInputDialog.getText(
            self,
            "Save Template",
            "Enter a name for this template:",
            text=f"{self.query_type}_template",
        )

        if not ok or not name.strip():
            return

        # Get description from user
        description, ok = QInputDialog.getText(
            self,
            "Template Description",
            "Enter a description for this template (optional):",
        )

        if not ok:
            return

        try:
            success = self.template_manager.save_template(
                name=name.strip(),
                query_type=self.query_type,
                query_data=query_data,
                description=description.strip() or "",
            )
            if success:
                QMessageBox.information(
                    self,
                    "Template Saved",
                    f"Template '{name.strip()}' has been saved successfully.",
                )
            else:
                QMessageBox.warning(self, "Save Error", "Failed to save template.")
        except Exception as e:
            QMessageBox.warning(
                self, "Save Error", f"Failed to save template: {str(e)}"
            )

    def _load_template(self) -> None:
        """Load a saved query template."""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox

        templates = self.template_manager.get_all_templates()
        if not templates:
            QMessageBox.information(self, "No Templates", "No saved templates found.")
            return

        # Create list of template names with descriptions
        template_items = []
        for template in templates:
            if template.description:
                template_items.append(f"{template.name} - {template.description}")
            else:
                template_items.append(template.name)

        # Show selection dialog
        item, ok = QInputDialog.getItem(
            self,
            "Load Template",
            "Select a template to load:",
            template_items,
            editable=False,
        )

        if not ok:
            return

        # Extract template name (before the " - " if present)
        template_name = item.split(" - ")[0]

        try:
            template = self.template_manager.load_template(template_name)
            if template is None:
                QMessageBox.warning(
                    self, "Load Error", f"Template '{template_name}' not found."
                )
                return

            # Load the template based on type
            if template.query_type == "find":
                self._load_find_template(template)
            elif template.query_type == "aggregate":
                self._load_aggregate_template(template)

            QMessageBox.information(
                self,
                "Template Loaded",
                f"Template '{template_name}' has been loaded successfully.",
            )

        except Exception as e:
            QMessageBox.warning(
                self, "Load Error", f"Failed to load template: {str(e)}"
            )

    def _manage_templates(self) -> None:
        """Open the template management dialog."""
        try:
            dialog = TemplateManagementDialog(self.template_manager, self)
            dialog.exec()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Error", f"Failed to open template manager: {str(e)}"
            )

    def _get_filter_data(self) -> list[dict[str, Any]]:
        """Get current filter data from the find query builder."""
        # For now, return empty list since we need complex integration with the filter builder
        # This can be enhanced later to extract actual filter data
        return []

    def _load_find_template(self, template: QueryTemplate) -> None:
        """Load a find query template."""
        # Switch to find tab
        self.tab_widget.setCurrentIndex(0)
        self.query_type = "find"

        # Clear current filters
        self._clear_current_builder()

        # Load filters
        filters = template.query_data.get("filters", [])
        for filter_data in filters:
            self._add_filter_from_data(filter_data)

        # Load options
        options = template.query_data.get("options", {})
        if "sort" in options:
            sort_data = options["sort"]
            if isinstance(sort_data, dict):
                for field, direction in sort_data.items():
                    self.sort_field_combo.setCurrentText(field)
                    self.sort_direction_combo.setCurrentText(
                        "Ascending" if direction == 1 else "Descending"
                    )
                    break

        if "limit" in options:
            self.limit_input.setText(str(options["limit"]))

        if "skip" in options:
            self.skip_input.setText(str(options["skip"]))

    def _load_aggregate_template(self, template: QueryTemplate) -> None:
        """Load an aggregation pipeline template."""
        # Switch to aggregate tab
        self.tab_widget.setCurrentIndex(1)
        self.query_type = "aggregate"

        # Clear current pipeline
        self.pipeline_builder.clear_pipeline()

        # Load pipeline stages
        pipeline = template.query_data.get("pipeline", [])
        for stage in pipeline:
            # For now, we'll add stages as raw JSON since add_stage_from_data doesn't exist
            pass

    def _add_filter_from_data(self, filter_data: dict[str, Any]) -> None:
        """Add a filter widget from saved data."""
        # This would need to be implemented based on the filter widget structure
        # For now, we'll skip this complex reconstruction
        pass
