import streamlit as st
import sqlite3
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def format_timestamp(timestamp):
    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    return dt.strftime('%d %b %H:%M')  # Day Month Time

def chat_section():
    st.title("Group Chats")
    conn = get_db_connection()

    # Fetch chats
    chats = conn.execute('SELECT * FROM chats').fetchall()

    if not chats:
        st.write("No chats available.")
        conn.close()
        return

    # Display chat options
    chat_options = [chat['id'] for chat in chats]
    chat_names = {chat['id']: chat['name'] for chat in chats}

    selected_chat_id = st.selectbox(
        "Select Chat",
        chat_options,
        format_func=lambda chat_id: chat_names.get(chat_id, "Unknown Chat")
    )

    if selected_chat_id:
        st.write(f"Chat: {chat_names.get(selected_chat_id, 'Unknown Chat')}")

        # Pagination variables
        if 'message_offset' not in st.session_state:
            st.session_state.message_offset = 0
        if 'messages_per_page' not in st.session_state:
            st.session_state.messages_per_page = 10

        # Load messages
        messages_query = '''
            SELECT * FROM messages 
            WHERE chat_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ? OFFSET ?
        '''
        messages = conn.execute(messages_query, (selected_chat_id, st.session_state.messages_per_page, st.session_state.message_offset)).fetchall()

        if messages:
            for message in reversed(messages):
                user_id = message['user_id']
                timestamp = message['timestamp']
                msg_content = message['message']

                # Fetch user name for display
                user_name_query = 'SELECT name FROM users WHERE id = ?'
                user_name_row = conn.execute(user_name_query, (user_id,)).fetchone()
                user_name = user_name_row['name'] if user_name_row else 'Unknown User'

                st.write(f"{user_name} ({format_timestamp(timestamp)}): {msg_content}")
                

            # Load more button
            if len(messages) == st.session_state.messages_per_page:
                if st.button("Load More"):
                    st.session_state.message_offset += st.session_state.messages_per_page
                    st.rerun()

        else:
            st.write("No messages in this chat.")

        # Purge chat button (admin only)
        is_admin = st.session_state.get('user', {}).get('is_admin', 0)
        if is_admin:
            if st.button("Purge Chat"):
                conn.execute('DELETE FROM messages WHERE chat_id = ?', (selected_chat_id,))
                conn.commit()
                st.success("Chat purged successfully!")
                st.rerun()

        # Send a new message
        st.subheader("Send a New Message")
        new_message = st.text_area("Message", "")
        if st.button("Send"):
            if new_message:
                user_id = st.session_state.get('user', {}).get('id', None)
                if user_id:
                    conn.execute(
                        'INSERT INTO messages (chat_id, user_id, message) VALUES (?, ?, ?)',
                        (selected_chat_id, user_id, new_message)
                    )
                    conn.commit()
                    st.success("Message sent!")
                    st.rerun()
                else:
                    st.error("You need to be logged in to send a message.")
            else:
                st.error("Message cannot be empty.")

    conn.close()
