import os
import requests
import pandas as pd
import sqlite3
from chromadb.utils import embedding_functions
from langchain_community.vectorstores import Chroma
import logging


# Define column maps (WHAT YOUR SCRIPT NEEDS)
CROP_COLUMNS_EXPECTED = {
    'State_Name': 'state',
    'District_Name': 'district',
    'Crop_Year': 'year',
    'Season': 'season',
    'Crop': 'crop',
    'Area': 'area',
    'Production': 'production'
}

RAIN_COLUMNS_EXPECTED = {
    'State': 'state',
    'District': 'district',
    'Year': 'year',
    'Month': 'month',
    'Avg_rainfall': 'rainfall'
}


class DataIngestionService:
    def __init__(self, db_path='project_samarth.db', vector_db_path='chroma_db'):
        # ... (keep existing __init__)
        self.db_path = db_path
        self.vector_db_path = vector_db_path
        self.conn = sqlite3.connect(self.db_path)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.vector_store = Chroma(
            persist_directory=self.vector_db_path,
            embedding_function=self.embedding_function
        )

    
    def ingest_data_from_csv(self, file_path, source_name):
        """
        Ingests data from a local CSV file.
        """
        try:
            logging.info(f"Reading data from CSV: {file_path}")
            df = pd.read_csv(file_path)
            
            logging.info(f"Original columns for {source_name}: {df.columns.tolist()}")

            # Clean and store the data
            df_cleaned = self.clean_data(df, source_name)
            
            if df_cleaned is not None:
                self.store_in_sql(df_cleaned, source_name)
                self.store_in_vector_db(df_cleaned, source_name)
                logging.info(f"Successfully ingested data for {source_name} from CSV.")
            else:
                logging.error(f"Data cleaning failed for {source_name}.")

        except FileNotFoundError:
            logging.error(f"File not found: {file_path}")
        except Exception as e:
            logging.error(f"Error ingesting data from {file_path}: {e}")
    # ====================================================================
    
    def ingest_data_from_api(self, api_url, source_name):
        # This function is now OBSOLETE, but we leave it
        logging.warning(f"Skipping API ingestion for {source_name}. Using local CSVs.")
        pass

    def fetch_data(self, api_url):
        # This function is now OBSOLETE
        pass

    def clean_data(self, df, source_name):
        """
        Cleans the data based on the source.
        This MUST be updated for your UP data.
        """
        try:
            if source_name == 'crop_production':
                # --- UPDATE THIS FOR YOUR CROP CSV ---
                df = df.rename(columns=CROP_COLUMNS_EXPECTED)
                
                # Keep only the columns we care about
                required_cols = ['state', 'district', 'year', 'season', 'crop', 'area', 'production']
                df = df[required_cols]
                
                # Convert types
                df['area'] = pd.to_numeric(df['area'], errors='coerce')
                df['production'] = pd.to_numeric(df['production'], errors='coerce')
                df['year'] = pd.to_numeric(df['year'], errors='coerce')
                
                # Fill missing data
                df.fillna({'production': 0, 'area': 0}, inplace=True)
                
                # Standardize text
                df['district'] = df['district'].str.strip().str.upper()
                df['crop'] = df['crop'].str.strip().str.title()
                
            elif source_name == 'rainfall':
                # --- UPDATE THIS FOR YOUR RAINFALL CSV ---
                df = df.rename(columns=RAIN_COLUMNS_EXPECTED)
                
                # Keep only the columns we care about
                required_cols = ['state', 'district', 'year', 'month', 'rainfall']
                df = df[required_cols]
                
                # Convert types
                df['rainfall'] = pd.to_numeric(df['rainfall'], errors='coerce')
                df['year'] = pd.to_numeric(df['year'], errors='coerce')
                
                # Fill missing data
                df.fillna({'rainfall': 0}, inplace=True)
                
                # Standardize text
                df['district'] = df['district'].str.strip().str.upper()

            else:
                logging.warning(f"No cleaning logic defined for source: {source_name}")
            
            logging.info(f"Cleaned columns for {source_name}: {df.columns.tolist()}")
            return df
        
        except KeyError as e:
            logging.error(f"Column mapping error for {source_name}: Missing column {e}")
            logging.error("Please check the CROP_COLUMNS_EXPECTED and RAIN_COLUMNS_EXPECTED dictionaries.")
            return None
        except Exception as e:
            logging.error(f"Error during data cleaning for {source_name}: {e}")
            return None

    def store_in_sql(self, df, table_name):
        # ... (keep existing store_in_sql)
        try:
            df.to_sql(table_name, self.conn, if_exists='replace', index=False)
            logging.info(f"Data stored in SQL table: {table_name}")
        except Exception as e:
            logging.error(f"Error storing data in SQL for {table_name}: {e}")

    def store_in_vector_db(self, df, collection_name):
        # ... (keep existing store_in_vector_db)
        try:
            # Drop existing collection if it exists
            if collection_name in [col.name for col in self.vector_store._client.list_collections()]:
                self.vector_store._client.delete_collection(name=collection_name)
                logging.info(f"Dropped existing vector collection: {collection_name}")

            collection = self.vector_store._client.create_collection(name=collection_name)
            
            # Prepare data for Chroma
            documents = []
            metadatas = []
            ids = []
            
            for index, row in df.iterrows():
                # The "document" is the string representation of the row
                doc_string = ", ".join([f"{col}: {val}" for col, val in row.items()])
                documents.append(doc_string)
                # The metadata is the dict representation
                metadatas.append(row.to_dict())
                ids.append(f"{collection_name}_{index}")

            # Add to Chroma in batches
            batch_size = 5000
            for i in range(0, len(documents), batch_size):
                logging.info(f"Storing batch {i//batch_size + 1} for collection {collection_name}")
                # logging.info( "How much  it is left",  )
                collection.add(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
            logging.info(f"Data stored in vector DB collection: {collection_name}")
        except Exception as e:
            logging.error(f"Error storing data in vector DB for {collection_name}: {e}")