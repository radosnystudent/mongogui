# mypy: ignore-errors
import sys
from typing import Generator, cast

import pytest
from PyQt5.QtWidgets import QApplication

from gui.index_dialog import IndexDialog, IndexEditDialog


@pytest.fixture(scope="module")
def app() -> Generator[object, None, None]:
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_index_dialog_add_edit_remove(app: QApplication) -> None:
    from PyQt5.QtWidgets import QDialog

    # Patch exec_ for all dialogs to auto-accept
    def auto_accept(self: object) -> int:  # type: ignore
        return QDialog.Accepted  # type: ignore[return-value]

    IndexDialog.exec_ = cast(object, auto_accept)  # type: ignore
    IndexEditDialog.exec_ = cast(object, auto_accept)  # type: ignore

    indexes = [
        {"name": "_id_", "key": [["_id", 1]], "unique": True},
        {"name": "idx1", "key": [["field1", 1]], "unique": False},
    ]
    dlg = IndexDialog(indexes)
    # Simulate add
    dlg.add_index_dialog()
    edit = dlg.findChild(IndexEditDialog)
    if edit:
        edit.name_edit.setText("idx2")
        # Add field2 as an ascending index
        edit.field_name_edit.setText("field2")
        edit.index_type_combo.setCurrentText("1 (asc)")
        edit.add_field_btn.click()
        edit.unique_checkbox.setChecked(True)
        edit.accept()
        data = edit.get_index_data()
        assert data is not None and data["name"] == "idx2"
    # Simulate select and remove
    dlg.selected_index_name = "idx1"
    dlg.remove_index()
    assert dlg.get_selected_index_name() is None
    # Simulate edit
    dlg.selected_index_name = "_id_"
    dlg.edit_index_dialog()
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
