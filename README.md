# AIIR - Airflow Intensive Learning Repository 🚀

A comprehensive, production-grade collection of Apache Airflow DAGs and configurations developed to master data orchestration, workflow automation, and high-performance ETL pipelines.

## 🌟 Overview

This project is a technical documentation of my journey from Airflow basics to complex orchestration patterns. It doesn't just contain simple scripts; it explores how Airflow handles state, data passing, and multi-DAG dependencies in real-world scenarios.

🎨 **Visual Learner?** Check out my [Airflow Theory Notes (SVG)](./Airflow_Notes.svg) for a structured breakdown of the architectural concepts I've mastered.

---

## 🧠 Technical Deep Dive: What I Learnt

### 1. Advanced Task Dependencies & Parallelism
*   **Sequential vs. Fan-out/Fan-in**: Implemented "Diamond" dependency patterns where a single extraction task feeds into multiple parallel transformation tasks, which then aggregate back into a single load task.
*   **Optimizing Throughput**: Learned how to define parallel branches in `6_parallel_tasks.py` to maximize worker utilization.

### 2. The XCom Data-Sharing Protocol
*   **State Persistence**: Understood how Airflow uses the metadata database to store task outputs (XComs).
*   **Explicit Workflows**: Used `ti.xcom_push` and `ti.xcom_pull` to share specific keys between tasks across different operators.
*   **Implicit Results**: Leveraged the **TaskFlow API** to automatically pass results between `@task` decorated functions, significantly reducing boilerplate code.

### 3. Conditional Branching & Dynamic Logic
*   **Runtime Decision Making**: Implemented `@task.branch` in `7_branches.py` to choose execution paths based on data status (e.g., skips "Load" tasks on weekends).
*   **Skipping Logic**: Mastered how Airflow handles 'skipped' tasks in the graph and how it affects downstream dependencies.

### 4. Precision Scheduling & Incremental ETL
*   **Cron vs. Timetables**: Explored high-precision scheduling using Cron expressions (`9_schedule_cron.py`) and Delta intervals.
*   **The Catchup Mechanism**: Deep investigation into `catchup=True` to understand how Airflow backfills historical data when a DAG is first enabled.
*   **Incremental Processing**: Used `data_interval_start` and `data_interval_end` tokens in `11_incremental_load.py` to ensure tasks only process data within their specific execution window, preventing data duplication.

### 5. Multi-DAG Orchestration (The Parent-Child Pattern)
*   **Modular Architecture**: Learned that monolithic DAGs are hard to maintain, so I implemented a **Parent-Child** orchestration pattern using the `TriggerDagRunOperator`.
*   **Cross-DAG Synchronization**: Configured `wait_for_completion=True` to create a synchronous flow between independent DAG files, allowing for cleaner, decoupled project structures.

---

## 📂 Detailed File Breakdown

| File | Core Learning Concept | Complexity |
| :--- | :--- | :--- |
| `1_first_dag.py` | Basic DAG structure, Task IDs, and the `>>` operator. | ⭐ |
| `3_operators.py` | Mixing `PythonOperator` and `BashOperator` in a single workflow. | ⭐ |
| `4_xcom_auto.py` | Automated XCom behavior in TaskFlow API. | ⭐⭐ |
| `5_xcom_manual.py` | Explicit `xcom_push/pull` for complex multi-key data passing. | ⭐⭐ |
| `6_parallel_tasks.py` | Fan-out/Fan-in architecture for parallel processing. | ⭐⭐⭐ |
| `7_branches.py` | Implementing `decider` tasks with `@task.branch`. | ⭐⭐⭐ |
| `11_incremental_load.py` | Mastering `data_interval` tokens for idempotent ETL runs. | ⭐⭐⭐ |
| `dag_orchestrate_parent.py` | High-level orchestration using `TriggerDagRunOperator`. | ⭐⭐⭐⭐ |

---

## 🛠️ Infrastructure & Setup

### Dockerized Environment
The environment is powered by **Docker Compose**, running a multi-container stack:
*   **PostgreSQL**: The metadata database tracking task states and XComs.
*   **Webserver**: The Flask-based UI for monitoring and manual triggering.
*   **Scheduler**: The heart of Airflow that monitors DAGs and triggers tasks.

### Local Development
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/vanshccmodi/AIIR.git
    cd AIIR
    ```
2.  **Environment Variables**: Ensure your `.env` is configured (refer to the `.env` template if provided).
3.  **Spin up the Stack**:
    ```bash
    docker-compose up -d
    ```
4.  **Access the Dashboard**: Navigate to `http://localhost:8080`.

---

*This project is a testament to my growth in Data Engineering. It reflects a deep understanding of how to build resilient, scalable, and manageable data workflows.* 🛠️📊
