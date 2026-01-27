🧠 0. Минимальная структура проекта
main.py
base_window.py
style.qss

start_window.py
register_window.py
auth_window.py

services/
    face_service.py
    camera_thread.py

ui/
    start.ui
    register.ui
    auth.ui

photos/
operators_db.csv

🧩 1. Загрузка .ui в любом окне
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMainWindow

class BaseWindow(QMainWindow):
    def load_ui(self, path):
        loader = QUiLoader()
        self.ui = loader.load(path, self)

▶️ 2. Переход между окнами
def open_window(self, WindowClass):
    self.w = WindowClass()
    self.w.show()
    self.close()


Использование:

self.ui.btn_register.clicked.connect(
    lambda: self.open_window(RegisterWindow)
)

🧍 3. Получить текст из поля
text = self.ui.input_lastname.text()

💾 4. Запись в CSV через pandas
import pandas as pd

def save_csv(data, file="operators_db.csv"):
    try:
        df = pd.read_csv(file)
    except:
        df = pd.DataFrame()

    df = pd.concat([df, pd.DataFrame([data])])
    df.to_csv(file, index=False)

📸 5. Сделать фото с камеры
import cv2

def capture_photo(path):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imwrite(path, frame)

😀 6. Face encoding / compare
import face_recognition

def get_encoding(img_path):
    img = face_recognition.load_image_file(img_path)
    return face_recognition.face_encodings(img)[0]


def compare(known_encoding, frame):
    rgb = frame[:, :, ::-1]
    enc = face_recognition.face_encodings(rgb)
    if not enc:
        return False
    return face_recognition.compare_faces([known_encoding], enc[0])[0]

🧵 7. QThread под камеру (антифриз)
from PySide6.QtCore import QThread, Signal
import cv2

class CameraThread(QThread):
    frame_ready = Signal(object)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)
        while self.running:
            ret, frame = cap.read()
            if ret:
                self.frame_ready.emit(frame)
        cap.release()

    def stop(self):
        self.running = False

🖼️ 8. Показать кадр в QLabel
from PySide6.QtGui import QImage, QPixmap

def show_frame(label, frame):
    rgb = frame[:, :, ::-1]
    h, w, ch = rgb.shape
    img = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(img))

⏱ 9. Таймер 9 часов
from PySide6.QtCore import QTimer, QTime

self.time_left = QTime(9,0,0)
self.timer = QTimer()
self.timer.timeout.connect(self.tick)
self.timer.start(1000)

def tick(self):
    self.time_left = self.time_left.addSecs(-1)
    self.ui.label_timer.setText(self.time_left.toString())

🎨 10. Подключить стиль
with open("style.qss") as f:
    app.setStyleSheet(f.read())

🚦 11. Поменять текст/цвет статуса
self.ui.label_status.setText("НОРМА")
self.ui.label_status.setStyleSheet("color: green; font-weight: bold;")

🔘 12. Кнопка нажата
self.ui.btn_save.clicked.connect(self.save)

🧭 13. ObjectName, которые должны быть в Designer
btn_register
btn_auth
btn_save
input_lastname
input_firstname
input_middlename
input_age
input_id
label_camera
label_terminal
label_status
label_timer
