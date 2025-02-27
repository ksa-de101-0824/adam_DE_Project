from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from datetime import timedelta


# Default arguments for all tasks
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}


# Function to fetch Snowflake connection details
def get_snowflake_connection(conn_id):
    """
    Retrieves Snowflake connection details from Airflow connections.
    """
    conn = BaseHook.get_connection(conn_id)
    return {
        'account': conn.extra_dejson.get('account'),
        'user': conn.login,
        'password': conn.password,
        'warehouse': conn.extra_dejson.get('warehouse'),
        'database': conn.extra_dejson.get('database'),
        'schema': conn.schema,
        'role': conn.extra_dejson.get('role')
    }


# Function to fetch data from the URL and return as DataFrame
def fetch_data_from_url(**context):
    """
    Fetches the data from the provided URL and pushes it to XCom.
    """
    URL_DATA = 'https://storage.data.gov.my/transportation/ridership_headline.parquet'
    df = pd.read_parquet(URL_DATA)
    
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])

    context['ti'].xcom_push(key='fetch_data_from_url', value=df.to_json())

    # Push the DataFrame to XCom as JSON
    context['ti'].xcom_push(key='fetch_data_from_url', value=df.to_json())


# Function to upload raw DataFrame to Snowflake
def upload_raw_to_snowflake(**context):
    """
    Uploads the raw DataFrame to Snowflake into a specified table.
    """
    # Pull the DataFrame from XCom
    df_json = context['ti'].xcom_pull(key='fetch_data_from_url')
    df = pd.read_json(df_json)

    # Retrieve Snowflake connection details
    snowflake_conn = get_snowflake_connection('Snowflake-Connection')

    try:
        # Establish Snowflake connection using context manager
        with snowflake.connector.connect(
            account=snowflake_conn['account'],
            user=snowflake_conn['user'],
            password=snowflake_conn['password'],
            warehouse=snowflake_conn['warehouse'],
            database=snowflake_conn['database'],
            schema=snowflake_conn['schema'],
            role=snowflake_conn['role']
        ) as conn:

            # Write the DataFrame to Snowflake in the RAW_EMPLOYEE_DATA table
            success, nchunks, nrows, _ = write_pandas(
                conn,
                df,
                'RAW_PUBLIC_TRANSPORT_DATA',  # The raw data table
                auto_create_table=True,
                overwrite=False  # Ensure we're appending, not overwriting
            )

            if success:
                print(f"Successfully uploaded {nrows} rows in {nchunks} chunks to RAW_EMPLOYEE_DATA in Snowflake.")
            else:
                print("Failed to upload data to Snowflake.")

    except snowflake.connector.errors.ProgrammingError as e:
        print(f"Snowflake Programming Error: {str(e)}")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise


# Define the DAG
with DAG(
    dag_id='send_to_snowflake',
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    description="A DAG that uploads raw employee data to Snowflake."
) as dag:

# Task 1: Fetch data from URL and create DataFrame
    fetch_data_task = PythonOperator(
        task_id='fetch_data_from_url',
        python_callable=fetch_data_from_url
    )

    # Task 2: Upload Raw DataFrame to Snowflake
    upload_raw_task = PythonOperator(
        task_id='upload_raw_to_snowflake',
        python_callable=upload_raw_to_snowflake
    )


    # Set task dependencies
    fetch_data_task >> upload_raw_task