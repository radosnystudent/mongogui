import json
from typing import Any

from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,  # <-- add QWidget for type annotation
)

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
    def __init__(self, indexes: list[dict], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage Indexes")
        self.setMinimumSize(700, 400)
        self.indexes = indexes
        self.selected_index_name: str | None = None
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Keys", "Unique"])
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setEditTriggers(self.table.NoEditTriggers)
        self.load_indexes()
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Index")
        self.edit_btn = QPushButton("Edit Index")
        self.remove_btn = QPushButton("Remove Index")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        self.add_btn.clicked.connect(self.add_index_dialog)
        self.edit_btn.clicked.connect(self.edit_index_dialog)
        self.remove_btn.clicked.connect(self.remove_index)
        self.table.cellClicked.connect(self.on_table_click)

    def load_indexes(self, /) -> None:
        # Show all indexes, including default ones like _id_
        self.table.setRowCount(len(self.indexes))
        for i, idx in enumerate(self.indexes):
            self.table.setItem(i, 0, QTableWidgetItem(idx.get("name", "")))
            self.table.setItem(i, 1, QTableWidgetItem(json.dumps(idx.get("key", []))))
            self.table.setItem(i, 2, QTableWidgetItem(str(idx.get("unique", False))))

    def on_table_click(self, row: int, col: int, /) -> None:
        item = self.table.item(row, 0)
        if item is not None:
            self.selected_index_name = item.text()
        else:
            self.selected_index_name = None

    def add_index_dialog(self, /) -> None:
        dlg = IndexEditDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self.accepted_data = dlg.get_index_data()
            self.accept()  # Use accept() so QDialog.Accepted is returned

    def edit_index_dialog(self, /) -> None:
        if not self.selected_index_name:
            QMessageBox.warning(
                self, "No index selected", "Please select an index to edit."
            )
            return
        idx = next(
            (i for i in self.indexes if i.get("name") == self.selected_index_name), None
        )
        if not idx:
            QMessageBox.warning(self, "Index not found", "Selected index not found.")
            return
        dlg = IndexEditDialog(idx, self)
        if dlg.exec_() == QDialog.Accepted:
            self.accepted_data = dlg.get_index_data()
            self.accept()  # Use accept() so QDialog.Accepted is returned

    def remove_index(self) -> None:
        if not self.selected_index_name:
            QMessageBox.warning(
                self, "No index selected", "Please select an index to remove."
            )
            return
        self.done(4)  # Custom code for remove
        self.selected_index_name = None  # Clear selection after removal

    def get_selected_index_name(self) -> str | None:
        return self.selected_index_name

    def get_index_data(self) -> dict | None:
        return getattr(self, "accepted_data", None)


class IndexEditDialog(QDialog):
    def __init__(
        self, index: dict | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Index" if index else "Add Index")
        self.setMinimumSize(420, 400)  # Keep compact width
        self.index = index or {}
        self.init_ui()

    def init_ui(self, /) -> None:
        layout = QVBoxLayout(self)
        # Index name
        layout.addWidget(QLabel("Index name:"))
        self.name_edit = QLineEdit(self)
        if self.index:
            self.name_edit.setText(self.index.get("name", ""))
        layout.addWidget(self.name_edit)

        # Tabs: Fields, Options
        from PyQt5.QtWidgets import (
            QCheckBox,
            QHBoxLayout,
            QPushButton,
            QTableWidget,
            QTabWidget,
            QWidget,
        )

        self.tabs = QTabWidget(self)
        # --- Fields tab ---
        self.fields_tab = QWidget()
        fields_layout = QVBoxLayout(self.fields_tab)
        # Indexed fields table
        self.fields_table = QTableWidget(self.fields_tab)
        self.fields_table.setColumnCount(2)
        self.fields_table.setHorizontalHeaderLabels(["Field name", "Index type"])
        self.fields_table.setEditTriggers(QTableWidget.NoEditTriggers)
        fields_layout.addWidget(self.fields_table)
        # Add field controls
        add_field_layout = QHBoxLayout()
        self.field_name_edit = QLineEdit(self.fields_tab)
        self.index_type_combo = QComboBox(self.fields_tab)
        self.index_type_combo.addItems(INDEX_TYPE_CHOICES)
        add_field_layout.addWidget(self.field_name_edit)
        add_field_layout.addWidget(self.index_type_combo)
        self.add_field_btn = QPushButton("Add field", self.fields_tab)
        self.remove_field_btn = QPushButton("Remove field", self.fields_tab)
        add_field_layout.addWidget(self.add_field_btn)
        add_field_layout.addWidget(self.remove_field_btn)
        fields_layout.addLayout(add_field_layout)
        self.tabs.addTab(self.fields_tab, "Fields")
        # --- Options tab ---
        self.options_tab = QWidget()
        options_layout = QVBoxLayout(self.options_tab)
        options_layout.setSpacing(16)  # Add more space between options
        # Unique
        self.unique_checkbox = QCheckBox("Unique", self.options_tab)
        options_layout.addWidget(self.unique_checkbox)
        options_layout.addWidget(
            QLabel(
                "Prevents the insertion of documents where the index key(s) match(es) an already existing value in the collection.\nOften combined with the sparse option.",
                self.options_tab,
            )
        )
        # Spacer
        options_layout.addSpacing(8)
        # Sparse
        self.sparse_checkbox = QCheckBox("Sparse", self.options_tab)
        options_layout.addWidget(self.sparse_checkbox)
        options_layout.addWidget(
            QLabel(
                "Omit references to documents that don't include the indexed field.\nFor fields that are only present in some documents. They may provide significant space savings.",
                self.options_tab,
            )
        )
        options_layout.addSpacing(8)
        # Hidden
        self.hidden_checkbox = QCheckBox("Hidden", self.options_tab)
        options_layout.addWidget(self.hidden_checkbox)
        options_layout.addWidget(
            QLabel(
                "This index becomes invisible to the query planner and can't be used to support a query.\nAvailable only in MongoDB 4.4 servers and newer.",
                self.options_tab,
            )
        )
        options_layout.addSpacing(8)
        # TTL
        self.ttl_checkbox = QCheckBox("TTL", self.options_tab)
        options_layout.addWidget(self.ttl_checkbox)
        ttl_row = QHBoxLayout()
        ttl_row.setSpacing(4)
        ttl_row.setContentsMargins(0, 0, 0, 0)
        ttl_row.addWidget(QLabel("Expire after", self.options_tab))
        self.ttl_seconds_edit = QLineEdit(self.options_tab)
        self.ttl_seconds_edit.setPlaceholderText("sec")
        self.ttl_seconds_edit.setMaximumWidth(60)
        ttl_row.addWidget(self.ttl_seconds_edit)
        ttl_row.addStretch(1)
        options_layout.addLayout(ttl_row)
        options_layout.addWidget(
            QLabel(
                "A special type of index that MongoDB can use to automatically remove documents from a\ncollection after a certain amount of time. The indexed field must be a date type.",
                self.options_tab,
            )
        )
        options_layout.addSpacing(8)
        # Partial
        self.partial_checkbox = QCheckBox("Partial", self.options_tab)
        options_layout.addWidget(self.partial_checkbox)
        options_layout.addWidget(
            QLabel(
                "Only index the documents in a collection that meet the filter expression entered below:",
                self.options_tab,
            )
        )
        from PyQt5.QtWidgets import QTextEdit

        self.partial_filter_edit = QTextEdit(self.options_tab)
        self.partial_filter_edit.setPlainText("{}")
        options_layout.addWidget(self.partial_filter_edit)
        self.options_tab.setLayout(options_layout)
        self.tabs.addTab(self.options_tab, "Options")
        layout.addWidget(self.tabs)
        # Create in background
        self.background_checkbox = QCheckBox("Create in background", self)
        layout.addWidget(self.background_checkbox)
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        # Populate fields if editing
        self._populate_fields_table()
        self.add_field_btn.clicked.connect(self._add_field)
        self.remove_field_btn.clicked.connect(self._remove_field)

    def _populate_fields_table(self) -> None:
        self.fields_table.setRowCount(0)
        keys = self.index.get("key", []) if self.index else []
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

    def _add_field(self) -> None:
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

    def _remove_field(self) -> None:
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
            "name": self.name_edit.text(),
            "key": keys,
        }
        for k, v in options.items():
            val = self._get_index_option_value(k, v)
            if val is not None:
                result[k] = val
        return result
