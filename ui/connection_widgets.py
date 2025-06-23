from typing import Any

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

from ui.collection_panel import CollectionPanelMixin
from ui.connection_dialog import ConnectionDialog

CONNECTION_ERROR_TITLE = "Connection Error"


class ConnectionWidgetManager:
    def __init__(
        self, connection_layout: QVBoxLayout, conn_manager: Any, ui_handler: Any
    ) -> None:
        self.connection_layout = connection_layout
        self.conn_manager = conn_manager
        self.ui_handler = ui_handler

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
            lambda pos, n=conn["name"]: self.ui_handler.show_connection_context_menu(
                pos, n, name_label
            )
        )
        conn_layout.addWidget(name_label)
        details = QLabel(
            f"{conn['db']}@{conn['ip']}:{conn['port']}{' (TLS)' if conn.get('tls', False) else ''}"
        )
        conn_layout.addWidget(details)
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(
            lambda: self.ui_handler.connect_to_database(conn["name"])
        )
        conn_layout.addWidget(connect_btn)
        self.connection_layout.addWidget(conn_widget)

    def remove_connection(self, name: str) -> None:
        self.conn_manager.remove_connection(name)
        self.load_connections()


class ConnectionStateManager:
    def __init__(self, mongo_client_factory: Any) -> None:
        self.active_clients: dict[str, Any] = {}
        self.mongo_client_factory = mongo_client_factory

    def connect_to_database(
        self,
        connection_name: str,
        conn_manager: Any,
        parent_widget: QWidget,
        add_database_collections: Any,
    ) -> None:
        conn_data = conn_manager.get_connection_by_name(connection_name)
        if not conn_data:
            QMessageBox.critical(
                parent_widget,
                CONNECTION_ERROR_TITLE,
                f"Connection '{connection_name}' not found",
            )
            return
        try:
            mongo_client = self.mongo_client_factory()
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
                add_database_collections(connection_name, mongo_client)
            else:
                QMessageBox.critical(
                    parent_widget,
                    CONNECTION_ERROR_TITLE,
                    f"Failed to connect to {connection_name}",
                )
        except Exception as e:
            QMessageBox.critical(parent_widget, CONNECTION_ERROR_TITLE, str(e))

    def disconnect_database(self, connection_name: str, clear_database_collections: Any) -> None:
        if connection_name in self.active_clients:
            del self.active_clients[connection_name]
            clear_database_collections(connection_name)


class ConnectionUIHandler:
    def __init__(self, conn_manager: Any, widget_manager: Any, state_manager: Any) -> None:
        self.conn_manager = conn_manager
        self.widget_manager = widget_manager
        self.state_manager = state_manager

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
            self.widget_manager.remove_connection(name)

    def add_connection(self) -> None:
        dialog = ConnectionDialog(None)
        if dialog.exec_() == QDialog.Accepted:
            conn_result = dialog.get_result()
            if conn_result:
                name, db, ip, port, login, password, tls = conn_result
                try:
                    self.conn_manager.add_connection(
                        name, db, ip, int(port), login, password, tls
                    )
                    self.widget_manager.load_connections()
                except Exception as e:
                    QMessageBox.critical(
                        None, CONNECTION_ERROR_TITLE, f"Failed to add connection: {e}"
                    )

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
            updated_result = dialog.get_result()
            if updated_result:
                name_new, db, ip, port, login, password, tls = updated_result
                try:
                    self.conn_manager.update_connection(
                        name_new,
                        db,
                        ip,
                        int(port),
                        login,
                        password,
                        tls,
                    )
                    self.widget_manager.load_connections()
                except Exception as e:
                    QMessageBox.critical(
                        None,
                        CONNECTION_ERROR_TITLE,
                        f"Failed to update connection: {e}",
                    )

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
            db = conn_data["db"]
            ip = conn_data["ip"]
            port = int(conn_data["port"])
            login = conn_data.get("login")
            password = conn_data.get("password")
            tls = conn_data.get("tls", False)
            self.conn_manager.add_connection(
                new_name, db, ip, port, login, password, tls
            )
            self.widget_manager.load_connections()
        except Exception as e:
            QMessageBox.critical(
                None, CONNECTION_ERROR_TITLE, f"Failed to duplicate connection: {e}"
            )

    def edit_and_connect(self) -> None:
        dialog = ConnectionDialog(None)
        if dialog.exec_() == QDialog.Accepted:
            conn_result = dialog.get_result()
            if conn_result:
                name, db, ip, port, login, password, tls = conn_result
                try:
                    self.conn_manager.add_connection(
                        name, db, ip, int(port), login, password, tls
                    )
                    self.widget_manager.load_connections()
                    self.connect_to_database(name)
                except Exception as e:
                    QMessageBox.critical(
                        None, CONNECTION_ERROR_TITLE, f"Failed to add and connect: {e}"
                    )

    def connect_to_database(self, connection_name: str) -> None:
        # This method delegates to the state manager
        parent_widget = getattr(self.widget_manager, "collection_tree", None)
        self.state_manager.connect_to_database(
            connection_name,
            self.conn_manager,
            parent_widget,
            getattr(
                self.widget_manager, "add_database_collections", lambda *a, **kw: None
            ),
        )

    def disconnect_database(self, connection_name: str) -> None:
        self.state_manager.disconnect_database(
            connection_name,
            getattr(
                self.widget_manager, "clear_database_collections", lambda *a, **kw: None
            ),
        )


# Refactored mixin using composition
class ConnectionWidgetsMixin(CollectionPanelMixin):
    def __init__(self, mongo_client_factory: Any) -> None:
        super().__init__()
        # Ensure these are initialized before use
        if not hasattr(self, "conn_manager"):
            self.conn_manager = None  # Should be set by subclass or externally
        if not hasattr(self, "connection_layout"):
            self.connection_layout = QVBoxLayout()  # Or set by subclass
        self.state_manager = ConnectionStateManager(mongo_client_factory)
        self.ui_handler = ConnectionUIHandler(
            self.conn_manager, self, self.state_manager
        )
        self.widget_manager = ConnectionWidgetManager(
            self.connection_layout, self.conn_manager, self.ui_handler
        )

    # Optionally, expose methods for compatibility
    def load_connections(self) -> None:
        self.widget_manager.load_connections()

    def add_connection_widget(self, conn: dict[str, Any]) -> None:
        self.widget_manager.add_connection_widget(conn)

    def show_connection_context_menu(
        self, pos: Any, name: str, widget: QWidget
    ) -> None:
        self.ui_handler.show_connection_context_menu(pos, name, widget)

    def add_connection(self) -> None:
        self.ui_handler.add_connection()

    def edit_connection(self, name: str) -> None:
        self.ui_handler.edit_connection(name)

    def duplicate_connection(self, name: str) -> None:
        self.ui_handler.duplicate_connection(name)

    def edit_and_connect(self) -> None:
        self.ui_handler.edit_and_connect()

    def remove_connection(self, name: str) -> None:
        self.widget_manager.remove_connection(name)

    def connect_to_database(self, connection_name: str) -> None:
        self.ui_handler.connect_to_database(connection_name)

    def disconnect_database(self, connection_name: str) -> None:
        self.ui_handler.disconnect_database(connection_name)
