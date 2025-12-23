import streamlit as st
from database import Database
from datetime import datetime, date

st.set_page_config(page_title="Задачи", layout="wide")

# Проверка авторизации
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if 'selected_stage' not in st.session_state:
    st.error("Этап не выбран")
    st.stop()

db = Database()
stage_id = st.session_state['selected_stage']

# Получение задач
tasks_df = db.get_stage_tasks(stage_id)

st.title("Задачи этапа")

if tasks_df.empty:
    st.info("Нет задач в этом этапе")
else:
    for _, task in tasks_df.iterrows():
        col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
        
        with col1:
            status = st.checkbox(
                "", 
                value=(task['status'] == 'completed'),
                key=f"status_{task['task_id']}",
                on_change=lambda t=task: db.update_task_status(
                    t['task_id'], 
                    'completed' if st.session_state[f"status_{t['task_id']}"] else 'pending'
                )
            )
        
        with col2:
            st.write(f"**{task['task_name']}**")
            if task['assigned_user_name']:
                st.caption(f"Ответственный: {task['assigned_user_name']}")
        
        with col3:
            st.caption(f"Срок: {task['date_end']}")
            if task['status'] == 'completed':
                st.success("Выполнено")
            elif datetime.strptime(task['date_end'], '%Y-%m-%d').date() < date.today():
                st.error("Просрочено")
            else:
                days_left = (datetime.strptime(task['date_end'], '%Y-%m-%d').date() - date.today()).days
                st.warning(f"Осталось дней: {days_left}")
        
        with col4:
            if st.button("Комментарий", key=f"comment_{task['task_id']}"):
                st.session_state[f"show_comment_{task['task_id']}"] = not st.session_state.get(f"show_comment_{task['task_id']}", False)
                st.rerun()
        
        # Поле для комментария
        if st.session_state.get(f"show_comment_{task['task_id']}"):
            comment = st.text_area("Добавить комментарий:", key=f"input_comment_{task['task_id']}")
            if st.button("Сохранить", key=f"save_comment_{task['task_id']}"):
                if comment:
                    # Здесь нужно добавить метод в Database для сохранения комментариев
                    st.success("Комментарий добавлен")
        
        st.markdown("---")

# Форма добавления новой задачи (только для администратора)
if st.session_state.get('is_admin'):
    st.subheader("Добавить задачу")
    
    with st.form("add_task_form"):
        users_df = db.get_all_users()
        user_options = {row['full_name']: row['user_id'] for _, row in users_df.iterrows()}
        
        task_name = st.text_input("Название задачи")
        selected_user = st.selectbox("Ответственный", list(user_options.keys()))
        date_end = st.date_input("Дата окончания", min_value=date.today())
        
        if st.form_submit_button("Добавить"):
            if task_name and selected_user:
                user_id = user_options[selected_user]
                db.create_task(stage_id, user_id, task_name, date_end.strftime('%Y-%m-%d'))
                st.success("Задача добавлена")
                st.rerun()
            else:
                st.error("Заполните все поля")

# Кнопка возврата
if st.button("Назад к этапам"):
    del st.session_state['selected_stage']
    st.switch_page("pages/01_projects.py")