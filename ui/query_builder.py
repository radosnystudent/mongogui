"""
Query Builder GUI component for MongoDB queries.
Provides a visual interface for building MongoDB queries with conditions and operators.
"""

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QResizeEvent, QShowEvent
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ConditionWidget(QWidget):
    """A widget representing a single query condition with field, operator, and value."""

    removed = pyqtSignal()  # Signal emitted when condition is removed

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.setObjectName("conditionWidget")
        self._setup_ui()
        self.setMinimumHeight(50)  # Reduced height for more compact layout

        self.setStyleSheet(
            """
            QWidget#conditionWidget {
                background-color: #505050;
                border: 1px solid #666;
                border-radius: 3px;
                padding: 5px;
                margin: 2px;
            }
            QLabel {
                color: #ddd;
                font-size: 11px;
                padding-bottom: 2px;
            }
            QComboBox, QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                min-height: 25px;
            }
            QComboBox {
                min-width: 120px;
            }
            QComboBox:hover, QLineEdit:focus {
                border-color: #4a9eff;
            }
        """
        )

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

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
        self.operator_combo.addItems(["=", "!=", ">", ">=", "<", "<="])
        self.operator_combo.setFixedWidth(80)
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

        # Remove button (aligned with input fields)
        remove_container = QWidget()
        remove_layout = QVBoxLayout(remove_container)
        remove_layout.setContentsMargins(0, 0, 0, 0)
        remove_layout.setSpacing(4)

        # Empty label for spacing
        remove_label = QLabel("")
        remove_layout.addWidget(remove_label)

        remove_btn = QPushButton("×")
        remove_btn.setFixedWidth(30)
        remove_btn.setFixedHeight(30)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #404040;
                color: #999;
                font-weight: bold;
                font-size: 16px;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c62828;
                color: white;
                border-color: #c62828;
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
        value_text = self.value_input.text()

        # Convert value to appropriate type (basic implementation)
        try:
            value: int | float | str = int(value_text)
        except ValueError:
            try:
                value = float(value_text)
            except ValueError:
                # Keep as string if not a number
                value = value_text

        # Map operators to MongoDB syntax
        operator_map = {
            "=": "$eq",
            "!=": "$ne",
            ">": "$gt",
            ">=": "$gte",
            "<": "$lt",
            "<=": "$lte",
        }

        return {field: {operator_map[operator]: value}}


