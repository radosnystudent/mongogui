from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
import sys

class App:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.main_window = MainWindow()

    def run(self):
        self.main_window.show()
        sys.exit(self.qt_app.exec_())