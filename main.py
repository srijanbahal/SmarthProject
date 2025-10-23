import streamlit as st
import sqlite3
st.set_page_config(page_title="Project Samarth (Enhanced QAS)", layout="wide")
import pandas as pd
import plotly.express as px
from groq import Groq
import os
import json
import re
import logging
import requests
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
import hashlib
import time  # Added for execution time

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [App] - %(levelname)s - %(message)s')

# MODIFIED: Database path points to the new local DB
DB_PATH = "./data/crop_yield.db"

# MODIFIED: Data sources map updated to reflect the 'crop_yield' table from the CSV
DATA_SOURCES_MAP = {
    "crop_yield": {
        "url": "N/A (Uploaded from crop_yield.csv)",
        "file": "crop_yield.csv",
        "description": "State-wise, season-wise crop production statistics from 1997-2018, including Area, Production, Annual_Rainfall, Fertilizer, Pesticide, and Yield."
    }
}

# --- Data Classes for Structured Pipeline ---
@dataclass
class QueryIntent:
    """Structured representation of query understanding"""
    intent_type: str  # compare, analyze, identify, correlate, policy
    entities: List[str]  # states, crops, years
    metrics: List[str]  # production, rainfall, area, yield
    constraints: Dict[str, Any]  # filters and conditions
    temporal_scope: Optional[str] = None  # last 5 years, 2018, etc.

@dataclass
class TableMetadata:
    """Schema and metadata for each table"""
    name: str
    columns: List[str]
    sample_rows: pd.DataFrame
    date_range: Tuple[Optional[int], Optional[int]]
    description: str
    key_columns: Dict[str, List[str]]  # entity types -> column names

@dataclass
class QueryPlan:
    """Execution plan for data retrieval"""
    sql_query: str
    parameters: List[Any]
    target_table: str
    intent: QueryIntent
    expected_columns: List[str]

@dataclass
class ExecutionResult:
    """Result of query execution with provenance"""
    data: pd.DataFrame
    query_plan: QueryPlan
    execution_time: float
    row_count: int
    source_metadata: Dict[str, Any]

# --- 0. Database Download (REMOVED) ---
# The download_db function is no longer needed as we use the local 'crop_yield.db'

# --- 1. Metadata Store Layer ---
class MetadataStore:
    """Manages schema metadata, statistics, and sample data"""
    
    def __init__(self, db_path: str, data_sources: Dict):
        self.db_path = db_path
        self.data_sources = data_sources
        self.tables_metadata: Dict[str, TableMetadata] = {}
        self._initialize_metadata()
    
    def _initialize_metadata(self):
        """Extract and store metadata from database"""
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                for table_name, source_info in self.data_sources.items():
                    # Get columns
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # Get sample rows
                    sample_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
                    
                    # Get date range
                    # MODIFIED: Use 'Crop_Year' as identified from the CSV
                    year_col = 'Crop_Year' if 'Crop_Year' in columns else 'year'
                    if year_col not in columns:
                         logging.warning(f"No year column found in {table_name}")
                         date_range = (None, None)
                    else:
                        date_df = pd.read_sql_query(
                            f"SELECT MIN({year_col}) as min_year, MAX({year_col}) as max_year FROM {table_name}", 
                            conn
                        )
                        date_range = (
                            int(date_df['min_year'].iloc[0]) if pd.notna(date_df['min_year'].iloc[0]) else None,
                            int(date_df['max_year'].iloc[0]) if pd.notna(date_df['max_year'].iloc[0]) else None
                        )
                    
                    # MODIFIED: Identify key columns by type based on CSV schema
                    key_columns = {
                        'state': [c for c in columns if 'state' in c.lower()],
                        'crop': [c for c in columns if c.lower() == 'crop'], # Exact match for 'Crop'
                        'year': [c for c in columns if 'year' in c.lower()],
                        'metrics': [c for c in columns if any(m in c.lower() for m in ['production', 'rainfall', 'area', 'yield', 'fertilizer', 'pesticide'])]
                    }
                    
                    self.tables_metadata[table_name] = TableMetadata(
                        name=table_name,
                        columns=columns,
                        sample_rows=sample_df,
                        date_range=date_range,
                        description=source_info['description'],
                        key_columns=key_columns
                    )
                    
            logging.info(f"Metadata initialized for {len(self.tables_metadata)} tables")
        except Exception as e:
            logging.error(f"Metadata initialization failed: {e}")
    
    def get_table_summary(self, table_name: str) -> str:
        """Generate human-readable table summary"""
        if table_name not in self.tables_metadata:
            return ""
        
        meta = self.tables_metadata[table_name]
        summary = f"""
Table: {meta.name}
Description: {meta.description}
Date Range: {meta.date_range[0]}-{meta.date_range[1]}
Columns: {', '.join(meta.columns)}
Key Entities: States={meta.key_columns['state']}, Metrics={meta.key_columns['metrics']}
Sample Data:
{meta.sample_rows.to_string()}
"""
        return summary
    
    def get_relevant_tables(self, query: str) -> List[str]:
        """Simple keyword-based table retrieval (can be enhanced with embeddings)"""
        # Since we only have one table, always return it.
        return list(self.tables_metadata.keys())

