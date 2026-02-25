
<div align="center">

# ⚙️ MLOps Strategy
### Smart Pump Monitoring & Optimization System

---

[![Airflow](https://img.shields.io/badge/Apache%20Airflow-2.x-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](#)
[![MLflow](https://img.shields.io/badge/MLflow-Model%20Registry-0194E2?style=for-the-badge&logo=mlflow)](#)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](#)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI%2FCD-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](#)

---

**Role**: MLOps  
**Scope**: ML Lifecycle Management, Pipeline Orchestration, Model Governance & Deployment

</div>

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [My Role & Boundaries](#1-my-role--boundaries) |
| 2 | [MLOps Architecture Overview](#2-mlops-architecture-overview) |
| 3 | [Tool Strategy](#3-tool-strategy) |
| 4 | [Airflow — Orchestration Strategy](#4-airflow--orchestration-strategy) |
| 5 | [MLflow — Experiment & Model Strategy](#5-mlflow--experiment--model-strategy) |
| 6 | [Docker — Deployment Strategy](#6-docker--deployment-strategy) |
| 7 | [GitHub Actions — CI/CD Strategy](#7-github-actions--cicd-strategy) *(Not yet decided)* |
| 8 | [Model Governance Strategy](#8-model-governance-strategy) |
| 9 | [Monitoring the ML System Itself](#9-monitoring-the-ml-system-itself) |
| 10 | [Rollback & Recovery Plan](#10-rollback--recovery-plan) |
| 11 | [What I Own vs What I Consume](#11-what-i-own-vs-what-i-consume) |

---

## 1. My Role & Boundaries

As the **MLOps Engineer**, my responsibility is to build and maintain the **infrastructure that makes the ML system reliable, reproducible, and continuously improving** over time.

> I do **not** own the data ingestion, sensor logic, PLC integration, dashboards, or alert rules.
> My job is to make sure **any model trained by this team can be tracked, versioned, deployed, and automatically retrained — without manual effort.**

### What I Own

| Responsibility | My Deliverable |
|---|---|
| **Orchestration** | Airflow DAGs for all ML workflows |
| **Experiment Tracking** | MLflow setup, logging standards, model registry |
| **Containerization** | Docker Compose stack for all services |
| **CI/CD** | GitHub Actions pipelines for testing and deployment |
| **Model Governance** | Promotion rules, versioning policy, rollback procedures |
| **ML System Health** | Monitoring drift, retraining triggers, performance degradation |

---

## 2. MLOps Architecture Overview

```
                      ┌─────────────────────────────────────┐
                      │         MLOps Layer (My Scope)       │
                      └─────────────┬───────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
  ┌───────────────┐        ┌────────────────┐       ┌─────────────────┐
  │  Orchestration│        │ Experiment &   │       │ Containerization│
  │               │        │ Model Registry │       │ & CI/CD         │
  │  Apache       │        │                │       │                 │
  │  Airflow      │        │  MLflow        │       │  Docker +       │
  │               │        │                │       │  GitHub Actions │
  │  - DAG design │        │  - Run logging │       │                 │
  │  - Schedules  │        │  - Versioning  │       │  - Services     │
  │  - Retries    │        │  - Registry    │       │  - Lint/Test    │
  │  - Alerts     │        │  - Promotion   │       │  - Deploy       │
  └───────────────┘        └────────────────┘       └─────────────────┘
          │                         │                         │
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
          ┌───────────────────────────────────────────────────┐
          │     Optimization Execution                        │
          │     Decided by another team member                │
          │     I will implement the infrastructure for       │
          │     whichever approach is chosen                  │
          └───────────────────────────────────────────────────┘
```


## 3. Tool Strategy

### Why These Four Tools

| Tool | Why I Chose It | What It Solves |
|---|---|---|
| **Apache Airflow** | Industry-standard for ML workflow orchestration. Native Python. DAG-based dependencies. | Eliminates manual retraining. Handles retries, failure alerting, scheduling. |
| **MLflow** | Lightweight, self-hosted, no cloud dependency. Integrates with any Python ML library. | Tracks every experiment, versions every model, enforces promotion gates. |
| **Docker** | Ensures every environment — dev, staging, production — is identical. | Prevents "works on my machine" failures. Easy to redeploy anywhere. |
| **GitHub Actions** | Already in the code hosting platform. Free for standard workflows. | Automates testing before any code lands in production. |

### Deliberately Not Using

| Skipped Tool | Reason |
|---|---|
| DVC | MLflow already handles data + model versioning for this scale |
| Kubeflow | Kubernetes is overkill; Docker Compose is sufficient |
| SageMaker / Vertex AI | On-premises Linux server; no cloud budget |
| Weights & Biases | MLflow self-hosted covers all our tracking needs |

---

## 4. Airflow — Orchestration Strategy

### 4.1 My DAG Design Plan

I will build and maintain **4 core DAGs**:

| DAG | Schedule | What It Does | Why This Schedule |
|---|---|---|---|
| `weekly_retrain_dag` | Every Sunday at 02:00 | Full model retrain + evaluation + conditional promotion | **Sunday** = least operationally busy day, no peak tariff or shift activity. **02:00 AM** = dead zone, no competing queries. Model ready before Monday 08:00 staff arrival. |
| `data_quality_dag` | Daily at 00:30 | Validates data freshness and completeness before training | **Daily** = data can break any day, not just retraining day. **00:30** = 30 min after midnight lets the historian flush and close the previous day cleanly. Runs before the 02:00 retrain window so bad data is caught early. |
| `alert_sweep_dag` | Every 5 minutes | Scans `readings_wide` flag columns, writes to `alerts_log` | **Not every 1 min** = avoids flooding `alerts_log` with noise. **Not every 10+ min** = CRITICAL alerts like B-01 and H-03 need fast detection. 5 min is the minimum sustained-condition window that covers all alert rules. |
| `model_validation_dag` | Triggered by retrain DAG | Compares challenger vs. production model; decides promotion | **Event-triggered, not scheduled** = must only run after a fresh, complete retrain — never independently. Uses `TriggerDagRunOperator` to enforce this dependency. |

### 4.2 weekly_retrain_dag — Step-by-Step

```
[Trigger: Sunday 02:00]
        │
        ▼
  [task_1] data_extraction
       Pull last 30 days from readings_wide
       Assert row count ≥ minimum threshold
        │
        ▼
  [task_2] data_validation
       Check for nulls, range violations, stale timestamps
       Raise AirflowSkipException if data is unacceptable
        │
        ▼
  [task_3] feature_engineering
       Compute lag features, z-scores, rolling stats, time encodings
        │
        ▼
  [task_4] train_model
       Model type and algorithm decided by ML Engineer
       Log params + metrics to MLflow
        │
        ▼
  [task_5] compare_vs_production
       Read production RMSE from MLflow registry
       Compare against new run metrics
                   │
          ┌────────┴────────┐
          ▼                 ▼
   [BETTER RMSE]      [NOT BETTER]
          │                 │
          ▼                 ▼
  [task_6a]          [task_6b]
  promote_model      archive_run
  → Production       → Staging only
  MLflow Registry    no promotion
```

### 4.3 Airflow Engineering Decisions

| Decision | My Choice | Reasoning |
|---|---|---|
| **Executor** | `LocalExecutor` | Sufficient for our workload; no need for Celery/Kubernetes |
| **Retry policy** | 2 retries, 5 min delay | Handles transient DB/network issues without spamming alerts |
| **Failure alerting** | Email on DAG failure | Immediate notification to team on broken retraining |
| **Backfill** | Disabled for retrain DAG | Retraining with stale triggers is not meaningful |
| **Data skip guard** | `AirflowSkipException` in validation task | Prevents training on bad data silently |

---

## 5. MLflow — Experiment & Model Strategy

### 5.1 Experiment Structure

I will organize MLflow into **2 experiments** — one per model purpose.

> ⚠️ **Note**: The specific algorithm for each model (e.g. which forecasting or efficiency model to use) is the **ML Engineer's decision, not mine**. My job is to build the tracking infrastructure that works regardless of which algorithm is chosen.

```
MLflow Experiments
│
├── 📁 tank_forecasting_model
│     Every Sunday retrain = 1 run
│     Params: [decided by ML Engineer — logged as-is]
│     Metrics: rmse_val, mae_val, rmse_train
│     Artifacts: model.pkl, forecast_plot.png
│     Note: Algorithm TBD by ML team (time-series model)
│
└── 📁 pump_efficiency_model
      Every Sunday retrain = 1 run
      Params: [decided by ML Engineer — logged as-is]
      Metrics: rmse_val, mae_val, r2_score
      Artifacts: model.pkl, feature_importance.png
      Note: Algorithm TBD by ML team (regression/ML model)
```

### 📋 Recommended Professional Setup — Retraining & Execution Frequency

| Component | Cadence | Reasoning |
|---|---|---|
| 🔮 **Forecast Model** | Weekly retrain | Demand patterns at a pump station are stable and seasonal. Weekly is sufficient to stay accurate without wasting compute. |
| ⚡ **Efficiency Model** | Weekly retrain | Pump degradation is gradual — it builds over days/weeks, not minutes. Weekly retraining captures the trend without overreacting to noise. |
| 📡 **Drift Monitoring** | Daily check | Abnormal sensor behaviour or data distribution shifts can appear any day. Daily monitoring catches this early before it affects the next retrain. |
| 📊 **Predictions / Output** | Hourly or per-minute | Operational usage — how often predictions are served depends on the optimization approach chosen by the responsible team member. |


### 5.2 Model Registry & Staging Strategy

```
              New Run Completed
                    │
                    ▼
           Logged in MLflow
           Stage: None (raw run)
                    │
                    ▼
           Automated Comparison
           (model_validation_dag)
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
    RMSE improved         RMSE worse or equal
          │                    │
          ▼                    ▼
   Move to "Staging"     Keep in "None"
   (human review gate)   (archived)
          │
          ▼
   Manual approval OR
   Auto-promote if
   improvement ≥ 2%
          │
          ▼
   Move to "Production"
   (serving layer loads this — approach decided by responsible team member)
```

### 5.3 Logging Standards I Will Enforce

Every training run **must** log the following — I will enforce this in a shared `mlops_utils.py` module:

```python
# Every training run must call these — governed by mlops_utils.py

mlflow.log_param("model_type", ...)        # e.g. "forecasting" or "efficiency" — name decided by ML team
mlflow.log_param("training_days", 30)
mlflow.log_param("training_date", ...)

mlflow.log_metric("rmse_val", ...)
mlflow.log_metric("mae_val", ...)
mlflow.log_metric("rmse_train", ...)

mlflow.log_artifact("model.pkl")
mlflow.set_tag("promoted", "false")        # Updated on promotion
mlflow.set_tag("data_start", ...)
mlflow.set_tag("data_end", ...)
```

### 5.4 Model Promotion Gate — Rules

| Rule | Threshold | Action if Failed |
|---|---|---|
| Validation RMSE must improve | New RMSE < Production RMSE − 2% | Reject promotion, stay on current prod |
| No NaN in predictions on holdout set | 0 NaN allowed | Hard reject, flag for investigation |
| Training data must have ≥ 25 days | min 36,000 rows | Skip training, alert team |
| Run must complete within time limit | < 30 min wall clock | Timeout, fail DAG |

---

## 6. Docker — Deployment Strategy

### 6.1 Services I Will Containerize

```yaml
# My docker-compose.yaml manages these 4 services:

services:

  postgres:          # Shared DB — not my data design, but I host it
    image: postgres:15
    port: 5432

  airflow-webserver: # DAG UI and API
    build: ./airflow
    port: 8080
    depends_on: [postgres]

  airflow-scheduler: # DAG execution engine
    build: ./airflow
    depends_on: [postgres, airflow-webserver]

  mlflow:            # Experiment tracking UI + model registry
    build: ./mlflow
    port: 5000
    volumes:
      - ./mlruns:/mlruns    # Persisted locally — no S3 needed
```

> **Streamlit** and **Inference** are owned by other team members. I provide the `postgres` and `mlflow` services as dependencies they consume.

### 6.2 Environment Strategy

| Environment | How It Works | Purpose |
|---|---|---|
| **Dev** | `docker-compose up` locally | Local development and DAG testing |
| **Staging** | Branch deploy via GitHub Actions | Integration testing before merge |
| **Production** | Auto-deploy on merge to `main` | Live system on Linux server |

### 6.3 Volume & Persistence Strategy

| Data | How I Persist It |
|---|---|
| PostgreSQL data | Named Docker volume — survives container restarts |
| MLflow run data | Bind mount `./mlruns` to host filesystem |
| Airflow logs | Bind mount `./logs` to host filesystem |
| Airflow DAGs | Bind mount `./dags` — live sync without restart |

---

## 7. GitHub Actions — CI/CD Strategy

> **Not yet decided. The CI/CD tooling, pipeline structure, and deployment approach will be defined once the team finalizes the development workflow.**
>
> My responsibility will be to set up and maintain whatever CI/CD pipeline is agreed upon — covering code quality checks, testing, and automated deployment to the Linux server.

---

## 8. Model Governance Strategy

### 8.1 The Core Question I Answer Every Week

> **"Is the model we're using in production still the best one available?"**

My governance process answers this automatically, every Sunday.

### 8.2 Governance Policy

| Policy | Rule |
|---|---|
| **One production model at a time** | Only one version of each model type lives in `Production` stage |
| **Never delete runs** | All MLflow runs are archived, never deleted — full audit trail |
| **Promotion requires validation** | No model goes to Production without passing the validation DAG |
| **A/B testing not required** | System is advisory; champion/challenger swaps are instantaneous |
| **Manual override allowed** | Team lead can manually promote/demote via MLflow UI — logged automatically |
| **Rollback is one command** | `mlflow models transition-stage` — covered in rollback plan |

### 8.3 Model Performance Tracking

Every week after retraining, I write the following to `model_performance` in PostgreSQL:

| Column | Value |
|---|---|
| `run_id` | MLflow run ID |
| `model_type` | `sarimax` or `xgboost` |
| `rmse_val` | Validation RMSE |
| `mae_val` | Validation MAE |
| `promoted` | 0 or 1 |
| `training_date` | Date of this run |
| `data_start` / `data_end` | Training window used |

This table powers the **"Model RMSE over time"** chart in the Streamlit dashboard — owned by the dashboard team, but I supply the data.

---

## 9. Monitoring the ML System Itself

> The rest of the team monitors the pump. **I monitor the ML system.**

### 9.1 What I Watch

| Signal | How I Detect It | Action |
|---|---|---|
| **Model performance drift** | Weekly RMSE trend in `model_performance` table | Alert if RMSE rises >15% week-over-week |
| **Data volume drop** | Row count check in `data_quality_dag` | Skip training + Slack/email alert |
| **Retraining failure** | Airflow DAG failure notification | Investigate + manual trigger if needed |
| **Serving/output outage** | Missing rows in predictions or optimization table | Alert + notify responsible team member to investigate |
| **Stale production model** | Age check: model in Production > 14 days without new run | Auto-trigger unscheduled retrain |

### 9.2 Alerting I Will Set Up

| Alert | Channel | Trigger |
|---|---|---|
| DAG failure | Email | Any DAG with `failed` state |
| Model not promoted 3 weeks in a row | Email | Suggests distribution shift — needs investigation |
| Data gap > 30 min in `readings_wide` | Email | Feeds the `data_quality_dag` check |
| Serving layer output missing | Log file + email | Notify responsible team member |

---

## 10. Rollback & Recovery Plan

### 10.1 Scenario: Bad Model Promoted to Production

```
Detection: RMSE spike in model_performance table OR
           dashboard team reports bad predictions
           │
           ▼
Step 1: Identify the previous Production run_id in MLflow
           │
           ▼
Step 2: mlflow models transition-stage
        --model-name pump_sarimax
        --version <previous_version>
        --stage Production
           │
           ▼
Step 3: The serving layer picks up the new Production model
        on its next scheduled run (timing decided by the responsible team member)
           │
           ▼
Step 4: Demote the bad model to Archived stage
Step 5: Open investigation DAG run in MLflow for root cause
```

**Total recovery time: < 5 minutes.**

### 10.2 Scenario: Airflow Scheduler Down

```
Docker container restart:
  docker-compose restart airflow-scheduler

If data corruption:
  docker-compose down
  docker-compose up -d
  (DAG state is stored in Postgres — recovers automatically)
```

### 10.3 Scenario: MLflow Server Down

```
Restart:
  docker-compose restart mlflow

MLflow data is bind-mounted → no data loss on restart.
Impact on the serving/optimization layer depends on the execution approach
decided by the responsible team member.
  → MLflow data is bind-mounted → no data loss on restart.
```

---

## 11. What I Own vs What I Consume

| Item | My Ownership | I Consume From |
|---|---|---|
| `readings_wide` table | ❌ Not mine | Data Engineering team |
| `model_performance` table | ✅ I populate it | My MLflow → Postgres write |
| `alerts_log` table | ❌ Not mine | Alert Engine team |
| `pump_health` table | ❌ Not mine — I read it for training features | Data Engineering |
| Training scripts (Forecasting, Efficiency) | ❌ I run them, don't write them | ML Engineer |
| Airflow DAGs | ✅ 100% mine | — |
| MLflow server & registry | ✅ 100% mine | — |
| Docker Compose stack | ✅ 100% mine | — |
| GitHub Actions YAML | ✅ 100% mine | — |
| Model promotion decision | ✅ 100% mine (automated) | MLflow metrics |
| Optimization execution approach | ❌ Not mine — decided by another team member | Responsible team member |
| Infrastructure for optimization | ✅ Mine — I set it up once approach is confirmed | — |
| Streamlit dashboard | ❌ Not mine | Dashboard team |

<div align="center">

---

### 🎯 My One-Line MLOps Mission

> **"Every model trained by this team should be automatically tracked, fairly evaluated against what's already in production, and deployed only if it genuinely improves. If it doesn't improve, we stay safe. If the system breaks, we recover in under 5 minutes."**

---

*📄 MLOps Strategy v1.0 | February 2026 | Author: ONCE*
*Tools: Apache Airflow · MLflow · Docker · GitHub Actions*

</div>
