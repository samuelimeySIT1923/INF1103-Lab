import difflib
from string.templatelib import convert

#Pls install nltk library if not already installed via cmd or terminal using the command [windows+R > cmd] below:
# pip install nltk
import nltk

from test import words_are_similar
nltk.download('wordnet')
from nltk.corpus import wordnet


dataBase = []
categoryType = ["groceries", "food & drink", "entertainment", "transport", "utility bills", "loans bills", "subscriptions bills", "others"]

errrorCheck = None
#Naming Convention
# lower full - definition
# 1st lower and rest Uppper no underscore - system variables
# 1st lower and rest Uppper with underscore - ???
# Full Upper no underscore - user input

def callcategory(EntryCategory):
        if EntryCategory.lower() not in categoryType:
            print("Invalid EntryCategory. EntryCategory pushed to Others.")
            EntryCategory = "others"
        return EntryCategory

def inflowoutflowcheck(TransactionType):
    if TransactionType.lower() == 'inflow':
        return True
    elif TransactionType.lower() == 'outflow':
        return False
    else:
        return None
    
def swaptransaction(TransactionType, changetransaction):
    if TransactionType.lower() == 'outflow':
        userInput = input("Do you want to swap to a Inflow Transaction? Clicking 'n' will void input. (y/n) ").strip().lower()
        if userInput == 'y':
            return 'inflow',True
        elif userInput == 'n':
            return 'outflow',False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            return swaptransaction()  # Recursively call until valid input is received
    elif TransactionType.lower() == 'inflow':
        userInput = input("Do you want to swap to a Outflow Transaction? Clicking 'n' will void input. (y/n) ").strip().lower()
        if userInput == 'y':
            return 'outflow',True
        elif userInput == 'n':
            return 'inflow',False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
            return swaptransaction()  # Recursively call until valid input is received

def lookupDescription(Description):
    #convert to synsets format
    synsDesc = wordnet.synsets(Description)
    for category in categoryType:
        #convert to synsets format
        synCategory = wordnet.synsets(category)
        #Compare to item in category Type list

        maxScore = 0
        for s1 in synsDesc:
            for s2 in synCategory:
                score = s1.path_similarity(s2)  # Returns a value between 0 and 1
                if score and score > maxScore:
                    maxScore = score
        return maxScore

        similarity_score = words_are_similar(synsDesc, synCategory)
        if similarity_score > 0.5:
            print(f"'{Description}' matches category '{category}'")
            return category

def entriesinput(errrorCheck, TotalInputCount):
    errorCheck = None
    TotalInputCount = input("Enter number of entries to input: ")
    if not (TotalInputCount.lstrip('-').isdigit()):
            print("Error: pls enter a valid number.")
            return entriesinput(), None  
    TotalInputCount = int(TotalInputCount)
    if TotalInputCount < 0:
            print("Error: Negative numbers are not allowed. Pls input a positive number or type 'quit' to exit.")
            return entriesinput(), None  
    else:
         return None, TotalInputCount

def getdata(errrorCheck, dataBase):
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
        EntryCategory = input("Enter the category of the product: [ie 'groceries', 'food & drink', 'entertainment', 'transport', 'utility bills', 'loans bills', 'subscriptions bills', 'others']")
        EntryCategory = callcategory(EntryCategory)
        TransactionType = input("Enter the transaction type (ie Inflow, Outflow):")
        inflowoutflowcheck(TransactionType)
        if inflowoutflowcheck(TransactionType) is None:
            print("Error: Invalid transaction type. Please enter 'Inflow' or 'Outflow'.")
            return 'error', None
        TransactionAmount = input("Enter the transaction amount:")
        if not (TransactionAmount.lstrip('-').isdigit()):
            print("Error: pls enter a valid number.")
            return 'error', None  
        TransactionAmount = int(TransactionAmount)
        if TransactionAmount < 0:
            print(f"Negative numbers detected. This is a {TransactionType} entry.")
            TransactionType, changetransaction = swaptransaction(TransactionType, changetransaction)
            if changetransaction == False:
                print(f"Error: Negative numbers detected. Please enter a positive amount.")
            else:
                TransactionAmount = abs(TransactionAmount)
                print(f"Transaction type swapped to {TransactionType}. Amount changed to ${TransactionAmount}.")
        inputFile.append([int(inputNo),Transaction_ID, Date, Time, Retailer, EntryCategory, TransactionType, int(TransactionAmount)])
        if inputFile[5] == 'others':
            #Enable user add transaction description
            Description = input("Please provide more information on this input: ")
            inputFile.append(Description)
            EntryCategory = lookupDescription(Description)
            if EntryCategory is not None:
                inputFile[5] = EntryCategory
        else:
            inputFile.append(None) 
        print(f"Successfully added transaction {inputNo}!")
        print(f"Details ID: {Transaction_ID}, Date: {Date}, Time: {Time}, Retailer: {Retailer}, Category: {EntryCategory}, Type: {TransactionType}, Amount: ${TransactionAmount}")


TotalInputCount = 0
errrorCheck, TotalInputCount = entriesinput(errrorCheck, TotalInputCount)
errrorCheck, dataBase = getdata(errrorCheck, dataBase)
