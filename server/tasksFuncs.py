def createTaskTable(conn):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS tasks (
        id SERIAL PRIMARY KEY,
        task_name VARCHAR(255) NOT NULL,
        user_id INTEGER NOT NULL,
        parent_task_id INTEGER,
        CONSTRAINT fk_user
            FOREIGN KEY (user_id)
            REFERENCES users(id),
        CONSTRAINT fk_parent
            FOREIGN KEY (parent_task_id)
            REFERENCES tasks(id)
    );
    """
    cursor = conn.cursor()

    try:
        cursor.execute(create_table_query)
        conn.commit()
        print("Таблица tasks успешно создана или уже существует.")
    except Exception as e:
        print("Ошибка при создании таблицы:", e)

def createTask(conn, user_id):
    try:
        # 1. Создание родительского задания
        insert_parent_query = """
        INSERT INTO tasks (task_name, user_id)
        VALUES (%s, %s)
        RETURNING id;
        """
        parent_data = ("Родительское задание", user_id)  # Здесь 1 — пример id пользователя
        cursor = conn.cursor()
        cursor.execute(insert_parent_query, parent_data)
        parent_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Родительское задание создано с id: {parent_id}")
        return parent_id
    except Exception as e:
        print("Ошибка при создании родительского задания:", e)
        conn.rollback()

def createSubtask(conn, user_id, parent_id):
    try:
        # 2. Создание подзадачи (child) для ранее созданного задания
        insert_child_query = """
        INSERT INTO tasks (task_name, user_id, parent_task_id)
        VALUES (%s, %s, %s)
        RETURNING id;
        """
        child_data = ("Подзадача для родительского задания", user_id, parent_id)
        cursor = conn.cursor()
        cursor.execute(insert_child_query, child_data)
        child_id = cursor.fetchone()[0]
        conn.commit()
        print(f"Подзадача создана с id: {child_id}")
    except Exception as e:
        print("Ошибка при создании подзадачи:", e)
        conn.rollback()

def calculateProgress(conn, task_id):
    cursor = conn.cursor()
    try:
        query = """
        SELECT status FROM tasks WHERE id = %s;
        """
        cursor.execute(query, (task_id,))
        status = cursor.fetchone()
        
        # cursor.close()
        # conn.close()
    except Exception as e:
        print(f"Ошибка при установки прогресса: {e}")
        return None
    
def deleteTask(conn, task_id):
    cursor = conn.cursor()
    try:
        query = """
        DELETE FROM tasks WHERE id = %s;
        """
        cursor.execute(query, (task_id,))
        conn.commit()
        return task_id
    except Exception as e:
        print(f"Ошибка при удалении задания: {e}")
    finally:
        cursor.close()
