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
