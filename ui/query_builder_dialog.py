"""
Query Builder Dialog for MongoDB queries.
A popup dialog that provides a visual interface for building MongoDB queries.
"""

import json
from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# Constants for operators
OP_EQUAL = "="
OP_NOT_EQUAL = "!="
OP_GREATER = ">"
OP_GREATER_EQUAL = ">="
OP_LESS = "<"
OP_LESS_EQUAL = "<="
OP_CONTAINS = "contains"
OP_STARTS_WITH = "starts with"

OPERATORS = [
    OP_EQUAL,
    OP_NOT_EQUAL,
    OP_GREATER,
    OP_GREATER_EQUAL,
    OP_LESS,
    OP_LESS_EQUAL,
    OP_CONTAINS,
    OP_STARTS_WITH,
]


class ConditionWidget(QWidget):
    """A widget representing a single query condition with field, operator, and value."""

    removed = pyqtSignal()  # Signal emitted when condition is removed

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.setObjectName("conditionWidget")
        self._setup_ui()
        self.setMinimumHeight(60)

        self.setStyleSheet(
            """
            QWidget#conditionWidget {
                background-color: #505050;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 8px;
                margin: 4px 2px;
            }
            QLabel {
                color: #ddd;
                font-size: 11px;
                font-weight: bold;
                padding-bottom: 3px;
            }
            QComboBox, QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px;
                min-height: 28px;
                font-size: 12px;
            }
            QComboBox {
                min-width: 120px;
            }
            QComboBox:hover, QLineEdit:focus {
                border-color: #4a9eff;
                background-color: #3a3a3a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #aaa;
                margin-right: 5px;
            }
        """
        )

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Field selector with label
        field_container = QWidget()
        field_layout = QVBoxLayout(field_container)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(4)

        field_label = QLabel("Field")
        field_layout.addWidget(field_label)

        self.field_combo = QComboBox()
        self.field_combo.addItems(self.fields)
        self.field_combo.setMinimumWidth(150)
        field_layout.addWidget(self.field_combo)
        layout.addWidget(field_container, stretch=2)

        # Operator selector with label
        op_container = QWidget()
        op_layout = QVBoxLayout(op_container)
        op_layout.setContentsMargins(0, 0, 0, 0)
        op_layout.setSpacing(4)

        op_label = QLabel("Operator")
        op_layout.addWidget(op_label)

        self.operator_combo = QComboBox()
        self.operator_combo.addItems(OPERATORS)
        self.operator_combo.setFixedWidth(100)
        op_layout.addWidget(self.operator_combo)
        layout.addWidget(op_container)

        # Value input with label
        value_container = QWidget()
        value_layout = QVBoxLayout(value_container)
        value_layout.setContentsMargins(0, 0, 0, 0)
        value_layout.setSpacing(4)

        value_label = QLabel("Value")
        value_layout.addWidget(value_label)

        self.value_input = QLineEdit()
        self.value_input.setMinimumWidth(150)
        self.value_input.setPlaceholderText("Enter value...")
        value_layout.addWidget(self.value_input)
        layout.addWidget(value_container, stretch=2)

        # Remove button
        remove_container = QWidget()
        remove_layout = QVBoxLayout(remove_container)
        remove_layout.setContentsMargins(0, 0, 0, 0)
        remove_layout.setSpacing(4)

        # Empty label for spacing
        remove_label = QLabel("")
        remove_layout.addWidget(remove_label)

        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(35)
        remove_btn.setFixedHeight(35)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border: none;
                border-radius: 17px;
            }
            QPushButton:hover {
                background-color: #c62828;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """
        )
        remove_btn.clicked.connect(self.removed.emit)
        remove_layout.addWidget(remove_btn)
        layout.addWidget(remove_container)

    def get_condition(self) -> dict[str, Any]:
        """Get the condition as a MongoDB query dict."""
        field = self.field_combo.currentText()
        operator = self.operator_combo.currentText()
        value_text = self.value_input.text().strip()

        if not value_text:
            return {}

        # Convert value to appropriate type
        try:
            value: int | float | str = int(value_text)
        except ValueError:
            try:
                value = float(value_text)
            except ValueError:
                # Keep as string
                value = value_text

        # Map operators to MongoDB syntax
        operator_map = {
            OP_EQUAL: "$eq",
            OP_NOT_EQUAL: "$ne",
            OP_GREATER: "$gt",
            OP_GREATER_EQUAL: "$gte",
            OP_LESS: "$lt",
            OP_LESS_EQUAL: "$lte",
            OP_CONTAINS: "$regex",
            OP_STARTS_WITH: "$regex",
        }

        mongo_op = operator_map.get(operator, "$eq")

        # Handle regex operators
        if operator == OP_CONTAINS:
            value = f".*{value}.*"
        elif operator == OP_STARTS_WITH:
            value = f"^{value}"

        return {field: {mongo_op: value}}


class LogicalOperatorWidget(QWidget):
    """Widget for selecting AND/OR logical operators between conditions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.setMinimumHeight(30)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["AND", "OR"])
        self.operator_combo.setFixedWidth(80)
        self.operator_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #4a9eff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox:hover {
                background-color: #357abd;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid white;
                margin-right: 5px;
            }
        """
        )
        layout.addWidget(self.operator_combo)

    def get_operator(self) -> str:
        """Get the MongoDB operator for the current selection."""
        operator_map = {"AND": "$and", "OR": "$or"}
        return operator_map[self.operator_combo.currentText()]


class QueryBuilderDialog(QDialog):
    """
    Dialog for building MongoDB queries visually.
    """

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.conditions: list[ConditionWidget] = []
        self.operators: list[LogicalOperatorWidget] = []
        self.built_query = ""

        self.setWindowTitle("MongoDB Query Builder")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(700, 500)

        self._setup_ui()
        self.add_condition()  # Start with one condition

    def _setup_ui(self) -> None:
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title
        title_label = QLabel("Build MongoDB Query")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #333; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Create conditions to build your MongoDB query. Click 'Add Condition' to add more criteria."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)

        # Add Condition button
        self.add_btn = QPushButton("+ Add Condition")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_condition)
        self.add_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a9eff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2565a3;
            }
        """
        )
        main_layout.addWidget(self.add_btn)

        # Scroll area for conditions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background-color: #f5f5f5;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
        """
        )

        # Conditions container
        self.conditions_widget = QWidget()
        self.conditions_layout = QVBoxLayout(self.conditions_widget)
        self.conditions_layout.setContentsMargins(10, 10, 10, 10)
        self.conditions_layout.setSpacing(8)
        self.conditions_layout.addStretch()

        scroll.setWidget(self.conditions_widget)
        main_layout.addWidget(scroll, stretch=1)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Clear All button
        clear_btn = QPushButton("Clear All")
        clear_btn.setMinimumHeight(40)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #c62828;
            }
        """
        )
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #757575;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """
        )
        button_layout.addWidget(cancel_btn)

        # Build Query button
        self.build_btn = QPushButton("Build Query")
        self.build_btn.setMinimumHeight(40)
        self.build_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.build_btn.clicked.connect(self.build_and_accept)
        self.build_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """
        )
        button_layout.addWidget(self.build_btn)

        main_layout.addLayout(button_layout)

        # Set dialog style
        self.setStyleSheet(
            """
            QDialog {
                background-color: white;
            }
        """
        )

    def add_condition(self) -> None:
        """Add a new condition widget to the builder."""
        # Add logical operator if not the first condition
        if self.conditions:
            operator = LogicalOperatorWidget()
            self.operators.append(operator)
            # Insert before the stretch
            self.conditions_layout.insertWidget(
                self.conditions_layout.count() - 1, operator
            )

        # Add new condition
        condition = ConditionWidget(self.fields)
        condition.removed.connect(lambda: self.remove_condition(condition))
        self.conditions.append(condition)
        # Insert before the stretch
        self.conditions_layout.insertWidget(
            self.conditions_layout.count() - 1, condition
        )

        # Update layout
        self.conditions_widget.updateGeometry()

    def remove_condition(self, condition: ConditionWidget) -> None:
        """Remove a condition and its associated operator."""
        if len(self.conditions) <= 1:
            return  # Don't remove the last condition

        idx = self.conditions.index(condition)

        # Remove operator if not the last condition
        if idx < len(self.conditions) - 1 and self.operators:
            operator = self.operators.pop(idx)
            operator.setParent(None)
            operator.deleteLater()
        # Remove operator before condition if not the first condition
        elif idx > 0 and self.operators:
            operator = self.operators.pop(idx - 1)
            operator.setParent(None)
            operator.deleteLater()

        # Remove and delete the condition
        self.conditions.remove(condition)
        condition.setParent(None)
        condition.deleteLater()

        # Update layout
        self.conditions_widget.updateGeometry()

    def clear_all(self) -> None:
        """Clear all conditions and start fresh."""
        # Remove all conditions and operators
        for condition in self.conditions[:]:
            condition.setParent(None)
            condition.deleteLater()
        for operator in self.operators[:]:
            operator.setParent(None)
            operator.deleteLater()

        self.conditions.clear()
        self.operators.clear()

        # Add one empty condition
        self.add_condition()

    def build_and_accept(self) -> None:
        """Build the query and accept the dialog."""
        query = self.build_query()
        if query:
            self.built_query = query
            self.accept()

    def build_query(self) -> str:
        """Build and return the MongoDB query string."""
        if not self.conditions:
            return "{}"

        # Get all valid conditions (non-empty)
        valid_conditions = []
        for condition in self.conditions:
            cond_dict = condition.get_condition()
            if cond_dict:  # Only add non-empty conditions
                valid_conditions.append(cond_dict)

        if not valid_conditions:
            return "{}"

        # Single condition case
        if len(valid_conditions) == 1:
            return json.dumps(valid_conditions[0])

        # Multiple conditions case
        if not self.operators:
            # If no operators but multiple conditions, default to AND
            query = {"$and": valid_conditions}
        else:
            current_operator = self.operators[0].get_operator()
            query = {current_operator: valid_conditions}

        # Convert to valid JSON string
        return json.dumps(query)

    def get_built_query(self) -> str:
        """Get the built query string."""
        return self.built_query
