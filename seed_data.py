import sys
import os

# Add the backend to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.app.services.data_ingestion import DataIngestionService
import logging

logging.basicConfig(level=logging.INFO)


DATA_SOURCES = [
    {
        "id": "crop_data",
        "file_path": "./data/crop_data_raw_UP.csv",  # Your local crop file
        "name": "crop_production"           # This will be the SQL table name
    },
    {
        "id": "rainfall_data",
        "file_path": "./data/rainfall_data_raw_UP.csv", # Your local rainfall file
        "name": "rainfall"                    # This will be the SQL table name
    }
]
# ====================================================================
# Get the absolute path of the directory this script is in
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define absolute paths for the databases
DB_PATH_ABS = os.path.join(BASE_DIR, 'project_samarth.db')
CHROMA_DB_PATH_ABS = os.path.join(BASE_DIR, 'chroma_db')



def main():
    try:
        # Delete old databases if they exist
        if os.path.exists('project_samarth.db'):
            os.remove('project_samarth.db')
            logging.info("Removed old project_samarth.db")
        
        # Note: ChromaDB is harder to delete, we'll clear collections instead
        
        ingestion_service = DataIngestionService()
        
        logging.info("Starting data ingestion process...")
        
        for source in DATA_SOURCES:
            logging.info(f"Ingesting {source['name']} from {source['file_path']}...")
            # --- CALL OUR NEW CSV FUNCTION ---
            ingestion_service.ingest_data_from_csv(source["file_path"], source["name"])
            
        logging.info("Data ingestion process completed.")
        
    except Exception as e:
        logging.error(f"An error occurred during the seeding process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()