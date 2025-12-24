import streamlit as st
from database import Database

if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("Требуется авторизация")
    st.stop()

if not st.session_state.get('is_admin'):
    st.error("Недостаточно прав")
    st.stop()

db = Database()

st.title("Администрирование: Пользователи")

# Создание пользователя
st.subheader("Создать пользователя")
with st.form("create_user_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        login = st.text_input("Логин (уникальный)")
        full_name = st.text_input("Полное имя")
    
    with col2:
        password = st.text_input("Пароль", type="password")
        is_admin = st.checkbox("Администратор")
    
    if st.form_submit_button("Создать пользователя"):
        if login and full_name and password:
            # Проверка уникальности логина
            all_users = db.get_all_users()
            existing_logins = [u['login'] for _, u in all_users.iterrows()]
            
            if login in existing_logins:
                st.error(f"Логин '{login}' уже занят")
            else:
                user_id = db.create_user(login, full_name, password, is_admin)
                role = "администратор" if is_admin else "пользователь"
                st.success(f"Пользователь '{full_name}' создан как {role} (логин: {login})")
                st.rerun()
        else:
            st.error("Заполните все поля")

st.markdown("---")

# Список пользователей с кнопками редактирования
st.subheader("Все пользователи")

users_df = db.get_all_users()

if users_df.empty:
    st.info("Нет пользователей")
else:
    for _, user in users_df.iterrows():
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            st.write(f"**{user['full_name']}**")
            st.caption(f"Логин: {user['login']}")
            if user['is_admin']:
                st.success("Администратор")
            else:
                st.info("Пользователь")
        
        with col2:
            st.caption(f"ID: {user['user_id']}")
        
        with col3:
            # Кнопка редактирования
            if st.button("✏️ Изменить", key=f"edit_{user['user_id']}"):
                st.session_state['editing_user_id'] = user['user_id']
                st.session_state['editing_user_login'] = user['login']
                st.session_state['editing_user_full_name'] = user['full_name']
                st.session_state['editing_user_is_admin'] = bool(user['is_admin'])
                st.rerun()
        
        with col4:
            # Кнопка удаления
            if user['login'] != 'admin':
                if st.button("🗑️ Удалить", key=f"delete_{user['user_id']}"):
                    success = db.delete_user(user['user_id'])
                    if success:
                        st.success(f"Пользователь '{user['full_name']}' удален")
                        st.rerun()
                    else:
                        st.error("Ошибка при удалении")
            else:
                st.button("🗑️ Удалить", disabled=True, key=f"disabled_{user['user_id']}")
        
        st.markdown("---")
    
    # Форма редактирования (показывается после нажатия "Изменить")
    if 'editing_user_id' in st.session_state and st.session_state['editing_user_id']:
        st.markdown("---")
        st.subheader(f"Редактирование пользователя")
        
        with st.form("edit_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                edit_login = st.text_input("Логин", 
                                         value=st.session_state['editing_user_login'])
                edit_full_name = st.text_input("Полное имя",
                                             value=st.session_state['editing_user_full_name'])
            
            with col2:
                edit_password = st.text_input("Новый пароль (оставьте пустым чтобы не менять)", 
                                            type="password")
                edit_is_admin = st.checkbox("Администратор",
                                          value=st.session_state['editing_user_is_admin'])
            
            col_save, col_cancel = st.columns(2)
            
            with col_save:
                if st.form_submit_button("💾 Сохранить изменения"):
                    if edit_login and edit_full_name:
                        # Проверяем уникальность логина (кроме текущего пользователя)
                        all_users = db.get_all_users()
                        other_users = [u for _, u in all_users.iterrows() 
                                     if u['user_id'] != st.session_state['editing_user_id']]
                        existing_logins = [u['login'] for u in other_users]
                        
                        if edit_login in existing_logins:
                            st.error(f"Логин '{edit_login}' уже занят другим пользователем")
                        else:
                            # Обновляем пользователя в базе данных
                            conn = db.get_connection()
                            cursor = conn.cursor()
                            
                            if edit_password:
                                # Обновляем с паролем
                                cursor.execute('''
                                    UPDATE Users 
                                    SET login = ?, full_name = ?, password = ?, is_admin = ?
                                    WHERE user_id = ?
                                ''', (edit_login, edit_full_name, edit_password, 
                                      1 if edit_is_admin else 0, 
                                      st.session_state['editing_user_id']))
                            else:
                                # Обновляем без пароля
                                cursor.execute('''
                                    UPDATE Users 
                                    SET login = ?, full_name = ?, is_admin = ?
                                    WHERE user_id = ?
                                ''', (edit_login, edit_full_name, 
                                      1 if edit_is_admin else 0, 
                                      st.session_state['editing_user_id']))
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"Данные пользователя обновлены")
                            
                            # Очищаем состояние редактирования
                            del st.session_state['editing_user_id']
                            del st.session_state['editing_user_login']
                            del st.session_state['editing_user_full_name']
                            del st.session_state['editing_user_is_admin']
                            
                            st.rerun()
                    else:
                        st.error("Логин и полное имя обязательны")
            
            with col_cancel:
                if st.form_submit_button("❌ Отмена"):
                    # Очищаем состояние редактирования
                    del st.session_state['editing_user_id']
                    del st.session_state['editing_user_login']
                    del st.session_state['editing_user_full_name']
                    del st.session_state['editing_user_is_admin']
                    st.rerun()