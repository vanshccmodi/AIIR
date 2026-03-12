import os
import sys
from airflow.decorators import dag, task
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import mlflow
import hashlib
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from airflow.utils.email import send_email

# Configuration
POSTGRES_CONN_URI = "postgresql+psycopg2://airflow:airflow@postgres:5432/data_pipe"
MLFLOW_TRACKING_URI = "http://mlflow:5000"
GMAIL_USER = "abc@gmail.com"
GMAIL_PASS = "abc"

def send_gmail(to_email, subject, html_content):
    """Bypasses Airflow config and sends email directly via SMTP."""
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        logging.info(f"Email sent successfully to {to_email}")
    except Exception as e:
        logging.error(f"Manual SMTP Error: {e}")

# FEATURE 6: Failure Alerting (Mock Callback)
# This function gets triggered if any task fails!
def alert_on_failure(context):
    """Sends a real email alert on task failure using direct SMTP."""
    task_instance = context.get('task_instance')
    logical_date = context.get('logical_date')
    
    subject = f"🚨 Airflow Task Failure: {task_instance.task_id}"
    html_content = f"""
    <h3>Airflow Task Failed</h3>
    <p><b>Task ID:</b> {task_instance.task_id}</p>
    <p><b>DAG ID:</b> {task_instance.dag_id}</p>
    <p><b>Execution Date:</b> {logical_date}</p>
    """
    send_gmail(GMAIL_USER, subject, html_content)

