import os
import sqlite3

# Удаляем старую базу
if os.path.exists("architecture.db"):
    os.remove("architecture.db")
    print("База данных удалена")

# Создаем новую
conn = sqlite3.connect("architecture.db")
cursor = conn.cursor()

# Создаем таблицы
cursor.execute('''
    CREATE TABLE Users (
        user_id INTEGER PRIMARY KEY,
        user_name TEXT UNIQUE NOT NULL,
        user_surname TEXT NOT NULL,
        user_password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE Projects (
        project_id INTEGER PRIMARY KEY,
        project_name TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES Users(user_id)
    )
''')

cursor.execute('''
    CREATE TABLE Project_Users (
        project_user_id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
        UNIQUE(project_id, user_id)
    )
''')

cursor.execute('''
    CREATE TABLE Stages (
        stage_id INTEGER PRIMARY KEY,
        project_id INTEGER NOT NULL,
        stage_name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
    )
''')

cursor.execute('''
    CREATE TABLE Tasks (
        task_id INTEGER PRIMARY KEY,
        stage_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        task_name TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        date_start DATE,
        date_end DATE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stage_id) REFERENCES Stages(stage_id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES Users(user_id)
    )
''')

# Администратор
cursor.execute('''
    INSERT INTO Users (user_id, user_name, user_surname, user_password, is_admin)
    VALUES (1, 'admin', 'admin', '1679', 1)
''')

conn.commit()
conn.close()

print("Новая база данных создана")
print("Администратор: admin/1679")