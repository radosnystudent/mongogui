import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


# Custom keyring mock that mimics real keyring behavior
class KeyringMock:
    _store: dict[tuple[str, str], str]

    def __init__(self) -> None:
        self._store = {}

    def set_password(self, service: str, key: str, value: str) -> None:
        self._store[(service, key)] = value

    def get_password(self, service: str, key: str) -> str | None:
        return self._store.get((service, key), None)

    def delete_password(self, service: str, key: str) -> None:
        self._store.pop((service, key), None)


# Custom errors to mimic keyring.errors
class KeyringError(Exception):
    pass


class PasswordDeleteError(Exception):
    pass


mock_keyring = KeyringMock()
mock_errors = type(
    "errors",
    (),
    {"KeyringError": KeyringError, "PasswordDeleteError": PasswordDeleteError},
)

with patch.dict(sys.modules, {"keyring": mock_keyring, "keyring.errors": mock_errors}):
    from db.connection_manager import ConnectionManager

    class TestConnectionManager(unittest.TestCase):
        def setUp(self) -> None:
            self.temp_dir = tempfile.mkdtemp()
            # Reset the keyring store for each test
            mock_keyring._store = {}

        def tearDown(self) -> None:
            shutil.rmtree(self.temp_dir)

        def test_init_creates_storage_directory(self) -> None:
            new_temp_dir = os.path.join(self.temp_dir, "new_storage")
            ConnectionManager(storage_path=new_temp_dir)
            self.assertTrue(os.path.exists(new_temp_dir))

        def test_add_connection_saves_data_and_credentials(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            name = "test_connection"
            db = "test_db"
            ip = "127.0.0.1"
            port = 27017
            login = "test_user"
            password = "test_password"
            tls = True
            cm.add_connection(name, db, ip, port, login, password, tls)
            file_path = os.path.join(self.temp_dir, f"{name}.json")
            self.assertTrue(os.path.exists(file_path))
            with open(file_path) as f:
                data = json.load(f)
            expected_data = {"name": name, "db": db, "ip": ip, "port": port, "tls": tls}
            self.assertEqual(data, expected_data)
            # Check that credentials are stored (password is encrypted)
            self.assertEqual(
                mock_keyring.get_password(cm.keyring_service, f"{name}_login"), login
            )
            encrypted_password = mock_keyring.get_password(cm.keyring_service, f"{name}_password")
            self.assertIsInstance(encrypted_password, str)
            from utils.encryption import decrypt_password
            if encrypted_password is not None:
                self.assertEqual(decrypt_password(encrypted_password), password)
            else:
                self.fail("Encrypted password not found in keyring")

        def test_add_connection_without_credentials(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            name = "test_connection_no_auth"
            db = "test_db"
            ip = "127.0.0.1"
            port = 27017
            tls = False
            cm.add_connection(name, db, ip, port, None, None, tls)
            file_path = os.path.join(self.temp_dir, f"{name}.json")
            self.assertTrue(os.path.exists(file_path))
            self.assertIsNone(
                mock_keyring.get_password(cm.keyring_service, f"{name}_login")
            )
            self.assertIsNone(
                mock_keyring.get_password(cm.keyring_service, f"{name}_password")
            )

        def test_get_connections_empty_directory(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            connections = cm.get_connections()
            self.assertEqual(connections, [])

        def test_get_connections_with_data(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
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
            connections = cm.get_connections()
            self.assertEqual(len(connections), 2)
            self.assertIn(test_data_1, connections)
            self.assertIn(test_data_2, connections)

        def test_get_connections_ignores_non_json_files(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            with open(os.path.join(self.temp_dir, "not_a_connection.txt"), "w") as f:
                f.write("This is not a JSON file")
            connections = cm.get_connections()
            self.assertEqual(connections, [])

        def test_get_connection_by_name_success(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            name = "test_conn"
            login = "test_user"
            password = "test_password"
            from utils.encryption import encrypt_password, decrypt_password
            # Pre-populate credentials (store encrypted password)
            mock_keyring.set_password(cm.keyring_service, f"{name}_login", login)
            encrypted_password = encrypt_password(password)
            mock_keyring.set_password(cm.keyring_service, f"{name}_password", encrypted_password)
            test_data = {
                "name": name,
                "db": "test_db",
                "ip": "127.0.0.1",
                "port": 27017,
                "tls": True,
            }
            with open(os.path.join(self.temp_dir, f"{name}.json"), "w") as f:
                json.dump(test_data, f)
            connection = cm.get_connection_by_name(name)
            expected_connection = {
                "name": name,
                "db": "test_db",
                "ip": "127.0.0.1",
                "port": 27017,
                "tls": True,
                "login": login,
                "password": encrypted_password,
            }
            self.assertEqual(connection, expected_connection)
            # Test decryption
            self.assertIsNotNone(connection)
            if connection is not None:
                self.assertEqual(connection, expected_connection)
                # Test decryption
                self.assertIsNotNone(connection["password"])
                self.assertEqual(decrypt_password(connection["password"]), password)

        def test_get_connection_by_name_not_found(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            connection = cm.get_connection_by_name("non_existent")
            self.assertIsNone(connection)

        def test_get_connection_by_name_missing_credentials(self) -> None:
            cm = ConnectionManager(storage_path=self.temp_dir)
            name = "test_conn"
            test_data = {
                "name": name,
                "db": "test_db",
                "ip": "127.0.0.1",
                "port": 27017,
                "tls": False,
            }
            with open(os.path.join(self.temp_dir, f"{name}.json"), "w") as f:
                json.dump(test_data, f)
            connection = cm.get_connection_by_name(name)
            expected_connection = {
                "name": name,
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
