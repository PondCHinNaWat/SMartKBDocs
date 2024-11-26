from dotenv import dotenv_values
from datetime import datetime
import psycopg2
import pandas as pd
import os
import streamlit as st

config = dotenv_values('.env')
   
def get_postgres_conn():
    try:
        conn = psycopg2.connect(
                database=config['DATABASES_NAME'], user=config['DATABASES_USER'],
            password=config['DATABASES_PASSWORD'], host=config['DATABASES_HOST']
            )
        return conn

    except Exception as error:
        print(error)   
def list_data_pg(sql,params):
    
    df=None   
    with get_postgres_conn().cursor() as cursor:
        
        if params is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql,params)
        
        columns = [col[0] for col in cursor.description]
        dataList = [dict(zip(columns, row)) for row in cursor.fetchall()]
        df = pd.DataFrame(data=dataList) 
    return df   

@st.cache_data (ttl= int(config["CatchData_HOUR"])*int(config["CatchData_SECOND"]))
def list_doc_type():
    
    sql="select * from app_doctype"
    dfDocType=list_data_pg(sql,None)
    listDocType=dfDocType['type_name'].tolist()
    
    return listDocType


@st.cache_data (ttl= int(config["CatchData_HOUR"])*int(config["CatchData_SECOND"]))
def list_all_prompt_doc_type():
    
    sql="select type_name,prompt_description from app_doctype where is_active='true' "
    dfDocType=list_data_pg(sql,None)
    
    return dfDocType

@st.cache_data (ttl= int(config["CatchData_HOUR"])*int(config["CatchData_SECOND"]))
def get_default_prompt():
    sql="select value from app_configvalue where key='default_prompt' limit 1"
    df=list_data_pg(sql, None)
    if df.empty==False:
      return df.iloc[0,0]
    else:
        e = RuntimeError("No default prompt template,please fill in in web admin [url]/admin/app/configvalue/default_5Fprompt/change/")
        st.exception(e)

def create_filter_metadata(dict_type, start_date, end_date):
    print("Create filter metadata.")
    # Convert start_date and end_date to timestamps
    start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
    end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp())
    
    # Create dictionaries for start and end timestamps
    dict_start_timestamp = {"greaterThanOrEquals": {"key": "doc_date", "value": start_timestamp}}
    dict_end_timestamp = {"lessThanOrEquals": {"key": "doc_date", "value": end_timestamp}}
    
    # Add these dictionaries to kb_timestamp_filter
    kb_timestamp_filter = [dict_start_timestamp, dict_end_timestamp]
    
    # Iterate over dict_type to create the kb_type_filter list
    if len(dict_type)>0:
        kb_type_filter = [{"equals": {"key": k, "value": v}} for k, v in dict_type.items()]
        # Combine kb_timestamp_filter and kb_type_filter into kb_filter_list
        kb_filter_list = kb_timestamp_filter + kb_type_filter
    else:
        kb_filter_list = kb_timestamp_filter
        
    # print(kb_filter_list)    
        
    
    # Create the final kb_filter dictionary
    kb_filter = {"andAll": kb_filter_list}
    
    return kb_filter



# kb_meta_data_db.py

import psycopg2
from psycopg2 import sql
import hashlib
import base64

# Function to authenticate user from the PostgreSQL auth_user table
def authenticate_user(username, password):
    try:
        # Connect to PostgreSQL database
        conn=get_postgres_conn()
        cur = conn.cursor()

        # Query the auth_user table for the given username
        query = sql.SQL("SELECT password FROM auth_user WHERE username = %s")
        cur.execute(query, (username,))
        result = cur.fetchone()

        # If user exists, check the password
        if result:
            stored_password = result[0]
            # Hash the entered password and compare
            if check_password(stored_password, password):
                return True

        # Close the database connection
        cur.close()
        conn.close()

        return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def check_password(stored_password, entered_password):
    """
    Check if the entered password matches the stored password from auth_user.
    Django stores passwords in the format: 'hashtype$salt$hashedpassword'.
    """
    if stored_password.startswith('pbkdf2_'):
        algo, iterations, salt, stored_hash = stored_password.split('$')

        # Hash the entered password using the same algorithm, salt, and iteration count
        entered_password_hash = hashlib.pbkdf2_hmac(
            'sha256', entered_password.encode('utf-8'), salt.encode('utf-8'), int(iterations)
        )
        
        # Convert the entered password hash to base64 for comparison (Django uses base64)
        entered_password_hash_b64 = base64.b64encode(entered_password_hash).decode('utf-8').strip()

        # Compare the base64 encoded hash with the stored hash
        return entered_password_hash_b64 == stored_hash

    return False
