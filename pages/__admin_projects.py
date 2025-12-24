import streamlit as st
from database import Database

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав")
    st.stop()

db = Database()

st.title("Администрирование: Проекты и этапы")

st.subheader("Создать проект")
with st.form("create_project_form", clear_on_submit=True):
    project_name = st.text_input("Название проекта")
    
    if st.form_submit_button("Создать проект"):
        if project_name:
            project_id = db.create_project(project_name)
            st.success(f"Проект '{project_name}' создан")
            st.rerun()
        else:
            st.error("Введите название проекта")

st.markdown("---")

st.subheader("Управление проектами")

projects_df = db.get_all_projects()

if projects_df.empty:
    st.info("Нет проектов")
else:
    for _, project in projects_df.iterrows():
        with st.expander(f"📁 Проект: {project['project_name']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.caption(f"ID: {project['project_id']}")
                st.caption(f"Создан: {project['created_at'][:10]}")
            
            with col2:
                if st.button("Удалить проект", key=f"delete_project_{project['project_id']}"):
                    db.delete_project(project['project_id'])
                    st.success("Проект удален")
                    st.rerun()
            
            st.markdown("---")
            
            st.write("**Добавить этап**")
            with st.form(f"create_stage_form_{project['project_id']}", clear_on_submit=True):
                stage_name = st.text_input("Название этапа", key=f"stage_name_{project['project_id']}")
                
                if st.form_submit_button("Добавить этап"):
                    if stage_name:
                        stage_id = db.create_stage(project['project_id'], stage_name)
                        st.success(f"Этап '{stage_name}' добавлен")
                        st.rerun()
                    else:
                        st.error("Введите название этапа")
            
            st.markdown("---")
            
            stages_df = db.get_project_stages(project['project_id'])
            
            if not stages_df.empty:
                st.write("**Этапы проекта:**")
                for _, stage in stages_df.iterrows():
                    stage_col1, stage_col2 = st.columns([3, 1])
                    
                    with stage_col1:
                        st.write(f"• {stage['stage_name']}")
                    
                    with stage_col2:
                        if st.button("Удалить этап", key=f"delete_stage_{stage['stage_id']}"):
                            db.delete_stage(stage['stage_id'])
                            st.success(f"Этап '{stage['stage_name']}' удален")
                            st.rerun()