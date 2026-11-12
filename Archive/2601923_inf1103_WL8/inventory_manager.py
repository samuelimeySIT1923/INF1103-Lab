from itertools import product
import json
import os
from datetime import datetime
from abc import ABC, abstractmethod
 
FILENAME = "inventory.json"
SEPARATOR_WIDTH = 48 #X dashes printed for formatting


#Common function 1 - Used to check for matching products ID in Add Product, Update Stock and Search Product
def find_product(products: "list[Product]", product_id: str) -> "Product | None":
    for product in products: # Return the matching product dictionary, or None if there is no match.
        if product.product_id == product_id:
            return product
    return None # only after the whole list has been checked

#Common Function 2 -  Append one entry to the transaction history (never overwritten).
def record_transaction(transactions: "list", product_id: str, change: int, kind: str):
        transactions.append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "product_id": product_id,
            "type": kind,
            "change": change,
        })

#Common Function 3 - Read number input with validation
def read_number(prompt: str, cast: type, minimum: int = 0) -> int:
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
def create_product(data: dict) -> Product:
    kind = data.get("type", "physical")
    supplier_data = data.get("supplier", {})
    if supplier_data:
        supplier = Supplier.from_dict(supplier_data)
    else:
        supplier = Supplier("N/A", "Unknown Supplier", "N/A")

    if kind == "physical":
        return PhysicalProduct(data["id"], data["product_name"], data["price"],
                               data["stock"], data.get("weight", 0.0), supplier)
    if kind == "digital":
        return DigitalProduct(data["id"], data["product_name"], data["price"],
                              data["stock"], data["download_size"], supplier)
    if kind == "subscription":
        return SubscriptionProduct(data["id"], data["product_name"], data["price"],
                                   data["stock"], data["months_left"], supplier)
    raise ValueError(f"Unknown product type: {kind}")

#Create the FileHandling Class - Load & Save Inventory .json file
class FileHandling:
    def __init__(self, filename=FILENAME):
        self.__filename = filename

    #Find json file and load it if it exists, otherwise start with an empty inventory.
    def load_inventory(self) -> tuple["list[Product]", "list"]:
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
    def save_inventory(self, products: "list[Product]", transactions: "list"):
        try:
            with open(self.__filename, "w") as f:
                json.dump({"products": [p.to_dict() for p in products], "transactions": transactions}, f, indent=4)
            print(f"Inventory saved successfully to {self.__filename}.")
        except OSError as e:
            print(f"Could not save to {self.__filename}: {e}")


#CanBeShipped Interface <Functional Class>
class CanBeShipped(ABC):
    @abstractmethod
    def calculate_shipping_cost(self, weight: float):
        pass

#2.1 Supplier Class
class Supplier:
    def __init__(self, supplier_id: str, supplier_name: str, contact_email: str):
        self.__supplier_id = supplier_id
        self.__supplier_name = supplier_name
        self.__contact_email = contact_email

    #Read-only access as private data to read supplier information
    @property
    def supplier_id(self):
        return self.__supplier_id
    @property
    def supplier_name(self):
        return self.__supplier_name
    @property
    def contact_email(self):
        return self.__contact_email

    def to_dict(self) -> dict:
        return {"supplier_id": self.__supplier_id, "supplier_name": self.__supplier_name,
                "contact_email": self.__contact_email}
 
    #Python dictionary back to Supplier object - used when loading Inventory.json
    @classmethod
    def from_dict(cls, data: dict) -> "Supplier":
        return cls(data["supplier_id"], data["supplier_name"], data["contact_email"])

