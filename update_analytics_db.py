import sqlite3

def update_database_for_analytics():
    """Добавляет новые поля и таблицы для аналитики"""
    
    conn = sqlite3.connect('architecture.db')
    cursor = conn.cursor()
    
    print("Начинаю обновление базы данных для аналитики...")
    
    try:
        # 1. Добавляем stage_cost в таблицу Stages
        cursor.execute("PRAGMA table_info(Stages)")
        stages_columns = [col[1] for col in cursor.fetchall()]
        
        if 'stage_cost' not in stages_columns:
            cursor.execute('ALTER TABLE Stages ADD COLUMN stage_cost DECIMAL(10,2) DEFAULT 0')
            print("✓ Добавлен столбец stage_cost в таблицу Stages")
        
        # 2. Добавляем новые поля в таблицу Tasks
        cursor.execute("PRAGMA table_info(Tasks)")
        tasks_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = [
            ('planned_hours', 'DECIMAL(5,2) DEFAULT 0'),
            ('actual_hours', 'DECIMAL(5,2) DEFAULT 0'),
            ('actual_end_date', 'DATE')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in tasks_columns:
                cursor.execute(f'ALTER TABLE Tasks ADD COLUMN {column_name} {column_type}')
                print(f"✓ Добавлен столбец {column_name} в таблицу Tasks")
        
        # 3. Создаем таблицу Salaries если её нет
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
        print("✓ Проверена/создана таблица Salaries")
        
        # 4. Обновляем существующие задачи с расчетом planned_hours
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
        print(f"✓ Обновлено planned_hours для {updated} задач")
        
        conn.commit()
        print("\n✅ База данных успешно обновлена для аналитики!")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_for_analytics()
    print("\nЗапустите скрипт миграции:")
    print("python update_analytics_db.py")