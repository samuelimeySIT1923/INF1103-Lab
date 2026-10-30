import json
import os
from datetime import datetime
 
FILENAME = "inventory.json"
SEPARATOR_WIDTH = 48 #X dashes printed for formatting


#Common function - Used to check for matching products ID in Add Product, Update Stock and Search Product
def find_product(products, product_id):
    for product in products: # Return the matching product dictionary, or None if there is no match.
        if product["id"] == product_id:
            return Product
        return None # only after the whole list has been checked


#2.8.1 Create the FileHandling Class - Load & Save Inventory .json file
class FileHandling:
    def __init__(self, filename=FILENAME):
        self.__filename = filename

    #Find json file and load it if it exists, otherwise start with an empty inventory.
    def load_inventory(self):
    #Load data from inventory.json if it exists, otherwise start empty.
    #<3i> Check whether inventory.json exists. Create load_inventory() to load inventory.json if it exists.
        if os.path.exists(self.__filename):
            try: #try to load file, will not crash if unable to
                with open(self.__filename, "r") as f:
                    data = json.load(f)
                print(f"{self.__filename} found. Inventory loaded successfully.")
                return data["products"], data.get("transactions", []) #call data with products, transactions
            except (json.JSONDecodeError, KeyError, TypeError): #ERROR HANDLING: fallback if cannot use file
                print(f"{self.__filename} is corrupted. Starting with empty inventory.")
        else:
            print(f"{self.__filename} not found. Starting with empty inventory.")
        return [], [] #empty inventory and transaction history Fallback

    #Save the products and full transaction history to inventory.json. Will override
    def save_inventory(self, products, transactions):
        try:
            with open(self.__filename, "w") as f:
                json.dump({"products": list(products), "transactions": transactions}, f, indent=4)
            print(f"Inventory saved successfully to {self.__filename}.")
        except OSError as e:
            print(f"Could not save to {self.__filename}: {e}")


#2.3 Create the Product Class - Handle Single Product Only
class Product:
    def __init__(self, product_id, name, price, stock): # Each product is a dictionary with id, name, price, and stock
        self.__product_id, self.__name, self.__price, self.__stock = product_id, name, price, stock

    #2.3.1 Add Product [2]
    def update_stock(self):
        print("\nUpdate Stock")
        product = find_product(self, input("Enter Product ID: ").strip())
        if product is None:
            print("Product not found.")
            return
        print("Product Found:")
        print(f"Name: {product['self.__name']}")
        print(f"Current Stock: {product['self.__stock']}")
        new_stock = self.read_number("New Stock Quantity: ", int)
        change = new_stock - product["self.__stock"]
        product["self.__stock"] = new_stock
        self.record_transaction(product["id"], change, "update")
        print("Stock updated successfully!")


#2.6 Create the Inventory Class - Amendable: Add Product + Update Stock
class Inventory:
    def __init__(self, products, transactions):
        self.__products = products if products is not None else [] #return empty if no products
        self.__transactions = transactions if transactions is not None else [] # list of transaction 

    #iter -  allow instances of class to be used directly inside loops & lists
    def __iter__(self):
        # Returns an iterator for the products list
        return iter(self.__products)

    #append - 
    def append(self, product):
        self.__products.append(product)

    #2.6.1 Display all Products [1]
    def display_all(self):
        print("\nCurrent Inventory")
        print("-" * SEPARATOR_WIDTH) 
        if not self.__products: #nothing in inventory
            print("No products in inventory.")
    # Represent inventory items using dictionaries and store at least three products in a list. 
        for p in self.__products: #loop for each product in inventory and print details
            print(f"ID: {p['id']} | Name: {p['name']} | "
                  f"Price: ${p['price']:.2f} | Stock: {p['stock']}")
        print("-" * SEPARATOR_WIDTH) 

    #2.8.1 Add Product [2] <Need to add on to whole existing list>
    def add_product(self):
        print("\nAdd New Product")
        self.__product_id = input("Product ID: ").strip() #remove white spaces from input
        if not self.__product_id: #ERROR handling: no blank id
            print("Product ID cannot be empty.")
            return
        if FindProduct(self, self.__product_id): #ERROR handling: no same id
            print("Product ID already exists.")
            return
        self.__name = input("Product Name: ").strip() #remove white spaces from input
        self.__price = self.read_number("Price: ", float) #price in float, accept decimal (Cents)
        self.__stock = self.read_number("Stock Quantity: ", int) #stock in int, whole number only
    #add on in list
        Product.append({"id": self.__product_id, "name": self.__name,
                      "price": self.__price, "stock": self.__stock})
        self.record_transaction(transactions, self.__product_id, self.__stock, "add")
        print("Product added successfully!")

  ##2.3.3 Search for a Product [4] <Find Within whole list>
    def search_product(self):
        print("\nSearch Product")
        product = find_product(self, input("Enter Product ID: ").strip())
        if product is None:
            print("Product not found.")
            return
        print("Product Found")
        print("-" * SEPARATOR_WIDTH)
        print(f"ID: {product['id']}")
        print(f"Name: {product['name']}")
        print(f"Price: ${product['price']:.2f}")
        print(f"Stock: {product['stock']}")
        print("-" * SEPARATOR_WIDTH)

    def record_transaction(self, change, kind):
    #Append one entry to the transaction history (never overwritten).
    #format Time, id, type, stock qty
    Inventory.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "product_id": self.__product_id,
        "type": kind,
        "change": change,
    })

#2c Read number input with validation
    def read_number(prompt, cast, minimum=0):
        #Keep asking until the user enters a valid number >= minimum.
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


#2.8.1 Create the MainProgram Class - Main menu & startup
class MainProgram:
    def __init__(self):

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
    print("=" * SEPARATOR_WIDTH)
    print("INVENTORY MANAGEMENT SYSTEM")
    print("=" * SEPARATOR_WIDTH) 
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