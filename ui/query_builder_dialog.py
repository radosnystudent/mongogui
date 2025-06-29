"""
Query Builder Dialog for MongoDB queries.
A popup dialog that provides a visual interface for building MongoDB queries.
"""

import json
import re
import time
from typing import Any, Union

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

# Security constants
MAX_FIELD_NAME_LENGTH = 100
MAX_VALUE_LENGTH = 1000
MAX_REGEX_LENGTH = 200
MAX_QUERY_SIZE = 8192  # 8KB limit for queries
MAX_NESTING_DEPTH = 15
MAX_ARRAY_SIZE = 50
MAX_CONDITIONS_PER_GROUP = 20
REGEX_TIMEOUT_MS = 100  # Maximum time for regex compilation

# UI constants
MIN_DIALOG_WIDTH = 700
MIN_DIALOG_HEIGHT = 500
DEFAULT_DIALOG_WIDTH = 800
DEFAULT_DIALOG_HEIGHT = 600

# Widget limits
MAX_LIMIT_VALUE = 10000
MAX_SKIP_VALUE = 100000

# CSS Style constants
BUTTON_BASE_STYLE = """
QPushButton {{
    background-color: {bg_color};
    color: #ddd;
    font-weight: bold;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
}}
QPushButton:hover {{
    background-color: {hover_color};
    border-color: #666;
}}
QPushButton:pressed {{
    background-color: {pressed_color};
}}
"""

COMBO_BASE_STYLE = """
QComboBox {{
    background-color: #333333;
    color: white;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 6px;
    min-height: 28px;
    font-size: 12px;
    min-width: 120px;
}}
QComboBox:hover {{
    border-color: #4a9eff;
    background-color: #3a3a3a;
}}
QComboBox:editable {{
    background-color: #333333;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #aaa;
    margin-right: 5px;
}}
"""


def validate_field_name(field_name: str) -> bool:
    """Validate field name for security and format."""
    if not field_name or len(field_name) > MAX_FIELD_NAME_LENGTH:
        return False

    # Prevent SQL-like injection patterns
    forbidden_patterns = ["'", '"', ";", "--", "/*", "*/", "\\", "eval", "function"]
    field_lower = field_name.lower()
    if any(pattern in field_lower for pattern in forbidden_patterns):
        return False

    # Allow alphanumeric, dots (for nested fields), underscores, and hyphens
    # Must start with letter or underscore
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9._-]*$", field_name):
        return False

    # Prevent excessive dots (nested field limit)
    if field_name.count(".") > 10:
        return False

    return True


def validate_value(value: str | None) -> bool:
    """Validate input value for security."""
    if not isinstance(value, str):
        return False

    if len(value) > MAX_VALUE_LENGTH:
        return False

    # Check for potential injection patterns
    forbidden_patterns = [
        "eval(",
        "function(",
        "javascript:",
        "settimeout",
        "setinterval",
    ]
    value_lower = value.lower()
    if any(pattern in value_lower for pattern in forbidden_patterns):
        return False

    return True


def safe_regex_compile(pattern: str) -> tuple[bool, str]:
    """Safely compile a regex pattern with timeout protection."""
    if len(pattern) > MAX_REGEX_LENGTH:
        return False, "Regex pattern too long"

    try:
        # Use a simple timeout mechanism
        start_time = time.time()
        compiled_regex = re.compile(pattern)
        compile_time = (time.time() - start_time) * 1000

        if compile_time > REGEX_TIMEOUT_MS:
            return False, "Regex compilation timeout"

        # Test the regex with a simple string to catch catastrophic backtracking
        _ = compiled_regex.search("test" * 100)  # Use _ to indicate unused result
        return True, pattern
    except re.error as e:
        return False, f"Invalid regex: {str(e)}"
    except Exception as e:
        return False, f"Regex error: {str(e)}"


