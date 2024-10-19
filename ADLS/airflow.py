import os

from azure.storage.blob import BlobServiceClient

def upload_to_adls(file_path, container_name, destination_path):
    blob_service_client = BlobServiceClient.from_connection_string("")
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=destination_path)

    with open(file_path, "rb") as data:
        blob_client.upload_blob(data) 

    print(f"Uploaded file to ADLS: {destination_path}")

def partition_data(df):
    # Group by mode of transport, year, month, and station
    df_grouped = df.groupby(['Mode', 'Year', 'Month', 'Station']).sum().reset_index()

    for (mode, year, month, station), group in df_grouped.groupby(['Mode', 'Year', 'Month', 'Station']):
        # Create local directory structure for saving Parquet files
        dir_path = os.path.join("publictransport", mode, station, str(year), month)
        os.makedirs(dir_path, exist_ok=True)

        # File name and path for parquet file
        file_name = f"{mode}_{year}_{month}.parquet"
        file_path = os.path.join(dir_path, file_name)

        # Save DataFrame as Parquet file locally
        group.to_parquet(file_path, index=False)

        # Create the path for Azure Data Lake Storage
        # Example: publictransport/KTM/ETS/2020/January/KTM_2020_January.parquet
        destination_path = f"publictransport/{'LRT'}/{'Ampang'}/{'2019'}/{month}/{file_name}"

        # Upload the parquet file to ADLS
        upload_to_adls(file_path, 'adam98adls', destination_path)

        print(f"Saved and uploaded parquet file: {file_path}")