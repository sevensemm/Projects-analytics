import streamlit as st
from database import Database

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

db = Database()

st.title("Мои проекты")

# Проверяем есть ли у нас функция get_user_projects_with_admin
try:
    # Пробуем использовать новую функцию если она есть
    if st.session_state.get('is_admin'):
        # Админ видит все проекты
        projects_df = db.get_all_projects()
    else:
        # Обычный пользователь видит только проекты со своими задачами
        projects_df = db.get_user_projects(st.session_state['user_id'])
except:
    # Если функция не найдена, создадим её в database.py
    st.info("Настройка отображения проектов...")
    
    # Показываем тестовый проект для проверки
    projects_df = db.get_all_projects() if st.session_state.get('is_admin') else None
    
    if projects_df is None or projects_df.empty:
        st.info("У вас пока нет проектов с задачами")
        st.stop()

if projects_df.empty:
    if st.session_state.get('is_admin'):
        st.info("Создайте первый проект в разделе 'Администрирование: Проекты'")
    else:
        st.info("У вас пока нет проектов с задачами. Обратитесь к администратору.")
else:
    for _, project in projects_df.iterrows():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(project['project_name'])
            st.caption(f"ID: {project['project_id']}")
            st.caption(f"Создан: {project['created_at'][:10]}")
        
        with col2:
            if st.button("Открыть", key=f"open_{project['project_id']}"):
                # Сохраняем проект в session_state
                st.session_state['selected_project'] = project['project_id']
                st.session_state['selected_project_name'] = project['project_name']
                st.switch_page("pages/_05_project_details.py")
        
        st.markdown("---")