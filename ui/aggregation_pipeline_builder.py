"""
Aggregation Pipeline Builder for MongoDB queries.
Provides a visual interface for building MongoDB aggregation pipelines.
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# Stage constants to avoid duplication
STAGE_MATCH = "$match"
STAGE_GROUP = "$group"
STAGE_PROJECT = "$project"
STAGE_SORT = "$sort"
STAGE_LOOKUP = "$lookup"
STAGE_LIMIT = "$limit"
STAGE_SKIP = "$skip"
STAGE_UNWIND = "$unwind"
STAGE_ADD_FIELDS = "$addFields"
STAGE_SAMPLE = "$sample"

# UI Style constants
HELP_TEXT_STYLE = "color: #aaa; font-size: 11px;"

# MongoDB aggregation stages organized by category
AGGREGATION_STAGES = {
    "Filtering": [
        STAGE_MATCH,
        STAGE_LIMIT,
        STAGE_SKIP,
        STAGE_SAMPLE,
        "$first",
        "$last",
    ],
    "Grouping": [STAGE_GROUP, "$bucket", "$bucketAuto", "$count", "$sortByCount"],
    "Transformation": [
        STAGE_PROJECT,
        STAGE_ADD_FIELDS,
        "$set",
        "$unset",
        "$replaceRoot",
        "$replaceWith",
    ],
    "Sorting": [STAGE_SORT],
    "Joining": [STAGE_LOOKUP, "$graphLookup", "$unionWith"],
    "Conditional": ["$facet", "$switch", "$cond"],
    "Array": [STAGE_UNWIND, "$push", "$addToSet"],
    "Text": ["$search", "$searchMeta"],
}

# Stage templates with common configurations
STAGE_TEMPLATES = {
    STAGE_MATCH: {"field": "value"},
    STAGE_PROJECT: {"field1": 1, "field2": 0},
    STAGE_GROUP: {"_id": "$field", "count": {"$sum": 1}},
    STAGE_SORT: {"field": 1},
    STAGE_LIMIT: 10,
    STAGE_SKIP: 0,
    STAGE_LOOKUP: {
        "from": "collection",
        "localField": "field",
        "foreignField": "field",
        "as": "result",
    },
    STAGE_UNWIND: "$field",
    STAGE_ADD_FIELDS: {"newField": "$expression"},
    STAGE_SAMPLE: {"size": 5},
}


class PipelineStageWidget(QWidget):
    """A widget representing a single aggregation pipeline stage."""

    removed = pyqtSignal()
    moved_up = pyqtSignal()
    moved_down = pyqtSignal()
    stage_changed = pyqtSignal()

    def __init__(
        self, fields: list[str], stage_number: int = 1, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.fields = fields
        self.stage_number = stage_number
        self.stage_type = STAGE_MATCH  # Default stage
        self.stage_config: Any = STAGE_TEMPLATES.get(self.stage_type, {})
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the stage widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with stage controls
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Stage number and type selector
        self.stage_label = QLabel(f"{self.stage_number}.")
        self.stage_label.setStyleSheet(
            """
            QLabel {
                color: #ddd;
                font-weight: bold;
                font-size: 14px;
                min-width: 20px;
            }
        """
        )
        header_layout.addWidget(self.stage_label)

        self.stage_combo = QComboBox()
        self.stage_combo.setMinimumWidth(120)
        self._populate_stage_combo()
        self.stage_combo.currentTextChanged.connect(self._on_stage_type_changed)
        header_layout.addWidget(self.stage_combo)

        # Configure button
        self.configure_btn = QPushButton("Configure...")
        self.configure_btn.setFixedSize(80, 28)
        self.configure_btn.clicked.connect(self._configure_stage)
        header_layout.addWidget(self.configure_btn)

        header_layout.addStretch()

        # Move buttons
        self.move_up_btn = QPushButton("↑")
        self.move_up_btn.setFixedSize(24, 24)
        self.move_up_btn.setToolTip("Move stage up")
        self.move_up_btn.clicked.connect(self.moved_up.emit)
        header_layout.addWidget(self.move_up_btn)

        self.move_down_btn = QPushButton("↓")
        self.move_down_btn.setFixedSize(24, 24)
        self.move_down_btn.setToolTip("Move stage down")
        self.move_down_btn.clicked.connect(self.moved_down.emit)
        header_layout.addWidget(self.move_down_btn)

        # Remove button
        remove_btn = QPushButton("×")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setToolTip("Remove this stage")
        remove_btn.clicked.connect(self.removed.emit)
        header_layout.addWidget(remove_btn)

        layout.addLayout(header_layout)

        # Stage preview
        self.preview_label = QLabel("Configuration:")
        self.preview_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(self.preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setFixedHeight(60)
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(
            """
            QTextEdit {
                background-color: #2a2a2a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """
        )
        layout.addWidget(self.preview_text)

        # Apply styles
        self.setStyleSheet(
            """
            PipelineStageWidget {
                background-color: #454545;
                border: 1px solid #666;
                border-radius: 4px;
                margin: 4px 2px;
            }
            QComboBox {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #4a9eff;
                background-color: #3a3a3a;
            }
            QPushButton {
                background-color: #505050;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
        """
        )

        self._update_preview()

    def _populate_stage_combo(self) -> None:
        """Populate the stage combo box with categorized stages."""
        self.stage_combo.clear()

        for category, stages in AGGREGATION_STAGES.items():
            self.stage_combo.addItem(f"--- {category} ---")
            # Make separator non-selectable by setting item data
            item_count = self.stage_combo.count() - 1
            self.stage_combo.setItemData(item_count, False, Qt.ItemDataRole.UserRole)

            for stage in stages:
                self.stage_combo.addItem(stage)

        # Set default selection
        self.stage_combo.setCurrentText(self.stage_type)

    def _on_stage_type_changed(self, stage_type: str) -> None:
        """Handle stage type change."""
        if stage_type.startswith("---"):
            # Don't allow selection of category headers
            self.stage_combo.setCurrentText(self.stage_type)
            return

        self.stage_type = stage_type
        self.stage_config = STAGE_TEMPLATES.get(stage_type, {})
        self._update_preview()
        self.stage_changed.emit()

    def _configure_stage(self) -> None:
        """Open configuration dialog for the current stage."""
        # Make a copy of the config, handling both dict and non-dict types
        if isinstance(self.stage_config, dict):
            config_copy = dict(self.stage_config)
        else:
            config_copy = {"value": self.stage_config}

        dialog = StageConfigurationDialog(
            self.stage_type, config_copy, self.fields, self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_config = dialog.get_configuration()
            # If we wrapped a non-dict value, unwrap it
            if isinstance(self.stage_config, dict):
                self.stage_config = new_config
            else:
                self.stage_config = new_config.get("value", new_config)
            self._update_preview()
            self.stage_changed.emit()

    def _update_preview(self) -> None:
        """Update the preview text with current configuration."""
        try:
            preview_json = json.dumps({self.stage_type: self.stage_config}, indent=2)
            self.preview_text.setPlainText(preview_json)
        except Exception:
            self.preview_text.setPlainText(f"{self.stage_type}: {self.stage_config}")

    def update_stage_number(self, number: int) -> None:
        """Update the stage number display."""
        self.stage_number = number
        self.stage_label.setText(f"{number}.")

    def get_stage_object(self) -> dict[str, Any]:
        """Get the stage as a MongoDB aggregation stage object."""
        return {self.stage_type: self.stage_config}

    def set_move_buttons_enabled(self, up_enabled: bool, down_enabled: bool) -> None:
        """Enable/disable move buttons based on position."""
        self.move_up_btn.setEnabled(up_enabled)
        self.move_down_btn.setEnabled(down_enabled)


class StageConfigurationDialog(QDialog):
    """Dialog for configuring individual pipeline stages."""

    def __init__(
        self,
        stage_type: str,
        initial_config: dict[str, Any],
        fields: list[str],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.stage_type = stage_type
        self.config = dict(initial_config) if initial_config else {}
        self.fields = fields

        self.setWindowTitle(f"Configure {stage_type} Stage")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the configuration dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title
        title_label = QLabel(f"Configure {self.stage_type} Stage")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ddd; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Configuration area
        if self.stage_type in [
            STAGE_MATCH,
            STAGE_PROJECT,
            STAGE_GROUP,
            STAGE_SORT,
            STAGE_LOOKUP,
        ]:
            self._setup_form_based_config(layout)
        else:
            self._setup_json_based_config(layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._validate_and_accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

        # Apply dialog styles
        self.setStyleSheet(
            """
            QDialog {
                background-color: #3a3a3a;
                color: #ddd;
            }
            QLabel {
                color: #ddd;
            }
            QLineEdit, QTextEdit, QComboBox {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #4a9eff;
                background-color: #3a3a3a;
            }
            QPushButton {
                background-color: #505050;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #606060;
                border-color: #666;
            }
            QPushButton:default {
                background-color: #4a6741;
            }
            QPushButton:default:hover {
                background-color: #5a7751;
            }
        """
        )

    def _setup_form_based_config(self, layout: QVBoxLayout) -> None:
        """Setup form-based configuration for common stages."""
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)

        if self.stage_type == STAGE_MATCH:
            self._setup_match_form(form_layout)
        elif self.stage_type == STAGE_PROJECT:
            self._setup_project_form(form_layout)
        elif self.stage_type == STAGE_GROUP:
            self._setup_group_form(form_layout)
        elif self.stage_type == STAGE_SORT:
            self._setup_sort_form(form_layout)
        elif self.stage_type == STAGE_LOOKUP:
            self._setup_lookup_form(form_layout)

        layout.addWidget(form_widget)

    def _setup_match_form(self, layout: QVBoxLayout) -> None:
        """Setup form for $match stage."""
        label = QLabel("Match conditions (JSON format):")
        layout.addWidget(label)

        self.match_text = QTextEdit()
        self.match_text.setFixedHeight(150)
        try:
            self.match_text.setPlainText(json.dumps(self.config, indent=2))
        except Exception:
            self.match_text.setPlainText("{}")
        layout.addWidget(self.match_text)

        help_label = QLabel('Example: {"status": "active", "age": {"$gte": 18}}')
        help_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(help_label)

    def _setup_project_form(self, layout: QVBoxLayout) -> None:
        """Setup form for $project stage."""
        label = QLabel("Field projections:")
        layout.addWidget(label)

        # Add some common project patterns
        include_label = QLabel("Include fields (1) or exclude (0):")
        include_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(include_label)

        self.project_text = QTextEdit()
        self.project_text.setFixedHeight(120)
        try:
            self.project_text.setPlainText(json.dumps(self.config, indent=2))
        except Exception:
            self.project_text.setPlainText('{\n  "field1": 1,\n  "field2": 0\n}')
        layout.addWidget(self.project_text)

    def _setup_group_form(self, layout: QVBoxLayout) -> None:
        """Setup form for $group stage."""
        label = QLabel("Group configuration:")
        layout.addWidget(label)

        self.group_text = QTextEdit()
        self.group_text.setFixedHeight(150)
        try:
            self.group_text.setPlainText(json.dumps(self.config, indent=2))
        except Exception:
            self.group_text.setPlainText(
                '{\n  "_id": "$field",\n  "count": {"$sum": 1}\n}'
            )
        layout.addWidget(self.group_text)

        help_label = QLabel(
            'Example: {"_id": "$category", "total": {"$sum": "$amount"}}'
        )
        help_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(help_label)

    def _setup_sort_form(self, layout: QVBoxLayout) -> None:
        """Setup form for $sort stage."""
        label = QLabel("Sort specification:")
        layout.addWidget(label)

        self.sort_text = QTextEdit()
        self.sort_text.setFixedHeight(100)
        try:
            self.sort_text.setPlainText(json.dumps(self.config, indent=2))
        except Exception:
            self.sort_text.setPlainText('{\n  "field": 1\n}')
        layout.addWidget(self.sort_text)

        help_label = QLabel("Use 1 for ascending, -1 for descending")
        help_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(help_label)

    def _setup_lookup_form(self, layout: QVBoxLayout) -> None:
        """Setup form for $lookup stage."""
        # From collection
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("From collection:"))
        self.from_input = QLineEdit()
        self.from_input.setText(self.config.get("from", ""))
        from_layout.addWidget(self.from_input)
        layout.addLayout(from_layout)

        # Local field
        local_layout = QHBoxLayout()
        local_layout.addWidget(QLabel("Local field:"))
        self.local_field_combo = QComboBox()
        self.local_field_combo.setEditable(True)
        self.local_field_combo.addItems(self.fields)
        self.local_field_combo.setCurrentText(self.config.get("localField", ""))
        local_layout.addWidget(self.local_field_combo)
        layout.addLayout(local_layout)

        # Foreign field
        foreign_layout = QHBoxLayout()
        foreign_layout.addWidget(QLabel("Foreign field:"))
        self.foreign_field_input = QLineEdit()
        self.foreign_field_input.setText(self.config.get("foreignField", ""))
        foreign_layout.addWidget(self.foreign_field_input)
        layout.addLayout(foreign_layout)

        # As field
        as_layout = QHBoxLayout()
        as_layout.addWidget(QLabel("As field:"))
        self.as_field_input = QLineEdit()
        self.as_field_input.setText(self.config.get("as", ""))
        as_layout.addWidget(self.as_field_input)
        layout.addLayout(as_layout)

    def _setup_json_based_config(self, layout: QVBoxLayout) -> None:
        """Setup JSON-based configuration for other stages."""
        label = QLabel(f"Configuration for {self.stage_type}:")
        layout.addWidget(label)

        self.json_text = QTextEdit()
        self.json_text.setFixedHeight(200)
        try:
            self.json_text.setPlainText(json.dumps(self.config, indent=2))
        except Exception:
            self.json_text.setPlainText(str(self.config))
        layout.addWidget(self.json_text)

        help_label = QLabel("Enter the stage configuration in JSON format")
        help_label.setStyleSheet(HELP_TEXT_STYLE)
        layout.addWidget(help_label)

    def _validate_and_accept(self) -> None:
        """Validate configuration and accept dialog."""
        try:
            if self.stage_type == STAGE_MATCH:
                self.config = json.loads(self.match_text.toPlainText())
            elif self.stage_type == STAGE_PROJECT:
                self.config = json.loads(self.project_text.toPlainText())
            elif self.stage_type == STAGE_GROUP:
                self.config = json.loads(self.group_text.toPlainText())
            elif self.stage_type == STAGE_SORT:
                self.config = json.loads(self.sort_text.toPlainText())
            elif self.stage_type == STAGE_LOOKUP:
                self.config = {
                    "from": self.from_input.text().strip(),
                    "localField": self.local_field_combo.currentText().strip(),
                    "foreignField": self.foreign_field_input.text().strip(),
                    "as": self.as_field_input.text().strip(),
                }
            else:
                self.config = json.loads(self.json_text.toPlainText())

            self.accept()
        except json.JSONDecodeError as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Invalid JSON", f"Invalid JSON format: {str(e)}")
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self, "Configuration Error", f"Error in configuration: {str(e)}"
            )

    def get_configuration(self) -> dict[str, Any]:
        """Get the configured stage settings."""
        return self.config


