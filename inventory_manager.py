import json
import os
from datetime import datetime
 
FILENAME = "inventory.json"

#Common Class - Used to check for matching products ID in Add Product, Update Stock and Search Product
class FindProduct:
    def __init__(self)

    def find_product(inventory, product_id):
        #Return the product dictionary with the given ID, or None.
        for product in inventory:
            if product.matches_id(product_id):
                return product
        return None


#2.3 Create the Product Class - Read Only: Show Overall List of Products + Search Product
class Product:
    def __init__(self, product_id, name, price, stock):
        self.__product_id = product_id 
        self.__name = name
        self.__price = price
        self.__stock = stock

    #Read only 
    def get_id(self):
        return self.__product_id
    def get_name(self):
        return self.__name
    def get_price(self):
        return self.__price
    def get_stock(self):
        return self.__stock

    # 3 Core functions - inventory: 
# #<2> Data Manipulation:  Maintain your functional design. ,
#3a Display all products in inventory
#<2iv> display_all()
def display_all(inventory):
    print("\nCurrent Inventory")
    print("-" * 48) #48 dashes printed for formatting
    if not inventory: #nothing in inventory
        print("No products in inventory.")
# <1> Represent inventory items using dictionaries and store at least three products in a list. 
    for p in inventory: #loop for each product in inventory and print details
        print(f"ID: {p['id']} | Name: {p['name']} | "
              f"Price: ${p['price']:.2f} | Stock: {p['stock']}")
    print("-" * 48) #48 dashes printed for formatting

  #3d Add a new product <2iii> search_product()
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


#2.8 Create the Inventory Class - Amendable: Add Product + Update Stock
class inventory:
    def __init__():


    def update_stock(product_id,quantity):
        if self.__product_id = product_id:
            Product.__stock = quantity


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
 
     #3b Add a new product <2i> add_product()
def add_product(inventory, transactions):
    print("\nAdd New Product")
    product_id = input("Product ID: ").strip() #remove white spaces from input
    if not product_id: #ERROR handling: no blank id
        print("Product ID cannot be empty.")
        return
    if find_product(inventory, product_id): #ERROR handling: no same id
        print("Product ID already exists.")
        return
    name = input("Product Name: ").strip() #remove white spaces from input
    price = read_number("Price: ", float) #price in float, accept decimal (Cents)
    stock = read_number("Stock Quantity: ", int) #stock in int, whole number only
 #add on in list
    inventory.append({"id": product_id, "name": name,
                      "price": price, "stock": stock})
    record_transaction(transactions, product_id, stock, "add")
    print("Product added successfully!")

      #3c Add a new product <2ii>  update_stock()
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


#2.8 Create the Inventory Class - Amendable: Add Product + Update Stock
class FileHandling:
    def __init__():

#1a find json file and load it if it exists, otherwise start with an empty inventory.
    def load_inventory():
    #Load data from inventory.json if it exists, otherwise start empty.
    #<3i> Check whether inventory.json exists. Create load_inventory() to load inventory.json if it exists.
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
    # <3ii> Otherwise, begin with an empty inventory.
        return [], []


    #1b Save the inventory and transaction history to inventory.json
    #<3iii> Create save_inventory() and save data to inventory.json.
    def save_inventory(inventory, transactions):
    #Save products and the full transaction history to inventory.json.
    #writes file, will override
        with open(FILENAME, "w") as f:
            json.dump({"products": inventory, "transactions": transactions}, f, indent=4)
        print(f"Inventory saved successfully to {FILENAME}.")


#Common Class - Used to check for matching products ID in Add Product, Update Stock and Search Product
class MainProgram:
    def __init__(self)

    #4 Menu System <4> Build a Menu System:  Create menu options for Display, Add, Update, Search, Save and Exit.
#4a Show menu options
def show_menu():
    print("\n----------- MENU -----------")
    print("1. Display All Products")
    print("2. Add Product")
    print("3. Update Stock")
    print("4. Search Product")
    print("5. Save Inventory")
    print("6. Exit")
    print("-----------------------------")
 
 #4b Main startup screen
def main():
    print("=" * 40) #40 equal sign
    print("INVENTORY MANAGEMENT SYSTEM")
    print("=" * 40) #40 equal sign
    inventory, transactions = load_inventory()
 #accept input 1-6
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
            #ERROR handling: invalid input beyond 1-6
            print("Invalid option. Please choose 1-6.")

 
 #Guard to ensure program launches directly when run as a script, not when imported as a module. External Code
if __name__ == "__main__":
    main()