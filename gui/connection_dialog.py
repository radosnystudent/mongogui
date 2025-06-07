from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Connection Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Database Name:"))
        layout.addWidget(self.db_input)
        layout.addWidget(QLabel("IP Address:"))
        layout.addWidget(self.ip_input)
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_input)
        layout.addWidget(QLabel("Login:"))
        layout.addWidget(self.login_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.show_password_checkbox)
        layout.addWidget(self.tls_checkbox)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

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
        if name and db and ip and port:
            self.connection_result = (name, db, ip, port, login, password, tls)
            super().accept()

    def get_result(self) -> tuple[str, str, str, str, str, str, bool] | None:
        return self.connection_result
