import streamlit as st
import sqlite3
import pickle
import requests
from bs4 import BeautifulSoup

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def save_note_with_files(user_id, note_title, content, files, is_global):
    conn = get_db_connection()
    serialized_files = pickle.dumps(files)
    conn.execute('INSERT INTO notes (user_id, title, content, files, is_global) VALUES (?, ?, ?, ?, ?)', 
                 (user_id, note_title, content, serialized_files, is_global))
    conn.commit()
    conn.close()

def update_note(note_id, title, content, files, is_global):
    conn = get_db_connection()
    serialized_files = pickle.dumps(files)
    conn.execute('UPDATE notes SET title = ?, content = ?, files = ?, is_global = ? WHERE id = ?',
                 (title, content, serialized_files, is_global, note_id))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

def pin_unpin(note_id, pin_status):
    conn = get_db_connection()
    conn.execute('UPDATE notes SET is_pinned = ? WHERE id = ?', (pin_status, note_id))
    conn.commit()
    conn.close()

def view_notes(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,)).fetchone()
    is_admin = user['is_admin'] if user else False
    notes = conn.execute('SELECT * FROM notes WHERE is_global = 1 OR user_id = ? ORDER BY is_pinned DESC, id DESC', (user_id,)).fetchall()
    conn.close()

    for note in notes:
        with st.expander(note['title'], expanded=True):
            st.write(note['content'])
            if note['files']:
                files = pickle.loads(note['files'])
                for i, file in enumerate(files):
                    st.download_button(label=f"Download File {i + 1}", data=file, key=f"download_file_{note['id']}_{i}")

            can_edit = note['user_id'] == user_id or is_admin
            can_delete = can_edit

            if can_edit:
                pin_status = "Unpin" if note['is_pinned'] else "Pin"
                if st.button(f"{pin_status} Note", key=f"{note['id']}_pin"):
                    new_status = 1 - note['is_pinned']
                    pin_unpin(note['id'], new_status)
                    st.success(f"Note {pin_status.lower()}ed successfully!")
                    st.rerun()

                edit_button = st.button(f"Edit {note['title']}", key=f"edit_{note['id']}")
                if edit_button:
                    st.session_state.edit_note_id = note['id']
                    st.session_state.edit_note_title = note['title']
                    st.session_state.edit_note_content = note['content']
                    st.session_state.edit_note_files = pickle.loads(note['files'])
                    st.session_state.edit_note_is_global = note['is_global']

            if can_delete:
                delete_button = st.button(f"Delete {note['title']}", key=f"delete_{note['id']}")
                if delete_button:
                    delete_note(note['id'])
                    st.success("Note deleted successfully!")
                    st.rerun()

    if 'edit_note_id' in st.session_state:
        st.write("## Edit Note")
        new_title = st.text_input("New Note Title", value=st.session_state.get('edit_note_title', ''), key="edit_note_title")
        new_content = st.text_area("New Note Content", value=st.session_state.get('edit_note_content', ''), key="edit_note_content")
        new_files = st.file_uploader("Upload new files", accept_multiple_files=True, key="edit_files")
        new_is_global = st.radio("Note Visibility", ("Local", "Global"), index=int(st.session_state.get('edit_note_is_global', 0)), key="edit_note_visibility")

        if st.button("Update Note", key="update_note_button"):
            if new_title and new_content:
                updated_files = [file.read() for file in new_files] if new_files else st.session_state.edit_note_files
                update_note(st.session_state.edit_note_id, new_title, new_content, updated_files, new_is_global == "Global")
                st.success("Note updated successfully!")
                
                del st.session_state.edit_note_id
                del st.session_state.edit_note_title
                del st.session_state.edit_note_content
                del st.session_state.edit_note_files
                del st.session_state.edit_note_is_global
                st.rerun()
            else:
                st.error("Both title and content are required to update a note.")

def create_note():
    st.write("## Create Note")
    user_id = st.session_state.get('user', {}).get('id', None)
    if user_id is None:
        st.error("You need to be logged in to create a note.")
        return

    note_title = st.text_input("Note Title", key="new_note_title")
    note_content = st.text_area("Note Content", key="new_note_content")
    note_type = st.radio("Note Visibility", ("Local", "Global"), key="new_note_visibility")
    uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True, key="new_note_files")

    if st.button("Save Note", key="save_note_button"):
        if note_title and note_content:
            files = [file.read() for file in uploaded_files]
            save_note_with_files(user_id, note_title, note_content, files, note_type == "Global")
            st.success("Note saved successfully!")
            st.rerun()
        else:
            st.error("Both title and content are required to save a note.")

def import_from_link():
    st.write("## Import Note from Link")
    url = st.text_input("Enter the URL of the page containing text", key="import_url")
    
    if st.button("Import Text", key="import_text_button"):
        if url:
            try:
                response = requests.get(url)
                response.raise_for_status()  # Check for HTTP errors
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text()

                st.session_state.import_note_content = text_content
                st.write("**Imported Text:**")
                st.write(text_content)

                # Option to save or edit the imported text
                option = st.radio("What would you like to do with the imported text?", ["Save as Note", "Edit", "Clear"])

                if option == "Save as Note":
                    note_title = st.text_input("Enter title for the new note", key="note_title")
                    if st.button("Save Imported Text", key="save_imported_text_button"):
                        if note_title:
                            user_id = st.session_state.get('user', {}).get('id', None)
                            if user_id:
                                save_note_with_files(user_id, note_title, text_content, [], is_global=False)
                                st.success("Note saved successfully!")
                        else:
                            st.error("Please enter a title for the note.")
                
                elif option == "Edit":
                    st.write("**Edit Imported Text:**")
                    edited_content = st.text_area("Edit the text", value=text_content, key="edit_text_area")
                    if st.button("Save Edited Text", key="save_edited_text_button"):
                        note_title = st.text_input("Enter title for the edited note", key="edited_note_title")
                        if note_title:
                            user_id = st.session_state.get('user', {}).get('id', None)
                            if user_id:
                                save_note_with_files(user_id, note_title, edited_content, [], is_global=False)
                                st.success("Note saved successfully!")
                        else:
                            st.error("Please enter a title for the note.")
                
                elif option == "Clear":
                    st.session_state.import_note_content = ""
                    st.write("Text cleared.")
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("URL cannot be empty.")

def notes_main():
    user_id = st.session_state.get('user', {}).get('id', None)
    is_admin = st.session_state.get('is_admin', False)
    tabs = st.tabs(["View Notes", "Create Note", "Import from Link"])

    with tabs[0]:
        view_notes(user_id)
        
    with tabs[1]:
        create_note()
        
    with tabs[2]:
        import_from_link()

if __name__ == "__main__":
    notes_main()
