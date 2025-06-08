from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox, QTreeWidgetItem

from gui.main_window import MainWindow


class TestMainWindow:
    """Test cases for MainWindow class."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        """Set up test fixtures."""
        # Ensure QApplication exists
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

        # Create a fully mocked MainWindow
        with (
            patch("gui.main_window.ConnectionManager"),
            patch("gui.main_window.MongoClientWrapper"),
        ):
            self.main_window_class = MainWindow

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_main_window_initialization(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test MainWindow initialization."""
        # Create instance
        main_window = MainWindow()

        # Verify core components are initialized
        mock_conn_manager.assert_called_once()
        assert main_window.mongo_client is None
        assert main_window.current_connection is None
        assert main_window.current_page == 0
        assert main_window.page_size == 50
        assert main_window.results == []

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_load_connections(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test load_connections method."""
        # Setup mock connection manager
        mock_conn_manager_instance = MagicMock()
        mock_conn_manager.return_value = mock_conn_manager_instance
        mock_connections = [
            {"name": "test1", "ip": "localhost", "port": 27017, "db": "testdb1"},
            {"name": "test2", "ip": "192.168.1.100", "port": 27018, "db": "testdb2"},
        ]
        mock_conn_manager_instance.get_connections.return_value = mock_connections

        # Create main window and test load_connections
        main_window = MainWindow()
        main_window.load_connections()

        # Verify get_connections was called
        mock_conn_manager_instance.get_connections.assert_called()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_connect_to_database_success(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test successful database connection."""
        # Setup mocks
        mock_conn_manager_instance = MagicMock()
        mock_conn_manager.return_value = mock_conn_manager_instance
        mock_mongo_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_mongo_client_instance

        connection_data = {
            "name": "test_conn",
            "ip": "localhost",
            "port": 27017,
            "db": "test_db",
            "login": "user",
            "password": "pass",
            "tls": False,
        }
        mock_conn_manager_instance.get_connection_by_name.return_value = connection_data
        mock_mongo_client_instance.connect.return_value = True
        mock_mongo_client_instance.list_collections.return_value = [
            "collection1",
            "collection2",
        ]

        # Patch exec_ to auto-accept the dialog
        from unittest.mock import patch

        import gui.connection_manager_window as cmw

        with (
            patch.object(
                cmw.ConnectionManagerWindow,
                "exec_",
                lambda self: (self.accept(), QDialog.Accepted)[1],
            ),
            patch.object(
                QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok
            ),
        ):
            main_window = MainWindow()
            main_window.connect_to_database("test_conn")

        # Verify connection was attempted
        mock_conn_manager_instance.get_connection_by_name.assert_called_with(
            "test_conn"
        )

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_connect_to_database_failure(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test failed database connection."""
        # Setup mocks
        mock_conn_manager_instance = MagicMock()
        mock_conn_manager.return_value = mock_conn_manager_instance
        mock_conn_manager_instance.get_connection_by_name.return_value = None

        # Patch exec_ to auto-accept the dialog
        from unittest.mock import patch

        import gui.connection_manager_window as cmw

        with (
            patch.object(
                cmw.ConnectionManagerWindow,
                "exec_",
                lambda self: (self.accept(), QDialog.Accepted)[1],
            ),
            patch.object(
                QMessageBox, "critical", lambda *args, **kwargs: QMessageBox.Ok
            ),
        ):
            main_window = MainWindow()
            main_window.connect_to_database("nonexistent_conn")

        # Verify error handling
        mock_conn_manager_instance.get_connection_by_name.assert_called_with(
            "nonexistent_conn"
        )

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_execute_query_no_connection(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test query execution without database connection."""
        main_window = MainWindow()
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        current_tab.query_input.setPlainText("db.test.find({})")
        current_tab.execute_query()
        # Should show no connection error
        assert "No database connection" in current_tab.result_display.toPlainText()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_execute_query_empty_query(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test query execution with empty query."""
        mock_mongo_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_mongo_client_instance
        main_window = MainWindow()
        main_window.active_clients = {"testdb": mock_mongo_client_instance}
        db_item = QTreeWidgetItem(["testdb", ""])
        col_item = QTreeWidgetItem(["", "test"])
        db_item.addChild(col_item)
        main_window.collection_tree.addTopLevelItem(db_item)
        main_window.collection_tree.setCurrentItem(col_item)
        main_window.mongo_client = mock_mongo_client_instance
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        current_tab.query_input.clear()
        current_tab.execute_query()
        # Should show no connection error (matches new logic)
        assert "No database connection" in current_tab.result_display.toPlainText()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_execute_query_success(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test successful query execution."""
        mock_mongo_client_instance = MagicMock()
        mock_mongo_client.return_value = mock_mongo_client_instance
        test_results = [
            {"_id": "1", "name": "test1", "value": 100},
            {"_id": "2", "name": "test2", "value": 200},
        ]
        mock_mongo_client_instance.execute_query.return_value = test_results
        main_window = MainWindow()
        # Patch for new logic: add mock client to active_clients and select a collection
        main_window.active_clients = {"testdb": mock_mongo_client_instance}
        db_item = QTreeWidgetItem(["testdb", ""])
        col_item = QTreeWidgetItem(["", "test"])
        db_item.addChild(col_item)
        main_window.collection_tree.addTopLevelItem(db_item)
        main_window.collection_tree.setCurrentItem(col_item)
        main_window.mongo_client = mock_mongo_client_instance
        # Open a new tab for the collection (simulate user click)
        main_window.on_collection_tree_item_clicked(col_item, 0)
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        current_tab.mongo_client = mock_mongo_client_instance  # Ensure mock is set
        current_tab.query_input.setPlainText("db.test.find({})")
        current_tab.execute_query()
        mock_mongo_client_instance.execute_query.assert_called_with("db.test.find({})")
        assert current_tab.results == test_results

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_display_results(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test results display functionality."""
        main_window = MainWindow()
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        test_results = [
            {"_id": "1", "name": "test1", "value": 100},
            {"_id": "2", "name": "test2", "value": 200},
        ]
        current_tab.results = test_results
        current_tab.current_page = 0
        current_tab.display_results()
        assert "test1" in current_tab.result_display.toPlainText()
        assert "test2" in current_tab.result_display.toPlainText()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_pagination_controls(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test pagination functionality."""
        main_window = MainWindow()
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        large_results = [{"_id": str(i), "value": i} for i in range(150)]
        current_tab.results = large_results
        current_tab.current_page = 0
        current_tab.page_size = 50
        current_tab.display_results()
        assert not current_tab.prev_btn.isEnabled()  # First page, no previous
        assert current_tab.next_btn.isEnabled()  # Has next page
        assert "Page 1" in current_tab.page_label.text()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_clear_query(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test query clearing functionality."""
        # Create main window
        main_window = MainWindow()
        # Set query text in the current tab
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        current_tab.query_input.setPlainText("db.test.find({})")
        # Clear query
        current_tab.clear_query()
        # Verify query is cleared
        assert current_tab.query_input.toPlainText() == ""

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    @patch("gui.connection_widgets.ConnectionDialog")
    def test_add_connection_dialog(
        self,
        mock_dialog: MagicMock,
        mock_mongo_client: MagicMock,
        mock_conn_manager: MagicMock,
    ) -> None:
        """Test add connection dialog functionality."""
        # Setup mocks
        mock_conn_manager_instance = MagicMock()
        mock_conn_manager.return_value = mock_conn_manager_instance
        mock_dialog_instance = MagicMock()
        mock_dialog.return_value = mock_dialog_instance
        mock_dialog_instance.exec_.return_value = QDialog.Accepted
        mock_dialog_instance.get_result.return_value = (
            "test_conn",
            "test_db",
            "localhost",
            "27017",
            "user",
            "pass",
            False,
        )
        # Create main window
        main_window = MainWindow()
        # Trigger add connection
        main_window.add_connection()
        # Verify dialog was created and connection was added
        mock_conn_manager_instance.add_connection.assert_called_once()

    @patch("gui.main_window.ConnectionManager")
    @patch("gui.main_window.MongoClientWrapper")
    def test_display_table_results(
        self, mock_mongo_client: MagicMock, mock_conn_manager: MagicMock
    ) -> None:
        """Test table display of results."""
        main_window = MainWindow()
        current_tab = main_window.query_tabs.currentWidget()
        assert current_tab is not None, "No current query tab available"
        test_results = [
            {"_id": "1", "name": "test1", "value": 100},
            {"_id": "2", "name": "test2", "value": 200},
        ]
        current_tab.display_table_results(test_results)
        if current_tab.data_table:
            assert current_tab.data_table.columnCount() == 3  # _id, name, value
            assert current_tab.data_table.rowCount() == 2
