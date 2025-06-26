import json
import os
import re
from collections.abc import Callable
from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QSplitter,  # Added QSplitter
    QTableWidgetItem,
    QTextEdit,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui.constants import EDIT_DOCUMENT_ACTION, EDIT_DOCUMENT_TITLE, SCHEMA_DIR
from ui.edit_document_dialog import EditDocumentDialog
from utils.error_handling import handle_exception


def get_schema_fields_for_path(schema: dict[str, Any], path: list[str]) -> list[str]:
    """
    Given a schema dict and a path (e.g., ["covers"]), return available fields at that path.

    Args:
        schema: The schema dictionary.
        path: List of keys representing the path in the schema.
    Returns:
        List of available field names at the specified path.
    """
    node: Any = schema
    for part in path:
        if isinstance(node, dict) and part in node:
            node = node[part]
            if isinstance(node, list) and node and isinstance(node[0], dict):
                node = node[0]
        else:
            return []
    if isinstance(node, dict):
        return list(node.keys())
    return []


class QueryPanelMixin:
    """
    Mixin for query panel logic, providing query execution, result display, and related UI logic.
    Intended to be used with PyQt5 QWidget subclasses.
    """

    mongo_client: Any
    result_display: "QTextEdit"
    query_input: Any
    data_table: Any
    prev_btn: Any
    next_btn: Any
    page_label: Any
    result_count_label: Any
    results: list[dict[str, Any]]
    current_page: int
    page_size: int
    last_query: str
    last_collection: str
    json_tree: Any
    _table_signals_connected: bool = False
    _tree_signals_connected: bool = False
    _explain_summary_widget: QWidget | None = None
    page_size_picker: Any = None  #: Optional widget for page size selection
    view_as_picker: Any = None  #: Optional widget for result view mode selection
    nav_controls_widget: QWidget | None = None  #: Optional container for nav controls
    view_switch_widget: QWidget | None = None  #: Optional container for view switcher

    def execute_query(self) -> None:
        """
        Execute the current query in the query input widget and update the results display.
        Handles error reporting and updates UI state accordingly.
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
            handle_exception(
                e, parent=getattr(self, "parent", None), title="Query Error"
            )
            self._set_db_info_label(f"Query error: {str(e)}")

    def _set_db_info_label(self, text: str) -> None:
        """
        Set the database info label text, if present.

        Args:
            text: The text to display in the info label.
        """
        label = getattr(self, "db_info_label", None)
        if label and hasattr(label, "setText"):
            label.setText(text)

    def display_results(self) -> None:
        """
        Display the query results in the UI, updating the table and tree widgets as needed.
        Handles empty result cases and resets UI state.
        """
        # Reset UI state and show all controls
        self._reset_ui_for_query_results()
        self._show_control_widgets()

        # Connect signals for context menus
        self.setup_query_panel_signals()

        # Handle empty results case
        if not self.results:
            self._handle_empty_results()
            return

        # Show all results for this page
        page_results = self.results

        # Update navigation and display
        self._update_navigation_controls(page_results)
        self.display_table_results(page_results)
        self.display_tree_results(page_results)
        self._update_tree_view(page_results)

        # Hide result_display (used for testing)
        if hasattr(self, "result_display") and self.result_display is not None:
            self.result_display.hide()

    def _update_navigation_controls(self, page_results: list[dict[str, Any]]) -> None:
        """Update navigation controls with current page information."""
        if hasattr(self, "prev_btn"):
            self.prev_btn.setEnabled(self.current_page > 0)
        if hasattr(self, "next_btn"):
            self.next_btn.setEnabled(len(page_results) == self.page_size)
        if hasattr(self, "page_label"):
            self.page_label.setText(f"Page {self.current_page + 1}")
        if hasattr(self, "result_count_label"):
            self.result_count_label.setText(f"Showing {len(page_results)} results")

    def _handle_empty_results(self) -> None:
        """Handle the case when there are no results to display."""
        if self.data_table:
            self.data_table.setRowCount(0)
        if getattr(self, "json_tree", None):
            self.json_tree.clear()
        if hasattr(self, "page_label"):
            self.page_label.setText(f"Page {self.current_page + 1}")
        if hasattr(self, "result_count_label"):
            self.result_count_label.setText("No results")
        if hasattr(self, "prev_btn"):
            self.prev_btn.setEnabled(self.current_page > 0)
        if hasattr(self, "next_btn"):
            self.next_btn.setEnabled(False)

    def _update_tree_view(self, page_results: list[dict[str, Any]]) -> None:
        """Update the JSON tree view with the current results."""
        if not getattr(self, "json_tree", None):
            return

        self.json_tree.clear()
        for idx, doc in enumerate(
            page_results, start=self.current_page * self.page_size + 1
        ):
            doc_item = self._add_tree_item(f"Document {idx}", doc)
            self.json_tree.addTopLevelItem(doc_item)
        self.json_tree.expandToDepth(1)
        self.json_tree.show()

    def _add_tree_item(self, key: str, value: Any) -> QTreeWidgetItem:
        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), ""])
            for k, v in value.items():
                child = self._add_tree_item(k, v)
                item.addChild(child)
            return item
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), f"[{len(value)} items]"])
            for idx, v in enumerate(value):
                child = self._add_tree_item(f"[{idx}]", v)
                item.addChild(child)
            return item
        else:
            return QTreeWidgetItem([str(key), str(value)])

    def _setup_context_menu_signal(
        self,
        widget: str,
        signal_name: str,
        handler: Callable[[Any], None],
        flag_name: str,
    ) -> None:
        if not hasattr(self, widget) or getattr(self, widget) is None:
            return
        w = getattr(self, widget)
        w.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        if getattr(self, flag_name, False):
            getattr(w, signal_name).disconnect(handler)
        getattr(w, signal_name).connect(handler)
        setattr(self, flag_name, True)

    def setup_query_panel_signals(self) -> None:
        """Connect context menu signals for table and tree widgets, ensuring old signals are disconnected."""
        self._setup_context_menu_signal(
            "data_table",
            "customContextMenuRequested",
            self.show_table_context_menu,
            "_table_signals_connected",
        )
        self._setup_context_menu_signal(
            "json_tree",
            "customContextMenuRequested",
            self.show_tree_context_menu,
            "_tree_signals_connected",
        )

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
        self.data_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_row_docs = []
        for row, doc in enumerate(results):
            self._table_row_docs.append(doc)
            for col, key in enumerate(columns):
                value = doc.get(key, "")
                self.data_table.setItem(row, col, QTableWidgetItem(str(value)))

    def show_table_context_menu(self, pos: Any) -> None:
        if not self.data_table:
            return
        index = self.data_table.indexAt(pos)
        if not index.isValid():
            return
        doc = (
            self._table_row_docs[index.row()]
            if hasattr(self, "_table_row_docs")
            and index.row() < len(self._table_row_docs)
            else None
        )
        if doc:
            menu = QMenu(self.data_table)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = (
                self.data_table.viewport()
                if hasattr(self.data_table, "viewport")
                else None
            )
            global_pos = (
                viewport.mapToGlobal(pos)
                if viewport
                else self.data_table.mapToGlobal(pos)
            )
            action = menu.exec(global_pos)
            if action == edit_action:
                self.edit_document(doc)

    def display_tree_results(self, results: list[dict[str, Any]]) -> None:
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
            doc_item.setData(0, Qt.ItemDataRole.UserRole + 1, doc)
        self.json_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

    def show_tree_context_menu(self, pos: Any) -> None:
        if not self.json_tree:
            return
        item = self.json_tree.itemAt(pos)
        if item and item.parent() is None:
            menu = QMenu(self.json_tree)
            edit_action = menu.addAction(EDIT_DOCUMENT_ACTION)
            viewport = (
                self.json_tree.viewport()
                if hasattr(self.json_tree, "viewport")
                else None
            )
            global_pos = (
                viewport.mapToGlobal(pos)
                if viewport
                else self.json_tree.mapToGlobal(pos)
            )
            action = menu.exec(global_pos)
            if action == edit_action:
                doc = item.data(0, Qt.ItemDataRole.UserRole + 1)
                if doc:
                    self.edit_document(doc)

    def edit_document(self, document: dict) -> None:
        # Use self if it's a QWidget, otherwise try to get parent or pass None
        parent = self if isinstance(self, QWidget) else None
        dialog = EditDocumentDialog(document, parent)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            edited_doc = dialog.get_edited_document()
            if edited_doc is not None:
                self.update_document_in_db(edited_doc)

    def update_document_in_db(self, edited_doc: dict) -> None:
        if not self.mongo_client or "_id" not in edited_doc:
            QMessageBox.warning(
                None,
                EDIT_DOCUMENT_TITLE,
                "Cannot update document: missing _id or no DB connection.",
            )
            return
        try:
            collection = getattr(self, "last_collection", None)
            if not collection:
                QMessageBox.warning(
                    None, EDIT_DOCUMENT_TITLE, "Cannot determine collection for update."
                )
                return
            result = self.mongo_client.update_document(
                collection, edited_doc["_id"], edited_doc
            )
            if result:
                QMessageBox.information(
                    None, EDIT_DOCUMENT_TITLE, "Document updated successfully."
                )
                self.execute_query()
            else:
                QMessageBox.warning(
                    None, EDIT_DOCUMENT_TITLE, "Document update failed."
                )
        except Exception as e:
            QMessageBox.critical(
                None, EDIT_DOCUMENT_TITLE, f"Error updating document: {e}"
            )

    def add_tree_item(self, parent: QTreeWidgetItem, data: dict[str, Any]) -> None:
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
            self.execute_query()

    def next_page(self) -> None:
        self.current_page += 1
        self.execute_query()

    def execute_explain(self) -> None:
        """Run the current query with explain and display the plan."""
        if not self.mongo_client:
            self._set_db_info_label("No database connection")
            return
        query_text = self.query_input.toPlainText().strip()
        if not query_text:
            self._set_db_info_label("Please enter a query")
            return
        try:
            result = self.mongo_client.execute_query(query_text, explain=True)
            if result.is_ok:
                explain_data = result.unwrap()
                self.display_explain_result(explain_data)
            else:
                self._set_db_info_label(f"Explain error: {result.unwrap_err()}")
        except Exception as e:
            self._set_db_info_label(f"Explain error: {str(e)}")

    def _hide_explain_controls(self) -> None:
        """Hide all control widgets when in explain mode."""
        for attr in (
            "prev_btn",
            "next_btn",
            "page_label",
            "result_count_label",
            "page_size_picker",
            "view_as_picker",
            "page_size_label",
            "view_as_label",
        ):
            widget = getattr(self, attr, None)
            if widget is not None and hasattr(widget, "setVisible"):
                widget.setVisible(False)
                if hasattr(widget, "hide"):
                    widget.hide()

        # Hide the parent containers
        for container in ("nav_controls_widget", "view_switch_widget"):
            widget = getattr(self, container, None)
            if widget is not None:
                widget.setVisible(False)
                widget.hide()

    def display_explain_result(self, result: Any) -> None:
        """Display the explain plan as a tree in the Results section and show a summary box above it."""
        if not self.json_tree:
            return

        # Clean up any previous state
        self._remove_previous_summary_widget()
        self._hide_explain_controls()

        # Hide the data table
        if hasattr(self, "data_table") and self.data_table is not None:
            self.data_table.hide()
            self.data_table.setVisible(False)

        # Set up and display explain view
        self._setup_explain_tree_view()
        self._hide_other_result_displays()
        self._create_summary_widget(result)
        self._display_explain_tree(result)

        # Ensure tree view is visible
        self.json_tree.update()
        self.json_tree.show()

    def _setup_explain_tree_view(self) -> None:
        """Set up the tree view for explain results."""
        self.json_tree.clear()
        self.json_tree.show()
        self.json_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.json_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.json_tree.setColumnWidth(0, 350)
        self.json_tree.setColumnWidth(1, 600)

    def _hide_other_result_displays(self) -> None:
        """Hide data table and result display widgets."""
        if hasattr(self, "data_table") and self.data_table is not None:
            self.data_table.hide()
        if hasattr(self, "result_display") and self.result_display is not None:
            self.result_display.hide()

    def _remove_previous_summary_widget(self) -> None:
        """Remove any existing explain summary widget and restore normal view state."""
        if (
            not hasattr(self, "_explain_summary_widget")
            or not self._explain_summary_widget
        ):
            return

        widget_to_remove = self._explain_summary_widget
        self._explain_summary_widget = None

        # Find the splitter ancestor for proper cleanup
        original_parent = widget_to_remove.parentWidget()
        while original_parent and not isinstance(original_parent, QSplitter):
            original_parent = original_parent.parentWidget()

        # Clean up the summary widget
        widget_to_remove.hide()
        widget_to_remove.setParent(None)
        widget_to_remove.deleteLater()

        # Update splitter if found
        if isinstance(original_parent, QSplitter):
            original_parent.refresh()
            original_parent.updateGeometry()
            original_parent.update()
            if hasattr(original_parent, "repaint"):
                original_parent.repaint()

        # Show all controls again
        self._show_control_widgets()

    def _show_widget_if_exists(self, widget_name: str) -> None:
        """Show and make visible a widget if it exists."""
        widget = getattr(self, widget_name, None)
        if widget is not None:
            widget.setVisible(True)
            if hasattr(widget, "show"):
                widget.show()

    def _show_container_if_exists(self, container_name: str) -> None:
        """Show and make visible a container widget if it exists, bringing it to front."""
        container = getattr(self, container_name, None)
        if container is not None:
            container.setVisible(True)
            container.show()
            if hasattr(container, "raise_"):
                container.raise_()

    def _show_control_widgets(self) -> None:
        """Show all control widgets and containers."""
        # Show all individual control widgets
        control_widgets = (
            "prev_btn",
            "next_btn",
            "page_label",
            "result_count_label",
            "page_size_picker",
            "view_as_picker",
            "page_size_label",
            "view_as_label",
        )
        for widget_name in control_widgets:
            self._show_widget_if_exists(widget_name)

        # Show container widgets and ensure they're in front
        containers = ("nav_controls_widget", "view_switch_widget")
        for container_name in containers:
            self._show_container_if_exists(container_name)

        # Show and bring data table to front
        self._show_container_if_exists("data_table")

        # Show tree view if it exists
        self._show_widget_if_exists("json_tree")

    def _create_summary_widget(self, result: Any) -> None:
        """Create and display the query summary widget."""
        summary_text = self._build_explain_summary(result)
        if not summary_text:
            summary_text = "<i>No summary available for this query plan.</i>"

        # Try to find the QSplitter ancestor, not just immediate parent
        splitter_widget = self.json_tree.parentWidget()
        while splitter_widget and not isinstance(splitter_widget, QSplitter):
            splitter_widget = splitter_widget.parentWidget()
        if not splitter_widget:
            # fallback: use immediate parent
            splitter_widget = self.json_tree.parentWidget()
            if not splitter_widget:
                return

        summary_widget_instance = QWidget(splitter_widget)
        summary_layout = QVBoxLayout(summary_widget_instance)
        summary_label = QLabel(f"<b>Query Summary</b><br>{summary_text}")
        summary_label.setWordWrap(True)
        summary_layout.addWidget(summary_label)
        summary_layout.setContentsMargins(8, 8, 8, 8)
        summary_widget_instance.setLayout(summary_layout)

        if isinstance(splitter_widget, QSplitter):
            splitter_widget.insertWidget(0, summary_widget_instance)
        else:
            parent_layout = splitter_widget.layout()
            if parent_layout:
                parent_layout.insertWidget(0, summary_widget_instance)

        summary_widget_instance.show()
        self._explain_summary_widget = summary_widget_instance

    def _display_explain_tree(self, result: Any) -> None:
        """Display the explain result in the tree view."""
        if isinstance(result, dict):
            root_item = QTreeWidgetItem(self.json_tree, ["Explain Plan"])
            self._add_tree_item_to_tree(root_item, result)
            root_item.setExpanded(True)
        else:
            QTreeWidgetItem(self.json_tree, ["Result: " + str(result)])

    def _build_explain_summary(self, result: Any) -> str:
        """Extract and format key insights from explain() output for summary display."""
        if not isinstance(result, dict):
            return ""

        plan = result.get("queryPlanner", {}).get("winningPlan", {})
        exec_stats = result.get("executionStats", {})

        summary_lines = [
            self._get_used_index_info(plan),
            self._get_scan_type_info(plan),
            self._get_docs_scanned_info(exec_stats),
            self._get_execution_time_info(exec_stats),
            self._get_sort_info(plan),
            self._get_rejected_plans_info(result),
        ]
        return "<br>".join(summary_lines)

    def _find_stage_in_plan(self, plan: Any, stage_name: str) -> dict[str, Any] | None:
        """Helper to recursively search for a stage in the plan."""
        if not isinstance(plan, dict):
            return None
        if plan.get("stage") == stage_name:
            return plan

        return self._search_nested_plan_structures(plan, stage_name)

    def _search_nested_plan_structures(
        self, plan: dict[str, Any], stage_name: str
    ) -> dict[str, Any] | None:
        """Search through nested plan structures for a specific stage."""
        search_keys = (
            "inputStage",
            "inputStages",
            "shards",
            "queryPlan",
            "winningPlan",
            "children",
            "subplans",
        )

        for key in search_keys:
            val = plan.get(key)
            found = self._search_plan_value(val, stage_name)
            if found:
                return found
        return None

    def _search_plan_value(self, val: Any, stage_name: str) -> dict[str, Any] | None:
        """Search a plan value (dict or list) for a specific stage."""
        if isinstance(val, dict):
            return self._find_stage_in_plan(val, stage_name)
        elif isinstance(val, list):
            for v in val:
                found = self._find_stage_in_plan(v, stage_name)
                if found:
                    return found
        return None

    def _find_deepest_access_stage(self, plan: Any) -> str | None:
        """Find the deepest access stage in the plan."""
        access_stages = {"IXSCAN", "COLLSCAN", "FETCH"}
        result_stage = None

        def recurse(node: Any) -> None:
            nonlocal result_stage
            if not isinstance(node, dict):
                return
            if node.get("stage") in access_stages:
                result_stage = node.get("stage")

            search_keys = ("inputStage", "inputStages", "children", "subplans")
            for key in search_keys:
                val = node.get(key)
                if isinstance(val, dict):
                    recurse(val)
                elif isinstance(val, list):
                    for v in val:
                        recurse(v)

        recurse(plan)
        return result_stage

    def _get_used_index_info(self, plan: dict[str, Any]) -> str:
        """Get information about index usage."""
        ixscan = self._find_stage_in_plan(plan, "IXSCAN")
        if ixscan and "indexName" in ixscan:
            return f"Used index: {ixscan['indexName']}"
        elif plan.get("inputStage", {}).get("stage") == "COLLSCAN":
            return "No index used (COLLSCAN)"
        return "No index used (COLLSCAN)"

    def _get_scan_type_info(self, plan: dict[str, Any]) -> str:
        """Get information about scan type."""
        scan_type = self._find_deepest_access_stage(plan)
        return f"Scan type: {scan_type}" if scan_type else "Scan type: Unknown"

    def _get_docs_scanned_info(self, exec_stats: dict[str, Any]) -> str:
        """Get information about documents scanned vs returned."""
        docs_examined = exec_stats.get("totalDocsExamined")
        n_returned = exec_stats.get("nReturned")
        if docs_examined is not None and n_returned is not None:
            return f"Documents scanned / returned: {docs_examined} / {n_returned}"
        return "Documents scanned / returned: Unknown"

    def _get_execution_time_info(self, exec_stats: dict[str, Any]) -> str:
        """Get information about execution time."""
        exec_time = exec_stats.get("executionTimeMillis")
        return (
            f"Execution time: {exec_time} ms"
            if exec_time is not None
            else "Execution time: Unknown"
        )

    def _get_sort_info(self, plan: dict[str, Any]) -> str:
        """Get information about sorting."""
        has_sort = bool(self._find_stage_in_plan(plan, "SORT"))
        return f"In-memory sort: {'Yes' if has_sort else 'No'}"

    def _get_rejected_plans_info(self, result: dict[str, Any]) -> str:
        """Get information about rejected plans."""
        rejected = result.get("queryPlanner", {}).get("rejectedPlans", [])
        rejected_count = len(rejected)
        if not rejected_count:
            return "Rejected plans: 0"

        rejected_indexes = []
        for r in rejected:
            ix = self._find_stage_in_plan(r, "IXSCAN")
            if ix and "indexName" in ix:
                rejected_indexes.append(ix["indexName"])

        if rejected_indexes:
            return (
                f"Rejected plans: {rejected_count} (e.g. {', '.join(rejected_indexes)})"
            )
        else:
            return f"Rejected plans: {rejected_count}"

    def _add_tree_item_to_tree(self, parent: QTreeWidgetItem, value: Any) -> None:
        """Add tree items for query results."""
        if isinstance(value, dict):
            for k, v in value.items():
                child = self._create_child_item(k, v)
                parent.addChild(child)
        elif isinstance(value, list):
            for idx, v in enumerate(value):
                child = self._create_child_item(f"[{idx}]", v)
                parent.addChild(child)

    def _create_child_item(self, key: str, value: Any) -> QTreeWidgetItem:
        """Create a new tree widget item based on the type of value."""
        if isinstance(value, dict | list):
            child = QTreeWidgetItem([str(key), ""])
            self._add_tree_item_to_tree(child, value)
            return child
        return QTreeWidgetItem([str(key), str(value)])

    def _reset_ui_for_query_results(self) -> None:
        """Reset UI state for displaying query results."""
        # First, clean up any explain summary
        self._remove_previous_summary_widget()

        # Then show data table which gets hidden in explain mode
        if hasattr(self, "data_table") and self.data_table is not None:
            self.data_table.show()

        # Force table visibility in case we're coming back from explain view
        if hasattr(self, "data_table") and self.data_table is not None:
            self.data_table.setVisible(True)
            if hasattr(self.data_table, "raise_"):
                self.data_table.raise_()

        # Now show the navigation and view controls
        if (
            hasattr(self, "nav_controls_widget")
            and self.nav_controls_widget is not None
        ):
            self.nav_controls_widget.show()
            self.nav_controls_widget.setVisible(True)
        if hasattr(self, "view_switch_widget") and self.view_switch_widget is not None:
            self.view_switch_widget.show()
            self.view_switch_widget.setVisible(True)

    def get_collection_schema_fields(
        self, db: str, collection: str, path: list[str]
    ) -> list[str]:
        schema_path = os.path.join(SCHEMA_DIR, f"{db}__{collection}.json")
        if not os.path.exists(schema_path):
            return []
        try:
            with open(schema_path, encoding="utf-8") as f:
                schema = json.load(f)
            return get_schema_fields_for_path(schema, path)
        except Exception:
            return []

    def provide_query_suggestions(
        self, text: str, db: str, collection: str
    ) -> list[str]:
        """Return field suggestions based on schema and current query context."""
        # Simple parser: look for db.collection.find({"field1.field2.")
        m = re.search(rf"db\\.{collection}\\.find\\(\{{.*?([\w\.]+)\\.$", text)
        if not m:
            return []
        path = m.group(1).split(".")
        return self.get_collection_schema_fields(db, collection, path)
