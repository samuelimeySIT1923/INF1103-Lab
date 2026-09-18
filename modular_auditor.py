
#Requirements: 
#Create a copy of your auditor.py from last week and name it modular_auditor.py. 
#This ensures you have a backup of your Week 2 solution. 




#4. Reporting: When the user types quit, print the Total Deliveries Processed        
#and the Number of Failed/Rejected Entries. 
#Your program must now consist of specific functions: 
#1. get_valid_input(): Handles the prompt, handles input validation, and 
#returns a valid integer or a "quit" signal. 
#2. process_delivery(current_total, new_value): Calculates the new total and 
#returns it. 
#3. calculate_tax(amount): A new requirement! This function takes a delivery 
#amount and returns the tax (10% of that specific delivery). 
#4. generate_report(total_units, failed_attempts): A dedicated function to print 
#the final summary. 
#Don't write code straight away. Map out your function signatures. A function 
#signature defines the inputs and outputs. Example: def process_delivery(total, 
#value): return new_total. Map your logic: 
#o What goes into get_valid_input()? (Nothing). What comes out? 
#(The number or a 'quit' status). 
#SIT Internal 
#o What goes into calculate_tax()? (The delivery value). What comes 
#out? (The tax amount). 
#o Then write the code





#1. Initialize the inventory to zero in the start
inv = 0
quit = False
entrycount = 0
errorcount = 0

#2. Run in a continuous loop asking user to enter a stock quantity, until the user types quit. (Think of which loop might be helpful here: "for,or,while")
while quit == False:
    inputQty = input("Enter stock quantity (or type 'quit' to exit): ")
    if inputQty.lower() == 'quit':  
            quit = True
            break
    if not (inputQty.lstrip('-').isdigit()):
        print("Error: pls enter a valid number or type 'quit' to exit.")
        errorcount += 1
        continue
    if int(inputQty) < 0:
        print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
        errorcount += 1
        continue
    elif inputQty.isdigit():
        print("Stock Quantity entered:", inputQty)
        
        inv += int(inputQty)
        if int(inv) > 500:
            print("ALERT: Overstock! Total inventory exceeds 500 units.")
            errorcount += 1
            break
        entrycount += 1
        print(entrycount,". Total Inventory:", inv)
#3. If the user enters a valid value:  
#• Add the delivery amount to the running total. 
#• Calculate the tax for that delivery. 
#• Update any counters and records you are tracking, such as the number 
#of deliveries processed. 

print("\n\033[1m", "Report Summary:", "\033[0m")
print("Total Units Processed:", inv)
print("Number of Failed/Rejected Entries:", errorcount)
    