# --- 2. Query Understanding Layer ---
class QueryUnderstanding:
    """Extract intent, entities, and metrics from natural language query"""
    
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def parse_query(self, question: str) -> QueryIntent:
        """Stage 1: Parse query into structured intent"""
        st.session_state.logs.append("🧠 Stage 1: Query Understanding & Intent Extraction...")
        
        prompt = f"""
You are an expert query understanding system for agricultural data analysis.
Analyze the user's question and extract structured information.

USER QUESTION: "{question}"

AVAILABLE DATA:
{self._get_schema_context()}

Respond with JSON containing:
{{
    "intent_type": "compare|analyze|identify|correlate|policy|lookup",
    "entities": ["state names", "crop names"],
    "metrics": ["production", "rainfall", "area", "yield", "fertilizer", "pesticide"],
    "constraints": {{"year": "2018", "crop": "Rice"}},
    "temporal_scope": "last 5 years" or "2010-2015" or "2018" or null
}}

Rules:
1. intent_type: What is user trying to do?
   - compare: comparing values across entities
   - analyze: trend analysis, patterns
   - identify: finding max/min/best
   - correlate: relationship between metrics
   - policy: recommendations, insights
   - lookup: simple fact retrieval

2. entities: Extract specific states, crops mentioned
3. metrics: What measurements are needed (production, rainfall, etc.)
4. constraints: Filters to apply (year ranges, specific crops, etc.)
5. temporal_scope: Time period described in natural language

JSON Response:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            st.session_state.logs.append(f"Intent extracted: {result.get('intent_type', 'unknown')}")
            
            return QueryIntent(
                intent_type=result.get('intent_type', 'lookup'),
                entities=result.get('entities', []),
                metrics=result.get('metrics', []),
                constraints=result.get('constraints', {}),
                temporal_scope=result.get('temporal_scope')
            )
        except Exception as e:
            st.session_state.logs.append(f"❌ Intent extraction failed: {e}")
            logging.error(f"Query understanding error: {e}")
            return QueryIntent('lookup', [], [], {})
    
    def _get_schema_context(self) -> str:
        """Build context about available data"""
        context = ""
        for table_name, meta in self.metadata.tables_metadata.items():
            context += f"\n{table_name}: {meta.description} (Years: {meta.date_range[0]}-{meta.date_range[1]})"
        return context

# --- 3. Query Plan Generation Layer ---
class QueryPlanner:
    """Generate execution plans based on intent and relevant tables"""
    
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def _get_case_rules(self, table_name: str) -> str:
        """Get case sensitivity rules for a table"""
        if table_name not in self.metadata.tables_metadata:
            return ""
        
        meta = self.metadata.tables_metadata[table_name]
        
        # Sample actual values to show LLM the casing
        rules = f"\nCASE SENSITIVITY RULES for {table_name}:\n"
        
        if meta.sample_rows.empty:
            return rules
        
        # MODIFIED: Show actual State values (not district)
        if meta.key_columns['state']:
            state_col = meta.key_columns['state'][0]
            sample_states = meta.sample_rows[state_col].dropna().unique()[:3]
            rules += f"- State values are Title Case: {list(sample_states)}\n"
            rules += f"  → Use parameterized: WHERE {state_col} = ? with Title Case param\n"
        
        # Show actual crop values
        if meta.key_columns['crop']:
            crop_col = meta.key_columns['crop'][0]
            sample_crops = meta.sample_rows[crop_col].dropna().unique()[:3]
            rules += f"- Crop values are Title Case: {list(sample_crops)}\n"
            rules += f"  → Use parameterized: WHERE {crop_col} = ? with Title Case param\n"
        
        return rules
    
    def generate_plans(self, intent: QueryIntent, question: str) -> List[QueryPlan]:
        """Stage 2: Generate SQL query plans"""
        st.session_state.logs.append("📋 Stage 2: Query Plan Generation...")
        
        # Get relevant tables (will just be 'crop_yield')
        relevant_tables = self.metadata.get_relevant_tables(question)
        st.session_state.logs.append(f"Relevant tables: {relevant_tables}")
        
        # Build schema context for selected tables
        schema_context = ""
        for table in relevant_tables:
            schema_context += self.metadata.get_table_summary(table)
            schema_context += self._get_case_rules(table)
            schema_context += "\n\n"
        
        prompt = f"""
