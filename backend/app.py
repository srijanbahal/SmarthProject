from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [API] - %(levelname)s - %(message)s')

# Configuration
DB_PATH = "../data/crop_yield.db"
DATA_SOURCES_MAP = {
    "crop_yield": {
        "url": "N/A (Uploaded from crop_yield.csv)",
        "file": "crop_yield.csv",
        "description": "State-wise, season-wise crop production statistics from 1997-2018, including Area, Production, Annual_Rainfall, Fertilizer, Pesticide, and Yield."
    }
}

# Initialize FastAPI
app = FastAPI(title="Project Samarth API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data Classes
@dataclass
class QueryIntent:
    intent_type: str
    entities: List[str]
    metrics: List[str]
    constraints: Dict[str, Any]
    temporal_scope: Optional[str] = None

@dataclass
class TableMetadata:
    name: str
    columns: List[str]
    sample_rows: Dict[str, Any]
    date_range: tuple
    description: str
    key_columns: Dict[str, List[str]]

@dataclass
class QueryPlan:
    sql_query: str
    parameters: List[Any]
    target_table: str
    intent: Dict[str, Any]
    expected_columns: List[str]

@dataclass
class ExecutionResult:
    data: Dict[str, Any]
    query_plan: Dict[str, Any]
    execution_time: float
    row_count: int
    source_metadata: Dict[str, Any]

# Request/Response Models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    key_findings: List[str]
    visualization: Optional[Dict[str, Any]]
    limitations: Optional[str]
    citations: Dict[str, Any]
    results: List[Dict[str, Any]]
    logs: List[str]

class MetadataResponse(BaseModel):
    tables: Dict[str, Dict[str, Any]]
    status: str

# Global instances
metadata_store = None
query_understanding = None
query_planner = None
data_executor = None
answer_synthesizer = None
logs = []

# Metadata Store Layer
class MetadataStore:
    def __init__(self, db_path: str, data_sources: Dict):
        self.db_path = db_path
        self.data_sources = data_sources
        self.tables_metadata: Dict[str, TableMetadata] = {}
        self._initialize_metadata()
    
    def _initialize_metadata(self):
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                for table_name, source_info in self.data_sources.items():
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    sample_df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
                    
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
                    
                    key_columns = {
                        'state': [c for c in columns if 'state' in c.lower()],
                        'crop': [c for c in columns if c.lower() == 'crop'],
                        'year': [c for c in columns if 'year' in c.lower()],
                        'metrics': [c for c in columns if any(m in c.lower() for m in ['production', 'rainfall', 'area', 'yield', 'fertilizer', 'pesticide'])]
                    }
                    
                    self.tables_metadata[table_name] = TableMetadata(
                        name=table_name,
                        columns=columns,
                        sample_rows=sample_df.to_dict('records'),
                        date_range=date_range,
                        description=source_info['description'],
                        key_columns=key_columns
                    )
                    
            logging.info(f"Metadata initialized for {len(self.tables_metadata)} tables")
        except Exception as e:
            logging.error(f"Metadata initialization failed: {e}")
    
    def get_table_summary(self, table_name: str) -> str:
        if table_name not in self.tables_metadata:
            return ""
        
        meta = self.tables_metadata[table_name]
        summary = f"""
Table: {meta.name}
Description: {meta.description}
Date Range: {meta.date_range[0]}-{meta.date_range[1]}
Columns: {', '.join(meta.columns)}
Key Entities: States={meta.key_columns['state']}, Metrics={meta.key_columns['metrics']}
"""
        return summary
    
    def get_relevant_tables(self, query: str) -> List[str]:
        return list(self.tables_metadata.keys())

# Query Understanding Layer
class QueryUnderstanding:
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def parse_query(self, question: str) -> QueryIntent:
        logs.append("🧠 Stage 1: Query Understanding & Intent Extraction...")
        
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
2. entities: Extract specific states, crops mentioned
3. metrics: What measurements are needed
4. constraints: Filters to apply
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
            logs.append(f"Intent extracted: {result.get('intent_type', 'unknown')}")
            
            return QueryIntent(
                intent_type=result.get('intent_type', 'lookup'),
                entities=result.get('entities', []),
                metrics=result.get('metrics', []),
                constraints=result.get('constraints', {}),
                temporal_scope=result.get('temporal_scope')
            )
        except Exception as e:
            logs.append(f"❌ Intent extraction failed: {e}")
            logging.error(f"Query understanding error: {e}")
            return QueryIntent('lookup', [], [], {})
    
    def _get_schema_context(self) -> str:
        context = ""
        for table_name, meta in self.metadata.tables_metadata.items():
            context += f"\n{table_name}: {meta.description} (Years: {meta.date_range[0]}-{meta.date_range[1]})"
        return context

# Query Planner Layer
class QueryPlanner:
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def _get_case_rules(self, table_name: str) -> str:
        if table_name not in self.metadata.tables_metadata:
            return ""
        
        meta = self.metadata.tables_metadata[table_name]
        rules = f"\nCASE SENSITIVITY RULES for {table_name}:\n"
        
        if not meta.sample_rows:
            return rules
        
        if meta.key_columns['state']:
            state_col = meta.key_columns['state'][0]
            sample_states = list(set([row.get(state_col) for row in meta.sample_rows[:3] if row.get(state_col)]))
            rules += f"- State values are Title Case: {sample_states}\n"
            rules += f"  → Use parameterized: WHERE {state_col} = ? with Title Case param\n"
        
        if meta.key_columns['crop']:
            crop_col = meta.key_columns['crop'][0]
            sample_crops = list(set([row.get(crop_col) for row in meta.sample_rows[:3] if row.get(crop_col)]))
            rules += f"- Crop values are Title Case: {sample_crops}\n"
            rules += f"  → Use parameterized: WHERE {crop_col} = ? with Title Case param\n"
        
        return rules
    
    def generate_plans(self, intent: QueryIntent, question: str) -> List[QueryPlan]:
        logs.append("📋 Stage 2: Query Plan Generation...")
        
        relevant_tables = self.metadata.get_relevant_tables(question)
        logs.append(f"Relevant tables: {relevant_tables}")
        
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

Generate a JSON list of SQL query specifications.

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

CRITICAL RULES:
1. ALWAYS use parameterized queries with ? placeholders
2. Parameter Casing: States and Crops in ANY case → Python converts to Title Case
3. For "last N years": Calculate from max year: {self.metadata.tables_metadata[relevant_tables[0]].date_range[1] if relevant_tables else 'unknown'}
4. Column names: Use exact names from schema: {self.metadata.tables_metadata[relevant_tables[0]].columns if relevant_tables else []}

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
                plans.append(QueryPlan(
                    sql_query=plan_spec['sql'],
                    parameters=plan_spec.get('parameters', []),
                    target_table=plan_spec['target_table'],
                    intent=asdict(intent),
                    expected_columns=plan_spec.get('expected_columns', [])
                ))
                logs.append(f"✓ Generated plan for '{plan_spec['target_table']}': {plan_spec['sql'][:80]}...")
            
            return plans
        except Exception as e:
            logs.append(f"❌ Query planning failed: {e}")
            logging.error(f"Query planning error: {e}")
            return []

# Data Executor Layer
class DataExecutor:
    def __init__(self, db_path: str, data_sources: Dict):
        self.db_path = db_path
        self.data_sources = data_sources
    
    def execute_plans(self, plans: List[QueryPlan]) -> List[ExecutionResult]:
        logs.append(f"⚙️ Stage 3: Executing {len(plans)} query plans...")
        
        results = []
        
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                for i, plan in enumerate(plans):
                    start_time = time.time()
                    
                    corrected_params = self._correct_parameters(plan.sql_query, plan.parameters)
                    
                    logs.append(f"Executing plan {i+1}: {plan.sql_query[:80]}... | Params: {corrected_params}")
                    
                    df = pd.read_sql_query(plan.sql_query, conn, params=corrected_params)
                    execution_time = time.time() - start_time
                    
                    source_info = self.data_sources.get(plan.target_table, {})
                    
                    result = ExecutionResult(
                        data=df.to_dict('records'),
                        query_plan=asdict(plan),
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
                    logs.append(f"✓ Plan {i+1} executed: {len(df)} rows in {execution_time:.3f}s")
                    
        except Exception as e:
            logs.append(f"❌ Execution error: {e}")
            logging.error(f"Data execution error: {e}")
        
        return results
    
    def _correct_parameters(self, sql: str, params: List[Any]) -> List[Any]:
        if not params:
            return []
        
        corrected = []
        sql_lower = sql.lower()
        
        for p in params:
            if not isinstance(p, str):
                corrected.append(p)
                continue
            
            if any(state_indicator in sql_lower for state_indicator in 
                   ['state = ?', 'state=?', 'state in (?', 'state_name = ?',
                    'district = ?', 'district=?', 'district in (?', 'district_name = ?']):
                corrected.append(p.title())
                continue
            
            if any(crop_indicator in sql_lower for crop_indicator in 
                   ['crop = ?', 'crop=?', 'crop in (?', 'crop_name = ?']):
                corrected.append(p.title())
                continue
            
            corrected.append(p)
        
        return corrected

# Answer Synthesizer Layer
class AnswerSynthesizer:
    def __init__(self, llm_client, model: str, metadata_store: MetadataStore):
        self.client = llm_client
        self.model = model
        self.metadata = metadata_store
    
    def synthesize(self, question: str, intent: QueryIntent, results: List[ExecutionResult]) -> Dict[str, Any]:
        logs.append("📝 Stage 4: Answer Synthesis...")
        
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
            logs.append("✓ Answer synthesized successfully")
            
            return synthesis
        except Exception as e:
            logs.append(f"❌ Synthesis error: {e}")
            logging.error(f"Answer synthesis error: {e}")
            return {
                "answer": "Unable to generate answer due to synthesis error.",
                "key_findings": [],
                "visualization": None,
                "limitations": str(e)
            }
    
    def _build_data_context(self, results: List[ExecutionResult]) -> str:
        context = ""
        
        for i, result in enumerate(results):
            data = result.data
            context += f"\n--- Result {i+1} (from {result.source_metadata['table']}) ---\n"
            context += f"Rows: {result.row_count} | Execution time: {result.execution_time:.3f}s\n"
            
            if not data:
                context += "[No data returned]\n"
            else:
                df = pd.DataFrame(data)
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    context += "\nSummary Statistics:\n"
                    context += df[numeric_cols].describe().to_string() + "\n"
                
                display_rows = min(len(df), 10)
                context += f"\nFirst {display_rows} rows:\n"
                context += df.head(display_rows).to_csv(index=False) + "\n"
        
        return context

# Provenance Tracker
class ProvenanceTracker:
    @staticmethod
    def generate_citations(results: List[ExecutionResult]) -> Dict[str, Any]:
        citations = {
            "sources": [],
            "queries": [],
            "data_lineage": []
        }
        
        for i, result in enumerate(results):
            source_info = {
                "table": result.source_metadata['table'],
                "url": result.source_metadata['url'],
                "file": result.source_metadata['file'],
                "rows_retrieved": result.row_count
            }
            if source_info not in citations["sources"]:
                citations["sources"].append(source_info)
            
            citations["queries"].append({
                "query_id": i + 1,
                "sql": result.source_metadata['query'],
                "parameters": result.source_metadata['parameters'],
                "execution_time": f"{result.execution_time:.3f}s",
                "rows_returned": result.row_count
            })
            
            citations["data_lineage"].append({
                "result_id": i + 1,
                "table": result.source_metadata['table'],
                "intent": result.query_plan['intent']['intent_type']
            })
        
        return citations

# Initialize components
def initialize_components():
    global metadata_store, query_understanding, query_planner, data_executor, answer_synthesizer
    
    if not os.getenv("GROQ_API_KEY"):
        raise Exception("GROQ_API_KEY not found in environment")
    
    client = Groq()
    model = "llama-3.3-70b-versatile"
    
    metadata_store = MetadataStore(DB_PATH, DATA_SOURCES_MAP)
    query_understanding = QueryUnderstanding(client, model, metadata_store)
    query_planner = QueryPlanner(client, model, metadata_store)
    data_executor = DataExecutor(DB_PATH, DATA_SOURCES_MAP)
    answer_synthesizer = AnswerSynthesizer(client, model, metadata_store)

# API Routes
@app.on_event("startup")
async def startup_event():
    if not os.path.exists(DB_PATH):
        logging.error(f"Database file not found: {DB_PATH}")
        raise Exception(f"Database file not found: {DB_PATH}")
    
    initialize_components()
    logging.info("API started successfully")

@app.get("/")
async def root():
    return {"message": "Project Samarth API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

@app.get("/metadata", response_model=MetadataResponse)
async def get_metadata():
    """Get database metadata and table information"""
    metadata = {}
    for table_name, meta in metadata_store.tables_metadata.items():
        metadata[table_name] = {
            "name": meta.name,
            "columns": meta.columns,
            "date_range": meta.date_range,
            "description": meta.description,
            "key_columns": meta.key_columns,
            "sample_rows": meta.sample_rows[:3]
        }
    
    return MetadataResponse(tables=metadata, status="success")

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language query"""
    global logs
    logs = []
    
    try:
        question = request.question.strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
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
        if results and not all(r.row_count == 0 for r in results):
            synthesis = answer_synthesizer.synthesize(question, intent, results)
            citations = ProvenanceTracker.generate_citations(results)
        elif not plans:
            synthesis = {
                "answer": "I was unable to create a data retrieval plan for that question.",
                "key_findings": [],
                "visualization": None,
                "limitations": "Query planning failed"
            }
            citations = {}
        else:
            synthesis = {
                "answer": "I found no data matching your query.",
                "key_findings": [],
                "visualization": None,
                "limitations": "No matching data found"
            }
            citations = {}
        
        # Prepare response
        results_data = [
            {
                "data": r.data,
                "row_count": r.row_count,
                "execution_time": r.execution_time,
                "source_metadata": r.source_metadata
            }
            for r in results
        ]
        
        return QueryResponse(
            answer=synthesis.get('answer', ''),
            key_findings=synthesis.get('key_findings', []),
            visualization=synthesis.get('visualization'),
            limitations=synthesis.get('limitations'),
            citations=citations,
            results=results_data,
            logs=logs
        )
        
    except Exception as e:
        logging.error(f"Query processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample-questions")
async def get_sample_questions():
    """Get sample questions for the UI"""
    return {
        "questions": [
            {
                "label": "Compare States",
                "question": "Compare rice production in Assam and Odisha over last 5 years"
            },
            {
                "label": "Find Maximum",
                "question": "Which state had highest wheat production in 2014?"
            },
            {
                "label": "Trend Analysis",
                "question": "Analyze wheat production trend in Assam for last 10 years"
            },
            {
                "label": "Correlation",
                "question": "How does annual rainfall correlate with rice production in Odisha?"
            },
            {
                "label": "Policy Insight",
                "question": "Which crops have the highest yield in Assam?"
            }
        ]
    }

@app.post("/generate-sample-questions")
async def generate_sample_questions():
    """Generate new sample questions using LLM"""
    try:
        if not metadata_store or not metadata_store.tables_metadata:
            raise HTTPException(status_code=500, detail="Metadata not initialized")
        logging.info("Generating new sample questions using LLM")
        # Get schema context
        schema_info = ""
        for table_name, meta in metadata_store.tables_metadata.items():
            schema_info += f"\nTable: {table_name}\n"
            schema_info += f"Columns: {', '.join(meta.columns)}\n"
            schema_info += f"Date Range: {meta.date_range[0]}-{meta.date_range[1]}\n"
            schema_info += f"Key States: {', '.join(list(set([row.get(meta.key_columns['state'][0]) for row in meta.sample_rows[:5] if meta.key_columns['state'] and row.get(meta.key_columns['state'][0])])))}\n"
            schema_info += f"Key Crops: {', '.join(list(set([row.get(meta.key_columns['crop'][0]) for row in meta.sample_rows[:5] if meta.key_columns['crop'] and row.get(meta.key_columns['crop'][0])])))}\n"
        
        client = Groq()
        model = "llama-3.3-70b-versatile"
        
        prompt = f"""You are an expert at generating insightful agricultural data analysis questions.

AVAILABLE DATABASE:
{schema_info}

Generate 5 diverse and interesting sample questions that users can ask about this agricultural data.
The questions should cover different types of analysis:
1. Comparison (compare entities)
2. Identification (find max/min/best)
3. Trend Analysis (analyze patterns over time)
4. Correlation (relationships between metrics)
5. Policy/Insights (actionable recommendations)

Make questions specific, using actual state names, crop names, and years from the data.
Make them varied and interesting - avoid repetitive patterns.

Respond with JSON in this exact format:
{{
    "questions": [
        {{
            "label": "Short category label (e.g., 'Compare Crops')",
            "question": "Full natural language question"
        }},
        ...
    ]
}}

JSON Response:"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Higher temperature for more variety
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        logging.info(f"Generated {len(result.get('questions', []))} new sample questions")
        
        return result
        
    except Exception as e:
        logging.error(f"Failed to generate sample questions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate questions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)