#2.2 Associate Supplier with Product
#Product Class - Handle Single Product Only
class Product(ABC):
    def __init__(self, product_id: str, product_name: str, price: float, stock_quantity: int, supplier: Supplier):
        self.__supplier: Supplier = supplier
        self.__product_id = product_id
        self.__product_name = product_name
        self.__price = price
        self.__stock_quantity = stock_quantity

    #Read-only access so child classes (and Inventory) can use the private data
    @property
    def product_id(self):
        return self.__product_id
    @property
    def product_name(self):
        return self.__product_name
    @property
    def price(self):
        return self.__price
    @property #get current stock value
    def stock(self):
        return self.__stock_quantity
    @stock.setter
    def stock(self, value):
        self.__stock_quantity = value

    @property
    def products(self) -> list[Product]:
        return list(self.__products)   # a copy, so outside code can't edit your list

    #6.3 A contract that no matter what type of product, it must implement a method to return fulfilment information.
    # The subclasses preserve it by having the same signautre, return type and meaning. This allows the Inventory to 
    # call get_fulfilment_info() on any product type without knowing the details of that type.
    @abstractmethod
    def get_fulfilment_info(self):
        pass

    #7.3 get_fulfilment_info() demonstrates polymorphism as the child methods respond to the same method call in their
    # own way, based on their own data. This allows the Inventory to call get_fulfilment_info() on any product type 
    # without knowing the details of that type. 
    # LSP supports this by esnuring that the subclasses preserve the same signature, return type and meaning of the method.
    #This guarantees that every implementation is safe to call, and that the Inventory can rely on the method to behave 
    # consistently across all product types.

    def get_details(self): #Regular Method - Children can extend from this method
        return (f"ID: {self.__product_id} | Product Name: {self.__product_name} |"
                f"Price: ${self.__price:.2f} | Stock: {self.__stock_quantity}|"
                f"Supplier ID: {self.__supplier.supplier_id} | Supplier Name: {self.__supplier.supplier_name} |"
                f"Supplier Contact Email: {self.__supplier.contact_email}")

    #written promise for what update_stock should mean for every product type.
    def update_stock(self, quantity: int) -> None:
        """Set stock to `quantity`. Raises ValueError if quantity < 0."""
        if quantity < 0:
            raise ValueError("Stock cannot be negative.")
        self.__stock_quantity = quantity

    def display_information(self):
        print(self.get_details())

    def to_dict(self):
        return {"id": self.__product_id, "product_name": self.__product_name,
                "price": self.__price, "stock":self.__stock_quantity, "supplier": self.__supplier.to_dict()}


#Create a PhysicalProduct class (Parent, interface)
class PhysicalProduct (Product, CanBeShipped):
    BASE_SHIPPING_COST = 5.00  # Base shipping cost in dollars
    COST_PER_KG = 2.00  # Cost per kilogram in dollars

    def __init__(self, product_id: str, product_name: str, price: float, stock_quantity: int, weight: float, supplier: Supplier):
        super().__init__(product_id, product_name, price, stock_quantity, supplier)  # Reuse Product constructor
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

#Implement the required method [PhysicalProduct] to return fulfilment information (ie name + shipping cost).
    def get_fulfilment_info(self):
        return f"Product {self.product_name} will be require physical shipping. \nEstimated shipping cost: ${self.calculate_shipping_cost(self.weight):.2f}"
    
    def calculate_shipping_cost(self, weight):
        return self.BASE_SHIPPING_COST + (self.COST_PER_KG * weight)


#Create a DigitalProduct class
class DigitalProduct(Product):
    def __init__(self, product_id: str, product_name: str, price: float, stock_quantity: int, download_size: float, supplier: Supplier):
        super().__init__(product_id, product_name, price, stock_quantity, supplier)
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

#Implement the required method [DigitalProduct] to return fulfilment information (ie name + download size).
    def get_fulfilment_info(self):
        return f"Product {self.product_name} will be delivered to you digitally. Download size: {self.download_size} MB"

#Create a SubscriptionProduct class
class SubscriptionProduct(Product):
    def __init__(self, product_id: str, product_name: str, price: float, stock_quantity: int, months_left: int, supplier: Supplier):
        super().__init__(product_id, product_name, price, stock_quantity, supplier)
        if months_left < 0:  # Validate months left in subscription
            raise ValueError("Month(s) left should not be negative. Else, product has expired.")
        self.__validity_period = months_left

    @property
    def validity_period(self):
        return self.__validity_period

    def get_details(self):
        return f"{super().get_details()} | Type: Subscription | Month(s) Left: {self.validity_period}"

    def to_dict(self):
        data = super().to_dict()
        data["type"] = "subscription"
        data["months_left"] = self.validity_period
        return data

