import psycopg2 
import os

from dotenv import load_dotenv

# =========================
# LOAD ENVIRONMENT VARIABLES
# =========================

load_dotenv()

host_name = os.environ.get("POSTGRES_HOST")
database_name = os.environ.get("POSTGRES_DB")
user_name = os.environ.get("POSTGRES_USER")
user_password = os.environ.get("POSTGRES_PASSWORD")


# =========================
# CONNECT TO DATABASE
# =========================

def get_connection():

    connection = psycopg2.connect(
        host=host_name,
        dbname=database_name,
        user=user_name,
        password=user_password
    )

    return connection