import streamlit as st
from database import Database
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Админ-панель", layout="wide")

# Проверка прав администратора
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав")
    st.stop()

db = Database()

st.title("Административная панель")

# Вкладки для админ-панели
tab1, tab2, tab3, tab4 = st.tabs([
    "Проекты", 
    "Пользователи", 
    "Назначения", 
    "Импорт"
])

# Вкладка 1: Проекты
with tab1:
    st.subheader("Управление проектами")
    
    # Создание нового проекта
    with st.form("create_project_form"):
        project_name = st.text_input("Название проекта")
        if st.form_submit_button("Создать проект"):
            if project_name:
                project_id = db.create_project(project_name)
                st.success(f"Проект '{project_name}' создан (ID: {project_id})")
                st.rerun()
            else:
                st.error("Введите название проекта")
    
    st.markdown("---")
    
    # Список проектов
    st.subheader("Существующие проекты")
    projects_df = db.get_all_projects()
    
    if not projects_df.empty:
        for _, project in projects_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{project['project_name']}**")
                st.caption(f"ID: {project['project_id']}")
            
            with col2:
                # Добавление этапа к проекту
                with st.form(f"add_stage_{project['project_id']}"):
                    stage_name = st.text_input("Название этапа", key=f"stage_name_{project['project_id']}")
                    if st.form_submit_button("Добавить этап"):
                        if stage_name:
                            stage_id = db.create_stage(project['project_id'], stage_name)
                            st.success(f"Этап '{stage_name}' добавлен")
                            st.rerun()
            
            with col3:
                if st.button("Удалить", key=f"del_{project['project_id']}"):
                    db.delete_project(project['project_id'])
                    st.success("Проект удален")
                    st.rerun()
            
            st.markdown("---")

# Вкладка 2: Пользователи
with tab2:
    st.subheader("Управление пользователями")
    
    # Создание нового пользователя
    with st.form("create_user_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            user_name = st.text_input("Имя")
        with col2:
            user_surname = st.text_input("Фамилия")
        with col3:
            password = st.text_input("Пароль", type="password")
        
        is_admin = st.checkbox("Администратор")
        
        if st.form_submit_button("Создать пользователя"):
            if user_name and user_surname and password:
                user_id = db.create_user(user_name, user_surname, password, is_admin)
                st.success(f"Пользователь создан (ID: {user_id})")
                st.rerun()
            else:
                st.error("Заполните все поля")
    
    st.markdown("---")
    
    # Список пользователей
    st.subheader("Все пользователи")
    users_df = db.get_all_users()
    
    if not users_df.empty:
        st.dataframe(users_df, use_container_width=True)
    else:
        st.info("Нет пользователей")

# Вкладка 3: Назначения
with tab3:
    st.subheader("Назначение пользователей на этапы")
    
    projects_df = db.get_all_projects()
    
    if not projects_df.empty:
        selected_project = st.selectbox(
            "Выберите проект", 
            projects_df['project_name'].tolist(),
            key="project_select"
        )
        
        project_id = projects_df[projects_df['project_name'] == selected_project].iloc[0]['project_id']
        stages_df = db.get_project_stages(project_id)
        
        if not stages_df.empty:
            selected_stage = st.selectbox(
                "Выберите этап", 
                stages_df['stage_name'].tolist(),
                key="stage_select"
            )
            
            stage_id = stages_df[stages_df['stage_name'] == selected_stage].iloc[0]['stage_id']
            
            # Получение всех пользователей
            users_df = db.get_all_users()
            
            if not users_df.empty:
                st.subheader("Назначить пользователей на этап")
                
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
                                db.assign_user_to_stage(stage_id, user['user_id'])
                                st.success(f"{user['full_name']} назначен на этап")
                            else:
                                # Здесь нужен метод для снятия назначения
                                st.info("Функция снятия назначения")
                            st.rerun()
                    
                    st.markdown("---")

# Вкладка 4: Импорт
with tab4:
    st.subheader("Импорт данных")
    
    uploaded_file = st.file_uploader("Выберите Excel файл", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("Предпросмотр данных:")
            st.dataframe(df.head(), use_container_width=True)
            
            if st.button("Импортировать данные"):
                # Здесь можно добавить логику импорта
                st.info("Функция импорта в разработке")
                
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {str(e)}")

# Кнопка возврата
if st.button("Назад в главное меню"):
    st.switch_page("app.py")