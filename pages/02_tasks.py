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

def display_comments(task_id):
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
                        if st.button("🗑️", key=f"delete_comment_{comment['comment_id']}"):
                            if db.delete_comment(comment['comment_id'], st.session_state['user_id']):
                                st.success("Комментарий удален")
                                st.rerun()
                
                st.markdown("---")

def display_task(task, is_completed=False):
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            if not is_completed:
                if st.checkbox(
                    "",
                    value=False,
                    key=f"task_{task['task_id']}",
                    on_change=lambda t=task: complete_task(t)
                ):
                    pass
            else:
                st.write("✓")
        
        with col2:
            if is_completed:
                st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", 
                           unsafe_allow_html=True)
            else:
                st.write(f"**{task['task_name']}**")
            
            st.caption(f"Проект: {task['project_name']} → Этап: {task['stage_name']}")
            
            comments_count = len(db.get_task_comments(task['task_id']))
            if comments_count > 0:
                st.caption(f"💬 {comments_count} комментариев")
        
        with col3:
            if task['date_end']:
                deadline_date = datetime.strptime(task['date_end'], '%Y-%m-%d').date()
                today = date.today()
                
                if is_completed:
                    st.success("✅ Выполнено")
                elif deadline_date < today:
                    st.error(f"❌ Просрочено ({task['date_end']})")
                else:
                    days_left = (deadline_date - today).days
                    st.warning(f"{task['date_end']} ({days_left} {'день' if days_left == 1 else 'дня' if 2 <= days_left <= 4 else 'дней'})")
        
        with col4:
            comments_expanded = st.session_state['expanded_comments'].get(task['task_id'], False)
            
            if st.button("💬", key=f"toggle_comments_{task['task_id']}"):
                st.session_state['expanded_comments'][task['task_id']] = not comments_expanded
                st.rerun()
        
        if st.session_state['expanded_comments'].get(task['task_id'], False):
            display_comments(task['task_id'])
            
            with st.form(key=f"add_comment_form_{task['task_id']}", clear_on_submit=True):
                new_comment = st.text_area("Добавить комментарий:", 
                                         key=f"new_comment_{task['task_id']}")
                
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
        
        st.markdown("---")

def display_archived_task(task):
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            if st.checkbox(
                "",
                value=True,
                key=f"archive_{task['task_id']}",
                on_change=lambda t=task: return_task_from_archive(t)
            ):
                pass
        
        with col2:
            st.markdown(f"<span style='color: gray'><s>{task['task_name']}</s></span>", 
                       unsafe_allow_html=True)
            
            if task['responsible_name']:
                st.caption(f"Ответственный: {task['responsible_name']}")
            
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
                new_comment = st.text_area("Добавить комментарий:", 
                                         key=f"new_comment_archive_{task['task_id']}")
                
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
        
        st.markdown("---")

def return_task_from_archive(task):
    db.update_task_status(task['task_id'], 'pending')

def complete_task(task):
    db.update_task_status(task['task_id'], 'completed')

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