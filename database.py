import sqlite3
import pandas as pd
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="architecture.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        if os.path.dirname(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0
            )
        ''')
        
        # Проекты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Этапы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Stages (
                stage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES Projects(project_id) ON DELETE CASCADE
            )
        ''')
        
        # Задачи
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
        
        # Комментарии
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
        
        # Администратор
        cursor.execute("SELECT COUNT(*) FROM Users WHERE login='admin'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO Users (login, full_name, password, is_admin)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'Администратор', '1679', 1))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Аутентификация
    def authenticate_user(self, login, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, login, full_name, is_admin
            FROM Users 
            WHERE login = ? AND password = ?
        ''', (login, password))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    # Проекты
    def get_user_projects(self, user_id):
        conn = self.get_connection()
        query = """
            SELECT DISTINCT p.*
            FROM Projects p
            JOIN Stages s ON p.project_id = s.project_id
            JOIN Tasks t ON s.stage_id = t.stage_id
            WHERE t.user_id = ? 
            ORDER BY p.created_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    def get_all_projects(self):
        conn = self.get_connection()
        query = "SELECT * FROM Projects ORDER BY created_at DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def create_project(self, project_name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Projects (project_name) VALUES (?)", (project_name,))
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return project_id
    
    def delete_project(self, project_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Projects WHERE project_id = ?", (project_id,))
        conn.commit()
        conn.close()
    
    # Этапы
    def get_project_stages(self, project_id):
        conn = self.get_connection()
        query = "SELECT * FROM Stages WHERE project_id = ? ORDER BY created_at"
        df = pd.read_sql_query(query, conn, params=(project_id,))
        conn.close()
        return df
    
    def create_stage(self, project_id, stage_name):
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
    
    def delete_stage(self, stage_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Stages WHERE stage_id = ?", (stage_id,))
        conn.commit()
        conn.close()
    
    # Задачи
    def get_stage_tasks(self, stage_id, current_user_id=None):
        conn = self.get_connection()
        if current_user_id:
            query = """
                SELECT t.*, u.full_name as responsible_name
                FROM Tasks t
                JOIN Users u ON t.user_id = u.user_id
                WHERE t.stage_id = ? 
                AND t.user_id = ?
                ORDER BY 
                    CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END,
                    t.date_end
            """
            df = pd.read_sql_query(query, conn, params=(stage_id, current_user_id))
        else:
            query = """
                SELECT t.*, u.full_name as responsible_name
                FROM Tasks t
                JOIN Users u ON t.user_id = u.user_id
                WHERE t.stage_id = ?
                ORDER BY 
                    CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END,
                    t.date_end
            """
            df = pd.read_sql_query(query, conn, params=(stage_id,))
        conn.close()
        return df
    
    def get_all_stage_tasks(self, stage_id):
        conn = self.get_connection()
        query = """
            SELECT t.*, u.full_name as responsible_name
            FROM Tasks t
            JOIN Users u ON t.user_id = u.user_id
            WHERE t.stage_id = ?
            ORDER BY 
                CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END,
                t.date_end
        """
        df = pd.read_sql_query(query, conn, params=(stage_id,))
        conn.close()
        return df
    
    def get_user_tasks(self, user_id):
        conn = self.get_connection()
        query = """
            SELECT t.*, 
                   s.stage_name,
                   p.project_name,
                   u.full_name as responsible_name
            FROM Tasks t
            JOIN Stages s ON t.stage_id = s.stage_id
            JOIN Projects p ON s.project_id = p.project_id
            JOIN Users u ON t.user_id = u.user_id
            WHERE t.user_id = ?
            ORDER BY 
                CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END,
                t.date_end
        """
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    def create_task(self, stage_id, user_id, task_name, date_end, date_start=None):
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
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Tasks SET status = ? WHERE task_id = ?", (status, task_id))
        conn.commit()
        conn.close()
    
    def delete_task(self, task_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Tasks WHERE task_id = ?", (task_id,))
        conn.commit()
        conn.close()
    
    # Пользователи
    def get_all_users(self):
        conn = self.get_connection()
        query = """
            SELECT user_id, login, full_name, is_admin
            FROM Users
            ORDER BY full_name
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def create_user(self, login, full_name, password, is_admin=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Users (login, full_name, password, is_admin)
            VALUES (?, ?, ?, ?)
        ''', (login, full_name, password, 1 if is_admin else 0))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def delete_user(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Users WHERE user_id = ? AND login != 'admin'", (user_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    # Комментарии
    def add_comment_to_task(self, task_id, user_id, comment_text):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Task_Comments (task_id, user_id, comment_text)
            VALUES (?, ?, ?)
        ''', (task_id, user_id, comment_text))
        conn.commit()
        conn.close()
    
    def get_task_comments(self, task_id):
        """Получить все комментарии к задаче"""
        conn = self.get_connection()
        query = """
            SELECT 
                tc.comment_id,
                tc.comment_text,
                tc.created_at,
                u.full_name as author_name,
                u.user_id
            FROM Task_Comments tc
            JOIN Users u ON tc.user_id = u.user_id
            WHERE tc.task_id = ?
            ORDER BY tc.created_at DESC
        """
        df = pd.read_sql_query(query, conn, params=(task_id,))
        conn.close()
        return df
    
    def delete_comment(self, comment_id, user_id):
        """Удалить комментарий (только свой)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM Task_Comments 
            WHERE comment_id = ? AND user_id = ?
        ''', (comment_id, user_id))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted