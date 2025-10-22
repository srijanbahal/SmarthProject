
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from groq import Groq
import os
import json
import scipy.stats
import re
from dotenv import load_dotenv
load_dotenv()


# --- 1. Configuration & Setup ---

# Use the DB created by our new seed_data.py
DB_PATH = "../project_samarth.db"

# Setup API Key
# IMPORTANT: Store your API key in Streamlit Secrets
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# *** NEW: Static map of our data sources ***
DATA_SOURCES_MAP = {
    "crop_production": "https://data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997-2022",
    "rainfall": "https://data.gov.in/resource/sub-division-district-wise-realtime-rainfall-2019-2024"
}
# Setup LLM Client
try:
    client = Groq()
    # Use a powerful model for both SQL generation and Synthesis
    MODEL = "llama-3.3-70b-versatile" 
except Exception as e:
    st.error(f"Failed to initialize Groq client. Check API Key. Error: {e}")
    st.stop()

# --- 2. Core Functions for QAS Pipeline ---

@st.cache_resource
def get_db_schema():
    """Gets the CREATE TABLE statements from the SQLite DB."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name IN ('crop_production', 'rainfall');")
            schema_rows = cursor.fetchall()
            if not schema_rows:
                st.error(f"Database '{DB_PATH}' seems to be empty. Did you run seed_data.py?")
                return None
            return "\n".join([row[0] for row in schema_rows if row[0]])
    except Exception as e:
        st.error(f"Error connecting to SQLite DB at '{DB_PATH}'. Did you run seed_data.py? Error: {e}")
        return None

def generate_sql_queries(question: str, schema: str):
    """
    Stage 1: The "Query Generator" (LLM 1)
    Takes a question and schema, returns a list of SQL queries.
    """
    st.session_state.logs.append("Stage 1: Generating SQL Queries...")
    
    prompt = f"""
    You are an expert Text-to-SQL data analyst for a SQLite database.
    Your task is to generate a JSON object containing a list of SQL queries needed to fetch all raw data to answer the user's question.
    
    DATABASE SCHEMA:
    {schema}
    
    RULES:
    1.  Respond with a single JSON object: {{"queries": ["SQL1", "SQL2", ...]}}
    2.  For simple questions (Q1, Q2), you will likely only need one query.
    3.  For complex questions (Q3: correlation, Q4: policy), you MUST generate multiple queries (e.g., one for 'crop_production', one for 'rainfall').
    4.  **Crucial for time:** For "last N years" (e.g., "last 5 years"), you MUST generate the SQL logic:
        `WHERE year > (SELECT MAX(year) - 5 FROM crop_production)`
    5.  **Crucial for matching:** Always use `UPPER()` on district names and `Title()` on crop names in your `WHERE` clauses (e.g., `WHERE district = UPPER('agra')` and `WHERE crop = 'Rice'`).
    6.  The database only contains data for 'Uttar Pradesh'. Do not filter for it.
    
    User Question:
    "{question}"
    
    JSON Response:
    """
    
    messages = [{"role": "user", "content": prompt}]
    
    try:
        response_text = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"},
        ).choices[0].message.content
        
        st.session_state.logs.append(f"LLM 1 (Query Gen) Raw Output:\n{response_text}")
        parsed_json = json.loads(response_text)
        queries = parsed_json.get("queries", [])
        
        if not queries:
            raise ValueError("LLM did not return any queries.")
            
        return queries
    except Exception as e:
        st.session_state.logs.append(f"LLM 1 (Query Gen) Error: {e}")
        return None

def run_sql_queries(sql_queries: list):
    """
    Stage 2: The "Data Executor" (Python/SQL)
    Runs queries and returns data and traceable citations.
    """
    st.session_state.logs.append(f"Stage 2: Executing {len(sql_queries)} SQL Queries...")
    
    data_dict = {}
    citation_details = {
        "sources_queried": [],
        "sql_run": []
    }
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            for i, query in enumerate(sql_queries):
                # Simple read-only validation
                if not query.strip().upper().startswith("SELECT"):
                    st.session_state.logs.append(f"Skipping non-SELECT query: {query}")
                    continue
                
                df = pd.read_sql_query(query, conn)
                
                # Infer table name for citation
                table_name = "unknown"
                if "crop_production" in query:
                    table_name = "crop_production"
                    citation_details["sources_queried"].append(DATA_SOURCES_MAP["crop_production"])
                elif "rainfall" in query:
                    table_name = "rainfall"
                    citation_details["sources_queried"].append(DATA_SOURCES_MAP["rainfall"])
                
                data_dict[f"data_{i+1}_{table_name}"] = df
                citation_details["sql_run"].append(query)
        
        # Deduplicate sources
        citation_details["sources_queried"] = list(set(citation_details["sources_queried"]))
        st.session_state.logs.append(f"DataExecutor: Success. Returning {len(data_dict)} dataframes.")
        return data_dict, citation_details
        
    except Exception as e:
        st.session_state.logs.append(f"DataExecutor Error: {e}")
        return None, {"error": str(e)}

def synthesize_answer(question: str, data_dict: dict):
    """
    Stage 3: The "Synthesizer & Analyst" (LLM 2)
    Takes the question and raw data, returns the final answer and viz spec.
    """
    st.session_state.logs.append(f"Stage 3: Synthesizing Answer with {len(data_dict)} dataframes...")
    
    # Convert dataframes to CSV strings for the prompt
    data_context = ""
    for name, df in data_dict.items():
        data_context += f"--- Data: {name} ---\n{df.to_csv(index=False)}\n\n"

    synthesis_prompt = f"""
    You are an expert agricultural and policy analyst. Your task is to provide a comprehensive answer AND a visualization spec.
    You MUST base your answer *ONLY* on the data provided in the 'DATA CONTEXT' section.
    
    USER QUESTION:
    "{question}"
    
    DATA CONTEXT:
    {data_context}
    
    INSTRUCTIONS:
    Respond with a single JSON object with two keys: "answer" and "visualization".
    
    1.  "answer": (string)
        -   Write a comprehensive, insightful answer to the user's question, using only the data.
        -   If asked to "correlate" (Q3), look at the two dataframes and state the apparent relationship (e.g., "production rose as rainfall increased").
        -   If asked for "policy arguments" (Q4), use the data to form compelling, logical arguments.
        -   Be well-structured and easy to read.
    
    2.  "visualization": (JSON object or null)
        -   Provide a JSON spec for the *best* Plotly Express chart to visualize the answer.
        -   The spec MUST include: "data_key" (the name of the data to use, e.g., "data_1_crop_production"), "type" (e.g., "bar", "line"), "x", "y", "color" (optional), and "title".
        -   Example: {{"data_key": "data_1_crop_production", "type": "bar", "x": "crop", "y": "production", "color": "district", "title": "Crop Production by District"}}
        -   If no visualization is appropriate, set this to null.

    YOUR JSON RESPONSE:
    """
    
    messages = [
        {"role": "system", "content": "You are a helpful analyst that synthesizes data into a JSON response containing an 'answer' and a 'visualization' spec."},
        {"role": "user", "content": synthesis_prompt}
    ]
    
    try:
        response_text = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"},
        ).choices[0].message.content
        
        st.session_state.logs.append(f"LLM 2 (Synthesizer) Raw Output:\n{response_text}")
        parsed_json = json.loads(response_text)
        return parsed_json
        
    except Exception as e:
        st.session_state.logs.append(f"LLM 2 (Synthesizer) Error: {e}")
        return None

# --- 3. Streamlit App UI ---

st.set_page_config(page_title="Project Samarth (QAS Model)", layout="wide")
st.title("🌾 Project Samarth (QAS Model)")
st.subheader("A robust Query-Analyze-Synthesize system for agricultural data in Uttar Pradesh.")

# Sample questions for the user to click
sample_questions = {
    "Q1 (Compare)": "Compare the total production of 'Rice' in 'AGRA' and 'LUCKNOW' in the most recent 5 years.",
    "Q2 (Identify)": "Identify the district with the highest production of 'Wheat' in 1997.",
    "Q3 (Correlate)": "Analyze the production trend of 'Wheat' in 'BASTI' district over the last 10 years. Correlate this trend with the average annual rainfall in that same district.",
    "Q4 (Policy)": "A policy advisor wants to promote drought-resistant crops (like 'Bajra', 'Jowar') over water-intensive crops (like 'Rice', 'Sugarcane') in 'JHANSI' district. Based on data from the last 5 years, what are data-backed arguments to support this?"
}

# Initialize session state
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'question_input' not in st.session_state:
    st.session_state.question_input = sample_questions["Q1 (Compare)"]

# Sidebar
db_schema = get_db_schema()
with st.sidebar:
    st.header("Sample Questions")
    for key, val in sample_questions.items():
        if st.button(f"{key}: {val[:50]}...", help=val):
            st.session_state.question_input = val
            st.rerun() 

    st.divider()
    st.header("System Status")
    if db_schema:
        st.success("SQLite DB Connected")
        with st.expander("Database Schema"):
            st.code(db_schema, language="sql")
    else:
        st.error("SQLite DB Connection Failed!")
        
    st.success("Groq LLM Client Initialized")

# Main content area
question = st.text_area("Ask your question:", 
                        value=st.session_state.get('question_input', ''), 
                        height=100,
                        key='question_input')

if st.button("🔍 Analyze", type="primary"):
    if not question.strip():
        st.warning("Please enter a question.")
    elif not db_schema:
        st.error("Cannot proceed, database schema is not loaded.")
    else:
        st.session_state.logs = []
        answer, viz_spec, data_dict, citation_details = None, None, None, None
        
        with st.spinner("Stage 1: Generating SQL..."):
            sql_queries = generate_sql_queries(question, db_schema)
        
        if sql_queries:
            with st.spinner("Stage 2: Executing SQL queries..."):
                data_dict, citation_details = run_sql_queries(sql_queries)
        
        if data_dict:
            with st.spinner("Stage 3: Analyzing data and synthesizing answer..."):
                answer_json = synthesize_answer(question, data_dict)
                if answer_json:
                    answer = answer_json.get("answer")
                    viz_spec = answer_json.get("visualization")
        
        st.divider()
        
        if answer:
            st.header("🤖 Answer")
            st.markdown(answer)
        else:
            st.error("I'm sorry, I couldn't generate an answer for that question. Please check the logs.")

        # Visualization
        if viz_spec:
            st.header("📊 Visualization")
            try:
                data_key = viz_spec.get("data_key")
                df_to_plot = data_dict.get(data_key)
                
                if df_to_plot is None:
                    st.warning(f"LLM wanted to plot '{data_key}', but that data wasn't found.")
                else:
                    chart_type = viz_spec.get("type")
                    x_col = viz_spec.get("x")
                    y_col = viz_spec.get("y")

                    if x_col not in df_to_plot.columns or y_col not in df_to_plot.columns:
                        st.warning(f"LLM suggested a chart but columns '{x_col}' or '{y_col}' were not in the data.")
                    else:
                        fig = None
                        if chart_type == "bar":
                            fig = px.bar(df_to_plot, x=x_col, y=y_col, color=viz_spec.get("color"), title=viz_spec.get("title"))
                        elif chart_type == "line":
                            fig = px.line(df_to_plot, x=x_col, y=y_col, color=viz_spec.get("color"), title=viz_spec.get("title"))
                        elif chart_type == "scatter":
                             fig = px.scatter(df_to_plot, x=x_col, y=y_col, color=viz_spec.get("color"), title=viz_spec.get("title"))
                        
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"LLM suggested an unknown chart type: '{chart_type}'")
            except Exception as e:
                st.error(f"Error rendering LLM-suggested visualization: {e}")
                st.session_state.logs.append(f"Viz Error: {e}, Spec: {viz_spec}")
        elif answer:
            st.info("No visualization was recommended for this answer.")

        # Traceable Citations
        if citation_details:
            st.header("📚 Data Source & Traceability")
            st.caption("This answer was generated by querying the following sources with these exact SQL queries:")
            
            for url in citation_details["sources_queried"]:
                st.markdown(f"- **Source:** `{url}`")
                
            st.markdown(f"**SQL Queries Run:**")
            st.code("\n\n".join(citation_details["sql_run"]), language="sql")
            
        if data_dict:
            with st.expander("View Raw Data Used for Answer"):
                for name, df in data_dict.items():
                    st.subheader(f"Data: `{name}`")
                    st.dataframe(df)
                
        with st.expander("View System Logs (Debug)"):
            st.code("\n".join(st.session_state.logs))