"""
Query Template Management Dialog.
Provides UI for saving, loading, and managing query templates.
"""

import json
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.query_template_manager import QueryTemplate, QueryTemplateManager


class TemplateManagementDialog(QDialog):
    """Dialog for managing query templates."""

    def __init__(
        self, template_manager: QueryTemplateManager, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.template_manager = template_manager
        self.selected_template: Optional[QueryTemplate] = None

        self.setWindowTitle("Query Template Manager")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(600, 400)

        self._setup_ui()
        self._load_templates()

    def _setup_ui(self) -> None:
        """Setup the template management UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Query Template Manager")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ddd; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Template list
        left_panel = self._create_template_list_panel()
        splitter.addWidget(left_panel)

        # Right panel - Template details
        right_panel = self._create_template_details_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, stretch=1)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        # Import/Export buttons
        import_btn = QPushButton("Import Templates")
        import_btn.clicked.connect(self._import_templates)
        button_layout.addWidget(import_btn)

        export_btn = QPushButton("Export Templates")
        export_btn.clicked.connect(self._export_templates)
        button_layout.addWidget(export_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

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
            QLineEdit, QTextEdit {
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
            QListWidget {
                background-color: #333333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #4a6741;
            }
            QListWidget::item:hover {
                background-color: #505050;
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

    def _create_template_list_panel(self) -> QWidget:
        """Create the template list panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Search box
        search_label = QLabel("Search Templates:")
        layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or description...")
        self.search_input.textChanged.connect(self._filter_templates)
        layout.addWidget(self.search_input)

        # Template list
        list_label = QLabel("Templates:")
        layout.addWidget(list_label)

        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self._on_template_selected)
        layout.addWidget(self.template_list)

        # List action buttons
        list_actions_layout = QHBoxLayout()

        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self._delete_template)
        list_actions_layout.addWidget(delete_btn)

        duplicate_btn = QPushButton("Duplicate")
        duplicate_btn.clicked.connect(self._duplicate_template)
        list_actions_layout.addWidget(duplicate_btn)

        layout.addLayout(list_actions_layout)

        return panel

    def _create_template_details_panel(self) -> QWidget:
        """Create the template details panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # Template details header
        details_label = QLabel("Template Details:")
        layout.addWidget(details_label)

        # Name
        name_label = QLabel("Name:")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)
        layout.addWidget(self.name_input)

        # Type
        type_label = QLabel("Type:")
        layout.addWidget(type_label)

        self.type_input = QLineEdit()
        self.type_input.setReadOnly(True)
        layout.addWidget(self.type_input)

        # Description
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        layout.addWidget(self.description_input)

        # Tags
        tags_label = QLabel("Tags (comma-separated):")
        layout.addWidget(tags_label)

        self.tags_input = QLineEdit()
        layout.addWidget(self.tags_input)

        # Query preview
        query_label = QLabel("Query Preview:")
        layout.addWidget(query_label)

        self.query_preview = QTextEdit()
        self.query_preview.setReadOnly(True)
        self.query_preview.setFont(QFont("Consolas", 10))
        layout.addWidget(self.query_preview)

        # Update button
        update_btn = QPushButton("Update Template")
        update_btn.clicked.connect(self._update_template)
        layout.addWidget(update_btn)

        layout.addStretch()

        return panel

    def _load_templates(self) -> None:
        """Load templates into the list."""
        self.template_list.clear()
        templates = self.template_manager.get_all_templates()

        for template in sorted(templates, key=lambda t: t.name.lower()):
            item = QListWidgetItem(f"{template.name} ({template.query_type})")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def _filter_templates(self) -> None:
        """Filter templates based on search query."""
        query = self.search_input.text()
        templates = self.template_manager.search_templates(query)

        self.template_list.clear()
        for template in sorted(templates, key=lambda t: t.name.lower()):
            item = QListWidgetItem(f"{template.name} ({template.query_type})")
            item.setData(Qt.ItemDataRole.UserRole, template)
            self.template_list.addItem(item)

    def _on_template_selected(self) -> None:
        """Handle template selection."""
        current_item = self.template_list.currentItem()
        if current_item:
            self.selected_template = current_item.data(Qt.ItemDataRole.UserRole)
            self._populate_template_details()
        else:
            self.selected_template = None
            self._clear_template_details()

    def _populate_template_details(self) -> None:
        """Populate template details panel."""
        if not self.selected_template:
            return

        self.name_input.setText(self.selected_template.name)
        self.type_input.setText(self.selected_template.query_type.upper())
        self.description_input.setPlainText(self.selected_template.description)
        self.tags_input.setText(", ".join(self.selected_template.tags))

        # Format query preview
        try:
            query_text = json.dumps(self.selected_template.query_data, indent=2)
            self.query_preview.setPlainText(query_text)
        except Exception:
            self.query_preview.setPlainText(str(self.selected_template.query_data))

    def _clear_template_details(self) -> None:
        """Clear template details panel."""
        self.name_input.clear()
        self.type_input.clear()
        self.description_input.clear()
        self.tags_input.clear()
        self.query_preview.clear()

    def _update_template(self) -> None:
        """Update the selected template."""
        if not self.selected_template:
            return

        description = self.description_input.toPlainText().strip()
        tags_text = self.tags_input.text().strip()
        tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        success = self.template_manager.update_template(
            self.selected_template.name, description, tags
        )

        if success:
            QMessageBox.information(self, "Success", "Template updated successfully!")
            self._load_templates()
        else:
            QMessageBox.warning(self, "Error", "Failed to update template.")

    def _delete_template(self) -> None:
        """Delete the selected template."""
        if not self.selected_template:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the template '{self.selected_template.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            success = self.template_manager.delete_template(self.selected_template.name)
            if success:
                self._load_templates()
                self._clear_template_details()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete template.")

    def _duplicate_template(self) -> None:
        """Duplicate the selected template."""
        if not self.selected_template:
            return

        # Find a unique name
        base_name = f"{self.selected_template.name} (Copy)"
        new_name = base_name
        counter = 1

        while self.template_manager.load_template(new_name):
            new_name = f"{base_name} {counter}"
            counter += 1

        success = self.template_manager.save_template(
            new_name,
            self.selected_template.query_type,
            self.selected_template.query_data,
            self.selected_template.description,
            self.selected_template.tags.copy(),
        )

        if success:
            self._load_templates()
            # Select the new template
            for i in range(self.template_list.count()):
                item = self.template_list.item(i)
                if item is not None:
                    template = item.data(Qt.ItemDataRole.UserRole)
                    if template and template.name == new_name:
                        self.template_list.setCurrentItem(item)
                        break
        else:
            QMessageBox.warning(self, "Error", "Failed to duplicate template.")

    def _import_templates(self) -> None:
        """Import templates from a file."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Templates",
            "",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            count = self.template_manager.import_templates(file_path, overwrite=False)
            if count > 0:
                QMessageBox.information(
                    self, "Success", f"Imported {count} template(s) successfully!"
                )
                self._load_templates()
            else:
                QMessageBox.warning(self, "Error", "No templates were imported.")

    def _export_templates(self) -> None:
        """Export templates to a file."""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Templates",
            "query_templates.json",
            "JSON Files (*.json);;All Files (*)",
        )

        if file_path:
            success = self.template_manager.export_templates(file_path)
            if success:
                count = self.template_manager.get_template_count()
                QMessageBox.information(
                    self, "Success", f"Exported {count} template(s) successfully!"
                )
            else:
                QMessageBox.warning(self, "Error", "Failed to export templates.")


