import streamlit as st
import boto3
import json
import datetime
import os
import time
import uuid
from streamlit_date_picker import date_range_picker, PickerType
import doc_kb_lib as kb
import sidebar_incident as sb
import kb_meta_data_db
import base64
from datetime import datetime as dt

def chat_doc_kb():

    #get username
    User = st.session_state.get('username', 'anonymous')

    def clear_chat_history():
        st.session_state.messages = []
        if 'sessionId' in st.session_state:
            st.session_state['sessionId'] = ""

        if 'context' in st.session_state:
            del st.session_state['context']

        st.markdown(f'<div class="clear-chat-info">Clear KB-SessionID : {st.session_state["sessionId"]}</div>', unsafe_allow_html=True) 
        sb.reset_filters()

    # Initialize session state variables
    if 'max_relevant_result' not in st.session_state:
        st.session_state.max_relevant_result = int(os.getenv("MAX_RELEVANT_RESULTS"))  # Default value

    # Load CSS
    with open('./page_style.css') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    def load_image(image_file):
        with open(image_file, "rb") as f:
            return base64.b64encode(f.read()).decode()

    logo_base64 = load_image("Logo/White.png")
                            
    # Sidebar
    with st.sidebar:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center;">
                <img src="data:image/png;base64,{logo_base64}" alt="logo" 
                    style="width: 150px; 
                    margin-right: 5px; 
                    margin-top: -50px;
                    margin-left: -30px;
                    ">
            </div>
            """,
            unsafe_allow_html=True
        )   

        st.markdown('<div class="sidebar">', unsafe_allow_html=True)

        # Inject CSS for styling
        st.markdown("""
            <style>
            div.stCheckbox > label > div {
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

        # Native Streamlit checkbox
        st.subheader("Guardrails")
        enable_guardrails = st.checkbox("Enable Guardrails", value=False, key="guardrails_checkbox")

        # Save the state in session_state
        st.session_state.enable_guardrails = enable_guardrails

        st.subheader("Settings")
        if 'temperature' not in st.session_state:
            st.session_state.temperature = float(os.getenv('TEMP_1'))  
        if 'max_tokens' not in st.session_state:
            st.session_state.max_tokens = int(os.getenv('MAX_TOKEN_1')) 
            
        st.markdown(
            "<h4 style='color:white; font-weight:bold;'>Creativity Level:</h4>", 
            unsafe_allow_html=True
        )
        sb.creativity_button()
        
        st.markdown(
            "<h4 style='color:white; font-weight:bold;'>Response Length:</h4>", 
            unsafe_allow_html=True
        )
        sb.token_button()
        
        st.markdown(
            "<h4 style='color:white; font-weight:bold;'>No. search result</h4>", 
            unsafe_allow_html=True
        )

        # Handle the max_relevant_result slider
        if 'reset_max_relevant_result' in st.session_state and st.session_state.reset_max_relevant_result:
            st.session_state.max_relevant_result = 3
            st.session_state.reset_max_relevant_result = False
        
        st.session_state.max_relevant_result = st.slider('', 1, 15, st.session_state.max_relevant_result, key='max_relevant_result_slider')

        st.markdown('<p>', unsafe_allow_html=True)

        st.subheader("Filter")

        # Initialize session state for date range if not already set
        if 'start_date' not in st.session_state:
            st.session_state.start_date = datetime.datetime.now() - datetime.timedelta(days=366)
        if 'end_date' not in st.session_state:
            st.session_state.end_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # Date picker 
        default_end = datetime.datetime.now() + datetime.timedelta(days=1)
        default_start = default_end - datetime.timedelta(days=366)

        date_range_string = date_range_picker(
            picker_type=PickerType.date,
            start=st.session_state.start_date,
            end=st.session_state.end_date,
            key='date_range_picker'
        )

        if date_range_string:
            start, end = date_range_string
            st.session_state.start_date = datetime.datetime.strptime(start, '%Y-%m-%d')
            st.session_state.end_date = datetime.datetime.strptime(end, '%Y-%m-%d')
            start_str = st.session_state.start_date.strftime('%d-%b-%y')
            end_str = st.session_state.end_date.strftime('%d-%b-%y')
            st.markdown(
                f"<p style='color:white;'>Doc Date: {start_str} To {end_str}</p>",
                unsafe_allow_html=True
            )

        sb.dropdownlist()
        sb.select_clear_button()
        st.markdown('<hr>', unsafe_allow_html=True)

        # Create the button for clearing chat history
        if st.button('Clear chat history', key="clear_chat_button"):
            clear_chat_history()
        
        st.markdown('</div>', unsafe_allow_html=True)

    def generate_unique_key():
        return str(uuid.uuid4())

    st.markdown("<br>", unsafe_allow_html=True)
    region = boto3.Session().region_name
    session = boto3.Session(region_name=region)
    lambda_client = session.client('lambda')

    st.markdown(
        """
        <div style="display: flex; align-items: center;">
            <img src="https://www.yipintsoi.com/assets/LOGO-1.png" alt="logo" style="width: 200px; margin-right: 5px;margin-left: 250px;">
        </div>
        """,
        unsafe_allow_html=True
    )

    # Load CSS for custom styling
    st.markdown(
        """
        <style>
            .custom-info {
                background-color: rgb(17, 17, 17, 0.81); /* Dark background */
                color: white; /* White text */
                padding: 10px;
                border-radius: 5px;
                border: 1px solid rgb(17, 17, 17, 0.25); /* Optional border */
                margin-bottom: 20px; /* Corrected property */
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Custom info message
    st.markdown(
        '<div class="custom-info"><strong>Hello:</strong> Welcome to the internal knowledge search by YIP.</div>',
        unsafe_allow_html=True
    )

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize session id
    if 'sessionId' not in st.session_state:
        st.session_state['sessionId'] = ""

    # Initialize feedback
    if 'feedback' not in st.session_state:
        st.session_state.feedback = {}

    def save_feedback_to_json(data):
        folder_name = "log"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        username = data.get("username", "anonymous")
        timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(folder_name, f"feedback_{username}_{timestamp}.json")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"An error occurred while saving feedback: {str(e)}")

    # Initialize session state for feedback status if not already done
    if 'feedback_status' not in st.session_state:
        st.session_state.feedback_status = {}

    def create_feedback_buttons(text_id):
        # Initialize feedback status for the text_id if not already done
        if text_id not in st.session_state.feedback_status:
            st.session_state.feedback_status[text_id] = None
        
        with st.container():
            col1, col2 = st.columns([1, 15])  # Use equal column width

            # Placeholder for success message
            success_message_placeholder = st.empty()
            
            feedback_given = st.session_state.feedback_status[text_id] is not None

            with col1:
                if not feedback_given:
                    if st.button('👍', key=f'like_{text_id}'):
                        feedback_data = {
                            "username": User,
                            "text_id": text_id,
                            "like_dislike": 1
                        }
                        save_feedback_to_json(feedback_data)
                        st.session_state.feedback[text_id] = 1
                        st.session_state.feedback_status[text_id] = 1  # Mark feedback as given
                        success_message_placeholder.success("You liked the message!")  # Display success message
                        st.session_state.feedback_given = True  # Update session state
                else:
                    st.write('👍')  # Replace button with text once clicked

            with col2:
                if not feedback_given:
                    if st.button('👎', key=f'unlike_{text_id}'):
                        feedback_data = {
                            "username": User,
                            "text_id": text_id,
                            "like_dislike": 0
                        }
                        save_feedback_to_json(feedback_data)
                        st.session_state.feedback[text_id] = 0
                        st.session_state.feedback_status[text_id] = 0  # Mark feedback as given
                        success_message_placeholder.success("You unliked the message!")  # Display success message
                        st.session_state.feedback_given = True  # Update session state
                else:
                    st.write('👎')  # Replace button with text once clicked

    # Display chat messages from history on app rerun
    for i, message in enumerate(st.session_state.messages):
        text_id = message["text_id"]
        with st.chat_message(message["role"]):
            st.markdown(f'<div class="h1">{message["content"]}</div>', unsafe_allow_html=True)
            if message["role"] == "assistant":
                create_feedback_buttons(text_id)

    if prompt := st.chat_input("What is up?"):
        question = prompt
        st.chat_message("user").markdown(f'<div class="user-message">{question}</div>', unsafe_allow_html=True)

        # Set start and end incident times
        start_incident_str = st.session_state.start_date.strftime('%Y-%m-%d')
        end_incident_str = st.session_state.end_date.strftime('%Y-%m-%d')

        # Set configuration parameters
        config_params = {
            "temperature": st.session_state.temperature,
            "max_token_response": st.session_state.max_tokens,
            "max_relevant_results": st.session_state.max_relevant_result
        }

        # Store feedback
        feedback = st.session_state.feedback
        
        # Create filter list
        doc_type = st.session_state.applied_filters.get('doc_type', '-')
        if doc_type != '-':
            # Create filter list
            filter_list = {
                'doc_type': doc_type
            }
            config_params["kb_prompt"] = kb.get_kb_prompt(doc_type)
        else:
            filter_list = {}
            config_params["kb_prompt"] = kb.get_kb_prompt("")

        # Create filter metadata including doc_type
        kb_filter = kb_meta_data_db.create_filter_metadata(filter_list, start_date=start_incident_str, end_date=end_incident_str)
        
        payload = {
            "question": question,
            "session_id": st.session_state['sessionId'],
            "metadata_filter": kb_filter,
            "config_params":config_params,
            "enable_guardrails": st.session_state.get('enable_guardrails', False)
        }
        # Get knowledge base response
        start_time = time.time()
        with st.spinner("Processing..."):
            # Get knowledge base response
            result = kb.invoke_lambda_function(
                payload
            )
        end_time = time.time()

        start_time_str = dt.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
        end_time_str = dt.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')

        print('===========result============')
        print(result)
        print('=============================')

        result = result['response']
        result = json.loads(result)
        print('===========result json============')
        print(result)
        print('=============================')

        print('===========payload============')
        print(payload)
        print('=============================')

        response_time_s = (end_time - start_time)
        answer = result['answer']
        sessionId = result['sessionId']
        context = result['all_contexts_to_answer']
        metadata_list = result['metadata']
        _, input_token_count = kb.count_char_tokens(question)
        _, output_token_count = kb.count_char_tokens(answer)
        max_chunk_result = st.session_state.max_relevant_result
        actual_chunk_result = len(result.get('metadata', []))
        created_datetime = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        prompt_kb = result['prompt_kb']

        text_id = generate_unique_key() 

        data_to_save = {
            "text_id": text_id,
            "session_id": sessionId,
            "username": User,
            "question": question,
            "answer": answer,
            "context": context,
            "no_input_question_token": input_token_count,
            "no_input_all_token" : 0,
            "no_output_answer_token": output_token_count,
            "start_datetime": start_time_str,
            "end_datetime": end_time_str,
            "duration_start_to_end": response_time_s,
            "temperature": st.session_state.temperature,
            "output_max_length": st.session_state.max_tokens,
            "max_relevant_result": max_chunk_result,
            "actual_relevant_result": actual_chunk_result,
            "like_dislike": st.session_state.feedback.get(text_id, None),
            "created_datetime": created_datetime,
            "prompt_kb": prompt_kb,
            "doc_type": doc_type if doc_type != '-' else ""
        }

        def save_data(data):
            folder_name = "log"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            username = data.get("username", "anonymous")
            timestamp = dt.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(folder_name, f"conversation_{username}_{timestamp}.json")

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        save_data(data_to_save)

        # Reset feedback after using
        st.session_state['sessionId'] = sessionId

        
        # Extract response details
        answer = result['answer']
        sessionId = result['sessionId']
        url_contexts = result['url']
        st.session_state['sessionId'] = sessionId

        # Add new message to chat history with the text_id
        st.session_state.messages.append({
            "role": "user",
            "content": question,
            "text_id": text_id  # Store the text_id with the message
        })

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            for word in answer.split():
                full_response += word + " "
                time.sleep(0.15)
                response_placeholder.markdown(f'<div class="assistant-message">{full_response}▌</div>', unsafe_allow_html=True)
            response_placeholder.markdown(f'<div class="assistant-message">{answer}</div>', unsafe_allow_html=True)

            create_feedback_buttons(text_id)

        # Display citations with presigned URLs
        if url_contexts:
                st.markdown('<div class="citation-header">====================Citation====================</div>', unsafe_allow_html=True)
                for url in url_contexts:
                    # Generate presigned URL
                    s3_presigned_url = kb.generate_presigned_url(url)
                    # Display link with presigned URL
                    if s3_presigned_url:
                        display_link = f"{[url]}({s3_presigned_url})"
                        st.markdown(display_link)
        
        # st.markdown('<div class="follow-up-questions">These are follow-up questions: ?</div>', unsafe_allow_html=True)
        # st.markdown(f'<div class="session-id">SessionID: {st.session_state["sessionId"]}</div>', unsafe_allow_html=True)

        # Save context in session state for displaying in expander
        st.session_state.context = result['all_contexts_to_answer']

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": answer, "text_id": text_id})

    with st.sidebar:
        st.markdown('<hr>', unsafe_allow_html=True)
        with st.expander("Context to answer"):
            if "context" in st.session_state:
                st.markdown(f"""
                    <div style="color:white;">
                        {st.session_state.context}
                """, unsafe_allow_html=True)