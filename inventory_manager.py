import json

print(f"==========================\nInventory Manager System\n==========================\n")

#funciton to find json to load inventory

print(f"----------Menu----------\n1. Display All Products\n2. Add Product\n3. Update Stock\n4. Search Product\n5. Save Inventory\n6. Exit\n------------------------\n")

option = input("Enter option (1-6): ")
if option == "1":
#Current Inventory
    print(f"Current Inventory:\n--------------------")
elif option == "2":

elif option == "2":
elif option == "2":
elif option == "2":
elif option == "6":
    quit = print(input("Are you sure you want to exit? (y/n): "))
    if quit == 'y':
        quit
    elif quit == 'n':
        return 'inflow',False
    else:
            print("Invalid input. Please enter 'y' or 'n'.")
            return swaptransaction()  # Recursively call until valid input is received

    elif option == "2
if option == "1":


#The store manager needs a system that remembers inventory levels even after the 
#program closes. Furthermore, they need to store a history of all transaction amounts, 
#not just the running total. 
#Requirements 
#1. Data Representation: 
#Represent inventory items using dictionaries and store at least three products in a 
#list.  






#2. Data Manipulation: 
#Maintain your functional design. Create add_product(), update_stock(), 
#search_product() and display_all() fuctions in inventory dictionary.  

#add_product()

#update_stock()

#search_product()

#display_all()

#3. Data Persistence:  
#Check whether inventory.json exists. Create load_inventory() to load 
#inventory.json if it exists. Otherwise, begin with an empty inventory. Create 
#save_inventory() and save data to inventory.json.  
#4. Build a Menu System: 
#Create menu options for Display, Add, Update, Search, Save and Exit.

# Initialize Your Workspace & Git 
#1. Initialize and track your work. 
#2. Commit your progress after you successfully complete each phase: 
#a. After creating the Dictionary and adding few products 
#b. After load_inventory() is working. 
#c. After the final save_inventory() is verified. 
#3. Finally push the code to your github repository. 