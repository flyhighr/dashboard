import sqlite3 , string , random
import streamlit as st
from werkzeug.security import generate_password_hash
from auth import get_db_connection, logout

def generate_token(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))



def admin_panel():
    conn = get_db_connection()
    if not st.session_state['user']['is_admin']:
        st.error("You do not have access to this section.")
        return

    st.title("Admin Panel")
    tab1, tab2, tab3,tab4 = st.tabs(["Create New Chat", "Manage Users", "Manage Tokens", "Online Users"])
    # Create New Chat
    with tab1:
        st.header("Create New Chat")
        new_chat_name = st.text_input("Chat Name", key="new_chat_name")

        if st.button("Create Chat", key="create_chat_button"):
            if new_chat_name:
                conn.execute('INSERT INTO chats (name, created_by) VALUES (?, ?)', (new_chat_name, st.session_state['user']['id']))
                conn.commit()
                st.success("Chat created!")
            else:
                st.error("Chat name cannot be empty.")

    # Manage Users
    with tab2:
        st.header("Manage Users")
        users = conn.execute('SELECT * FROM users').fetchall()

        for user in users:
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 2])
            with col1:
                st.write(f"**{user['username']}**")
            with col2:
                st.write("Admin" if user['is_admin'] else "User")
            with col3:
                if user['is_original_admin'] == 0:  # Only allow deletion if not original admin
                    if st.button(f"Delete User", key=f"delete_user_{user['id']}"):
                        conn.execute('DELETE FROM users WHERE id = ?', (user['id'],))
                        conn.commit()
                        st.success(f"User {user['username']} deleted.")
                        st.rerun()
                else:
                    st.write("Cannot delete original admin")
            with col4:
                if user['is_admin'] == 0:  # Only allow promoting if not already an admin
                    if st.button(f"Make Admin", key=f"make_admin_{user['id']}"):
                        conn.execute('UPDATE users SET is_admin = 1 WHERE id = ?', (user['id'],))
                        conn.commit()
                        st.success(f"User {user['username']} is now an admin.")
                        st.rerun()
                    
                else:
                    st.write("Already an admin")
            with col5:
                if user['is_admin'] == 1 and user['is_original_admin'] == 0:  # Only allow demoting if not original admin
                    if st.button(f"Remove Admin", key=f"remove_admin_{user['id']}"):
                        conn.execute('UPDATE users SET is_admin = 0 WHERE id = ?', (user['id'],))
                        conn.commit()
                        st.success(f"User {user['username']} is no longer an admin.")
                        st.rerun()
                      
                else:
                    st.write("Cannot remove original admin status")
            with col6:
                reset_clicked = st.button(f"Reset Password", key=f"reset_password_{user['id']}")
                if reset_clicked:
                    new_password = st.text_input(f"Enter new password for {user['username']}", type="password", key=f"new_password_{user['id']}")
                    update_clicked = st.button(f"Update Password", key=f"update_password_{user['id']}")
                    if update_clicked and new_password:
                        conn.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(new_password), user['id']))
                        conn.commit()
                        st.success(f"Password for user {user['username']} updated.")
    with tab3:
    # Manage Tokens
        st.header("Manage Registration Tokens")
        token_action = st.radio("Select Action", ["Generate New Token", "View Tokens", "Delete Token"])

        if token_action == "Generate New Token":
            if st.button("Generate Token"):
                token = generate_token()
                conn.execute('INSERT INTO tokens (token, created_by) VALUES (?, ?)', (token, st.session_state['user']['id']))
                conn.commit()
                st.success(f"Token generated: {token}")

        elif token_action == "View Tokens":
            tokens = conn.execute('SELECT * FROM tokens').fetchall()
            for token in tokens:
                st.write(f"Token: {token['token']}, Used: {'Yes' if token['is_used'] else 'No'}, Created By: {token['created_by']}")
                if not token['is_used']:
                    if st.button(f"Delete Token {token['token']}"):
                        conn.execute('DELETE FROM tokens WHERE token = ?', (token['token'],))
                        conn.commit()
                        st.success(f"Token {token['token']} deleted.")
                        st.rerun()
    with tab4:                
        st.subheader("Online Users")
        online_users = conn.execute('SELECT * FROM users WHERE is_online = 1').fetchall()
        if online_users:
            for user in online_users:
                st.write(f"**{user['username']}** (Online)")
        else:
            st.write("No users are currently online.")
   
        if st.button("Logout", key="logout_button"):
            logout()
            st.rerun()
    conn.close()



# Main function for the admin panel
def main():
    if 'user' in st.session_state and st.session_state['user']['is_admin']:
        admin_panel()
    else:
        st.error("You need to be an admin to access this page.")

if __name__ == "__main__":
    main()
