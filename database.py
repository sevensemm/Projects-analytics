import sqlite3
import pandas as pd
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="db/construction_company.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных с нужными таблицами"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                user_surname TEXT NOT NULL,
                user_password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        # Таблица проектов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица этапов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
            )
        ''')
        
        # Таблица участников этапов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Stage_Users (
                stage_user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                FOREIGN KEY (stage_id) REFERENCES Stages(stage_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
                UNIQUE(stage_id, user_id)
            )
        ''')
        
        # Таблица задач
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        
        # Таблица комментариев
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Task_Comments (
                comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES Tasks(task_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES Users(user_id)
            )
        ''')
        
        # Создаем администратора по умолчанию если нет пользователей
        cursor.execute("SELECT COUNT(*) FROM Users")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO Users (user_name, user_surname, user_password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin', 'admin123', 1))
            print("Создан администратор: admin/admin123")
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Аутентификация
    def authenticate_user(self, username, password):
        """Аутентификация пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, user_name, user_surname, is_admin
            FROM Users 
            WHERE user_name = ? AND user_password = ?
        ''', (username, password))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                'user_id': user['user_id'],
                'name': f"{user['user_name']} {user['user_surname']}",
                'is_admin': bool(user['is_admin'])
            }
        return None
    
    # Проекты
    def get_all_projects(self):
        """Получить все проекты"""
        conn = self.get_connection()
        query = "SELECT * FROM Projects ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def create_project(self, project_name):
        """Создать новый проект"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Projects (project_name) VALUES (?)", (project_name,))
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return project_id
    
    def delete_project(self, project_id):
        """Удалить проект"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Projects WHERE project_id = ?", (project_id,))
        conn.commit()
        conn.close()
    
    # Этапы
    def get_project_stages(self, project_id):
        """Получить этапы проекта"""
        conn = self.get_connection()
        query = """
            SELECT s.*, 
                   GROUP_CONCAT(u.user_name || ' ' || u.user_surname) as assigned_users
            FROM Stages s
            LEFT JOIN Stage_Users su ON s.stage_id = su.stage_id
            LEFT JOIN Users u ON su.user_id = u.user_id
            WHERE s.project_id = ?
            GROUP BY s.stage_id
            ORDER BY s.created_at
        """
        df = pd.read_sql_query(query, conn, params=(project_id,))
        conn.close()
        return df
    
    def create_stage(self, project_id, stage_name):
        """Создать этап в проекте"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Stages (project_id, stage_name)
            VALUES (?, ?)
        ''', (project_id, stage_name))
        stage_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return stage_id
    
    def assign_user_to_stage(self, stage_id, user_id):
        """Назначить пользователя на этап"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO Stage_Users (stage_id, user_id)
                VALUES (?, ?)
            ''', (stage_id, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Уже назначен
        finally:
            conn.close()
    
    # Задачи
    def get_stage_tasks(self, stage_id):
        """Получить задачи этапа"""
        conn = self.get_connection()
        query = """
            SELECT t.*, 
                   u.user_name || ' ' || u.user_surname as assigned_user_name
            FROM Tasks t
            LEFT JOIN Users u ON t.user_id = u.user_id
            WHERE t.stage_id = ?
            ORDER BY t.date_end
        """
        df = pd.read_sql_query(query, conn, params=(stage_id,))
        conn.close()
        return df
    
    def create_task(self, stage_id, user_id, task_name, date_end, date_start=None):
        """Создать задачу"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if date_start is None:
            date_start = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute('''
            INSERT INTO Tasks (stage_id, user_id, task_name, date_start, date_end)
            VALUES (?, ?, ?, ?, ?)
        ''', (stage_id, user_id, task_name, date_start, date_end))
        
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def update_task_status(self, task_id, status):
        """Обновить статус задачи"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Tasks SET status = ? WHERE task_id = ?", (status, task_id))
        conn.commit()
        conn.close()
    
    # Пользователи
    def get_all_users(self):
        """Получить всех пользователей"""
        conn = self.get_connection()
        query = """
            SELECT user_id, 
                   user_name || ' ' || user_surname as full_name,
                   is_admin
            FROM Users
            ORDER BY user_surname
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def create_user(self, user_name, user_surname, password, is_admin=False):
        """Создать нового пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Users (user_name, user_surname, user_password, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (user_name, user_surname, password, 1 if is_admin else 0))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    # Аналитика
    def get_project_progress(self, project_id):
        """Получить прогресс по проекту"""
        conn = self.get_connection()
        query = """
            SELECT 
                s.stage_name,
                COUNT(t.task_id) as total_tasks,
                SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM Stages s
            LEFT JOIN Tasks t ON s.stage_id = t.stage_id
            WHERE s.project_id = ?
            GROUP BY s.stage_id
        """
        df = pd.read_sql_query(query, conn, params=(project_id,))
        conn.close()
        return df