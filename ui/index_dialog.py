import json
from typing import Any

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from ui.ui_utils import setup_dialog_layout

ADD_INDEX_LABEL = "Add Index"
EDIT_INDEX_LABEL = "Edit Index"
REMOVE_INDEX_LABEL = "Remove Index"
SAVE_LABEL = "Save"
CANCEL_LABEL = "Cancel"

INDEX_TYPE_ASC = "1 (asc)"
INDEX_TYPE_DESC = "-1 (desc)"
INDEX_TYPE_HASHED = "hashed"
INDEX_TYPE_2DSPHERE = "2dsphere"
INDEX_TYPE_2D = "2d"
INDEX_TYPE_TEXT = "text"
INDEX_TYPE_CHOICES = [
    INDEX_TYPE_ASC,
    INDEX_TYPE_DESC,
    INDEX_TYPE_HASHED,
    INDEX_TYPE_2DSPHERE,
    INDEX_TYPE_2D,
    INDEX_TYPE_TEXT,
]


class IndexDialog(QDialog):
    """Dialog for managing MongoDB indexes."""

    def __init__(
        self, indexes: list[dict[str, Any]], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Indexes")
        self.setMinimumWidth(600)
        self.indexes = indexes

        # Initialize table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Name", "Fields"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        if header := self.table.horizontalHeader():
            header.setStretchLastSection(True)

        # Create buttons
        self.add_btn = QPushButton("Add Index")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        # Set up layout
        from typing import cast

        widgets = [cast(QWidget, self.table)]
        button_widgets = [
            cast(QWidget, btn)
            for btn in [
                self.add_btn,
                self.edit_btn,
                self.delete_btn,
                self.ok_btn,
                self.cancel_btn,
            ]
        ]
        setup_dialog_layout(self, widgets, button_widgets)

        # Connect signals
        self.add_btn.clicked.connect(self.add_index)
        self.edit_btn.clicked.connect(self.edit_index)
        self.delete_btn.clicked.connect(self.delete_index)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        self.selected_index_name: str | None = None  # Track the selected index name
        self.populate_table()

    def show_dialog(self, dialog_class, *args, **kwargs) -> tuple[int, Any]:
        dialog = dialog_class(*args, parent=self, **kwargs)
        result = dialog.exec()
        return result, dialog

    def populate_table(self) -> None:
        """Populate the index table with current indexes."""
        self.table.setRowCount(len(self.indexes))
        for row, index in enumerate(self.indexes):
            self.table.setItem(row, 0, QTableWidgetItem(index.get("name", "")))
            key_data = index.get("key", [])
            if isinstance(key_data, dict):
                # Handle dictionary format
                fields = ", ".join(
                    f"{k}: {v}"
                    for k, v in key_data.items()
                    if isinstance(k, str) and (v == 1 or v == -1)
                )
            else:
                # Handle list format
                fields = ", ".join(
                    f"{field}: {direction}"
                    for field, direction in key_data
                    if isinstance(field, str) and (direction == 1 or direction == -1)
                )
            self.table.setItem(row, 1, QTableWidgetItem(fields))

    def add_index(self) -> None:
        """Open the index editor dialog to add a new index."""
        result, dlg = self.show_dialog(IndexEditDialog, {})
        if result == QDialog.DialogCode.Accepted:
            new_index = dlg.get_index_data()
            if new_index:
                self.indexes.append(new_index)
                self.populate_table()

    def edit_index(self) -> None:
        """Open the index editor dialog to edit the selected index."""
        if not (selected_items := self.table.selectedItems()):
            return

        row = selected_items[0].row()
        if item := self.table.item(row, 0):
            index_name = item.text()
            index_dict = next(
                (idx for idx in self.indexes if idx["name"] == index_name), None
            )
            if index_dict:
                result, dlg = self.show_dialog(IndexEditDialog, index_dict)
                if result == QDialog.DialogCode.Accepted:
                    updated_index = dlg.get_index_data()
                    if updated_index:
                        index_dict.update(updated_index)
                        self.populate_table()

    def delete_index(self) -> None:
        """Delete the selected index after confirmation."""
        if not (selected_items := self.table.selectedItems()):
            return

        row = selected_items[0].row()
        if item := self.table.item(row, 0):
            index_name = item.text()
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete the index '{index_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                del self.indexes[row]
                self.selected_index_name = None  # Reset selection after deleting
                self.populate_table()

    def get_selected_index_name(self) -> str | None:
        return self.selected_index_name

    def get_index_data(self) -> dict | None:
        return getattr(self, "accepted_data", None)


class IndexEditDialog(QDialog):
    """Dialog for editing a single MongoDB index."""

    def __init__(
        self, index_dict: dict[str, Any], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Index")
        self.setMinimumWidth(500)
        self.index_dict = index_dict
        self.index_name = index_dict.get("name", "")

        # Create widgets
        self.name_input = QLineEdit(self.index_name)
        self.unique_checkbox = QCheckBox("Unique")
        self.unique_checkbox.setChecked(index_dict.get("unique", False))

        self.fields_table = QTableWidget(0, 2)
        self.fields_table.setHorizontalHeaderLabels(["Field", "Order"])
        self.fields_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        if header := self.fields_table.horizontalHeader():
            header.setStretchLastSection(True)

        self.add_field_btn = QPushButton("Add Field")
        self.delete_field_btn = QPushButton("Delete Field")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        # Field editing section
        field_edit_layout = QHBoxLayout()
        self.field_name_edit = QLineEdit()
        self.field_name_edit.setPlaceholderText("Field name")
        self.index_type_combo = QComboBox()
        self.index_type_combo.addItems(INDEX_TYPE_CHOICES)
        field_edit_layout.addWidget(QLabel("Field:"))
        field_edit_layout.addWidget(self.field_name_edit)
        field_edit_layout.addWidget(QLabel("Type:"))
        field_edit_layout.addWidget(self.index_type_combo)

        # Set up layout
        from typing import cast

        widgets = [
            QLabel("Name:"),
            cast(QWidget, self.name_input),  # Use existing name_input
            cast(QWidget, self.unique_checkbox),
            QLabel("Fields:"),
            cast(QWidget, self.fields_table),
            cast(
                QWidget, QWidget(self).setLayout(field_edit_layout)
            ),  # Add field editing section
        ]
        button_widgets = [
            cast(QWidget, btn)
            for btn in [
                self.add_field_btn,
                self.delete_field_btn,
                self.ok_btn,
                self.cancel_btn,
            ]
        ]
        setup_dialog_layout(self, widgets, button_widgets)

        # Connect signals
        self.add_field_btn.clicked.connect(self.add_field)
        self.delete_field_btn.clicked.connect(self.delete_field)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Initialize fields
        self.populate_fields()

    def populate_fields(self) -> None:
        """Populate the fields table with the index's fields."""
        self.fields_table.setRowCount(0)
        keys = self.index_dict.get("key", []) if self.index_dict else []
        if not isinstance(keys, list):
            try:
                keys = list(keys.items())
            except Exception:
                keys = []
        for pair in keys:
            if isinstance(pair, list | tuple) and len(pair) == 2:
                row = self.fields_table.rowCount()
                self.fields_table.insertRow(row)
                self.fields_table.setItem(row, 0, QTableWidgetItem(str(pair[0])))
                val = pair[1]
                if val == 1:
                    val_str = INDEX_TYPE_ASC
                elif val == -1:
                    val_str = INDEX_TYPE_DESC
                elif val in (
                    INDEX_TYPE_HASHED,
                    INDEX_TYPE_2DSPHERE,
                    INDEX_TYPE_2D,
                    INDEX_TYPE_TEXT,
                ):
                    val_str = str(val)
                else:
                    val_str = str(val)
                self.fields_table.setItem(row, 1, QTableWidgetItem(val_str))

    def add_field(self) -> None:
        name = self.field_name_edit.text().strip()
        idx_type = self.index_type_combo.currentText()
        if not name:
            return
        # Only allow canonical values in the table
        if idx_type not in INDEX_TYPE_CHOICES:
            idx_type = INDEX_TYPE_ASC
        row = self.fields_table.rowCount()
        self.fields_table.insertRow(row)
        self.fields_table.setItem(row, 0, QTableWidgetItem(name))
        self.fields_table.setItem(row, 1, QTableWidgetItem(idx_type))
        self.field_name_edit.clear()

    def delete_field(self) -> None:
        selected = self.fields_table.currentRow()
        if selected >= 0:
            self.fields_table.removeRow(selected)

    def _get_index_keys(self) -> list:
        keys: list[tuple[str, int | str]] = []
        for row in range(self.fields_table.rowCount()):
            field_item = self.fields_table.item(row, 0)
            value_item = self.fields_table.item(row, 1)
            if field_item is None or value_item is None:
                continue
            field = field_item.text()
            value_str = value_item.text()
            value: int | str
            if value_str == INDEX_TYPE_ASC:
                value = 1
            elif value_str == INDEX_TYPE_DESC:
                value = -1
            elif value_str in (
                INDEX_TYPE_HASHED,
                INDEX_TYPE_2DSPHERE,
                INDEX_TYPE_2D,
                INDEX_TYPE_TEXT,
            ):
                value = value_str
            else:
                try:
                    value = int(value_str)
                except Exception:
                    value = value_str
            keys.append((field, value))
        return keys

    def _get_index_options(self) -> dict[str, Any]:
        """Extract index options from dialog fields, minimizing cognitive complexity."""
        options: dict[str, Any] = {}
        # Use a tuple of (attribute, option_name, type, parse_func)
        option_fields = [
            ("unique_checkbox", "unique", bool, lambda w: w.isChecked()),
            ("sparse_checkbox", "sparse", bool, lambda w: w.isChecked()),
            ("hidden_checkbox", "hidden", bool, lambda w: w.isChecked()),
            (
                "ttl_checkbox",
                "expireAfterSeconds",
                int,
                lambda w: (
                    int(w.text()) if w.text().isdigit() and int(w.text()) > 0 else None
                ),
            ),
            (
                "partial_checkbox",
                "partialFilterExpression",
                dict,
                lambda w: (
                    json.loads(w.toPlainText()) if w.toPlainText().strip() else None
                ),
            ),
        ]
        for attr, opt_name, typ, parse_func in option_fields:
            widget = getattr(self, attr, None)
            if widget:
                try:
                    val = parse_func(widget)
                    if val is not None and isinstance(val, typ):
                        options[opt_name] = val
                except Exception:
                    pass
        return options

    def _get_index_option_value(self, k: str, v: Any) -> Any:
        if k in ("unique", "sparse", "hidden") and isinstance(v, bool):
            return v
        if k == "expireAfterSeconds" and isinstance(v, int):
            return v
        if k == "partialFilterExpression" and isinstance(v, dict):
            return v
        return None

    def get_index_data(self, /) -> dict | None:
        # Refactored to reduce cognitive complexity
        keys = self._get_index_keys()
        options = self._get_index_options()
        result: dict[str, Any] = {
            "name": self.name_input.text(),
            "key": keys,
        }
        for k, v in options.items():
            val = self._get_index_option_value(k, v)
            if val is not None:
                result[k] = val
        return result