class AggregationPipelineBuilder(QWidget):
    """Main widget for building MongoDB aggregation pipelines."""

    pipeline_changed = pyqtSignal()

    def __init__(self, fields: list[str], parent: QWidget | None = None):
        super().__init__(parent)
        self.fields = fields
        self.stages: list[PipelineStageWidget] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the pipeline builder UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title and controls
        header_layout = QHBoxLayout()

        title_label = QLabel("Aggregation Pipeline")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ddd;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Add stage button
        add_stage_btn = QPushButton("+ Add Stage")
        add_stage_btn.setToolTip("Add a new pipeline stage")
        add_stage_btn.clicked.connect(self.add_stage)
        add_stage_btn.setStyleSheet(
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
        """
        )
        header_layout.addWidget(add_stage_btn)

        layout.addLayout(header_layout)

        # Pipeline stages scroll area
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

        # Stages container
        self.stages_widget = QWidget()
        self.stages_layout = QVBoxLayout(self.stages_widget)
        self.stages_layout.setContentsMargins(10, 10, 10, 10)
        self.stages_layout.setSpacing(8)
        self.stages_layout.addStretch()

        scroll.setWidget(self.stages_widget)
        layout.addWidget(scroll, stretch=1)

        # Pipeline preview
        preview_label = QLabel("Pipeline Preview:")
        preview_label.setStyleSheet("color: #ddd; font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)

        self.pipeline_preview = QTextEdit()
        self.pipeline_preview.setFixedHeight(120)
        self.pipeline_preview.setReadOnly(True)
        self.pipeline_preview.setStyleSheet(
            """
            QTextEdit {
                background-color: #2a2a2a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """
        )
        layout.addWidget(self.pipeline_preview)

        # Start with one stage
        self.add_stage()

    def add_stage(self) -> None:
        """Add a new pipeline stage."""
        stage_number = len(self.stages) + 1
        stage = PipelineStageWidget(self.fields, stage_number)

        # Connect signals
        stage.removed.connect(lambda: self._remove_stage(stage))
        stage.moved_up.connect(lambda: self._move_stage_up(stage))
        stage.moved_down.connect(lambda: self._move_stage_down(stage))
        stage.stage_changed.connect(self._update_pipeline_preview)

        self.stages.append(stage)
        self.stages_layout.insertWidget(len(self.stages) - 1, stage)

        self._update_stage_numbers()
        self._update_pipeline_preview()

    def _remove_stage(self, stage: PipelineStageWidget) -> None:
        """Remove a pipeline stage."""
        if len(self.stages) <= 1:
            return  # Don't remove the last stage

        self.stages.remove(stage)
        stage.setParent(None)
        stage.deleteLater()

        self._update_stage_numbers()
        self._update_pipeline_preview()

    def _move_stage_up(self, stage: PipelineStageWidget) -> None:
        """Move a stage up in the pipeline."""
        index = self.stages.index(stage)
        if index > 0:
            # Swap stages
            self.stages[index], self.stages[index - 1] = (
                self.stages[index - 1],
                self.stages[index],
            )

            # Update layout
            self.stages_layout.removeWidget(stage)
            self.stages_layout.insertWidget(index - 1, stage)

            self._update_stage_numbers()
            self._update_pipeline_preview()

    def _move_stage_down(self, stage: PipelineStageWidget) -> None:
        """Move a stage down in the pipeline."""
        index = self.stages.index(stage)
        if index < len(self.stages) - 1:
            # Swap stages
            self.stages[index], self.stages[index + 1] = (
                self.stages[index + 1],
                self.stages[index],
            )

            # Update layout
            self.stages_layout.removeWidget(stage)
            self.stages_layout.insertWidget(index + 1, stage)

            self._update_stage_numbers()
            self._update_pipeline_preview()

    def _update_stage_numbers(self) -> None:
        """Update stage numbering and move button states."""
        for i, stage in enumerate(self.stages):
            stage.update_stage_number(i + 1)
            stage.set_move_buttons_enabled(i > 0, i < len(self.stages) - 1)

    def _update_pipeline_preview(self) -> None:
        """Update the pipeline preview text."""
        try:
            pipeline = self.get_pipeline()
            if pipeline:
                preview_json = json.dumps(pipeline, indent=2)
                self.pipeline_preview.setPlainText(preview_json)
            else:
                self.pipeline_preview.setPlainText("[]")
        except Exception as e:
            self.pipeline_preview.setPlainText(f"Error generating preview: {str(e)}")

        self.pipeline_changed.emit()

    def get_pipeline(self) -> list[dict[str, Any]]:
        """Get the complete aggregation pipeline."""
        pipeline = []
        for stage in self.stages:
            stage_obj = stage.get_stage_object()
            if stage_obj:
                pipeline.append(stage_obj)
        return pipeline

    def clear_pipeline(self) -> None:
        """Clear all stages and start fresh."""
        # Remove all stages except one
        while len(self.stages) > 1:
            stage = self.stages[-1]
            self._remove_stage(stage)

        # Reset the remaining stage
        if self.stages:
            self.stages[0].stage_type = STAGE_MATCH
            self.stages[0].stage_config = STAGE_TEMPLATES.get(STAGE_MATCH, {})
            self.stages[0]._update_preview()

        self._update_pipeline_preview()
