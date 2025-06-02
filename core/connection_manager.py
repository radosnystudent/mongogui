import json
import os
from typing import Any, Dict, List, Optional

import keyring
from keyring.errors import PasswordDeleteError


class ConnectionManager:
    def __init__(self, storage_path: str = "connections") -> None:
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.keyring_service = "mongo-client-app"

    def add_connection(
        self,
        name: str,
        db: str,
        ip: str,
        port: int,
        login: Optional[str],
        password: Optional[str],
        tls: bool,
    ) -> None:
        # Store non-sensitive data in file
        data = {"name": name, "db": db, "ip": ip, "port": port, "tls": tls}
        with open(os.path.join(self.storage_path, f"{name}.json"), "w") as f:
            json.dump(data, f)

        # Store credentials in keyring
        if login:
            keyring.set_password(self.keyring_service, f"{name}_login", login)
        if password:
            keyring.set_password(self.keyring_service, f"{name}_password", password)

    def get_connections(self) -> List[Dict[str, Any]]:
        connections: List[Dict[str, Any]] = []
        for fname in os.listdir(self.storage_path):
            if fname.endswith(".json"):
                with open(os.path.join(self.storage_path, fname)) as f:
                    data = json.load(f)
                    # Do not include credentials
                    connections.append(data)
        return connections

    def get_connection_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            with open(os.path.join(self.storage_path, f"{name}.json")) as f:
                data: Dict[str, Any] = json.load(f)
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
        self,
        old_name: str,
        db: str,
        ip: str,
        port: int,
        login: Optional[str],
        password: Optional[str],
        tls: bool,
        new_name: Optional[str] = None,
    ) -> None:
        """
        Update an existing connection. If new_name is provided and different from old_name, the connection is renamed.
        Overwrites the connection file and credentials.
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

    def remove_connection(self, name: str) -> None:
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
