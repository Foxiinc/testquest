import cv2
import face_recognition
from base_window import BaseWindow
from services.camera_thread import FaceAuthThread
from services.face_service import encode_face
from PySide6.QtGui import QImage, QPixmap


class AuthWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.load_ui("ui/auth.ui")

        self.ui.btn_auth.clicked.connect(self.start_auth)

    def start_auth(self):
        operator_id = self.ui.input_id.text()
        path = f"photos/ID_{operator_id}.jpg"

        img = face_recognition.load_image_file(path)
        known_encoding = face_recognition.face_encodings(img)[0]

        self.thread = FaceAuthThread(known_encoding)
        self.thread.frame_ready.connect(self.update_camera)
        self.thread.success.connect(self.auth_success)

        self.thread.start()
        self.ui.label_terminal.setText("Идёт распознавание лица...")

    def update_camera(self, frame):
        rgb = frame[:, :, ::-1]
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(img)
        self.ui.label_camera.setPixmap(pix)

    def auth_success(self):
        self.ui.label_terminal.setText("Оператор определён!")
        self.thread.stop()
