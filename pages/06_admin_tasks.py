import streamlit as st
from database import Database
from datetime import datetime, date

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

def display_task_admin(task, db_instance, is_completed=False):
    """Отображение задачи для администратора"""
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            status_text = "✓" if is_completed else "○"
            st.write(status_text)
        
        with col2:
            if is_completed:
                st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", unsafe_allow_html=True)
            else:
                st.write(f"**{task['task_name']}**")
            
            if task['assigned_user_name']:
                st.caption(f"Ответственный: {task['assigned_user_name']}")
        
        with col3:
            if task['date_end']:
                deadline_date = datetime.strptime(task['date_end'], '%Y-%m-%d').date()
                today = date.today()
                
                if is_completed:
                    st.info(f"Выполнено: {task['date_end']}")
                elif deadline_date < today:
                    st.error(f"Просрочено: {task['date_end']}")
                else:
                    days_left = (deadline_date - today).days
                    st.warning(f"Срок: {task['date_end']} ({days_left} дней)")
        
        with col4:
            col4_1, col4_2 = st.columns(2)
            with col4_1:
                # Кнопка изменения статуса
                if not is_completed:
                    if st.button("✓ Завершить", key=f"complete_{task['task_id']}"):
                        db_instance.update_task_status(task['task_id'], 'completed')
                        st.success("Задача завершена")
                        st.rerun()
                else:
                    if st.button("↻ Возобновить", key=f"reopen_{task['task_id']}"):
                        db_instance.update_task_status(task['task_id'], 'pending')
                        st.info("Задача возобновлена")
                        st.rerun()
            
            with col4_2:
                # Кнопка удаления задачи
                if st.button("🗑️ Удалить", key=f"delete_{task['task_id']}"):
                    conn = db_instance.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM Tasks WHERE task_id = ?", (task['task_id'],))
                    conn.commit()
                    conn.close()
                    st.success("Задача удалена")
                    st.rerun()
        
        st.markdown("---")

st.title("Администратор: Управление задачами")

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

# Получение этапов проекта
stages_df = db.get_project_stages(project_id)

if stages_df.empty:
    st.info("В проекте нет этапов")
    st.stop()

selected_stage = st.selectbox(
    "Выберите этап",
    stages_df['stage_name'].tolist(),
    key="stage_select"
)

stage_id = stages_df[stages_df['stage_name'] == selected_stage].iloc[0]['stage_id']

st.markdown("---")

# Создание новой задачи
st.subheader(f"Создать задачу для этапа: {selected_stage}")

users_df = db.get_all_users()
user_options = {row['full_name']: row['user_id'] for _, row in users_df.iterrows()}

with st.form("create_task_form"):
    task_name = st.text_input("Название задачи")
    selected_user = st.selectbox("Ответственный", list(user_options.keys()))
    date_end = st.date_input("Дата окончания", min_value=date.today())
    
    if st.form_submit_button("Создать задачу"):
        if task_name and selected_user:
            user_id = user_options[selected_user]
            task_id = db.create_task(stage_id, user_id, task_name, date_end.strftime('%Y-%m-%d'))
            st.success(f"Задача '{task_name}' создана (ID: {task_id})")
            st.rerun()
        else:
            st.error("Заполните все поля")

st.markdown("---")

# Просмотр существующих задач
st.subheader("Существующие задачи")

tasks_df = db.get_stage_tasks(stage_id)

if tasks_df.empty:
    st.info("В этапе нет задач")
else:
    # Разделяем выполненные и активные задачи
    completed_tasks = tasks_df[tasks_df['status'] == 'completed']
    active_tasks = tasks_df[tasks_df['status'] != 'completed']
    
    # Показываем активные задачи
    if not active_tasks.empty:
        st.write("**Активные задачи:**")
        for _, task in active_tasks.iterrows():
            display_task_admin(task, db)
    
    # Показываем выполненные задачи
    if not completed_tasks.empty:
        st.write("**Выполненные задачи:**")
        for _, task in completed_tasks.iterrows():
            display_task_admin(task, db, is_completed=True)