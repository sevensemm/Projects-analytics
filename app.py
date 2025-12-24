import streamlit as st
from database import Database

st.set_page_config(
    page_title="Архитектурная компания - Личный кабинет",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get help': None,
        'Report a bug': None,
        'About': None
    }
)

# Инициализация БД
db = Database()

# Инициализация сессии
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['user_id'] = None
    st.session_state['login'] = None
    st.session_state['full_name'] = None
    st.session_state['is_admin'] = False

def login_page():
    st.title("Архитектурная компания")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.form("login_form"):
            login = st.text_input("Логин")
            password = st.text_input("Пароль", type="password")
            
            submit = st.form_submit_button("Войти")
            
            if submit:
                if not login or not password:
                    st.error("Заполните все поля")
                else:
                    user = db.authenticate_user(login, password)
                    if user:
                        st.session_state['authenticated'] = True
                        st.session_state['user_id'] = user['user_id']
                        st.session_state['login'] = user['login']
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
        st.caption(f"Логин: {st.session_state['login']}")
        
        if st.session_state['is_admin']:
            st.success("Администратор")
        else:
            st.info("Пользователь")
        
        st.markdown("---")
        
        # Меню навигации - только основные страницы
        st.write("**Основное меню**")
        
        if st.button("📁 Мои проекты", use_container_width=True):
            st.switch_page("pages/01_projects.py")
        
        if st.button("✅ Мои задачи", use_container_width=True):
            st.switch_page("pages/02_tasks.py")
        
        # Админские страницы показываем только админу
        if st.session_state['is_admin']:
            st.markdown("---")
            st.write("**Администрирование**")
            
            if st.button("🏗️ Управление проектами", use_container_width=True):
                st.switch_page("pages/03_admin_projects.py")
            
            if st.button("👥 Управление пользователями", use_container_width=True):
                st.switch_page("pages/04_admin_users.py")
            
            if st.button("⚙️ Настройки видимости", use_container_width=True):
                st.switch_page("pages/05_admin_visibility.py")
        
        st.markdown("---")
        
        # Кнопка выхода
        if st.button("🚪 Выйти из аккаунта", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state['authenticated'] = False
            st.rerun()
    
    # Основная область личного кабинета
    st.write(f"Добро пожаловать, **{st.session_state['full_name']}**!")
    
    # Статистика пользователя
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Количество проектов пользователя
        projects = db.get_user_projects(st.session_state['user_id'])
        st.metric("Мои проекты", len(projects))
    
    with col2:
        # Количество активных задач
        tasks = db.get_user_tasks(st.session_state['user_id'])
        active_tasks = tasks[tasks['status'] != 'completed']
        st.metric("Активные задачи", len(active_tasks))
    
    with col3:
        # Выполненные задачи
        completed_tasks = tasks[tasks['status'] == 'completed']
        st.metric("Выполнено задач", len(completed_tasks))
    
    # Быстрые действия
    st.markdown("---")
    st.subheader("Быстрые действия")
    
    action_col1, action_col2 = st.columns(2)
    
    with action_col1:
        if st.button("Перейти к моим проектам", use_container_width=True):
            st.switch_page("pages/01_projects.py")
        
        if st.button("Просмотреть мои задачи", use_container_width=True):
            st.switch_page("pages/02_tasks.py")
    
    with action_col2:
        if st.session_state['is_admin']:
            if st.button("Создать новый проект", use_container_width=True):
                st.switch_page("pages/03_admin_projects.py")
            
            if st.button("Добавить пользователя", use_container_width=True):
                st.switch_page("pages/04_admin_users.py")