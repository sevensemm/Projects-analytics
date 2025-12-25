import sqlite3
from datetime import datetime

def migrate_database():
    """Миграция существующей базы данных для аналитики"""
    
    conn = sqlite3.connect('architecture.db')
    cursor = conn.cursor()
    
    print("Начинаю миграцию базы данных...")
    
    try:
        # 1. Проверяем существующие таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Найдены таблицы: {tables}")
        
        # 2. Добавляем столбец stage_cost в Stages (если нет)
        cursor.execute("PRAGMA table_info(Stages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'stage_cost' not in columns:
            cursor.execute('ALTER TABLE Stages ADD COLUMN stage_cost DECIMAL(10,2) DEFAULT 0')
            print("✓ Добавлен столбец stage_cost в таблицу Stages")
        
        # 3. Удаляем старые столбцы видимости (если есть)
        if 'is_visible' in columns:
            # Создаем временную таблицу без is_visible
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Stages_new (
                    stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    stage_name TEXT NOT NULL,
                    stage_cost DECIMAL(10,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
                )
            ''')
            
            cursor.execute('''
                INSERT INTO Stages_new (stage_id, project_id, stage_name, stage_cost, created_at)
                SELECT stage_id, project_id, stage_name, 0, created_at FROM Stages
            ''')
            
            cursor.execute('DROP TABLE Stages')
            cursor.execute('ALTER TABLE Stages_new RENAME TO Stages')
            print("✓ Удален столбец is_visible из таблицы Stages")
        
        # 4. Обновляем таблицу Tasks
        cursor.execute("PRAGMA table_info(Tasks)")
        task_columns = [col[1] for col in cursor.fetchall()]
        
        # Удаляем is_visible из Tasks
        if 'is_visible' in task_columns:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Tasks_new (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    task_name TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    date_start DATE,
                    date_end DATE NOT NULL,
                    planned_hours DECIMAL(5,2) DEFAULT 0,
                    actual_hours DECIMAL(5,2) DEFAULT 0,
                    actual_end_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (stage_id) REFERENCES Stages(stage_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES Users(user_id)
                )
            ''')
            
            cursor.execute('''
                INSERT INTO Tasks_new (
                    task_id, stage_id, user_id, task_name, status, 
                    date_start, date_end, created_at
                )
                SELECT 
                    task_id, stage_id, user_id, task_name, status,
                    date_start, date_end, created_at
                FROM Tasks
            ''')
            
            cursor.execute('DROP TABLE Tasks')
            cursor.execute('ALTER TABLE Tasks_new RENAME TO Tasks')
            print("✓ Обновлена таблица Tasks (удален is_visible, добавлены новые поля)")
        
        # 5. Добавляем недостающие поля в Tasks
        cursor.execute("PRAGMA table_info(Tasks)")
        task_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ('planned_hours', 'DECIMAL(5,2) DEFAULT 0'),
            ('actual_hours', 'DECIMAL(5,2) DEFAULT 0'),
            ('actual_end_date', 'DATE')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in task_columns:
                cursor.execute(f'ALTER TABLE Tasks ADD COLUMN {column_name} {column_type}')
                print(f"✓ Добавлен столбец {column_name} в таблицу Tasks")
        
        # 6. Создаем таблицу Salaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Salaries (
                salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month DATE NOT NULL,
                salary_amount DECIMAL(10,2) NOT NULL,
                hourly_rate DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES Users(user_id),
                UNIQUE(user_id, month)
            )
        ''')
        print("✓ Создана таблица Salaries")
        
        # 7. Рассчитываем planned_hours для существующих задач
        cursor.execute('''
            UPDATE Tasks 
            SET planned_hours = 
                CASE 
                    WHEN date_start IS NOT NULL AND date_end IS NOT NULL 
                    THEN (julianday(date_end) - julianday(date_start) + 1) * 8
                    ELSE 0
                END
            WHERE planned_hours = 0
        ''')
        
        updated = cursor.rowcount
        print(f"✓ Рассчитаны planned_hours для {updated} задач")
        
        # 8. Рассчитываем actual_hours для выполненных задач
        cursor.execute('''
            UPDATE Tasks 
            SET actual_hours = 
                CASE 
                    WHEN status = 'completed' AND date_start IS NOT NULL AND actual_end_date IS NOT NULL
                    THEN (julianday(actual_end_date) - julianday(date_start) + 1) * 8
                    ELSE 0
                END
            WHERE actual_hours = 0 AND status = 'completed'
        ''')
        
        updated = cursor.rowcount
        print(f"✓ Рассчитаны actual_hours для {updated} выполненных задач")
        
        conn.commit()
        print("\n✅ Миграция успешно завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
    print("\nТеперь можно запустить приложение:")
    print("streamlit run app.py --clear-cache")