from datetime import timedelta

import pendulum
from airflow import DAG   # type: ignore
from airflow.operators.bash import BashOperator   # type: ignore

# docker-compose.yml mein poora project yahin mount hota hai
PROJECT_DIR = "/opt/airflow/project"

# Container ke andar "localhost" ka matlab container khud hai, Windows nahi.
# Isliye MySQL host override karte hain. Baaki DB_* values config/.env se aati hain.
ENV = {"DB_HOST": "host.docker.internal"}

default_args = {
    "owner": "himanshu",
    "retries": 2,                         # yfinance kabhi-kabhi fail hota hai
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_market_pipeline",
    description="NSE stocks: extract (yfinance) -> transform -> load (MySQL)",
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata"),
    schedule="0 16 * * 1-5",              # Mon-Fri, 4:00 PM IST
    catchup=False,
    default_args=default_args,
    tags=["etl", "stocks"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT_DIR} && python scripts/extract.py",
        env=ENV,
        append_env=True,
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR} && python scripts/transform.py",
        env=ENV,
        append_env=True,
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"cd {PROJECT_DIR} && python scripts/load.py",
        env=ENV,
        append_env=True,
    )

    extract >> transform >> load