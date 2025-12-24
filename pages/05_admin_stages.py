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

st.title("Администратор: Управление этапами")

# Выбор проекта
projects_df = db.get_all_projects()

if projects_df.empty:
    st.info("Сначала создайте проект")
    st.stop()

selected_project = st.selectbox(
    "Выберите проект",
    projects_df['project_name'].tolist(),
    key="project_select"
)

project_id = projects_df[projects_df['project_name'] == selected_project].iloc[0]['project_id']

st.markdown("---")

# Создание нового этапа
st.subheader(f"Создать этап для проекта: {selected_project}")
with st.form("create_stage_form"):
    stage_name = st.text_input("Название этапа")
    
    if st.form_submit_button("Создать этап"):
        if stage_name:
            stage_id = db.create_stage(project_id, stage_name)
            st.success(f"Этап '{stage_name}' создан (ID: {stage_id})")
            st.rerun()
        else:
            st.error("Введите название этапа")

st.markdown("---")

# Управление существующими этапами
st.subheader("Существующие этапы")

# Получение этапов проекта
stages_df = db.get_project_stages(project_id)

if stages_df.empty:
    st.info("В проекте нет этапов")
else:
    for _, stage in stages_df.iterrows():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{stage['stage_name']}**")
            if stage['assigned_users']:
                st.caption(f"Ответственные: {stage['assigned_users']}")
            else:
                st.caption("Ответственные не назначены")
        
        with col2:
            if st.button("Удалить этап", key=f"delete_{stage['stage_id']}"):
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Stages WHERE stage_id = ?", (stage['stage_id'],))
                conn.commit()
                conn.close()
                st.success(f"Этап '{stage['stage_name']}' удален")
                st.rerun()
        
        st.markdown("---")
    
    st.markdown("---")
    
    # Назначение пользователей на этапы
    st.subheader("Назначение пользователей на этапы")
    
    selected_stage = st.selectbox(
        "Выберите этап для назначения пользователей",
        stages_df['stage_name'].tolist(),
        key="stage_select"
    )
    
    stage_id = stages_df[stages_df['stage_name'] == selected_stage].iloc[0]['stage_id']
    
    # Получение всех пользователей
    users_df = db.get_all_users()
    
    st.write(f"**Назначение пользователей на этап: {selected_stage}**")
    
    for _, user in users_df.iterrows():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(user['full_name'])
            if user['is_admin']:
                st.caption("Администратор")
        
        with col2:
            # Проверяем, назначен ли уже пользователь
            assigned_users = stages_df[
                stages_df['stage_id'] == stage_id
            ].iloc[0]['assigned_users']
            
            is_assigned = assigned_users and user['full_name'] in assigned_users
            
            if st.button(
                "Назначить" if not is_assigned else "Снять",
                key=f"assign_{user['user_id']}_{stage_id}"
            ):
                if not is_assigned:
                    success = db.assign_user_to_stage(stage_id, user['user_id'])
                    if success:
                        st.success(f"{user['full_name']} назначен на этап")
                    else:
                        st.info("Пользователь уже назначен")
                else:
                    success = db.remove_user_from_stage(stage_id, user['user_id'])
                    if success:
                        st.info(f"{user['full_name']} снят с этапа")
                    else:
                        st.info("Пользователь не был назначен")
                st.rerun()
        
        st.markdown("---")