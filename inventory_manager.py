import json
import os
from datetime import datetime
from abc import ABC, abstractmethod
 
FILENAME = "inventory.json"
SEPARATOR_WIDTH = 48 #X dashes printed for formatting


#Common function 1 - Used to check for matching products ID in Add Product, Update Stock and Search Product
def find_product(products, product_id):
    for product in products: # Return the matching product dictionary, or None if there is no match.
        if product.product_id == product_id:
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

#Common Function 4 - Build the correct Product object from a saved dictionary (used when loading inventory.json)
def create_product(data):
    kind = data.get("type", "physical")
    if kind == "physical":
        return PhysicalProduct(data["id"], data["name"], data["price"],
                               data["stock"], data.get("weight", 0.0))
    if kind == "digital":
        return DigitalProduct(data["id"], data["name"], data["price"],
                              data["stock"], data["download_size"])
    raise ValueError(f"Unknown product type: {kind}")


#Create the FileHandling Class - Load & Save Inventory .json file
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
                products = [create_product(item) for item in data["products"]]
                print(f"{self.__filename} found. Inventory loaded successfully.")
                return products, data.get("transactions", []) #call data with products, transactions
            except (json.JSONDecodeError, KeyError, TypeError, ValueError, AttributeError): #ERROR HANDLING: fallback if cannot use file
                print(f"{self.__filename} is corrupted. Starting with empty inventory.")
        else:
            print(f"{self.__filename} not found. Starting with empty inventory.")
        return [], [] #empty inventory and transaction history Fallback

    #Save the products and full transaction history to inventory.json. Will override
    def save_inventory(self, products, transactions):
        try:
            with open(self.__filename, "w") as f:
                json.dump({"products": [p.to_dict() for p in products], "transactions": transactions}, f, indent=4)
            print(f"Inventory saved successfully to {self.__filename}.")
        except OSError as e:
            print(f"Could not save to {self.__filename}: {e}")


#4.1 CanBeShipped Interface <Functional Class>
class CanBeShipped(ABC):
    @abstractmethod
    def calculate_shipping_cost(self, weight):
        pass


#Product Class - Handle Single Product Only
class Product(ABC):
    def __init__(self, product_id, name, price, stock):
        self.__product_id = product_id
        self.__name = name
        self.__price = price
        self.__stock = stock

    #Read-only access so child classes (and Inventory) can use the private data
    @property
    def product_id(self):
        return self.__product_id
    @property
    def name(self):
        return self.__name
    @property
    def price(self):
        return self.__price
    @property #get current stock value
    def stock(self):
        return self.__stock
    @stock.setter
    def stock(self, value):
        self.__stock = value

    #3.1 Convert Product into an abstract class
    @abstractmethod
    def get_fulfilment_info(self):
        pass

    def get_details(self): #Regular Method - Children can extend from this method
        return (f"ID: {self.__product_id} | Name: {self.__name} | "
                f"Price: ${self.__price:.2f} | Stock: {self.__stock}")

    def display_information(self):
        print(self.get_details())

    def to_dict(self):
        return {"id": self.__product_id, "name": self.__name,
                "price": self.__price, "stock": self.__stock}


#1.2 Create a PhysicalProduct class (Parent, interface)
class PhysicalProduct (Product, CanBeShipped):
    BASE_SHIPPING_COST = 5.00  # Base shipping cost in dollars
    COST_PER_KG = 2.00  # Cost per kilogram in dollars

    def __init__(self, product_id, name, price, stock, weight):
        super().__init__(product_id, name, price, stock)  # Reuse Product constructor
        if weight < 0:  # Validate weight
            raise ValueError("Weight cannot be negative.")
        self.__weight = weight  # Initialize weight attribute

    @property
    def weight(self):
        return self.__weight

    def get_details(self):
        return f"{super().get_details()} | Type: Physical | Weight: {self.weight} kg"

#Physical product object to Python dictionary - to be saved to Inventory.json
    def to_dict(self):
        data = super().to_dict()
        data["type"] = "physical"
        data["weight"] = self.weight
        return data

