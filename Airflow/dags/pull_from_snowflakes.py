from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from airflow.hooks.base import BaseHook
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from datetime import datetime, timedelta


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


# Function to pull raw data from Snowflake
def pull_raw_data_from_snowflake(**context):
    """
    Pulls raw data from the RAW_EMPLOYEE_DATA table in Snowflake and pushes it to XCom.
    """
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
            
            # Create a cursor object
            cur = conn.cursor()

            # Define the SQL query to pull raw data
            sql_query = "SELECT * FROM RAW_PUBLIC_TRANSPORT_DATA"

            # Execute the query
            cur.execute(sql_query)

            # Fetch all the results
            result = cur.fetchall()

            # Get column names
            columns = [desc[0] for desc in cur.description]

            # Create a DataFrame from the results
            df = pd.DataFrame(result, columns=columns)

            # Push the DataFrame to XCom as JSON
            context['ti'].xcom_push(key='fetch_data_from_url', value=df.to_json())

            print(f"Pulled raw data from Snowflake: {df}")

    except snowflake.connector.errors.ProgrammingError as e:
        print(f"Snowflake Programming Error: {str(e)}")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise


# Function to process the pulled DataFrame
def processed_data_from_url(**context):
    """
    Processes the raw employee data, adds new columns, and pushes it to XCom.
    """
    # Pull the raw DataFrame from XCom
    df_json = context['ti'].xcom_pull(key='fetch_data_from_url')
    df = pd.read_json(df_json)

    # Add new columns: years of experience, performance score
    df['years_of_experience'] = (pd.Timestamp.now() - pd.to_datetime(df['join_date'])).dt.days // 365
    df['performance_score'] = df['salary'] * 0.001  # Example: Arbitrary performance score based on salary

    # Push the processed DataFrame to XCom
    context['ti'].xcom_push(key='processed_data_from_url', value=df.to_json())

    print(f"Processed data: {df}")


# Function to upload processed data to Snowflake
def upload_processed_data_to_snowflake(**context):
    """
    Uploads the processed DataFrame to Snowflake into a specified table.
    """
    # Pull the processed DataFrame from XCom
    df_json = context['ti'].xcom_pull(key='processed_data_from_url')
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

            # Write the DataFrame to Snowflake in the PROCESSED_PUBLIC_TRANSPORT_DATA table
            success, nchunks, nrows, _ = write_pandas(
                conn,
                df,
                'PROCESSED_PUBLIC_TRANSPORT_DATA',  # The processed data table
                auto_create_table=True,
                overwrite=False  # Ensure we're appending, not overwriting
            )

            if success:
                print(f"Successfully uploaded {nrows} rows in {nchunks} chunks to PROCESSED_PUBLIC_TRANSPORT_DATA in Snowflake.")
            else:
                print("Failed to upload processed data to Snowflake.")

    except snowflake.connector.errors.ProgrammingError as e:
        print(f"Snowflake Programming Error: {str(e)}")
        raise

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise


# Define the DAG
with DAG(
    dag_id='pull_from_snowflake',
    default_args=default_args,
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    description="A DAG that processes raw employee data and uploads processed data to Snowflake."
) as dag:

    # Task 1: Pull Raw Data from Snowflake
    pull_raw_data_task = PythonOperator(
        task_id='pull_raw_data_from_snowflake',
        python_callable=pull_raw_data_from_snowflake
    )

    # Task 2: Process the Raw Data
    processed_data_from_url_task = PythonOperator(
        task_id='processed_data_from_url',
        python_callable=processed_data_from_url
    )

    # Task 3: Upload Processed Data to Snowflake
    upload_processed_data_task = PythonOperator(
        task_id='upload_processed_data_to_snowflake',
        python_callable=upload_processed_data_to_snowflake
    )


    # Set task dependencies
    pull_raw_data_task >> processed_data_from_url_task >> upload_processed_data_task