You are an expert SQL query planner for agricultural data analysis.

USER QUESTION: "{question}"

EXTRACTED INTENT:
- Type: {intent.intent_type}
- Entities: {intent.entities}
- Metrics: {intent.metrics}
- Constraints: {intent.constraints}
- Temporal Scope: {intent.temporal_scope}

AVAILABLE TABLES & SCHEMA:
{schema_context}

Generate a JSON list of SQL query specifications needed to answer the question.

Response format:
{{
    "query_plans": [
        {{
            "sql": "SELECT ... FROM ... WHERE ...",
            "parameters": ["Assam", 2010],
            "target_table": "crop_yield",
            "expected_columns": ["State", "Crop", "Production", "Crop_Year"],
            "reasoning": "Why this query is needed"
        }}
    ]
}}

CRITICAL RULES FOR SQL GENERATION:
1. **ALWAYS use parameterized queries with ? placeholders** - NEVER put string values directly in SQL
   
   ✅ CORRECT:
   WHERE State = ? AND Crop = ?
   Parameters: ["Assam", "Rice"]
   
   ❌ WRONG:
   WHERE State = Assam AND Crop = Rice  (missing quotes, will fail!)
   WHERE State = 'assam' AND Crop = 'rice'  (wrong case, will fail!)

2. **Parameter Casing** (Python will auto-correct these):
   # MODIFIED: Changed District to State and UPPERCASE to Title Case
   - States: Provide in ANY case → Python converts to Title Case
   - Crops: Provide in ANY case → Python converts to Title Case
   - Years: Numbers, no conversion needed

3. **For "last N years"**: 
   - Calculate from max year: {self.metadata.tables_metadata[relevant_tables[0]].date_range[1] if relevant_tables else 'unknown'}
   - Example: "last 5 years" from 2018 → years >= 2014
   - Use: WHERE Crop_Year >= ? with parameter [2014]

4. **Column names**: Use exact names from schema (case-sensitive): {self.metadata.tables_metadata[relevant_tables[0]].columns if relevant_tables else []}

5. **Aggregations**: Use appropriate SQL functions (SUM, AVG, MAX, MIN, COUNT)

6. **Single table**: All queries should target the 'crop_yield' table.

JSON Response:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            plans = []
            
            for plan_spec in result.get('query_plans', []):
                sql = plan_spec['sql']
                
                # VALIDATE: Check for unquoted string literals (common LLM mistake)
                if self._has_unquoted_literals(sql):
                    st.session_state.logs.append(
                        f"⚠️ Warning: Query has unquoted literals, likely will fail: {sql[:100]}"
                    )
                
                plans.append(QueryPlan(
                    sql_query=sql,
                    parameters=plan_spec.get('parameters', []),
                    target_table=plan_spec['target_table'],
                    intent=intent,
                    expected_columns=plan_spec.get('expected_columns', [])
                ))
                st.session_state.logs.append(
                    f"✓ Generated plan for '{plan_spec['target_table']}': {sql[:80]}..."
                )
            
            return plans
        except Exception as e:
            st.session_state.logs.append(f"❌ Query planning failed: {e}")
            logging.error(f"Query planning error: {e}")
            return []
    
    def _has_unquoted_literals(self, sql: str) -> bool:
        """Detect if SQL has unquoted string literals (common error)"""
        sql_upper = sql.upper()
        
        import re
        
        # Pattern: = followed by uppercase word without quotes
        pattern = r'=\s*([A-Z][A-Z_]+)(?:\s|$|AND|OR)'
        matches = re.findall(pattern, sql_upper)
        
        # Filter out SQL keywords
        sql_keywords = {'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'NULL', 
                        'TRUE', 'FALSE', 'ASC', 'DESC', 'LIMIT', 'OFFSET'}
        
        suspicious = [m for m in matches if m not in sql_keywords]
        
        return len(suspicious) > 0

