import cv2
import pandas as pd
from datetime import datetime
from base_window import BaseWindow
import os


DB_FILE = "operators_db.csv"
PHOTO_DIR = "photos"


class RegisterWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.load_ui("ui/register.ui")

        os.makedirs(PHOTO_DIR, exist_ok=True)

        self.ui.btn_save.clicked.connect(self.save_operator)

    def save_operator(self):
        lastname = self.ui.input_lastname.text()
        firstname = self.ui.input_firstname.text()
        middlename = self.ui.input_middlename.text()
        age = self.ui.input_age.text()

        if not all([lastname, firstname, middlename, age]):
            self.ui.label_terminal.setText("Заполните все поля!")
            return

        operator_id = self.save_to_csv(lastname, firstname, middlename, age)
        self.save_photo(operator_id)

        self.ui.label_terminal.setText(f"Оператор сохранён! ID = {operator_id}")

    def save_to_csv(self, last, first, middle, age):
        try:
            df = pd.read_csv(DB_FILE)
        except:
            df = pd.DataFrame()

        new_id = len(df) + 1

        data = {
            "id": new_id,
            "lastname": last,
            "firstname": first,
            "middlename": middle,
            "age": age,
            "date": datetime.now().strftime("%d-%m-%Y"),
            "time": datetime.now().strftime("%H:%M:%S"),
        }

        df = pd.concat([df, pd.DataFrame([data])])
        df.to_csv(DB_FILE, index=False)

        return new_id

    def save_photo(self, operator_id):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if ret:
            path = f"{PHOTO_DIR}/ID_{operator_id}.jpg"
            cv2.imwrite(path, frame)
