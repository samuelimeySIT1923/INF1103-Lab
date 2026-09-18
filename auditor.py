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
    #4. Handle invalid input, ".lsstrip('-')" allow negative numbers to go through by stripping the negative sign before checking.
    if not (inputQty.lstrip('-').isdigit()):
        print("Error: pls enter a valid number or type 'quit' to exit.")
        errorcount += 1
        continue
    #5. Enforce business rules: Reject negative numbers.
    if int(inputQty) < 0:
        print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
        errorcount += 1
        continue
    #3. Accept stock values as integers
    elif inputQty.isdigit():
        print("Stock Quantity entered:", inputQty)
        #6. Manage State: Keep a running total of the inventory.
        inv += int(inputQty)
        #7. Trigger Overstock Alert: If the total inventory exceeds 500 units, print an alert and break the loop immediately. (keep in mind of the conditional flow we discussed this week: if, elif and else)
        if int(inv) > 500:
            print("ALERT: Overstock! Total inventory exceeds 500 units.")
            errorcount += 1
            break
        entrycount += 1
        print(entrycount,". Total Inventory:", inv)

#8. Reporting: When the user types quit, print the Total Units Processed and the Number of Failed/Rejected Entries.
print("\n\033[1m", "Report Summary:", "\033[0m")
print("Total Units Processed:", inv)
print("Number of Failed/Rejected Entries:", errorcount)
    


    
    
    

   



