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



class MainAppWindow(QWidget):
    def __init__(self, user_id, client):
        super().__init__()
        self.client = client
        self.tasks = []
        self.selected_task_id = -1
        self.user_id = user_id
        self.username = ""
        self.updating_table = False  # флаг блокировки обновления
        self.initUI()
        self.load_tasks()

    def initUI(self):
        self.setWindowTitle("Основное окно - Список задач")
        self.resize(1600, 900)
        layout = QVBoxLayout()

        self.info_label = QLabel("Загрузка пользователя...")
        layout.addWidget(self.info_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Task ID", "Name", "Status", ""])
        self.table.hideColumn(0)
        self.table.cellChanged.connect(self.onCellChanged)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.get_username_by_id()

    def get_username_by_id(self):
        message = {'action': 'get_username', 'user_id': self.user_id}
        self.client.send_request(message, self.handle_username_response)

    def handle_username_response(self, data):
        self.username = data.get('username', '')
        self.info_label.setText(f"Список задач для пользователя {self.username}")

    def load_tasks(self):
        self.updating_table = True
        message = {'action': 'get_tasks', 'user_id': self.user_id}
        self.client.send_request(message, self.handle_tasks_response)

    def handle_tasks_response(self, data):
        self.tasks = data.get('tasks', [])
        self.populate_table(self.tasks)
        self.updating_table = False

    def populate_table(self, tasks):
        # Фильтруем родительские задачи (без parent_task_id)
        parent_tasks = [task for task in tasks if task.get('parent_task_id') is None]
        row_count = len(parent_tasks) + 1  # +1 для ввода новой задачи
        self.table.setRowCount(row_count)

        for row, task in enumerate(parent_tasks):
            id_item = QTableWidgetItem(str(task.get('id')))
            self.table.setItem(row, 0, id_item)

            name_item = QTableWidgetItem(task.get('Name', ''))
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 1, name_item)

            status_item = QTableWidgetItem(task.get('Status', 'to do'))
            status_item.setFlags(status_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 2, status_item)

            button = QPushButton()
            button.setIcon(QIcon("C:/Users/Elisa/WorkPlanner/images/trash.png"))
            button.clicked.connect(lambda checked, r=row: self.delete_task(r))
            self.table.setCellWidget(row, 3, button)

        # Последняя строка – для ввода новой задачи
        new_row = row_count - 1
        self.table.setItem(new_row, 0, QTableWidgetItem(""))
        new_task_edit = QLineEdit()
        new_task_edit.setPlaceholderText("Введите новое задание...")
        self.table.setCellWidget(new_row, 1, new_task_edit)
        new_status_combo = QComboBox()
        new_status_combo.addItems(["to do", "in progress", "done"])
        new_status_combo.setCurrentIndex(0)
        self.table.setCellWidget(new_row, 2, new_status_combo)
        self.table.setItem(new_row, 3, QTableWidgetItem(""))
        new_task_edit.editingFinished.connect(self.onNewTaskEditingFinished)

    def onNewTaskEditingFinished(self):
        sender = self.sender()
        if sender is None:
            return
        input_row = None
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 1)
            if widget is sender:
                input_row = row
                break
        if input_row is None:
            return
        new_text = sender.text().strip()
        if not new_text:
            return
        status_combo = self.table.cellWidget(input_row, 2)
        new_status = status_combo.currentText() if status_combo else "to do"
        self.add_task(new_text, new_status)

    def add_task(self, task_name, status):
        message = {
            'action': 'add_task',
            'user_id': self.user_id,
            'task_name': task_name,
            'status': status
        }
        self.client.send_request(message, lambda data: self.handle_add_task_response(data, task_name, status))

    def handle_add_task_response(self, data, task_name, status):
        if data.get('added'):
            new_task_id = data.get('task_id')
            print("Задание добавлено, task_id:", new_task_id)
            self.tasks.append({"id": int(new_task_id), "Name": task_name, "Status": status, "Progress": 0})
            # Удаляем строку ввода
            last_row = self.table.rowCount() - 1
            self.table.removeRow(last_row)
            # Добавляем строку с новой задачей
            new_row = self.table.rowCount()
            self.table.insertRow(new_row)
            id_item = QTableWidgetItem(str(new_task_id))
            self.table.setItem(new_row, 0, id_item)
            name_item = QTableWidgetItem(task_name)
            name_item.setFlags(name_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(new_row, 1, name_item)
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(new_row, 2, status_item)
            button = QPushButton()
            button.setIcon(QIcon("C:/Users/Elisa/WorkPlanner/images/trash.png"))
            button.clicked.connect(lambda checked, r=new_row: self.delete_task(r))
            self.table.setCellWidget(new_row, 3, button)
            self.add_input_row()
        else:
            print("Ошибка при добавлении задания:", data.get("error"))

    def add_input_row(self):
        new_row = self.table.rowCount()
        self.table.insertRow(new_row)
        self.table.setItem(new_row, 0, QTableWidgetItem(""))
        new_task_edit = QLineEdit()
        new_task_edit.setPlaceholderText("Введите новое задание...")
        self.table.setCellWidget(new_row, 1, new_task_edit)
        new_status_combo = QComboBox()
        new_status_combo.addItems(["to do", "in progress", "done"])
        new_status_combo.setCurrentIndex(0)
        self.table.setCellWidget(new_row, 2, new_status_combo)
        self.table.setItem(new_row, 3, QTableWidgetItem(""))
        new_task_edit.editingFinished.connect(self.onNewTaskEditingFinished)

    def delete_task(self, row):
        task_id = int(self.table.item(row, 0).text())
        message = {"action": "delete_task", "task_id": task_id}
        self.client.send_request(message, lambda data: self.handle_delete_task_response(data, row))

    def handle_delete_task_response(self, data, row):
        if data.get("deleted_task"):
            print("Задача удалена")
            self.table.removeRow(row)
            if not isinstance(self.table.cellWidget(self.table.rowCount()-1, 1), QLineEdit):
                self.add_input_row()
        else:
            print("Ошибка при удалении задачи:", data.get("error"))

    def onCellChanged(self, row, column):
        # Здесь можно добавить логику обновления задачи, если требуется
        pass

