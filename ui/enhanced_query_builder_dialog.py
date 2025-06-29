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

    # Constants for dialog titles
    LOAD_ERROR_TITLE = "Load Error"
    SAVE_ERROR_TITLE = "Save Error"
    TEMPLATE_LOADED_TITLE = "Template Loaded"
    TEMPLATE_SAVED_TITLE = "Template Saved"

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

        self._add_header_components(layout)
        self._setup_tab_widget(layout)
        self._add_action_buttons(layout)
        self._apply_dialog_styling()

    def _add_header_components(self, layout: QVBoxLayout) -> None:
        """Add title and description to the dialog."""
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

    def _setup_tab_widget(self, layout: QVBoxLayout) -> None:
        """Setup the main tab widget with Find and Aggregation tabs."""
        self.tab_widget = QTabWidget()
        self._apply_tab_styling()
        self._create_tabs()

        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget, stretch=1)

    def _apply_tab_styling(self) -> None:
        """Apply styling to the tab widget."""
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

    def _create_tabs(self) -> None:
        """Create and add the Find Query and Aggregation tabs."""
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

    def _add_action_buttons(self, layout: QVBoxLayout) -> None:
        """Add the action buttons at the bottom of the dialog."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self._add_template_buttons(button_layout)
        self._add_utility_buttons(button_layout)
        self._add_main_action_buttons(button_layout)

        layout.addLayout(button_layout)

    def _add_template_buttons(self, button_layout: QHBoxLayout) -> None:
        """Add template management buttons."""
        save_template_btn = self._create_styled_button(
            "💾 Save Template",
            "Save current query as a template",
            self._save_template,
            "#4a5a6a",
            "#5a6a7a",
        )
        button_layout.addWidget(save_template_btn)

        load_template_btn = self._create_styled_button(
            "📂 Load Template",
            "Load a saved query template",
            self._load_template,
            "#5a4a6a",
            "#6a5a7a",
        )
        button_layout.addWidget(load_template_btn)

        manage_templates_btn = self._create_styled_button(
            "🗂️ Manage",
            "Manage saved templates",
            self._manage_templates,
            "#6a5a4a",
            "#7a6a5a",
        )
        button_layout.addWidget(manage_templates_btn)

    def _add_utility_buttons(self, button_layout: QHBoxLayout) -> None:
        """Add utility buttons like Clear."""
        clear_btn = self._create_styled_button(
            "Clear",
            "Clear the current query builder",
            self._clear_current_builder,
            "#505050",
            "#606060",
        )
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()

    def _add_main_action_buttons(self, button_layout: QHBoxLayout) -> None:
        """Add the main action buttons (Cancel, Build Query)."""
        cancel_btn = self._create_styled_button(
            "Cancel", "Cancel and close dialog", self.reject, "#505050", "#606060"
        )
        button_layout.addWidget(cancel_btn)

        self.build_btn = self._create_styled_button(
            "Build Query",
            "Build the query and insert into main window",
            self._build_and_accept,
            "#4a6741",
            "#5a7751",
        )
        button_layout.addWidget(self.build_btn)

    def _create_styled_button(
        self, text: str, tooltip: str, callback: Any, bg_color: str, hover_color: str
    ) -> QPushButton:
        """Create a styled button with consistent appearance."""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {bg_color};
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border-color: #666;
            }}
        """
        )
        return button

    def _apply_dialog_styling(self) -> None:
        """Apply overall dialog styling."""
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
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self._add_find_group_button(layout)
        self._setup_find_scroll_area(layout)
        self._add_find_controls(layout)
        self._initialize_find_root_group()

        return container

    def _add_find_group_button(self, layout: QVBoxLayout) -> None:
        """Add the 'Add Group' button to the find builder."""
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

    def _setup_find_scroll_area(self, layout: QVBoxLayout) -> None:
        """Setup the scroll area for condition groups."""
        from PyQt6.QtWidgets import QScrollArea

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

    def _add_find_controls(self, layout: QVBoxLayout) -> None:
        """Add sort, limit, and skip controls to the find builder."""
        controls_group = QWidget()
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self._add_sort_controls(controls_layout)
        self._add_limit_skip_controls(controls_layout)

        layout.addWidget(controls_group)

    def _add_sort_controls(self, controls_layout: QVBoxLayout) -> None:
        """Add sort controls to the find builder."""
        from PyQt6.QtWidgets import QComboBox

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

    def _add_limit_skip_controls(self, controls_layout: QVBoxLayout) -> None:
        """Add limit and skip controls to the find builder."""
        from PyQt6.QtWidgets import QLineEdit

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

    def _initialize_find_root_group(self) -> None:
        """Initialize the find builder with the root condition group."""
        from ui.query_builder_dialog import ConditionGroup

        self.find_root_group: ConditionGroup | None = None
        self._create_find_root_group()

    def _create_find_root_group(self) -> None:
        """Create the initial root group for find queries."""
        from ui.query_builder_dialog import ConditionGroup

        self.find_root_group = ConditionGroup(self.fields)
        # Remove the remove button from root group
        if self.find_root_group:
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

        # Clear any initial conditions that may have been automatically created
        if self.find_root_group and hasattr(self.find_root_group, "conditions"):
            # Remove all existing conditions from the root group
            for condition in self.find_root_group.conditions[
                :
            ]:  # Make a copy to iterate safely
                if hasattr(condition, "setParent"):
                    condition.setParent(None)
                    condition.deleteLater()
            self.find_root_group.conditions.clear()

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

        # Get current query data by building it on-demand
        try:
            if self.query_type == "find":
                # Build the query data from current filter state
                query_data = {
                    "type": "find",
                    "filters": self._extract_current_filter_data(),
                    "options": self.get_query_options(),
                }
                # Check if we have meaningful data
                has_data = bool(query_data.get("filters")) or bool(
                    query_data.get("options")
                )
            else:
                # For aggregation, get the pipeline
                pipeline = self.pipeline_builder.get_pipeline()
                query_data = {
                    "type": "aggregate",
                    "pipeline": pipeline,
                }
                has_data = bool(pipeline)

            # If no meaningful data, show message
            if not has_data:
                QMessageBox.information(
                    self,
                    "No Query Data",
                    "Please add some conditions or pipeline stages before saving as a template.",
                )
                return

        except Exception as e:
            QMessageBox.warning(
                self,
                self.SAVE_ERROR_TITLE,
                f"Error extracting query data: {str(e)}",
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
                    self.TEMPLATE_SAVED_TITLE,
                    f"Template '{name.strip()}' has been saved successfully.",
                )
            else:
                QMessageBox.warning(
                    self, self.SAVE_ERROR_TITLE, "Failed to save template."
                )
        except Exception as e:
            QMessageBox.warning(
                self, self.SAVE_ERROR_TITLE, f"Failed to save template: {str(e)}"
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
            maybe_template = self.template_manager.load_template(template_name)
            if maybe_template is None:
                QMessageBox.warning(
                    self,
                    self.LOAD_ERROR_TITLE,
                    f"Template '{template_name}' not found.",
                )
                return

            # Load the template based on type
            # At this point, template is guaranteed to be non-None
            template = maybe_template
            if template.query_type == "find":
                self._load_find_template(template)
            elif template.query_type == "aggregate":
                self._load_aggregate_template(template)
            else:
                QMessageBox.warning(
                    self,
                    self.LOAD_ERROR_TITLE,
                    f"Unknown query type: {template.query_type}",
                )
                return

            QMessageBox.information(
                self,
                self.TEMPLATE_LOADED_TITLE,
                f"Template '{template_name}' has been loaded successfully.",
            )

        except Exception as e:
            QMessageBox.warning(
                self, self.LOAD_ERROR_TITLE, f"Failed to load template: {str(e)}"
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
        return self._extract_current_filter_data()

    def _extract_current_filter_data(self) -> list[dict[str, Any]]:
        """Extract current filter data from the find query builder UI components."""
        if not self.find_root_group:
            return []

        try:
            # Extract UI-format data instead of MongoDB format for better template restoration
            filter_data = []

            # Get data from root group
            root_data = self._extract_group_ui_data(self.find_root_group)
            if root_data:
                filter_data.extend(root_data)

            # Get data from additional groups
            for i in range(self.find_groups_layout.count()):
                item = self.find_groups_layout.itemAt(i)
                if not item:
                    continue

                widget = item.widget()
                if self._is_valid_additional_group(widget):
                    group_data = self._extract_group_ui_data(widget)
                    if group_data:
                        filter_data.extend(group_data)

            return filter_data
        except Exception as e:
            print(f"Warning: Could not extract filter data: {e}")
            return []

    def _extract_group_ui_data(self, group: Any) -> list[dict[str, Any]]:
        """Extract UI format data from a condition group."""
        if not hasattr(group, "conditions"):
            return []

        ui_data = []
        for condition in group.conditions:
            if (
                hasattr(condition, "field_combo")
                and hasattr(condition, "operator_combo")
                and hasattr(condition, "value_input")
            ):
                # This is a ConditionWidget, extract UI data
                field = condition.field_combo.currentText().strip()
                operator = condition.operator_combo.currentText()
                value = condition.value_input.text().strip()

                if field and operator:
                    ui_data.append(
                        {"field": field, "operator": operator, "value": value}
                    )

        return ui_data

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

        # If we have stages to load, replace the default stage and add the rest
        if pipeline:
            # Set the first stage if it exists
            if len(pipeline) > 0 and self.pipeline_builder.stages:
                first_stage = pipeline[0]
                self._configure_stage_from_data(
                    self.pipeline_builder.stages[0], first_stage
                )

            # Add remaining stages
            for stage_data in pipeline[1:]:
                self.pipeline_builder.add_stage()
                if self.pipeline_builder.stages:
                    last_stage = self.pipeline_builder.stages[-1]
                    self._configure_stage_from_data(last_stage, stage_data)

        # Update the pipeline preview
        self.pipeline_builder._update_pipeline_preview()

    def _configure_stage_from_data(
        self, stage_widget: Any, stage_data: dict[str, Any]
    ) -> None:
        """Configure a pipeline stage widget from template data."""
        if not stage_data:
            return

        # Extract stage type and configuration
        stage_type = list(stage_data.keys())[0] if stage_data else "$match"
        stage_config = stage_data.get(stage_type, {})

        # Set the stage type and configuration
        stage_widget.stage_type = stage_type
        stage_widget.stage_config = stage_config

        # Update the UI to reflect the new stage type
        if hasattr(stage_widget, "stage_combo"):
            # Find and set the correct stage type in the combo box
            combo = stage_widget.stage_combo
            for i in range(combo.count()):
                if combo.itemText(i) == stage_type:
                    combo.setCurrentIndex(i)
                    break

        # Update the preview
        stage_widget._update_preview()

    def _add_filter_from_data(self, filter_data: dict[str, Any]) -> None:
        """Add a filter widget from saved data."""
        if not filter_data or not self.find_root_group:
            return

        try:
            # Always add a new condition since we start with a clean root group when loading templates
            self.find_root_group.add_condition()
            if self.find_root_group.conditions:
                last_condition = self.find_root_group.conditions[-1]
                # Check if it's a ConditionWidget (not a ConditionGroup)
                from ui.query_builder_dialog import ConditionWidget

                if isinstance(last_condition, ConditionWidget):
                    self._set_condition_components(last_condition, filter_data)
        except Exception as e:
            # If we can't properly reconstruct the filter, just skip it
            # This ensures the template loading doesn't completely fail
            print(f"Warning: Could not load filter data: {e}")
            # This ensures the template loading doesn't completely fail

    def _populate_condition_from_data(
        self, group: Any, filter_data: dict[str, Any]
    ) -> None:
        """Populate a condition group from filter data."""
        if not filter_data:
            return

        if self._is_logical_operation(filter_data):
            self._handle_logical_operation(group, filter_data)
        else:
            self._handle_single_condition(group, filter_data)

    def _is_logical_operation(self, filter_data: dict[str, Any]) -> bool:
        """Check if filter data represents a logical operation."""
        return "$and" in filter_data or "$or" in filter_data

    def _handle_logical_operation(
        self, group: Any, filter_data: dict[str, Any]
    ) -> None:
        """Handle logical operations like $and/$or."""
        operator = "$and" if "$and" in filter_data else "$or"
        conditions = filter_data[operator]

        for condition_data in conditions:
            self._add_condition_to_group(group, condition_data)

    def _handle_single_condition(self, group: Any, filter_data: dict[str, Any]) -> None:
        """Handle a single condition."""
        self._add_condition_to_group(group, filter_data)

    def _add_condition_to_group(
        self, group: Any, condition_data: dict[str, Any]
    ) -> None:
        """Add a condition to the group and populate it."""
        group.add_condition()
        if group.conditions:
            last_condition = group.conditions[-1]
            from ui.query_builder_dialog import ConditionWidget

            if isinstance(last_condition, ConditionWidget):
                self._set_condition_components(last_condition, condition_data)

    def _set_condition_components(
        self, condition_widget: Any, filter_data: dict[str, Any]
    ) -> None:
        """Set the components of a condition widget from filter data."""
        if not self._can_set_condition_components(condition_widget, filter_data):
            return

        try:
            field, operator, value = self._extract_condition_parts(filter_data)
            self._apply_condition_parts(condition_widget, field, operator, value)
        except Exception as e:
            print(f"Warning: Could not set condition components: {e}")

    def _can_set_condition_components(
        self, condition_widget: Any, filter_data: dict[str, Any]
    ) -> bool:
        """Check if condition components can be set."""
        return hasattr(condition_widget, "field_combo") and bool(filter_data)

    def _extract_condition_parts(
        self, filter_data: dict[str, Any]
    ) -> tuple[str, str, Any]:
        """Extract field, operator, and value from filter data."""
        if self._is_direct_format(filter_data):
            return self._extract_from_direct_format(filter_data)
        else:
            return self._extract_from_mongodb_format(filter_data)

    def _is_direct_format(self, filter_data: dict[str, Any]) -> bool:
        """Check if filter data is in direct format."""
        return (
            "field" in filter_data
            and "operator" in filter_data
            and "value" in filter_data
        )

    def _extract_from_direct_format(
        self, filter_data: dict[str, Any]
    ) -> tuple[str, str, Any]:
        """Extract parts from direct format."""
        return (
            filter_data["field"],
            filter_data["operator"],
            filter_data["value"],
        )

    def _extract_from_mongodb_format(
        self, filter_data: dict[str, Any]
    ) -> tuple[str, str, Any]:
        """Extract parts from MongoDB query format."""
        field = list(filter_data.keys())[0] if filter_data else ""
        field_data = filter_data.get(field, {})

        if isinstance(field_data, dict) and field_data:
            operator = list(field_data.keys())[0]
            value = field_data[operator]
            operator, value = self._convert_mongodb_operator_to_ui(operator, value)
        else:
            operator = "="
            value = field_data

        return field, operator, value

    def _convert_mongodb_operator_to_ui(
        self, operator: str, value: Any
    ) -> tuple[str, Any]:
        """Convert MongoDB operator to UI operator and adjust value if needed."""
        if operator == "$regex":
            return self._convert_regex_to_ui_format(value)
        elif operator == "$exists":
            return self._convert_exists_to_ui_format(value)
        else:
            return self._convert_standard_operator_to_ui(operator), value

    def _convert_standard_operator_to_ui(self, operator: str) -> str:
        """Convert standard MongoDB operators to UI operators."""
        operator_mapping = {
            "$eq": "=",
            "$ne": "!=",
            "$gt": ">",
            "$gte": ">=",
            "$lt": "<",
            "$lte": "<=",
            "$in": "in",
            "$nin": "not in",
        }
        return operator_mapping.get(operator, "=")

    def _convert_exists_to_ui_format(self, value: Any) -> tuple[str, str]:
        """Convert $exists operator to UI format."""
        operator = "exists" if value else "not exists"
        return operator, ""  # Existence operators don't need a value in UI

    def _convert_regex_to_ui_format(self, regex_value: str | Any) -> tuple[str, str]:
        """Convert a MongoDB regex pattern back to UI operator and value."""
        if isinstance(regex_value, str):
            # Check for starts with pattern: ^value
            if regex_value.startswith("^") and not regex_value.endswith("$"):
                return "starts with", regex_value[1:]  # Remove the ^
            # Check for ends with pattern: value$
            elif regex_value.endswith("$") and not regex_value.startswith("^"):
                return "ends with", regex_value[:-1]  # Remove the $
            # Check for contains pattern: .*value.*
            elif regex_value.startswith(".*") and regex_value.endswith(".*"):
                return "contains", regex_value[2:-2]  # Remove .* from both ends
            # Otherwise treat as raw regex
            else:
                return "regex", regex_value
        else:
            return "regex", str(regex_value)

    def _apply_condition_parts(
        self, condition_widget: Any, field: str, operator: str, value: Any
    ) -> None:
        """Apply the extracted parts to the condition widget."""
        self._set_field_component(condition_widget, field)
        self._set_operator_component(condition_widget, operator)
        self._set_value_component(condition_widget, value)

    def _set_field_component(self, condition_widget: Any, field: str) -> None:
        """Set the field component."""
        if hasattr(condition_widget, "field_combo"):
            condition_widget.field_combo.setCurrentText(field)

    def _set_operator_component(self, condition_widget: Any, operator: str) -> None:
        """Set the operator component."""
        if hasattr(condition_widget, "operator_combo"):
            condition_widget.operator_combo.setCurrentText(operator)

    def _set_value_component(self, condition_widget: Any, value: Any) -> None:
        """Set the value component."""
        if hasattr(condition_widget, "value_input"):
            if isinstance(value, str | int | float):
                condition_widget.value_input.setText(str(value))
            else:
                condition_widget.value_input.setText(json.dumps(value))
