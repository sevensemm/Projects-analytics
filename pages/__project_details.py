import streamlit as st
from database import Database
from datetime import datetime, date

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if 'selected_project' not in st.session_state:
    st.error("Проект не выбран. Вернитесь в 'Мои проекты' и выберите проект.")
    st.stop()

db = Database()
project_id = st.session_state['selected_project']

if 'expanded_comments_project' not in st.session_state:
    st.session_state['expanded_comments_project'] = {}

def display_comments_in_project(task_id):
    comments_df = db.get_task_comments(task_id)
    
    if not comments_df.empty:
        st.markdown("---")
        st.write("**Комментарии:**")
        
        for _, comment in comments_df.iterrows():
            with st.container():
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.markdown(f"**{comment['author_name']}**")
                    st.caption(f"{comment['created_at'][:19]}")
                    st.write(comment['comment_text'])
                
                with col2:
                    if comment['user_id'] == st.session_state['user_id']:
                        if st.button("🗑️", key=f"delete_proj_comment_{comment['comment_id']}"):
                            if db.delete_comment(comment['comment_id'], st.session_state['user_id']):
                                st.success("Комментарий удален")
                                st.rerun()
                
                st.markdown("---")

def display_task_in_stage(task, is_completed=False):
    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
    
    with col1:
        if not is_completed:
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
            
        comments_count = len(db.get_task_comments(task['task_id']))
        if comments_count > 0:
            st.caption(f"💬 {comments_count} комментариев")
    
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
    
    with col4:
        comments_expanded = st.session_state['expanded_comments_project'].get(task['task_id'], False)
        
        if st.button("💬", key=f"toggle_proj_comments_{task['task_id']}"):
            st.session_state['expanded_comments_project'][task['task_id']] = not comments_expanded
            st.rerun()
    
    if st.session_state['expanded_comments_project'].get(task['task_id'], False):
        display_comments_in_project(task['task_id'])
        
        with st.form(key=f"add_proj_comment_form_{task['task_id']}", clear_on_submit=True):
            new_comment = st.text_area("Добавить комментарий:", 
                                     key=f"new_proj_comment_{task['task_id']}")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("Добавить комментарий"):
                    if new_comment.strip():
                        db.add_comment_to_task(task['task_id'], st.session_state['user_id'], new_comment.strip())
                        st.success("Комментарий добавлен")
                        st.rerun()
                    else:
                        st.error("Введите текст комментария")
            with col_cancel:
                if st.form_submit_button("Отмена"):
                    st.session_state['expanded_comments_project'][task['task_id']] = False
                    st.rerun()

def complete_task_in_stage(task):
    if task['user_id'] == st.session_state['user_id']:
        db.update_task_status(task['task_id'], 'completed')
        st.rerun()
    else:
        st.error("Вы не можете отмечать чужие задачи")

def create_task_form(stage_id):
    with st.form(f"create_task_form_{stage_id}", clear_on_submit=True):
        st.write("**Добавить задачу**")
        
        task_name = st.text_input("Название задачи")
        
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

st.title(f"Проект: {st.session_state.get('selected_project_name', f'ID {project_id}')}")

if st.button("← Назад к проектам"):
    if 'selected_project' in st.session_state:
        del st.session_state['selected_project']
    if 'selected_project_name' in st.session_state:
        del st.session_state['selected_project_name']
    st.switch_page("pages/01_projects.py")

st.markdown("---")

stages_df = db.get_project_stages(project_id)

if stages_df.empty:
    st.info("В проекте нет этапов")
    
    if st.session_state.get('is_admin'):
        st.write("**Чтобы добавить этапы, перейдите в раздел 'Администрирование: Проекты'**")
else:
    for _, stage in stages_df.iterrows():
        with st.expander(f"📋 Этап: {stage['stage_name']}", expanded=False):
            # Блок для администратора: настройка стоимости этапа и создание задач
            if st.session_state.get('is_admin'):
                # Настройка стоимости этапа
                st.write("**Настройка стоимости этапа:**")
                current_cost = stage.get('stage_cost', 0)
                
                col_cost1, col_cost2 = st.columns([3, 1])
                with col_cost1:
                    new_cost = st.number_input(
                        "Стоимость этапа (руб.):",
                        min_value=0.0,
                        value=float(current_cost),
                        step=1000.0,
                        key=f"stage_cost_{stage['stage_id']}"
                    )
                with col_cost2:
                    if st.button("💾 Обновить", key=f"update_cost_{stage['stage_id']}"):
                        db.update_stage_cost(stage['stage_id'], new_cost)
                        st.success(f"Стоимость этапа обновлена: {new_cost} руб.")
                        st.rerun()
                
                st.markdown("---")
                
                # Создание задачи
                create_task_form(stage['stage_id'])
                st.markdown("---")
            
            # Получаем задачи этапа
            if st.session_state.get('is_admin'):
                tasks_df = db.get_all_stage_tasks(stage['stage_id'])
            else:
                tasks_df = db.get_stage_tasks(stage['stage_id'], current_user_id=st.session_state['user_id'])
            
            if tasks_df.empty:
                st.info("В этапе нет задач")
            else:
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