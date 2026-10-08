import json
import os
from datetime import datetime
 
FILENAME = "inventory.json"
  
#1 Persistence
#1a find json file and load it if it exists, otherwise start with an empty inventory.
def load_inventory():
    """Load data from inventory.json if it exists, otherwise start empty."""
    if os.path.exists(FILENAME):
        try:
            #read file and load data
            with open(FILENAME, "r") as f:
                data = json.load(f)
            print(f"{FILENAME} found. Inventory loaded successfully.")
            #call data with products, transactions
            return data["products"], data.get("transactions", [])
        #ERROR HANDLING: fallback if cannot use file
        except (json.JSONDecodeError, KeyError):
            print(f"{FILENAME} is corrupted. Starting with empty inventory.")
    else:
        print(f"{FILENAME} not found. Starting with empty inventory.")
        #empty inventory and transaction history
    return [], []
 
 #1b Save the inventory and transaction history to inventory.json
def save_inventory(inventory, transactions):
    """Save products and the full transaction history to inventory.json."""
    #writes file, will override
    with open(FILENAME, "w") as f:
        json.dump({"products": inventory, "transactions": transactions}, f, indent=4)
    print(f"Inventory saved successfully to {FILENAME}.")
 
 #2 Helpers
 #2a Record transaction history
def record_transaction(transactions, product_id, change, kind):
    """Append one entry to the transaction history (never overwritten)."""
    #format Time, id, type, stock qty
    transactions.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_id": product_id,
        "type": kind,
        "change": change,
    })
 
 #2b find product by ID
def find_product(inventory, product_id):
    """Return the product dictionary with the given ID, or None."""
    for product in inventory:
        #match id to lowercase input id
        if product["id"].lower() == product_id.lower():
            return product
    return None
 
 #2c Read number input with validation
def read_number(prompt, cast, minimum=0):
    """Keep asking until the user enters a valid number >= minimum."""
    while True:
        try:
            value = cast(input(prompt))
            #less than 0 = reject
            if value < minimum:
                print(f"Value must be at least {minimum}.")
                continue
            return value
        #not number = reject
        except ValueError:
            print("Invalid input. Please enter a number.")
 
 
# 3 Core functions
#3a Display all products in inventory
def display_all(inventory):
    print("\nCurrent Inventory")
    print("-" * 48)
    if not inventory:
        print("No products in inventory.")
    for p in inventory:
        print(f"ID: {p['id']} | Name: {p['name']} | "
              f"Price: ${p['price']:.2f} | Stock: {p['stock']}")
    print("-" * 48)
 
 
def add_product(inventory, transactions):
    print("\nAdd New Product")
    product_id = input("Product ID: ").strip()
    if not product_id:
        print("Product ID cannot be empty.")
        return
    if find_product(inventory, product_id):
        print("Product ID already exists.")
        return
    name = input("Product Name: ").strip()
    price = read_number("Price: ", float)
    stock = read_number("Stock Quantity: ", int)
 
    inventory.append({"id": product_id, "name": name,
                      "price": price, "stock": stock})
    record_transaction(transactions, product_id, stock, "add")
    print("Product added successfully!")
 
 
def update_stock(inventory, transactions):
    print("\nUpdate Stock")
    product = find_product(inventory, input("Enter Product ID: ").strip())
    if product is None:
        print("Product not found.")
        return
    print("Product Found:")
    print(f"Name: {product['name']}")
    print(f"Current Stock: {product['stock']}")
    new_stock = read_number("New Stock Quantity: ", int)
 
    change = new_stock - product["stock"]
    product["stock"] = new_stock
    record_transaction(transactions, product["id"], change, "update")
    print("Stock updated successfully!")
 
 
def search_product(inventory):
    print("\nSearch Product")
    product = find_product(inventory, input("Enter Product ID: ").strip())
    if product is None:
        print("Product not found.")
        return
    print("Product Found")
    print("-" * 48)
    print(f"ID: {product['id']}")
    print(f"Name: {product['name']}")
    print(f"Price: ${product['price']:.2f}")
    print(f"Stock: {product['stock']}")
    print("-" * 48)

# Menu
# ---------------------------------------------------------------
def show_menu():
    print("\n----------- MENU -----------")
    print("1. Display All Products")
    print("2. Add Product")
    print("3. Update Stock")
    print("4. Search Product")
    print("5. Save Inventory")
    print("6. Exit")
    print("-----------------------------")
 
 
def main():
    print("SIT Internal")
    print("=" * 40)
    print("INVENTORY MANAGEMENT SYSTEM")
    print("=" * 40)
    inventory, transactions = load_inventory()
 
    while True:
        show_menu()
        choice = input("Enter option: ").strip()
        if choice == "1":
            display_all(inventory)
        elif choice == "2":
            add_product(inventory, transactions)
        elif choice == "3":
            update_stock(inventory, transactions)
        elif choice == "4":
            search_product(inventory)
        elif choice == "5":
            print("Saving inventory...")
            save_inventory(inventory, transactions)
        elif choice == "6":
            print("Saving inventory before exit...")
            save_inventory(inventory, transactions)
            print("Thank you for using Inventory Management System.")
            print("Program terminated.")
            break
        else:
            print("Invalid option. Please choose 1-6.")
 
 
if __name__ == "__main__":
    main()




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