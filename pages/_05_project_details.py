import streamlit as st
from database import Database
from datetime import datetime, date

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

# Проверяем выбрал ли пользователь проект
if 'selected_project' not in st.session_state:
    st.error("Проект не выбран. Вернитесь в 'Мои проекты' и выберите проект.")
    st.stop()

db = Database()
project_id = st.session_state['selected_project']

# Функция отображения задачи в этапе
def display_task_in_stage(task, is_completed=False):
    col1, col2, col3 = st.columns([1, 3, 2])
    
    with col1:
        if not is_completed:
            # Проверяем, принадлежит ли задача текущему пользователю
            task_belongs_to_user = task['user_id'] == st.session_state['user_id']
            
            if task_belongs_to_user:
                if st.checkbox(
                    "",
                    value=False,
                    key=f"stage_task_{task['task_id']}",
                    on_change=lambda t=task: complete_task_in_stage(t)
                ):
                    pass
            else:
                # Показываем, но не даем отмечать чужие задачи
                st.write("👤")
        else:
            st.write("✓")
    
    with col2:
        if is_completed:
            st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", 
                       unsafe_allow_html=True)
        else:
            st.write(f"**{task['task_name']}**")
        
        if task['responsible_name']:
            st.caption(f"Ответственный: {task['responsible_name']}")
    
    with col3:
        if task['date_end']:
            deadline_date = datetime.strptime(task['date_end'], '%Y-%m-%d').date()
            today = date.today()
            
            if is_completed:
                st.success("Выполнено")
            elif deadline_date < today:
                st.error(f"Просрочено: {task['date_end']}")
            else:
                days_left = (deadline_date - today).days
                st.warning(f"{task['date_end']} ({days_left} {'день' if days_left == 1 else 'дня' if 2 <= days_left <= 4 else 'дней'})")

def complete_task_in_stage(task):
    # Проверяем, что задача принадлежит пользователю
    if task['user_id'] == st.session_state['user_id']:
        db.update_task_status(task['task_id'], 'completed')
        st.rerun()
    else:
        st.error("Вы не можете отмечать чужие задачи")

# Создание задачи
def create_task_form(stage_id):
    with st.form(f"create_task_form_{stage_id}", clear_on_submit=True):
        st.write("**Добавить задачу**")
        
        task_name = st.text_input("Название задачи")
        
        # Выбор ответственного
        users_df = db.get_all_users()
        user_options = {row['full_name']: row['user_id'] for _, row in users_df.iterrows()}
        selected_user = st.selectbox("Ответственный", list(user_options.keys()))
        
        date_end = st.date_input("Срок выполнения", min_value=date.today())
        
        if st.form_submit_button("Создать задачу"):
            if task_name and selected_user:
                user_id = user_options[selected_user]
                task_id = db.create_task(stage_id, user_id, task_name, date_end.strftime('%Y-%m-%d'))
                st.success(f"Задача '{task_name}' создана для {selected_user}")
                st.rerun()
            else:
                st.error("Заполните все поля")

# Получаем информацию о проекте
st.title(f"Проект: {st.session_state.get('selected_project_name', f'ID {project_id}')}")

# Кнопка возврата
if st.button("← Назад к проектам"):
    # Очищаем выбранный проект
    if 'selected_project' in st.session_state:
        del st.session_state['selected_project']
    if 'selected_project_name' in st.session_state:
        del st.session_state['selected_project_name']
    st.switch_page("pages/01_projects.py")

st.markdown("---")

# Получаем этапы проекта с учетом видимости
stages_df = db.get_project_stages(project_id, user_is_admin=st.session_state.get('is_admin', False))

if stages_df.empty:
    st.info("В проекте нет этапов")
    
    # Если админ, показываем возможность добавить этап
    if st.session_state.get('is_admin'):
        st.write("**Чтобы добавить этапы, перейдите в раздел 'Администрирование: Проекты'**")
else:
    for _, stage in stages_df.iterrows():
        with st.expander(f"📋 Этап: {stage['stage_name']}", expanded=False):
            # Создание задачи для этого этапа (только для админа)
            if st.session_state.get('is_admin'):
                create_task_form(stage['stage_id'])
                st.markdown("---")
            
            # Получаем задачи этапа
            # Админ видит все задачи, пользователь только свои
            if st.session_state.get('is_admin'):
                tasks_df = db.get_all_stage_tasks(stage['stage_id'])
            else:
                tasks_df = db.get_stage_tasks(stage['stage_id'], current_user_id=st.session_state['user_id'])
            
            if tasks_df.empty:
                st.info("В этапе нет задач")
            else:
                # Разделяем выполненные и активные
                completed_tasks = tasks_df[tasks_df['status'] == 'completed']
                active_tasks = tasks_df[tasks_df['status'] != 'completed']
                
                # Активные задачи
                if not active_tasks.empty:
                    st.write("**Активные задачи:**")
                    for _, task in active_tasks.iterrows():
                        display_task_in_stage(task)
                        st.markdown("---")
                
                # Архив выполненных задач
                if not completed_tasks.empty:
                    with st.expander(f"📁 Архив выполненных задач ({len(completed_tasks)})", expanded=False):
                        for _, task in completed_tasks.iterrows():
                            display_task_in_stage(task, is_completed=True)
                            st.markdown("---")
        
        st.markdown("---")