import streamlit as st
from database import Database
from datetime import datetime, date

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

db = Database()

st.title("Мои задачи")

if 'expanded_comments' not in st.session_state:
    st.session_state['expanded_comments'] = {}

if 'completing_task' not in st.session_state:
    st.session_state['completing_task'] = None

def display_comments(task_id):
    comments_df = db.get_task_comments(task_id)
    
    if not comments_df.empty:
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
                        if st.button("🗑️", key=f"delete_comment_{comment['comment_id']}"):
                            if db.delete_comment(comment['comment_id'], st.session_state['user_id']):
                                st.success("Комментарий удален")
                                st.rerun()

def display_task(task, is_completed=False):
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            if not is_completed:
                if st.session_state.get('completing_task') == task['task_id']:
                    st.write("⏳")
                else:
                    if st.button("✅", key=f"start_complete_{task['task_id']}", help="Завершить задачу"):
                        st.session_state['completing_task'] = task['task_id']
                        st.rerun()
            else:
                st.write("✓")
        
        with col2:
            if is_completed:
                st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", unsafe_allow_html=True)
            else:
                st.write(f"**{task['task_name']}**")
            
            st.caption(f"Проект: {task['project_name']} → Этап: {task['stage_name']}")
            
            if task.get('planned_hours'):
                st.caption(f"⏱️ Плановые часы: {task['planned_hours']} ч")
            
            comments_count = len(db.get_task_comments(task['task_id']))
            if comments_count > 0:
                st.caption(f"💬 {comments_count} комментариев")
        
        with col3:
            if task['date_end']:
                deadline_date = datetime.strptime(task['date_end'], '%Y-%m-%d').date()
                today = date.today()
                
                if is_completed:
                    if task.get('actual_hours'):
                        st.success(f"✅ Выполнено ({task['actual_hours']} ч)")
                    else:
                        st.success("✅ Выполнено")
                elif deadline_date < today:
                    st.error(f"❌ Просрочено ({task['date_end']})")
                else:
                    days_left = (deadline_date - today).days
                    st.warning(f"{task['date_end']} ({days_left} дн.)")
        
        with col4:
            comments_expanded = st.session_state['expanded_comments'].get(task['task_id'], False)
            if st.button("💬", key=f"toggle_comments_{task['task_id']}"):
                st.session_state['expanded_comments'][task['task_id']] = not comments_expanded
                st.rerun()
        
        # Форма завершения задачи
        if not is_completed and st.session_state.get('completing_task') == task['task_id']:
            with st.form(key=f"complete_task_form_{task['task_id']}"):
                st.subheader("Завершение задачи")
                
                st.info(f"Задача: **{task['task_name']}**")
                if task.get('planned_hours'):
                    st.info(f"Плановые часы: **{task['planned_hours']} ч**")
                
                # ИСПРАВЛЕНА ОШИБКА: все типы должны быть float
                actual_hours = st.number_input(
                    "Фактически затраченные часы:",
                    min_value=0.0,  # исправлено с 0
                    max_value=200.0,  # исправлено с 200
                    value=float(task.get('planned_hours', 4.0)),  # исправлено - приведение к float
                    step=0.5,
                    help="Укажите реальное количество часов, потраченных на задачу",
                    key=f"actual_hours_{task['task_id']}"
                )
                
                col_submit, col_cancel = st.columns(2)
                with col_submit:
                    submit = st.form_submit_button("✅ Завершить задачу")
                with col_cancel:
                    cancel = st.form_submit_button("❌ Отмена")
                
                if submit:
                    if actual_hours > 0:
                        db.complete_task(task['task_id'], float(actual_hours))
                        st.success(f"Задача завершена! Затрачено: {actual_hours} ч")
                        st.session_state['completing_task'] = None
                        st.rerun()
                    else:
                        st.error("Пожалуйста, укажите количество часов (больше 0)")
                
                if cancel:
                    st.session_state['completing_task'] = None
                    st.rerun()
        
        # Комментарии
        if st.session_state['expanded_comments'].get(task['task_id'], False):
            display_comments(task['task_id'])
            
            with st.form(key=f"add_comment_form_{task['task_id']}", clear_on_submit=True):
                new_comment = st.text_area("Добавить комментарий:", key=f"new_comment_{task['task_id']}")
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
                        st.session_state['expanded_comments'][task['task_id']] = False
                        st.rerun()

def display_archived_task(task):
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            if st.checkbox("", value=True, key=f"archive_{task['task_id']}", 
                          on_change=lambda t=task: return_task_from_archive(t)):
                pass
        
        with col2:
            st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", unsafe_allow_html=True)
            
            if task['responsible_name']:
                st.caption(f"Ответственный: {task['responsible_name']}")
            
            if task.get('actual_hours'):
                st.caption(f"⏱️ Фактические часы: {task['actual_hours']} ч")
            
            st.caption(f"Проект: {task['project_name']} → Этап: {task['stage_name']}")
            
            comments_count = len(db.get_task_comments(task['task_id']))
            if comments_count > 0:
                st.caption(f"💬 {comments_count} комментариев")
        
        with col3:
            if task['date_end']:
                st.info(f"Выполнено: {task['date_end']}")
        
        with col4:
            comments_expanded = st.session_state['expanded_comments'].get(task['task_id'], False)
            if st.button("💬", key=f"toggle_comments_archive_{task['task_id']}"):
                st.session_state['expanded_comments'][task['task_id']] = not comments_expanded
                st.rerun()
        
        if st.session_state['expanded_comments'].get(task['task_id'], False):
            display_comments(task['task_id'])
            
            with st.form(key=f"add_comment_form_archive_{task['task_id']}", clear_on_submit=True):
                new_comment = st.text_area("Добавить комментарий:", key=f"new_comment_archive_{task['task_id']}")
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("Добавить комментарий"):
                        if new_comment.strip():
                            db.add_comment_to_task(task['task_id'], st.session_state['user_id'], new_comment.strip())
                            st.success("Комментарий добавлен")
                            st.rerun()
                with col_cancel:
                    if st.form_submit_button("Отмена"):
                        st.session_state['expanded_comments'][task['task_id']] = False
                        st.rerun()

def return_task_from_archive(task):
    db.complete_task(task['task_id'], actual_hours=0)  # Сбрасываем часы при возврате
    st.rerun()

# Основной код
tasks_df = db.get_user_tasks(st.session_state['user_id'])

if tasks_df.empty:
    st.info("У вас пока нет задач")
else:
    completed_tasks = tasks_df[tasks_df['status'] == 'completed']
    active_tasks = tasks_df[tasks_df['status'] != 'completed']
    
    if not active_tasks.empty:
        st.subheader("Активные задачи")
        for _, task in active_tasks.iterrows():
            display_task(task)
    
    if not completed_tasks.empty:
        with st.expander(f"📁 Архив выполненных задач ({len(completed_tasks)})", expanded=False):
            st.write("Выполненные задачи (снимите галочку чтобы вернуть в активные):")
            for _, task in completed_tasks.iterrows():
                display_archived_task(task)