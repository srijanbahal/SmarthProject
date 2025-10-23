import pandas as pd
import sqlite3
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [Seeder] - %(levelname)s - %(message)s')

# --- Configuration ---
SOURCE_CSV_PATH = "../data/crop_yield.csv" # Path to your new dataset
DB_PATH = "../data/crop_yield.db"         # Name of the output SQLite database
TABLE_NAME = "crop_yield"         # Name of the table within the database

def clean_column_name(col_name):
    """Converts column names to snake_case for SQL compatibility."""
    col_name = re.sub(r'(?<!^)(?=[A-Z])', '_', col_name).lower() # CamelCase to snake_case
    col_name = re.sub(r'\W+', '_', col_name) # Replace non-alphanumeric with underscore
    col_name = re.sub(r'_+', '_', col_name) # Replace multiple underscores with one
    col_name = col_name.strip('_') # Remove leading/trailing underscores
    return col_name

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans the crop_yield dataframe."""
    logging.info(f"Original columns: {df.columns.tolist()}")

    # 1. Clean Column Names
    df.columns = [clean_column_name(col) for col in df.columns]
    logging.info(f"Cleaned columns: {df.columns.tolist()}")

    # Expected columns after cleaning
    expected_cols = ['crop', 'crop_year', 'season', 'state', 'area', 'production',
                     'annual_rainfall', 'fertilizer', 'pesticide', 'yield']
    
    # Check if all expected columns exist
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing expected columns after cleaning: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
        
    # Ensure correct data types (adjust as needed based on actual data)
    try:
        df['crop_year'] = pd.to_numeric(df['crop_year'], errors='coerce').astype('Int64') # Use Int64 for nullable integer
        df['area'] = pd.to_numeric(df['area'], errors='coerce')
        df['production'] = pd.to_numeric(df['production'], errors='coerce')
        df['annual_rainfall'] = pd.to_numeric(df['annual_rainfall'], errors='coerce')
        df['fertilizer'] = pd.to_numeric(df['fertilizer'], errors='coerce')
        df['pesticide'] = pd.to_numeric(df['pesticide'], errors='coerce')
        df['yield'] = pd.to_numeric(df['yield'], errors='coerce')
    except Exception as e:
        logging.error(f"Error during type conversion: {e}")
        # Optionally, inspect failing columns/rows here
        raise

    # Clean string columns (remove extra spaces, handle inconsistencies)
    str_cols = ['crop', 'season', 'state']
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].str.strip().str.title() # Convert to Title Case
            # Handle specific known inconsistencies if necessary
            # df[col] = df[col].replace({'Old Name': 'New Name'})

    # Handle missing values (example: fill numeric NaNs with 0 or mean/median)
    numeric_cols = df.select_dtypes(include=['number']).columns
    df[numeric_cols] = df[numeric_cols].fillna(0) # Simple fill with 0, adjust strategy if needed

    logging.info("Data type conversion and NaN handling complete.")
    logging.info(f"Data shape after cleaning: {df.shape}")
    logging.info(f"Sample data head:\n{df.head().to_string()}")

    return df

def create_database(df: pd.DataFrame):
    """Creates the SQLite database and table, then inserts data."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        logging.info(f"Removed existing database: {DB_PATH}")

    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Connected to new database: {DB_PATH}")

        # Create table and insert data
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
        logging.info(f"Created table '{TABLE_NAME}' and inserted {len(df)} rows.")

        # Optional: Add indexes for faster querying
        cursor = conn.cursor()
        logging.info("Adding indexes...")
        cursor.execute(f"CREATE INDEX idx_crop_year ON {TABLE_NAME} (crop_year);")
        cursor.execute(f"CREATE INDEX idx_state ON {TABLE_NAME} (state);")
        cursor.execute(f"CREATE INDEX idx_crop ON {TABLE_NAME} (crop);")
        conn.commit()
        logging.info("Indexes added successfully.")

        conn.close()
        logging.info("Database connection closed.")

    except sqlite3.Error as e:
        logging.error(f"SQLite error during database creation: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

def main():
    """Main function to run the seeding process."""
    logging.info(f"Starting data seeding process for {SOURCE_CSV_PATH}...")

    if not os.path.exists(SOURCE_CSV_PATH):
        logging.error(f"Source CSV file not found: {SOURCE_CSV_PATH}")
        return

    try:
        # Load
        df_raw = pd.read_csv(SOURCE_CSV_PATH)
        logging.info(f"Loaded {len(df_raw)} rows from {SOURCE_CSV_PATH}")

        # Clean
        df_cleaned = clean_data(df_raw.copy()) # Use copy to avoid modifying original df

        # Store
        create_database(df_cleaned)

        logging.info("Data seeding process completed successfully!")

    except ValueError as ve:
        logging.error(f"Data validation error: {ve}")
    except Exception as e:
        logging.error(f"Seeding failed with unexpected error: {e}")

if __name__ == "__main__":
    main()

