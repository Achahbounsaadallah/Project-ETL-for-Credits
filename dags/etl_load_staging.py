from datetime import datetime, timedelta
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="etl_load_staging",
    default_args=default_args,
    description="Exécute scripts d'extraction et charge la table stg_credit",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["etl"],
) as dag:

    run_connection_script = BashOperator(
        task_id="run_connection_to_db",
        bash_command="python /opt/airflow/scripts/connection_to_db.py",
    )
    run_add_data_to_dw = BashOperator(
        task_id="run_add_data_to_dw",
        bash_command="python /opt/airflow/spark/add_data_to_DW.py",
    )
    run_powerbi_refresh = BashOperator(
        task_id="run_powerbi_refresh",
        bash_command="python /opt/airflow/powerbi/powerbi.py",
    )

    run_connection_script >> run_add_data_to_dw >> run_powerbi_refresh