@dag(
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "mlflow", "postgres", "production"],
    on_failure_callback=alert_on_failure,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=1)}
)
def etl_mlflow_postgres_pipeline():
    
    @task
    def setup_database_schema():
        """Validate or initialize the required database schema."""
        from sqlalchemy import text
        engine = create_engine(POSTGRES_CONN_URI)
        
        # Schema definition for sensor records
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS raw_sensor_data (
            id SERIAL PRIMARY KEY,
            sensor_id INTEGER,
            timestamp TIMESTAMP WITHOUT TIME ZONE,
            temperature DOUBLE PRECISION,
            humidity DOUBLE PRECISION,
            pressure DOUBLE PRECISION
        );
        """
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        logging.info("Schema verified: raw_sensor_data table is ready.")

    @task
    def create_and_dump_raw_data(data_interval_end=None) -> str:
        """Task to simulate ingestion of raw sensor data into the database."""
        engine = create_engine(POSTGRES_CONN_URI)
        run_date = data_interval_end or datetime.now()
        
        dates = pd.date_range(start=run_date - timedelta(days=1), end=run_date, freq='H')[:-1] 
        data = {
            "sensor_id": np.random.choice([101, 102, 103], size=len(dates)),
            "timestamp": dates,
            "temperature": np.random.normal(25, 5, size=len(dates)),
            "humidity": np.random.normal(50, 10, size=len(dates)),
            "pressure": np.random.normal(1013, 2, size=len(dates))
        }
        df = pd.DataFrame(data)
        
        # Append data into the table
        df.to_sql("raw_sensor_data", engine, if_exists="append", index=False)
        return "raw_sensor_data"

    @task
    def extract_transform_load_and_log(table_name: str, data_interval_end=None):
        """End-to-end ETL process with validation, anomaly detection, and analytics."""
        import json
        engine = create_engine(POSTGRES_CONN_URI)
        run_date_str = (data_interval_end or datetime.now()).strftime("%Y%m%d%H%M%S")
        
        # 1. Extract
        df = pd.read_sql_table(table_name, engine)
        
        # Data Validation with Pydantic
        validation_success = True
        try:
            from pydantic import BaseModel, Field
            class SensorReading(BaseModel):
                sensor_id: int
                timestamp: datetime
                temperature: float = Field(..., ge=-50, le=100)
                humidity: float = Field(..., ge=0, le=100)
                pressure: float = Field(..., ge=800, le=1200)
            
            for record in df.tail(50).to_dict(orient="records"):
                SensorReading(**record)
        except Exception as e:
            validation_success = False
            logging.error(f"Data Validation Error: {e}")

        # Data Versioning Fingerprint
        data_fingerprint = hashlib.md5(pd.util.hash_pandas_object(df, index=False).values).hexdigest()

        # Anomaly Detection
        try:
            from sklearn.ensemble import IsolationForest
            iso = IsolationForest(contamination=0.03, random_state=42)
            X = df[['temperature', 'humidity']].values
            df['is_anomaly'] = iso.fit_predict(X)
            anomaly_count = (df['is_anomaly'] == -1).sum()
        except:
            df['is_anomaly'] = 1
            anomaly_count = 0

        # 2. Transform Phase - ADVANCED ANALYTICS (Meaningful)
        df['hour'] = df['timestamp'].dt.hour
        df['heat_index'] = df['temperature'] + (0.5 * df['humidity']) 
        
        # Aggregations
        transformed_df = df.groupby('sensor_id').agg(
            avg_temp=('temperature', 'mean'),
            max_temp=('temperature', 'max'),
            avg_humidity=('humidity', 'mean'),
            record_count=('sensor_id', 'count'),
            anomaly_total=('is_anomaly', lambda x: (x == -1).sum())
        ).reset_index()

        # Statistical trend calculation for temperature metrics
        # Calculates the linear trend over the last window of records per sensor
        trend_slopes = []
        for sid in transformed_df['sensor_id']:
            sensor_data = df[df['sensor_id'] == sid].tail(24)
            if len(sensor_data) > 1:
                slope, _ = np.polyfit(range(len(sensor_data)), sensor_data['temperature'], 1)
                trend_slopes.append(slope)
            else:
                trend_slopes.append(0.0)
        transformed_df['temperature_trend_slope'] = trend_slopes

        # 3. Load Phase
        target_table = "processed_sensor_metrics"
        transformed_df.to_sql(target_table, engine, if_exists="replace", index=False)
        
        enriched_table = "enriched_sensor_data"
        df.to_sql(enriched_table, engine, if_exists="replace", index=False)
        
        # 4. Log phase (MLflow) - ENTERPRISE OBSERVABILITY UPGRADE
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment("Enterprise_Sensor_Pipeline")
        
        with mlflow.start_run(run_name=f"full_audit_{run_date_str}"):
            # A. LINEAGE & SCHEMA METADATA
            metadata = {
                "source_node": os.uname().nodename if hasattr(os, 'uname') else "windows_node",
                "table_uri": f"{POSTGRES_CONN_URI}/{table_name}",
                "dataset_version": data_fingerprint,
                "process_date": str(datetime.now()),
                "source_rows": len(df),
                "target_tables": [target_table, enriched_table],
                "python_version": sys.version.split()[0],
                "airflow_dag_id": "etl_mlflow_postgres_pipeline"
            }
            
            # Log all metadata as Params
            mlflow.log_params(metadata)
            
            # B. STATISTICAL DISTRIBUTIONS (Proper Logging)
            # We log stats for every numerical column
            for col in ['temperature', 'humidity', 'pressure', 'heat_index']:
                stats = df[col].describe()
                mlflow.log_metrics({
                    f"{col}_mean": stats['mean'],
                    f"{col}_std": stats['std'],
                    f"{col}_min": stats['min'],
                    f"{col}_max": stats['max']
                })
            
            # C. PIPELINE METRICS
            total_anomalies = int((df['is_anomaly'] == -1).sum())
            health_score = (1 - (total_anomalies/len(df))) * 100 if len(df) > 0 else 0
            
            mlflow.log_metrics({
                "anomaly_count": total_anomalies,
                "data_health_score": health_score,
                "sensor_diversity": df['sensor_id'].nunique()
            })

            # D. TAGGING FOR SEARCHABILITY
            mlflow.set_tags({
                "quality_tier": "GOLD" if health_score > 98 else "SILVER",
                "environment": "production",
                "data_owner": "Modi Vansh"
            })

            # E. ARTIFACTS (Evidence)
            # Log the Metadata JSON
            meta_path = f"/tmp/metadata_{run_date_str}.json"
            with open(meta_path, "w") as f:
                json.dump(metadata, f, indent=4)
            mlflow.log_artifact(meta_path)
            
            # Log a Sample of the final data for manual audit
            sample_path = f"/tmp/sample_{run_date_str}.csv"
            transformed_df.to_csv(sample_path, index=False)
            mlflow.log_artifact(sample_path)

            # Optional: Visual profiling report logic
            try:
                from ydata_profiling import ProfileReport
                profile = ProfileReport(df, title="Sensor Data Profile", minimal=True)
                profile_path = f"/tmp/profile_{run_date_str}.html"
                profile.to_file(profile_path)
                mlflow.log_artifact(profile_path)
            except:
                logging.info("ydata-profiling not installed. Skipping HTML report.")
        
        return transformed_df.to_json()

    @task
    def send_success_notification(metrics_json: str):
        """Sends a structured email report after successful pipeline completion."""
        df_metrics = pd.read_json(metrics_json)
        
        subject = "✅ ETL Pipeline Success: Sensor Insights Ready"
        html_content = f"""
        <h3>Sensor Analytics Pipeline Completed</h3>
        <p>The daily ETL batch has finished successfully. Data is now available in Postgres and MLflow.</p>
        <h4>Summary Metrics per Sensor:</h4>
        {df_metrics.to_html(index=False)}
        <br>
        <p>View the full report and artifacts at: <a href="http://localhost:5000">MLflow Tracking UI</a></p>
        """
        send_gmail(GMAIL_USER, subject, html_content)

    # Execution Order
    setup_db = setup_database_schema()
    dump_data = create_and_dump_raw_data()
    metrics_json = extract_transform_load_and_log(dump_data)
    
    # Send email only after all tasks succeed
    setup_db >> dump_data >> metrics_json >> send_success_notification(metrics_json)

etl_mlflow_postgres_pipeline()
