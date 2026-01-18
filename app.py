import streamlit as st
import sqlite3
import pandas as pd
from google import genai
from google.genai import types

# 1. Page Config
st.set_page_config(page_title="SQL Assistant", layout="centered")
st.title("Auto SQL Generator")

# 2. Get API Key from Sidebar
api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if not api_key:
    st.info("Please enter your Gemini API key in the sidebar to continue.")
    st.stop()

# 3. Configure Gemini Client (New SDK)
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Failed to initialize client: {e}")
    st.stop()

# 4. Database Context
db_schema = """
Table: employees (id, name, salary, department_id, hire_date)
Table: departments (id, name)
"""

def get_sql_from_gemini(question):
    prompt = f"""
    You are an expert SQL assistant.
    Schema:
    {db_schema}
    
    Task: Convert this question to a valid SQL query for SQLite.
    Question: {question}
    
    Rules:
    1. Return ONLY the raw SQL query.
    2. Do not use markdown formatting (no ```sql).
    3. Do not include explanations.
    """
    
    try:
        # UPDATED SYNTAX: "models.generate_content"
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite', 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def run_query(query):
    conn = sqlite3.connect('company.db')
    try:
        return pd.read_sql_query(query, conn), None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

# 5. UI Logic
user_question = st.text_input("Ask a question:", "Who earns the most in Engineering?")

if st.button("Run Query"):
    with st.spinner("Generating SQL..."):
        sql_query = get_sql_from_gemini(user_question)
        
        # Check for errors in generation
        if "Error" in sql_query:
            st.error(sql_query)
        else:
            # Display the generated SQL
            st.code(sql_query, language="sql")
            
            # Run the SQL
            results, error = run_query(sql_query)
            if error:
                st.error(f"SQL Execution Error: {error}")
            else:
                st.success("Query successful!")
                st.dataframe(results)