import psycopg2
import os
from dotenv import load_dotenv

def check_db():
    try:
        # Hardcoding default for check
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="GitVision",
            user="postgres",
            password="postgres"
        )
        print("Successfully connected to GitVision database!")
        conn.close()
    except Exception as e:
        print(f"Error connecting to DB: {e}")

if __name__ == "__main__":
    check_db()
