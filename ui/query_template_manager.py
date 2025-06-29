"""
Query Template Manager for saving and loading query templates.
Provides functionality to save, load, and manage query templates for reuse.
"""

import json
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal


class QueryTemplate:
    """Represents a saved query template."""

    def __init__(
        self,
        name: str,
        query_type: str,
        query_data: dict,
        description: str = "",
        tags: list[str] | None = None,
        created_at: datetime | None = None,
    ):
        self.name = name
        self.query_type = query_type  # 'find' or 'aggregate'
        self.query_data = query_data
        self.description = description
        self.tags = tags or []
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> dict:
        """Convert template to dictionary for serialization."""
        return {
            "name": self.name,
            "query_type": self.query_type,
            "query_data": self.query_data,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "QueryTemplate":
        """Create template from dictionary."""
        created_at = None
        if "created_at" in data:
            try:
                created_at = datetime.fromisoformat(data["created_at"])
            except ValueError:
                created_at = datetime.now()

        return cls(
            name=data["name"],
            query_type=data["query_type"],
            query_data=data["query_data"],
            description=data.get("description", ""),
            tags=data.get("tags", []),
            created_at=created_at,
        )


class QueryTemplateManager(QObject):
    """Manages query templates - saving, loading, and organizing."""

    templates_changed = pyqtSignal()

    def __init__(self, storage_dir: str | None = None):
        super().__init__()
        self.storage_dir = Path(storage_dir or self._get_default_storage_dir())
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.templates_file = self.storage_dir / "query_templates.json"
        self._templates: dict[str, QueryTemplate] = {}
        self._load_templates()

    def _get_default_storage_dir(self) -> str:
        """Get default storage directory for templates."""
        home_dir = Path.home()
        return str(home_dir / ".mongogui" / "templates")

    def _load_templates(self) -> None:
        """Load templates from storage."""
        if not self.templates_file.exists():
            return

        try:
            with open(self.templates_file, encoding="utf-8") as f:
                data = json.load(f)

            self._templates = {}
            for template_data in data.get("templates", []):
                template = QueryTemplate.from_dict(template_data)
                self._templates[template.name] = template

        except (OSError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading templates: {e}")
            self._templates = {}

    def _save_templates(self) -> None:
        """Save templates to storage."""
        try:
            data = {
                "version": "1.0",
                "templates": [
                    template.to_dict() for template in self._templates.values()
                ],
            }

            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.templates_changed.emit()

        except OSError as e:
            print(f"Error saving templates: {e}")

    def save_template(
        self,
        name: str,
        query_type: str,
        query_data: dict,
        description: str = "",
        tags: list[str] | None = None,
    ) -> bool:
        """Save a query template."""
        if not name.strip():
            return False

        template = QueryTemplate(
            name=name.strip(),
            query_type=query_type,
            query_data=query_data,
            description=description.strip(),
            tags=tags or [],
        )

        self._templates[template.name] = template
        self._save_templates()
        return True

    def load_template(self, name: str) -> QueryTemplate | None:
        """Load a template by name."""
        return self._templates.get(name)

    def delete_template(self, name: str) -> bool:
        """Delete a template by name."""
        if name in self._templates:
            del self._templates[name]
            self._save_templates()
            return True
        return False

    def get_all_templates(self) -> list[QueryTemplate]:
        """Get all templates."""
        return list(self._templates.values())

    def get_templates_by_type(self, query_type: str) -> list[QueryTemplate]:
        """Get templates by query type."""
        return [t for t in self._templates.values() if t.query_type == query_type]

    def get_templates_by_tags(self, tags: list[str]) -> list[QueryTemplate]:
        """Get templates that contain any of the specified tags."""
        if not tags:
            return self.get_all_templates()

        return [
            t for t in self._templates.values() if any(tag in t.tags for tag in tags)
        ]

    def search_templates(self, query: str) -> list[QueryTemplate]:
        """Search templates by name or description."""
        query = query.lower().strip()
        if not query:
            return self.get_all_templates()

        return [
            t
            for t in self._templates.values()
            if query in t.name.lower() or query in t.description.lower()
        ]

    def rename_template(self, old_name: str, new_name: str) -> bool:
        """Rename a template."""
        if old_name not in self._templates or new_name.strip() in self._templates:
            return False

        template = self._templates[old_name]
        template.name = new_name.strip()

        del self._templates[old_name]
        self._templates[new_name.strip()] = template

        self._save_templates()
        return True

    def update_template(
        self,
        name: str,
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """Update template metadata."""
        if name not in self._templates:
            return False

        template = self._templates[name]
        if description is not None:
            template.description = description.strip()
        if tags is not None:
            template.tags = tags

        self._save_templates()
        return True

    def export_templates(self, file_path: str) -> bool:
        """Export templates to a file."""
        try:
            data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "templates": [
                    template.to_dict() for template in self._templates.values()
                ],
            }

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except OSError:
            return False

    def import_templates(self, file_path: str, overwrite: bool = False) -> int:
        """Import templates from a file. Returns number of imported templates."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            imported_count = 0
            for template_data in data.get("templates", []):
                template = QueryTemplate.from_dict(template_data)

                if template.name not in self._templates or overwrite:
                    self._templates[template.name] = template
                    imported_count += 1

            if imported_count > 0:
                self._save_templates()

            return imported_count

        except (OSError, json.JSONDecodeError, KeyError):
            return 0

    def get_template_count(self) -> int:
        """Get total number of templates."""
        return len(self._templates)

    def clear_all_templates(self) -> None:
        """Clear all templates."""
        self._templates.clear()
        self._save_templates()
