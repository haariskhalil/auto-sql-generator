import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from google import genai

# 1. SETUP PAGE CONFIG
st.set_page_config(
    page_title="Data Commander",
    page_icon="⚡",
    layout="wide"
)

# 2. CUSTOM CSS
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #41424C;
    }
</style>
""", unsafe_allow_html=True)

# 3. SIDEBAR CONFIG
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    
    st.markdown("### 💡 Tips")
    st.info("Try asking about 'Salaries' or 'Department counts'.")

# 4. INITIALIZE GEMINI
if not api_key:
    st.warning("Please enter your API Key in the sidebar to start.")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 5. DATABASE HELPERS
def get_db_connection():
    return sqlite3.connect('company.db')

def run_query(query):
    conn = get_db_connection()
    try:
        return pd.read_sql_query(query, conn), None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

#LIVE DATA PREVIEW
st.title("⚡ Data Commander")
st.markdown("### Talk to your database in plain English")

with st.expander("📂 View Database Schema & Data (Click to Expand)", expanded=False):
    # This will look cramped on smaller screens - perfect for our "Before" commit
    col1, col2, col3 = st.columns(3)
    
    conn = get_db_connection()
    
    with col1:
        st.subheader("Employees")
        df_emp = pd.read_sql("SELECT * FROM employees", conn)
        st.dataframe(df_emp, use_container_width=True, height=200)
    
    with col2:
        st.subheader("Departments")
        df_dept = pd.read_sql("SELECT * FROM departments", conn)
        st.dataframe(df_dept, use_container_width=True, height=200)

    with col3:
        st.subheader("Projects") # <--- The new table!
        df_proj = pd.read_sql("SELECT * FROM projects", conn)
        st.dataframe(df_proj, use_container_width=True, height=200)
    
    conn.close()

# 7. CHAT INTERFACE & LOGIC
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How can I help you analyze the data today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. THE BRAIN
# Add clickable pills for quick queries
example_prompts = [
    "Who has the highest salary?", 
    "Show average salary by department", 
    "List all employees in Engineering",
    "Count employees per department"
]

button_cols = st.columns(4)
query_to_run = None

# Create buttons that trigger the query
for i, prompt in enumerate(example_prompts):
    if button_cols[i].button(prompt, use_container_width=True):
        query_to_run = prompt

# Input field (works for both manual typing and button clicks)
if prompt := st.chat_input("Ask a question...") or query_to_run:
    # If it was a button click, we need to treat it as a prompt
    if query_to_run and not prompt: 
        prompt = query_to_run

    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking in SQL..."):
            
            # Prompt for better SQL generation
            db_schema = """
            Table: employees (id, name, email, salary, department_id, hire_date)
            Table: departments (id, name, manager_name)
            Table: projects (id, name, budget, deadline, department_id, status)

            Relationships:
            - employees.department_id -> departments.id
            - projects.department_id -> departments.id
            """
            
            system_prompt = f"""
            You are a SQL expert. Convert the user's question into a SQL query for SQLite.
            Schema: {db_schema}
            
            Rules:
            1. Return ONLY the raw SQL query. No markdown.
            2. If the user asks for visualization (like 'plot', 'graph'), just get the data.
            3. Always JOIN tables if department name is needed.
            
            Question: {prompt}
            """
            
            try:
                # Using your preferred model
                response = client.models.generate_content(
                    model='gemini-2.5-flash-lite', # Updated to likely valid string, check yours
                    contents=system_prompt
                )
                sql_query = response.text.strip().replace("```sql", "").replace("```", "")
                
                # Show the code snippet (Transparency adds to the 'Tech' feel)
                st.code(sql_query, language="sql")
                
                # Run Query
                results, error = run_query(sql_query)
                
                if error:
                    st.error(f"SQL Error: {error}")
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {error}"})
                elif results.empty:
                    st.warning("Query returned no results.")
                    st.session_state.messages.append({"role": "assistant", "content": "Query returned no results."})
                else:
                    st.dataframe(results, use_container_width=True)
                    
                    # AUTO-VISUALIZATION
                    # Heuristic: If we have 1 text col and 1 number col, make a Bar Chart
                    num_cols = results.select_dtypes(include=['number']).columns
                    cat_cols = results.select_dtypes(include=['object']).columns
                    
                    if len(num_cols) == 1 and len(cat_cols) == 1:
                        st.subheader("📊 Visual Insight")
                        fig = px.bar(results, x=cat_cols[0], y=num_cols[0], 
                                     color=cat_cols[0], template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Store context
                    st.session_state.messages.append({"role": "assistant", "content": "Here is the data you requested."})

            except Exception as e:
                st.error(f"AI Error: {e}")