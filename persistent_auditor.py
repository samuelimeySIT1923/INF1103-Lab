import sys
import os

#Initialize the inventory to zero in the start
quit = False
status = False
current_total = 0
failed_attempts = 0
totaltax = 0
Overstock_Limit = 500

#4. Modularity: Maintain your functional design. Create a load_inventory() and save_inventory() function. 
def load_inventory():
    totalOrderList = []
    entry_count = 0
    final_total = 0
    #Persistence: At the start of the program, read the information previously saved in the inventory file.
    try:
        with open('inventory.txt', 'r') as file:
            for line in file:
                parts = line.strip().split(', ')
                if len(parts) == 3:
                    order_no, product_name, qty = parts
                    totalOrderList.append([int(order_no), product_name, int(qty)])
                    final_total += int(qty)
        # After the file is read, fill list and print out
        entry_count = totalOrderList[-1][0] if totalOrderList else 0
        if totalOrderList:
            print("Current Orders:")
            for order_no, product_name, qty in totalOrderList:
                print(f"{order_no}, {product_name}, {qty}")
            print(f"Overall stock input: {final_total}")
    #If the inventory file does not exist, start with an empty inventory and continue running without producing an error.
    except FileNotFoundError:
        pass
    return totalOrderList, entry_count, final_total



def save_inventory(totalOrderList,recent_Count,current_total):
    recentOrders = totalOrderList[recent_Count:]
    #totalOrderList.extend(current_total)
    with open('inventory.txt', 'w') as file:
        #Print each product [Order no, Product Name, Quantity]:
        for order_no, product_name, qty in totalOrderList:
            file.write(f"{order_no}, {product_name}, {qty}\n")
        file.write(f"Total: {current_total}\n")

    print("\nNew orders added:")
    if recentOrders:
        for order_no, product_name, qty in recentOrders:
            print(f"{order_no}, {product_name}, {qty}")
    else:
        print("None")      
    print("Order sucessfully saved to inventory.txt")
    return totalOrderList, current_total

#Handles the prompt, handles input validation, and returns a valid integer or a "quit" signal. 
def get_valid_input(entry_count):
    try:
        qty = input("Enter stock quantity (or type 'quit' to exit): ")
    except EOFError:
        print("\nNo more input available. Exiting gracefully.")
        return 'quit', entry_count, None
    
    if qty.lower() == 'quit':  
            return 'quit', entry_count, None
    if not (qty.lstrip('-').isdigit()):
            print("Error: pls enter a valid number or type 'quit' to exit.")
            return 'error', entry_count, None
    qty = int(qty)
    if qty < 0:
            print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
            return 'error', entry_count, None
    else:
        try:
            product_name = input("Enter product name: ")
        except EOFError:
            print("\nNo more input available. Exiting gracefully.")
            return 'quit', entry_count, None
        #Update any counters and records you are tracking, such as the number of deliveries processed. 
        entry_count += 1
        print(f"\n\033[1m Entry Count {entry_count}: \n Product Name: {product_name}\033[0m")
        return 'ok', entry_count, [entry_count, product_name, qty]

 #Calculates the new total and returns it.        
def process_delivery(current_total, qty):
    current_total += qty
    print("Stock Quantity entered:", qty)
    return current_total, qty

#Takes a delivery amount and returns the tax (10% of that specific delivery). 
def calculate_tax(qty):
    tax = qty * 0.10
    print("Tax for this delivery: S$", tax)
    return tax

#Print the final summary. 
def generate_report(current_total, totaltax, failed_attempts):
    print("\n\033[1m", "Report Summary:", "\033[0m")
    print("Total Units Processed:", current_total)
    print("Total Tax Paid: S$", totaltax)
    print("Number of Failed/Rejected Entries:", failed_attempts)
    #print("\nNew orders added:")
    #for order_no, product_name, qty in totalOrderList[recent_Count]:
    #    print(f"{order_no}, {product_name}, {qty}")

def overstock_alert(current_total):
    if current_total > Overstock_Limit:
        print("ALERT: Overstock! Total inventory input exceeds 500 units!")
        return True
    return False

totalOrderList, entry_count, final_total = load_inventory()
recent_Count = len(totalOrderList)
current_total = final_total
#Continuous loop asking user to enter a stock quantity, until the user types quit. 
while quit == False:
    status, entry_count, input_value = get_valid_input(entry_count)
    if status == 'quit':
        quit = True
        break
    if status == 'error':
        failed_attempts += 1
        print("Number of Failed/Rejected Entries:", failed_attempts)
        continue
    #Add the delivery amount to the running total. 
    totalOrderList.append(input_value)
    qty = input_value[2]
    current_total, qty = process_delivery(current_total, qty)
    #Calculate the tax for that delivery. 
    tax = calculate_tax(qty)
    #Update any counters and records you are tracking, such as the number of deliveries processed. 
    totaltax += tax
    quit = overstock_alert(current_total)

generate_report(current_total, totaltax, failed_attempts)

#3. Write-Back: When the user types quit, save the final total and the transaction history list to inventory.txt. 
save_inventory(totalOrderList, recent_Count, current_total)