def escape_regex_value(value: str) -> str:
    """Safely escape regex special characters."""
    if len(value) > MAX_REGEX_LENGTH:
        # Truncate if too long
        value = value[:MAX_REGEX_LENGTH]

    # Escape regex special characters to prevent injection
    return re.escape(str(value))


# Constants for operators
OP_EQUAL = "="
OP_NOT_EQUAL = "!="
OP_GREATER = ">"
OP_GREATER_EQUAL = ">="
OP_LESS = "<"
OP_LESS_EQUAL = "<="
OP_CONTAINS = "contains"
OP_STARTS_WITH = "starts with"
OP_ENDS_WITH = "ends with"
OP_IN = "in"
OP_NOT_IN = "not in"
OP_EXISTS = "exists"
OP_NOT_EXISTS = "not exists"
OP_REGEX = "regex"

# MongoDB operator constants
MONGO_REGEX = "$regex"

OPERATORS = [
    OP_EQUAL,
    OP_NOT_EQUAL,
    OP_GREATER,
    OP_GREATER_EQUAL,
    OP_LESS,
    OP_LESS_EQUAL,
    OP_CONTAINS,
    OP_STARTS_WITH,
    OP_ENDS_WITH,
    OP_IN,
    OP_NOT_IN,
    OP_EXISTS,
    OP_NOT_EXISTS,
    OP_REGEX,
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
            QComboBox:editable {
                background-color: #333333;
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

        field_label = QLabel("Field (type or select)")
        field_layout.addWidget(field_label)

        self.field_combo = QComboBox()
        self.field_combo.setEditable(True)  # Allow typing custom field names
        self.field_combo.addItems(self.fields)
        self.field_combo.setMinimumWidth(150)
        self.field_combo.setToolTip("Select a field or type a custom field name")
        self.field_combo.setStyleSheet(COMBO_BASE_STYLE)

        # Set placeholder text for the editable field
        line_edit = self.field_combo.lineEdit()
        if line_edit:
            line_edit.setPlaceholderText("Type field name...")
            # Add input validation
            line_edit.textChanged.connect(self._validate_field_input)
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
        self.operator_combo.setStyleSheet(COMBO_BASE_STYLE)
        self.operator_combo.currentTextChanged.connect(self._on_operator_changed)
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
        self.value_input.setPlaceholderText(
            "Enter value (comma-separated for 'in/not in')..."
        )
        self.value_input.textChanged.connect(self._validate_value_input)
        self.value_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px;
                min-height: 28px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
                background-color: #3a3a3a;
            }
        """
        )
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

        remove_btn = QPushButton("Remove")
        remove_btn.setFixedWidth(70)
        remove_btn.setToolTip("Remove this condition")
        remove_btn.clicked.connect(self.removed.emit)
        remove_btn.setStyleSheet(
            BUTTON_BASE_STYLE.format(
                bg_color="#505050", hover_color="#6a4c4c", pressed_color="#5a3c3c"
            )
        )
        remove_layout.addWidget(remove_btn)
        layout.addWidget(remove_container)

    def _validate_field_input(self, text: str) -> None:
        """Validate field input in real-time."""
        line_edit = self.field_combo.lineEdit()
        if line_edit:
            if validate_field_name(text) or not text:
                line_edit.setStyleSheet("")  # Reset to default
            else:
                line_edit.setStyleSheet("QLineEdit { border: 2px solid #ff6b6b; }")

    def _on_operator_changed(self, operator: str) -> None:
        """Handle operator change to update value input placeholder."""
        if operator in [OP_EXISTS, OP_NOT_EXISTS]:
            self.value_input.setPlaceholderText("(no value needed)")
            self.value_input.setEnabled(False)
        elif operator in [OP_IN, OP_NOT_IN]:
            self.value_input.setPlaceholderText("Enter comma-separated values...")
            self.value_input.setEnabled(True)
        else:
            self.value_input.setPlaceholderText("Enter value...")
            self.value_input.setEnabled(True)

    def _validate_value_input(self, text: str) -> None:
        """Validate value input in real-time."""
        if validate_value(text) or not text:
            self.value_input.setStyleSheet(
                """
                QLineEdit {
                    background-color: #333333;
                    color: white;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 6px;
                    min-height: 28px;
                    font-size: 12px;
                }
                QLineEdit:focus {
                    border-color: #4a9eff;
                    background-color: #3a3a3a;
                }
            """
            )
        else:
            self.value_input.setStyleSheet(
                """
                QLineEdit {
                    background-color: #333333;
                    color: white;
                    border: 2px solid #ff6b6b;
                    border-radius: 3px;
                    padding: 6px;
                    min-height: 28px;
                    font-size: 12px;
                }
            """
            )

    def _validate_field_name(self, field_name: str) -> bool:
        """Validate field name for security and format."""
        return validate_field_name(field_name)

    def _validate_value(self, value: str) -> bool:
        """Validate input value for security."""
        return validate_value(value)

    def _escape_regex_value(self, value: str) -> str:
        """Safely escape regex special characters."""
        return escape_regex_value(value)

    def get_condition(self) -> dict[str, Any]:
        """Get the condition as a MongoDB query dict with enhanced validation."""
        try:
            # Get field name from either selected item or typed text
            field = self.field_combo.currentText().strip()
            operator = self.operator_combo.currentText()
            value_text = self.value_input.text().strip()

            # Validate field name for security
            if not field or not self._validate_field_name(field):
                return {}

            # Handle existence operators that don't need values
            if operator in [OP_EXISTS, OP_NOT_EXISTS]:
                return {field: {"$exists": operator == OP_EXISTS}}

            # For other operators, require a value
            if not value_text:
                return {}

            # Validate value length
            if not self._validate_value(value_text):
                return {}

            # Convert value to appropriate type
            if operator not in [OP_IN, OP_NOT_IN]:
                value: int | float | str | list[
                    int | float | str
                ] = self._convert_single_value(value_text)
            else:
                value = self._convert_array_values(value_text)
                # Validate array size
                if isinstance(value, list) and len(value) > MAX_ARRAY_SIZE:
                    return {}

            # Get MongoDB operator
            mongo_op = self._get_mongo_operator(operator)

            # Handle regex operators with proper validation
            if operator in [OP_CONTAINS, OP_STARTS_WITH, OP_ENDS_WITH, OP_REGEX]:
                regex_result = self._build_regex_value(operator, str(value))
                if regex_result is None:
                    return {}  # Invalid regex
                value = regex_result

            return {field: {mongo_op: value}}

        except Exception:
            # Return empty dict on any error to prevent crashes
            return {}

    def _convert_single_value(self, value_text: str) -> int | float | str:
        """Convert a single value to appropriate type."""
        try:
            return int(value_text)
        except ValueError:
            try:
                return float(value_text)
            except ValueError:
                return value_text

    def _convert_array_values(self, value_text: str) -> list[int | float | str]:
        """Convert comma-separated values to a list with type conversion."""
        value_list = [v.strip() for v in value_text.split(",") if v.strip()]
        converted_values: list[int | float | str] = []

        for v in value_list:
            if not self._validate_value(v):
                continue  # Skip invalid values
            converted_values.append(self._convert_single_value(v))

        return converted_values

    def _get_mongo_operator(self, operator: str) -> str:
        """Get the MongoDB operator for the given UI operator."""
        operator_map = {
            OP_EQUAL: "$eq",
            OP_NOT_EQUAL: "$ne",
            OP_GREATER: "$gt",
            OP_GREATER_EQUAL: "$gte",
            OP_LESS: "$lt",
            OP_LESS_EQUAL: "$lte",
            OP_CONTAINS: MONGO_REGEX,
            OP_STARTS_WITH: MONGO_REGEX,
            OP_ENDS_WITH: MONGO_REGEX,
            OP_IN: "$in",
            OP_NOT_IN: "$nin",
            OP_REGEX: MONGO_REGEX,
        }
        return operator_map.get(operator, "$eq")

    def _build_regex_value(self, operator: str, value: str) -> str | None:
        """Build a safe regex value for the given operator."""
        try:
            if operator == OP_CONTAINS:
                escaped_value = self._escape_regex_value(value)
                pattern = f".*{escaped_value}.*"
            elif operator == OP_STARTS_WITH:
                escaped_value = self._escape_regex_value(value)
                pattern = f"^{escaped_value}"
            elif operator == OP_ENDS_WITH:
                escaped_value = self._escape_regex_value(value)
                pattern = f"{escaped_value}$"
            elif operator == OP_REGEX:
                # For raw regex, validate it's safe
                is_valid, pattern = safe_regex_compile(value)
                if not is_valid:
                    # If invalid regex, escape it
                    pattern = self._escape_regex_value(value)
            else:
                pattern = self._escape_regex_value(value)

            # Final validation of the pattern
            is_valid, validated_pattern = safe_regex_compile(pattern)
            return validated_pattern if is_valid else None

        except Exception:
            return None


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
                background-color: #404040;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                font-weight: bold;
                font-size: 12px;
            }
            QComboBox:hover {
                background-color: #505050;
                border-color: #666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ddd;
                margin-right: 5px;
            }
        """
        )
        layout.addWidget(self.operator_combo)

    def get_operator(self) -> str:
        """Get the MongoDB operator for the current selection."""
        operator_map = {"AND": "$and", "OR": "$or"}
        return operator_map[self.operator_combo.currentText()]


