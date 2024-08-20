import sqlite3
import streamlit as st

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def edit_profile():
    st.title("Edit Profile")
    user = st.session_state['user']

    # Input fields with updated labels
    name = st.text_input("Name", value=user['name'], key="profile_name")
    job_profile = st.text_input("Job Profile", value=user.get('job_profile', ''), key="profile_job")
    github = st.text_input("GitHub", value=user.get('github', ''), key="profile_github")
    discord = st.text_input("Discord", value=user.get('discord', ''), key="profile_discord")

    if st.button("Save Profile", key="save_profile_button"):
        conn = get_db_connection()
        conn.execute('UPDATE users SET name = ?, job_profile = ?, github = ?, discord = ? WHERE id = ?',
                     (name, job_profile, github, discord, user['id']))
        conn.commit()
        conn.close()
        st.success("Profile updated!")
        

def view_profiles():
    st.title("View Profiles")
    conn = get_db_connection()
    profiles = conn.execute('SELECT * FROM users').fetchall()
    conn.close()

    # Display profiles in a more structured layout
    for profile in profiles:
        st.subheader(profile['name'])
        
        # Displaying profile information in a cleaner format
        st.write(f"**Job Profile:** {profile['job_profile']}")
        st.write(f"**GitHub:** [@{profile['github']}]({profile['github']})" if profile['github'] else "GitHub: Not provided")
        st.write(f"**Discord:** {profile['discord']}" if profile['discord'] else "Discord: Not provided")
        
        st.markdown("---")
