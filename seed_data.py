#!/usr/bin/env python3
"""
Data seeding script for testing Project Samarth
This script creates sample data for Uttar Pradesh districts
"""

import os
import sys
from datetime import datetime, timedelta
import random

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.database.models import create_tables, SessionLocal, CropProduction, Rainfall, DataCacheMetadata

def seed_sample_data():
    """Create sample data for testing"""
    
    # Create tables
    create_tables()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Sample districts in Uttar Pradesh
        districts = [
            "Agra", "Lucknow", "Kanpur", "Varanasi", "Allahabad", 
            "Meerut", "Ghaziabad", "Bareilly", "Moradabad", "Aligarh"
        ]
        
        # Sample crops
        crops = [
            "Rice", "Wheat", "Sugarcane", "Maize", "Bajra", 
            "Arhar/Tur", "Moong", "Groundnut", "Onion", "Potato"
        ]
        
        # Sample seasons
        seasons = ["Kharif", "Rabi", "Zaid"]
        
        # Create sample crop production data
        print("Creating sample crop production data...")
        crop_records = []
        
        for year in range(2018, 2024):  # 6 years of data
            for district in districts:
                for crop in crops:
                    for season in seasons:
                        # Skip some combinations for realism
                        if random.random() < 0.3:  # 30% chance of having data
                            area = random.uniform(100, 5000)  # hectares
                            production = random.uniform(50, 10000)  # tonnes
                            
                            crop_record = CropProduction(
                                state="Uttar Pradesh",
                                district=district,
                                crop_year=year,
                                season=season,
                                crop=crop,
                                area=area,
                                production=production,
                                source_url="https://api.data.gov.in/resource/crop-production-data"
                            )
                            crop_records.append(crop_record)
        
        db.add_all(crop_records)
        print(f"Added {len(crop_records)} crop production records")
        
        # Create sample rainfall data
        print("Creating sample rainfall data...")
        rainfall_records = []
        
        for year in range(2018, 2024):
            for district in districts:
                for month in range(1, 13):  # 12 months
                    # Generate realistic rainfall patterns
                    if month in [6, 7, 8, 9]:  # Monsoon months
                        avg_rainfall = random.uniform(50, 200)
                    elif month in [10, 11, 12, 1, 2]:  # Winter months
                        avg_rainfall = random.uniform(5, 30)
                    else:  # Summer months
                        avg_rainfall = random.uniform(10, 50)
                    
                    # Create multiple records per month for realism
                    for day in range(1, 29, 7):  # Every 7 days
                        date = datetime(year, month, min(day, 28))
                        
                        rainfall_record = Rainfall(
                            state="Uttar Pradesh",
                            district=district,
                            date=date,
                            year=year,
                            month=month,
                            avg_rainfall=avg_rainfall + random.uniform(-10, 10),
                            agency_name="NRSC VIC MODEL",
                            source_url="https://api.data.gov.in/resource/rainfall-data"
                        )
                        rainfall_records.append(rainfall_record)
        
        db.add_all(rainfall_records)
        print(f"Added {len(rainfall_records)} rainfall records")
        
        # Create metadata records
        print("Creating metadata records...")
        
        crop_metadata = DataCacheMetadata(
            data_source="crop_production",
            last_sync=datetime.utcnow(),
            total_records=len(crop_records),
            source_url="https://api.data.gov.in/resource/crop-production-data"
        )
        
        rainfall_metadata = DataCacheMetadata(
            data_source="rainfall",
            last_sync=datetime.utcnow(),
            total_records=len(rainfall_records),
            source_url="https://api.data.gov.in/resource/rainfall-data"
        )
        
        db.add(crop_metadata)
        db.add(rainfall_metadata)
        
        # Commit all changes
        db.commit()
        print("✅ Sample data created successfully!")
        
        # Print summary
        print("\n📊 Data Summary:")
        print(f"Districts: {len(districts)}")
        print(f"Crops: {len(crops)}")
        print(f"Crop Production Records: {len(crop_records)}")
        print(f"Rainfall Records: {len(rainfall_records)}")
        print(f"Years Covered: 2018-2023")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌾 Project Samarth - Data Seeding Script")
    print("=" * 50)
    seed_sample_data()
    print("\n🎉 Data seeding completed!")
    print("\nNext steps:")
    print("1. Start the FastAPI backend: cd backend && python -m uvicorn app.main:app --reload")
    print("2. Start the Streamlit frontend: cd frontend && streamlit run streamlit_app.py")
    print("3. Visit http://localhost:8501 to test the system")
