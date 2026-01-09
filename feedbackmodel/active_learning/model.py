from feedbackmodel.dataset.processing.dataset_loader import load_dataset

def train_active_learning_model():
    """
    Train an active learning model using the training dataset.
    """
    # Load training data
    train_df = load_dataset("train")
    if "feedback_text" not in train_df.columns or "label" not in train_df.columns:
        raise ValueError("Training dataset must contain 'feedback_text' and 'label' columns.")

    texts = train_df["feedback_text"].tolist()
    labels = train_df["label"].tolist()

    # Encode texts
    embeddings = encode_texts(texts)

    # Initialize and train model
    model = ActiveLearningModel()
    model.train(embeddings, labels)

    return model