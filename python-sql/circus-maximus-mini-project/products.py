import csv
import os
from dotenv import load_dotenv
import csv
import psycopg2


def print_product_menu():
    print("\n ------ Products Menu ------")
    print("|\t\t\t|")
    print("| 1. Print Products\t|")
    print("| 2. Add Product\t|")
    print("| 3. Update Product\t|")
    print("| 4. Remove Product\t|")
    print("| 0. Main Menu\t\t|")
    print("|\t\t\t|")
    print("------------------------")




def product_menu():
            while True:
                print_product_menu()
                product_choice = input("Enter option: ")

                if product_choice == "0":
                    break

                elif product_choice == "1":
                    # gets all the products from the database and prints them
                    retrieve_products()
                    
                elif product_choice == "2":
                    while True:
                        # Gets input for a new product and inserts it into database
                        try:         
                            new_product = input("Enter new product name: ")
                            new_product_price = float(input("Enter a price for this product: "))
                            product_name = new_product
                            if check_product_exists(product_name) == False:
                                insert_products(new_product, new_product_price)
                                retrieve_products()
                                break
                            else:
                                cursor.close()
                        except: 
                            print("Invalid Input")
                            cursor.close()
                            break
                            
                elif product_choice == "3":
                    while True:
                        # Calls upon functions to print the database and update either name or price using the previously selected id. If it is blank it will pass the function to update 
                        #MISSING ERROR HANDLING
                        try:
                            retrieve_products()
                            select_id = (input("Please select an id to update: "))
                            if retrieve_product(select_id) == False:
                                break
                            else:
                                print("Product selected ")
                                upd_name = input("Please select a new name - Leave blank to keep: ")
                                if upd_name != "":
                                    product_name = upd_name
                                    if check_product_exists(product_name) == False:
                                        update_products_name(select_id, upd_name)
                                        pass
                                    else:
                                        break
                                else:
                                    pass
                                
                                    upd_price = (input("Please select a new price - Leave blank to keep: "))
                                    if upd_price != "":
                                        update_product_price(select_id, upd_price)
                                        pass 
                                    else:
                                        pass
                                    break
                        except:
                            print("Invalid Input ")
                            cursor.close()
                            break

                elif product_choice == "4":
                    # Retrieves a list of products and deletes via id input from the database
                    while True:
                        try:
                            retrieve_products()
                            delete_id = (input("Please select the ID of what you want to delete: "))
                            delete_product(delete_id)
                            break
                        except:
                            print("Invalid Input")
                            cursor.close()
                            break


####################################################################
#Database code - Some will be replaced when merged


# Connects to the database and gets all details from .env
load_dotenv()
host_name = os.environ.get("POSTGRES_HOST")
database_name = os.environ.get("POSTGRES_DB")
user_name = os.environ.get("POSTGRES_USER")
user_password = os.environ.get("POSTGRES_PASSWORD")



conn_string = f'host={host_name} dbname={database_name} user={user_name} password={user_password}'
# Establishes a database connection
try:
    with psycopg2.connect(conn_string) as connection:

        # print('Opening cursor...')
        cursor = connection.cursor()
except:
    print("WARNING - Failed to connect to database ")

#Inserts a new product into the table
def insert_products(new_product, new_product_price):
    cursor = connection.cursor()
    insert = '''
    INSERT INTO products (product_name, product_price)
    VALUES (%s,%s)
    '''

    cursor.execute(insert, (new_product, new_product_price))
    connection.commit()

    cursor.close()

# Retrieves all products from the table with id name and price and also pulls the collumn names and prints them
def retrieve_products():
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM products')
    products = (cursor.fetchall())
    #Next two lines gets the column names puts them in a list and prints them
    field_name = [desc[0] for desc in cursor.description]
    print(field_name)
    for product_id, product_name, product_price in products:
        print(product_id, product_name, product_price)
    cursor.close()

#Retrieves a single product from a selected ID and prints it
def retrieve_product(select_id):
    cursor = connection.cursor()
    product_pull = '''SELECT * FROM products
    WHERE product_id = %s'''
    cursor.execute(product_pull, select_id)
    product_id_check = cursor.fetchone()
    if product_id_check == None:
        print("Product does not exist ")
        cursor.close()
        return False
    else:
        product_id, product_name, product_price = product_id_check
        print(product_id, product_name, product_price)
        cursor.close()

        
# Updates the name of a product based off of ID
def update_products_name(select_id, upd_name):
    cursor = connection.cursor()
    
    update = '''
    UPDATE products
    SET product_name =%s
    WHERE product_id = %s
    '''
    cursor.execute(update, (upd_name, select_id))
    connection.commit()
    
    cursor.close()
# Updates the price of a product based off of ID
def update_product_price(select_id, upd_price):
    cursor = connection.cursor()
    
    update = '''
    UPDATE products
    SET product_price =%s
    WHERE product_id = %s
    '''
    cursor.execute(update, (upd_price, select_id))
    connection.commit()
    
    cursor.close()

#Deletes a product off the table using ID
def delete_product(delete_id):
    cursor = connection.cursor()
    delete = 'DELETE FROM products WHERE product_id =%s'
    cursor.execute(delete, (delete_id))
    
    connection.commit()
    
    cursor.close()


# Searches if the name given is already in the database and returns true or false if it exists or not
def check_product_exists(product_name):
    cursor = connection.cursor()
    check_product = '''SELECT * FROM products
    WHERE product_name = %s'''
    cursor.execute(check_product,(product_name,))
    check = cursor.fetchone()
    if check is not None:
        print("Product already exists")
        return True
        
    else:
        print("Adding Product")
        return False
    

    ####################################################################################
    # Exporting to csv
def export_products_csv():
    try:
        # Gets products
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM products')
        products = (cursor.fetchall())
        headers = ["product_id","product_name","product_price"]
    # Converts a tuple to a dict entry - Zip makes the header take the tuple returned as values dict then converts the tuple to a dict format of key:value
        products_conv = [ dict(zip(headers, product))
        for product in products ]
     #Save products back to Products.csv file
        with open('Products.csv', 'w', newline="") as file:
            f = csv.DictWriter(file, fieldnames=headers)
            f.writeheader()
            f.writerows(products_conv)

            cursor.close()
    except Exception as e:
        print(f"Error exporting products: {e}")
        cursor.close()