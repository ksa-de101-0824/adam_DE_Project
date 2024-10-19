from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import requests
import os
import pandas as pd
from bs4 import BeautifulSoup
from azure.storage.blob import BlobServiceClient

# Scraping function
def scrape_data():
    url = 'https://data.gov.my/data-catalogue/ridership_headline'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    data = []
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if cells:
            mode = cells[0].text.strip()
            station = cells[1].text.strip()
            year = cells[2].text.strip()
            month = cells[3].text.strip()
            ridership = cells[4].text.strip()
            data.append([mode, station, year, month, ridership])

    df = pd.DataFrame(data, columns=['Mode', 'Station', 'Year', 'Month', 'Ridership'])
    return df

# Function to upload data to ADLS
def upload_to_adls(file_path, container_name, destination_path):
    blob_service_client = BlobServiceClient.from_connection_string("your_connection_string")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=destination_path)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data)

    print(f"Uploaded file to ADLS: {destination_path}")

# Partition function
def partition_data(df):
    df_grouped = df.groupby(['Mode', 'Station', 'Year', 'Month']).sum().reset_index()

    for (mode, station, year, month), group in df_grouped.groupby(['Mode', 'Station', 'Year', 'Month']):
        dir_path = os.path.join("publictransport", mode, station, str(year), month)
        os.makedirs(dir_path, exist_ok=True)

        file_name = f"{mode}_{year}_{month}.parquet"
        file_path = os.path.join(dir_path, file_name)

        # Save DataFrame as Parquet file locally
        group.to_parquet(file_path, index=False)

        # Create the path for Azure Data Lake Storage
        destination_path = f"publictransport/{mode}/{station}/{year}/{month}/{file_name}"

        # Upload to ADLS
        upload_to_adls(file_path, 'adam98adls', destination_path)

        print(f"Saved and uploaded parquet file: {file_path}")

# Define the Airflow DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 10, 18),
    'email_on_failure': False,
    'email_on_retry': False
}

dag = DAG('public_transport_data_pipeline', default_args=default_args, schedule_interval='@monthly')

# Task to scrape data
scrape_task = PythonOperator(
    task_id='scrape_data',
    python_callable=scrape_data,
    dag=dag
)

# Task to partition data and upload to ADLS
partition_task = PythonOperator(
    task_id='partition_data',
    python_callable=lambda: partition_data(scrape_data()),
    dag=dag
)

# Set task dependencies
scrape_task >> partition_task
