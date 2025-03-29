import sys
import socket
import threading
import json

from PyQt5.QtWidgets import ( QApplication, QWidget, QVBoxLayout,
                             QPushButton, QTextEdit, QLineEdit,
                             QLabel, QTableWidget, QTableWidgetItem,
                             QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from components.MainWindow import MainAppWindow



class LoginWindow(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Аутентификация")
        self.resize(300, 150)
        layout = QVBoxLayout()

        self.username_label = QLabel("Username:")
        self.username_edit = QLineEdit()
        self.password_label = QLabel("Password:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Войти")
        self.register_button = QPushButton("Регистрация")
        self.result_label = QLabel("")

        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_registration)

        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        layout.addWidget(self.result_label)
        self.setLayout(layout)
    
    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        credentials = {'action': 'login', 'username': username, 'password': password}
        self.client.send_request(credentials, self.handle_login_response)

    def handle_login_response(self, data):
        print("Ответ на login:", data)
        if data.get('authenticated'):
            self.result_label.setText("Аутентификация успешна!")
            user_id = data.get('user_id')
            self.open_main_window(user_id)
        else:
            self.result_label.setText("Неверные учетные данные!")


    def handle_registration(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if not username or not password:
            self.result_label.setText("Введите имя и пароль")
            return
        message = {'action': 'register', 'username': username, 'password': password}
        self.client.send_request(message, self.handle_registration_response)

    def handle_registration_response(self, data):
        if data.get('registered'):
            self.result_label.setText("Регистрация успешна!")
            user_id = data.get('user_id')
            self.open_main_window(user_id)
        else:
            error = data.get('error', "Ошибка регистрации!")
            self.result_label.setText(error)

    def open_main_window(self, user_id):
        self.main_window = MainAppWindow(user_id, client=self.client)
        self.main_window.show()
        self.close()

