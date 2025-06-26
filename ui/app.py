import sys

from PyQt6.QtWidgets import QApplication

from ui.connection_manager_window import ConnectionManagerWindow
from ui.main_window import MainWindow


class App:
    def __init__(self) -> None:
        self.qt_app = QApplication(sys.argv)
        self.connection_manager_window = ConnectionManagerWindow()
        self.main_window = MainWindow()
        # Connect the signal so startup window works like the button
        self.connection_manager_window.connection_selected.connect(
            self.main_window.connect_to_database
        )

    def run(self) -> None:
        # Show connection manager at startup
        self.connection_manager_window.show()
        self.main_window.show()
        sys.exit(self.qt_app.exec())
