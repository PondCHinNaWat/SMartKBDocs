from dotenv import dotenv_values
import streamlit as st
import os
from  kb_app import chat_doc_kb
from kb_meta_data_db import authenticate_user

# Initialize session state for login
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Login Form
if not st.session_state.authenticated:
    # Display login form
    with st.form(key='login_form'):
        st.write("Please log in to access the chatbot:")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type='password')
        submit_button = st.form_submit_button("Login")

    # Check login credentials
    if submit_button:
        if authenticate_user(username_input, password_input):
            st.session_state.authenticated = True
            st.success("Login successful!")
            chat_doc_kb()

        else:
            st.error("Invalid username or password.")
else:
    # Invoke the main chatbot function
    chat_doc_kb()

    # Provide a logout button
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()
