import re
import nltk
import difflib

from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple
from nltk.corpus import stopwords, wordnet

def ensurewordnet() -> None: ##Check if wordnet is downloaded, else will download. Nothing expected to return
    try:
        wordnet.synsets("bird")
    except LookupError:
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
    try:
        stopwords.words("english")
    except LookupError:
        nltk.download("stopwords", quiet=True)

ensurewordnet()
STOPWORDS = set(stopwords.words("english")) #frequently used unique words in langauge
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Food": ["meal", "breakfast", "lunch", "dinner", "cafe", "restaurant", "snack", "foodpanda", "grabfood", "deliveroo"],
    "Transport": ["bus", "train", "taxi", "gojek", "tada", "ezlink", "fare", "mrt", "petrol", "fuel"],
    "Groceries": ["grocery", "supermarket", "fairprice", "ntuc", "vegetable", "fruit", "meat"],
    "Entertainment": ["movie", "game", "concert", "cinema"],
    "Bills": ["electricity", "water", "rent", "utility", "phone", "insurance", "loans"],
    "Shopping": ["clothes", "shoes", "mall", "gadget", "shopee", "lazada", "amazon", "uniqlo"],
} #Shortcut for potential keywords 

@lru_cache(maxsize=1) #decorator to call nouns once and store for future reference [ie no need to keep loading nouns]
def nounsbylength() -> Dict[int, List[str]]: #expect list of strings (words) mapped by int
    groups: Dict[int, List[str]] = {} #Create  disctionary mapping int [word length int] to a list of strings [words]
    for noun in wordnet.all_lemma_names(pos=wordnet.NOUN): #for every noun
        if noun.isalpha():
            groups.setdefault(len(noun), []).append(noun) #ensure words are pure letters
    return groups

@lru_cache(maxsize=4096) #Fix Typo with Closest known words
def fixtypo(word: str, cutoff: float = 0.8) -> str:
    if len(word) < 4:  # Omit short words as they cause too many false fixes
        return word
    if wordnet.synsets(word):  # WordNet knows word in any part of speech, return word
        return word
    bylength = nounsbylength() #fetches dictionary of nouns
    pool = [
        noun
        for length in range(len(word) - 2, len(word) + 3) #length range of n-2 to n+3
        for noun in bylength.get(length, []) #return empty list instead of KeyError if no nouns found
    ] 
    matches = difflib.get_close_matches(word, pool, n=1, cutoff=cutoff) #compare word against pool of words, matches if n=1 when at least cutoff range [ie 0.8]
    return matches[0] if matches else word #Return best matching word, else return original word unchanged
 
@lru_cache(maxsize=512) #Given Cateogry Name, return WordNet noun meaning and keywords as a tuple. Run once and reuse
def categorysynsets(category: str) -> tuple: 
    words = re.findall(r"[a-z]+", category.lower()) #standby to handle multiple words
    words += CATEGORY_KEYWORDS.get(category.title(), []) #build list of words to lookup [Category + keywords, no keywords = blank]
    synsets = []
    for w in words: #for each word meaning, add to 1 list
        if w in STOPWORDS: #skip if it is a frequently used unique words in langauge
            continue
        synsets.extend(wordnet.synsets(w.replace(" ", "_"), pos=wordnet.NOUN)) #look up noun meaning of 1 word/phrase and add on to running list, convert space to "_"
    return tuple(synsets)

#Return (best_category, score) for a description or (None, 0.0)
@lru_cache(maxsize=1024)
def matchcategory(description: str, categories: Iterable[str]) -> Tuple[Optional[str], float]: 
    threshold: float = 0.2
    words = {
        fixtypo(w) #fix typo
        for w in re.findall(r"[a-z]+", (description or "").lower()) #if description is blank, become empty string instead of crashing
        if w not in STOPWORDS #drop filler words
    }
    word_synsets = [
        syn for w in words for syn in wordnet.synsets(w, pos=wordnet.NOUN) # Look up each word's meanings once
    ]
    if not word_synsets: #if no word have any meaning = return early with no match
        return None, 0.0
    bestCategory: Optional[str] = None
    bestScore = 0.0 #
    for category in categories: #for every category
        for cat_syn in categorysynsets(category): #for every meaning stored in list
            for word_syn in word_synsets: #for every word
                score = word_syn.path_similarity(cat_syn)
                # Compare closenest of meaning [1.0 = identical meaning, 0.5 = 1 step apart, 
                # 0.25 = 3 Steps apart, none = meanings not connected]
                if score and score > bestScore: #Remember if highet score so far
                    bestScore = score
                    bestCategory = category
 
    if bestScore >= threshold: #if exceed treshold, return. Else reject
        return bestCategory, bestScore
    return None, 0.0