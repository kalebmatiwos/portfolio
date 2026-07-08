Active_User_List = []
try:
    with open('Active_Users.txt', 'r') as file:
        for Act_User_List in file:
            Active_User_List.append(Act_User_List.strip())
except FileNotFoundError:
    print("Active users list not found")

def save_Active_Users(Active_User_List):
    # Save added user back to Active_Users.txt file
    try:
        with open('Active_Users.txt', 'w') as file:
            for User in Active_User_List:
                file.write(User + '\n')
    except Exception as e:
        print(f"Error saving active users: {e}")

Disabled_User_List = []
try:
    with open('Disabled_Users.txt', 'r') as file:
        for Dis_User_List in file:
            Disabled_User_List.append(Dis_User_List.strip())
except FileNotFoundError:
    print("Disabled user list not found")

def save_Disabled_Users(Disabled_User_List):
    # Save added user back to Disabled_Users.txt file
    try:
        with open('Disabled_Users.txt', 'w') as file:
            for User in Disabled_User_List:
                file.write(User + '\n')
    except Exception as e:
        print(f"Error saving disabled users: {e}")

def print_Type_of_user():
    print("1. Active User")
    print("2. Disabled User")

def print_main_menu():
    print("Main Menu")
    print("1. Add User")
    print("2. View Active/Disabled Users")
    print("3. Enable/Disable User")
    print("0. Exit")

while True:
    print_main_menu()
    try:
        User_input = int(input("Please input the index of your choice: "))
    except ValueError:
        print("Invalid input, please enter a number.")
        continue

    if User_input == 0:
        print("Exiting app, Thank you for using the app")
        print("User list has been updated")
        save_Active_Users(Active_User_List)
        save_Disabled_Users(Disabled_User_List)
        break

    elif User_input == 1:
        while True:
            print_Type_of_user()
            try:
                User_type_choice = int(input('Please choose the type of user you want to add (1 or 2): '))
            except ValueError:
                print("Invalid input, please enter 1 or 2.")
                continue
            if User_type_choice == 1:
                New_Active_User = input("Input the new active user: ")
                if New_Active_User in Active_User_List:
                    print("This user already exists")
                else:
                    Active_User_List.append(New_Active_User)
                    print("User added successfully.")
                    break
            elif User_type_choice == 2:
                New_Disabled_User = input("Please input new disabled user: ")
                if New_Disabled_User in Disabled_User_List:
                    print("This disabled user already exists")
                else:
                    Disabled_User_List.append(New_Disabled_User)
                    print("User added successfully.")
                    break
            else:
                print("Please enter a valid input (1 or 2)")

    elif User_input == 2:
        print(f"The Active Users are:\n{Active_User_List}")
        print(f"The Disabled users are:\n{Disabled_User_List}")

    elif User_input == 3:
        while True:
            print_Type_of_user()
            try:
                User_choice = int(input("Please select the choice to view active or disabled list (1 or 2): "))
            except ValueError:
                print("Invalid input, please enter 1 or 2.")
                continue
            if User_choice == 1:
                if not Active_User_List:
                    print("No active users to disable.")
                    break
                print("Please select the index of the user you want to disable:")
                for index, Active_user in enumerate(Active_User_List):
                    print(f"{index}: {Active_user}")
                try:
                    delete_select_index = int(input('Please select the index of the user you want to disable: '))
                    if 0 <= delete_select_index < len(Active_User_List):
                        user_to_move = Active_User_List.pop(delete_select_index)
                        Disabled_User_List.append(user_to_move)
                        print("User disabled successfully.")
                        break
                    else:
                        print('Please enter a valid index.')
                except ValueError:
                    print('Invalid input, please enter a number.')
            elif User_choice == 2:
                if not Disabled_User_List:
                    print("No disabled users to enable.")
                    break
                print("Please select the index of the user you want to enable:")
                for index, Disabled_user in enumerate(Disabled_User_List):
                    print(f"{index}: {Disabled_user}")
                try:
                    delete_select_index = int(input('Please select the index of the user you want to enable: '))
                    if 0 <= delete_select_index < len(Disabled_User_List):
                        user_to_move = Disabled_User_List.pop(delete_select_index)
                        Active_User_List.append(user_to_move)
                        print("User enabled successfully.")
                        break
                    else:
                        print('Please enter a valid index.')
                except ValueError:
                    print('Invalid input, please enter a number.')
            else:
                print("Please enter 1 or 2.")

    else:
        print("Invalid choice, please select 0-3.")
