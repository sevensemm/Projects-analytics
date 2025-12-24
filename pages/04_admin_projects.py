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

# Проверка прав администратора
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав")
    st.stop()

db = Database()

st.title("Администратор: Управление проектами")

# Создание нового проекта
st.subheader("Создать новый проект")
with st.form("create_project_form"):
    project_name = st.text_input("Название проекта")
    
    if st.form_submit_button("Создать проект"):
        if project_name:
            project_id = db.create_project(project_name)
            st.success(f"Проект '{project_name}' создан (ID: {project_id})")
            st.rerun()
        else:
            st.error("Введите название проекта")

st.markdown("---")

# Список существующих проектов
st.subheader("Существующие проекты")
projects_df = db.get_all_projects()

if projects_df.empty:
    st.info("Нет проектов")
else:
    for _, project in projects_df.iterrows():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{project['project_name']}**")
            st.caption(f"ID: {project['project_id']} | Создан: {project['created_at'][:10]}")
        
        with col2:
            if st.button("Удалить", key=f"delete_{project['project_id']}"):
                db.delete_project(project['project_id'])
                st.success("Проект удален")
                st.rerun()
        
        st.markdown("---")