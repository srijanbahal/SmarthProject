# 🌾 Project Samarth - Enhanced Agricultural Query & Analysis System

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

> **A sophisticated multi-stage AI-powered system for natural language agricultural data analysis**

Project Samarth enables non-technical users to query complex agricultural datasets using natural language. It leverages LLM-powered query understanding, automatic SQL generation, and intelligent answer synthesis to provide comprehensive insights with full data provenance.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Data Schema](#data-schema)
- [Contributing](#contributing)

---

## 🎯 Overview

Project Samarth transforms natural language questions into actionable agricultural insights through a **4-stage processing pipeline**:

1. **Query Understanding**: Extract intent, entities, and metrics from user questions
2. **Query Planning**: Generate optimized SQL queries with parameterization
3. **Data Execution**: Execute queries with provenance tracking
4. **Answer Synthesis**: Create natural language answers with visualizations

### Sample Questions
- *"Compare rice production in Assam and Odisha over last 5 years"*
- *"Which state had highest wheat production in 2014?"*
- *"How does annual rainfall correlate with rice production?"*
- *"Analyze wheat production trend in Assam for last 10 years"*

---

## 🏗️ Architecture

<div align="center">

![Project Samarth Architecture](https://raw.githubusercontent.com/srijanbahal/SmarthProject/master/architecture.png)

</div>

### System Architecture Overview

The system follows a **5-layer architecture** with clear separation of concerns:

#### **Layer 1: User Interface (React Frontend)** 🎨
Modern, responsive React application with:
- **Query Input**: Natural language text area for user questions
- **Sample Questions**: AI-generated question suggestions with refresh capability
- **Visualizations**: Interactive charts (Bar, Line, Scatter) using Recharts
- **Results Display**: Expandable sections for answers, findings, citations, and raw data

**Tech Stack**: React, Recharts, Lucide Icons, Tailwind CSS (inline)

#### **Layer 2: API Gateway (FastAPI Backend)** 🚀
RESTful API serving as the communication layer:
- **Endpoints**: `/query`, `/metadata`, `/generate-sample-questions`, `/health`
- **CORS Support**: Enables cross-origin requests from React frontend
- **Request Validation**: Pydantic models for type safety
- **Response Formatting**: Structured JSON responses

**Tech Stack**: FastAPI, Uvicorn, Pydantic

#### **Layer 3: Query Processing Pipeline** 🧠
Multi-stage intelligent processing system:

**Stage 1: Query Understanding**
```
Input: "Compare rice production in Assam and Odisha"
↓
LLM Analysis:
├─ Intent Type: compare
├─ Entities: [Assam, Odisha]
├─ Metrics: [production]
└─ Temporal Scope: last 5 years
```

**Stage 2: Query Planning**
```
Intent → SQL Generation
↓
SELECT State, Crop_Year, SUM(Production) as Total_Production
FROM crop_yield
WHERE State IN (?, ?) AND Crop = ?
GROUP BY State, Crop_Year
↓
Parameters: ['Assam', 'Odisha', 'Rice']
```

**Stage 3: Data Execution**
```
SQL Query + Parameters → SQLite Execution
↓
Result: DataFrame with production data
↓
Metadata: execution_time, row_count, provenance
```

**Stage 4: Answer Synthesis**
```
Raw Data → LLM Analysis
↓
Output:
├─ Natural Language Answer
├─ Key Findings (3-5 bullet points)
├─ Visualization Spec (chart type, axes)
└─ Citations & Limitations
```

**Tech Stack**: Groq API (Llama 3.3-70B), Pandas, Custom Pipeline Classes

#### **Layer 4: Data Storage** 💾
Persistent data management:
- **SQLite Database**: `crop_yield.db` containing agricultural statistics (1997-2018)
  - 11 columns: State, Crop, Year, Season, Area, Production, Rainfall, etc.
  - ~100K+ records of state-wise crop data
- **Metadata Store**: In-memory cache of schema information, sample data, and statistics

**Tech Stack**: SQLite3, Pandas

#### **Layer 5: External Services** ☁️
Third-party integrations:
- **Groq API**: Hosted Llama 3.3-70B Versatile model
  - JSON mode for structured outputs
  - Temperature control (0.0 for SQL, 0.8 for questions)
  - Fallback error handling

**Tech Stack**: Groq Python SDK

---

## ✨ Features

### 🤖 AI-Powered Capabilities

| Feature | Description |
|---------|-------------|
| **Natural Language Understanding** | Ask questions in plain English without SQL knowledge |
| **Intent Recognition** | Automatically identifies if you want to compare, analyze, correlate, or find extremes |
| **Smart SQL Generation** | Converts natural language to optimized parameterized SQL queries |
| **Dynamic Question Generator** | LLM creates fresh, contextual sample questions from your actual data |
| **Answer Synthesis** | Transforms raw data into human-readable insights with markdown formatting |

### 📊 Data Analysis Features

- **Multi-metric Analysis**: Production, rainfall, area, yield, fertilizer, pesticide
- **Temporal Analysis**: Trends over time, year-over-year comparisons, last N years
- **Correlation Detection**: Identify relationships between metrics (e.g., rainfall vs yield)
- **Geographic Comparisons**: State-wise and regional analysis across India
- **Aggregate Functions**: SUM, AVG, MAX, MIN, COUNT operations
- **Filtering & Grouping**: By state, crop, year, season

### 🎨 Visualization

- **Automatic Chart Selection**: System recommends bar/line/scatter based on data type
- **Interactive Recharts**: 
  - Hover tooltips with detailed values
  - Responsive design (mobile, tablet, desktop)
  - Custom color schemes (purple gradient theme)
- **Data-driven Insights**: Visual highlighting of trends and anomalies

### 🔍 Transparency & Provenance

Every query response includes:
- **Source Attribution**: Which tables/files data came from
- **SQL Query Display**: Exact queries executed with parameters
- **Execution Metrics**: Query time, rows retrieved, caching info
- **Raw Data Access**: View the underlying data tables
- **System Logs**: Complete pipeline execution trace

### 💅 Modern UI/UX

- **Gradient Design**: Pastel purple/indigo/pink color scheme
- **Dark Mode Support**: Automatic system preference detection
- **Responsive Layout**: Optimized for mobile (320px+), tablet, desktop
- **Loading States**: Skeleton screens and spinners during API calls
- **Collapsible Sections**: Organized accordion UI for better readability
- **Smooth Animations**: Hover effects, transitions, fade-ins
- **Accessibility**: ARIA labels, keyboard navigation, proper contrast ratios

---

## 🛠️ Technology Stack

### Backend Technologies

```python
# Core Framework
FastAPI           # Modern async web framework
Uvicorn          # ASGI server
Pydantic         # Data validation

# Data Processing
Pandas           # Data manipulation and analysis
SQLite3          # Embedded database

# AI/ML
Groq             # LLM API client
Python 3.8+      # Programming language

# Utilities
Logging          # Application logging
JSON             # Data serialization
Dataclasses      # Structured data types
```

### Frontend Technologies

```javascript
// Core Libraries
React 18+        // UI library
JavaScript ES6+  // Programming language

// Visualization
Recharts         // Charting library (Bar, Line, Scatter)

// UI Components
Lucide React     // Icon library (200+ icons)
Custom CSS       // Tailwind-style utility classes

// State Management
React Hooks      // useState, useEffect

// HTTP Client
Fetch API        // Native browser API
```

### Data & AI Stack

- **LLM**: Llama 3.3-70B Versatile (via Groq)
- **Database**: SQLite 3.x
- **Data Format**: JSON for API, CSV for source data
- **Query Language**: SQL with parameterization

---

## 📦 Installation

### Prerequisites

Ensure you have the following installed:

- **Python**: 3.8 or higher
- **Node.js**: 14.x or higher
- **npm** or **yarn**: Latest version
- **Groq API Key**: Sign up at [groq.com](https://groq.com)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/project-samarth.git
cd project-samarth
```

### Step 2: Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install fastapi uvicorn groq pandas plotly pydantic python-multipart

# Create data directory
mkdir -p data

# Place your crop_yield.db file in the data directory
# (Ensure the database file is in ./data/crop_yield.db)
```

### Step 3: Environment Variables

Create a `.env` file in the root directory:

```bash
# .env file
GROQ_API_KEY=your_groq_api_key_here
```

Or export directly:

```bash
# On macOS/Linux:
export GROQ_API_KEY="your_groq_api_key_here"

# On Windows (CMD):
set GROQ_API_KEY=your_groq_api_key_here

# On Windows (PowerShell):
$env:GROQ_API_KEY="your_groq_api_key_here"
```

### Step 4: Frontend Setup

```bash
# Create React app
npx create-react-app project-samarth-frontend
cd project-samarth-frontend

# Install dependencies
npm install recharts lucide-react

# Replace src/App.jsx with the provided React code
# Copy the App.jsx content to src/App.jsx

# Optional: Update src/index.css for global styles
```

### Step 5: Verify Installation

**Backend**:
```bash
python main.py
# Should output: INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend**:
```bash
npm start
# Should open browser at http://localhost:3000
```

---

## 🚀 Usage

### Starting the Application

#### Terminal 1 (Backend):
```bash
cd project-samarth
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```
✅ Backend running at: `http://localhost:8000`

#### Terminal 2 (Frontend):
```bash
cd project-samarth-frontend
npm start
```
✅ Frontend running at: `http://localhost:3000`

### Using the Interface

#### 1️⃣ **Ask Questions**

**Option A**: Type your own question
```
Type: "What are the top 5 crops by production in Kerala in 2015?"
Click: "Analyze Query" button
```

**Option B**: Use sample questions
```
Click any sample question button in the sidebar
Question automatically loads and generates new suggestions
```

#### 2️⃣ **View Results**

The response includes multiple sections:

**Answer Section** (Always visible)
- Natural language explanation
- Markdown formatted with bold, italics
- Data-backed insights

**Key Findings** (Expandable)
- 3-5 bullet points summarizing important discoveries
- Numbered list with gradient badges

**Visualization** (Expandable)
- Interactive chart (bar/line/scatter)
- Hover tooltips
- Responsive to screen size

**Data Sources & Provenance** (Expandable)
- Table names and file sources
- Number of rows retrieved
- Source URLs (if applicable)

**SQL Queries Executed** (Expandable)
- Syntax-highlighted SQL code
- Parameters used
- Execution time and row count

**Retrieved Data** (Expandable)
- Raw data tables
- Sortable columns
- First 10 rows preview

**System Logs** (Expandable)
- Pipeline execution trace
- Stage-by-stage progress
- Error messages (if any)

#### 3️⃣ **Generate New Questions**

**Manual Refresh**:
```
Click "✨ Refresh" button in sidebar
→ LLM generates 5 new questions from your data
→ Questions appear in ~2-3 seconds
```

**Auto Refresh**:
```
Click any sample question
→ Question loads to input
→ New questions automatically generate in background
→ Sidebar updates with fresh suggestions
```

### Example Workflow

```
1. User clicks: "Compare States"
   ↓
2. Question loads: "Compare rice production in Assam and Odisha..."
   ↓
3. New questions generate automatically
   ↓
4. User clicks "Analyze Query"
   ↓
5. Backend processes through 4 stages
   ↓
6. Results appear with:
   - Natural language answer
   - Bar chart comparing states
   - Citations to data sources
   - SQL query that was executed
```

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### `GET /`
Health check and API information

**Response:**
```json
{
  "message": "Project Samarth API",
  "version": "1.0.0"
}
```

---

#### `GET /health`
System health status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

#### `GET /metadata`
Database schema and table information

**Response:**
```json
{
  "tables": {
    "crop_yield": {
      "name": "crop_yield",
      "columns": [
        "State", "Crop", "Crop_Year", "Season", 
        "Area", "Production", "Annual_Rainfall", 
        "Fertilizer", "Pesticide", "Yield"
      ],
      "date_range": [1997, 2018],
      "description": "State-wise, season-wise crop production statistics",
      "key_columns": {
        "state": ["State"],
        "crop": ["Crop"],
        "year": ["Crop_Year"],
        "metrics": ["Area", "Production", "Yield"]
      },
      "sample_rows": [
        {
          "State": "Assam",
          "Crop": "Rice",
          "Crop_Year": 2015,
          "Production": 4500000
        }
      ]
    }
  },
  "status": "success"
}
```

---

#### `GET /sample-questions`
Get default sample questions

**Response:**
```json
{
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
```

---

#### `POST /generate-sample-questions`
Generate new AI-powered sample questions

**Request:** Empty body
```json
{}
```

**Response:**
```json
{
  "questions": [
    {
      "label": "Seasonal Comparison",
      "question": "Compare Kharif and Rabi season yields for wheat in Punjab"
    },
    {
      "label": "Pesticide Impact",
      "question": "How does pesticide usage affect cotton production in Gujarat?"
    },
    {
      "label": "Multi-State Analysis",
      "question": "Which states show declining rice yields from 2010-2018?"
    },
    {
      "label": "Fertilizer Efficiency",
      "question": "What is the relationship between fertilizer and production in Kerala?"
    },
    {
      "label": "Best Practices",
      "question": "Which state has the most sustainable farming practices for sugarcane?"
    }
  ]
}
```

---

#### `POST /query`
Process natural language query

**Request Body:**
```json
{
  "question": "Compare rice production in Assam and Odisha over last 5 years"
}
```

**Response:**
```json
{
  "answer": "Based on the data from 2014-2018, **Odisha significantly outproduces Assam in rice cultivation**. \n\nOdisha's rice production averages **7.2 million tonnes annually**, while Assam produces approximately **4.8 million tonnes**. This represents a **50% higher output** for Odisha.\n\n**Key trends observed:**\n- Odisha shows consistent growth with a 12% increase from 2014 to 2018\n- Assam's production remained relatively stable with minor fluctuations\n- Both states experienced peak production in 2017 due to favorable monsoons",
  
  "key_findings": [
    "Odisha produces 50% more rice than Assam on average (7.2M vs 4.8M tonnes)",
    "Odisha shows 12% growth from 2014-2018, while Assam remains stable",
    "Both states peaked in 2017, correlating with above-average rainfall",
    "Assam has higher yield per hectare (2.1 vs 1.8 tonnes/ha) despite lower total production"
  ],
  
  "visualization": {
    "result_index": 0,
    "type": "line",
    "x": "Crop_Year",
    "y": "Production",
    "color": "State",
    "title": "Rice Production Comparison: Assam vs Odisha (2014-2018)"
  },
  
  "limitations": "Data only available until 2018. Recent trends post-2018 are not reflected.",
  
  "citations": {
    "sources": [
      {
        "table": "crop_yield",
        "url": "N/A (Uploaded from crop_yield.csv)",
        "file": "crop_yield.csv",
        "rows_retrieved": 10
      }
    ],
    "queries": [
      {
        "query_id": 1,
        "sql": "SELECT State, Crop_Year, SUM(Production) as Total_Production FROM crop_yield WHERE State IN (?, ?) AND Crop = ? AND Crop_Year >= ? GROUP BY State, Crop_Year ORDER BY Crop_Year",
        "parameters": ["Assam", "Odisha", "Rice", 2014],
        "execution_time": "0.023s",
        "rows_returned": 10
      }
    ],
    "data_lineage": [
      {
        "result_id": 1,
        "table": "crop_yield",
        "intent": "compare"
      }
    ]
  },
  
  "results": [
    {
      "data": [
        {"State": "Assam", "Crop_Year": 2014, "Total_Production": 4650000},
        {"State": "Assam", "Crop_Year": 2015, "Total_Production": 4720000},
        {"State": "Odisha", "Crop_Year": 2014, "Total_Production": 6950000},
        {"State": "Odisha", "Crop_Year": 2015, "Total_Production": 7180000}
      ],
      "row_count": 10,
      "execution_time": 0.023,
      "source_metadata": {
        "table": "crop_yield",
        "query": "SELECT State, Crop_Year, ...",
        "parameters": ["Assam", "Odisha", "Rice", 2014]
      }
    }
  ],
  
  "logs": [
    "🧠 Stage 1: Query Understanding & Intent Extraction...",
    "Intent extracted: compare",
    "📋 Stage 2: Query Plan Generation...",
    "Relevant tables: ['crop_yield']",
    "✓ Generated plan for 'crop_yield': SELECT State, Crop_Year, SUM(Production)...",
    "⚙️ Stage 3: Executing 1 query plans...",
    "Executing plan 1: SELECT State, Crop_Year... | Params: ['Assam', 'Odisha', 'Rice', 2014]",
    "✓ Plan 1 executed: 10 rows in 0.023s",
    "📝 Stage 4: Answer Synthesis...",
    "✓ Answer synthesized successfully"
  ]
}
```

---

## 📁 Project Structure

```
project-samarth/
├── 📂 backend/
│   ├── 📄 main.py                      # FastAPI application entry point
│   ├── 📂 data/
│   │   └── 📊 crop_yield.db            # SQLite database (100K+ records)
│   ├── 📄 requirements.txt             # Python dependencies
│   └── 📄 .env                         # Environment variables (GROQ_API_KEY)
│
├── 📂 frontend/
│   ├── 📂 public/
│   │   ├── 📄 index.html
│   │   └── 🎨 favicon.ico
│   ├── 📂 src/
│   │   ├── 📄 App.jsx                  # Main React component (1000+ lines)
│   │   ├── 📄 index.js                 # React entry point
│   │   ├── 📄 index.css                # Global styles
│   │   └── 📄 App.test.js              # Unit tests
│   ├── 📄 package.json                 # Node dependencies
│   └── 📄 package-lock.json
│
├── 🎨 architecture.svg                 # System architecture diagram
├── 📖 README.md                        # This file (comprehensive documentation)
├── 📄 .gitignore                       # Git ignore rules
└── 📜 LICENSE                          # Project license
```

### Key Files Description

| File | Purpose | Lines of Code |
|------|---------|---------------|
| `main.py` | FastAPI backend with all business logic | ~800 |
| `App.jsx` | React frontend with complete UI | ~600 |
| `crop_yield.db` | SQLite database with agricultural data | 100K+ records |
| `architecture.svg` | Visual system architecture | SVG diagram |
| `README.md` | Complete project documentation | This file |

---

## 📊 Data Schema

### `crop_yield` Table

The core database table containing agricultural statistics:

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `State` | TEXT | State name (Title Case) | `"Assam"`, `"Punjab"` |
| `Crop` | TEXT | Crop name (Title Case) | `"Rice"`, `"Wheat"` |
| `Crop_Year` | INTEGER | Year of cultivation | `2015`, `2018` |
| `Season` | TEXT | Growing season | `"Kharif"`, `"Rabi"`, `"Whole Year"` |
| `Area` | REAL | Cultivated area in hectares | `1250000.5` |
| `Production` | REAL | Total production in tonnes | `4500000.0` |
| `Annual_Rainfall` | REAL | Annual rainfall in mm | `1450.75` |
| `Fertilizer` | REAL | Fertilizer usage (kg/ha) | `125.5` |
| `Pesticide` | REAL | Pesticide usage (kg/ha) | `2.3` |
| `Yield` | REAL | Crop yield (tonnes/hectare) | `2.15` |

### Data Coverage

- **Time Period**: 1997 - 2018 (22 years)
- **Geographic Scope**: All major agricultural states in India
- **Crop Types**: 100+ different crops including:
  - **Cereals**: Rice, Wheat, Maize, Bajra, Jowar
  - **Pulses**: Arhar, Moong, Urad, Masoor, Gram
  - **Cash Crops**: Cotton, Sugarcane, Jute, Tea, Coffee
  - **Oilseeds**: Groundnut, Soybean, Sunflower, Mustard
  - **Spices**: Turmeric, Chili, Coriander, Cumin
  - **Fruits & Vegetables**: Various varieties

### Sample Data

```sql
SELECT * FROM crop_yield LIMIT 3;
```

| State | Crop | Crop_Year | Season | Area | Production | Annual_Rainfall | Fertilizer | Pesticide | Yield |
|-------|------|-----------|--------|------|------------|-----------------|------------|-----------|-------|
| Assam | Rice | 2015 | Kharif | 2200000 | 4650000 | 2450.5 | 85.2 | 1.8 | 2.11 |
| Punjab | Wheat | 2016 | Rabi | 3500000 | 16800000 | 650.3 | 165.8 | 3.2 | 4.80 |
| Gujarat | Cotton | 2017 | Kharif | 2650000 | 8200000 | 850.7 | 125.4 | 4.5 | 3.09 |

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

1. **Report Bugs**: Open an issue with bug details and reproduction steps
2. **Suggest Features**: Share ideas for new features or improvements
3. **Submit Pull Requests**: Fix bugs or implement new features
4. **Improve Documentation**: Help us make the docs clearer
5. **Share Use Cases**: Tell us how you're using Project Samarth

### Development Setup

```bash
# Fork the repository
git clone https://github.com/yourusername/project-samarth.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make your changes

# Run tests (if available)
python -m pytest tests/

# Commit with descriptive message
git commit -m "Add: feature description"

# Push to your fork
git push origin feature/your-feature-name

# Open a Pull Request
```

### Code Style

- **Python**: Follow PEP 8 guidelines
- **JavaScript**: Use ESLint with Airbnb config
- **Commits**: Use conventional commit messages
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation
  - `refactor:` for code refactoring
  - `test:` for adding tests

---

## 🔒 Security & Privacy

### Data Security

- **Read-Only Database**: SQLite opened in read-only mode (`?mode=ro`)
- **Parameterized Queries**: All SQL uses `?` placeholders to prevent injection
- **No User Data Storage**: No personally identifiable information collected
- **API Key Protection**: Groq API key stored in environment variables

### Best Practices

```python
# ✅ CORRECT: Parameterized query
query = "SELECT * FROM crop_yield WHERE State = ?"
params = [user_input]
pd.read_sql_query(query, conn, params=params)

# ❌ WRONG: String concatenation (vulnerable to injection)
query = f"SELECT * FROM crop_yield WHERE State = '{user_input}'"
```

### Privacy Considerations

- No user authentication required
- No query history stored
- No analytics or tracking
- CORS configured for localhost only (update for production)

---

## 📈 Performance Optimization

### Backend Optimizations

1. **Metadata Caching**: Schema loaded once at startup
2. **Connection Pooling**: SQLite connections reused
3. **Async Processing**: FastAPI handles concurrent requests
4. **Selective Data Loading**: Only requested columns retrieved

### Frontend Optimizations

1. **Code Splitting**: React lazy loading for large components
2. **Memoization**: React.memo for expensive components
3. **Debouncing**: Prevent excessive API calls
4. **Lazy Rendering**: Collapsible sections loaded on demand

### Typical Response Times

| Operation | Time |
|-----------|------|
| Simple lookup query | 50-200ms |
| Complex aggregation | 200-500ms |
| LLM processing | 1-3s |
| Question generation | 2-4s |
| Full pipeline (end-to-end) | 3-7s |

---

## 🐛 Troubleshooting

### Common Issues

#### Backend won't start
```bash
Error: GROQ_API_KEY not found

Solution:
export GROQ_API_KEY="your_key_here"
```

#### Frontend can't connect to backend
```bash
Error: CORS policy blocked

Solution:
1. Verify backend is running on port 8000
2. Check CORS settings in main.py
3. Ensure frontend uses http://localhost:8000
```

#### Database file not found
```bash
Error: Database file not found: ./data/crop_yield.db

Solution:
mkdir -p data
# Copy your database file to data/crop_yield.db
```

#### Sample questions not loading
```bash
Solution:
1. Check browser console for errors
2. Verify /sample-questions endpoint returns data
3. Fallback questions should load automatically
```

#### LLM responses fail
```bash
Error: 429 Too Many Requests

Solution:
1. Check Groq API rate limits
2. Verify API key is valid
3. Add retry logic with exponential backoff
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)
- [Groq API Reference](https://console.groq.com/docs)
- [Recharts Examples](https://recharts.org/en-US/examples)

### Related Projects
- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [Streamlit](https://streamlit.io/) - Alternative UI framework
- [Pandas](https://pandas.pydata.org/) - Data manipulation library

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 Project Samarth Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
