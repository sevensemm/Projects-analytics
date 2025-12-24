import streamlit as st
from database import Database

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

st.title("Администратор: Управление пользователями")

# Инициализация состояния для редактирования
if 'edit_mode' not in st.session_state:
    st.session_state['edit_mode'] = False
    st.session_state['edit_user_id'] = None

# Создание нового пользователя
st.subheader("Создать нового пользователя")
with st.form("create_user_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        username = st.text_input("Логин (уникальный)", key="new_username")
        full_name = st.text_input("Полное имя", key="new_full_name")
    
    with col2:
        password = st.text_input("Пароль", type="password", key="new_password")
        is_admin = st.checkbox("Администратор", key="new_is_admin")
    
    if st.form_submit_button("Создать пользователя"):
        if username and full_name and password:
            # Проверяем уникальность логина
            existing_users = db.get_all_users()
            existing_usernames = [u['username'] for u in existing_users.to_dict('records')]
            
            if username in existing_usernames:
                st.error(f"Логин '{username}' уже занят")
            else:
                user_id = db.create_user(username, full_name, password, is_admin)
                role = "администратора" if is_admin else "пользователя"
                st.success(f"Пользователь '{full_name}' создан как {role} (ID: {user_id})")
                st.rerun()
        else:
            st.error("Заполните все поля")

st.markdown("---")

# Редактирование пользователя
if st.session_state['edit_mode'] and st.session_state['edit_user_id']:
    st.subheader("Редактирование пользователя")
    
    user = db.get_user_by_id(st.session_state['edit_user_id'])
    
    if user:
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_username = st.text_input("Логин", value=user['username'], key="edit_username")
                edit_full_name = st.text_input("Полное имя", value=user['full_name'], key="edit_full_name")
            
            with col2:
                # Для безопасности не показываем текущий пароль
                new_password = st.text_input("Новый пароль (оставьте пустым чтобы не менять)", 
                                           type="password", key="edit_password")
                edit_is_admin = st.checkbox("Администратор", 
                                          value=bool(user['is_admin']), 
                                          key="edit_is_admin")
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.form_submit_button("Сохранить изменения"):
                    # Если указан новый пароль - обновляем
                    if new_password:
                        # Здесь нужно добавить метод для обновления пароля
                        st.info("Обновление пароля - функция в разработке")
                    
                    # Обновляем остальные данные
                    success = db.update_user(
                        user['user_id'], 
                        edit_username, 
                        edit_full_name, 
                        edit_is_admin
                    )
                    
                    if success:
                        st.success(f"Данные пользователя '{edit_full_name}' обновлены")
                        st.session_state['edit_mode'] = False
                        st.session_state['edit_user_id'] = None
                        st.rerun()
                    else:
                        st.error("Ошибка при обновлении данных")
            
            with col_cancel:
                if st.form_submit_button("Отмена"):
                    st.session_state['edit_mode'] = False
                    st.session_state['edit_user_id'] = None
                    st.rerun()
    else:
        st.error("Пользователь не найден")
        st.session_state['edit_mode'] = False
        st.session_state['edit_user_id'] = None

st.markdown("---")

# Список существующих пользователей
st.subheader("Существующие пользователи")

users_df = db.get_all_users()

if users_df.empty:
    st.info("Нет пользователей")
else:
    for _, user in users_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{user['full_name']}**")
            st.caption(f"Логин: {user['username']}")
            if user['is_admin']:
                st.success("Администратор")
            else:
                st.info("Пользователь")
        
        with col2:
            if st.button("Редактировать", key=f"edit_{user['user_id']}"):
                st.session_state['edit_mode'] = True
                st.session_state['edit_user_id'] = user['user_id']
                st.rerun()
        
        with col3:
            # Не даем удалить себя или admin
            if user['username'] not in [st.session_state.get('username'), 'admin']:
                if st.button("Удалить", key=f"delete_{user['user_id']}"):
                    success = db.delete_user(user['user_id'])
                    if success:
                        st.success(f"Пользователь '{user['full_name']}' удален")
                        st.rerun()
                    else:
                        st.error("Ошибка при удалении пользователя")
            else:
                st.button("Удалить", disabled=True, key=f"disabled_delete_{user['user_id']}")
        
        st.markdown("---")