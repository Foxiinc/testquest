import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
import sys

# --- НАСТРОЙКИ ---
SERIAL_PORT = '/dev/ttyUSB0' # Или 'COM3' на винде
BAUD_RATE = 115200
PLOT_WINDOW = 400 * 5        # Показывать последние 5 секунд (примерно 2000 точек)
# -----------------

# Инициализация Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Подключено к {SERIAL_PORT}. Ожидание данных...")
    # Очистим буфер, чтобы не рисовать старый мусор
    ser.reset_input_buffer()
except Exception as e:
    print(f"Ошибка подключения к порту: {e}")
    sys.exit(1)

# Буфер для хранения данных графика
# Забиваем серединным значением (512), чтобы график не прыгал на старте
data_buffer = deque([512]*PLOT_WINDOW, maxlen=PLOT_WINDOW)

# --- Настройка Matplotlib ---
fig, ax = plt.subplots()
ax.set_title('ЭКГ сигнал в реальном времени')
ax.set_xlabel('Семплы')
ax.set_ylabel('Значение АЦП (0-1023)')
ax.grid(True, which='both', linestyle='--', linewidth=0.5)

# Линия, которую будем обновлять
line, = ax.plot([], [], lw=1.5, color='blue')

# Начальные границы осей
ax.set_ylim(0, 1023)
ax.set_xlim(0, PLOT_WINDOW)

# Эта функция вызывается перед стартом анимации
def init():
    line.set_data([], [])
    return line,

# Эта функция вызывается в цикле для обновления кадра
def update(frame):
    # Читаем ВСЕ данные, которые накопились в буфере Serial,
    # чтобы график не отставал от реальности.
    while ser.in_waiting > 0:
        try:
            line_raw = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line_raw: continue
            
            # Парсим строку вида "123,456,789,"
            vals = [int(x) for x in line_raw.split(',') if x.isdigit()]
            data_buffer.extend(vals)
            
        except ValueError:
            pass # Игнорируем битые пакеты
        except Exception as e:
            print(f"Ошибка чтения: {e}")
            break

    # Преобразуем дек в numpy массив для быстрого рисования
    Y = np.array(data_buffer)
    X = np.arange(len(Y))
    
    # Обновляем данные линии
    line.set_data(X, Y)
    
    # Динамическое масштабирование оси Y, чтобы сигнал всегда был виден
    # Берем мин/макс за последние данные и добавляем отступы
    if len(Y) > 100:
        ymin = np.min(Y[-PLOT_WINDOW:]) - 50
        ymax = np.max(Y[-PLOT_WINDOW:]) + 50
        # Не даем уйти за пределы АЦП
        ax.set_ylim(max(0, ymin), min(1023, ymax))

    return line,

# Запуск анимации
# interval=30 означает попытку обновления каждые 30мс (~33 FPS)
# blit=True ускоряет перерисовку
ani = animation.FuncAnimation(fig, update, init_func=init, frames=None,
                              interval=30, blit=True, cache_frame_data=False)

print("График запущен. Закрой окно графика для выхода.")
plt.show()

# Закрываем порт при выходе
ser.close()
print("Порт закрыт.")