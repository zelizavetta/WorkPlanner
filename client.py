import sys
import socket
import threading
import json

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel, QTableWidget, QTableWidgetItem, QComboBox, QToolButton
from PyQt5.QtCore import Qt

from server.tasksFuncs import createTask, createSubtask


class MainAppWindow(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.username = ""
        self.server_host = '127.0.0.1'  # измените при необходимости
        self.server_port = 5000
        self.updating_table = False  # флаг для блокировки обработки сигналов при обновлении
        self.initUI()
        self.load_tasks()
    
    def initUI(self):
        self.setWindowTitle("Основное окно - Список задач")
        self.resize(700, 400)
        layout = QVBoxLayout()
        
        self.get_username_by_id()
        self.info_label = QLabel(f"Список задач для пользователя {self.username}")
        layout.addWidget(self.info_label)
        
        # Таблица с 4 колонками: 0 - Task ID (скрытая), 1 - Name, 2 - Status, 3 - кнопка для подзадач
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Task ID", "Name", "Status", ""])
        self.table.hideColumn(0)
        # Для редактирования родительских задач можно подключить cellChanged
        self.table.cellChanged.connect(self.onCellChanged)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def get_username_by_id(self):
        message = {'action': 'get_username', 'user_id': self.user_id}
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_host, self.server_port))
            s.send(json.dumps(message).encode())
            response = s.recv(1024).decode()
            data = json.loads(response)
            self.username = data.get('username', '')
        except Exception as e:
            print("Ошибка загрузки имени юзера:", e)
        finally:
            s.close()
    
    def load_tasks(self):
        self.updating_table = True
        message = {'action': 'get_tasks', 'user_id': self.user_id}
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_host, self.server_port))
            s.send(json.dumps(message).encode())
            response = s.recv(4096).decode()
            data = json.loads(response)
            tasks = data.get('tasks', [])
            self.populate_table(tasks)
        except Exception as e:
            print("Ошибка загрузки задач:", e)
        finally:
            s.close()
            self.updating_table = False
    
    def populate_table(self, tasks):
        # Фильтруем родительские задачи (parent_task_id is None)
        parent_tasks = [task for task in tasks if task.get('parent_task_id') is None]
        # Количество строк = количество родительских задач + 1 (для новой задачи)
        row_count = len(parent_tasks) + 1
        self.table.setRowCount(row_count)
        
        # Заполняем строки с родительскими задачами
        for row, task in enumerate(parent_tasks):
            # Колонка 0: Task ID (скрытая)
            id_item = QTableWidgetItem(str(task.get('id')))
            self.table.setItem(row, 0, id_item)
            
            # Колонка 1: Название задачи (редактируемая)
            name_item = QTableWidgetItem(task.get('Name', ''))
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)
            
            # Колонка 2: Статус задачи (редактируемый текст)
            status_item = QTableWidgetItem(task.get('Status', 'to do'))
            status_item.setFlags(status_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 2, status_item)
            
            # Колонка 3: Кнопка-стрелка для открытия/сворачивания подзадач
            arrow_btn = QToolButton()
            arrow_btn.setText("▼")
            arrow_btn.clicked.connect(lambda _, r=row, pid=task.get('id'): self.toggleSubtaskRows(r, pid))
            self.table.setCellWidget(row, 3, arrow_btn)
        
        # Последняя строка – для ввода новой родительской задачи.
        new_row = row_count - 1
        self.table.setItem(new_row, 0, QTableWidgetItem(""))  # скрытая колонка пустая
        # Вместо QTableWidgetItem используем QLineEdit для ввода названия
        new_task_edit = QLineEdit()
        new_task_edit.setPlaceholderText("Введите новое задание...")
        self.table.setCellWidget(new_row, 1, new_task_edit)
        # QComboBox для выбора статуса нового задания
        new_status_combo = QComboBox()
        new_status_combo.addItems(["to do", "in progress", "done"])
        new_status_combo.setCurrentIndex(0)
        self.table.setCellWidget(new_row, 2, new_status_combo)
        # Колонка 3 оставляем пустой
        
        # Подключаем сигнал editingFinished для QLineEdit новой задачи
        new_task_edit.editingFinished.connect(lambda: self.onNewTaskEditingFinished(new_row))
    
    def onNewTaskEditingFinished(self, row):
        # Получаем QLineEdit из колонки 1
        widget = self.table.cellWidget(row, 1)
        if widget is None:
            return
        new_text = widget.text().strip()
        if not new_text:
            return
        # Получаем выбранный статус из QComboBox в колонке 2
        status_combo = self.table.cellWidget(row, 2)
        new_status = status_combo.currentText() if status_combo else "to do"
        self.add_task(new_text, new_status)
    
    def add_task(self, task_name, status):
        message = {
            'action': 'add_task',
            'user_id': self.user_id,
            'task_name': task_name,
            'status': status
        }
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_host, self.server_port))
            s.send(json.dumps(message).encode())
            response = s.recv(1024).decode()
            data = json.loads(response)
            if data.get('added'):
                print("Задание добавлено, task_id:", data.get('task_id'))
                self.load_tasks()  # Обновляем таблицу после добавления
            else:
                print("Ошибка при добавлении задания:", data.get('error'))
        except Exception as e:
            print("Ошибка при добавлении задания:", e)
        finally:
            s.close()
    
    # Остальные функции для подзадач (toggleSubtaskRows, insertEmptySubtaskRow, onSubtaskEditingFinished, add_subtask, etc.)
    def toggleSubtaskRows(self, parent_row, parent_task_id):
        child_rows = []
        i = parent_row + 1
        while i < self.table.rowCount():
            marker_item = self.table.item(i, 0)
            if marker_item and marker_item.data(Qt.UserRole) == "subtask" and marker_item.data(Qt.UserRole + 1) == parent_task_id:
                child_rows.append(i)
            else:
                break
            i += 1
        
        if child_rows:
            current_visibility = self.table.isRowHidden(child_rows[0])
            for r in child_rows:
                self.table.setRowHidden(r, not current_visibility)
        else:
            self.insertEmptySubtaskRow(parent_row, parent_task_id)
    
    def insertEmptySubtaskRow(self, parent_row, parent_task_id):
        insert_row = parent_row + 1
        self.table.insertRow(insert_row)
        marker = QTableWidgetItem("")
        marker.setData(Qt.UserRole, "subtask")
        marker.setData(Qt.UserRole + 1, parent_task_id)
        self.table.setItem(insert_row, 0, marker)
        
        subtask_edit = QLineEdit()
        subtask_edit.setPlaceholderText("Введите подзадачу...")
        subtask_edit.setStyleSheet("padding-left: 20px;")
        self.table.setCellWidget(insert_row, 1, subtask_edit)
        subtask_edit.setFocus()
        subtask_edit.editingFinished.connect(lambda: self.onSubtaskEditingFinished(insert_row))
        
        status_combo = QComboBox()
        status_combo.addItems(["to do", "in progress", "done"])
        status_combo.setCurrentIndex(0)
        self.table.setCellWidget(insert_row, 2, status_combo)
    
    def onSubtaskEditingFinished(self, row):
        line_edit = self.table.cellWidget(row, 1)
        if not line_edit:
            return
        task_text = line_edit.text().strip()
        if not task_text:
            return
        status_combo = self.table.cellWidget(row, 2)
        task_status = status_combo.currentText() if status_combo else "to do"
        marker_item = self.table.item(row, 0)
        parent_task_id = marker_item.data(Qt.UserRole + 1) if marker_item else None
        if parent_task_id is None:
            print("Ошибка: parent_task_id не найден")
            return
        self.add_subtask(parent_task_id, task_text, task_status)
        new_item = QTableWidgetItem(task_text)
        new_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.removeCellWidget(row, 1)
        self.table.setItem(row, 1, new_item)
        self.ensureEmptySubtaskRow(parent_task_id, row)
    
    def ensureEmptySubtaskRow(self, parent_task_id, current_row):
        last_child_row = current_row
        i = current_row + 1
        while i < self.table.rowCount():
            marker_item = self.table.item(i, 0)
            if marker_item and marker_item.data(Qt.UserRole) == "subtask" and marker_item.data(Qt.UserRole + 1) == parent_task_id:
                last_child_row = i
                i += 1
            else:
                break
        widget = self.table.cellWidget(last_child_row, 1)
        if widget is None:
            self.insertEmptySubtaskRow(last_child_row, parent_task_id)
    
    def add_subtask(self, parent_id, task_name, status):
        message = {
            'action': 'add_subtask',
            'user_id': self.user_id,
            'parent_id': parent_id,
            'task_name': task_name,
            'status': status
        }
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.server_host, self.server_port))
            s.send(json.dumps(message).encode())
            response = s.recv(1024).decode()
            data = json.loads(response)
            if data.get('added'):
                print("Подзадача добавлена, task_id:", data.get('task_id'))
            else:
                print("Ошибка при добавлении подзадачи:", data.get('error'))
        except Exception as e:
            print("Ошибка при добавлении подзадачи:", e)
        finally:
            s.close()
    
    def onCellChanged(self, row, column):
        # Обновление родительских заданий можно реализовать здесь, если нужно.
        pass
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.server_host = '127.0.0.1'  # адрес сервера (замените, если необходимо)
        self.server_port = 5000
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
        self.register_button = QPushButton("Регистрация")  # кнопка для переключения в окно регистрации
        self.result_label = QLabel("")
        
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)
        layout.addWidget(self.result_label)
        self.setLayout(layout)
        
        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_registration)
        
    def handle_login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        credentials = {'action': 'login', 'username': username, 'password': password}
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            client_socket.send(json.dumps(credentials).encode())
            
            response = client_socket.recv(1024).decode()
            data = json.loads(response)
            if data.get('authenticated'):
                self.result_label.setText("Аутентификация успешна!")
                # Получаем user_id и открываем основное окно
                user_id = data.get('user_id')
                self.open_main_window(user_id)
            else:
                self.result_label.setText("Неверные учетные данные!")
        except Exception as e:
            self.result_label.setText(f"Ошибка: {e}")
        finally:
            client_socket.close()
        
    def handle_registration(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        if not username or not password:
            self.result_label.setText("Введите имя и пароль")
            return
        
        message = {
            'action': 'register',
            'username': username,
            'password': password
        }
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.server_host, self.server_port))
            client_socket.send(json.dumps(message).encode())
            
            response = client_socket.recv(1024).decode()
            data = json.loads(response)
            if data.get('registered'):
                self.result_label.setText("Регистрация успешна!")
                # Передаём user_id из ответа сервера
                user_id = data.get('user_id')
                self.open_main_window(user_id)
            else:
                error = data.get('error', "Ошибка регистрации!")
                self.result_label.setText(error)
        except Exception as e:
            self.result_label.setText(f"Ошибка: {e}")
        finally:
            client_socket.close()

    def open_main_window(self, user_id):
        self.main_window = MainAppWindow(user_id)
        self.main_window.show()
        self.close()

