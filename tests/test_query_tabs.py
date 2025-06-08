from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot  # type: ignore[import-untyped]

from ui.main_window import MainWindow


def test_query_tab_state_preserved(qtbot: "QtBot") -> None:
    main_window = MainWindow()
    qtbot.addWidget(main_window)
    # Add two tabs for two collections
    main_window.add_query_tab(collection_name="col1", db_label="db1")
    main_window.add_query_tab(collection_name="col2", db_label="db2")
    assert main_window.query_tabs.count() >= 2
    tab1 = main_window.query_tabs.widget(0)
    tab2 = main_window.query_tabs.widget(1)
    assert tab1 is not None, "Tab 1 is None"
    assert tab2 is not None, "Tab 2 is None"
    # Set different queries in each tab
    tab1.query_input.setPlainText("db.col1.find({a: 1})")
    tab2.query_input.setPlainText("db.col2.find({b: 2})")
    # Switch tabs and check state is preserved
    main_window.query_tabs.setCurrentIndex(0)
    assert tab1.query_input.toPlainText() == "db.col1.find({a: 1})"
    main_window.query_tabs.setCurrentIndex(1)
    assert tab2.query_input.toPlainText() == "db.col2.find({b: 2})"
    # Close tab2 and ensure tab1 is still present and state is preserved
    main_window._close_query_tab(1)
    assert main_window.query_tabs.count() >= 1
    assert tab1.query_input.toPlainText() == "db.col1.find({a: 1})"
