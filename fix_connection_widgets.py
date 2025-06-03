"""
Fix connection_widgets.py file by replacing it with a corrected version.
"""

import os

fixed_content = r"""from typing import TYPE_CHECKING, Any, Dict

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QMenu, QPushButton, QVBoxLayout, QWidget

from core.mongo_client import MongoClientWrapper
from gui.collection_panel import CollectionPanelMixin
from gui.connection_dialog import ConnectionDialog

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QTextEdit


class ConnectionWidgetsMixin(CollectionPanelMixin):
    connection_layout: "QVBoxLayout"
    conn_manager: Any
    result_display: "QTextEdit"
    mongo_client: Any
    query_input: Any
    data_table: Any
    current_page: int
    page_size: int
    last_query: str
    results: Any
    prev_btn: Any
    next_btn: Any
    page_label: Any
    result_count_label: Any
    db_info_label: Any  # Ensure this is always present

    def load_connections(self) -> None:
        while self.connection_layout.count():
            child = self.connection_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()
        connections = self.conn_manager.get_connections()
        for conn in connections:
            self.add_connection_widget(conn)

    def add_connection_widget(self, conn: Dict[str, Any]) -> None:
        conn_widget = QWidget()
        conn_layout = QVBoxLayout(conn_widget)
        conn_layout.setContentsMargins(0, 0, 0, 0)
        conn_layout.setSpacing(10)
        name_label = QLabel(f"<b>{conn['name']}</b>")
        name_label.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        name_label.customContextMenuRequested.connect(
            lambda pos, n=conn["name"]: self.show_connection_context_menu(
                pos, n, name_label
            )
        )
        conn_layout.addWidget(name_label)
        info_label = QLabel(f"{conn['ip']}:{conn['port']}")
        conn_layout.addWidget(info_label)
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.connect_to_database(conn["name"]))
        conn_layout.addWidget(connect_btn)
        conn_layout.addStretch(1)
        self.connection_layout.addWidget(conn_widget)

    def show_connection_context_menu(
        self, pos: Any, name: str, widget: QWidget
    ) -> None:
        menu = QMenu(widget)
        edit_action = menu.addAction("Edit")
        duplicate_action = menu.addAction("Duplicate")
        remove_action = menu.addAction("Remove")
        action = menu.exec_(widget.mapToGlobal(pos))
        if action == edit_action:
            self.edit_connection(name)
        elif action == duplicate_action:
            self.duplicate_connection(name)
        elif action == remove_action:
            self.remove_connection(name)

    def edit_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            self.result_display.setPlainText(f"Connection '{name}' not found")
            return
        dialog = ConnectionDialog(self)
        dialog.name_input.setText(conn_data["name"])
        dialog.db_input.setText(conn_data["db"])
        dialog.ip_input.setText(conn_data["ip"])
        dialog.port_input.setText(str(conn_data["port"]))
        dialog.login_input.setText(conn_data.get("login", ""))
        dialog.password_input.setText(conn_data.get("password", ""))
        dialog.tls_checkbox.setChecked(conn_data.get("tls", False))
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                new_name, db, ip, port, login, password, tls = result
                try:
                    port_int = int(port)
                    self.conn_manager.update_connection(
                        name, db, ip, port_int, login, password, tls, new_name=new_name
                    )
                    self.load_connections()
                except ValueError:
                    self.result_display.setPlainText("Error: Invalid port number")

    def duplicate_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            self.result_display.setPlainText(f"Connection '{name}' not found")
            return
        conn_data = dict(conn_data)
        conn_data["login"] = conn_data.get("login", "")
        conn_data["password"] = conn_data.get("password", "")
        base_name = name
        if base_name.endswith(")"):
            import re

            base_name = re.sub(r" \(Copy( \d+)?\)$", "", base_name)
        new_name = f"{base_name} (Copy)"
        existing_names = {c["name"] for c in self.conn_manager.get_connections()}
        copy_idx = 2
        while new_name in existing_names:
            new_name = f"{base_name} (Copy {copy_idx})"
            copy_idx += 1
        try:
            self.conn_manager.add_connection(
                new_name,
                conn_data["db"],
                conn_data["ip"],
                conn_data["port"],
                conn_data.get("login", ""),
                conn_data.get("password", ""),
                conn_data.get("tls", False),
            )
            self.load_connections()
            self.result_display.setPlainText(f"Duplicated connection as '{new_name}'")
        except Exception as e:
            self.result_display.setPlainText(f"Failed to duplicate: {e}")

    def add_connection(self) -> None:
        dialog = ConnectionDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result:
                name, db, ip, port, login, password, tls = result
                try:
                    port_int = int(port)
                    self.conn_manager.add_connection(
                        name, db, ip, port_int, login, password, tls
                    )
                    self.load_connections()
                except ValueError:
                    self.result_display.setPlainText("Error: Invalid port number")

    def remove_connection(self, name: str) -> None:
        self.conn_manager.remove_connection(name)
        self.load_connections()

    def connect_to_database(self, connection_name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(connection_name)
        if not conn_data:
            self.result_display.setPlainText(
                f"Connection '{connection_name}' not found"
            )
            return
        try:
            self.mongo_client = MongoClientWrapper()
            success = self.mongo_client.connect(
                conn_data["ip"],
                conn_data["port"],
                conn_data["db"],
                conn_data.get("login"),
                conn_data.get("password"),
                conn_data.get("tls", False),
            )
            if success:
                self.current_connection = conn_data
                label = getattr(self, "db_info_label", None)
                if label:
                    label.setText(
                        f"Connected: {connection_name} ({conn_data['db']}@{conn_data['ip']}:{conn_data['port']})"
                    )
                self.result_display.setPlainText(f"Connected to: {connection_name}")
                self.load_collections()
            else:
                label = getattr(self, "db_info_label", None)
                if label:
                    label.setText(f"Failed to connect to {connection_name}")
                self.result_display.setPlainText(
                    f"Failed to connect to {connection_name}"
                )
        except Exception as e:
            label = getattr(self, "db_info_label", None)
            if label:
                label.setText(f"Connection error: {str(e)}")
            self.result_display.setPlainText(f"Connection error: {str(e)}")
"""

filepath = os.path.join("gui", "connection_widgets.py")
with open(filepath, "w") as f:
    f.write(fixed_content)
print(f"Fixed {filepath} successfully!")
