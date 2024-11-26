import streamlit as st
import pandas as pd 
import awswrangler as wr 
import psycopg2 
import os
from dotenv import load_dotenv
from streamlit_date_picker import date_range_picker, date_picker, PickerType
import datetime
import time
import kb_meta_data_db 

load_dotenv()


# Setting
def creativity_button():
    st.markdown("""
    <style>
        .custom-button {
            width: 100%; /* Make button width 100% of its container */
            height: 40px; /* Adjust height as needed */
            font-size: 14px; /* Adjust font size as needed */
        }
        .custom-col {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .st-emotion-cache-yk7at5.ef3psqc14 {
            white-space: nowrap;
            margin: 0 -5px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button('Accurate', key='temp_low', type='secondary' if st.session_state.temperature != float(os.getenv('TEMP_1')) else 'primary', help="Select factual mode"):
            st.session_state.temperature = float(os.getenv('TEMP_1'))
    with col2:
        if st.button('Balanced', key='temp_medium', type='secondary' if st.session_state.temperature !=  float(os.getenv('TEMP_2')) else 'primary', help="Select balanced mode"):
            st.session_state.temperature = float(os.getenv('TEMP_2'))
    with col3:
        if st.button('Creative', key='temp_high', type='secondary' if st.session_state.temperature !=  float(os.getenv('TEMP_3')) else 'primary', help="Select creative mode"):
            st.session_state.temperature =  float(os.getenv('TEMP_3'))

def token_button():
    st.markdown("""
    <style>
        .custom-button {
            width: 100%; /* Make button width 100% of its container */
            height: 40px; /* Adjust height as needed */
            font-size: 14px; /* Adjust font size as needed */
        }
        .custom-col {
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .st-emotion-cache-yk7at5.ef3psqc14 {
            white-space: nowrap;
            margin: 0 -5px;
        }
    </style>
    """, unsafe_allow_html=True)

    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button('Brief', key='tokens_short', type='secondary' if st.session_state.max_tokens != int(os.getenv('MAX_TOKEN_1')) else 'primary', help="Concise response"):
            st.session_state.max_tokens = int(os.getenv('MAX_TOKEN_1'))
    with col5:
        if st.button('Moderate', key='tokens_medium', type='secondary' if st.session_state.max_tokens != int(os.getenv('MAX_TOKEN_2')) else 'primary', help="Moderate response"):
            st.session_state.max_tokens = int(os.getenv('MAX_TOKEN_2'))
    with col6:
        if st.button('Detailed', key='tokens_long', type='secondary' if st.session_state.max_tokens != int(os.getenv('MAX_TOKEN_3')) else 'primary', help="Detailed response"):
            st.session_state.max_tokens = int(os.getenv('MAX_TOKEN_3'))        

# filter dropdown
import streamlit as st

def reset_filters():
    st.session_state.filters_applied = False
    st.session_state.applied_filters = {
        'doc_type': '-'
    }
    
    # ตรวจสอบและกำหนดค่าให้ doc_type_options หากยังไม่มี
    if 'doc_type_options' not in st.session_state:
        st.session_state.doc_type_options = ['-'] + kb_meta_data_db.list_doc_type()

    # # รีเซ็ตค่า config parameters
    # st.session_state.temperature = float(os.getenv('TEMP_2', 0.5))
    # st.session_state.max_tokens = int(os.getenv('MAX_TOKEN_2', 100))
    # st.session_state.reset_max_relevant_result = st.slider('', 1, 10, 3)

    # ใช้ st.experimental_rerun() เพื่อรีเฟรชหน้าจอและให้ค่า default แสดงผล
    st.rerun()

def filter_data(doc_type):
    if doc_type != '-':
        return doc_type  # Return the selected doc_type for demonstration purposes
    return None  # If no filter applied, return None

def dropdownlist():
    # ตรวจสอบและกำหนดค่าเริ่มต้นสำหรับ filters_applied
    if 'filters_applied' not in st.session_state:
        st.session_state.filters_applied = False

    if 'applied_filters' not in st.session_state:
        st.session_state.applied_filters = {
            'doc_type': '-'
        }

    # ตรวจสอบว่ามีค่าใน st.session_state หรือไม่และตั้งค่า default ให้ doc_type_options
    if 'doc_type_options' not in st.session_state:
        st.session_state.doc_type_options = ['-'] + kb_meta_data_db.list_doc_type()

    # สร้าง string สำหรับแสดง selected filters
    selected_filters = ""
    if st.session_state.filters_applied:
        if st.session_state.applied_filters['doc_type'] != '-':
            # Change "Document Type:" to white using CSS
            selected_filters += f"<span style='color: white;'>Document Type:</span> {st.session_state.applied_filters['doc_type']}, "
        
        # Remove the trailing comma and space if selected_filters is not empty
        if selected_filters:
            selected_filters = selected_filters[:-2]  # ตัดเครื่องหมาย , ตัวสุดท้ายออก
            # Display the selected filters as an h5 header
            st.markdown(f"<h5>{selected_filters}</h5>", unsafe_allow_html=True)
        else:
            st.markdown('<div style="margin: 0 0 -10px 0;"><h5>No filter selected</h5></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="margin: 0 0 -10px 0;"><h5>No filter selected</h5></div>', unsafe_allow_html=True)

    # กำหนดค่า default index ถ้าไม่ได้เลือกตัวเลือกใด ๆ
    def get_index(options, selected):
        return options.index(selected) if selected in options else 0

    doc_type_options = st.session_state.doc_type_options

    # Displaying the label as an h5 header
    st.markdown('<div style="margin: -20px 0 -100px 0;">"<h5>Select Document Type</h5>"</div>', unsafe_allow_html=True)

    # Create the selectbox for document types
    doc_type_selected = st.selectbox(
        '',
        doc_type_options,
        key='doc_type_selectbox',
        index=get_index(doc_type_options, st.session_state.applied_filters['doc_type'])
    )

def select_clear_button():
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button('Select', key='select_button'):
            # ตรวจสอบว่ามีการเลือก filter
            if st.session_state.doc_type_selectbox != '-':
                st.session_state.filters_applied = True
                st.session_state.applied_filters = {
                    'doc_type': st.session_state.doc_type_selectbox
                }
                st.rerun()
            else:
                st.error("⚠️ Please select a document type.")

    with col2:
        if st.button('Clear filter', key='clear_filter_button'):
            reset_filters()
            st.rerun()

