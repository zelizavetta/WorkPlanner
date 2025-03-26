import psycopg2
from server.tasksFuncs import createTaskTable, createTask, createSubtask
from server.usersFuncs import createUsersTable, authenticate_user, register_user, get_tasks_for_user, get_username_by_id
import threading
import json
import socket

def handle_client(client_socket, address):
    db_host = 'ep-plain-term-a51varre-pooler.us-east-2.aws.neon.tech'
    db_name = 'test'
    db_user = 'neondb_owner'
    db_password = 'npg_kh5Oj1EVJlqe'
    db_port = 5432  # Измените, если необходимо

    # Устанавливаем подключение к БД для каждого клиента
    conn = psycopg2.connect(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )

    # createTaskTable(conn)
    # createTask(conn, 11)

    
    print(f"[SERVER] Подключился клиент: {address}")
    try:
        data = client_socket.recv(1024).decode()
        if not data:
            return
        # Клиент должен отправить JSON с полем action
        message = json.loads(data)
        action = message.get('action')
        response = {}
        
        if action == "login":
            username = message.get('username')
            password = message.get('password')
            auth_success = authenticate_user(conn, username, password)
            if auth_success:
                # Если аутентификация успешна, получаем user_id из базы
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                if result is not None:
                    user_id = result[0]
                    response = {'authenticated': True, 'user_id': user_id}
                else:
                    response = {'authenticated': False}
            else:
                response = {'authenticated': False}
        elif action == "register":
            username = message.get('username')
            password = message.get('password')
            user_id = register_user(conn, username, password)
            if user_id is not None:
                response = {'registered': True, 'user_id': user_id}
            else:
                response = {'registered': False, 'error': 'Пользователь с таким именем уже существует'}
        elif action == "get_tasks":
            user_id = message.get('user_id')
            tasks = get_tasks_for_user(conn, user_id)
            tasks_list = [{"id": t[0], "Name": t[1], "Status": t[2], "Progress": t[3]} for t in tasks]
            response = {'tasks': tasks_list}
        elif action == "add_subtask":
            user_id = message.get('user_id')
            parent_id = message.get('parent_id')
            task_name = message.get('task_name')
            status = message.get('status', 'to do')
            try:
                cursor = conn.cursor()
                query = """
                    INSERT INTO tasks (task_name, status, user_id, parent_task_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """
                cursor.execute(query, (task_name, status, user_id, parent_id))
                new_task_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                response = {"added": True, "task_id": new_task_id}
            except Exception as e:
                response = {"added": False, "error": str(e)}

        elif action == "get_username":
            user_id = message.get('user_id')
            username = get_username_by_id(conn, user_id)
            print(username)
            response = {'username': username}
        elif action == "add_task":
            user_id = message.get('user_id')
            task_name = message.get('task_name')
            try:
                cursor = conn.cursor()
                # Предполагаем, что таблица tasks имеет колонки: id, task_name, user_id, parent_task_id (может быть NULL)
                cursor.execute(
                    "INSERT INTO tasks (task_name, user_id) VALUES (%s, %s) RETURNING id",
                    (task_name, user_id)
                )
                new_task_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                response = {'added': True, 'task_id': new_task_id}
            except Exception as e:
                response = {'added': False, 'error': str(e)}
        elif action == "update":
            task_id = message.get('task_id')
            task_name = message.get('task_name')
            status = message.get('status')
            try:
                cursor = conn.cursor()
                # Обновляем название и статус задачи с заданным id
                query = "UPDATE tasks SET task_name = %s, status = %s WHERE id = %s"
                cursor.execute(query, (task_name, status, int(task_id)))
                conn.commit()
                cursor.close()
                response = {"uploaded": True, "task_id": int(task_id)}
            except Exception as e:
                response = {"uploaded": False, "error": str(e)}
        else:
            response = {'error': 'Неизвестное действие'}
        
        # Отправляем ответ и обрабатываем ошибку, если соединение уже закрыто
        try:
            client_socket.send(json.dumps(response).encode())
        except Exception as send_error:
            print(f"[SERVER] Ошибка при отправке ответа клиенту {address}: {send_error}")
            
    except Exception as e:
        print(f"[SERVER] Ошибка при работе с клиентом {address}: {e}")
    # finally:
    #     client_socket.close()
    #     conn.close()


def start_server():
    host = '0.0.0.0'
    port = 5000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"[SERVER] Сервер запущен на порту {port}")
    
    while True:
        client_sock, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        client_thread.start()

if __name__ == '__main__':
    start_server()
