import sqlite3
import pandas as pd
from datetime import datetime

def update_database():
    conn = sqlite3.connect("architecture.db")
    cursor = conn.cursor()
    
    # Проверяем структуру таблицы Tasks
    cursor.execute("PRAGMA table_info(Tasks)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Если нет поля actual_hours - добавляем 
    if 'actual_hours' not in columns:
        cursor.execute('''
            ALTER TABLE Tasks ADD COLUMN actual_hours DECIMAL(5,2) DEFAULT 0
        ''')
        print("Добавлено поле actual_hours")
    
    # Проверяем тип данных для плановых часов
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Tasks'")
    if cursor.fetchone():
        print("База данных успешно обновлена")
    
    conn.commit()
    conn.close()
    print("Миграция завершена!")

if __name__ == "__main__":
    update_database()