import json
import os
from typing import Any, Dict, List, Optional

import keyring


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