class SaveTemplateDialog(QDialog):
    """Dialog for saving a new query template."""

    def __init__(
        self, query_type: str, query_data: dict, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.query_type = query_type
        self.query_data = query_data
        self.template_name = ""
        self.template_description = ""
        self.template_tags: list[str] = []

        self.setWindowTitle("Save Query Template")
        self.setModal(True)
        self.resize(500, 400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the save template dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Save Query Template")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ddd; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # Template name
        name_label = QLabel("Template Name:")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter template name...")
        layout.addWidget(self.name_input)

        # Description
        desc_label = QLabel("Description (optional):")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter template description...")
        self.description_input.setMaximumHeight(80)
        layout.addWidget(self.description_input)

        # Tags
        tags_label = QLabel("Tags (optional, comma-separated):")
        layout.addWidget(tags_label)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("e.g., users, analytics, reporting")
        layout.addWidget(self.tags_input)

        # Query type and preview
        type_label = QLabel(f"Query Type: {self.query_type.upper()}")
        type_label.setStyleSheet("font-weight: bold; color: #4a9eff;")
        layout.addWidget(type_label)

        preview_label = QLabel("Query Preview:")
        layout.addWidget(preview_label)

        self.query_preview = QTextEdit()
        self.query_preview.setReadOnly(True)
        self.query_preview.setFont(QFont("Consolas", 10))
        self.query_preview.setMaximumHeight(120)

        try:
            query_text = json.dumps(self.query_data, indent=2)
            self.query_preview.setPlainText(query_text)
        except Exception:
            self.query_preview.setPlainText(str(self.query_data))

        layout.addWidget(self.query_preview)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Template")
        save_btn.clicked.connect(self._save_template)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)

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
            QLineEdit, QTextEdit {
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

    def _save_template(self) -> None:
        """Save the template."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a template name.")
            return

        self.template_name = name
        self.template_description = self.description_input.toPlainText().strip()

        tags_text = self.tags_input.text().strip()
        self.template_tags = [
            tag.strip() for tag in tags_text.split(",") if tag.strip()
        ]

        self.accept()

    def get_template_data(self) -> tuple[str, str, list[str]]:
        """Get the template data."""
        return self.template_name, self.template_description, self.template_tags
