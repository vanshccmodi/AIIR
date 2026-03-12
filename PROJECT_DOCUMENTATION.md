# Enterprise Sensor Analytics Pipeline

## 📌 Project Overview
The objective of this project was to build a robust, end-to-end data pipeline that simulates real-world sensor data ingestion, performs complex transformations, detects anomalies using Machine Learning, and logs detailed data observability metrics to MLflow.

The pipeline is fully automated and runs within a Dockerized environment using **Apache Airflow 3.x**.

---

## 🏗️ Architecture & Data Flow
The project follows a **Medallion Architecture** pattern:
1.  **Bronze (Raw)**: Simulated sensor data is appended to `raw_sensor_data` in PostgreSQL.
2.  **Silver (Enriched)**: Data is validated with **Pydantic**, and new features like *Heat Index* and *Is Anomaly* (via ML) are added.
3.  **Gold (Aggregated)**: Final analytics like **Trend Slopes** and hourly averages are saved to `processed_sensor_metrics`.

---

## 🛠️ Technology Stack
-   **Orchestration**: Apache Airflow 3.1.7 (TaskFlow API)
-   **Storage**: PostgreSQL 16
-   **Tracking & Observability**: MLflow
-   **Data Processing**: Pandas, NumPy, SQLAlchemy
-   **Data Validation**: Pydantic v2
-   **Machine Learning**: Scikit-Learn (Isolation Forest)
-   **Communication**: Gmail SMTP (Direct Injection)

---

## 🚀 Step-by-Step Implementation

### 1. Environment Setup
- **Dockerization**: Configured a `docker-compose.yaml` with services for Airflow (Scheduler, Worker, Webserver, Triggerer), Postgres, Redis, and MLflow.
- **Dependency Management**: Utilized a `.env` file with `_PIP_ADDITIONAL_REQUIREMENTS` to automatically install necessary Python libraries inside the containers.

### 2. Database Automation
- Implemented a `setup_database_schema` task within the DAG.
- This ensures that even on a fresh run, the PostgreSQL table structures are created automatically with the correct data types (`SERIAL`, `TIMESTAMP`, `DOUBLE PRECISION`).

### 3. Data Simulation (Incremental Loading)
- Created a generator that simulates sensor readings for Temperature, Humidity, and Pressure.
- Employed **Incremental Loading** logic using `if_exists="append"`. This preserves historical data and simulates a continuous data stream.

### 4. Advanced Transformation & AI Integration
- **Feature Engineering**: Calculated the *Heat Index* and extracted temporal features (hour).
- **Trend Analysis**: Implemented a **Linear Regression Slope** calculation to identify if temperatures are trending up or down.
- **Anomaly Detection**: Integrated an **Isolation Forest** ML model to automatically flag statistically unlikely readings.

### 5. Data Observability (MLflow)
- Logged exhaustive **Statistical Distributions** (Mean, Std Dev, Min, Max) for all sensor metrics.
- Tracked system metadata (Python version, Airflow Dag ID, Docker Node).
- **Data Quality & Lineage**: Implemented **Data Versioning** using MD5 hashing and formal **MLflow Dataset Tracking** (`mlflow.log_input`) to record exactly which data was used in each run.
- **Evidence Retrieval**: Uploaded run-time artifacts including a `metadata.json` audit log and a `sample_data.csv` snapshot.

### 6. Intelligent Alerting
- Configured a **Direct SMTP** email system.
- **Success Report**: Sends a formatted HTML table of sensor aggregates to the user's Gmail.
- **Failure Alert**: Sends a critical notification if any task in the pipeline fails.

---

## 📋 How to Run & Monitor

### 1. Configuration
Ensure your `.env` file contains the correct SMTP credentials:
```text
AIRFLOW__SMTP__SMTP_PASSWORD=hwaobelabsyibfgg  # Google App Password
AIRFLOW__SMTP__SMTP_USER=modivanshnikunjkumar@gmail.com
```

### 2. Execution
1.  Start the stack: `docker-compose up -d`.
2.  Open Airflow at `http://localhost:8080` and trigger the `etl_mlflow_postgres_pipeline`.
3.  Monitor the MLflow dashboard at `http://localhost:5000`.

### 3. Verification
- **Postgres**: Check the `data_pipe` database for `processed_sensor_metrics`.
- **Email**: Check your inbox for the successful completion report.
- **MLflow**: Review artifacts and "Full Audit" run metadata.

---

## 🏆 Key Achievements
- **Idempotency**: The DAG can be re-run safely without causing schema corruption.
- **Professional Scalability**: Uses modern decorators and high-perf libraries.
- **Security**: Implemented Gmail App Password integration for secure notifications.
