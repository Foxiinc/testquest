from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow


class BaseWindow(QMainWindow):
    def load_ui(self, path):
        loader = QUiLoader()
        self.ui = loader.load(path, self)
