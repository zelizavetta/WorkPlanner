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

from server.server import start_server 
from client.clientClass import Client
from components.LoginWindow import LoginWindow

############################
# GUI: LoginWindow
############################


if __name__ == '__main__':
    # Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    app = QApplication(sys.argv)
    client = Client()  # Клиент использует пул соединений
    loginWindow = LoginWindow(client=client)
    loginWindow.show()
    sys.exit(app.exec_())
