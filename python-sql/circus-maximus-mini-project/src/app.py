products_list = ["Mocha", "Americano", "Cappucino", "Latte", "Tea"]

def print_main_menu():
    print(" ------ Main Menu ------")
    print("|\t\t\t|")
    print("| 1. Products Menu\t|")
    print("| 0. Exit\t\t|")
    print("|\t\t\t|")
    print("------------------------")

def print_product_menu():
    print("\n ------ Products Menu ------")
    print("|\t\t\t|")
    print("| 1. Products list\t|")
    print("| 2. Add product\t|")
    print("| 3. Update product\t|")
    print("| 4. Remove product\t|")
    print("| 0. Main Menu\t\t|")
    print("|\t\t\t|")
    print("------------------------")

while True:
    print_main_menu()
    user_input = input("Enter option: ")

    if user_input == "0":
        print("Exiting app...")
        break

    elif user_input == "1":
        while True:
            print_product_menu()
            product_choice = input("Enter option: ")

            if product_choice == "0":
                break

            elif product_choice == "1":
                print(products_list)

            elif product_choice == "2":
                new_product = input("Enter the name of the new product: ")
                products_list.append(new_product)
                print(products_list)
                print("New product added")

            elif product_choice == "3":
                check_product = input("Enter the name of the product that you want to update: ")
                if check_product in products_list:
                    print("The product is in the list")

                    index = products_list.index(check_product)          # get the position of the item
                    updated_product = input("Enter the updated product: ")      # get new value from the user
                    products_list[index] = updated_product              # replace/update the old value at the correct position with a new one 
                    
                    print(products_list)

                else:
                    print("invalid product")

            elif product_choice == "4":
                print(f"Here are the current products: {products_list}")

                index = int(input("Enter the index of the product to be deleted: "))
                products_list.pop(index)

                print(f"Here is the new product list: {products_list}")


            else:
                print("invalid input")


    else:
        print("Invalid input")

