import sys
import socket
import json
from queue import Queue, Empty

from PyQt5.QtCore import QThread, QTimer, QObject, pyqtSlot


from PyQt5.QtCore import QThread, QMetaObject, Qt, Q_ARG
from queue import Queue, Empty
import json
import socket

class ConnectionWorker(QThread):
    def __init__(self, host, port, client, parent=None):
        super().__init__(parent)
        self.host = host
        self.port = port
        self.client = client  # ссылка на объект Client, который находится в главном потоке
        self.request_queue = Queue()
        self.running = True
        self.sock = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(5)  # увеличили таймаут для отладки
            print(f"[Worker] Соединение установлено с {self.host}:{self.port}")
        except Exception as e:
            print("Ошибка подключения в ConnectionWorker:", e)
            self.running = False
            return

        while self.running:
            try:
                message, callback = self.request_queue.get(timeout=0.1)
                print("[Worker] Извлечен запрос:", message)
            except Empty:
                continue

            try:
                self.sock.send(json.dumps(message).encode())
                response = self.sock.recv(4096).decode()
                print("[Worker] Получен ответ:", response)
                data = json.loads(response)
            except Exception as e:
                data = {'error': str(e)}
            if callback:
                # Вызываем слот invoke_callback объекта client, который находится в главном потоке
                QMetaObject.invokeMethod(self.client, "invoke_callback", Qt.QueuedConnection,
                                         Q_ARG(dict, data), Q_ARG(object, callback))
        self.sock.close()

    def send_request(self, message, callback):
        self.request_queue.put((message, callback))

    def stop(self):
        self.running = False
        self.wait()

############################
# КЛАСС ПУЛА СОЕДИНЕНИЙ
############################

class ConnectionPool:
    def __init__(self, host, port, pool_size=3, client=None):
        self.workers = []
        self.index = 0
        for i in range(pool_size):
            worker = ConnectionWorker(host, port, client)
            worker.start()
            self.workers.append(worker)

    def send_request(self, message, callback):
        worker = self.workers[self.index]
        self.index = (self.index + 1) % len(self.workers)
        worker.send_request(message, callback)

    def stop(self):
        for worker in self.workers:
            worker.stop()

############################
# КЛАСС КЛИЕНТА
############################


class Client(QObject):
    def __init__(self, host='127.0.0.1', port=5000, pool_size=3):
        super().__init__()
        self.pool = ConnectionPool(host, port, pool_size, client=self)

    def send_request(self, message, callback):
        self.pool.send_request(message, callback)

    @pyqtSlot(dict, object)
    def invoke_callback(self, data, callback):
        # Этот слот вызывается в главном потоке, поэтому можно безопасно обновлять UI
        callback(data)

    def stop(self):
        self.pool.stop()

