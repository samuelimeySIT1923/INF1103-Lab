import difflib
import nltk
from string.templatelib import convert
from nltk.corpus import wordnet
nltk.download("wordnet", quiet=True)

#1. Call any input with unknown category (Categories: Misc) in Array table
#2. User input description and save to new column
#3. Match words in description with listed category
#   1. If match, change “Misc” to said category
#   2. Else, Check if user still wants to keep it at Misc Category
#      1. If Yes, save Description and keep as Misc
#      2. If no, ask to re-enter description

# Naming Convention
# lower full - definition
# 1st lower and rest Uppper no underscore - system variables
# 1st lower and rest Uppper with underscore - ???
# Full Upper no underscore - user input
# Full Upper with Underscroe - Stored Arrays

ALL_KNOWN_CATEGORIES = {}
FULL_TABLE = []
MISC_TABLE = []

#Function 1A: Sort any item with invalid categories into "Misc"
def assignmisc(rows):
    for row in rows:
        if row.get("category") not in ALL_KNOWN_CATEGORIES: #To includ array of defined categories
            row["category"] = "Misc"
    return rows

#Function 1B: Call any rows with Misc Categories
def getmisc(rows):
    """Return all rows categorized as 'Misc'."""
    return [row.copy() for row in rows if row["category"] == "Misc"]

#Function 2A: For any rows with Description "Misc", ask for user input
def adddescription(rows):
    for row in rows:
        row["description"] = input(f"Describle '{row['Input']}': ").strip()
    return rows

assignmisc(FULL_TABLE)
MISC_TABLE = getmisc(FULL_TABLE)
adddescription(MISC_TABLE)

#Way to view and print out misc table rows
for row in getmisc(FULL_TABLE):
    print(row)

#once done with table, reset table to blank state
MISC_TABLE.clear()

#[Shelved Function]
#def inoutflowcheck(TransactionType):
    if TransactionType.lower() == 'inflow':
        return True
    elif TransactionType.lower() == 'outflow':
        return False
    else:
        return None

#[Shelved Function]
#def swaptransaction(TransactionType, changetransaction): 
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

#        
def match_category(description, threshold=0.5):
    """Return the category most similar to any word in the description, or None."""
    words = description.lower().split()

    best_category = None
    best_score = 0

    for category in categoryType:
        synCategory = wordnet.synsets(category.lower(), pos=wordnet.NOUN)

        for word in words:
            synsDesc = wordnet.synsets(word, pos=wordnet.NOUN)

            for s1 in synsDesc:
                for s2 in synCategory:
                    score = s1.path_similarity(s2)   # 0 to 1, or None
                    if score and score > best_score:
                        best_score = score
                        best_category = category

    if best_score >= threshold:
        print(f"'{description}' matches category '{best_category}' ({best_score:.2f})")
        return best_category
    return None

def match_category(description):
    """Return the first category whose name or keywords appear in the description."""
    words = set(description.lower().split())
    for category, keywords in CATEGORIES.items():
        if category.lower() in words or words & set(keywords):
            return category
    return None


def resolve_misc(table):
    for row in table:
        row.setdefault("description", "")          # new column

        if row["category"] != "Misc":              # Step 1: only call Misc rows
            continue

        while True:
            # Step 2: user enters description
            desc = input(f"Describe '{row['item']}' (${row['amount']}): ").strip()
            row["description"] = desc

            # Step 3: match words to a category
            found = match_category(desc)
            if found:                              # 3.1 match -> replace Misc
                row["category"] = found
                print(f"  -> Category changed to {found}")
                break

            # 3.2 no match -> ask whether to keep Misc
            keep = input("  No match found. Keep as Misc? (y/n): ").strip().lower()
            if keep == "y":                        # 3.2.1 save description, stay Misc
                print("  -> Kept as Misc")
                break
            # 3.2.2 "n" -> loop back and ask for a new description

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

from test import words_are_similar
nltk.download('wordnet')
from nltk.corpus import wordnet

dataBase = []
categoryType = ["groceries", "food & drink", "entertainment", "transport", "bills", "others"]

errrorCheck = None


resolve_misc(table)
for row in table:
    print(row)