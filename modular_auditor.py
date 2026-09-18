#1. Initialize the inventory to zero in the start
quit = False
entrycount = 0
current_total = 0
failed_attempts = 0

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

#4d. generate_report(current_total, failed_attempts): A dedicated function to print the final summary. 
def generate_report(current_total, failed_attempts):
    print("\n\033[1m", "Report Summary:", "\033[0m")
    print("Total Units Processed:", current_total)
    print("Number of Failed/Rejected Entries:", failed_attempts)\

#2. Run in a continuous loop asking user to enter a stock quantity, until the user types quit. (Think of which loop might be helpful here: "for,or,while")
while quit == False:
    new_value, has_error = get_valid_input()
    if new_value == 'quit':
        quit = True
        break
    if has_error:
        failed_attempts += 1
        print("Number of Failed/Rejected Entries:", failed_attempts)
        continue
    entrycount += 1
    print("\n\033[1m", "Entry Count:", entrycount, "\033[0m")
    current_total, new_value = process_delivery(current_total, new_value)
    tax = calculate_tax(new_value)

        
generate_report(current_total, failed_attempts)  





#Don't write code straight away. Map out your function signatures. A function 
#signature defines the inputs and outputs. Example: def process_delivery(total, 
#value): return new_total. Map your logic: 
#o What goes into get_valid_input()? (Nothing). What comes out? (The number or a 'quit' status). 
#o What goes into calculate_tax()? (The delivery value). What comes out? (The tax amount). 
#o Then write the code


#3. If the user enters a valid value:  
#• Add the delivery amount to the running total. 
#• Calculate the tax for that delivery. 
#• Update any counters and records you are tracking, such as the number of deliveries processed. 


#    elif new_value.isdigit():
#        print("Stock Quantity entered:", new_value)
#
#        inv += int(new_value)
#        if int(inv) > 500:
#            print("ALERT: Overstock! Total inventory exceeds 500 units.")
#            failed_attempts += 1
#            break
#        current_total += 1
#        print(current_total,". Total Inventory:", inv)
    
#new_value.isdigit():
#       print("Stock Quantity entered:", new_value)
#
#        inv += int(new_value)
#        if int(inv) > 500:
#            print("ALERT: Overstock! Total inventory exceeds 500 units.")
#            failed_attempts += 1
#            break
#        current_total += 1
#        print(current_total,". Total Inventory:", inv)