from typing import TYPE_CHECKING, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.mongo_client import MongoClientWrapper
from gui.collection_panel import CollectionPanelMixin
from gui.connection_dialog import ConnectionDialog

CONNECTION_ERROR_TITLE = "Connection Error"

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
    active_clients: dict[str, MongoClientWrapper]

    def __init__(self) -> None:
        super().__init__()
        self.active_clients = {}  # connection_name -> MongoClientWrapper

    def load_connections(self) -> None:
        count = self.connection_layout.count()
        while count:
            child = self.connection_layout.takeAt(0)
            if child and child.widget():
                widget = child.widget()
                if widget:
                    widget.deleteLater()
            count -= 1
        connections = self.conn_manager.get_connections()
        for conn in connections:
            self.add_connection_widget(conn)

    def add_connection_widget(self, conn: dict[str, Any]) -> None:
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
        details = QLabel(
            f"{conn['db']}@{conn['ip']}:{conn['port']}{' (TLS)' if conn.get('tls', False) else ''}"
        )
        conn_layout.addWidget(details)
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(lambda: self.connect_to_database(conn["name"]))
        conn_layout.addWidget(connect_btn)
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

    def add_connection(self) -> None:
        dialog = ConnectionDialog(None)
        if dialog.exec_() == QDialog.Accepted:
            conn_data = dialog.get_connection_data()
            try:
                self.conn_manager.add_connection(conn_data)
                self.load_connections()
            except Exception:
                pass

    def edit_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            return
        dialog = ConnectionDialog(None)
        dialog.name_input.setText(conn_data["name"])
        dialog.db_input.setText(conn_data["db"])
        dialog.ip_input.setText(conn_data["ip"])
        dialog.port_input.setText(str(conn_data["port"]))
        dialog.login_input.setText(conn_data.get("login", ""))
        dialog.password_input.setText(conn_data.get("password", ""))
        dialog.tls_checkbox.setChecked(conn_data.get("tls", False))
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_connection_data()
            try:
                self.conn_manager.update_connection(
                    name,
                    updated_data["db"],
                    updated_data["ip"],
                    updated_data["port"],
                    updated_data.get("login"),
                    updated_data.get("password"),
                    updated_data.get("tls", False),
                )
                self.load_connections()
            except Exception:
                pass

    def duplicate_connection(self, name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(name)
        if not conn_data:
            return
        try:
            new_name = f"{name}_copy"
            counter = 1
            while self.conn_manager.get_connection_by_name(new_name):
                new_name = f"{name}_copy_{counter}"
                counter += 1
            conn_data_copy = conn_data.copy()
            conn_data_copy["name"] = new_name
            self.conn_manager.add_connection(conn_data_copy)
            self.load_connections()
        except Exception:
            pass

    def edit_and_connect(self) -> None:
        dialog = ConnectionDialog(None)
        if dialog.exec_() == QDialog.Accepted:
            conn_data = dialog.get_connection_data()
            try:
                self.conn_manager.add_connection(conn_data)
                self.load_connections()
                self.connect_to_database(conn_data["name"])
            except ValueError:
                pass

    def remove_connection(self, name: str) -> None:
        self.conn_manager.remove_connection(name)
        self.load_connections()

    def connect_to_database(self, connection_name: str) -> None:
        conn_data = self.conn_manager.get_connection_by_name(connection_name)
        parent_widget = getattr(self, "collection_tree", None)
        if not conn_data:
            QMessageBox.critical(
                parent_widget,
                CONNECTION_ERROR_TITLE,
                f"Connection '{connection_name}' not found",
            )
            return
        try:
            mongo_client = MongoClientWrapper()
            success = mongo_client.connect(
                conn_data["ip"],
                conn_data["port"],
                conn_data["db"],
                conn_data.get("login"),
                conn_data.get("password"),
                conn_data.get("tls", False),
            )
            if success:
                self.active_clients[connection_name] = mongo_client
                # Add this database to the collections tree
                self.add_database_collections(connection_name, mongo_client)
            else:
                QMessageBox.critical(
                    parent_widget,
                    CONNECTION_ERROR_TITLE,
                    f"Failed to connect to {connection_name}",
                )
        except Exception as e:
            QMessageBox.critical(parent_widget, CONNECTION_ERROR_TITLE, str(e))

    def disconnect_database(self, connection_name: str) -> None:
        # Remove client and its collections from the tree
        if connection_name in self.active_clients:
            del self.active_clients[connection_name]
            self.clear_database_collections(connection_name)
