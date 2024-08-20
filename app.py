import streamlit as st

from prof import edit_profile, view_profiles
from notes import notes_main
from todo import todo_section
from group_chat import chat_section
from admin import admin_panel
from db import init_db


from auth import logout, register, login


def main():
    st.set_page_config(page_title="IRIS Dashboard", layout="wide")
   
    init_db()

    if 'user' not in st.session_state:
        st.sidebar.title("Welcome")
        st.sidebar.write("Please log in or register.")
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            login()
        
        with tab2:
            register()
    else:
        st.sidebar.title("Menu")
        menu_options = ["Profile", "Notes", "To-Do List", "Group Chats"]
        if st.session_state['user']['is_admin']:
            menu_options.append("Admin Panel")
        selected_menu = st.sidebar.selectbox("Navigate", menu_options)
        st.sidebar.markdown("---")
        if st.sidebar.button("Logout"):
            logout()
            st.rerun()
        
        if selected_menu == "Profile":
            edit_profile()
            view_profiles()
        elif selected_menu == "Notes":
            notes_main()
        elif selected_menu == "To-Do List":
            todo_section()
        elif selected_menu == "Group Chats":
            chat_section()
        elif selected_menu == "Admin Panel":
            admin_panel()

if __name__ == "__main__":
    main()