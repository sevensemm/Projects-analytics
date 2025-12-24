import streamlit as st
from database import Database
from datetime import datetime, date

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

db = Database()

st.title("Мои задачи")

# Функция отображения активной задачи
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
            # Кнопка для комментария
            if st.button("💬", key=f"comment_{task['task_id']}"):
                st.session_state[f"show_comment_{task['task_id']}"] = not st.session_state.get(f"show_comment_{task['task_id']}", False)
                st.rerun()
        
        # Поле для комментария (если нажали кнопку)
        if st.session_state.get(f"show_comment_{task['task_id']}"):
            comment = st.text_area("Комментарий:", key=f"input_comment_{task['task_id']}")
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Сохранить", key=f"save_{task['task_id']}"):
                    if comment:
                        db.add_comment_to_task(task['task_id'], st.session_state['user_id'], comment)
                        st.success("Комментарий добавлен")
                        del st.session_state[f"show_comment_{task['task_id']}"]
                        st.rerun()
            with col_cancel:
                if st.button("Отмена", key=f"cancel_{task['task_id']}"):
                    del st.session_state[f"show_comment_{task['task_id']}"]
                    st.rerun()
        
        st.markdown("---")

def display_archived_task(task):
    """Отображение задачи в архиве"""
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
    
    with col3:
        if task['date_end']:
            st.info(f"Выполнено: {task['date_end']}")
    
    with col4:
        if st.button("💬", key=f"comment_archive_{task['task_id']}"):
            st.session_state[f"show_comment_archive_{task['task_id']}"] = not st.session_state.get(f"show_comment_archive_{task['task_id']}", False)
            st.rerun()
    
    # Поле для комментария в архиве
    if st.session_state.get(f"show_comment_archive_{task['task_id']}"):
        comment = st.text_area("Комментарий:", key=f"input_comment_archive_{task['task_id']}")
        col_save, col_cancel = st.columns(2)
        with col_save:
            if st.button("Сохранить", key=f"save_archive_{task['task_id']}"):
                if comment:
                    db.add_comment_to_task(task['task_id'], st.session_state['user_id'], comment)
                    st.success("Комментарий добавлен")
                    del st.session_state[f"show_comment_archive_{task['task_id']}"]
                    st.rerun()
        with col_cancel:
            if st.button("Отмена", key=f"cancel_archive_{task['task_id']}"):
                del st.session_state[f"show_comment_archive_{task['task_id']}"]
                st.rerun()

def return_task_from_archive(task):
    """Вернуть задачу из архива"""
    db.update_task_status(task['task_id'], 'pending')
    st.rerun()

def complete_task(task):
    """Отметить задачу как выполненную"""
    db.update_task_status(task['task_id'], 'completed')
    st.rerun()

# Получаем ТОЛЬКО СВОИ задачи пользователя
tasks_df = db.get_user_tasks(st.session_state['user_id'])

if tasks_df.empty:
    st.info("У вас пока нет задач")
else:
    # Разделяем выполненные и активные
    completed_tasks = tasks_df[tasks_df['status'] == 'completed']
    active_tasks = tasks_df[tasks_df['status'] != 'completed']
    
    # Активные задачи
    if not active_tasks.empty:
        st.subheader("Активные задачи")
        for _, task in active_tasks.iterrows():
            display_task(task)
    
    # Архив выполненных задач
    if not completed_tasks.empty:
        with st.expander(f"📁 Архив выполненных задач ({len(completed_tasks)})", expanded=False):
            st.write("Выполненные задачи (снимите галочку чтобы вернуть в активные):")
            for _, task in completed_tasks.iterrows():
                display_archived_task(task)
                st.markdown("---")