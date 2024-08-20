import sqlite3 ,re
import streamlit as st
from werkzeug.security import generate_password_hash, check_password_hash

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# Create users table
def create_users_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            job_profile TEXT,
            github TEXT,
            discord TEXT,
            is_admin INTEGER DEFAULT 0,
            is_original_admin INTEGER DEFAULT 0,
            is_online INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

# Register user
def register_user(username, password, email, name, token):
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    is_admin = 1 if user_count == 0 else 0
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Validate token only if provided
    if token:
        token_row = conn.execute('SELECT * FROM tokens WHERE token = ? AND is_used = 0', (token,)).fetchone()
        if not token_row:
            st.error("Invalid or already used token.")
            conn.close()
            return
        conn.execute('UPDATE tokens SET is_used = 1 WHERE token = ?', (token,))
    else:
        st.error("No Token Provided.")
    try:
        conn.execute('INSERT INTO users (username, password, email, name, is_admin, is_original_admin) VALUES (?, ?, ?, ?, ?, ?)',
                     (username, hashed_password, email, name, is_admin, is_admin))
        conn.commit()
        st.success("Registration successful! Please log in.")
    except sqlite3.IntegrityError:
        st.error("User with this email or username already exists.")
    finally:
        conn.close()

def register_user_notoken(username, password, email, name):
    conn = get_db_connection()
    user_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    is_admin = 1 if user_count == 0 else 0
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Validate token only if provided
    
    
    try:
        conn.execute('INSERT INTO users (username, password, email, name, is_admin, is_original_admin) VALUES (?, ?, ?, ?, ?, ?)',
                     (username, hashed_password, email, name, is_admin, is_admin))
        conn.commit()
        st.success("Registration successful! Please log in.")
    except sqlite3.IntegrityError:
        st.error("User with this email or username already exists.")
    finally:
        conn.close()

# Update user status (online/offline)
def update_user_status(user_id, is_online):
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_online = ? WHERE id = ?', (is_online, user_id))
    conn.commit()
    conn.close()

# Login user
def login_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        st.session_state['user'] = dict(user)
        update_user_status(user['id'], 1)  # Mark user as online
        return True
    else:
        st.error("Invalid credentials.")
        return False

# Logout user
def logout():
    user_id = st.session_state.get('user', {}).get('id', None)
    if user_id:
        update_user_status(user_id, 0)  # Mark user as offline
    st.session_state.pop('user', None)
    st.success("Logged out successfully!")

def is_valid_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

def register():
    st.header("Register")
    with st.form("register_form"):
        conn = get_db_connection()
        if conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
            conn.close()
            username = st.text_input("Username")
            email = st.text_input("Email")
            name = st.text_input("Name")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit_button = st.form_submit_button("Register")
        
            if submit_button:
                if password == confirm_password:
                    # If no token is provided and the user count is zero, skip token validation
                    
                    register_user_notoken(username, password, email, name)
                    
                else:
                    st.error("A registration token is required.")
            else:
                st.error("Passwords do not match.")
        
        else:
            username = st.text_input("Username")
            email = st.text_input("Email")
            name = st.text_input("Name")
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            token = st.text_input("Registration Token")  # Token is optional for the first user
            submit_button = st.form_submit_button("Register")
        
            if submit_button:
            
                if password == confirm_password:
                    # If no token is provided and the user count is zero, skip token validation
                    conn = get_db_connection()
                    if token or (conn.execute('SELECT COUNT(*) FROM users').fetchone()[0] > 0):
                        register_user(username, password, email, name, token)
                        conn.close()
                    else:
                        st.error("A registration token is required.")
                else:
                    st.error("Passwords do not match.")

# Login page
def login():
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if login_user(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

# Home page
def home():
    st.title("Welcome")
    st.write(f"Hello, {st.session_state['user']['name']}!")
    if st.button("Logout"):
        logout()
        st.rerun()

# Main function
def main():
    create_users_table()
    
    st.sidebar.title("Navigation")
    if 'user' not in st.session_state:
        page = st.sidebar.radio("Go to", ["Login", "Register"])
    else:
        page = "Home"
        st.sidebar.text(f"Logged in as: {st.session_state['user']['name']}")
        if st.session_state['user']['is_admin']:
            st.sidebar.button("Admin Panel", on_click=lambda: st.session_state.update({"page": "Admin Panel"}))

    if page == "Login":
        login()
    elif page == "Register":
        register()
    elif page == "Home":
        home()

if __name__ == "__main__":
    main()
