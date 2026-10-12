import re
import nltk
import difflib
from datetime import datetime
from nltk.corpus import wordnet

nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

# Naming Convention
# lower full - definition
# 1st lower and rest Uppper no underscore - system variables
# 1st lower and rest Uppper with underscore - ???
# Full Upper no underscore - user input
# Full Upper with Underscroe - Stored Arrays

ALL_KNOWN_CATEGORIES = [ 
    "Food",
    "Transport",
    "Groceries",
    "Entertainment",
    "Bills",
    "Shopping",
    "Misc",
]
FULL_TABLE = []
MISC_TABLE = []

#[For 3A] lookup table that store WordNet's meaning for each category
CATEGORY_SYNSETS = {
    category: wordnet.synsets(category.lower(), pos=wordnet.NOUN)
    for category in ALL_KNOWN_CATEGORIES
}

#[For 3B] Array of every noun WordNet knows
ALL_NOUNS = list(wordnet.all_lemma_names(pos=wordnet.NOUN))

#Function 1A: Sort any item with invalid categories into "Misc"
def assignmisc(mainRows):
    for row in mainRows:
        if row.get("category") not in ALL_KNOWN_CATEGORIES: #To includ array of defined categories
            row["category"] = "Misc"
    return mainRows

#Function 1B: Call any rows with Misc Categories
def getmisc(mainRows):
    """Return all rows categorized as 'Misc'."""
    return [row.copy() for row in mainRows if row["category"] == "Misc"]

#Function 3A: Fix Typo with Closest known words
def fixtypo(word, cutoff=0.8):
    if len(word) < 4:                    # Omit short words given too many false fixes
        return word
    if wordnet.synsets(word):            # WordNet knows word in any part of speech
        return word
    matches = difflib.get_close_matches(word, ALL_NOUNS, n=1, cutoff=cutoff)
    if matches:
        print(f"  (corrected '{word}' -> '{matches[0]}')") #declare autocorrected word
        return matches[0]
    return word

#Function 3B: Return category most similar to word in description, or none
def matchcategory(description, threshold=0.2): #treshold = level of acceptance to determine similarity of words
    words = {fixtypo(word) for word in re.findall(r"[a-z]+", description.lower())}
        
    bestCategory = None #temp variable to store closest category
    bestScore = 0 #temp variable to determine highscore of closest category
    
    for category, synCategory in CATEGORY_SYNSETS.items(): #for every category with stored meanings 
        for word in words: #for every word in description
            for synWord in wordnet.synsets(word, pos=wordnet.NOUN): #lookup word meaning in WordNet 1 at a time
                for synCat in synCategory: #For each meaning of category
                    # Compare closenest of meaning [1.0 = identical meaning, 0.5 = 1 step apart, 
                    # 0.25 = 3 Steps apart, none = meanings not connected]
                    score = synWord.path_similarity(synCat) 
                    if score and score > bestScore:     #Remember if highet score so far               
                        bestScore = score
                        bestCategory = category

    if bestScore >= threshold: #ie highscore higher than threshold
        print(f"'{description}' matches category '{bestCategory}' ({bestScore:.2f})") #Announce Description matches a category [List score - debugging]
        return bestCategory #return closest category
    return None #none if below threshold

#Function 3C: Accepting of User input [Y/N]
def askyn(prompt):
    while True: #loop until return occurs [ie valid Y/N]
        answer = input(prompt).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer yes or no.")

#Function 3D: Asking & Matching of Description
def processmiscrows(tempRows):
    for row in tempRows:
        while True: #ie Get 1 row with Misc Category
            #Function 2: For any rows with Description "Misc", ask for user input
            row["description"] = input(f"Describe '{row['transaction_id']}' on '{row['date_and_time']}': ").strip()
            matched = matchcategory(row["description"])

            #3Ci. Match with ALL_KNOWN_CATEGORIES
            if matched:                                   
                row["category"] = matched
                print(f"  -> Matched category: {matched}")
                break

            #3Cii. No match: Ask whether to keep as Misc
            if askyn("No category matched. Keep Category as 'Misc'? (yes/no) "):
                print("  -> Description saved, kept as Misc.")
                break
            print("  Category not matched, please retype & rephrase.")  # 3b-ii

#Function 4A: Write updated category and description back to the main table.
def synctomain(mainRows, tempRows):
    updates = {row["transaction_id"]: row for row in tempRows}
    for row in mainRows:
        if row["transaction_id"] in updates:
            row["category"] = updates[row["transaction_id"]]["category"]
            row["description"] = updates[row["transaction_id"]]["description"]

#Running Code
assignmisc(FULL_TABLE)
MISC_TABLE = getmisc(FULL_TABLE)
processmiscrows(MISC_TABLE)
synctomain(FULL_TABLE, MISC_TABLE)

#Output Sent
updateStamp = datetime.now().strftime("%Y-%m-%d[%H:%M:%S]")
print(f"Final table: \n On {updateStamp}")
for row in FULL_TABLE:
    print(row)

#once done with table, reset table to blank state
MISC_TABLE.clear()