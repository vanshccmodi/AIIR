# Airflow and MLflow Integration Setup

This guide documents the complete setup process required to integrate MLflow with our Dockerized Apache Airflow environment, allowing DAGs to seamlessly train models and log metrics to a dedicated MLflow tracking server.

## 1. Environment Configuration (`.env`)

To ensure that Airflow's internal execution containers have access to MLflow and other necessary scientific libraries, we must instruct Airflow to install them on startup. 

We updated the hidden `.env` file to include these Python packages:

```env
AIRFLOW_UID=50000
_PIP_ADDITIONAL_REQUIREMENTS=apache-airflow-providers-postgres mlflow scikit-learn
```
*Note: The Airflow entrypoint script natively checks this variable and runs `pip install` across the Scheduler, Worker, and Webserver containers when they boot.*

## 2. Docker Compose Configuration (`docker-compose.yaml`)

Instead of running MLflow locally on the Windows host machine (which causes complex Docker networking issues and DNS rebinding strictness), we added a dedicated MLflow container directly into the Airflow Docker Compose stack.

Added this service at the bottom of `docker-compose.yaml` (just above `volumes:`):

```yaml
  mlflow:
    image: python:3.9
    command: >
      bash -c "pip install mlflow && 
               mlflow server --host 0.0.0.0 --port 5000"
    ports:
      - "5000:5000"
    volumes:
      - ./mlflow:/mlflow
```

## 3. Version Control (`.gitignore`)

Since MLflow will generate persistent artifacts, databases, and experiment metrics locally in our `./mlflow` volume mapping, we must ensure these are not pushed to Git. 

Appended the following to `.gitignore`:

```text
# MLflow
mlflow/
mlruns/
mlruns.db
.trash/
```

## 4. The Data Pipeline (`dags/mlflow_airflow_pipeline.py`)

We structured our DAG to point directly to our newly created Docker service via internal DNS (`http://mlflow:5000`).

```python
from airflow.decorators import dag, task
from datetime import datetime
import mlflow
import mlflow.sklearn
from sklearn.datasets import load_diabetes
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

@dag(
    dag_id="mlflow_airflow_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["mlflow"]
)
def mlflow_airflow_pipeline():

    @task
    def train_model():
        # Set the MLflow tracking URI to point to the MLflow container
        mlflow.set_tracking_uri("http://mlflow:5000")
        mlflow.set_experiment("Airflow_MLflow_Demo")

        # Load data
        X, y = load_diabetes(return_X_y=True)
        X_train, X_test, y_train, y_test = train_test_split(X, y)

        # Train model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Evaluate model
        score = model.score(X_test, y_test)

        # Log parameters, metrics, and the model to MLflow
        with mlflow.start_run():
            mlflow.log_param("model_type", "LinearRegression")
            mlflow.log_metric("score", score)
            mlflow.sklearn.log_model(model, "model")

    # Call the task sequence
    train_model()

# Instantiate the DAG
dag_instance = mlflow_airflow_pipeline()
```

## 5. How to Run the Stack

1. **Boot the environment**:
   Open a terminal in the root directory and start the entire stack in detached mode:
   ```bash
   docker compose down
   docker compose up -d
   ```
   *(Note: The `mlflow` container takes about 60 seconds on first boot to download dependencies before the tracking server goes live).*

2. **Access MLflow**:
   Open your browser and navigate to: [http://localhost:5000](http://localhost:5000)

3. **Trigger the Pipeline**:
   Open Airflow at [http://localhost:8080](http://localhost:8080). Unpause the `mlflow_airflow_pipeline` DAG and manually trigger it. 

4. **Verify**:
   Once the Airflow task succeeds, refresh the MLflow UI. You will see the new `Airflow_MLflow_Demo` experiment complete with logged parameters, accuracy metrics, and the serialized scikit-learn model artifact!
