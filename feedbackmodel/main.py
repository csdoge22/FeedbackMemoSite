import re
import string
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

def tokenize(text: str):
    # Naive Tokenization:
    lower_text = text.lower()
    translator = str.maketrans('', '', string.punctuation)
    clean_text = lower_text.translate(translator)
    return np.array(clean_text.split(" "))

if __name__=="__main__":
    # print(tokenize("The heart is red"))
    # print(tokenize("Hi John! Hello there Nancy. Fine day eh?"))
    TfidfVectorizer()
    
    print()
