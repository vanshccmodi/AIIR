# AIIR - Airflow Intensive Learning Repository 🚀

A comprehensive collection of Apache Airflow DAGs and configurations developed to master data orchestration, workflow automation, and ETL pipelines.

## 🌟 Overview

This project serves as a structured learning journey into the world of **Apache Airflow**. From foundational concepts like DAG definition and scheduling to advanced topics like XCom data sharing, task parallelism, and incremental loading, this repository documents the evolution of my data engineering skills.

## 🧠 What I Learnt

Through this project, I have mastered the following core concepts:

### 1. Fundamentals of Data Orchestration
*   **DAG Definition**: Learned how to define Directed Acyclic Graphs with specific `start_dates`, `catchup` policies, and `schedules`.
*   **Sequential vs. Parallel Execution**: Understood how to chain tasks linearly and how to branch them for parallel processing to optimize execution time.

### 2. Advanced Communication (XComs)
*   **Auto-XComs**: Leveraged Airflow's automatic return value tracking.
*   **Manual XComs**: Implemented `ti.xcom_push` and `ti.xcom_pull` for explicit data sharing between complex tasks.

### 3. Dynamic Workflow Management
*   **DAG Versioning**: Explored strategies for maintaining and iterating on DAG logic without losing historical context.
*   **Operators**: Experimented with various operators (PythonOperator, BashOperator, etc.) to handle diverse task types.

### 4. Efficient Data Loading
*   **Incremental Loads**: Implemented logic to process only new or changed data, a critical pattern for production-grade ETL pipelines.
*   **Data Dependencies**: Managed complex dependencies where tasks wait for specific data states before proceeding.

### 5. Infrastructure & Deployment
*   **Dockerized Airflow**: Successfully set up a full Airflow environment (Webserver, Scheduler, Postgres) using `docker-compose`.
*   **Environment Management**: Used `.env` files and secret management to keep configurations secure and portable.

## 📂 Repository Structure

*   `dags/`: The heart of the project, containing various DAG implementations:
    *   `1_first_dag.py`: The beginning - basic structure and simple tasks.
    *   `3_operators.py`: Deep dive into different Airflow operators.
    *   `4_xcom_auto.py` & `5_xcom_manual.py`: Mastering data sharing between tasks.
    *   `6_parallel_tasks.py`: Implementing parallel execution branches.
    *   `11_incremental_load.py`: Building production-ready incremental ETL logic.
*   `docker-compose.yaml`: Configuration for local development environment.
*   `plugins/`: Custom hooks and operators for extended functionality.

## 🛠️ Setup & Usage

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/vanshccmodi/AIIR.git
    cd AIIR
    ```

2.  **Initialize Airflow**:
    ```bash
    docker-compose up -d
    ```

3.  **Access the UI**:
    Open `http://localhost:8080` in your browser. Default credentials are usually `airflow/airflow`.

---

*This project is a testament to my growth in Data Engineering. Happy Orchestrating!* 🛠️📊
