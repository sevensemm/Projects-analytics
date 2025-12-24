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

if 'selected_project' not in st.session_state:
    st.error("Проект не выбран")
    st.stop()

db = Database()
project_id = st.session_state['selected_project']

# Получение информации о проекте
projects_df = db.get_all_projects()
current_project = projects_df[projects_df['project_id'] == project_id]

if not current_project.empty:
    st.title(f"Проект: {current_project.iloc[0]['project_name']}")

# Кнопка возврата
if st.button("Назад к проектам"):
    del st.session_state['selected_project']
    st.switch_page("pages/01_projects.py")

st.markdown("---")

# Получение этапов проекта
stages_df = db.get_project_stages(project_id)

if stages_df.empty:
    st.info("В проекте нет этапов")
else:
    for _, stage in stages_df.iterrows():
        with st.expander(f"Этап: {stage['stage_name']}", expanded=False):
            if stage['assigned_users']:
                st.write(f"Ответственные: {stage['assigned_users']}")
            else:
                st.write("Ответственные не назначены")
            
            if st.button("Задачи", key=f"tasks_{stage['stage_id']}"):
                st.session_state['selected_stage'] = stage['stage_id']
                st.switch_page("pages/03_tasks.py")
        
        st.markdown("---")