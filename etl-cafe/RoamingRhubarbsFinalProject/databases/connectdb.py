import psycopg2
import json
import os
import boto3
from dotenv import load_dotenv


# Loads the Environment variables
load_dotenv()

host_name = os.environ.get("POSTGRES_HOST")
database_name = os.environ.get("POSTGRES_DB")
user_name = os.environ.get("POSTGRES_USER")
user_password = os.environ.get("POSTGRES_PASSWORD")
port = int(os.getenv("POSTGRES_PORT", 5432))




# Uses the environment variables to connect to the DB
def get_connection():

    connection = psycopg2.connect(
        host=host_name,
        dbname=database_name,
        user=user_name,
        password=user_password,
        port = port
    )

    return connection

def get_redshift_config_from_ssm(parameter_name):
    ssm_client = boto3.client("ssm")

    response = ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True     
    )
    return json.loads(response["Parameter"]["Value"])

def get_redshift_connection(parameter_name):
    config = get_redshift_config_from_ssm(parameter_name)

    connection = psycopg2.connect(
        host=config["host"],
        dbname=config["database-name"],
        user=config["user"],
        password=config["password"],
        port=config.get("port", 5439)  # Default Redshift port is 5439
    )

    return connection



