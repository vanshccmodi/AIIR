import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            dbname='postgres',
            user='airflow',
            password='airflow',
            host='localhost' # Since I'm running this from the host machine (Windows)
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if data_pipe exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname='data_pipe'")
        exists = cur.fetchone()
        
        if not exists:
            print("Creating database 'data_pipe'...")
            cur.execute("CREATE DATABASE data_pipe")
        else:
            print("Database 'data_pipe' already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_database()
