#Persistence: At the start of the program, read the information previously saved in the inventory file. If the inventory file does not exist, start with an empty inventory and continue running without producing an error. 
file = open('orders.txt','r')
#2. History Tracking: Use a Python list (array) to store every valid transaction 
#amount entered. 
#3. Write-Back: When the user types quit, save the final total and the transaction history list to inventory.txt. 
#4. Modularity: Maintain your functional design. Create a load_inventory() and save_inventory() function. 



#1. Initialize the inventory to zero in the start
quit = False
entrycount = 0
current_total = 0
failed_attempts = 0
totaltax = 0

#4a. get_valid_input(): Handles the prompt, handles input validation, and returns a valid integer or a "quit" signal. 
def get_valid_input():
    new_value = input("Enter stock quantity (or type 'quit' to exit): ")
    if new_value.lower() == 'quit':  
            return 'quit', False
    if not (new_value.lstrip('-').isdigit()):
            print("Error: pls enter a valid number or type 'quit' to exit.")
            return None, True
    new_value = int(new_value)
    if new_value < 0:
            print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
            return None, True
    else:
        return new_value, False

 #4b. process_delivery(current_total, new_value): Calculates the new total and returns it.        
def process_delivery(current_total, new_value):
    current_total += new_value
    print("Stock Quantity entered:", new_value)
    print("Overall Stock Quantity :", current_total)
    return current_total, new_value

#4c. calculate_tax(amount): A new requirement! This function takes a delivery amount and returns the tax (10% of that specific delivery). 
def calculate_tax(new_value):
    tax = new_value * 0.10
    print("Tax for this delivery: S$", tax)
    return tax

#4d. generate_report(current_total, entrycount, totaltax, failed_attempts): A dedicated function to print the final summary. 
def generate_report(current_total, entrycount,totaltax, failed_attempts):
    print("\n\033[1m", "Report Summary:", "\033[0m")
    print("Total Units Processed:", current_total)
    print("Total Deliveries Processed:", entrycount)
    print("Total Tax Paid: S$", totaltax)
    print("Number of Failed/Rejected Entries:", failed_attempts)

def overstock_alert(current_total):
    if current_total > 500:
        print("ALERT: Overstock! Total inventory exceeds 500 units!")
        return True
    return False

#2. un in a continuous loop asking user to enter a stock quantity, until the user types quit. 
while quit == False:
    new_value, has_error = get_valid_input()
    if new_value == 'quit':
        quit = True
        break
    if has_error:
        failed_attempts += 1
        print("Number of Failed/Rejected Entries:", failed_attempts)
        continue
    #3. If the user enters a valid value:  
    #3c. Update any counters and records you are tracking, such as the number of deliveries processed. 
    entrycount += 1
    print("\n\033[1m", "Entry Count:", entrycount, "\033[0m")
    #3a. Add the delivery amount to the running total. 
    current_total, new_value = process_delivery(current_total, new_value)
    #3b. Calculate the tax for that delivery. 
    tax = calculate_tax(new_value)
    #3c. Update any counters and records you are tracking, such as the number of deliveries processed. 
    totaltax += tax
    quit = overstock_alert(current_total)
    
generate_report(current_total, entrycount, totaltax, failed_attempts)  