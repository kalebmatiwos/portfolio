'''
Before running the application for the first time, run this file (setup_db.py) ONCE to set up tables and load dummy data
!!!Drop your existing tables first if you run into foreign key issues with the order_dummy_values_load() function!!!
'''

from db import get_connection

try:

    connection = get_connection()

    print("Opening cursor...")

    cursor = connection.cursor()

    # =========================
    # CREATE PRODUCTS TABLE
    # =========================

    sql = """
    CREATE TABLE IF NOT EXISTS products (
        product_id SERIAL PRIMARY KEY,
        product_name VARCHAR(255) NOT NULL,
        product_price NUMERIC(5,2) NOT NULL
    )
    """

    cursor.execute(sql)

    # =========================
    # CREATE COURIERS TABLE
    # =========================

    sql = """
    CREATE TABLE IF NOT EXISTS couriers (
        courier_id SERIAL PRIMARY KEY,
        courier_name VARCHAR(100) NOT NULL,
        courier_phone VARCHAR(20) NOT NULL
    )
    """

    cursor.execute(sql)


    
    cursor.execute('''
                create table if not exists status (
                status_id serial primary key,
                order_status text not null
                )
                ''')

    cursor.execute('''
                create table if not exists status (
                status_id serial primary key,
                order_status text not null
                )
                ''')

    cursor.execute('''
                create table if not exists orders (
                order_id serial primary key,
                customer_name text not null,
                customer_address text not null,
                customer_phone VARCHAR(20) not null,
                courier_id integer REFERENCES couriers(courier_id),
                status_id integer not null REFERENCES status(status_id),
                products_id text not null
                )
                ''')

    connection.commit()

    print("Tables created successfully!")

    cursor.close()
    connection.close()

except Exception as ex:

    print("Database setup failed:", ex)


def dummy_values_load():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO couriers (courier_name, courier_phone) VALUES
        ('Alice Johnson', '07123456789'),
        ('Bob Smith', '07234567890'),
        ('Charlie Brown', '07345678901');
                
        INSERT INTO products (product_name, product_price) VALUES
        ('Mocha', '1.99'),
        ('Latte', '2.49'),
        ('Hot Chocolate', '3.99');

        INSERT INTO status (order_status) VALUES
        ('pending'),
        ('order received'),
        ('preparing'),
        ('on the way'),
        ('delivered');        
    """)

    

    conn.commit()
    cur.close()
    conn.close()
    print("Dummy Values loaded")

dummy_values_load()

def order_dummy_values_load():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO orders (customer_name, customer_address, customer_phone, courier_id, status_id, products_id) VALUES
        ('John Doe', '123 Main St', '07123456', 1, 1, '1, 2, 3'),
        ('Jane Smith', '456 Elm St', '5555678', 2, 3, '2'),
        ('Bob Johnson', '789 Oak St', '5559012', 3, 2, '1, 3');        
    """)

    

    conn.commit()
    cur.close()
    conn.close()
    print("Order Dummy Values loaded")

order_dummy_values_load()