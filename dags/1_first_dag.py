from airflow.sdk import dag,task

@dag(
    dag_id="first_dag",
)
def first_dag():
    @task.python
    def first_task():
        print("this is the first task")
    
    @task.python
    def second_task():
        print("this is the second task")

    @task.python
    def third_task():
        print("this is the third task")

    t1=first_task()
    t2=second_task()
    t3=third_task()

    t1>>t2>>t3

first_dag()
