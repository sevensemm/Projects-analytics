import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
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
                stage_cost DECIMAL(10,2) DEFAULT 0,
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
                planned_hours DECIMAL(5,2) DEFAULT 0,
                actual_hours DECIMAL(5,2) DEFAULT 0,
                actual_end_date DATE,
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
        
        # Зарплаты
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
        # Дебаг: проверяем что приходит
        print(f"DEBUG get_project_stages: project_id = {project_id}, type = {type(project_id)}")
        
        query = "SELECT * FROM Stages WHERE project_id = ? ORDER BY created_at"
        print(f"DEBUG SQL query: {query}")
        
        try:
            df = pd.read_sql_query(query, conn, params=(int(project_id),))
            print(f"DEBUG Found stages: {len(df)} stages")
            if len(df) > 0:
                print(f"DEBUG Stage names: {df['stage_name'].tolist()}")
        except Exception as e:
            print(f"DEBUG Error: {e}")
            df = pd.DataFrame()
        
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
    
    def update_stage_cost(self, stage_id, stage_cost):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Stages SET stage_cost = ? WHERE stage_id = ?
        ''', (stage_cost, stage_id))
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
        
        date_start_obj = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end_obj = datetime.strptime(date_end, '%Y-%m-%d').date()
        planned_days = (date_end_obj - date_start_obj).days + 1
        planned_hours = planned_days * 8
        
        cursor.execute('''
            INSERT INTO Tasks (stage_id, user_id, task_name, date_start, date_end, planned_hours)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (stage_id, user_id, task_name, date_start, date_end, planned_hours))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id
    
    def update_task_status(self, task_id, status):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status == 'completed':
            cursor.execute('SELECT date_start, date_end FROM Tasks WHERE task_id = ?', (task_id,))
            task = cursor.fetchone()
            
            if task and task['date_start']:
                date_start = datetime.strptime(task['date_start'], '%Y-%m-%d').date()
                date_end = datetime.now().date()
                
                actual_days = (date_end - date_start).days + 1
                actual_hours = actual_days * 8
                
                cursor.execute('''
                    UPDATE Tasks 
                    SET status = ?, actual_hours = ?, actual_end_date = ?
                    WHERE task_id = ?
                ''', (status, actual_hours, date_end.strftime('%Y-%m-%d'), task_id))
            else:
                cursor.execute('''
                    UPDATE Tasks 
                    SET status = ?, actual_end_date = ?
                    WHERE task_id = ?
                ''', (status, datetime.now().strftime('%Y-%m-%d'), task_id))
        else:
            cursor.execute('''
                UPDATE Tasks 
                SET status = ?, actual_hours = 0, actual_end_date = NULL
                WHERE task_id = ?
            ''', (status, task_id))
        
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
    
    # Зарплаты
    def add_salary(self, user_id, month, salary_amount, hourly_rate=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if hourly_rate is None:
            hourly_rate = salary_amount / (22 * 8)
        
        cursor.execute('''
            INSERT OR REPLACE INTO Salaries (user_id, month, salary_amount, hourly_rate)
            VALUES (?, ?, ?, ?)
        ''', (user_id, month, salary_amount, hourly_rate))
        
        conn.commit()
        conn.close()
    
    def get_user_salary(self, user_id, month=None):
        conn = self.get_connection()
        
        if month:
            query = '''
                SELECT * FROM Salaries 
                WHERE user_id = ? AND month = ?
                ORDER BY month DESC
            '''
            df = pd.read_sql_query(query, conn, params=(user_id, month))
        else:
            query = '''
                SELECT * FROM Salaries 
                WHERE user_id = ?
                ORDER BY month DESC
            '''
            df = pd.read_sql_query(query, conn, params=(user_id,))
        
        conn.close()
        return df
    
    def get_all_salaries(self, month=None):
        conn = self.get_connection()
        
        if month:
            query = '''
                SELECT s.*, u.full_name, u.login
                FROM Salaries s
                JOIN Users u ON s.user_id = u.user_id
                WHERE s.month = ?
                ORDER BY u.full_name
            '''
            df = pd.read_sql_query(query, conn, params=(month,))
        else:
            query = '''
                SELECT s.*, u.full_name, u.login
                FROM Salaries s
                JOIN Users u ON s.user_id = u.user_id
                ORDER BY s.month DESC, u.full_name
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    # Аналитика - ИСПРАВЛЕННЫЕ МЕТОДЫ
    def get_stage_analytics(self, stage_id):
        conn = self.get_connection()
        
        query = '''
            SELECT 
                t.*,
                u.full_name as responsible_name,
                s.stage_cost,
                CASE 
                    WHEN t.status = 'completed' AND t.actual_hours > 0 AND t.planned_hours > 0 THEN
                        CASE 
                            WHEN t.actual_hours <= t.planned_hours THEN 'ontime'
                            ELSE 'delayed'
                        END
                    WHEN t.status = 'pending' THEN 'pending'
                    ELSE 'unknown'
                END as task_status_type
            FROM Stages s
            LEFT JOIN Tasks t ON s.stage_id = t.stage_id
            LEFT JOIN Users u ON t.user_id = u.user_id
            WHERE s.stage_id = ?
            ORDER BY 
                CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END,
                t.date_end
        '''
        
        df = pd.read_sql_query(query, conn, params=(stage_id,))
        conn.close()
        return df
    
    def get_project_analytics(self, project_id):
        conn = self.get_connection()
        
        query = '''
            SELECT 
                s.stage_id,
                s.stage_name,
                s.stage_cost,
                COUNT(t.task_id) as task_count,
                SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_count,
                COALESCE(SUM(t.planned_hours), 0) as total_planned_hours,
                COALESCE(SUM(t.actual_hours), 0) as total_actual_hours,
                CASE 
                    WHEN SUM(t.actual_hours) > 0 AND SUM(t.planned_hours) > 0 
                    THEN SUM(t.actual_hours) / SUM(t.planned_hours)
                    ELSE NULL 
                END as avg_efficiency
            FROM Stages s
            LEFT JOIN Tasks t ON s.stage_id = t.stage_id
            WHERE s.project_id = ?
            GROUP BY s.stage_id, s.stage_name, s.stage_cost
            ORDER BY s.created_at
        '''
        
        df = pd.read_sql_query(query, conn, params=(project_id,))
        conn.close()
        return df
    
    def get_employee_performance(self, start_date=None, end_date=None):
        conn = self.get_connection()
        
        where_clause = ""
        params = []
        
        if start_date and end_date:
            where_clause = "WHERE t.actual_end_date BETWEEN ? AND ?"
            params = [start_date, end_date]
        elif start_date:
            where_clause = "WHERE t.actual_end_date >= ?"
            params = [start_date]
        elif end_date:
            where_clause = "WHERE t.actual_end_date <= ?"
            params = [end_date]
        else:
            # Если даты не указаны, берем последние 30 дней
            where_clause = "WHERE t.actual_end_date >= date('now', '-30 days')"
        
        query = f'''
            SELECT 
                u.user_id,
                u.full_name,
                u.login,
                COUNT(t.task_id) as total_tasks,
                SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                COALESCE(SUM(t.planned_hours), 0) as total_planned_hours,
                COALESCE(SUM(t.actual_hours), 0) as total_actual_hours,
                CASE 
                    WHEN SUM(t.actual_hours) > 0 AND SUM(t.planned_hours) > 0 
                    THEN SUM(t.actual_hours) / SUM(t.planned_hours)
                    ELSE NULL 
                END as avg_efficiency,
                COUNT(CASE WHEN t.status = 'completed' AND t.actual_hours <= t.planned_hours THEN 1 END) as ontime_tasks,
                COUNT(CASE WHEN t.status = 'completed' AND t.actual_hours > t.planned_hours THEN 1 END) as delayed_tasks
            FROM Users u
            LEFT JOIN Tasks t ON u.user_id = t.user_id
            {where_clause}
            GROUP BY u.user_id, u.full_name, u.login
            HAVING total_tasks > 0
            ORDER BY total_actual_hours DESC
        '''
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df