class LogicalOperatorWidget(QWidget):
    """Widget for selecting AND/OR logical operators between conditions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self.setMinimumHeight(25)

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["AND", "OR"])
        self.operator_combo.setFixedWidth(80)
        layout.addWidget(self.operator_combo)
        layout.addStretch()  # Push operator to the left

    def get_operator(self) -> str:
        """Get the MongoDB operator for the current selection."""
        operator_map = {"AND": "$and", "OR": "$or"}
        return operator_map[self.operator_combo.currentText()]


class QueryBuilder(QWidget):
    """
    Main query builder widget that allows users to construct MongoDB queries
    using a visual interface with conditions and logical operators.
    """

    query_built = pyqtSignal(str)  # Signal emitted when query is built

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.conditions: list[ConditionWidget] = []
        self.operators: list[LogicalOperatorWidget] = []

        # Set up the widget
        self.setObjectName("queryBuilderMain")
        self.setMinimumHeight(200)  # Reduced from 250 to match container
        self.setMinimumWidth(400)

        # Initialize UI
        self._setup_ui()

        # Add initial condition
        self.add_condition()

        # Force update to ensure visibility
        self.updateGeometry()
        self.update()
        self.show()  # Explicitly show the widget

    def _setup_ui(self) -> None:
        """Initialize the UI components."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            0, 0, 0, 0
        )  # Remove margins since container already has padding
        main_layout.setSpacing(0)

        # Container widget for all builder content
        content = QWidget(self)
        content.setObjectName("queryBuilderContent")
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)  # Move margins to content
        content_layout.setSpacing(10)

        # Add Condition button at the top
        self.add_btn = QPushButton("+ Add Condition")
        self.add_btn.setObjectName("addConditionButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setMinimumHeight(35)
        self.add_btn.setVisible(True)  # Explicitly set visible
        self.add_btn.clicked.connect(self.add_condition)
        content_layout.addWidget(self.add_btn)

        # Conditions container (direct, no scroll area for now)
        self.conditions_container = QWidget()
        self.conditions_container.setObjectName("conditionsContainer")
        self.conditions_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.conditions_container.setMinimumHeight(120)
        self.conditions_layout = QVBoxLayout(self.conditions_container)
        self.conditions_layout.setContentsMargins(8, 8, 8, 8)
        self.conditions_layout.setSpacing(8)
        self.conditions_layout.addStretch()

        content_layout.addWidget(self.conditions_container, stretch=1)

        # Build Query button at the bottom
        self.build_btn = QPushButton("Build Query")
        self.build_btn.setObjectName("buildQueryButton")
        self.build_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.build_btn.setMinimumHeight(35)
        self.build_btn.setVisible(True)  # Explicitly set visible
        self.build_btn.clicked.connect(self.build_query)
        content_layout.addWidget(self.build_btn)

        # Add content to main layout
        self.content = content  # Store reference
        main_layout.addWidget(content)

        # Force everything to be visible
        content.setVisible(True)
        content.show()
        self.add_btn.setVisible(True)
        self.add_btn.show()
        self.build_btn.setVisible(True)
        self.build_btn.show()
        self.conditions_container.setVisible(True)
        self.conditions_container.show()

        # Set stylesheet
        self.setStyleSheet(
            """
            QWidget#queryBuilderMain {
                background-color: #353535;
                border: 2px solid #4a9eff;
                border-radius: 4px;
            }
            QWidget#queryBuilderContent {
                background-color: transparent;
                min-width: 100%;
            }
            QScrollArea#conditionsScroll {
                background-color: #2a2a2a;
                border: 1px solid #555;
                border-radius: 3px;
                min-height: 120px;
            }
            QWidget#conditionsContainer {
                background-color: #2a2a2a;
                border-radius: 3px;
                min-height: 120px;
                padding: 5px;
            }
            QPushButton#addConditionButton {
                background-color: #4a9eff;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton#addConditionButton:hover {
                background-color: #357abd;
            }
            QPushButton#buildQueryButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-size: 13px;
                min-height: 35px;
            }
            QPushButton#buildQueryButton:hover {
                background-color: #218838;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
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

        # Force layout update
        self.conditions_container.updateGeometry()
        self.update()

    def remove_condition(self, condition: ConditionWidget) -> None:
        """Remove a condition and its associated operator."""
        idx = self.conditions.index(condition)

        # Remove operator if not the last condition
        if idx < len(self.conditions) - 1 and self.operators:
            operator = self.operators.pop(idx)
            operator.deleteLater()
        # Remove operator before condition if not the first condition
        elif idx > 0 and self.operators:
            operator = self.operators.pop(idx - 1)
            operator.deleteLater()

        # Remove and delete the condition
        self.conditions.remove(condition)
        condition.deleteLater()

    def build_query(self) -> None:
        """Build and emit the MongoDB query string."""
        if not self.conditions:
            self.query_built.emit("{}")
            return

        # Single condition case
        if len(self.conditions) == 1:
            query = self.conditions[0].get_condition()
            self.query_built.emit(str(query))
            return

        # Multiple conditions case
        current_operator = self.operators[0].get_operator()
        query = {current_operator: []}

        for i, condition in enumerate(self.conditions):
            # Add condition
            query[current_operator].append(condition.get_condition())

            # Check if operator changes
            if i < len(self.operators):
                next_operator = self.operators[i].get_operator()
                if next_operator != current_operator:
                    # Create new operator group and update current
                    new_query = {next_operator: [query]}
                    query = new_query
                    current_operator = next_operator

        self.query_built.emit(str(query))

    def showEvent(self, a0: QShowEvent | None) -> None:
        """Override showEvent to ensure all child widgets are visible."""
        super().showEvent(a0)

        # Ensure buttons are visible
        if hasattr(self, "add_btn"):
            self.add_btn.setVisible(True)
            self.add_btn.show()

        if hasattr(self, "build_btn"):
            self.build_btn.setVisible(True)
            self.build_btn.show()

        # Ensure conditions container is visible
        if hasattr(self, "conditions_container"):
            self.conditions_container.setVisible(True)
            self.conditions_container.show()

        # Ensure all condition widgets are visible
        for condition in self.conditions:
            condition.setVisible(True)
            condition.show()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        """Override resizeEvent to update layout when resized."""
        super().resizeEvent(a0)
        self.updateGeometry()
