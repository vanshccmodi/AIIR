from airflow.sdk import dag, task

@dag(
    dag_id="xcom_dag_manual",
)
def xcom_dag_manual():
    @task.python
    def first_task(**kwargs):
        ti = kwargs["ti"]
        ti.xcom_push(key="data", value={"data": [1, 2, 3, 4, 5]})
    
    @task.python
    def second_task(**kwargs):
        ti = kwargs["ti"]
        # Pull data. Using .get() or checking for None is safer, but dependencies will fix the immediate crash
        pull_result = ti.xcom_pull(task_ids='first_task', key='data')
        if pull_result:
            data = pull_result['data']
            data2 = data * 3
            ti.xcom_push(key="data2", value={"data2": data2})
        else:
            raise ValueError("No data found from first_task")

    @task.python
    def third_task(**kwargs):
        ti = kwargs["ti"]
        data = ti.xcom_pull(task_ids='second_task', key='data2')
        print(f"Received data: {data}")

    t1 = first_task()
    t2 = second_task()
    t3 = third_task()

    # Define dependencies
    t1 >> t2 >> t3

xcom_dag_manual()




