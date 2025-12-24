import sqlite3

def update_database_structure():
    """Обновляет структуру базы данных, удаляя столбцы видимости"""
    
    conn = sqlite3.connect('architecture.db')
    cursor = conn.cursor()
    
    print("Начинаю обновление структуры базы данных...")
    
    try:
        # 1. Проверяем, есть ли столбцы is_visible
        cursor.execute("PRAGMA table_info(Stages)")
        stages_columns = cursor.fetchall()
        has_visibility_in_stages = any(col[1] == 'is_visible' for col in stages_columns)
        
        cursor.execute("PRAGMA table_info(Tasks)")
        tasks_columns = cursor.fetchall()
        has_visibility_in_tasks = any(col[1] == 'is_visible' for col in tasks_columns)
        
        if not has_visibility_in_stages and not has_visibility_in_tasks:
            print("База данных уже обновлена. Столбцы is_visible не найдены.")
            conn.close()
            return
        
        print("Обнаружены старые столбцы видимости. Начинаю обновление...")
        
        # 2. Создаем временные таблицы
        cursor.executescript('''
            -- Сохраняем старые данные
            CREATE TABLE IF NOT EXISTS Old_Stages AS SELECT * FROM Stages;
            CREATE TABLE IF NOT EXISTS Old_Tasks AS SELECT * FROM Tasks;
            
            -- Создаем новые таблицы без is_visible
            CREATE TABLE New_Stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
            );
            
            CREATE TABLE New_Tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                date_start DATE,
                date_end DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stage_id) REFERENCES New_Stages(stage_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            );
        ''')
        
        # 3. Копируем данные из старых таблиц в новые
        if has_visibility_in_stages:
            cursor.execute('''
                INSERT INTO New_Stages (stage_id, project_id, stage_name, created_at)
                SELECT stage_id, project_id, stage_name, created_at FROM Old_Stages
            ''')
        else:
            cursor.execute('INSERT INTO New_Stages SELECT * FROM Stages')
        
        if has_visibility_in_tasks:
            cursor.execute('''
                INSERT INTO New_Tasks (task_id, stage_id, user_id, task_name, status, date_start, date_end, created_at)
                SELECT task_id, stage_id, user_id, task_name, status, date_start, date_end, created_at FROM Old_Tasks
            ''')
        else:
            cursor.execute('INSERT INTO New_Tasks SELECT * FROM Tasks')
        
        # 4. Удаляем старые таблицы и переименовываем новые
        cursor.executescript('''
            DROP TABLE Tasks;
            DROP TABLE Stages;
            
            ALTER TABLE New_Stages RENAME TO Stages;
            ALTER TABLE New_Tasks RENAME TO Tasks;
            
            DROP TABLE IF EXISTS Old_Stages;
            DROP TABLE IF EXISTS Old_Tasks;
        ''')
        
        conn.commit()
        print("Структура базы данных успешно обновлена!")
        print("Столбцы is_visible удалены из таблиц Stages и Tasks.")
        
    except Exception as e:
        print(f"Ошибка при обновлении базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_structure()
    print("\nОбновление завершено. Теперь запустите приложение с новой версией database.py")