class Client(QWidget):
    def __init__(self):
        super().__init__()
        self.client_socket = None
        self.host = '127.0.0.1'  # IP-адрес сервера; замените на реальный, если сервер удалённый
        self.port = 5000
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Socket Client (PyQt)")
        self.resize(400, 300)
        layout = QVBoxLayout()

        # Текстовое поле для отображения сообщений
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        layout.addWidget(self.text_display)

        # Поле ввода для отправки сообщений
        self.input_line = QLineEdit()
        layout.addWidget(self.input_line)

        # Кнопка отправки
        self.send_button = QPushButton("Отправить")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        self.setLayout(layout)
        self.connect_to_server()

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.text_display.append("Подключено к серверу.")
            # Запускаем отдельный поток для получения сообщений
            thread = threading.Thread(target=self.receive_messages)
            thread.daemon = True
            thread.start()
        except Exception as e:
            self.text_display.append(f"Ошибка подключения: {e}")

    def send_message(self):
        message = self.input_line.text().strip()
        if message and self.client_socket:
            try:
                self.client_socket.send(message.encode())
                self.input_line.clear()
            except Exception as e:
                self.text_display.append(f"Ошибка отправки: {e}")

    def receive_messages(self):
        while True:
            try:
                data = self.client_socket.recv(1024).decode()
                if data:
                    self.text_display.append(f"[Сервер]: {data}")
                else:
                    self.text_display.append("Соединение с сервером разорвано.")
                    break
            except Exception as e:
                self.text_display.append(f"Ошибка получения данных: {e}")
                break
        self.client_socket.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    client = LoginWindow()
    client.show()
    sys.exit(app.exec_())
