#Naming Convention
# lower full - definition
# 1st lower and rest Uppper no underscore - system variables
# 1st lower and rest Uppper with underscore - ???
# Full Upper no underscore - user input

ef getdata(errrorCheck, data):
    TotalInputCount = input("Enter number of entries to input: ")
    if not (TotalInputCount.lstrip('-').isdigit()):
            print("Error: pls enter a valid number.")
            return 'error', None  
    TotalInputCount = int(TotalInputCount)
    if TotalInputCount < 0:
            print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
            return 'error', None
    for i in range(int(TotalInputCount)):
        #In Discretion on how Input Validaation & Error Cath will be executed,
        inputFile = []
        inputNo = i
        Transaction_ID = input("Enter your transaction Reference:")
        Date = input("Enter the date of transaction (DDMMYYYY):")
        if not (Date.isdigit() and len(Date) == 8):
            print("Error: Invalid date format. Please enter the date in DDMMYYYY format.")
            return 'error', None
        Time = input("Enter the time of transaction (HHMM):")
        if not (Time.isdigit() and len(Time) == 4):
                print("Error: Invalid time format. Please enter the time in HHMM format.")
                return 'error', None  
        Retailer = input("Enter the retailer name:")
        Category = input("Enter the category of the product:")
        callcategory()
        TransactionType = input("Enter the transaction type (ie Inflow, Outflow):")
        if TransactionType.lower() not in ['inflow', 'outflow']:
            print("Error: Invalid transaction type. Please enter 'Inflow' or 'Outflow'.")
            return 'error', None
        TransactionAmount = input("Enter the transaction amount:")
        if not (TransactionAmount.lstrip('-').isdigit()):
            print("Error: pls enter a valid number.")
            return 'error', None  
        TransactionAmount = int(TransactionAmount)
        if TransactionAmount < 0:
            print(f"Error: Negative numbers detected. This is a {TransactionType} entry.")
            if TransactionType.lower() == 'outflow':
                
                print(input"Do you want to swap to a Inflow Transaction? se enter a positive number.")
        
            print(input("Please confirm if you want to proceed with this amount (yes/no): ").strip().lower())
            return 'error', None       

           #Re-evaluation of user input after clarification from user