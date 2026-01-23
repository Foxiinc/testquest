import serial
import time
import sys

PORT = '/dev/ttyUSB0'   # Windows: 'COM3'
BAUDRATE = 115200

# Пороги подберёшь под себя
NORMAL_MAX = 40
WARNING_MAX = 80

def get_status(val: int) -> str:
    if val <= NORMAL_MAX:
        return "НОРМА"
    elif val <= WARNING_MAX:
        return "ВНИМАНИЕ"
    return "КРИТИЧНО"

def bar(val: int, width: int = 50) -> str:
    filled = int((val / 255) * width)
    return "█" * filled + "-" * (width - filled)

def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=1)
        print(f"Подключено к {PORT} @ {BAUDRATE}")
        time.sleep(2)  # ждём инициализации Arduino

        while True:
            line = ser.readline().decode(errors='ignore').strip()
            if line.isdigit():
                value = int(line)
                status = get_status(value)

                sys.stdout.write(
                    f"\rEMG: {value:3d} | {bar(value)} | {status}   "
                )
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nОстановлено пользователем.")
    except serial.SerialException as e:
        print(f"\nОшибка Serial: {e}")
    finally:
        try:
            ser.close()
        except:
            pass

if __name__ == "__main__":
    main()
