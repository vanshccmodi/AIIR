from airflow.sdk import dag,task

@dag(
    dag_id="xcom_auto_dag",
)
def xcom_auto_dag():
    @task.python
    def first_task():
        fetched_data={"data" :[1,2,3,4,5]}
        return fetched_data
    
    @task.python
    def second_task(data:dict):
        tr_data=data["data"]
        trr_data=tr_data*2
        return trr_data

    @task.python
    def third_task(data:dict):
        yu_data=data
        return yu_data


    t1=first_task()
    t2=second_task(t1)
    t3=third_task(t2)


xcom_auto_dag()