# --- 4. Data Execution Layer ---
class DataExecutor:
    """Execute query plans with validation and error handling"""
    
    def __init__(self, db_path: str, data_sources: Dict):
        self.db_path = db_path
        self.data_sources = data_sources
    
    def execute_plans(self, plans: List[QueryPlan]) -> List[ExecutionResult]:
        """Stage 3: Execute query plans and collect results"""
        st.session_state.logs.append(f"⚙️ Stage 3: Executing {len(plans)} query plans...")
        
        results = []
        
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                for i, plan in enumerate(plans):
                    start_time = time.time()
                    
                    # Correct parameter casing
                    corrected_params = self._correct_parameters(plan.sql_query, plan.parameters)
                    
                    st.session_state.logs.append(
                        f"Executing plan {i+1}: {plan.sql_query[:80]}... | Params: {corrected_params}"
                    )
                    
                    # Execute query
                    df = pd.read_sql_query(plan.sql_query, conn, params=corrected_params)
                    execution_time = time.time() - start_time
                    
                    # Build provenance metadata
                    source_info = self.data_sources.get(plan.target_table, {})
                    
                    result = ExecutionResult(
                        data=df,
                        query_plan=plan,
                        execution_time=execution_time,
                        row_count=len(df),
                        source_metadata={
                            'table': plan.target_table,
                            'url': source_info.get('url', ''),
                            'file': source_info.get('file', ''),
                            'query': plan.sql_query,
                            'parameters': corrected_params
                        }
                    )
                    
                    results.append(result)
                    st.session_state.logs.append(
                        f"✓ Plan {i+1} executed: {len(df)} rows in {execution_time:.3f}s"
                    )
                    
        except Exception as e:
            st.session_state.logs.append(f"❌ Execution error: {e}")
            logging.error(f"Data execution error: {e}")
        
        return results
    
    def _correct_parameters(self, sql: str, params: List[Any]) -> List[Any]:
        """Apply case corrections based on column context in SQL"""
        if not params:
            return []
        
        corrected = []
        sql_lower = sql.lower()
        
        for i, p in enumerate(params):
            if not isinstance(p, str):
                corrected.append(p)
                continue
            
            # MODIFIED: Check for State column and use .title()
            if any(state_indicator in sql_lower for state_indicator in 
                   ['state = ?', 'state=?', 'state in (?', 'state_name = ?',
                    'district = ?', 'district=?', 'district in (?', 'district_name = ?']):
                corrected.append(p.title())
                continue
            
            # Check if this param is for a crop column  
            if any(crop_indicator in sql_lower for crop_indicator in 
                   ['crop = ?', 'crop=?', 'crop in (?', 'crop_name = ?']):
                corrected.append(p.title())
                continue
            
            # Default: keep as-is for other strings (e.g., Season)
            corrected.append(p)
        
        return corrected

