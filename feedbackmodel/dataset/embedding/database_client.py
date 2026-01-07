import os
import chromadb
from dataset.processing.dataset_loader import load_dataset
from dataset.embedding.embedding_generator import encode_texts

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "chroma")
)

def initialize_db():
    os.makedirs(BASE_DIR, exist_ok=True)
    print("Persist dir:", BASE_DIR)

    client = chromadb.PersistentClient(
        path=BASE_DIR
    )

    collection = client.get_or_create_collection(
        name="feedback_priority_rag"
    )

    train_set = load_dataset("train")

    ids = [f"train_{fid}" for fid in train_set["feedback_id"]]
    documents = train_set["feedback_text"].tolist()
    embeddings = encode_texts(train_set["feedback_text"])

    metadatas = [
        {
            "split": "train",
            "labeled": False,
            "category": row["category"],
            "source_context": row["source_context"],
            "actionability_hint": row["actionability_hint"]
        }
        for _, row in train_set.iterrows()
    ]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )

    print("Collection count:", collection.count())
    print("Chroma persistence complete.")

if __name__ == "__main__":
    initialize_db()
