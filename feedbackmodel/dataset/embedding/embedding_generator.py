# dataset/embedding/embedding_generator.py
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from dataset.processing.dataset_loader import load_dataset, get_split_ids

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIR = os.path.join(os.path.dirname(__file__), "../data/embeddings")
os.makedirs(EMBEDDING_DIR, exist_ok=True)

def encode_texts(texts: list[str], model_name: str = MODEL_NAME) -> np.ndarray:
    """
    Generate embeddings for a list of texts using SentenceTransformer.

    Args:
        texts (list[str]): Text strings to encode.
        model_name (str): Pretrained SentenceTransformer model name.

    Returns:
        np.ndarray: Embeddings array (num_texts, embedding_dim)
    """
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings

def encode_dataset_split(split_name: str) -> tuple[list[str], np.ndarray]:
    """
    Encode the 'feedback_text' column for a specific dataset split,
    and return embeddings along with unique string IDs.

    Args:
        split_name (str): 'train', 'test', or 'stop'.

    Returns:
        ids (list[str]): Unique string IDs for each row.
        embeddings (np.ndarray): Corresponding embeddings.
    """
    df = load_dataset(split_name)
    if "feedback_text" not in df.columns:
        raise ValueError("Dataset must contain 'feedback_text' column.")
    
    ids = get_split_ids(split_name)
    embeddings = encode_texts(df["feedback_text"].tolist())

    # Save embeddings to disk for caching
    save_path = os.path.join(EMBEDDING_DIR, f"{split_name}_{MODEL_NAME}_{df.shape[0]}rows.npy")
    np.save(save_path, embeddings)
    print(f"Saved {split_name} embeddings to: {save_path}")

    return ids, embeddings

def encode_all_splits() -> dict[str, tuple[list[str], np.ndarray]]:
    """
    Encode all dataset splits and return a dictionary mapping split_name
    to (IDs, embeddings).

    Returns:
        dict[str, tuple[list[str], np.ndarray]]: Mapping from split to embeddings & IDs
    """
    results = {}
    for split in ["train", "test", "stop"]:
        ids, embeddings = encode_dataset_split(split)
        results[split] = (ids, embeddings)
    return results

if __name__ == "__main__":
    all_embeddings = encode_all_splits()
    for split, (ids, embs) in all_embeddings.items():
        print(f"{split} -> {len(ids)} embeddings, shape: {embs.shape}")
