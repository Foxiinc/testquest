import cv2
from PySide6.QtCore import QThread, Signal
from services.face_service import encode_face, compare_faces


class FaceAuthThread(QThread):
    success = Signal()
    frame_ready = Signal(object)

    def __init__(self, known_encoding):
        super().__init__()
        self.known_encoding = known_encoding
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            self.frame_ready.emit(frame)

            if compare_faces(self.known_encoding, frame):
                self.success.emit()
                break

        cap.release()

    def stop(self):
        self.running = False
