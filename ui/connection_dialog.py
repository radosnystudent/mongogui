from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QWidget,
)

from ui.ui_utils import setup_dialog_layout
from utils.validators import validate_connection_params


class ConnectionDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Connection")
        self.setMinimumWidth(400)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint  # type: ignore
        )
        self.name_input = QLineEdit()
        self.db_input = QLineEdit()
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.login_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.show_password_checkbox = QCheckBox("Show Password")
        self.tls_checkbox = QCheckBox("Use TLS/SSL")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")
        self.connection_result: tuple[str, str, str, str, str, str, bool] | None = None

        widgets = [
            QLabel("Connection Name:"),
            self.name_input,
            QLabel("Database Name:"),
            self.db_input,
            QLabel("IP Address:"),
            self.ip_input,
            QLabel("Port:"),
            self.port_input,
            QLabel("Login:"),
            self.login_input,
            QLabel("Password:"),
            self.password_input,
            self.show_password_checkbox,
            self.tls_checkbox,
        ]
        button_widgets: list[QWidget] = [self.ok_btn, self.cancel_btn]
        setup_dialog_layout(self, widgets, button_widgets)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.show_password_checkbox.stateChanged.connect(
            self.toggle_password_visibility
        )

    def toggle_password_visibility(self, state: int) -> None:
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def accept(self) -> None:
        name = self.name_input.text().strip()
        db = self.db_input.text().strip()
        ip = self.ip_input.text().strip()
        port = self.port_input.text().strip()
        login = self.login_input.text().strip()
        password = self.password_input.text().strip()
        tls = self.tls_checkbox.isChecked()
        if not (name and db and ip and port):
            QMessageBox.critical(self, "Validation Error", "All fields except login/password are required.")
            return
        is_valid, error_msg = validate_connection_params(ip, port, db)
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", error_msg)
            return
        self.connection_result = (name, db, ip, port, login, password, tls)
        super().accept()

    def get_result(self) -> tuple[str, str, str, str, str, str, bool] | None:
        return self.connection_result
