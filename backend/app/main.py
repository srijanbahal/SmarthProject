from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging
import os
from dotenv import load_dotenv

from .database.models import create_tables, get_db
from .services.data_ingestion import DataIngestionService
from .agents.agent_orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Project Samarth - Agricultural Q&A System",
    description="Intelligent Q&A system for agricultural and climate data from Uttar Pradesh",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    status: str
    question: str
    response: Optional[str] = None
    summary: Optional[Dict[str, Any]] = None
    citations: Optional[List[Dict[str, str]]] = None
    visualizations: Optional[List[Dict[str, Any]]] = None
    raw_data: Optional[Dict[str, Any]] = None
    confidence_score: Optional[float] = None
    processing_steps: Optional[Dict[str, str]] = None
    error: Optional[str] = None
    details: Optional[str] = None

class DataRefreshResponse(BaseModel):
    status: str
    message: str
    sources_updated: List[str]

class HealthResponse(BaseModel):
    status: str
    agents: Dict[str, str]
    database: str
    api_keys: Dict[str, bool]

# Initialize database tables
create_tables()

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Project Samarth API")
    
    # Check API keys
    groq_key = os.getenv("GROQ_API_KEY")
    crop_key = os.getenv("DATA_GOV_API_KEY_CROP")
    rainfall_key = os.getenv("DATA_GOV_API_KEY_RAINFALL")
    
    if not groq_key:
        logger.warning("GROQ_API_KEY not found in environment variables")
    if not crop_key:
        logger.warning("DATA_GOV_API_KEY_CROP not found in environment variables")
    if not rainfall_key:
        logger.warning("DATA_GOV_API_KEY_RAINFALL not found in environment variables")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Project Samarth - Agricultural Q&A System",
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        db_status = "disconnected"
    
    # Check API keys
    api_keys = {
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "crop_data": bool(os.getenv("DATA_GOV_API_KEY_CROP")),
        "rainfall_data": bool(os.getenv("DATA_GOV_API_KEY_RAINFALL"))
    }
    
    # Get agent status
    orchestrator = AgentOrchestrator(db)
    agents = orchestrator.get_agent_status()
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        agents=agents,
        database=db_status,
        api_keys=api_keys
    )

@app.post("/api/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Main Q&A endpoint"""
    try:
        orchestrator = AgentOrchestrator(db)
        result = await orchestrator.process_query(request.question)
        
        return QueryResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/crops")
async def get_crop_data(
    state: Optional[str] = None,
    district: Optional[str] = None,
    crop: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get crop production data with filters"""
    try:
        from .database.models import CropProduction
        
        query = db.query(CropProduction)
        
        if state:
            query = query.filter(CropProduction.state.ilike(f"%{state}%"))
        if district:
            query = query.filter(CropProduction.district.ilike(f"%{district}%"))
        if crop:
            query = query.filter(CropProduction.crop.ilike(f"%{crop}%"))
        if year:
            query = query.filter(CropProduction.crop_year == year)
        
        results = query.limit(limit).all()
        
        return {
            "status": "success",
            "data": [
                {
                    "state": r.state,
                    "district": r.district,
                    "crop_year": r.crop_year,
                    "season": r.season,
                    "crop": r.crop,
                    "area": r.area,
                    "production": r.production,
                    "source_url": r.source_url,
                    "last_updated": r.last_updated
                }
                for r in results
            ],
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error fetching crop data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/rainfall")
async def get_rainfall_data(
    state: Optional[str] = None,
    district: Optional[str] = None,
    year: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get rainfall data with filters"""
    try:
        from .database.models import Rainfall
        
        query = db.query(Rainfall)
        
        if state:
            query = query.filter(Rainfall.state.ilike(f"%{state}%"))
        if district:
            query = query.filter(Rainfall.district.ilike(f"%{district}%"))
        if year:
            query = query.filter(Rainfall.year == year)
        
        results = query.limit(limit).all()
        
        return {
            "status": "success",
            "data": [
                {
                    "state": r.state,
                    "district": r.district,
                    "date": r.date,
                    "year": r.year,
                    "month": r.month,
                    "avg_rainfall": r.avg_rainfall,
                    "agency_name": r.agency_name,
                    "source_url": r.source_url,
                    "last_updated": r.last_updated
                }
                for r in results
            ],
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error fetching rainfall data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/data/refresh", response_model=DataRefreshResponse)
async def refresh_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger data refresh from APIs"""
    try:
        ingestion_service = DataIngestionService(db)
        
        # Run data sync in background
        background_tasks.add_task(ingestion_service.sync_all_data)
        
        return DataRefreshResponse(
            status="success",
            message="Data refresh initiated in background",
            sources_updated=["crop_production", "rainfall"]
        )
        
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sources")
async def get_data_sources(db: Session = Depends(get_db)):
    """Get all data sources with metadata"""
    try:
        ingestion_service = DataIngestionService(db)
        sources = ingestion_service.get_data_sources()
        
        return {
            "status": "success",
            "sources": sources,
            "count": len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error fetching data sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
