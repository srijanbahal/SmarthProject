# Project Samarth - Intelligent Agricultural Q&A System

An end-to-end intelligent Q&A system for agricultural and climate data from Uttar Pradesh, India. This system sources data directly from government portals and provides natural language answers with visualizations and citations.

## 🌟 Features

- **Natural Language Queries**: Ask complex questions about agricultural and climate data
- **Multi-Agent Architecture**: Specialized AI agents for query understanding, data retrieval, analysis, visualization, and response synthesis
- **Real-time Data**: Direct integration with data.gov.in APIs
- **Visualizations**: Interactive charts and graphs using Plotly
- **Citation System**: Complete traceability of data sources
- **Uttar Pradesh Focus**: Optimized for UP state agricultural data

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    FastAPI      │    │   SQLite DB     │
│   Frontend      │◄──►│    Backend      │◄──►│   + Cache       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Multi-Agent    │
                    │  LLM System     │
                    │  (Groq/Llama)   │
                    └─────────────────┘
```

### Multi-Agent System

1. **Query Understanding Agent**: Parses user questions and extracts entities
2. **Data Retrieval Agent**: Generates SQL queries and fetches data
3. **Analysis Agent**: Performs statistical analysis and correlations
4. **Visualization Agent**: Creates interactive charts and graphs
5. **Response Synthesis Agent**: Combines results with citations

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- API keys for:
  - Groq (for LLM)
  - data.gov.in (for crop and rainfall data)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd BharatFellowship
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Copy the template
cp env_template.txt .env

# Edit .env with your API keys
GROQ_API_KEY=your_groq_api_key_here
DATA_GOV_API_KEY_CROP=your_crop_api_key_here
DATA_GOV_API_KEY_RAINFALL=your_rainfall_api_key_here
DATABASE_URL=sqlite:///./data/samarth.db
CACHE_TTL_HOURS=24
LOG_LEVEL=INFO
```

4. **Initialize the database**
```bash
cd backend
python -c "from app.database.models import create_tables; create_tables()"
```

### Running the Application

1. **Start the FastAPI backend**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the Streamlit frontend** (in a new terminal)
```bash
cd frontend
streamlit run streamlit_app.py --server.port 8501
```

3. **Access the application**
- Frontend: http://localhost:8501
- API Documentation: http://localhost:8000/docs

## 📊 Sample Questions

The system can answer complex questions like:

1. **Comparative Analysis**: "Compare the average annual rainfall in Agra and Lucknow for the last 5 available years. In parallel, list the top 3 most produced crops by volume in each of those districts during the same period."

2. **District Comparison**: "Identify the district in Uttar Pradesh with the highest production of Rice in the most recent year available and compare that with the district with the lowest production of Rice."

3. **Trend Analysis**: "Analyze the production trend of Wheat in Uttar Pradesh over the last decade. Correlate this trend with the corresponding climate data for the same period."

4. **Policy Recommendations**: "A policy advisor is proposing a scheme to promote drought-resistant crops over water-intensive crops in Uttar Pradesh. Based on historical data from the last 5 years, what are the three most compelling data-backed arguments to support this policy?"

## 🔧 API Endpoints

### Core Endpoints

- `POST /api/query` - Main Q&A endpoint
- `GET /api/health` - System health check
- `GET /api/data/crops` - Get crop data with filters
- `GET /api/data/rainfall` - Get rainfall data with filters
- `POST /api/data/refresh` - Trigger data sync
- `GET /api/sources` - List all data sources

### Example API Usage

```python
import requests

# Ask a question
response = requests.post("http://localhost:8000/api/query", 
                        json={"question": "What are the top crops in Agra district?"})
result = response.json()

print(result["response"])
print(f"Confidence: {result['confidence_score']}")
```

## 🗄️ Database Schema

### Tables

- **crop_production**: State, District, Crop_Year, Season, Crop, Area, Production, source_url, last_updated
- **rainfall**: State, District, Date, Year, Month, Avg_rainfall, Agency_name, source_url, last_updated
- **data_cache_metadata**: Track data sync status and sources

## 🔄 Data Flow

1. **Data Ingestion**: Fetch data from data.gov.in APIs
2. **Filtering**: Filter for Uttar Pradesh data
3. **Storage**: Store in SQLite with caching
4. **Query Processing**: Multi-agent pipeline processes user questions
5. **Response Generation**: Natural language answers with visualizations and citations

## 🎯 Key Features

### Citation System
Every data point is traced back to its source with:
- Dataset name and description
- Original URL
- Access date
- Data quality metrics

### Visualization Types
- Bar charts for comparisons
- Line charts for trends
- Pie charts for distributions
- Correlation heatmaps
- District-wise maps

### Error Handling
- Graceful degradation when data is missing
- Clear error messages for users
- Fallback responses for incomplete data

## 🧪 Testing

### Test Sample Questions

```bash
# Test the system with sample questions
curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the top 3 crops in Uttar Pradesh?"}'
```

### Health Check

```bash
curl http://localhost:8000/api/health
```

## 📈 Performance

- **Response Time**: < 10 seconds for complex queries
- **Data Freshness**: Configurable cache TTL (default 24 hours)
- **Scalability**: SQLite for MVP, easily upgradeable to PostgreSQL
- **Accuracy**: Confidence scoring for all responses

## 🔒 Security & Privacy

- **Data Sovereignty**: All data processing happens locally
- **API Key Management**: Environment variable based configuration
- **No Data Persistence**: User queries are not stored
- **Source Attribution**: Complete data lineage tracking

## 🚀 Deployment

### Local Development
```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload

# Frontend  
cd frontend && streamlit run streamlit_app.py
```

### Production Deployment (Render)
1. Create `render.yaml` configuration
2. Set environment variables in Render dashboard
3. Deploy backend and frontend separately
4. Configure database (PostgreSQL recommended)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Data Sources**: Ministry of Agriculture & Farmers Welfare, India Meteorological Department
- **LLM Provider**: Groq for fast inference
- **Visualization**: Plotly for interactive charts
- **Framework**: FastAPI and Streamlit

## 📞 Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the health endpoint at `/api/health`
3. Check logs for detailed error information

---

**Project Samarth** - Empowering agricultural decision-making through intelligent data analysis.
