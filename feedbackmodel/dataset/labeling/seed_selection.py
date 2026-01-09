import os
import numpy as np

from dataset.embedding.embedding_generator import EMBEDDING_DIR

def select_initial_seed():
    # load the train embeddings
    train_embeddings = np.load(os.path.join(EMBEDDING_DIR,"train_all-MiniLM-L6-v2_801rows.npy"))
    print(f"Train Embeddings Shape: {train_embeddings.shape}")

if __name__ == "__main__":
    select_initial_seed()