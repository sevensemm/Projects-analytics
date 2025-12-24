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

def display_task(task, db_instance, is_completed=False):
    """Отображение одной задачи"""
    with st.container():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            # Чекбокс для выполнения
            if not is_completed:
                if st.checkbox(
                    "",
                    value=False,
                    key=f"complete_{task['task_id']}",
                    on_change=lambda t=task: complete_task(t, db_instance)
                ):
                    pass
            else:
                st.write("✓")
        
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
            # Кнопка для комментария
            if st.button("Комментарий", key=f"comment_{task['task_id']}"):
                st.session_state[f"show_comment_{task['task_id']}"] = True
                st.rerun()
        
        # Поле для комментария
        if st.session_state.get(f"show_comment_{task['task_id']}"):
            comment = st.text_area("Текст комментария:", key=f"input_comment_{task['task_id']}")
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("Сохранить", key=f"save_{task['task_id']}"):
                    if comment:
                        db_instance.add_comment_to_task(task['task_id'], st.session_state['user_id'], comment)
                        st.success("Комментарий добавлен")
                        del st.session_state[f"show_comment_{task['task_id']}"]
                        st.rerun()
            with col_cancel:
                if st.button("Отмена", key=f"cancel_{task['task_id']}"):
                    del st.session_state[f"show_comment_{task['task_id']}"]
                    st.rerun()
        
        st.markdown("---")

def complete_task(task, db_instance):
    """Отметить задачу как выполненную"""
    db_instance.update_task_status(task['task_id'], 'completed')
    st.rerun()