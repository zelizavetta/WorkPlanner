import bcrypt



def authenticate_user(conn, username, input_password):
    """
    Получает хэш пароля для пользователя из базы данных и сравнивает с введённым паролем.
    
    :param username: имя пользователя
    :param input_password: пароль, введённый пользователем
    :return: True, если аутентификация успешна, иначе False
    """
    try:
        cursor = conn.cursor()
        query = "SELECT password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        # cursor.close()
        # conn.close()
        
        if result is None:
            return False
        
        stored_hash = result[0]
        # Если хэш хранится как строка, преобразуем в bytes
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        # bcrypt.checkpw сравнивает байтовые строки
        return bcrypt.checkpw(input_password.encode('utf-8'), stored_hash)
    except Exception as e:
        print("Ошибка аутентификации:", e)
        return False
    
def register_user(conn, username, password):
    """
    Регистрирует нового пользователя:
    - хэширует пароль с помощью bcrypt
    - вставляет данные в таблицу users
    Возвращает id нового пользователя или None при ошибке.
    """
    try:
        cursor = conn.cursor()
        # Проверяем, существует ли пользователь с таким именем
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone() is not None:
            cursor.close()
            return None
        # Хэшируем пароль
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        # Вставляем нового пользователя
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
            (username, hashed_password)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        # cursor.close()
        # conn.close()
        return user_id
    except Exception as e:
        print("Ошибка регистрации:", e)
        return None


def get_password_by_username(cursor, conn, username):
    """
    Получает пароль пользователя по его имени из таблицы users.
    
    :param username: Имя пользователя (строка)
    :return: Пароль пользователя, если найден, иначе None
    """
    try:
        # Выполнение запроса для получения пароля по имени пользователя
        query = "SELECT password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        
        # cursor.close()
        # conn.close()
        
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при получении пароля: {e}")
        return None
    
def createUsersTable(cursor, conn):
    users_table_query = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        username VARCHAR(255) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL
    );
    """

    try:
        cursor.execute(users_table_query)
        conn.commit()
        print("Таблица tasks успешно создана или уже существует.")
    except Exception as e:
        print("Ошибка при создании таблицы:", e)

def get_tasks_for_user(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_name, status, progress FROM tasks WHERE user_id = %s", (user_id,))
    tasks = cursor.fetchall()
    return tasks

def get_username_by_id(conn, user_id):
    """
    Получает имя пользователя по его id из таблицы users.
    
    :param user_id: id пользователя
    :return: Имя пользователя, если найден, иначе None
    """
    cursor = conn.cursor()
    try:
        
        # Выполнение запроса для получения пароля по имени пользователя
        query = "SELECT username FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchone()
        
        # cursor.close()
        # conn.close()
        
        if result:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Ошибка при получении имени юзера: {e}")
        return None