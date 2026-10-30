import json
import os
from datetime import datetime
 
FILENAME = "inventory.json"
SEPARATOR_WIDTH = 48 #X dashes printed for formatting


#Common function 1 - Used to check for matching products ID in Add Product, Update Stock and Search Product
def find_product(products, product_id):
    for product in products: # Return the matching product dictionary, or None if there is no match.
        if product["id"] == product_id:
            return product
    return None # only after the whole list has been checked

#Common Function 2 -  Append one entry to the transaction history (never overwritten).
def record_transaction(transactions, product_id, change, kind):
        transactions.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "product_id": product_id,
            "type": kind,
            "change": change,
        })

#Common Function 3 - Read number input with validation
def read_number(prompt, cast, minimum=0):
    #Keep asking until the user enters a valid number >= minimum.
    while True:
        try:
            value = cast(input(prompt))
            if value < minimum: #less than 0 = reject
                print(f"Value must be at least {minimum}.")
                continue
            return value
        except ValueError:        #not number = reject
            print("Invalid input. Please enter a number.")


#2.8.1 Create the FileHandling Class - Load & Save Inventory .json file
class FileHandling:
    def __init__(self, filename=FILENAME):
        self.__filename = filename

    #Find json file and load it if it exists, otherwise start with an empty inventory.
    def load_inventory(self):
    #Load data from inventory.json if it exists, otherwise create new inventory.json and start empty.
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

    #2.3.1 Update Stock [3]
    def update_stock(products, transactions):
        print("\nUpdate Stock")
        product = find_product(products, input("Enter Product ID: ").strip())
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


#2.6 Create the Inventory Class - Amendable: Add Product + Update Stock
class Inventory:
    def __init__(self, products, transactions):
        self.__products = products if products is not None else [] #return empty if no products
        self.__transactions = transactions if transactions is not None else [] # list of transaction 

    #iter -  allow instances of class to be used directly inside loops & lists
    def __iter__(self):
        return iter(self.__products) # Returns an iterator for the products list

    #append - Allow add on to existing data
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

    #2.6.2 Add Product [2] <Need to add on to whole existing list>
    def add_product(self):
        print("\nAdd New Product")
        product_id = input("Product ID: ").strip() #remove white spaces from input
        if not product_id: #ERROR handling: no blank id
            print("Product ID cannot be empty.")
            return
        if find_product(self, product_id): #ERROR handling: no same id
            print("Product ID already exists.")
            return
        name = input("Product Name: ").strip() #remove white spaces from input
        price = read_number("Price: ", float) #price in float, accept decimal (Cents)
        stock = read_number("Stock Quantity: ", int) #stock in int, whole number only
        self.append({"id": product_id, "name": name,
                      "price": price, "stock": stock})     #add on in list
        record_transaction(self.__transactions, product_id, stock, "add")
        print("Product added successfully!")

  ##2.6.3 Search for a Product [4] <Find Within whole list>
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

#2.8.2 Create the MainProgram Class - Main menu & startup
class MainProgram:
    def __init__(self):
        self.file_handler = FileHandling()
        products, self.transactions = self.file_handler.load_inventory()
        self.inventory = Inventory(products, self.transactions)

    #2.8.2.1 Menu System - Create menu options for Display, Add, Update, Search, Save and Exit.
    def show_menu(self):
        print("\n----------- MENU -----------")
        print("1. Display All Products")
        print("2. Add Product")
        print("3. Update Stock")
        print("4. Search Product")
        print("5. Save Inventory")
        print("6. Exit")
        print("-----------------------------")

    #2.8.2.2 Common Function within = Save Inventory
    def save(self):
        self.file_handler.save_inventory(self.inventory, self.transactions)

    #2.8.2.3 Main startup screen [Screen Input for 1-6]
    def main(self):
        print("=" * SEPARATOR_WIDTH)
        print("INVENTORY MANAGEMENT SYSTEM")
        print("=" * SEPARATOR_WIDTH)
        #accept input 1-6
        while True:
            self.show_menu()
            choice = input("Enter option: ").strip()
            if choice == "1":
                self.inventory.display_all()
            elif choice == "2":
                self.inventory.add_product()
            elif choice == "3":
                Product.update_stock(self.inventory, self.transactions)
            elif choice == "4":
                self.inventory.search_product()
            elif choice == "5":
                print("Saving inventory...")
                self.save()
            elif choice == "6":
                print("Saving inventory before exit...")
                self.save()
                print("Thank you for using Inventory Management System.")
                print("Program terminated.")
                break
            else:
                #ERROR handling: invalid input beyond 1-6
                print("Invalid option. Please choose 1-6.")


  #Guard to ensure program launches directly when run as a script, not when imported as a module. External Code
if __name__ == "__main__":
    MainProgram().main()