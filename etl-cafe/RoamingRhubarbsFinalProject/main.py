# THIS CODE WILL RUN THE FULL ETL PIPELINE
from databases import connectdb
from ETL import Extract, transform
from ETL.load import load_all
import time



def wait_for_db():
    while True:
        try:
            with connectdb.get_connection() as conn:
                print("Database is ready!")
            return
        except Exception as e:
            print(f"Waiting for database... {e}")
            time.sleep(2)


def main():
    rawdata = Extract.get_data()
    transformed_data = transform.etl_transform(rawdata)

    with connectdb.get_connection() as conn:
        load_counts = load_all(transformed_data, conn)

    print("Load completed successfully.")
    print(load_counts)


if __name__ == "__main__":
    wait_for_db()
    main()