# --- 5. Answer Synthesis Layer ---
class AnswerSynthesizer:
    """Generate natural language answers with visualizations"""
    
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def synthesize(self, question: str, intent: QueryIntent, results: List[ExecutionResult]) -> Dict[str, Any]:
        """Stage 4: Synthesize answer from execution results"""
        st.session_state.logs.append("📝 Stage 4: Answer Synthesis...")
        
        # Build data context
        data_context = self._build_data_context(results)
        
        prompt = f"""
You are an expert agricultural data analyst for India.
Provide a comprehensive, data-driven answer based ONLY on the provided execution results.

USER QUESTION: "{question}"

QUERY INTENT: {intent.intent_type}
ENTITIES ANALYZED: {', '.join(intent.entities) if intent.entities else 'N/A'}
METRICS: {', '.join(intent.metrics) if intent.metrics else 'N/A'}

DATA RESULTS:
{data_context}

Generate a JSON response:
{{
    "answer": "Comprehensive markdown-formatted answer with insights",
    "key_findings": ["Finding 1", "Finding 2", "Finding 3"],
    "visualization": {{
        "result_index": 0,
        "type": "bar|line|scatter",
        "x": "column_name",
        "y": "column_name",
        "color": "optional_column",
        "title": "Chart title"
    }} or null,
    "limitations": "Any data limitations or caveats"
}}

INSTRUCTIONS:
1. Start with direct answer to the question
2. Include specific numbers and time periods from data
3. For trends: describe patterns, compare values
4. For correlations: mention relationships observed
5. For policy questions: provide data-backed recommendations
6. If data is insufficient, state what's missing (e.g., "Data only available until 2018")
7. Suggest visualization only if data supports it
8. Use markdown formatting: **bold**, *italic*, bullet points
9. Be precise with units (tonnes for Production, mm for Rainfall, hectares for Area)

JSON Response:
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            synthesis = json.loads(response.choices[0].message.content)
            st.session_state.logs.append("✓ Answer synthesized successfully")
            
            return synthesis
        except Exception as e:
            st.session_state.logs.append(f"❌ Synthesis error: {e}")
            logging.error(f"Answer synthesis error: {e}")
            return {
                "answer": "Unable to generate answer due to synthesis error.",
                "key_findings": [],
                "visualization": None,
                "limitations": str(e)
            }
    
    def _build_data_context(self, results: List[ExecutionResult]) -> str:
        """Format execution results for LLM context"""
        context = ""
        
        for i, result in enumerate(results):
            df = result.data
            context += f"\n--- Result {i+1} (from {result.source_metadata['table']}) ---\n"
            context += f"Rows: {result.row_count} | Execution time: {result.execution_time:.3f}s\n"
            
            if df.empty:
                context += "[No data returned]\n"
            else:
                # Show summary statistics for numeric columns
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    context += "\nSummary Statistics:\n"
                    context += df[numeric_cols].describe().to_string() + "\n"
                
                # Show sample rows
                display_rows = min(len(df), 10)
                context += f"\nFirst {display_rows} rows:\n"
                context += df.head(display_rows).to_csv(index=False) + "\n"
        
        return context

# --- 6. Citation & Provenance Layer ---
class ProvenanceTracker:
    """Track and format data provenance for transparency"""
    
    @staticmethod
    def generate_citations(results: List[ExecutionResult]) -> Dict[str, Any]:
        """Generate citation information from execution results"""
        citations = {
            "sources": [],
            "queries": [],
            "data_lineage": []
        }
        
        for i, result in enumerate(results):
            # Source attribution
            source_info = {
                "table": result.source_metadata['table'],
                "url": result.source_metadata['url'],
                "file": result.source_metadata['file'],
                "rows_retrieved": result.row_count
            }
            if source_info not in citations["sources"]:
                citations["sources"].append(source_info)
            
            # Query provenance
            citations["queries"].append({
                "query_id": i + 1,
                "sql": result.source_metadata['query'],
                "parameters": result.source_metadata['parameters'],
                "execution_time": f"{result.execution_time:.3f}s",
                "rows_returned": result.row_count
            })
            
            # Data lineage
            citations["data_lineage"].append({
                "result_id": i + 1,
                "table": result.source_metadata['table'],
                "intent": result.query_plan.intent.intent_type
            })
        
        return citations

# --- Main Application ---
def initialize_groq_client():
    """Initialize Groq LLM client"""
    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY not found in environment. Please set this environment variable to run the application.")
        st.stop()
    
    try:
        client = Groq()
        # MODIFIED: Changed model to a recommended Llama 3 model
        model = "llama-3.3-70b-versatile" 
        logging.info("Groq client initialized")
        return client, model
    except Exception as e:
        st.error(f"Failed to initialize Groq: {e}")
        st.stop()

def main():
    st.title("🌾 Project Samarth - Enhanced QAS (crop_yield.csv)")
    st.subheader("Multi-Stage Query Understanding → Planning → Execution → Synthesis Pipeline")
    
    # Initialize session state
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    # MODIFIED: Check for local database file
    if not os.path.exists(DB_PATH):
        st.error(f"Database file not found: {DB_PATH}")
        st.error("Please download the 'crop_yield.db' file I provided and place it in the same directory as this script.")
        st.stop()
    
    # Initialize components
    client, model = initialize_groq_client()
    
    metadata_store = MetadataStore(DB_PATH, DATA_SOURCES_MAP)
    query_understanding = QueryUnderstanding(client, model, metadata_store)
    query_planner = QueryPlanner(client, model, metadata_store)
    data_executor = DataExecutor(DB_PATH, DATA_SOURCES_MAP)
    answer_synthesizer = AnswerSynthesizer(client, model, metadata_store)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Sample Questions")
        
        # MODIFIED: Sample questions updated to use States (not Districts) and match the new schema
        samples = {
            "Compare States": "Compare rice production in Assam and Odisha over last 5 years",
            "Find Maximum": "Which state had highest wheat production in 2014?",
            "Trend Analysis": "Analyze wheat production trend in Assam for last 10 years",
            "Correlation": "How does annual rainfall correlate with rice production in Odisha?",
            "Policy Insight": "Which crops have the highest yield in Assam?"
        }
        
        for label, question in samples.items():
            if st.button(label, help=question):
                st.session_state['question'] = question
                st.rerun()
        
        st.divider()
        st.header("🗄️ System Status")
        st.success("✓ Database Connected")
        for table_name, meta in metadata_store.tables_metadata.items():
            st.info(f"{table_name}: {meta.date_range[0]}-{meta.date_range[1]}")
        
        with st.expander("View Metadata"):
            for table_name in metadata_store.tables_metadata:
                st.text(metadata_store.get_table_summary(table_name))
    
    # Main interface
    question = st.text_area(
        "Ask your agricultural data question:",
        value=st.session_state.get('question', ''),
        height=100,
        key='question'
    )
    
    if st.button("🔍 Analyze", type="primary"):
        if not question.strip():
            st.warning("Please enter a question")
            return
        
        st.session_state.logs = []
        
        with st.spinner("Processing your query through 4-stage pipeline..."):
            # Stage 1: Query Understanding
            intent = query_understanding.parse_query(question)
            
            # Stage 2: Query Planning
            plans = query_planner.generate_plans(intent, question)
            
            # Stage 3: Data Execution
            if plans:
                results = data_executor.execute_plans(plans)
            else:
                results = []
            
            # Stage 4: Answer Synthesis
            if results and not all(r.data.empty for r in results):
                synthesis = answer_synthesizer.synthesize(question, intent, results)
                citations = ProvenanceTracker.generate_citations(results)
            elif not plans:
                 synthesis = {"answer": "I was unable to create a data retrieval plan for that question.", "key_findings": [], "visualization": None}
                 citations = {}
            else:
                synthesis = {"answer": "I found no data matching your query.", "key_findings": [], "visualization": None}
                citations = {}
        
        st.divider()
        
        # Display results
        if synthesis.get('answer'):
            st.header("🤖 Answer")
            st.markdown(synthesis['answer'])
            
            if synthesis.get('key_findings'):
                st.subheader("🔑 Key Findings")
                for finding in synthesis['key_findings']:
                    st.markdown(f"- {finding}")
        
        # Visualization
        if synthesis.get('visualization') and results:
            st.header("📊 Visualization")
            viz = synthesis['visualization']
            result_idx = viz.get('result_index', 0)
            
            if result_idx < len(results):
                df = results[result_idx].data
                
                if not df.empty:
                    try:
                        plot_func = {
                            'bar': px.bar,
                            'line': px.line,
                            'scatter': px.scatter
                        }.get(viz['type'])
                        
                        if plot_func:
                            fig = plot_func(
                                df,
                                x=viz['x'],
                                y=viz['y'],
                                color=viz.get('color'),
                                title=viz['title']
                            )
                            st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.error(f"Visualization error: {e}")
        
        # Citations & Provenance
        if citations:
            st.header("📚 Data Sources & Provenance")
            
            for source in citations['sources']:
                st.markdown(f"**Table:** {source['table']} ({source['rows_retrieved']} rows)")
                st.markdown(f"**Source:** {source['url']}")
                st.markdown(f"**File:** `{source['file']}`")
                st.divider()
            
            with st.expander("View SQL Queries Executed"):
                for query_info in citations['queries']:
                    st.subheader(f"Query {query_info['query_id']}")
                    st.code(query_info['sql'], language='sql')
                    st.write(f"**Parameters:** {query_info['parameters']}")
                    st.write(f"**Execution Time:** {query_info['execution_time']}")
                    st.write(f"**Rows:** {query_info['rows_returned']}")
        
        # Raw data
        if results:
            with st.expander("🔍 View Retrieved Data"):
                for i, result in enumerate(results):
                    st.subheader(f"Result {i+1}: {result.source_metadata['table']}")
                    if result.data.empty:
                        st.write("No data")
                    else:
                        st.dataframe(result.data)
        
        # System logs
        with st.expander("🔧 System Logs"):
            st.code("\n".join(st.session_state.logs))

if __name__ == "__main__":
    main()