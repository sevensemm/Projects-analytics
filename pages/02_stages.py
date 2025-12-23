import streamlit as st
from database import Database
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Задачи", layout="wide")

# Проверка аутентификации
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Пожалуйста, войдите в систему")
    st.stop()

if 'selected_stage' not in st.session_state:
    st.error("Этап не выбран")
    st.stop()

db = Database()
stage_id = st.session_state['selected_stage']

# Получаем информацию об этапе
stage = db.get_stage_details(stage_id)
if stage:
    st.title(f"✅ Задачи этапа: {stage['stages_name']}")
    st.caption(f"Проект: {stage['project_name']}")

col1, col2 = st.columns([3, 1])

with col1:
    # Показываем задачи
    tasks_df = db.get_stage_tasks(stage_id)
    
    if tasks_df.empty:
        st.info("В этом этапе пока нет задач")
    else:
        for _, task in tasks_df.iterrows():
            with st.container():
                st.markdown("---")
                col_task = st.columns([1, 4, 2, 2])
                
                with col_task[0]:
                    status = st.checkbox(
                        "", 
                        value=(task['status'] == 'completed'),
                        key=f"task_{task['task_id']}"
                    )
                
                with col_task[1]:
                    st.write(f"**{task['tasks_name']}**")
                    if task['assigned_to_name']:
                        st.caption(f"👤 {task['assigned_to_name']}")
                
                with col_task[2]:
                    st.caption(f"Начало: {task['date_start']}")
                    st.caption(f"Конец: {task['date_end']}")
                
                with col_task[3]:
                    # Кнопка для добавления комментария
                    if st.button("💬", key=f"comment_{task['task_id']}"):
                        st.session_state[f"show_comment_{task['task_id']}"] = True
                
                # Поле для комментария
                if st.session_state.get(f"show_comment_{task['task_id']}"):
                    comment = st.text_area("Комментарий:", key=f"input_comment_{task['task_id']}")
                    col_save = st.columns(2)
                    with col_save[0]:
                        if st.button("Сохранить", key=f"save_comment_{task['task_id']}"):
                            if comment:
                                db.add_comment_to_task(
                                    task['task_id'], 
                                    comment, 
                                    st.session_state['user_id']
                                )
                                st.success("Комментарий добавлен")
                                st.rerun()
                    with col_save[1]:
                        if st.button("Отмена", key=f"cancel_comment_{task['task_id']}"):
                            del st.session_state[f"show_comment_{task['task_id']}"]
                            st.rerun()

with col2:
    # Форма добавления новой задачи
    st.subheader("➕ Добавить задачу")
    
    with st.form("add_task_form"):
        task_name = st.text_input("Название задачи")
        
        # Получаем список пользователей для выбора
        users_df = db.get_all_users()
        user_options = {row['full_name']: row['user_id'] for _, row in users_df.iterrows()}
        selected_user = st.selectbox("Ответственный", list(user_options.keys()))
        
        date_start = st.date_input("Дата начала")
        date_end = st.date_input("Дата окончания")
        
        if st.form_submit_button("Добавить задачу"):
            if task_name and selected_user and date_start and date_end:
                user_id = user_options[selected_user]
                db.create_task(
                    stage_id, 
                    task_name, 
                    user_id, 
                    date_start.strftime('%Y-%m-%d'), 
                    date_end.strftime('%Y-%m-%d')
                )
                st.success("Задача добавлена!")
                st.rerun()
            else:
                st.error("Заполните все поля")

# Кнопка возврата
if st.button("⬅️ Назад к этапам"):
    del st.session_state['selected_stage']
    st.switch_page("pages/1_🏠_Проекты.py")