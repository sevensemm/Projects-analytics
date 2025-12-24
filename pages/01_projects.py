import streamlit as st
from database import Database

# Проверяем аутентификацию
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.error("Требуется авторизация. Пожалуйста, войдите в систему.")
    
    # Кнопка для возврата на главную
    if st.button("Вернуться на главную"):
        st.switch_page("app.py")
    st.stop()

# Проверка авторизации
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

db = Database()

st.title("Проекты")

# Получение всех проектов
projects_df = db.get_all_projects()

if projects_df.empty:
    st.info("Нет доступных проектов")
else:
    for _, project in projects_df.iterrows():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader(project['project_name'])
            st.caption(f"Создан: {project['created_at'][:10]}")
        
        with col2:
            if st.button("Открыть", key=f"open_{project['project_id']}"):
                st.session_state['selected_project'] = project['project_id']
                st.switch_page("pages/02_stages.py")
        
        st.markdown("---")