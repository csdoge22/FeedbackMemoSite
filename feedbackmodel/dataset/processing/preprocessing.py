# dataset/processing/preprocessing.py

import re
import unicodedata

def clean_text(text: str) -> str:
    """
    Clean and normalize text for embedding generation.
    Steps:
        1. Lowercase
        2. Remove extra whitespace
        3. Remove non-ASCII characters
        4. Normalize unicode
        5. Optional: remove punctuation (if desired)
    """
    if not isinstance(text, str):
        text = str(text)

    # Lowercase
    text = text.lower()

    # Normalize unicode (e.g., accents)
    text = unicodedata.normalize("NFKD", text)

    # Remove non-ASCII characters
    text = text.encode("ascii", "ignore").decode("utf-8")

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def preprocess_text_series(text_series):
    """
    Apply cleaning to a pandas Series of text.
    Returns a list of cleaned strings.
    """
    return [clean_text(t) for t in text_series]
