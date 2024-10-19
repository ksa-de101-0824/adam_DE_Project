import os
import pandas as pd
from airflow import DAG  # Keep this for the Airflow DAG file
from ADLS.airflow import upload_to_adls # Correct import from the right file

def partition_data(df):
    # Group by mode of transport, station, year, and month
    df_grouped = df.groupby(['Mode', 'Station', 'Year', 'Month']).sum().reset_index()

    for (mode, station, year, month), group in df_grouped.groupby(['Mode', 'Station', 'Year', 'Month']):
        # Create directory structure based on mode, station, year, and month
        dir_path = os.path.join("publictransport", mode, station, str(year), month)
        
        # Make sure the directory exists locally
        os.makedirs(dir_path, exist_ok=True)

        # File name and path for parquet file
        file_name = f"{mode}_{year}_{month}.parquet"
        file_path = os.path.join(dir_path, file_name)

        # Save DataFrame as a Parquet file locally
        group.to_parquet(file_path, index=False)

        # Upload the file to Azure Data Lake Storage (ADLS)
        # Update the path in ADLS to match your desired directory structure
        destination_path = f"{mode}/{station}/{year}/{month}/{file_name}"
        upload_to_adls(file_path, 'trafficdata', destination_path)

        print(f"Saved and uploaded parquet file: {file_path}")  # Optional: for debugging