class ConditionGroup(QWidget):
    """A widget that groups multiple conditions with logical operators."""

    removed = pyqtSignal()

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.conditions: list[ConditionWidget | ConditionGroup] = []
        self.operators: list[LogicalOperatorWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the group UI with visual grouping."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Header with group controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Group label
        group_label = QLabel("Group")
        group_label.setStyleSheet(
            """
            QLabel {
                color: #bbb;
                font-weight: bold;
                font-size: 11px;
                background-color: #404040;
                padding: 2px 6px;
                border-radius: 3px;
            }
        """
        )
        header_layout.addWidget(group_label)

        # Add condition button
        add_condition_btn = QPushButton("+ Condition")
        add_condition_btn.setFixedSize(80, 24)
        add_condition_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a6741;
                color: #ddd;
                font-size: 10px;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QPushButton:hover {
                background-color: #5a7751;
            }
        """
        )
        add_condition_btn.clicked.connect(self.add_condition)
        header_layout.addWidget(add_condition_btn)

        # Add group button
        add_group_btn = QPushButton("+ Group")
        add_group_btn.setFixedSize(70, 24)
        add_group_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #6a4a41;
                color: #ddd;
                font-size: 10px;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QPushButton:hover {
                background-color: #7a5a51;
            }
        """
        )
        add_group_btn.clicked.connect(self.add_group)
        header_layout.addWidget(add_group_btn)

        header_layout.addStretch()

        # Remove group button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setToolTip("Remove this group")
        remove_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #5a3c3c;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #6a4c4c;
            }
        """
        )
        remove_btn.clicked.connect(self.removed.emit)
        header_layout.addWidget(remove_btn)

        main_layout.addLayout(header_layout)

        # Container for conditions with visual grouping
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(
            15, 8, 8, 8
        )  # Left indent for visual grouping
        self.content_layout.setSpacing(6)
        self.content_layout.addStretch()

        # Style the content area to show grouping
        self.content_widget.setStyleSheet(
            """
            QWidget {
                background-color: #353535;
                border-left: 3px solid #666;
                border-radius: 4px;
            }
        """
        )

        main_layout.addWidget(self.content_widget)

        # Start with one condition
        self.add_condition()

    def add_condition(self) -> None:
        """Add a new condition to this group."""
        # Limit the number of conditions per group
        if len(self.conditions) >= MAX_CONDITIONS_PER_GROUP:
            return

        # Add logical operator if not the first item
        if self.conditions:
            operator = LogicalOperatorWidget()
            self.operators.append(operator)
            self.content_layout.insertWidget(self.content_layout.count() - 1, operator)

        # Add new condition
        condition = ConditionWidget(self.fields)
        condition.removed.connect(lambda: self.remove_item(condition))
        self.conditions.append(condition)
        self.content_layout.insertWidget(self.content_layout.count() - 1, condition)

        self.content_widget.updateGeometry()

    def add_group(self) -> None:
        """Add a new nested group."""
        # Limit the number of items per group
        if len(self.conditions) >= MAX_CONDITIONS_PER_GROUP:
            return

        # Add logical operator if not the first item
        if self.conditions:
            operator = LogicalOperatorWidget()
            self.operators.append(operator)
            self.content_layout.insertWidget(self.content_layout.count() - 1, operator)

        # Add new group
        group = ConditionGroup(self.fields)
        group.removed.connect(lambda: self.remove_item(group))
        self.conditions.append(group)
        self.content_layout.insertWidget(self.content_layout.count() - 1, group)

        self.content_widget.updateGeometry()

    def remove_item(self, item: Union[ConditionWidget, "ConditionGroup"]) -> None:
        """Remove a condition or group and its associated operator."""
        if len(self.conditions) <= 1:
            return  # Don't remove the last item

        idx = self.conditions.index(item)

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

        # Remove and delete the item
        self.conditions.remove(item)
        item.setParent(None)
        item.deleteLater()

        self.content_widget.updateGeometry()

    def get_conditions(self) -> dict[str, Any]:
        """Get all conditions in this group as a MongoDB query dict."""
        if not self.conditions:
            return {}

        # Get all valid conditions
        valid_conditions = []
        for condition in self.conditions:
            if isinstance(condition, ConditionWidget):
                cond_dict = condition.get_condition()
                if cond_dict:
                    valid_conditions.append(cond_dict)
            elif isinstance(condition, ConditionGroup):
                group_dict = condition.get_conditions()
                if group_dict:
                    valid_conditions.append(group_dict)

        if not valid_conditions:
            return {}

        # Single condition case
        if len(valid_conditions) == 1:
            return valid_conditions[0]

        # Multiple conditions case
        if not self.operators:
            # If no operators but multiple conditions, default to AND
            return {"$and": valid_conditions}
        else:
            current_operator = self.operators[0].get_operator()
            return {current_operator: valid_conditions}


class QueryBuilderDialog(QDialog):
    """
    Dialog for building MongoDB queries visually.
    """

    def __init__(self, fields: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields = fields
        self.root_group: ConditionGroup | None = None
        self.built_query = ""

        self.setWindowTitle("MongoDB Query Builder")
        self.setModal(True)
        self.resize(DEFAULT_DIALOG_WIDTH, DEFAULT_DIALOG_HEIGHT)
        self.setMinimumSize(MIN_DIALOG_WIDTH, MIN_DIALOG_HEIGHT)

        self._setup_ui()
        self._create_root_group()  # Start with root group

    def _validate_field_name(self, field_name: str) -> bool:
        """Validate field name for security and format."""
        return validate_field_name(field_name)

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
        title_label.setStyleSheet("color: #ddd; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Create conditions to build your MongoDB query. Use groups to create complex logical structures like (A AND B) OR (C AND D)."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaa; font-size: 12px; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)

        # Add Group button
        self.add_group_btn = QPushButton("+ Add Group")
        self.add_group_btn.setToolTip("Add a new condition group")
        self.add_group_btn.clicked.connect(self.add_group)
        self.add_group_btn.setStyleSheet(
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
            QPushButton:pressed {
                background-color: #353535;
            }
        """
        )
        main_layout.addWidget(self.add_group_btn)

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
        self.groups_widget = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_widget)
        self.groups_layout.setContentsMargins(10, 10, 10, 10)
        self.groups_layout.setSpacing(8)
        self.groups_layout.addStretch()

        scroll.setWidget(self.groups_widget)
        main_layout.addWidget(scroll, stretch=1)

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
        self.sort_field_combo.addItems(
            [""] + self.fields
        )  # Empty option for no sorting
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

        main_layout.addWidget(controls_group)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Clear All button
        clear_btn = QPushButton("Clear All")
        clear_btn.setToolTip("Remove all conditions")
        clear_btn.clicked.connect(self.clear_all)
        clear_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #505050;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #404040;
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
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #404040;
            }
        """
        )
        button_layout.addWidget(cancel_btn)

        # Build Query button
        self.build_btn = QPushButton("Build Query")
        self.build_btn.setToolTip("Build the query and insert into main window")
        self.build_btn.clicked.connect(self.build_and_accept)
        self.build_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a6741;
                color: #ddd;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #5a7751;
                border-color: #666;
            }
            QPushButton:pressed {
                background-color: #3a5731;
            }
        """
        )
        button_layout.addWidget(self.build_btn)

        main_layout.addLayout(button_layout)

        # Set dialog style
        self.setStyleSheet(
            """
            QDialog {
                background-color: #3a3a3a;
                color: #ddd;
            }
        """
        )

    def _create_root_group(self) -> None:
        """Create the initial root group."""
        self.root_group = ConditionGroup(self.fields)
        # Remove the remove button from root group since it's the main group
        remove_btn = self.root_group.findChild(QPushButton)
        if remove_btn and remove_btn.text() == "×":
            remove_btn.setVisible(False)

        self.groups_layout.insertWidget(0, self.root_group)

    def add_group(self) -> None:
        """Add a new top-level group."""
        # If we already have groups, add a logical operator first
        if self.groups_layout.count() > 1:  # > 1 because of the stretch
            operator = LogicalOperatorWidget()
            self.groups_layout.insertWidget(self.groups_layout.count() - 1, operator)

        # Add new group
        group = ConditionGroup(self.fields)
        group.removed.connect(lambda: self.remove_group(group))
        self.groups_layout.insertWidget(self.groups_layout.count() - 1, group)

        self.groups_widget.updateGeometry()

    def remove_group(self, group: ConditionGroup) -> None:
        """Remove a top-level group."""
        # Don't remove if it's the only group
        if self.groups_layout.count() <= 2:  # 1 group + 1 stretch
            return

        group_index = self._find_group_index(group)
        if group_index >= 0:
            self._remove_associated_operator(group_index)
            self._remove_group_widget(group)

        self.groups_widget.updateGeometry()

    def _find_group_index(self, target_group: ConditionGroup) -> int:
        """Find the index of a group in the layout."""
        for i in range(self.groups_layout.count()):
            item = self.groups_layout.itemAt(i)
            if item and item.widget() == target_group:
                return i
        return -1

    def _remove_associated_operator(self, group_index: int) -> None:
        """Remove the logical operator associated with a group."""
        if group_index > 0:
            prev_item = self.groups_layout.itemAt(group_index - 1)
            if prev_item:
                widget = prev_item.widget()
                if widget and isinstance(widget, LogicalOperatorWidget):
                    widget.setParent(None)
                    widget.deleteLater()

    def _remove_group_widget(self, group: ConditionGroup) -> None:
        """Remove the group widget from the layout."""
        group.setParent(None)
        group.deleteLater()

    def clear_all(self) -> None:
        """Clear all groups and start fresh."""
        # Remove all widgets except the stretch
        while self.groups_layout.count() > 1:
            item = self.groups_layout.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    widget.deleteLater()

        # Create a new root group
        self._create_root_group()

    def build_query(self) -> str:
        """Build and return the MongoDB query string."""
        if not self.root_group:
            return "{}"

        all_groups = self._collect_all_groups()

        if not all_groups:
            return "{}"

        # Single group case
        if len(all_groups) == 1:
            return json.dumps(all_groups[0])

        # Multiple groups case
        return self._build_multiple_groups_query(all_groups)

    def _collect_all_groups(self) -> list[dict[str, Any]]:
        """Collect all valid group conditions."""
        all_groups = []

        # Add root group conditions
        if self.root_group:
            root_conditions = self.root_group.get_conditions()
            if root_conditions:
                all_groups.append(root_conditions)

        # Add other top-level groups
        for i in range(self.groups_layout.count()):
            item = self.groups_layout.itemAt(i)
            if item:
                widget = item.widget()
                if (
                    widget
                    and isinstance(widget, ConditionGroup)
                    and widget != self.root_group
                ):
                    group_conditions = widget.get_conditions()
                    if group_conditions:
                        all_groups.append(group_conditions)

        return all_groups

    def _build_multiple_groups_query(self, all_groups: list[dict[str, Any]]) -> str:
        """Build query for multiple groups with operators."""
        operators = self._find_logical_operators()

        # Use first operator found, default to AND
        if operators:
            query = {operators[0]: all_groups}
        else:
            query = {"$and": all_groups}

        return json.dumps(query)

    def _find_logical_operators(self) -> list[str]:
        """Find all logical operators between groups."""
        operators = []
        for i in range(self.groups_layout.count()):
            item = self.groups_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and isinstance(widget, LogicalOperatorWidget):
                    operators.append(widget.get_operator())
        return operators

    def build_and_accept(self) -> None:
        """Build the query and accept the dialog."""
        query = self.build_query()
        if query:
            # Validate the query before accepting
            validation_result = self.validate_query(query)
            if not validation_result["valid"]:
                from PyQt6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self, "Query Validation Error", validation_result["message"]
                )
                return

            self.built_query = query
            self.accept()

    def validate_query(self, query_str: str) -> dict[str, Any]:
        """Validate the built query for common issues and security."""
        try:
            # Check string length to prevent DoS
            if len(query_str) > MAX_QUERY_SIZE:
                return {
                    "valid": False,
                    "message": f"Query exceeds maximum size ({MAX_QUERY_SIZE} chars)",
                }

            # Basic format checks
            if not query_str.strip():
                return {"valid": False, "message": "Query cannot be empty"}

            # Try to parse as JSON with strict parsing
            try:
                query_obj = json.loads(query_str)
            except json.JSONDecodeError as e:
                return {"valid": False, "message": f"Invalid JSON: {str(e)[:100]}"}

            # Basic validation checks
            if not isinstance(query_obj, dict):
                return {"valid": False, "message": "Query must be a JSON object"}

            # Check for empty conditions
            if not query_obj:
                return {"valid": False, "message": "Query cannot be empty"}

            # Validate query structure and operators
            validation_result = self._validate_query_structure(query_obj)
            if not validation_result["valid"]:
                return validation_result

            return {"valid": True, "message": "Query is valid"}

        except Exception as e:
            return {"valid": False, "message": f"Validation error: {str(e)[:100]}"}

    def _validate_query_structure(self, query_obj: dict[str, Any]) -> dict[str, Any]:
        """Validate the structure and operators in the query."""
        try:
            is_valid, error_msg = self._check_query_operators(query_obj)
            if not is_valid:
                return {
                    "valid": False,
                    "message": f"Query validation failed: {error_msg}",
                }

            return {"valid": True, "message": "Structure is valid"}
        except Exception as e:
            return {"valid": False, "message": f"Validation error: {str(e)[:100]}"}

    def _get_valid_mongodb_operators(self) -> set[str]:
        """Get the set of valid MongoDB operators."""
        return {
            "$eq",
            "$ne",
            "$gt",
            "$gte",
            "$lt",
            "$lte",
            "$in",
            "$nin",
            MONGO_REGEX,
            "$exists",
            "$and",
            "$or",
            "$not",
            "$size",
            "$all",
            "$elemMatch",
            "$type",
        }

    def _check_query_operators(self, obj: Any, depth: int = 0) -> tuple[bool, str]:
        """Recursively check query operators and structure."""
        # Prevent excessively deep nesting (DoS protection)
        if depth > MAX_NESTING_DEPTH:
            return False, f"Query nesting exceeds maximum depth ({MAX_NESTING_DEPTH})"

        if isinstance(obj, dict):
            return self._validate_dict_object(obj, depth)
        elif isinstance(obj, list):
            return self._validate_list_object(obj, depth)
        elif isinstance(obj, str):
            return self._validate_string_object(obj)
        elif isinstance(obj, int | float):
            return self._validate_numeric_object(obj)

        return True, ""

    def _validate_dict_object(
        self, obj: dict[str, Any], depth: int
    ) -> tuple[bool, str]:
        """Validate a dictionary object in the query."""
        valid_ops = self._get_valid_mongodb_operators()

        for key, value in obj.items():
            # Validate field names and operators
            if key.startswith("$"):
                if key not in valid_ops:
                    return False, f"Invalid MongoDB operator: {key}"
            else:
                # Validate field name format
                if not validate_field_name(key):
                    return False, f"Invalid field name: {key}"

            is_valid, error_msg = self._check_query_operators(value, depth + 1)
            if not is_valid:
                return False, error_msg

        return True, ""

    def _validate_list_object(self, obj: list[Any], depth: int) -> tuple[bool, str]:
        """Validate a list object in the query."""
        if len(obj) > MAX_ARRAY_SIZE:
            return False, f"Array size exceeds limit ({MAX_ARRAY_SIZE})"

        for item in obj:
            is_valid, error_msg = self._check_query_operators(item, depth + 1)
            if not is_valid:
                return False, error_msg

        return True, ""

    def _validate_string_object(self, obj: str) -> tuple[bool, str]:
        """Validate a string object in the query."""
        if len(obj) > MAX_VALUE_LENGTH:
            return False, f"String value exceeds maximum length ({MAX_VALUE_LENGTH})"
        return True, ""

    def _validate_numeric_object(self, obj: int | float) -> tuple[bool, str]:
        """Validate a numeric object in the query."""
        # Check for reasonable numeric bounds
        if abs(obj) > 1e15:  # Prevent extremely large numbers
            return False, "Numeric value too large"
        return True, ""

    def get_built_query(self) -> str:
        """Get the built query string."""
        return self.built_query

    def get_query_options(self) -> dict[str, Any]:
        """Get additional query options like sort, limit, skip with validation."""
        options: dict[str, Any] = {}

        try:
            # Sort options
            sort_field = self.sort_field_combo.currentText().strip()
            if sort_field and validate_field_name(sort_field):
                sort_direction = (
                    1 if self.sort_direction_combo.currentText() == "Ascending" else -1
                )
                options["sort"] = {sort_field: sort_direction}

            # Limit option with validation
            limit_text = self.limit_input.text().strip()
            if limit_text:
                try:
                    limit_value = int(limit_text)
                    if 0 < limit_value <= MAX_LIMIT_VALUE:
                        options["limit"] = limit_value
                except (ValueError, OverflowError):
                    pass  # Ignore invalid limit values

            # Skip option with validation
            skip_text = self.skip_input.text().strip()
            if skip_text:
                try:
                    skip_value = int(skip_text)
                    if 0 <= skip_value <= MAX_SKIP_VALUE:
                        options["skip"] = skip_value
                except (ValueError, OverflowError):
                    pass  # Ignore invalid skip values

        except Exception:
            # Return empty options on any error
            pass

        return options

    def get_query_with_options(self) -> dict[str, Any]:
        """Get the complete query structure with filter and options."""
        try:
            filter_query_str = self.build_query()
            options = self.get_query_options()

            result = {"filter": filter_query_str, "options": options}

            return result
        except Exception:
            return {"filter": "{}", "options": {}}
