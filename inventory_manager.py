import json
import os
from datetime import datetime
 
FILENAME = "inventory.json"
 
 
# Persistence
def load_inventory():
    """Load data from inventory.json if it exists, otherwise start empty."""
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, "r") as f:
                data = json.load(f)
            print(f"{FILENAME} found. Inventory loaded successfully.")
            return data["products"], data.get("transactions", [])
        except (json.JSONDecodeError, KeyError):
            print(f"{FILENAME} is corrupted. Starting with empty inventory.")
    else:
        print(f"{FILENAME} not found. Starting with empty inventory.")
    return [], []
 
 
def save_inventory(inventory, transactions):
    """Save products and the full transaction history to inventory.json."""
    with open(FILENAME, "w") as f:
        json.dump({"products": inventory, "transactions": transactions}, f, indent=4)
    print(f"Inventory saved successfully to {FILENAME}.")
 
 
# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def record_transaction(transactions, product_id, change, kind):
    """Append one entry to the transaction history (never overwritten)."""
    transactions.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_id": product_id,
        "type": kind,
        "change": change,
    })
 
 
def find_product(inventory, product_id):
    """Return the product dictionary with the given ID, or None."""
    for product in inventory:
        if product["id"].lower() == product_id.lower():
            return product
    return None
 
 
def read_number(prompt, cast, minimum=0):
    """Keep asking until the user enters a valid number >= minimum."""
    while True:
        try:
            value = cast(input(prompt))
            if value < minimum:
                print(f"Value must be at least {minimum}.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a number.")
 
 
# ---------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------
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