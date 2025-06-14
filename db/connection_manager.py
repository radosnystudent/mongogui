"""
MongoDB connection manager for handling connection profiles and secure credential storage.
"""

import json
import logging
import os
from typing import Any

import keyring
from keyring.errors import KeyringError, PasswordDeleteError


class ConnectionManager:
    """
    Manages MongoDB connection profiles and secure credential storage for the GUI application.
    Handles reading, writing, and deleting connection profiles and credentials.
    """

    def __init__(self, storage_path: str = "connections") -> None:
        """
        Initialize the ConnectionManager.

        Args:
            storage_path: Directory path for storing connection profiles.
        """
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.keyring_service = "mongo-client-app"
        self._verify_keyring_storage()

    def _verify_keyring_storage(self) -> None:
        """
        Verify that keyring is available and can store/retrieve credentials.
        Raises an exception if keyring is not functional.
        """
        test_key: str = "__test_key__"
        test_value: str = "__test_value__"
        try:
            keyring.set_password(self.keyring_service, test_key, test_value)
            value: str | None = keyring.get_password(self.keyring_service, test_key)
            if value != test_value:
                raise KeyringError("Keyring storage verification failed.")
        except Exception as e:
            logging.warning(f"Keyring storage verification failed: {e}")
            raise RuntimeError(
                "Secure credential storage (keyring) is not available or not working."
            ) from e
        finally:
            try:
                keyring.delete_password(self.keyring_service, test_key)
            except Exception:
                pass

    def add_connection(
        self: "ConnectionManager",
        name: str,
        db: str,
        ip: str,
        port: int,
        login: str | None,
        password: str | None,
        tls: bool,
    ) -> None:
        """
        Add a new MongoDB connection profile.

        Args:
            name: Connection profile name.
            db: Database name.
            ip: Host IP address.
            port: Port number.
            login: Username (optional).
            password: Password (optional).
            tls: Whether to use TLS/SSL.
        """
        # Store non-sensitive data in file
        data = {"name": name, "db": db, "ip": ip, "port": port, "tls": tls}
        with open(os.path.join(self.storage_path, f"{name}.json"), "w") as f:
            json.dump(data, f)

        # Store credentials in keyring
        if login:
            keyring.set_password(self.keyring_service, f"{name}_login", login)
        if password:
            keyring.set_password(self.keyring_service, f"{name}_password", password)

    def get_connections(self: "ConnectionManager") -> list[dict[str, Any]]:
        """
        Retrieve all saved MongoDB connection profiles.

        Returns:
            List of connection profile dictionaries (excluding credentials).
        """
        connections: list[dict[str, Any]] = []
        for fname in os.listdir(self.storage_path):
            if fname.endswith(".json"):
                with open(os.path.join(self.storage_path, fname)) as f:
                    data = json.load(f)
                    # Do not include credentials
                    connections.append(data)
        return connections

    def get_connection_by_name(
        self: "ConnectionManager", name: str
    ) -> dict[str, Any] | None:
        """
        Retrieve a connection profile by its name.

        Args:
            name: Connection profile name.
        Returns:
            Connection profile dictionary or None if not found.
        """
        try:
            with open(os.path.join(self.storage_path, f"{name}.json")) as f:
                data: dict[str, Any] = json.load(f)
                # Retrieve credentials from keyring
                login = keyring.get_password(self.keyring_service, f"{name}_login")
                password = keyring.get_password(
                    self.keyring_service, f"{name}_password"
                )
                data["login"] = login
                data["password"] = password
                return data
        except FileNotFoundError:
            return None

    def update_connection(
        self: "ConnectionManager",
        old_name: str,
        db: str,
        ip: str,
        port: int,
        login: str | None,
        password: str | None,
        tls: bool,
        new_name: str | None = None,
    ) -> None:
        """
        Update an existing MongoDB connection profile.

        Args:
            old_name: Existing profile name.
            db: Database name.
            ip: Host IP address.
            port: Port number.
            login: Username (optional).
            password: Password (optional).
            tls: Whether to use TLS/SSL.
            new_name: New profile name (optional).
        """
        # If renaming, remove old file and credentials
        name_to_use = new_name if new_name else old_name
        if new_name and new_name != old_name:
            old_file = os.path.join(self.storage_path, f"{old_name}.json")
            if os.path.exists(old_file):
                os.remove(old_file)
            try:
                keyring.delete_password(self.keyring_service, f"{old_name}_login")
            except PasswordDeleteError:
                pass
            try:
                keyring.delete_password(self.keyring_service, f"{old_name}_password")
            except PasswordDeleteError:
                pass
        # Add or overwrite the connection
        self.add_connection(name_to_use, db, ip, port, login, password, tls)

    def remove_connection(self: "ConnectionManager", name: str) -> None:
        """
        Remove a MongoDB connection profile by name.

        Args:
            name: Connection profile name to remove.
        """
        # Remove the connection file and credentials
        file_path = os.path.join(self.storage_path, f"{name}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
        try:
            keyring.delete_password(self.keyring_service, f"{name}_login")
        except PasswordDeleteError:
            pass
        try:
            keyring.delete_password(self.keyring_service, f"{name}_password")
        except PasswordDeleteError:
            pass
