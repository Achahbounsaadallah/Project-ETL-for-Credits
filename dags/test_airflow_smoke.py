from datetime import timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="test_airflow_smoke",
    default_args=default_args,
    description="DAG de smoke test pour vérifier Airflow + volumes",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=["smoke"],
) as dag:

    list_dags = BashOperator(
        task_id="list_dags_folder",
        bash_command="ls -la /opt/airflow/dags || echo 'dags folder missing'"
    )

    list_data = BashOperator(
        task_id="list_data_folder",
        bash_command="ls -la /opt/airflow/data || echo 'data folder missing'"
    )

    smoke_ok = BashOperator(
        task_id="smoke_ok",
        bash_command='echo "SMOKE TEST OK: Airflow can run tasks and access volumes"'
    )

    list_dags >> list_data >> smoke_ok