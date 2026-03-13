import os
import sys
import json
import hashlib
import logging
import smtplib
from io import StringIO
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import mlflow

from sqlalchemy import create_engine, text

# Airflow 3 imports (fix warning)
from airflow.sdk import dag, task

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


POSTGRES_CONN_URI = "postgresql+psycopg2://airflow:airflow@postgres:5432/data_pipe"
MLFLOW_TRACKING_URI = "http://mlflow:5000"

GMAIL_USER = "abc@gmail.com"
GMAIL_PASS = "abc"


def send_gmail(to_email, subject, html_content):

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:

        with smtplib.SMTP("smtp.gmail.com", 587) as server:

            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)

        logging.info("Email sent successfully")

    except Exception as e:

        logging.error(f"SMTP Error: {e}")


def alert_on_failure(context):

    task_instance = context.get("task_instance")
    logical_date = context.get("logical_date")

    subject = f"🚨 Airflow Task Failure: {task_instance.task_id}"

    html_content = f"""
    <h3>Airflow Task Failed</h3>
    <p><b>DAG:</b> {task_instance.dag_id}</p>
    <p><b>Task:</b> {task_instance.task_id}</p>
    <p><b>Execution Date:</b> {logical_date}</p>
    """

    send_gmail(GMAIL_USER, subject, html_content)


@dag(
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "mlflow", "postgres"],
    on_failure_callback=alert_on_failure,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)}
)
def etl_mlflow_postgres_pipeline():

    @task
    def setup_database_schema():

        ADMIN_URI = POSTGRES_CONN_URI.replace("/data_pipe", "/postgres")

        admin_engine = create_engine(ADMIN_URI, isolation_level="AUTOCOMMIT")

        with admin_engine.connect() as conn:

            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname='data_pipe'")
            )

            if not result.fetchone():

                conn.execute(text("CREATE DATABASE data_pipe"))

        engine = create_engine(POSTGRES_CONN_URI)

        create_tables_sql = """
        CREATE TABLE IF NOT EXISTS raw_sensor_data (
            id SERIAL PRIMARY KEY,
            sensor_id INTEGER,
            timestamp TIMESTAMP,
            temperature DOUBLE PRECISION,
            humidity DOUBLE PRECISION,
            pressure DOUBLE PRECISION
        );

        CREATE TABLE IF NOT EXISTS processed_sensor_metrics (
            sensor_id INTEGER,
            avg_temp DOUBLE PRECISION,
            max_temp DOUBLE PRECISION,
            avg_humidity DOUBLE PRECISION,
            record_count INTEGER,
            anomaly_total INTEGER,
            temperature_trend_slope DOUBLE PRECISION,
            batch_timestamp TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS enriched_sensor_data (
            id INTEGER,
            sensor_id INTEGER,
            timestamp TIMESTAMP,
            temperature DOUBLE PRECISION,
            humidity DOUBLE PRECISION,
            pressure DOUBLE PRECISION,
            is_anomaly INTEGER,
            hour INTEGER,
            heat_index DOUBLE PRECISION,
            batch_timestamp TIMESTAMP
        );
        """

        with engine.connect() as conn:

            conn.execute(text(create_tables_sql))
            conn.commit()

    @task
    def create_and_dump_raw_data(data_interval_end=None) -> str:

        engine = create_engine(POSTGRES_CONN_URI)

        run_date = data_interval_end or datetime.now()

        dates = pd.date_range(
            start=run_date - timedelta(days=1),
            end=run_date,
            freq="h"
        )[:-1]

        df = pd.DataFrame({

            "sensor_id": np.random.choice([101, 102, 103], len(dates)),

            "timestamp": dates,

            "temperature": np.random.normal(25, 5, len(dates)),

            "humidity": np.random.normal(50, 10, len(dates)),

            "pressure": np.random.normal(1013, 2, len(dates))

        })

        df.to_sql("raw_sensor_data", engine, if_exists="append", index=False)

        return "raw_sensor_data"

    @task
    def extract_transform_load_and_log(table_name: str, data_interval_end=None):

        engine = create_engine(POSTGRES_CONN_URI)

        run_date = data_interval_end or datetime.now()

        run_id = run_date.strftime("%Y%m%d%H%M%S")

        # incremental extraction
        query = """
        SELECT *
        FROM raw_sensor_data
        WHERE timestamp >= NOW() - INTERVAL '1 day'
        """

        df = pd.read_sql(query, engine)

        fingerprint = hashlib.md5(
            pd.util.hash_pandas_object(df, index=False).values
        ).hexdigest()

        try:

            from sklearn.ensemble import IsolationForest

            iso = IsolationForest(contamination=0.03)

            df["is_anomaly"] = iso.fit_predict(df[["temperature", "humidity"]])

        except:

            df["is_anomaly"] = 1

        df["hour"] = df["timestamp"].dt.hour

        df["heat_index"] = df["temperature"] + 0.5 * df["humidity"]

        transformed_df = df.groupby("sensor_id").agg(

            avg_temp=("temperature", "mean"),
            max_temp=("temperature", "max"),
            avg_humidity=("humidity", "mean"),
            record_count=("sensor_id", "count"),
            anomaly_total=("is_anomaly", lambda x: (x == -1).sum())

        ).reset_index()

        slopes = []

        for sid in transformed_df["sensor_id"]:

            sensor_data = df[df["sensor_id"] == sid].tail(24)

            if len(sensor_data) > 1:

                slope, _ = np.polyfit(
                    range(len(sensor_data)),
                    sensor_data["temperature"],
                    1
                )

            else:

                slope = 0

            slopes.append(slope)

        transformed_df["temperature_trend_slope"] = slopes

        transformed_df["batch_timestamp"] = run_date
        df["batch_timestamp"] = run_date

        # idempotency
        with engine.connect() as conn:

            conn.execute(
                text("DELETE FROM processed_sensor_metrics WHERE batch_timestamp = :ts"),
                {"ts": run_date}
            )

            conn.execute(
                text("DELETE FROM enriched_sensor_data WHERE batch_timestamp = :ts"),
                {"ts": run_date}
            )

            conn.commit()

        transformed_df.to_sql(
            "processed_sensor_metrics",
            engine,
            if_exists="append",
            index=False
        )

        df.to_sql(
            "enriched_sensor_data",
            engine,
            if_exists="append",
            index=False
        )

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment("Enterprise_Sensor_Pipeline")

        with mlflow.start_run(run_name=f"run_{run_id}"):

            mlflow.log_param("dataset_version", fingerprint)
            mlflow.log_metric("rows_processed", len(df))

        return transformed_df.to_json(orient="records")

    @task
    def send_success_notification(metrics_json: str):

        df_metrics = pd.read_json(StringIO(metrics_json))

        subject = "ETL Pipeline Success"

        html = f"""
        <h3>Pipeline Completed</h3>
        {df_metrics.to_html(index=False)}
        """

        send_gmail(GMAIL_USER, subject, html)

    setup_db = setup_database_schema()

    dump_data = create_and_dump_raw_data()

    metrics_json = extract_transform_load_and_log(dump_data)

    setup_db >> dump_data >> metrics_json >> send_success_notification(metrics_json)


etl_mlflow_postgres_pipeline()