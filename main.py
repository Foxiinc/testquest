import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, 
    QHBoxLayout, QGridLayout, QPushButton, QLabel, QLineEdit, QTextEdit
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from datetime import datetime


class StartWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Система контроля операторов")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        
        reg_btn = QPushButton("Регистрация")
        reg_btn.setMinimumHeight(50)
        reg_btn.clicked.connect(lambda: self.main_window.show_form(1))
        
        auth_btn = QPushButton("Авторизация")
        auth_btn.setMinimumHeight(50)
        auth_btn.clicked.connect(lambda: self.main_window.show_form(2))
        
        layout.addWidget(title)
        layout.addWidget(reg_btn)
        layout.addWidget(auth_btn)
        self.setLayout(layout)


class RegistrationForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Левая часть - поля ввода
        left_layout = QVBoxLayout()
        
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Фамилия")
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Имя")
        
        self.patronymic_input = QLineEdit()
        self.patronymic_input.setPlaceholderText("Отчество")
        
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Возраст")
        
        record_btn = QPushButton("Записать")
        record_btn.clicked.connect(self.record_data)
        
        self.next_btn = QPushButton("Далее")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(lambda: self.main_window.show_form(3))
        
        left_layout.addWidget(QLabel("Регистрация оператора"))
        left_layout.addWidget(self.surname_input)
        left_layout.addWidget(self.name_input)
        left_layout.addWidget(self.patronymic_input)
        left_layout.addWidget(self.age_input)
        left_layout.addWidget(record_btn)
        left_layout.addWidget(self.next_btn)
        
        # Правая часть - заглушка камеры
        camera_label = QLabel("ЗДЕСЬ БУДЕТ КАМЕРА")
        camera_label.setAlignment(Qt.AlignCenter)
        camera_label.setStyleSheet("border: 2px solid gray; background-color: lightgray; min-height: 200px;")
        
        # Информационный блок
        info_layout = QVBoxLayout()
        self.info_label = QLabel("Заполните все поля для регистрации")
        self.info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.info_label)
        
        main_layout.addLayout(left_layout)
        main_layout.addWidget(camera_label)
        
        full_layout = QVBoxLayout()
        full_layout.addLayout(main_layout)
        full_layout.addLayout(info_layout)
        
        self.setLayout(full_layout)
    
    def record_data(self):
        print(f"Записаны данные: {self.surname_input.text()} {self.name_input.text()}")
        self.info_label.setText("Данные записаны успешно")
        self.next_btn.setEnabled(True)


class AuthForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Авторизация")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID оператора")
        
        auth_btn = QPushButton("Авторизация")
        auth_btn.clicked.connect(self.authorize)
        
        layout.addWidget(title)
        layout.addWidget(self.id_input)
        layout.addWidget(auth_btn)
        self.setLayout(layout)
    
    def authorize(self):
        print(f"Авторизация ID: {self.id_input.text()}")
        self.main_window.show_form(3)


class InfoForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Левая часть - информация
        left_layout = QVBoxLayout()
        
        info_data = [
            "ФИО: Иванов Иван Иванович",
            "Возраст: 30",
            f"Дата/время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            "Время запуска ПО: 08:00:00",
            "Время в дороге: 01:30:00",
            "Оставшееся время: 09:00:00"
        ]
        
        for info in info_data:
            label = QLabel(info)
            left_layout.addWidget(label)
        
        # Правая часть - заглушка камеры
        camera_label = QLabel("ЗДЕСЬ БУДЕТ КАМЕРА")
        camera_label.setAlignment(Qt.AlignCenter)
        camera_label.setStyleSheet("border: 2px solid gray; background-color: lightgray; min-height: 200px;")
        
        main_layout.addLayout(left_layout)
        main_layout.addWidget(camera_label)
        
        # Статус блок
        status_layout = QVBoxLayout()
        status_label = QLabel("Оператор определен")
        status_label.setStyleSheet("color: green; font-weight: bold;")
        status_label.setAlignment(Qt.AlignCenter)
        
        next_btn = QPushButton("Далее")
        next_btn.clicked.connect(lambda: self.main_window.show_form(4))
        
        status_layout.addWidget(status_label)
        status_layout.addWidget(next_btn)
        
        full_layout = QVBoxLayout()
        full_layout.addLayout(main_layout)
        full_layout.addLayout(status_layout)
        
        self.setLayout(full_layout)


class InstructionForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        main_layout = QHBoxLayout()
        
        # Левое меню
        menu_layout = QVBoxLayout()
        
        instruction_btn = QPushButton("Инструкция")
        instruction_btn.clicked.connect(lambda: self.show_content("instruction"))
        
        analysis_btn = QPushButton("Анализ")
        analysis_btn.clicked.connect(lambda: self.main_window.show_form(5))
        
        control_btn = QPushButton("Управление")
        control_btn.clicked.connect(lambda: self.main_window.show_form(6))
        
        menu_layout.addWidget(instruction_btn)
        menu_layout.addWidget(analysis_btn)
        menu_layout.addWidget(control_btn)
        menu_layout.addStretch()
        
        # Центральный блок
        self.content_label = QLabel()
        self.content_label.setAlignment(Qt.AlignTop)
        self.content_label.setWordWrap(True)
        self.show_content("instruction")
        
        # Кнопка далее
        next_btn = QPushButton("Далее")
        next_btn.clicked.connect(lambda: self.main_window.show_form(5))
        
        main_layout.addLayout(menu_layout)
        main_layout.addWidget(self.content_label)
        
        full_layout = QVBoxLayout()
        full_layout.addLayout(main_layout)
        full_layout.addWidget(next_btn)
        
        self.setLayout(full_layout)
    
    def show_content(self, content_type):
        if content_type == "instruction":
            text = """
            Описание состояний оператора:
            
            🟢 НОРМА - нормальное состояние оператора
            Пульс в пределах нормы, оператор готов к работе
            
            🟡 ВНИМАНИЕ - требуется внимание
            Показатели близки к критическим значениям
            
            🔴 КРИТИЧНО - критическое состояние
            Немедленно прекратить работу, обратиться к врачу
            """
            self.content_label.setText(text)
            self.content_label.setStyleSheet("")


class AnalysisForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Поля ввода
        input_layout = QGridLayout()
        
        input_layout.addWidget(QLabel("Порог пульса:"), 0, 0)
        self.pulse_threshold = QLineEdit("120")
        input_layout.addWidget(self.pulse_threshold, 0, 1)
        
        input_layout.addWidget(QLabel("Норма пульса:"), 1, 0)
        self.pulse_norm = QLineEdit("70")
        input_layout.addWidget(self.pulse_norm, 1, 1)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        record_btn = QPushButton("Записать")
        record_btn.clicked.connect(self.record_settings)
        
        next_btn = QPushButton("Далее")
        next_btn.clicked.connect(lambda: self.main_window.show_form(6))
        
        btn_layout.addWidget(record_btn)
        btn_layout.addWidget(next_btn)
        
        # Терминальный блок
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setText("Система анализа готова к работе\nОжидание данных...")
        self.terminal.setMaximumHeight(150)
        
        layout.addLayout(input_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(QLabel("Терминал:"))
        layout.addWidget(self.terminal)
        
        self.setLayout(layout)
    
    def record_settings(self):
        print(f"Настройки: порог={self.pulse_threshold.text()}, норма={self.pulse_norm.text()}")
        self.terminal.append(f"Настройки сохранены: порог={self.pulse_threshold.text()}, норма={self.pulse_norm.text()}")


class ControlForm(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        self.setup_timer()
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Верхняя информация
        info_layout = QHBoxLayout()
        
        operator_info = QVBoxLayout()
        operator_info.addWidget(QLabel("ФИО: Иванов Иван Иванович"))
        operator_info.addWidget(QLabel(f"Дата/время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"))
        
        status_info = QVBoxLayout()
        self.status_label = QLabel("НОРМА")
        self.status_label.setStyleSheet("background-color: green; color: white; padding: 10px; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.pulse_label = QLabel("72")
        self.pulse_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.pulse_label.setAlignment(Qt.AlignCenter)
        
        self.timer_label = QLabel("09:00:00")
        self.timer_label.setFont(QFont("Arial", 16))
        self.timer_label.setAlignment(Qt.AlignCenter)
        
        status_info.addWidget(QLabel("Состояние оператора:"))
        status_info.addWidget(self.status_label)
        status_info.addWidget(QLabel("Пульс:"))
        status_info.addWidget(self.pulse_label)
        status_info.addWidget(QLabel("Оставшееся время:"))
        status_info.addWidget(self.timer_label)
        
        info_layout.addLayout(operator_info)
        info_layout.addLayout(status_info)
        
        # Видео блоки
        video_layout = QHBoxLayout()
        
        video1 = QLabel("ЗДЕСЬ БУДЕТ КАМЕРА\n(Основная)")
        video1.setAlignment(Qt.AlignCenter)
        video1.setStyleSheet("border: 2px solid gray; background-color: lightgray; min-height: 200px;")
        
        video2 = QLabel("ЗДЕСЬ БУДЕТ КАМЕРА\n(Оператор)")
        video2.setAlignment(Qt.AlignCenter)
        video2.setStyleSheet("border: 2px solid gray; background-color: lightgray; min-height: 200px;")
        
        video_layout.addWidget(video1)
        video_layout.addWidget(video2)
        
        # Терминал
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setText("Система мониторинга активна\nОтслеживание состояния оператора...")
        self.terminal.setMaximumHeight(100)
        
        main_layout.addLayout(info_layout)
        main_layout.addLayout(video_layout)
        main_layout.addWidget(QLabel("Терминал:"))
        main_layout.addWidget(self.terminal)
        
        self.setLayout(main_layout)
    
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(2000)  # Обновление каждые 2 секунды
    
    def update_display(self):
        # Имитация изменения пульса
        import random
        pulse = random.randint(65, 85)
        self.pulse_label.setText(str(pulse))
        
        # Имитация изменения статуса
        if pulse > 80:
            self.status_label.setText("ВНИМАНИЕ")
            self.status_label.setStyleSheet("background-color: yellow; color: black; padding: 10px; font-weight: bold;")
        elif pulse > 90:
            self.status_label.setText("КРИТИЧНО")
            self.status_label.setStyleSheet("background-color: red; color: white; padding: 10px; font-weight: bold;")
        else:
            self.status_label.setText("НОРМА")
            self.status_label.setStyleSheet("background-color: green; color: white; padding: 10px; font-weight: bold;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система контроля операторов")
        self.setGeometry(100, 100, 800, 600)
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Создание всех форм
        self.forms = [
            StartWindow(self),           # 0
            RegistrationForm(self),      # 1
            AuthForm(self),              # 2
            InfoForm(self),              # 3
            InstructionForm(self),       # 4
            AnalysisForm(self),          # 5
            ControlForm(self)            # 6
        ]
        
        for form in self.forms:
            self.stacked_widget.addWidget(form)
        
        self.show_form(0)
    
    def show_form(self, index):
        self.stacked_widget.setCurrentIndex(index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

