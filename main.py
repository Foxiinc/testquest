#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Нейрободрор - Программа для мониторинга состояния водителей
Конкурсное задание WorldSkills / Профессионалы
"""

import sys
import os
import json
import random
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import cv2
import face_recognition
from PIL import Image

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QLineEdit, QSpinBox, QFrame,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox,
    QStackedWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal, QRect
from PySide6.QtGui import (
    QFont, QPixmap, QImage, QPainter, QPen, QColor, QIcon
)
from PySide6.QtMultimedia import QCamera, QMediaCaptureSession
from PySide6.QtMultimediaWidgets import QVideoWidget


class CameraThread(QThread):
    """Поток для работы с камерой и распознавания лиц"""
    frame_ready = Signal(np.ndarray)
    face_detected = Signal(bool, np.ndarray)  # найдено лицо, embedding
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.cap = None
        self.known_encodings = []
        self.tolerance = 0.45
        
    def start_camera(self):
        """Запуск камеры"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Ошибка: не удалось открыть камеру")
            return False
        self.running = True
        self.start()
        return True
        
    def stop_camera(self):
        """Остановка камеры"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.quit()
        self.wait()
        
    def load_known_faces(self, database_path):
        """Загрузка известных лиц из базы"""
        self.known_encodings = []
        db_path = Path(database_path)
        if db_path.exists():
            for npy_file in db_path.glob("*.npy"):
                try:
                    encoding = np.load(npy_file)
                    self.known_encodings.append(encoding)
                except Exception as e:
                    print(f"Ошибка загрузки {npy_file}: {e}")
                    
    def run(self):
        """Основной цикл обработки видео"""
        while self.running:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Отправляем кадр для отображения
                    self.frame_ready.emit(frame)
                    
                    # Поиск лиц каждый 5-й кадр для производительности
                    if hasattr(self, 'frame_count'):
                        self.frame_count += 1
                    else:
                        self.frame_count = 0
                        
                    if self.frame_count % 5 == 0:
                        self.detect_faces(frame)
                        
            self.msleep(33)  # ~30 FPS
            
    def detect_faces(self, frame):
        """Обнаружение и распознавание лиц"""
        try:
            # Уменьшаем размер для ускорения
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Поиск лиц
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                # Берем первое найденное лицо
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if face_encodings:
                    face_encoding = face_encodings[0]
                    self.face_detected.emit(True, face_encoding)
                    return
                    
            self.face_detected.emit(False, np.array([]))
            
        except Exception as e:
            print(f"Ошибка распознавания: {e}")
            self.face_detected.emit(False, np.array([]))


class StartWindow(QWidget):
    """Стартовое окно выбора действий"""
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Выберите необходимые действия")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Кнопка регистрации
        reg_btn = QPushButton("Регистрация")
        reg_btn.setMinimumSize(200, 60)
        reg_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        reg_btn.clicked.connect(self.open_registration)
        
        # Кнопка авторизации
        auth_btn = QPushButton("Авторизация")
        auth_btn.setMinimumSize(200, 60)
        auth_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        auth_btn.clicked.connect(self.open_authorization)
        
        layout.addWidget(reg_btn)
        layout.addWidget(auth_btn)
        self.setLayout(layout)
        
    def open_registration(self):
        """Открыть окно регистрации"""
        self.main_app.show_registration()
        
    def open_authorization(self):
        """Открыть окно авторизации"""
        self.main_app.show_authorization()


class RegistrationWindow(QMainWindow):
    """Окно регистрации оператора"""
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.camera_thread = CameraThread()
        self.current_face_encoding = None
        self.face_encodings_buffer = []  # Буфер для усреднения
        self.operator_id = None
        self.init_ui()
        self.setup_camera()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Нейрободрор")
        self.setMinimumSize(1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Зеленая полоса сверху
        header = QFrame()
        header.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        header.setFixedHeight(80)
        
        header_layout = QVBoxLayout(header)
        title = QLabel("Нейрободрор")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Программа для мониторинга состояния водителей")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        # Основной контент
        content_layout = QHBoxLayout()
        
        # Левая колонка - регистрация данных
        left_widget = self.create_registration_form()
        left_widget.setMaximumWidth(300)
        
        # Центральная колонка - камера
        center_widget = self.create_camera_widget()
        center_widget.setMinimumWidth(400)
        
        # Правая колонка - информационный блок
        right_widget = self.create_info_widget()
        right_widget.setMaximumWidth(300)
        
        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(center_widget, 2)
        content_layout.addWidget(right_widget, 1)
        
        main_layout.addWidget(header)
        main_layout.addLayout(content_layout)
        
        # Кнопка "Далее" внизу
        self.next_btn = QPushButton("Далее")
        self.next_btn.setEnabled(False)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.next_btn.clicked.connect(self.proceed_to_monitoring)
        main_layout.addWidget(self.next_btn)
        
    def create_registration_form(self):
        """Создание формы регистрации"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Регистрация оператора")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Поля ввода
        layout.addWidget(QLabel("Фамилия"))
        self.surname_edit = QLineEdit()
        layout.addWidget(self.surname_edit)
        
        layout.addWidget(QLabel("Имя"))
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_edit)
        
        layout.addWidget(QLabel("Отчество"))
        self.patronymic_edit = QLineEdit()
        layout.addWidget(self.patronymic_edit)
        
        layout.addWidget(QLabel("Возраст"))
        self.age_spinbox = QSpinBox()
        self.age_spinbox.setRange(16, 100)
        self.age_spinbox.setValue(18)
        layout.addWidget(self.age_spinbox)
        
        # Кнопка записи
        record_btn = QPushButton("Записать")
        record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                padding: 8px;
                border: none;
                border-radius: 3px;
            }
        """)
        record_btn.clicked.connect(self.record_operator)
        layout.addWidget(record_btn)
        
        layout.addStretch()
        return widget
        
    def create_camera_widget(self):
        """Создание виджета камеры"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Идентификация")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Область для видео
        self.video_frame = QLabel()
        self.video_frame.setFixedSize(400, 300)
        self.video_frame.setStyleSheet("border: 2px solid #cccccc; background-color: #f0f0f0;")
        self.video_frame.setAlignment(Qt.AlignCenter)
        self.video_frame.setText("Инициализация камеры...")
        layout.addWidget(self.video_frame)
        
        # Статус
        self.camera_status = QLabel("❌ Оператор не определён")
        self.camera_status.setAlignment(Qt.AlignCenter)
        self.camera_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.camera_status)
        
        return widget
        
    def create_info_widget(self):
        """Создание информационного блока"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Информационный блок")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Статус оператора
        self.operator_status = QLabel("❌ Оператор не определён")
        self.operator_status.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.operator_status)
        
        # ID блок
        self.id_label = QLabel("ID не присвоен")
        self.id_label.setStyleSheet("""
            background-color: #F44336;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        layout.addWidget(self.id_label)
        
        # Сообщение о невозможности запуска
        self.launch_status = QLabel("Запуск программы невозможен")
        self.launch_status.setStyleSheet("color: red; font-style: italic;")
        layout.addWidget(self.launch_status)
        
        layout.addStretch()
        return widget
        
    def setup_camera(self):
        """Настройка камеры"""
        # Подключение сигналов
        self.camera_thread.frame_ready.connect(self.update_video_frame)
        self.camera_thread.face_detected.connect(self.on_face_detected)
        
        # Запуск камеры
        if self.camera_thread.start_camera():
            print("Камера запущена успешно")
        else:
            self.video_frame.setText("Ошибка: камера недоступна")
            
    def update_video_frame(self, frame):
        """Обновление кадра видео"""
        try:
            # Конвертация в RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Рисование рамки если лицо найдено
            if hasattr(self, 'face_found') and self.face_found:
                # Поиск лица для рамки
                small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
                face_locations = face_recognition.face_locations(small_frame)
                
                if face_locations:
                    # Масштабирование координат обратно
                    top, right, bottom, left = face_locations[0]
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Рисование зеленой рамки
                    cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 3)
            
            # Конвертация в QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Масштабирование под размер виджета
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.video_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            self.video_frame.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Ошибка обновления видео: {e}")
            
    def on_face_detected(self, found, encoding):
        """Обработка обнаружения лица"""
        self.face_found = found
        
        if found and len(encoding) > 0:
            self.camera_status.setText("✅ Оператор определён")
            self.camera_status.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            
            # Добавляем encoding в буфер для усреднения
            self.face_encodings_buffer.append(encoding)
            if len(self.face_encodings_buffer) > 5:
                self.face_encodings_buffer.pop(0)
                
            # Усредняем последние encodings
            if len(self.face_encodings_buffer) >= 3:
                self.current_face_encoding = np.mean(self.face_encodings_buffer, axis=0)
        else:
            self.camera_status.setText("❌ Оператор не определён")
            self.camera_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            
    def record_operator(self):
        """Запись данных оператора"""
        # Проверка заполненности полей
        if not all([self.surname_edit.text(), self.name_edit.text(), self.patronymic_edit.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return
            
        # Проверка наличия лица
        if self.current_face_encoding is None:
            QMessageBox.warning(self, "Ошибка", "Лицо не обнаружено! Посмотрите в камеру.")
            return
            
        try:
            # Создание папки базы данных
            db_path = Path("database")
            db_path.mkdir(exist_ok=True)
            
            # Генерация уникального ID
            self.operator_id = self.generate_unique_id()
            
            # Сохранение данных
            operator_data = {
                "id": self.operator_id,
                "surname": self.surname_edit.text(),
                "name": self.name_edit.text(),
                "patronymic": self.patronymic_edit.text(),
                "age": self.age_spinbox.value(),
                "registration_date": datetime.now().isoformat()
            }
            
            # Сохранение JSON
            with open(db_path / f"{self.operator_id}.json", "w", encoding="utf-8") as f:
                json.dump(operator_data, f, ensure_ascii=False, indent=2)
                
            # Сохранение encoding
            np.save(db_path / f"{self.operator_id}.npy", self.current_face_encoding)
            
            # Сохранение фото
            self.save_operator_photo()
            
            # Обновление интерфейса
            self.operator_status.setText("✅ Оператор определён")
            self.operator_status.setStyleSheet("color: green; font-weight: bold;")
            
            self.id_label.setText(f"ID {self.operator_id}")
            self.id_label.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            """)
            
            self.launch_status.setText("Готов к запуску программы")
            self.launch_status.setStyleSheet("color: green; font-style: normal;")
            
            self.next_btn.setEnabled(True)
            
            QMessageBox.information(self, "Успех", f"Оператор зарегистрирован!\nID: {self.operator_id}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")
            
    def generate_unique_id(self):
        """Генерация уникального 6-значного ID"""
        db_path = Path("database")
        existing_ids = set()
        
        if db_path.exists():
            for json_file in db_path.glob("*.json"):
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        existing_ids.add(data.get("id"))
                except:
                    pass
                    
        while True:
            new_id = random.randint(100000, 999999)
            if new_id not in existing_ids:
                return new_id
                
    def save_operator_photo(self):
        """Сохранение фото оператора"""
        try:
            # Получаем текущий кадр
            if self.camera_thread.cap and self.camera_thread.cap.isOpened():
                ret, frame = self.camera_thread.cap.read()
                if ret:
                    # Сохраняем как JPG
                    photo_path = Path("database") / f"{self.operator_id}.jpg"
                    cv2.imwrite(str(photo_path), frame)
        except Exception as e:
            print(f"Ошибка сохранения фото: {e}")
            
    def proceed_to_monitoring(self):
        """Переход к мониторингу"""
        self.camera_thread.stop_camera()
        self.main_app.show_monitoring(self.operator_id)
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.camera_thread.stop_camera()
        event.accept()


class AuthorizationWindow(QWidget):
    """Окно авторизации"""
    
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.camera_thread = CameraThread()
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Авторизация оператора")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        title = QLabel("Авторизация оператора")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Поле ввода ID
        id_label = QLabel("Введите ID:")
        layout.addWidget(id_label)
        
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText("Введите 6-значный ID")
        self.id_edit.setMaxLength(6)
        layout.addWidget(self.id_edit)
        
        # Кнопка авторизации
        auth_btn = QPushButton("Авторизоваться")
        auth_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                padding: 10px;
                border: none;
                border-radius: 5px;
            }
        """)
        auth_btn.clicked.connect(self.authorize)
        layout.addWidget(auth_btn)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def authorize(self):
        """Авторизация оператора"""
        operator_id = self.id_edit.text().strip()
        
        if len(operator_id) != 6 or not operator_id.isdigit():
            self.show_error("ID должен содержать 6 цифр")
            return
            
        # Проверка существования оператора
        db_path = Path("database")
        json_file = db_path / f"{operator_id}.json"
        npy_file = db_path / f"{operator_id}.npy"
        
        if not json_file.exists() or not npy_file.exists():
            self.show_error("Оператор с таким ID не найден")
            return
            
        # Загрузка данных оператора
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                operator_data = json.load(f)
                
            stored_encoding = np.load(npy_file)
            
            # Запуск камеры для проверки лица
            self.verify_face(operator_id, stored_encoding, operator_data)
            
        except Exception as e:
            self.show_error(f"Ошибка загрузки данных: {e}")
            
    def verify_face(self, operator_id, stored_encoding, operator_data):
        """Проверка лица через камеру"""
        self.status_label.setText("Посмотрите в камеру для проверки...")
        self.status_label.setStyleSheet("color: blue;")
        
        # Запуск камеры
        if not self.camera_thread.start_camera():
            self.show_error("Ошибка доступа к камере")
            return
            
        # Таймер для проверки лица
        self.verification_timer = QTimer()
        self.verification_timer.timeout.connect(lambda: self.check_face_match(operator_id, stored_encoding, operator_data))
        self.verification_timer.start(1000)  # Проверка каждую секунду
        
        # Таймаут авторизации
        self.timeout_timer = QTimer()
        self.timeout_timer.timeout.connect(self.verification_timeout)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.start(10000)  # 10 секунд на авторизацию
        
    def check_face_match(self, operator_id, stored_encoding, operator_data):
        """Проверка совпадения лица"""
        try:
            if self.camera_thread.cap and self.camera_thread.cap.isOpened():
                ret, frame = self.camera_thread.cap.read()
                if ret:
                    # Поиск лица
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locations = face_recognition.face_locations(rgb_frame)
                    
                    if face_locations:
                        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                        if face_encodings:
                            current_encoding = face_encodings[0]
                            
                            # Сравнение с сохраненным encoding
                            distance = face_recognition.face_distance([stored_encoding], current_encoding)[0]
                            
                            if distance < 0.45:  # Порог совпадения
                                self.authorization_success(operator_id, operator_data)
                                return
                                
        except Exception as e:
            print(f"Ошибка проверки лица: {e}")
            
    def authorization_success(self, operator_id, operator_data):
        """Успешная авторизация"""
        self.verification_timer.stop()
        self.timeout_timer.stop()
        self.camera_thread.stop_camera()
        
        self.status_label.setText("✅ Авторизация успешна!")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        
        QMessageBox.information(self, "Успех", f"Добро пожаловать, {operator_data['name']}!")
        
        # Переход к мониторингу
        self.main_app.show_monitoring(operator_id)
        self.close()
        
    def verification_timeout(self):
        """Таймаут авторизации"""
        self.verification_timer.stop()
        self.camera_thread.stop_camera()
        self.show_error("Время авторизации истекло")
        
    def show_error(self, message):
        """Показ ошибки"""
        self.status_label.setText(f"❌ {message}")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if hasattr(self, 'verification_timer'):
            self.verification_timer.stop()
        if hasattr(self, 'timeout_timer'):
            self.timeout_timer.stop()
        self.camera_thread.stop_camera()
        event.accept()


class MonitoringWindow(QMainWindow):
    """Главное окно мониторинга"""
    
    def __init__(self, main_app, operator_id):
        super().__init__()
        self.main_app = main_app
        self.operator_id = operator_id
        self.operator_data = None
        self.camera_thread = CameraThread()
        self.start_time = datetime.now()
        self.work_duration = timedelta(hours=10)  # 10 часов рабочего времени
        
        self.load_operator_data()
        self.init_ui()
        self.setup_camera()
        self.setup_timers()
        
    def load_operator_data(self):
        """Загрузка данных оператора"""
        try:
            json_file = Path("database") / f"{self.operator_id}.json"
            with open(json_file, "r", encoding="utf-8") as f:
                self.operator_data = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки данных оператора: {e}")
            
    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Нейрободрор - Мониторинг")
        self.setMinimumSize(1200, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Зеленая полоса сверху
        header = QFrame()
        header.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        header.setFixedHeight(80)
        
        header_layout = QVBoxLayout(header)
        title = QLabel("Нейрободрор")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        subtitle = QLabel("Программа для мониторинга состояния водителей")
        subtitle.setFont(QFont("Arial", 12))
        subtitle.setAlignment(Qt.AlignCenter)
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        
        # Основной контент
        content_layout = QHBoxLayout()
        
        # Левая колонка - информация оператора
        left_widget = self.create_operator_info()
        left_widget.setMaximumWidth(300)
        
        # Центральная колонка - камера
        center_widget = self.create_monitoring_camera()
        center_widget.setMinimumWidth(400)
        
        # Правая колонка - информационный блок
        right_widget = self.create_monitoring_info()
        right_widget.setMaximumWidth(300)
        
        content_layout.addWidget(left_widget, 1)
        content_layout.addWidget(center_widget, 2)
        content_layout.addWidget(right_widget, 1)
        
        main_layout.addWidget(header)
        main_layout.addLayout(content_layout)
        
        # Кнопка запуска мониторинга
        start_btn = QPushButton("Запуск мониторинга")
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                padding: 15px;
                border: none;
                border-radius: 5px;
            }
        """)
        start_btn.clicked.connect(self.start_monitoring)
        main_layout.addWidget(start_btn)
        
    def create_operator_info(self):
        """Создание блока информации об операторе"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Информация оператора")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Фото оператора
        self.photo_label = QLabel()
        self.photo_label.setFixedSize(150, 150)
        self.photo_label.setStyleSheet("border: 2px solid #cccccc; background-color: #f0f0f0;")
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.load_operator_photo()
        layout.addWidget(self.photo_label)
        
        if self.operator_data:
            # ФИО
            full_name = f"{self.operator_data['surname']} {self.operator_data['name']} {self.operator_data['patronymic']}"
            name_label = QLabel(full_name)
            name_label.setFont(QFont("Arial", 12, QFont.Bold))
            name_label.setWordWrap(True)
            layout.addWidget(name_label)
            
            # Возраст
            age_label = QLabel(f"Возраст: {self.operator_data['age']}")
            layout.addWidget(age_label)
            
        # Временные метки
        self.datetime_label = QLabel()
        self.start_time_label = QLabel(f"Время запуска ПО: {self.start_time.strftime('%H:%M:%S')}")
        self.work_time_label = QLabel("Время в дороге: 00:00:00")
        self.remaining_time_label = QLabel("Оставшееся время: 10:00:00")
        
        layout.addWidget(self.datetime_label)
        layout.addWidget(self.start_time_label)
        layout.addWidget(self.work_time_label)
        layout.addWidget(self.remaining_time_label)
        
        layout.addStretch()
        return widget
        
    def create_monitoring_camera(self):
        """Создание виджета камеры для мониторинга"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Мониторинг состояния")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Область для видео
        self.monitor_video_frame = QLabel()
        self.monitor_video_frame.setFixedSize(500, 375)
        self.monitor_video_frame.setStyleSheet("border: 2px solid #cccccc; background-color: #f0f0f0;")
        self.monitor_video_frame.setAlignment(Qt.AlignCenter)
        self.monitor_video_frame.setText("Инициализация камеры...")
        layout.addWidget(self.monitor_video_frame)
        
        # Статус мониторинга
        self.monitor_status = QLabel("Ожидание запуска мониторинга")
        self.monitor_status.setAlignment(Qt.AlignCenter)
        self.monitor_status.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.monitor_status)
        
        return widget
        
    def create_monitoring_info(self):
        """Создание информационного блока мониторинга"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title = QLabel("Информационный блок")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Статус оператора
        self.monitor_operator_status = QLabel("✅ Оператор определён")
        self.monitor_operator_status.setStyleSheet("color: green; font-weight: bold;")
        layout.addWidget(self.monitor_operator_status)
        
        # ID блок
        self.monitor_id_label = QLabel(f"ID {self.operator_id}")
        self.monitor_id_label.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        layout.addWidget(self.monitor_id_label)
        
        # Состояние мониторинга
        self.monitoring_state = QLabel("🟢 НОРМА")
        self.monitoring_state.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
        layout.addWidget(self.monitoring_state)
        
        layout.addStretch()
        return widget
        
    def load_operator_photo(self):
        """Загрузка фото оператора"""
        try:
            photo_path = Path("database") / f"{self.operator_id}.jpg"
            if photo_path.exists():
                pixmap = QPixmap(str(photo_path))
                scaled_pixmap = pixmap.scaled(self.photo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.photo_label.setPixmap(scaled_pixmap)
            else:
                self.photo_label.setText("Фото\nне найдено")
        except Exception as e:
            print(f"Ошибка загрузки фото: {e}")
            self.photo_label.setText("Ошибка\nзагрузки")
            
    def setup_camera(self):
        """Настройка камеры для мониторинга"""
        # Загрузка известных лиц
        self.camera_thread.load_known_faces("database")
        
        # Подключение сигналов
        self.camera_thread.frame_ready.connect(self.update_monitor_frame)
        self.camera_thread.face_detected.connect(self.on_monitor_face_detected)
        
    def setup_timers(self):
        """Настройка таймеров"""
        # Таймер обновления времени
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time_labels)
        self.time_timer.start(1000)  # Обновление каждую секунду
        
        # Таймер проверки лица (каждые 5 секунд)
        self.face_check_timer = QTimer()
        self.face_check_timer.timeout.connect(self.periodic_face_check)
        
    def update_time_labels(self):
        """Обновление временных меток"""
        now = datetime.now()
        
        # Текущее время
        self.datetime_label.setText(f"Дата/время: {now.strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Время работы
        work_elapsed = now - self.start_time
        hours, remainder = divmod(work_elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.work_time_label.setText(f"Время в дороге: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        
        # Оставшееся время
        remaining = self.work_duration - work_elapsed
        if remaining.total_seconds() > 0:
            hours, remainder = divmod(remaining.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.remaining_time_label.setText(f"Оставшееся время: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
        else:
            self.remaining_time_label.setText("Время работы истекло!")
            self.remaining_time_label.setStyleSheet("color: red; font-weight: bold;")
            
    def start_monitoring(self):
        """Запуск мониторинга"""
        if self.camera_thread.start_camera():
            self.monitor_status.setText("🟢 Мониторинг активен")
            self.monitor_status.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            
            # Запуск периодической проверки лица
            self.face_check_timer.start(5000)  # Каждые 5 секунд
        else:
            self.monitor_status.setText("❌ Ошибка запуска камеры")
            self.monitor_status.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            
    def update_monitor_frame(self, frame):
        """Обновление кадра мониторинга"""
        try:
            # Конвертация в RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Рисование рамки если лицо найдено
            if hasattr(self, 'monitor_face_found') and self.monitor_face_found:
                # Поиск лица для рамки
                small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)
                face_locations = face_recognition.face_locations(small_frame)
                
                if face_locations:
                    # Масштабирование координат обратно
                    top, right, bottom, left = face_locations[0]
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4
                    
                    # Рисование зеленой рамки
                    cv2.rectangle(rgb_frame, (left, top), (right, bottom), (0, 255, 0), 3)
            
            # Конвертация в QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Масштабирование под размер виджета
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(self.monitor_video_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            self.monitor_video_frame.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Ошибка обновления видео мониторинга: {e}")
            
    def on_monitor_face_detected(self, found, encoding):
        """Обработка обнаружения лица в мониторинге"""
        self.monitor_face_found = found
        
        if found and len(encoding) > 0:
            # Проверка совпадения с зарегистрированным оператором
            try:
                stored_encoding = np.load(f"database/{self.operator_id}.npy")
                distance = face_recognition.face_distance([stored_encoding], encoding)[0]
                
                if distance < 0.45:
                    self.monitor_operator_status.setText("✅ Оператор определён")
                    self.monitor_operator_status.setStyleSheet("color: green; font-weight: bold;")
                    self.monitoring_state.setText("🟢 НОРМА")
                    self.monitoring_state.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")
                else:
                    self.monitor_operator_status.setText("⚠️ Другой человек")
                    self.monitor_operator_status.setStyleSheet("color: orange; font-weight: bold;")
                    self.monitoring_state.setText("🟡 ВНИМАНИЕ")
                    self.monitoring_state.setStyleSheet("color: orange; font-weight: bold; font-size: 16px;")
                    
            except Exception as e:
                print(f"Ошибка проверки лица: {e}")
        else:
            self.monitor_operator_status.setText("❌ Оператор не определён")
            self.monitor_operator_status.setStyleSheet("color: red; font-weight: bold;")
            self.monitoring_state.setText("🔴 КРИТИЧНО")
            self.monitoring_state.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            
    def periodic_face_check(self):
        """Периодическая проверка лица"""
        # Эта функция вызывается каждые 5 секунд для дополнительных проверок
        pass
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        self.camera_thread.stop_camera()
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        if hasattr(self, 'face_check_timer'):
            self.face_check_timer.stop()
        event.accept()


class NeurobodrApp(QApplication):
    """Главное приложение"""
    
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("Нейрободрор")
        self.setApplicationVersion("1.0")
        
        # Создание папки базы данных
        Path("database").mkdir(exist_ok=True)
        
        # Стартовое окно
        self.start_window = StartWindow(self)
        self.start_window.show()
        
        # Другие окна
        self.registration_window = None
        self.authorization_window = None
        self.monitoring_window = None
        
    def show_registration(self):
        """Показать окно регистрации"""
        self.start_window.hide()
        self.registration_window = RegistrationWindow(self)
        self.registration_window.show()
        
    def show_authorization(self):
        """Показать окно авторизации"""
        self.start_window.hide()
        self.authorization_window = AuthorizationWindow(self)
        self.authorization_window.show()
        
    def show_monitoring(self, operator_id):
        """Показать окно мониторинга"""
        if self.registration_window:
            self.registration_window.hide()
        if self.authorization_window:
            self.authorization_window.hide()
            
        self.monitoring_window = MonitoringWindow(self, operator_id)
        self.monitoring_window.show()


def main():
    """Главная функция"""
    app = NeurobodrApp(sys.argv)
    
    # Установка стилей приложения
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #F5F5F5;
            font-family: 'Arial', 'Segoe UI';
            font-size: 12px;
        }
        
        QLabel {
            color: #333333;
        }
        
        QLineEdit, QSpinBox {
            padding: 8px;
            border: 2px solid #cccccc;
            border-radius: 4px;
            background-color: white;
        }
        
        QLineEdit:focus, QSpinBox:focus {
            border-color: #4CAF50;
        }
        
        QPushButton {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
    """)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()