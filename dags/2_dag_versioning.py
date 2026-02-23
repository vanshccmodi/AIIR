from airflow.sdk import dag,task

@dag(
    dag_id="versioning_dag",
)
def versioning_dag():
    @task.python
    def first_task():
        print("this is the first task")
    
    @task.python
    def second_task():
        print("this is the second task")

    @task.python
    def third_task():
        print("this is the third task")

    @task.python
    def fourth_task():
        print("this is the fourth task")

    @task.python
    def fifth_task():
        print("this is the fifth task")

    t1=first_task()
    t2=second_task()
    t3=third_task()
    t4=fourth_task()
    t5=fifth_task()

    t1>>t2>>t3>>t4>>t5

versioning_dag()