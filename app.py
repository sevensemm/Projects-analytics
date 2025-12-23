import streamlit as st
from database import Database
import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
from datetime import datetime

# Настройки страницы
st.set_page_config(
    page_title="Архитектурная компания",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Инициализация базы данных
db = Database()

def login_page():
    """Страница входа"""
    st.title("Архитектурная компания - Вход в систему")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Авторизация")
        
        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            
            submit = st.form_submit_button("Войти")
            
            if submit:
                if not username or not password:
                    st.error("Заполните все поля")
                else:
                    user = db.authenticate_user(username, password)
                    if user:
                        st.session_state['authenticated'] = True
                        st.session_state['user_id'] = user['user_id']
                        st.session_state['user_name'] = user['name']
                        st.session_state['is_admin'] = user['is_admin']
                        st.success(f"Добро пожаловать, {user['name']}")
                        st.rerun()
                    else:
                        st.error("Неверные учетные данные")

def main_app():
    """Основное приложение после входа"""
    # Боковая панель
    with st.sidebar:
        st.markdown(f"**Пользователь:** {st.session_state['user_name']}")
        
        if st.session_state.get('is_admin'):
            st.markdown("**Роль:** Администратор")
        
        st.markdown("---")
        
        # Навигация
        page_options = ["Проекты", "Аналитика"]
        
        if st.session_state.get('is_admin'):
            page_options.append("Админ-панель")
        
        page = st.radio("Меню", page_options)
        
        st.markdown("---")
        
        if st.button("Выйти"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Отображение выбранной страницы
    if page == "Проекты":
        show_projects_page()
    elif page == "Аналитика":
        show_analytics_page()
    elif page == "Админ-панель":
        st.switch_page("pages/04_admin.py")

def show_projects_page():
    """Страница проектов"""
    st.title("Проекты")
    
    projects_df = db.get_all_projects()
    
    if projects_df.empty:
        st.info("Нет проектов")
        return
    
    # Отображение проектов
    for _, project in projects_df.iterrows():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(project['project_name'])
            st.caption(f"ID: {project['project_id']} | Создан: {project['created_at'][:10]}")
        
        with col2:
            if st.button("Открыть", key=f"open_{project['project_id']}"):
                st.session_state['selected_project'] = project['project_id']
                st.switch_page("pages/01_projects.py")
        
        st.markdown("---")

def show_analytics_page():
    """Страница аналитики"""
    st.title("Аналитика проектов")
    
    projects_df = db.get_all_projects()
    
    if projects_df.empty:
        st.info("Нет данных для анализа")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Статистика проектов")
        st.dataframe(projects_df, use_container_width=True)
    
    with col2:
        st.subheader("График проектов")
        if len(projects_df) > 0:
            fig = px.bar(projects_df, x='project_name', title="Количество проектов")
            st.plotly_chart(fig, use_container_width=True)

# Основная логика
def main():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    if not st.session_state['authenticated']:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()