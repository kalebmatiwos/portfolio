import csv
from db import get_connection

def print_courier_menu():
    print("\n ----- Courier Menu -----")
    print("|\t\t\t|")
    print("| 1. Print Couriers\t|")
    print("| 2. Add Courier\t|")
    print("| 3. Update Courier\t|")
    print("| 4. Remove Courier\t|")
    print("| 0. Main Menu\t\t|")
    print("|\t\t\t|")
    print("------------------------")


# Export all courier records from the database into a CSV file
def export_courier_table_to_csv():

    try:

        # Open database connection
        with get_connection() as conn:
            # Create cursor object
            with conn.cursor() as cur:

                # Open CSV file in write mode
                with open('couriers.csv', 'w', newline='') as csvfile:
                    # Define CSV column names
                    fieldnames = ['courier_id', 'courier_name', 'courier_phone']

                    # Create CSV writer object
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    # Write header row
                    writer.writeheader()

                    # Copy table contents directly into CSV file
                    cur.copy_to(csvfile, 'couriers', sep=",")

    except Exception as e:
        print(f'Error: {e}')



# Print all couriers stored in the database
def print_courier_list():

    try:
        # Open database connection
        with get_connection() as conn:
            # Create cursor object
            with conn.cursor() as cur:

                # SQL query to retrieve all couriers
                cur.execute("""
                    SELECT * FROM couriers
                    ORDER BY courier_id ASC        
                """)

                # Fetch all rows from query result
                couriers = cur.fetchall()

                # Print couriers if records exist
                if couriers:
                    print('ID    Name   Phone')
                    for id, name, phone in couriers:
                        print(f"{id} |  {name}      {phone}")
                else:
                    print(f'No Couriers')

    except Exception as e:
        print(f'Error: {e}')



# Print a single courier using courier ID
def print_courier(courier_id):

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                
                # SQL query to find courier by ID
                sql = """
                SELECT * FROM couriers
                WHERE courier_id = %s
                """

                # Execute parameterised query
                cur.execute(sql, (courier_id,))

                # Fetch one matching record
                courier = cur.fetchone()

                # Print courier if found
                if courier:
                    print(f"You've selected: {courier}")

                else:
                    print("Courier doesn't exist")

    except Exception as e:
        print(f'Error: {e}')



# Add a new courier to the database
def add_courier():

    # Ask user to enter courier details
    new_courier = input("Enter the name of courier: ")          
    new_courier_phone = input("Enter the phone number of courier: ")

    try: 
        with get_connection() as conn:
            with conn.cursor() as cur:

                # SQL INSERT statement
                sql = """
                INSERT INTO couriers (courier_name, courier_phone) 
                VALUES (%s, %s)
                """

                # Execute query with user input
                cur.execute(sql, (new_courier, new_courier_phone))

                # Save changes to database
                conn.commit()

    except Exception as e:
        print(f"Error: {e}")



# Update courier name using courier ID
def update_courier_name(id_choice, new_name):

    try: 
        with get_connection() as conn:
            with conn.cursor() as cur:
                
                # SQL UPDATE statement for courier name
                sql = """
                UPDATE couriers
                SET courier_name = %s
                WHERE courier_id = %s
                """

                # Execute query
                cur.execute(sql, (new_name, id_choice))

                # Save changes
                conn.commit()

    except Exception as e:
        print(f"Error: {e}")



# Update courier phone number using courier ID
def update_courier_phone(id_choice, new_phone):

    try: 
        with get_connection() as conn:
            with conn.cursor() as cur:

                # SQL UPDATE statement for courier phone
                sql = """
                UPDATE couriers
                SET courier_phone = %s
                WHERE courier_id = %s
                """

                # Execute query
                cur.execute(sql, (new_phone, id_choice))

                # Save changes
                conn.commit()

    except Exception as e:
        print(f"Error: {e}")



# Update courier details
def update_courier():

    # Display current courier list
    print_courier_list()

    # Ask user which courier to update
    id_choice = input("Enter the id of a courier you want to update: ")
    
    # Continue only if input is not blank
    if id_choice != "":

        # Print selected courier
        print_courier(id_choice)

        # Ask for updated name
        new_courier_name = input("Enter a new name (leave blank to keep old): ")

        # Update name only if user entered a value
        if new_courier_name != "":
            update_courier_name(id_choice=id_choice, new_name=new_courier_name)

        # Ask for updated phone number
        new_courier_phone = input("Enter a new phone number (leave blank to keep old): ")

        # Update phone only if user entered a value
        if new_courier_phone != "":
            update_courier_phone(id_choice=id_choice, new_phone=new_courier_phone)



# Remove a courier from the database
def remove_courier():

    # Display current couriers
    print_courier_list()

    # Ask user which courier to delete
    delete_id = input("Enter the id of courier to delete: ")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                # SQL DELETE statement
                sql = """
                DELETE FROM couriers
                WHERE courier_id = %s
                """

                # Execute delete query
                cur.execute(sql, (delete_id,))

                # Save changes to database
                conn.commit()

                print("Courier deleted")

    except Exception as e:
        print(f"Error: {e}")



# Main courier menu loop
def courier_menu():

    while True:

        # Display menu options
        print_courier_menu()

        # Ask user for menu option
        courier_choice = input("Enter Option: ")

        # Return to main menu
        if courier_choice == "0":
            break
        
        # Print courier list
        elif courier_choice == "1":
            print_courier_list()

        # Add new courier    
        elif courier_choice == "2":
            add_courier()            

        # Update existing courier        
        elif courier_choice == "3":
            update_courier()

        # Delete courier    
        elif courier_choice == "4":
            remove_courier()
        
        # Handle invalid menu option
        else: 
            print ("Invalid Input")



######################################
# Legacy CSV functions - no longer used
# Data is now stored in the SQL database



# def load_couriers():
#     """Load couriers from couriers.csv file"""

#     # Create empty list to store courier dictionaries
#     couriers = []

#     try:
#         # Open CSV file in read mode
#         with open('couriers.csv', 'r', newline='') as csvfile:
            
#             # Read CSV rows as dictionaries
#             reader = csv.DictReader(csvfile)

#             # Loop through each row in the CSV file
#             for row in reader:

#                 # Create courier dictionary
#                 courier = {
#                     'name': row['name'],
#                     'phone': row['phone']
#                 }

#                 # Add courier to list
#                 couriers.append(courier)

#     # Use default data if file does not exist            
#     except FileNotFoundError:
#         print("Courier not found. Using default couriers.")
#         couriers = [
#             {"name": "John",
#              "phone": "071111111111"},
#             {"name": "Mark",
#              "phone": "072222222222"} 
#         ]

#     return couriers




# def save_couriers(couriers):
#     """Save couriers back to couriers.csv file"""

#     try:
#         # Open CSV file in write mode
#         with open('couriers.csv', 'w', newline='') as csvfile:

#             # Define CSV column names
#             fieldnames = ['name', 'phone']

#             # Create CSV writer object
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#              # Write header row
#             writer.writeheader()

#             # Write each courier dictionary as a row
#             for courier in couriers:
#                 writer.writerow({'name': courier['name'],
#                                  'phone': courier['phone']})

#     except Exception as e:
#         print(f"Error saving couriers: {e}")

#########################################