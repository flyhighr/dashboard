import streamlit as st
from db import get_db_connection
from datetime import datetime, timedelta
import random

def todo_section():
    st.title("To-Do List")
    user_id = st.session_state['user']['id']
    is_admin = st.session_state['user']['is_admin']
    conn = get_db_connection()

    tabs = ["Current Work", "Dropped Work", "Other Users' Tasks"]
    if is_admin:
        tabs.append("Admin Panel")
    
    selected_tab = st.selectbox("Select Tab", tabs)

    if selected_tab == "Current Work":
        show_current_work(user_id, conn)

    elif selected_tab == "Dropped Work":
        show_dropped_work(user_id, conn)

    elif selected_tab == "Other Users' Tasks":
        show_other_users_tasks(conn)

    elif selected_tab == "Admin Panel" and is_admin:
        admin_panel(conn)

    conn.close()

def show_current_work(user_id, conn):
    st.subheader("Your Current Tasks")
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? AND is_done = 0', (user_id,)).fetchall()
    for task in tasks:
        deadline = task['deadline']
        remaining_days = (datetime.strptime(deadline, '%Y-%m-%d') - datetime.now()).days

        with st.expander(f"Deadline: {deadline} ({remaining_days} days left)"):
            st.write(f"Task: {task['task']}")
            if st.button(f"Complete Task {task['id']}", key=f"complete_{task['id']}"):
                complete_task(task['id'])
                st.rerun()

            # Reminders
            if remaining_days == 1:
                st.warning("Reminder: Only 1 day left to complete this task!")

    st.subheader("Past Tasks")
    past_tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? AND is_done = 1', (user_id,)).fetchall()
    for task in past_tasks:
        st.write(f"{task['task']} - Completed on: {task['deadline']}")

def show_dropped_work(user_id, conn):
    st.subheader("Dropped Tasks")
    tasks = conn.execute('SELECT * FROM tasks WHERE is_global = 1 AND user_id IS NULL').fetchall()
    for task in tasks:
        st.write(f"{task['task']} - Task ID: {task['task_id']}")
        if st.button(f"Pick Up Task {task['id']}", key=f"pickup_{task['id']}"):
            assign_task_to_user(task['id'], user_id)
            st.success("Task assigned to you. Complete it within 7 days.")
            st.rerun()

def show_other_users_tasks(conn):
    st.subheader("Other Users' Tasks")
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id IS NOT NULL').fetchall()
    for task in tasks:
        user = conn.execute('SELECT name FROM users WHERE id = ?', (task['user_id'],)).fetchone()
        if user:
            st.write(f"{task['task']} - Assigned to: {user['name']} - Deadline: {task['deadline']}")
        else:
            st.write(f"{task['task']} - Assigned to: [User not found] - Deadline: {task['deadline']}")

def admin_panel(conn):
    st.subheader("Admin Panel - Create and Manage Tasks")

    # Create new task
    with st.form(key='create_task'):
        task = st.text_input("New Task")
        user_names = get_all_users(conn)
        assigned_user_name = st.selectbox("Assign to User", list(user_names.values()))
        assigned_user_id = [k for k, v in user_names.items() if v == assigned_user_name][0]
        deadline = st.date_input("Deadline")
        is_global = st.checkbox("Dump in Dropped Work Tab")
        submit_button = st.form_submit_button(label='Create Task')

        if submit_button and task:
            task_id = random.randint(100000, 999999)
            user_id = None if is_global else assigned_user_id
            add_task(user_id, task, is_global, deadline, task_id)
            st.success(f"Task created with ID {task_id}!")
            st.rerun()

    # View tasks, move to dropped work, and delete tasks
    st.subheader("Manage Current Tasks")
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id IS NOT NULL AND is_done = 0').fetchall()
    for task in tasks:
        user = conn.execute('SELECT name FROM users WHERE id = ?', (task['user_id'],)).fetchone()
        if user:
            st.write(f"{task['task']} - Assigned to: {user['name']} - Deadline: {task['deadline']}")
        else:
            st.write(f"{task['task']} - Assigned to: [User not found] - Deadline: {task['deadline']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Move to Dropped Work {task['id']}", key=f"move_{task['id']}"):
                move_task_to_dropped(task['id'])
                st.success("Task moved to Dropped Work!")
                st.rerun()

        with col2:
            if st.button(f"Delete Task {task['id']}", key=f"delete_{task['id']}"):
                delete_task(task['id'])
                st.success("Task deleted!")
                st.rerun()

def add_task(user_id, task, is_global, deadline, task_id):
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (user_id, task, is_global, deadline, task_id) VALUES (?, ?, ?, ?, ?)', 
                 (user_id, task, int(is_global), deadline, task_id))
    conn.commit()
    conn.close()

def complete_task(task_id):
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET is_done = 1 WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def assign_task_to_user(task_id, user_id):
    conn = get_db_connection()
    deadline = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    conn.execute('UPDATE tasks SET user_id = ?, deadline = ? WHERE id = ?', (user_id, deadline, task_id))
    conn.commit()
    conn.close()

def move_task_to_dropped(task_id):
    conn = get_db_connection()
    conn.execute('UPDATE tasks SET user_id = NULL, is_global = 1 WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def get_all_users(conn):
    users = conn.execute('SELECT id, name FROM users').fetchall()
    return {user['id']: user['name'] for user in users}