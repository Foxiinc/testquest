from base_window import BaseWindow


class StartWindow(BaseWindow):
    def __init__(self):
        super().__init__()
        self.load_ui("ui/start.ui")

        self.ui.btn_register.clicked.connect(self.open_register)
        self.ui.btn_auth.clicked.connect(self.open_auth)

    def open_register(self):
        from register_window import RegisterWindow
        self.w = RegisterWindow()
        self.w.show()
        self.close()

    def open_auth(self):
        from auth_window import AuthWindow
        self.w = AuthWindow()
        self.w.show()
        self.close()
