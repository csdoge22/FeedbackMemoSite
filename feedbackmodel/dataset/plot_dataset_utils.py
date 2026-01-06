import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Statistically plot the distribution of categories in the generated dataset
def plot_source_context_distribution(tsv_url: str) -> None:
    """ This function plots the distribution of feedback categories in the generated dataset. """
    dataframe = pd.read_csv(tsv_url, sep="\t")
    plt.figure(figsize=(20,7))
    plt.bar(dataframe['source_context'].unique(), dataframe['source_context'].value_counts())
    os.makedirs(os.path.join(os.path.dirname(__file__),"plots"), exist_ok=True)
    plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "plots", "distribution1.png")))
    print(dataframe['source_context'].value_counts())
    return dataframe['source_context'].value_counts()

def get_source_context_train_size(tsv_url: str) -> str:
    optimal = pd.Series.astype(np.ceil(plot_source_context_distribution(tsv_url=tsv_url)*0.8), dtype=int)
    return optimal, pd.Series.sum(optimal)

def plot_category_distribution(tsv_url: str) -> None:
    """ This function plots the distribution of feedback categories in the generated dataset. """
    dataframe = pd.read_csv(tsv_url, sep="\t")
    plt.figure(figsize=(20,7))
    plt.bar(dataframe['category'].unique(), dataframe['category'].value_counts())
    os.makedirs(os.path.join(os.path.dirname(__file__),"plots"), exist_ok=True)
    plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "plots", "distribution2.png")))
    print(dataframe['category'].value_counts())
    return dataframe['category'].value_counts()

def get_category_train_size(tsv_url: str) -> str:
    optimal = pd.Series.astype(np.ceil(plot_category_distribution(tsv_url=tsv_url)*0.8), dtype=int)
    return optimal, pd.Series.sum(optimal)

def plot_actionability_hint_distribution(tsv_url: str) -> None:
    """ This function plots the distribution of feedback categories in the generated dataset. """
    dataframe = pd.read_csv(tsv_url, sep="\t")
    plt.figure(figsize=(20,7))
    plt.bar(dataframe['actionability_hint'].unique(), dataframe['actionability_hint'].value_counts())
    os.makedirs(os.path.join(os.path.dirname(__file__),"plots"), exist_ok=True)
    plt.savefig(os.path.abspath(os.path.join(os.path.dirname(__file__), "plots", "distribution3.png")))
    print(dataframe['actionability_hint'].value_counts())
    return dataframe['actionability_hint'].value_counts()

def get_actionability_hint_train_size(tsv_url: str) -> str:
    optimal = pd.Series.astype(np.ceil(plot_actionability_hint_distribution(tsv_url=tsv_url)*0.8), dtype=int)
    return optimal, pd.Series.sum(optimal)

if __name__=="__main__":
    # print(os.curdir)
    dataset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "synthetic_feedback_dataset.tsv"))
    # print(get_source_context_train_size(dataset_path))
    # print(get_category_train_size(dataset_path))
    # print(get_actionability_hint_train_size(dataset_path))
    dataset = pd.read_csv()