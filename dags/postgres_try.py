from datetime import datetime, timedelta

from airflow.sdk import dag
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

default_args = {
    'owner': 'once',
    'retries': 5,
    'retry_delay': timedelta(minutes=5)
}

@dag(
    dag_id='dag_with_postgres_operator_v1',
    default_args=default_args,
    start_date=datetime(2025, 10, 5),
    schedule='@daily',
    catchup=False
)
def postgres_try_dag():

    # Task 1: Create first table (dag_runs)
    create_dag_runs_table = SQLExecuteQueryOperator(
        task_id='create_dag_runs_table',
        conn_id='postgres_localhost',
        sql="""
            drop table if exists dag_runs;
            create table if not exists dag_runs (
                dt date,
                dag_id character varying,
                primary key (dt, dag_id)
            );
        """
        
    )

    # Task 2: Create second table (user_activity)
    create_user_activity_table = SQLExecuteQueryOperator(
        task_id='create_user_activity_table',
        conn_id='postgres_localhost',
        sql="""
            create table if not exists user_activity (
                id serial primary key,
                username character varying not null,
                activity_date date,
                action character varying
            );
        """
    )

    # Task 3: Insert into dag_runs
    insert_into_dag_runs = SQLExecuteQueryOperator(
        task_id='insert_into_dag_runs',
        conn_id='postgres_localhost',
        sql="""
            insert into dag_runs (dt, dag_id) values 
            ('{{ ds }}', '{{ dag.dag_id }}')
            on conflict (dt, dag_id) do nothing;
        """
    )

    # Task 4: Insert multiple rows into user_activity
    insert_into_user_activity = SQLExecuteQueryOperator(
        task_id='insert_into_user_activity',
        conn_id='postgres_localhost',
        sql="""
            insert into user_activity (username, activity_date, action) values 
            ('modi', '{{ ds }}', 'triggered_dag'),
            ('admin', '{{ ds }}', 'reviewed_logs'),
            ('coder2j', '{{ ds }}', 'wrote_code');
        """
    )

    # Define dependencies
    create_dag_runs_table >> insert_into_dag_runs
    create_user_activity_table >> insert_into_user_activity

postgres_try_dag()
