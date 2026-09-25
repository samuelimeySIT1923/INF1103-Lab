#Initialize the inventory to zero in the start
import re


quit = False
current_total = 0
failed_attempts = 0
totaltax = 0
final_total = 0
entry_count = 0
#2. History Tracking: Use a Python list (array) to store every valid transaction 
#amount entered. 
totalOrderList = []
newOrderList = []
recentInput = []


#4. Modularity: Maintain your functional design. Create a load_inventory() and save_inventory() function. 
def load_inventory(totalOrderList,entry_count, final_total):
    #Persistence: At the start of the program, read the information previously saved in the inventory file.
    try:
        with open('inventory.txt', 'r') as file:
            totalOrderList = file.readlines()
            print(f"Current Orders: {totalOrderList}")
            print(f"Overall stock input: {final_total}")
            entry_count = int(totalOrderList[-3]) if totalOrderList else 0
    #If the inventory file does not exist, start with an empty inventory and continue running without producing an error.
    except FileNotFoundError:
         totalOrderList = []
         entry_count = 0
         final_total = 0
    return totalOrderList, entry_count, final_total

def save_inventory(totalOrderList,newOrderList):
    totalOrderList.extend(newOrderList)
    with open('inventory.txt', 'a') as file:
        print("New orders Added:")
        #Print each product [Order no, Product Name, Quantity]:
        for o in range(0, len(newOrderList), 3):
            chunk = newOrderList[o : o + 3]
            newTxtLine = ', '.join(str(x) for x in chunk)
            file.write(newTxtLine + '\n')
            print(newTxtLine)
    file.close()
    print("Order sucessfully saved to inventory.txt")
    return totalOrderList, newOrderList

#Handles the prompt, handles input validation, and returns a valid integer or a "quit" signal. 
def get_valid_input(entry_count):
    new_value = input("Enter stock quantity (or type 'quit' to exit): ")
    product_name = input("Enter product name: ") 
    if new_value.lower() == 'quit':  
            return 'quit', False, entry_count
    if not (new_value.lstrip('-').isdigit()):
            print("Error: pls enter a valid number or type 'quit' to exit.")
            return None, True, entry_count
    new_value = int(new_value)
    if new_value < 0:
            print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
            return None, True, entry_count
    else:
        #Update any counters and records you are tracking, such as the number of deliveries processed. 
        entry_count += 1
        recentInput = [entry_count, product_name, new_value]
        print(f"\n\033[1m Entry Count {entry_count} , {product_name}\033[0m")
        #newOrderList.append(recentInput)
        return recentInput, False, entry_count, product_name, new_value

 #Calculates the new total and returns it.        
def process_delivery(current_total, new_value):
    current_total += new_value
    print("Stock Quantity entered:", new_value)
    return current_total, new_value

#Takes a delivery amount and returns the tax (10% of that specific delivery). 
def calculate_tax(new_value):
    tax = new_value * 0.10
    print("Tax for this delivery: S$", tax)
    return tax

#Print the final summary. 
def generate_report(current_total, totaltax, failed_attempts):
    print("\n\033[1m", "Report Summary:", "\033[0m")
    print("Total Units Processed:", current_total)
    print("Total Tax Paid: S$", totaltax)
    print("Number of Failed/Rejected Entries:", failed_attempts)

def overstock_alert(current_total):
    if current_total > 500:
        print("ALERT: Overstock! Total inventory input exceeds 500 units!")
        return True
    return False

totalOrderList, entry_count, final_total = load_inventory(totalOrderList, entry_count, final_total)
#Continuous loop asking user to enter a stock quantity, until the user types quit. 
while quit == False:
    recentInput = []
    recentInput, has_error, entry_count = get_valid_input(recentInput, entry_count)
    if new_value == 'quit':
        quit = True
        break
    if has_error:
        failed_attempts += 1
        print("Number of Failed/Rejected Entries:", failed_attempts)
        continue
    #Add the delivery amount to the running total. 
    print(recentInput)
    new_value = recentInput[2]
    newOrderList.extend(recentInput)
    current_total, new_value = process_delivery(current_total, new_value)
    #Calculate the tax for that delivery. 
    tax = calculate_tax(new_value)
    #Update any counters and records you are tracking, such as the number of deliveries processed. 
    totaltax += tax
    quit = overstock_alert(current_total)
generate_report(current_total, totaltax, failed_attempts)

#3. Write-Back: When the user types quit, save the final total and the transaction history list to inventory.txt. 
save_inventory(totalOrderList,newOrderList)

