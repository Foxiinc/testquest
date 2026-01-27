import sys
from PySide6.QtWidgets import QApplication
from start_window import StartWindow

app = QApplication(sys.argv)

# Подключаем стиль
with open("style.qss", "r") as f:
    app.setStyleSheet(f.read())

window = StartWindow()
window.show()

sys.exit(app.exec())