#3.2.1 Implement the required method [PhysicalProduct]
    def get_fulfilment_info(self):
        return f"Product {self.name} will be require physical shipping. \nEstimated shipping cost: ${self.calculate_shipping_cost(self.weight):.2f}"
    
    def calculate_shipping_cost(self, weight):
        return self.BASE_SHIPPING_COST + (self.COST_PER_KG * weight)


#1.3 Create a DigitalProduct class
class DigitalProduct(Product):
    def __init__(self, product_id, name, price, stock, download_size):
        super().__init__(product_id, name, price, stock)
        if download_size < 0:  # Validate download size
            raise ValueError("Download size cannot be negative.")
        self.__download_size = download_size

    @property
    def download_size(self):
        return self.__download_size

    def get_details(self):
        return f"{super().get_details()} | Type: Digital | Download Size: {self.download_size} MB"

#Digital product object to Python dictionary - to be saved to Inventory.json
    def to_dict(self):
        data = super().to_dict()
        data["type"] = "digital"
        data["download_size"] = self.download_size
        return data

#3.2.2 Implement the required method [DigitalProduct]
    def get_fulfilment_info(self):
        return f"Product {self.name} will be delivered to you digitally. Download size: {self.download_size} MB"


#Inventory Class - Amendable: Add Product + Update Stock
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

    #Display all Products [1]
    def display_all(self):
        print("\nCurrent Inventory")
        print("-" * SEPARATOR_WIDTH) 
        if not self.__products: #nothing in inventory
            print("No products in inventory.")
    # Represent inventory items using dictionaries and store at least three products in a list. 
        for product in self.__products: #loop for each product in inventory and print details
            product.display_information()
        print("-" * SEPARATOR_WIDTH) 

    #Add Product [2] <Need to add on to whole existing list>
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
        print (f"Select Product Type:\n1. Physical Product\n2. Digital Product")
        while True:
            product_type = input("Choose Product Type (1 or 2): ").strip()
            if product_type == "1":
                weight = read_number("Weight (kg): ", float)
                product = PhysicalProduct(product_id, name, price, stock, weight)
                break
            elif product_type == "2":
                download_size = read_number("Download Size (MB): ", float)
                product = DigitalProduct(product_id, name, price, stock, download_size)
                break
            else:
                print("Invalid option. Please choose 1 or 2.")
        self.__products.append(product)
        record_transaction(self.__transactions, product_id, stock, "add")
        print("Product added successfully!")

    #Update Stock [3]
    def update_stock(self):
        print("\nUpdate Stock")
        product = find_product(self, input("Enter Product ID: ").strip())
        if product is None:
            print("Product not found.")
            return
        print("Product Found:")
        print(f"Name: {product.name}")
        print(f"Current Stock: {product.stock}")
        new_stock = read_number("New Stock Quantity: ", int)
        change = new_stock - product.stock
        product.stock = new_stock
        record_transaction(self.__transactions, product.product_id, change, "update")
        print("Stock updated successfully!")

  #Search for a Product [4] <Find Within whole list>
    def search_product(self):
        print("\nSearch Product")
        product = find_product(self, input("Enter Product ID: ").strip())
        if product is None:
            print("Product not found.")
            return
        print("Product Found")
        print("-" * SEPARATOR_WIDTH)
        product.display_information()
        print(product.get_fulfilment_info())
        print("-" * SEPARATOR_WIDTH)

#Create the MainProgram Class - Main menu & startup
class MainProgram:
    def __init__(self):
        self.file_handler = FileHandling()
        products, self.transactions = self.file_handler.load_inventory()
        self.inventory = Inventory(products, self.transactions)

    #Menu System - Create menu options for Display, Add, Update, Search, Save and Exit.
    def show_menu(self):
        print("\n----------- MENU -----------")
        print("1. Display All Products")
        print("2. Add Product")
        print("3. Update Stock")
        print("4. Search Product")
        print("5. Save Inventory")
        print("6. Exit")
        print("-----------------------------")

    #Common Function within = Save Inventory
    def save(self):
        self.file_handler.save_inventory(self.inventory, self.transactions)

    #Main startup screen [Screen Input for 1-6]
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
                self.inventory.update_stock()
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