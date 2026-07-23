from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

VENV_PYTHON = "/opt/airflow/project_venv/bin/python"

default_args = {
    "owner": "jory",
    "retries": 0,
}

with DAG(
    dag_id="wafra_capstone_pipeline",
    description="Bronze -> Silver -> Gold -> Quality Gate, with gate halting downstream stages on failure",
    default_args=default_args,
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["capstone", "wafra"],
) as dag:

    bronze_task = BashOperator(
        task_id="bronze_layer",
        bash_command=f"{VENV_PYTHON} /opt/airflow/lakehouse/bronze_layer.py",
    )

    silver_task = BashOperator(
        task_id="silver_layer",
        bash_command=f"{VENV_PYTHON} /opt/airflow/lakehouse/silver_layer.py",
    )

    quality_gate_task = BashOperator(
        task_id="quality_gate",
        bash_command=f"{VENV_PYTHON} /opt/airflow/quality_lineage/quality_gate.py",
    )

    gold_task = BashOperator(
        task_id="gold_layer",
        bash_command=f"{VENV_PYTHON} /opt/airflow/lakehouse/gold_layer.py",
    )

    bronze_task >> silver_task >> quality_gate_task >> gold_task
