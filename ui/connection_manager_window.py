import datetime
import json
import os
from typing import Any

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QAction,
    QDialog,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,  # Add QWidget for type annotation
)

from db.connection_manager import ConnectionManager
from ui.connection_dialog import ConnectionDialog
from ui.ui_utils import setup_dialog_layout
from utils.validators import validate_connection_params

NO_CONN_MSG = "No connection selected."
TO_URI_LABEL = "To URI"


class ConnectionManagerWindow(QDialog):
    connection_selected = pyqtSignal(str)  # connection name

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Connection Manager")
        self.setModal(True)  # Ensure window is modal and stays on top
        self.resize(700, 400)
        self.conn_manager = ConnectionManager()
        self.toolbar = QToolBar()
        self.action_new_conn = QAction("New connection", self)
        self.action_new_folder = QAction("New folder", self)
        self.action_edit = QAction("Edit", self)
        self.action_duplicate = QAction("Duplicate", self)
        self.action_delete = QAction("Delete", self)
        self.action_import = QAction("Import", self)
        self.action_export = QAction("Export", self)
        self.action_to_uri = QAction(TO_URI_LABEL, self)
        for action in [
            self.action_new_conn,
            self.action_new_folder,
            self.action_edit,
            self.action_duplicate,
            self.action_delete,
            self.action_import,
            self.action_export,
            self.action_to_uri,
        ]:
            self.toolbar.addAction(action)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["Name", "DB Server", "Security", "Last connected", "Last modified"]
        )
        self.btn_connect = QPushButton("Connect")
        self.btn_close = QPushButton("Close")
        widgets = [self.toolbar, self.tree]
        button_widgets: list[QWidget] = [self.btn_connect, self.btn_close]
        setup_dialog_layout(self, widgets, button_widgets)

        self.btn_close.clicked.connect(self.reject)
        self.btn_connect.clicked.connect(self.connect_selected)
        self.action_new_conn.triggered.connect(self.add_connection)
        self.action_edit.triggered.connect(self.edit_selected)
        self.action_delete.triggered.connect(self.delete_selected)
        self.action_duplicate.triggered.connect(self.duplicate_selected)
        self.action_import.triggered.connect(self.import_connections)
        self.action_export.triggered.connect(self.export_connections)
        self.action_to_uri.triggered.connect(self.copy_uri_selected)
        self.action_new_folder.triggered.connect(self.add_folder)
        self.tree.itemDoubleClicked.connect(self.connect_selected)

        self.load_connections()

    def load_connections(self) -> None:
        self.tree.clear()
        connections = self.conn_manager.get_connections()
        root = QTreeWidgetItem(["Local resources", "", "", "", ""])
        for conn in connections:
            # Ensure last_connected and last_modified are present
            last_connected = conn.get("last_connected", "")
            last_modified = conn.get("last_modified", "")
            item = QTreeWidgetItem(
                [
                    conn.get("name", ""),
                    f"{conn.get('ip', '')}:{conn.get('port', '')}",
                    conn.get("login", ""),
                    str(last_connected),
                    str(last_modified),
                ]
            )
            item.setData(0, int(Qt.ItemDataRole.UserRole), conn)
            root.addChild(item)
        self.tree.addTopLevelItem(root)
        self.tree.expandAll()

    def add_connection(self) -> None:
        dlg = ConnectionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            result = dlg.get_result() if hasattr(dlg, "get_result") else None
            if result:
                name, db, ip, port, login, password, tls = result
                is_valid, error_msg = validate_connection_params(ip, port, db)
                if not is_valid:
                    QMessageBox.critical(self, "Validation Error", error_msg)
                    return
                now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
                # Save extra fields manually after add_connection
                self.conn_manager.add_connection(
                    name, db, ip, int(port), login, password, tls
                )
                # Patch file to add last_connected/last_modified
                path = os.path.join(self.conn_manager.storage_path, f"{name}.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                data["last_connected"] = ""
                data["last_modified"] = now
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                self.load_connections()

    def get_selected_connection(self) -> dict[str, Any] | None:
        item = self.tree.currentItem()
        if item and item.parent():
            data = item.data(0, int(Qt.ItemDataRole.UserRole))
            if isinstance(data, dict):
                return data
            return None
        return None

    def edit_selected(self) -> None:
        conn = self.get_selected_connection()
        if not conn:
            QMessageBox.warning(self, "Edit Connection", NO_CONN_MSG)
            return
        dlg = ConnectionDialog(self)
        dlg.name_input.setText(conn.get("name", ""))
        dlg.db_input.setText(conn.get("db", ""))
        dlg.ip_input.setText(conn.get("ip", ""))
        dlg.port_input.setText(str(conn.get("port", "")))
        dlg.login_input.setText(conn.get("login", ""))
        dlg.password_input.setText(conn.get("password", ""))
        dlg.tls_checkbox.setChecked(conn.get("tls", False))
        if dlg.exec_() == QDialog.Accepted:
            result = dlg.get_result() if hasattr(dlg, "get_result") else None
            if result:
                name, db, ip, port, login, password, tls = result
                is_valid, error_msg = validate_connection_params(ip, port, db)
                if not is_valid:
                    QMessageBox.critical(self, "Validation Error", error_msg)
                    return
                now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
                self.conn_manager.update_connection(
                    conn["name"], db, ip, int(port), login, password, tls, new_name=name
                )
                # Patch file to update last_modified
                path = os.path.join(self.conn_manager.storage_path, f"{name}.json")
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                data["last_connected"] = data.get("last_connected", "")
                data["last_modified"] = now
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                self.load_connections()

    def delete_selected(self) -> None:
        conn = self.get_selected_connection()
        if not conn:
            QMessageBox.warning(self, "Delete Connection", NO_CONN_MSG)
            return
        name = conn.get("name") or ""
        reply = QMessageBox.question(
            self,
            "Delete Connection",
            f"Delete connection '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes and name:
            self.conn_manager.remove_connection(name)
            self.load_connections()

    def duplicate_selected(self) -> None:
        conn = self.get_selected_connection()
        if not conn:
            QMessageBox.warning(self, "Duplicate Connection", NO_CONN_MSG)
            return
        new_name = f"{conn['name']}_copy"
        counter = 1
        while self.conn_manager.get_connection_by_name(new_name):
            new_name = f"{conn['name']}_copy_{counter}"
            counter += 1
        self.conn_manager.add_connection(
            new_name,
            conn["db"],
            conn["ip"],
            int(conn["port"]),
            conn.get("login"),
            conn.get("password"),
            conn.get("tls", False),
        )
        self.load_connections()

    def connect_selected(self, *args: Any) -> None:
        conn = self.get_selected_connection()
        if conn:
            now = datetime.datetime.now().isoformat(sep=" ", timespec="seconds")
            conn["last_connected"] = now
            conn["last_modified"] = now
            # Patch file to update last_connected/last_modified
            path = os.path.join(self.conn_manager.storage_path, f"{conn['name']}.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data["last_connected"] = now
            data["last_modified"] = now
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            self.selected_connection = conn
            self.connection_selected.emit(conn["name"])
            self.accept()

    def import_connections(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Connections", "", "JSON Files (*.json);;All Files (*)"
        )
        if path:
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                # Accept both a list of connections or a single connection
                if isinstance(data, dict):
                    data = [data]
                for conn in data:
                    self.conn_manager.add_connection(
                        conn["name"],
                        conn["db"],
                        conn["ip"],
                        int(conn["port"]),
                        conn.get("login"),
                        conn.get("password"),
                        conn.get("tls", False),
                    )
                self.load_connections()
                QMessageBox.information(self, "Import", "Connections imported.")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def export_connections(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Connections",
            "connections_export.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if path:
            try:
                connections = self.conn_manager.get_connections()
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(connections, f, indent=2)
                QMessageBox.information(self, "Export", "Connections exported.")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def copy_uri_selected(self) -> None:
        conn = self.get_selected_connection()
        if not conn:
            QMessageBox.warning(self, TO_URI_LABEL, NO_CONN_MSG)
            return
        # Build MongoDB URI
        userinfo = (
            f"{conn['login']}:{conn['password']}@"
            if conn.get("login") and conn.get("password")
            else ""
        )
        tls = "?tls=true" if conn.get("tls", False) else ""
        uri = f"mongodb://{userinfo}{conn['ip']}:{conn['port']}/{conn['db']}{tls}"
        # Copy to clipboard
        clipboard = QGuiApplication.clipboard() if QGuiApplication.instance() else None
        if clipboard:
            clipboard.setText(uri)
            QMessageBox.information(
                self, TO_URI_LABEL, f"URI copied to clipboard:\n{uri}"
            )
        else:
            QMessageBox.warning(
                self, TO_URI_LABEL, f"Could not copy URI. Clipboard unavailable.\n{uri}"
            )

    def add_folder(self) -> None:
        # For now, just add a new folder under root
        name, ok = QFileDialog.getSaveFileName(self, "New Folder Name", "", "")
        if ok and name:
            folder_item = QTreeWidgetItem([name, "", "", "", ""])
            self.tree.addTopLevelItem(folder_item)
