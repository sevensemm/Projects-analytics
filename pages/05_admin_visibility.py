import streamlit as st
from database import Database

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав")
    st.stop()

db = Database()

st.title("Администрирование: Управление видимостью")

# Выбор проекта
projects_df = db.get_all_projects()

if projects_df.empty:
    st.info("Нет проектов")
    st.stop()

selected_project = st.selectbox(
    "Выберите проект",
    projects_df['project_name'].tolist(),
    key="project_select"
)

project_id = projects_df[projects_df['project_name'] == selected_project].iloc[0]['project_id']

st.markdown("---")

# Управление видимостью этапов
st.subheader(f"Этапы проекта: {selected_project}")

stages_df = db.get_project_stages(project_id, user_is_admin=True)

if stages_df.empty:
    st.info("В проекте нет этапов")
else:
    for _, stage in stages_df.iterrows():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{stage['stage_name']}**")
            status = "✅ Видимый" if stage['is_visible'] == 1 else "❌ Скрытый"
            st.caption(status)
        
        with col2:
            current_state = bool(stage['is_visible'])
            new_state = st.checkbox(
                "Видимый",
                value=current_state,
                key=f"stage_vis_{stage['stage_id']}",
                on_change=lambda s=stage, cs=current_state: toggle_stage_visibility(s, cs)
            )
        
        st.markdown("---")

def toggle_stage_visibility(stage, current_state):
    """Переключить видимость этапа"""
    new_state = not current_state
    db.update_stage_visibility(stage['stage_id'], new_state)
    st.rerun()

st.markdown("---")

# Управление видимостью задач
st.subheader("Видимость задач по этапам")

for _, stage in stages_df.iterrows():
    with st.expander(f"Задачи этапа: {stage['stage_name']}", expanded=False):
        tasks_df = db.get_stage_tasks(stage['stage_id'])
        
        if tasks_df.empty:
            st.info("В этапе нет задач")
        else:
            for _, task in tasks_df.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"• {task['task_name']}")
                    if task.get('is_visible', 1) == 1:
                        st.caption("✅ Видимая")
                    else:
                        st.caption("❌ Скрытая")
                
                with col2:
                    if task.get('assigned_user_name'):
                        st.caption(f"Ответственный: {task['assigned_user_name']}")
                
                with col3:
                    task_visible = task.get('is_visible', 1) == 1
                    new_visible = st.checkbox(
                        "Видимая",
                        value=task_visible,
                        key=f"task_vis_{task['task_id']}",
                        on_change=lambda t=task, tv=task_visible: toggle_task_visibility(t, tv)
                    )
                
                st.markdown("---")

def toggle_task_visibility(task, current_visible):
    """Переключить видимость задачи"""
    new_visible = not current_visible
    db.update_task_visibility(task['task_id'], new_visible)
    st.rerun()