from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

def print_hello():
    print('Hello Adam Arzemy!')

def print_goodbye():
    print('Bye Adam Arzemy!')

with DAG(
    dag_id = 'my_first_dag',
    default_args = default_args,
    description = 'My first DAG',
    schedule_interval = timedelta(days=1),
    start_date = datetime(2025, 2, 25),
    end_date = datetime(2025, 2, 26),
    catchup = False,
    tags = ['example_1'],
) as dag:
    task_1 = PythonOperator(
        task_id = 'task_1',
        python_callable = print_hello,
        provide_context = True,
    )

    task_2 = PythonOperator(
        task_id = 'task_2',
        python_callable = print_goodbye,
        provide_context = True,
    )

    task_1 >> task_2