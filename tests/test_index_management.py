# mypy: ignore-errors
import sys
from collections.abc import Generator
from typing import cast

import pytest
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox, QTableWidget

from ui.index_dialog import IndexDialog, IndexEditDialog


@pytest.fixture(scope="module")
def app() -> Generator[object]:
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def _setup_dialog_mocks() -> None:
    """Set up dialog-related mock functions."""
    def auto_accept(self: object) -> int:  # type: ignore
        return QDialog.DialogCode.Accepted  # type: ignore[return-value]

    def mock_question(*args, **kwargs) -> QMessageBox.StandardButton:
        return QMessageBox.StandardButton.Yes

    IndexDialog.exec = cast(object, auto_accept)  # type: ignore
    IndexEditDialog.exec = cast(object, auto_accept)  # type: ignore
    QMessageBox.question = staticmethod(mock_question)  # type: ignore


def _find_and_select_row(table: QTableWidget, name: str) -> None:
    """Find and select a row in the table by index name."""
    for row in range(table.rowCount()):
        if (item := table.item(row, 0)) and item.text() == name:
            table.selectRow(row)
            break


def test_index_dialog_add_edit_remove(app: QApplication) -> None:
    _setup_dialog_mocks()

    # Initialize dialog with test data
    indexes = [
        {"name": "_id_", "key": [["_id", 1]], "unique": True},
        {"name": "idx1", "key": [["field1", 1]], "unique": False},
    ]
    dlg = IndexDialog(indexes)

    # Test adding a new index
    dlg.add_index()
    if edit := dlg.findChild(IndexEditDialog):
        edit.name_input.setText("idx2")
        edit.field_name_edit.setText("field2")
        edit.index_type_combo.setCurrentText("1 (asc)")
        edit.add_field_btn.click()
        edit.unique_checkbox.setChecked(True)
        edit.accept()
        data = edit.get_index_data()
        assert data is not None and data["name"] == "idx2"

    # Test deleting an index
    _find_and_select_row(dlg.table, "idx1")
    dlg.delete_index()
    assert dlg.get_selected_index_name() is None

    # Test editing an index
    _find_and_select_row(dlg.table, "_id_")
    dlg.edit_index()
    edit2 = dlg.findChild(IndexEditDialog)
    if edit2:
        # Remove all existing fields
        while edit2.fields_table.rowCount() > 0:
            edit2.fields_table.removeRow(0)
        # Add _id as a descending index
        edit2.field_name_edit.setText("_id")
        edit2.index_type_combo.setCurrentText("-1 (desc)")
        edit2.add_field_btn.click()
        edit2.accept()
        data2 = edit2.get_index_data()
        assert data2 is not None and data2["key"] == [("_id", -1)]
    dlg.close()
    if edit:
        edit.close()
    if edit2:
        edit2.close()
