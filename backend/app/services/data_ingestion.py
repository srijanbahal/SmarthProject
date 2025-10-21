import httpx
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Optional
import os
from ..database.models import CropProduction, Rainfall, DataCacheMetadata

logger = logging.getLogger(__name__)

class DataIngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.crop_api_key = os.getenv("DATA_GOV_API_KEY_CROP")
        self.rainfall_api_key = os.getenv("DATA_GOV_API_KEY_RAINFALL")
        
    async def fetch_crop_data(self, limit: int = 1000) -> List[Dict]:
        """Fetch crop production data from API and filter for UP"""
        try:
            async with httpx.AsyncClient() as client:
                # This is a placeholder URL - replace with actual data.gov.in API endpoint
                url = f"https://api.data.gov.in/resource/crop-production-data"
                params = {
                    "api-key": self.crop_api_key,
                    "format": "json",
                    "limit": limit,
                    "filters[state]": "Uttar Pradesh"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                records = data.get("records", [])
                
                # Filter for UP state
                up_records = [
                    record for record in records 
                    if record.get("state", "").lower() == "uttar pradesh"
                ]
                
                logger.info(f"Fetched {len(up_records)} UP crop records")
                return up_records
                
        except Exception as e:
            logger.error(f"Error fetching crop data: {e}")
            return []
    
    async def fetch_rainfall_data(self, limit: int = 1000) -> List[Dict]:
        """Fetch rainfall data from API and filter for UP"""
        try:
            async with httpx.AsyncClient() as client:
                # This is a placeholder URL - replace with actual data.gov.in API endpoint
                url = f"https://api.data.gov.in/resource/rainfall-data"
                params = {
                    "api-key": self.rainfall_api_key,
                    "format": "json",
                    "limit": limit,
                    "filters[state]": "Uttar Pradesh"
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                records = data.get("records", [])
                
                # Filter for UP state
                up_records = [
                    record for record in records 
                    if record.get("state", "").lower() == "uttar pradesh"
                ]
                
                logger.info(f"Fetched {len(up_records)} UP rainfall records")
                return up_records
                
        except Exception as e:
            logger.error(f"Error fetching rainfall data: {e}")
            return []
    
    def store_crop_data(self, records: List[Dict], source_url: str):
        """Store crop production data in database"""
        try:
            stored_count = 0
            for record in records:
                # Check if record already exists
                existing = self.db.query(CropProduction).filter(
                    CropProduction.state == record.get("state"),
                    CropProduction.district == record.get("district"),
                    CropProduction.crop_year == record.get("crop_year"),
                    CropProduction.season == record.get("season"),
                    CropProduction.crop == record.get("crop")
                ).first()
                
                if not existing:
                    crop_record = CropProduction(
                        state=record.get("state"),
                        district=record.get("district"),
                        crop_year=record.get("crop_year"),
                        season=record.get("season"),
                        crop=record.get("crop"),
                        area=record.get("area"),
                        production=record.get("production"),
                        source_url=source_url
                    )
                    self.db.add(crop_record)
                    stored_count += 1
            
            self.db.commit()
            logger.info(f"Stored {stored_count} new crop records")
            
            # Update metadata
            self._update_cache_metadata("crop_production", source_url, stored_count)
            
        except Exception as e:
            logger.error(f"Error storing crop data: {e}")
            self.db.rollback()
    
    def store_rainfall_data(self, records: List[Dict], source_url: str):
        """Store rainfall data in database"""
        try:
            stored_count = 0
            for record in records:
                # Parse date
                date_str = record.get("date")
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except:
                        date_obj = datetime.now()
                else:
                    date_obj = datetime.now()
                
                # Check if record already exists
                existing = self.db.query(Rainfall).filter(
                    Rainfall.state == record.get("state"),
                    Rainfall.district == record.get("district"),
                    Rainfall.date == date_obj
                ).first()
                
                if not existing:
                    rainfall_record = Rainfall(
                        state=record.get("state"),
                        district=record.get("district"),
                        date=date_obj,
                        year=record.get("year"),
                        month=record.get("month"),
                        avg_rainfall=record.get("avg_rainfall"),
                        agency_name=record.get("agency_name"),
                        source_url=source_url
                    )
                    self.db.add(rainfall_record)
                    stored_count += 1
            
            self.db.commit()
            logger.info(f"Stored {stored_count} new rainfall records")
            
            # Update metadata
            self._update_cache_metadata("rainfall", source_url, stored_count)
            
        except Exception as e:
            logger.error(f"Error storing rainfall data: {e}")
            self.db.rollback()
    
    def _update_cache_metadata(self, data_source: str, source_url: str, new_records: int):
        """Update cache metadata"""
        metadata = self.db.query(DataCacheMetadata).filter(
            DataCacheMetadata.data_source == data_source
        ).first()
        
        if metadata:
            metadata.last_sync = datetime.utcnow()
            metadata.total_records += new_records
            metadata.source_url = source_url
        else:
            metadata = DataCacheMetadata(
                data_source=data_source,
                last_sync=datetime.utcnow(),
                total_records=new_records,
                source_url=source_url
            )
            self.db.add(metadata)
        
        self.db.commit()
    
    async def sync_all_data(self):
        """Sync all data sources"""
        logger.info("Starting data sync...")
        # Try to load crop data from local CSV first
        crop_csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "..", "data", "crop_data_raw_UP.csv")
        # The above resolves to repository root; normalize path
        crop_csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "crop_data_raw_UP.csv"))

        crop_records = []
        if os.path.exists(crop_csv_path):
            try:
                df = pd.read_csv(crop_csv_path)
                # Convert DataFrame rows to dict records matching expected keys
                crop_records = df.where(pd.notnull(df), None).to_dict(orient="records")
                logger.info(f"Loaded {len(crop_records)} crop records from {crop_csv_path}")
                self.store_crop_data(crop_records, f"file://{crop_csv_path}")
            except Exception as e:
                logger.error(f"Error reading crop CSV {crop_csv_path}: {e}")
        else:
            # Fallback to API fetch
            crop_records = await self.fetch_crop_data()
            if crop_records:
                self.store_crop_data(crop_records, "https://api.data.gov.in/resource/crop-production-data")

        # Try to load rainfall data from local CSV first
        rainfall_csv_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "rainfall_data_raw_UP.csv"))

        rainfall_records = []
        if os.path.exists(rainfall_csv_path):
            try:
                df = pd.read_csv(rainfall_csv_path)
                rainfall_records = df.where(pd.notnull(df), None).to_dict(orient="records")
                logger.info(f"Loaded {len(rainfall_records)} rainfall records from {rainfall_csv_path}")
                # Normalize date column if present to ISO string or expected format
                for rec in rainfall_records:
                    if rec.get("date") and isinstance(rec.get("date"), str):
                        # keep as-is; store_rainfall_data will parse
                        pass
                self.store_rainfall_data(rainfall_records, f"file://{rainfall_csv_path}")
            except Exception as e:
                logger.error(f"Error reading rainfall CSV {rainfall_csv_path}: {e}")
        else:
            # Fallback to API fetch
            rainfall_records = await self.fetch_rainfall_data()
            if rainfall_records:
                self.store_rainfall_data(rainfall_records, "https://api.data.gov.in/resource/rainfall-data")
        
        logger.info("Data sync completed")
    
    def get_data_sources(self) -> List[Dict]:
        """Get all data sources with metadata"""
        sources = self.db.query(DataCacheMetadata).all()
        return [
            {
                "data_source": source.data_source,
                "last_sync": source.last_sync,
                "total_records": source.total_records,
                "source_url": source.source_url,
                "last_updated": source.last_updated
            }
            for source in sources
        ]
