import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from db.connection_manager import ConnectionManager


class TestConnectionManager(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.connection_manager = ConnectionManager(storage_path=self.temp_dir)

    def tearDown(self) -> None:
        """Clean up after each test method."""
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init_creates_storage_directory(self) -> None:
        """Test that ConnectionManager creates storage directory if it doesn't exist."""
        new_temp_dir = os.path.join(self.temp_dir, "new_storage")
        ConnectionManager(storage_path=new_temp_dir)
        self.assertTrue(os.path.exists(new_temp_dir))

    @patch("db.connection_manager.keyring")
    def test_add_connection_saves_data_and_credentials(
        self, mock_keyring: MagicMock
    ) -> None:
        """Test that add_connection saves connection data and credentials properly."""
        # Test data
        name = "test_connection"
        db = "test_db"
        ip = "127.0.0.1"
        port = 27017
        login = "test_user"
        password = "test_password"
        tls = True

        # Add connection
        self.connection_manager.add_connection(name, db, ip, port, login, password, tls)

        # Verify file was created
        file_path = os.path.join(self.temp_dir, f"{name}.json")
        self.assertTrue(os.path.exists(file_path))

        # Verify file contents
        with open(file_path) as f:
            data = json.load(f)

        expected_data = {"name": name, "db": db, "ip": ip, "port": port, "tls": tls}
        self.assertEqual(data, expected_data)

        # Verify keyring calls
        mock_keyring.set_password.assert_any_call(
            self.connection_manager.keyring_service, f"{name}_login", login
        )
        mock_keyring.set_password.assert_any_call(
            self.connection_manager.keyring_service, f"{name}_password", password
        )

    @patch("db.connection_manager.keyring")
    def test_add_connection_without_credentials(self, mock_keyring: MagicMock) -> None:
        """Test that add_connection works without login credentials."""
        name = "test_connection_no_auth"
        db = "test_db"
        ip = "127.0.0.1"
        port = 27017
        tls = False

        self.connection_manager.add_connection(name, db, ip, port, None, None, tls)

        # Verify file was created
        file_path = os.path.join(self.temp_dir, f"{name}.json")
        self.assertTrue(os.path.exists(file_path))

        # Verify no keyring calls for credentials
        mock_keyring.set_password.assert_not_called()

    def test_get_connections_empty_directory(self) -> None:
        """Test get_connections returns empty list for empty directory."""
        connections = self.connection_manager.get_connections()
        self.assertEqual(connections, [])

    def test_get_connections_with_data(self) -> None:
        """Test get_connections returns list of connections."""
        # Create test connection files
        test_data_1 = {
            "name": "conn1",
            "db": "db1",
            "ip": "127.0.0.1",
            "port": 27017,
            "tls": False,
        }
        test_data_2 = {
            "name": "conn2",
            "db": "db2",
            "ip": "127.0.0.2",
            "port": 27018,
            "tls": True,
        }

        with open(os.path.join(self.temp_dir, "conn1.json"), "w") as f:
            json.dump(test_data_1, f)
        with open(os.path.join(self.temp_dir, "conn2.json"), "w") as f:
            json.dump(test_data_2, f)

        connections = self.connection_manager.get_connections()

        self.assertEqual(len(connections), 2)
        self.assertIn(test_data_1, connections)
        self.assertIn(test_data_2, connections)

    def test_get_connections_ignores_non_json_files(self) -> None:
        """Test get_connections ignores non-JSON files."""
        # Create a non-JSON file
        with open(os.path.join(self.temp_dir, "not_a_connection.txt"), "w") as f:
            f.write("This is not a JSON file")

        connections = self.connection_manager.get_connections()
        self.assertEqual(connections, [])

    @patch("db.connection_manager.keyring")
    def test_get_connection_by_name_success(self, mock_keyring: MagicMock) -> None:
        """Test get_connection_by_name returns connection with credentials."""
        # Setup mock keyring
        mock_keyring.get_password.side_effect = lambda service, key: {
            "test_conn_login": "test_user",
            "test_conn_password": "test_password",
        }.get(key)

        # Create test connection file
        test_data = {
            "name": "test_conn",
            "db": "test_db",
            "ip": "127.0.0.1",
            "port": 27017,
            "tls": True,
        }
        with open(os.path.join(self.temp_dir, "test_conn.json"), "w") as f:
            json.dump(test_data, f)

        connection = self.connection_manager.get_connection_by_name("test_conn")

        expected_connection = {
            "name": "test_conn",
            "db": "test_db",
            "ip": "127.0.0.1",
            "port": 27017,
            "tls": True,
            "login": "test_user",
            "password": "test_password",
        }

        self.assertEqual(connection, expected_connection)

    def test_get_connection_by_name_not_found(self) -> None:
        """Test get_connection_by_name returns None for non-existent connection."""
        connection = self.connection_manager.get_connection_by_name("non_existent")
        self.assertIsNone(connection)

    @patch("db.connection_manager.keyring")
    def test_get_connection_by_name_missing_credentials(
        self, mock_keyring: MagicMock
    ) -> None:
        """Test get_connection_by_name handles missing credentials gracefully."""
        # Setup mock keyring to return None for missing credentials
        mock_keyring.get_password.return_value = None

        # Create test connection file
        test_data = {
            "name": "test_conn",
            "db": "test_db",
            "ip": "127.0.0.1",
            "port": 27017,
            "tls": False,
        }
        with open(os.path.join(self.temp_dir, "test_conn.json"), "w") as f:
            json.dump(test_data, f)

        connection = self.connection_manager.get_connection_by_name("test_conn")

        expected_connection = {
            "name": "test_conn",
            "db": "test_db",
            "ip": "127.0.0.1",
            "port": 27017,
            "tls": False,
            "login": None,
            "password": None,
        }

        self.assertEqual(connection, expected_connection)


if __name__ == "__main__":
    unittest.main()
