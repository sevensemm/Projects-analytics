import streamlit as st
from database import Database

# Настройки страницы
st.set_page_config(
    page_title="Архитектурная компания - Личный кабинет",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация БД
db = Database()

# Инициализация состояния сессии
if 'initialized' not in st.session_state:
    st.session_state['initialized'] = True
    st.session_state['authenticated'] = False
    st.session_state['user_id'] = None
    st.session_state['username'] = None
    st.session_state['full_name'] = None
    st.session_state['is_admin'] = False

def login_page():
    st.title("Архитектурная компания")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            username = st.text_input("Логин")
            password = st.text_input("Пароль", type="password")
            
            submit = st.form_submit_button("Войти")
            
            if submit:
                if not username or not password:
                    st.error("Заполните все поля")
                else:
                    user = db.authenticate_user(username, password)
                    if user:
                        # Сохраняем все данные в session_state
                        st.session_state['authenticated'] = True
                        st.session_state['user_id'] = user['user_id']
                        st.session_state['username'] = user['username']
                        st.session_state['full_name'] = user['full_name']
                        st.session_state['is_admin'] = bool(user['is_admin'])
                        st.success(f"Добро пожаловать, {st.session_state['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Неверный логин или пароль")

# Основная логика
if not st.session_state['authenticated']:
    login_page()
else:
    # Личный кабинет
    st.title("Личный кабинет")
    
    with st.sidebar:
        st.write(f"**{st.session_state['full_name']}**")
        st.caption(f"Логин: {st.session_state['username']}")
        
        if st.session_state['is_admin']:
            st.success("Режим администратора")
        else:
            st.info("Пользователь")
        
        st.markdown("---")
        
        # Меню навигации
        st.write("**Навигация**")
        
        # Всегда показываем Проекты
        if st.button("📁 Проекты", use_container_width=True):
            st.session_state['current_page'] = 'projects'
            st.switch_page("pages/01_projects.py")
        
        # Показываем Этапы и Задачи только если выбран проект/этап
        if 'selected_project' in st.session_state:
            if st.button("📋 Этапы проекта", use_container_width=True):
                st.switch_page("pages/02_stages.py")
        
        if 'selected_stage' in st.session_state:
            if st.button("✅ Задачи этапа", use_container_width=True):
                st.switch_page("pages/03_tasks.py")
        
        # Админские страницы только для админов
        if st.session_state['is_admin']:
            st.markdown("---")
            st.write("**Администрирование**")
            
            if st.button("🏗️ Управление проектами", use_container_width=True):
                st.switch_page("pages/04_admin_projects.py")
            
            if st.button("📊 Управление этапами", use_container_width=True):
                st.switch_page("pages/05_admin_stages.py")
            
            if st.button("✅ Управление задачами", use_container_width=True):
                st.switch_page("pages/06_admin_tasks.py")
            
            if st.button("👥 Управление пользователями", use_container_width=True):
                st.switch_page("pages/07_admin_users.py")
        
        st.markdown("---")
        
        # Кнопка выхода
        if st.button("🚪 Выйти из аккаунта", type="secondary", use_container_width=True):
            # Очищаем только session_state, не редиректим
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['initialized'] = True
            st.session_state['authenticated'] = False
            st.rerun()
    
    # Основная область - информация о пользователе
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Информация о пользователе")
        st.write(f"**Полное имя:** {st.session_state['full_name']}")
        st.write(f"**Логин:** {st.session_state['username']}")
        st.write(f"**ID пользователя:** {st.session_state['user_id']}")
        
        # Статистика пользователя
        st.subheader("Моя статистика")
        
        # Получаем задачи пользователя
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Все задачи пользователя
        cursor.execute('''
            SELECT COUNT(*) as total_tasks,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM Tasks 
            WHERE user_id = ?
        ''', (st.session_state['user_id'],))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats and stats['total_tasks'] > 0:
            completed = stats['completed_tasks'] or 0
            total = stats['total_tasks']
            progress = (completed / total) * 100
            
            st.write(f"**Всего задач:** {total}")
            st.write(f"**Выполнено:** {completed}")
            st.progress(progress / 100)
            st.caption(f"Прогресс: {progress:.1f}%")
        else:
            st.info("У вас пока нет задач")
    
    with col2:
        st.subheader("Быстрые действия")
        
        # Кнопки быстрого перехода
        if st.session_state['is_admin']:
            if st.button("➕ Создать проект", use_container_width=True):
                st.switch_page("pages/04_admin_projects.py")
            
            if st.button("➕ Добавить пользователя", use_container_width=True):
                st.switch_page("pages/07_admin_users.py")
        
        if st.button("📁 Мои проекты", use_container_width=True):
            st.switch_page("pages/01_projects.py")
        
        if st.button("✅ Мои задачи", use_container_width=True):
            # Создаем временную страницу для моих задач
            st.switch_page("pages/03_tasks.py")