#Implement the required method [SubscriptionProduct] to return fulfilment information (ie name + months left).
    def get_fulfilment_info(self):
        return f"Product {self.product_name} is a subscription. {self.validity_period} month(s) left before expiry."

#Reflection:
# It was easy to add the new product type in based on the layout of the previous items. However, modifications are required for it
# to be selectable as a product type and display accordingly.

# To modify, there is a need to add "3. Subscription Product" and update "create_product" to accept the new product type. 
# This can be combersome if there is a need to modify multiple areas of the code for each new product type.

# 1 proposition for the design to be enhanced will be to create a list of available product types where each product type is a dictionary
# containing the name and the class reference. This will allow for the menu to be generated dynamically and "create_product" can 
# automatically update itself to dynamically handle the creation of each type.


#Inventory Class - Amendable: Add Product + Update Stock
class Inventory:
    def __init__(self, products: list[Product] | None = None,transactions: list[dict] | None = None) -> None:
        self.__products: list[Product] = products if products is not None else [] #return empty if no products
        #products is in list[Product] given it is the overall parent  class of all product types. 
        #This allows for the inventory to be able to store any type of product [ie PhysicalProduct, DigitalProduct, SubscriptionProduct].
        self.__transactions: list[dict] = transactions if transactions is not None else [] # list of transaction 

    #iter -  allow instances of class to be used directly inside loops & lists
    def __iter__(self):
        return iter(self.__products) # Returns an iterator for the products list

    def find_product(self, product_id: str) -> Product | None:
        return find_product(self.__products, product_id)

    #Display all Products [1]
    def display_all(self) -> None:
        print("\nCurrent Inventory")
        print("-" * SEPARATOR_WIDTH) 
        if not self.__products: #nothing in inventory
            print("No products in inventory.")
    # Represent inventory items using dictionaries and store at least three products in a list. 
        for product in self.__products: #loop for each product in inventory and print details
            product.display_information()
        print("-" * SEPARATOR_WIDTH) 

    #Update Stock [3]
    def update_stock(self):
        print("\nUpdate Stock")
        product = self.find_product(input("Enter Product ID: ").strip())
        if product is None:
            print("Product not found.")
            return
        print("Product Found:")
        print(f"Name: {product.product_name}")
        print(f"Current Stock: {product.stock}")
        new_stock = read_number("New Stock Quantity: ", int)
        change = new_stock - product.stock
        product.update_stock(new_stock)
        record_transaction(self.__transactions, product.product_id, change, "update")
        print("Stock updated successfully!")

    #3.2 Add Existing Product to inventory [4]
    def add_product(self, product: Product) -> None:
        if self.find_product(product.product_id) is not None:
            raise ValueError(f"Product ID {product.product_id} already exists in the inventory.")
        self.__products.append(product)
        record_transaction(self.__transactions, product.product_id, product.stock, "add to inv")

    #3.2 Remove Product from Inventory [5]
    def remove_product(self, product_id: str) -> bool:
        product = self.find_product(product_id)
        if product is None:
            return False
        self.__products.remove(product)
        record_transaction(self.__transactions, product.product_id, -product.stock, "remove from inv")
        return True
        
  #Search for a Product [6] <Find Within whole list>
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

#4.1 OrderLine Class - Represents a single line in an order, containing a product and its quantity.
class OrderLine:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

    def calculate_subtotal(self) -> float:
        return self.product.price * self.quantity

#4.2 Order Class - Represents an order containing multiple order lines.
class Order:
    def __init__(self, order_id: str):
        self.order_id: str = order_id
        self.order_lines: list[OrderLine] = []

    def add_order_line(self, product: Product, quantity: int) -> None:
        order_line = OrderLine(product, quantity)
        self.order_lines.append(order_line)

    def calculate_total(self) -> float:
        return sum(line.calculate_subtotal() for line in self.order_lines)


#Create the MainProgram Class - Main menu & startup
class MainProgram:
    def __init__(self):
        self.file_handler = FileHandling()
        products, self.transactions = self.file_handler.load_inventory()
        self.inventory = Inventory(products, self.transactions)
        self.created_products: list[Product] = []

    #Menu System - Create menu options for Display, Add, Update, Search, Save and Exit.
    def show_menu(self):
        print("\n----------- MENU -----------")
        print("1. Display All Products")
        print("2. Create Product")
        print("3. Update Stock")
        print("4. Add Product to Inventory")
        print("5. Remove Product from Inventory")
        print("6. Search Product")
        print("7. Save Inventory")
        print("8. Exit")
        print("-----------------------------")

    #Common Function 1: Save Inventory
    def save(self):
        self.file_handler.save_inventory(self.inventory, self.transactions)

    #Common function 2: Option 2 helper - ask the user for details and BUILD a product. Returns it; does not add it to any inventory.
    def prompt_for_product(self) -> Product | None:
        print("\nCreate New Product")
        product_id = input("Product ID: ").strip() #remove white spaces from input
        if not product_id: #ERROR handling: no blank id
            print("Product ID cannot be empty.")
            return None
        if self.inventory.find_product(product_id) or find_product(self.created_products, product_id): #ERROR handling: no same id
            print("Product ID already exists.")
            return None
        product_name = input("Product Name: ").strip() #remove white spaces from input
        price = read_number("Price: ", float) #price in float, accept decimal (Cents)
        stock_quantity = read_number("Stock Quantity: ", int) #stock in int, whole number only
        supplier = Supplier(
            input("Supplier ID: ").strip(),
            input("Supplier Name: ").strip(),
            input("Supplier Contact Email: ").strip()
        )
        print("Select Product Type:\n1. Physical Product\n2. Digital Product\n3. Subscription Product")
        while True:
            product_type = input("Choose Product Type (1, 2 or 3): ").strip()
            if product_type == "1":
                weight = read_number("Weight (kg): ", float)
                return PhysicalProduct(product_id, product_name, price, stock_quantity, weight, supplier)
            elif product_type == "2":
                download_size = read_number("Download Size (MB): ", float)
                return DigitalProduct(product_id, product_name, price, stock_quantity, download_size, supplier)
            elif product_type == "3":
                months_left = read_number("Months Left: ", int)
                return SubscriptionProduct(product_id, product_name, price, stock_quantity, months_left, supplier)
            else:
                print("Invalid option. Please choose 1, 2 or 3.")                

    #Common function 3: Option 4 helper - pick an EXISTING product (created earlier, not currently in the inventory) and add it
    def add_existing_product(self) -> None:
        print("\nAdd Existing Product to Inventory")
        available = [p for p in self.created_products if self.inventory.find_product(p.product_id) is None]
        if not available:
            print("No created products available. Create one in option 2 first.")
            return
        for p in available:
            print(f"{p.product_id} - {p.product_name}")
        product = find_product(available, input("Enter Product ID to add: ").strip())
        if product is None:
            print("Product not found.")
            return
        try:
            self.inventory.add_product(product) # passes the existing object, not a copy
            print("Product added to inventory successfully!")
        except ValueError as e:
            print(e)

    #Common function 4: Option 5 helper - remove a product from the inventory, but keep it usable (e.g. to re-add later)
    def remove_product_interface(self):
        print("\nRemove Product from Inventory")
        product_id = input("Enter Product ID to remove: ").strip()
        product = self.inventory.find_product(product_id)
        if product is None:
            print("Product not found.")
            return
        self.inventory.remove_product(product_id)
        if product not in self.created_products:
            self.created_products.append(product)
        print("Product removed from inventory.")

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
                product = self.prompt_for_product()
                if product is not None:
                    self.created_products.append(product)
                    print("Product created. Use option 4 to add it to the inventory.")
            elif choice == "3":
                self.inventory.update_stock()
            elif choice == "4":
                self.add_existing_product()
            elif choice == "5":
                self.remove_product_interface()
            elif choice == "6":
                self.inventory.search_product()
            elif choice == "7":
                print("Saving inventory...")
                self.save()
            elif choice == "8":
                print("Saving inventory before exit...")
                self.save()
                print("Thank you for using Inventory Management System.")
                print("Program terminated.")
                break         
            else:
                #ERROR handling: invalid input beyond 1-8
                print("Invalid option. Please choose 1-8.")


  #Guard to ensure program launches directly when run as a script, not when imported as a module. External Code
if __name__ == "__main__":
    MainProgram().main()