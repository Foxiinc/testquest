import cv2
import face_recognition
import numpy as np
import os
import pickle
from typing import Dict


class FaceRecognizer:
    def __init__(self):
        self.known_faces: Dict[str, np.ndarray] = {}
        self.tolerance = 0.6
        self.load_known_faces()
        self.frame_skip = 3
        self.frame_count = 0
        self.last_face_locations = []  # Сохраняем последние позиции лиц
        self.last_face_names = []      # Сохраняем последние имена
        
    def load_known_faces(self):
        """Загружает все известные лица из файла"""
        if os.path.exists('known_faces.pkl'):
            with open('known_faces.pkl', 'rb') as f:
                self.known_faces = pickle.load(f)
                print(f"Загружено {len(self.known_faces)} известных лиц из known_faces.pkl")
        else:
            print("Файл known_faces.pkl не найден, создается новая база")
                
    def save_known_faces(self):
        """Сохраняет известные лица в файл"""
        with open('known_faces.pkl', 'wb') as f:
            pickle.dump(self.known_faces, f)
        print(f"База сохранена в known_faces.pkl ({len(self.known_faces)} лиц)")

    def add_new_face(self, name: str, face_encoding: np.ndarray):
        """Добавляет новое лицо в базу"""
        self.known_faces[name] = face_encoding
        self.save_known_faces()



    def run(self):
        """Запускает распознавание лиц"""
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("Ошибка: не удалось открыть камеру")
            return
            
        print("Нажмите 'q' для выхода, 's' для сохранения нового лица")
        print(f"Лица сохраняются в файл: {os.path.abspath('known_faces.pkl')}")
        
        try:
            while True:
                ret, frame = camera.read()
                if not ret:
                    continue
                
                self.frame_count += 1
                
                # Обрабатываем распознавание только каждый N-й кадр
                if self.frame_count % self.frame_skip == 0:
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    # Масштабируем координаты обратно
                    self.last_face_locations = [(top*4, right*4, bottom*4, left*4) for (top, right, bottom, left) in face_locations]
                    self.last_face_names = []
                    
                    for face_encoding in face_encodings:
                        name = "Unknown"
                        
                        if self.known_faces:
                            matches = face_recognition.compare_faces(list(self.known_faces.values()), face_encoding, tolerance=self.tolerance)
                            if True in matches:
                                match_index = matches.index(True)
                                name = list(self.known_faces.keys())[match_index]
                        
                        self.last_face_names.append(name)
                
                # Рисуем рамки на каждом кадре используя последние данные
                min_count = min(len(self.last_face_locations), len(self.last_face_names))
                for i in range(min_count):
                    (top, right, bottom, left) = self.last_face_locations[i]
                    name = self.last_face_names[i]
                    color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
                    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                
                cv2.imshow('Face Recognition', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Сохраняем текущее лицо
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    if face_locations:
                        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                        if face_encodings:
                            name = input("\nВведите имя для сохранения: ").strip()
                            if name:
                                self.add_new_face(name, face_encodings[0])
                                print(f"Лицо '{name}' сохранено!")
                    
        finally:
            camera.release()
            cv2.destroyAllWindows()




if __name__ == "__main__":
    recognizer = FaceRecognizer()
    recognizer.run()