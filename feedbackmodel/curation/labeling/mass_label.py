import lmstudio as lms
import yaml
from pathlib import Path
import pandas as pd
from typing import List

ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = ROOT / "dataset" / "data" / "synthetic_feedback_dataset_train.tsv"
PROMPT_PATH = ROOT / "dataset" / "prompts" / "feedback_generate_prompt.yaml"
OUTPUT_PATH = ROOT / "dataset" / "data" / "synthetic_feedback_dataset_train_labeled.tsv"

MODEL_NAME = "qwen2.5-coder-14b-instruct-mlx"
BATCH_SIZE = 16


def load_prompt() -> str:
    with open(PROMPT_PATH, "r") as f:
        prompt_yaml = yaml.safe_load(f)
    return prompt_yaml["prompt"]


def batch_rows(df: pd.DataFrame, batch_size: int):
    for i in range(0, len(df), batch_size):
        yield df.iloc[i:i + batch_size]


def format_batch_for_prompt(batch: pd.DataFrame) -> str:
    lines = []
    for _, row in batch.iterrows():
        lines.append(f"{row.feedback_id}\t{row.feedback_text}")
    return "\n".join(lines)


def main():
    model = lms.llm(MODEL_NAME)
    base_prompt = load_prompt()

    df = pd.read_csv(DATA_PATH, sep="\t")

    all_outputs: List[str] = []

    for batch in batch_rows(df, BATCH_SIZE):
        batch_text = format_batch_for_prompt(batch)

        prompt = base_prompt.replace("{{INPUT_ROWS}}", batch_text)

        try:
            response = model.respond(
                prompt,
                temperature=0.2,
                max_tokens=2048,
            )
            all_outputs.append(response.strip())
        except Exception as e:
            print(f"Batch failed: {e}")
            continue

    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(all_outputs))


if __name__ == "__main__":
    main()
