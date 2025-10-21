from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class CropProduction(Base):
    __tablename__ = "crop_production"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    crop_year = Column(Integer, nullable=False, index=True)
    season = Column(String(50), nullable=False)
    crop = Column(String(100), nullable=False, index=True)
    area = Column(Float, nullable=True)  # Area in hectares
    production = Column(Float, nullable=True)  # Production in tonnes
    source_url = Column(Text, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class Rainfall(Base):
    __tablename__ = "rainfall"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(100), nullable=False, index=True)
    district = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    avg_rainfall = Column(Float, nullable=True)  # Rainfall in mm
    agency_name = Column(String(200), nullable=True)
    source_url = Column(Text, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataCacheMetadata(Base):
    __tablename__ = "data_cache_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    data_source = Column(String(100), nullable=False, unique=True)
    last_sync = Column(DateTime, nullable=True)
    total_records = Column(Integer, default=0)
    source_url = Column(Text, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/samarth.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
