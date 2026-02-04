import os
import sys
import csv
import yaml
import json
import random
import argparse
from time import sleep
from typing import List, Dict, Set
from collections import defaultdict

import lmstudio as lms

# -----------------------------
# Constants
# -----------------------------

PROMPT_DIR = os.path.join(os.path.dirname(__file__), "..", "prompts")
PROMPT_FILES = [
    "feedback_generate_prompt.yaml",           # Base
    "feedback_generate_prompt_variant_A.yaml", # Variant A
    "feedback_generate_prompt_variant_B.yaml", # Variant B
]

EXPECTED_COLUMNS = [
    "feedback_id",
    "feedback_text",
    "category",
    "source_context",
    "actionability_hint",
]

CATEGORY_SET = {"growth", "team", "skill", "subject", "productivity", "communication"}
SOURCE_SET = {"peer_review", "manager_feedback", "self_reflection", "course_feedback"}
ACTIONABILITY_SET = {"actionable", "partially_actionable", "descriptive_only"}

CATEGORY_MAP = {"learning": "growth", "design": "subject"}
ACTIONABILITY_MAP = {
    "partially_action": "partially_actionable",
    "action": "actionable",
}

# -----------------------------
# Prompt loading with rotation
# -----------------------------

def load_prompt(num_rows: int, batch_index: int) -> str:
    """
    Rotates between prompt variants for each batch.
    """
    prompt_file = PROMPT_FILES[batch_index % len(PROMPT_FILES)]
    prompt_path = os.path.join(PROMPT_DIR, prompt_file)
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt.replace("N", str(num_rows))

# -----------------------------
# LM Studio generation (JSON)
# -----------------------------

def generate_raw(model_name: str, prompt: str) -> str:
    model = lms.llm(model_name)
    result = model.respond(prompt)
    return result.content

# -----------------------------
# JSON extraction + parsing
# -----------------------------

def extract_json_block(text: str) -> List[Dict]:
    """
    Extract the first valid JSON array from model output.
    """
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON array not found in output.")
    return json.loads(text[start : end + 1])

# -----------------------------
# Normalization
# -----------------------------

def normalize_and_repair(rows: List[Dict]) -> List[List[str]]:
    cleaned = []

    for r in rows:
        try:
            text = r["feedback_text"].encode("ascii", "ignore").decode("ascii")
            cat = CATEGORY_MAP.get(r["category"].lower(), r["category"].lower())
            src = r["source_context"].lower()
            hint = ACTIONABILITY_MAP.get(
                r["actionability_hint"].lower(),
                r["actionability_hint"].lower(),
            )

            if (
                cat in CATEGORY_SET
                and src in SOURCE_SET
                and hint in ACTIONABILITY_SET
            ):
                cleaned.append([text, cat, src, hint])
        except Exception:
            continue

    return cleaned

def reindex(rows: List[List[str]]) -> List[List[str]]:
    return [[str(i)] + r for i, r in enumerate(rows)]

# -----------------------------
# Dataset generation with prompt rotation and uniqueness
# -----------------------------

def generate_dataset(
    model: str,
    total_rows: int,
    batch_size: int,
    retries: int,
) -> List[List[str]]:
    collected: List[List[str]] = []
    seen_texts: Set[str] = set()
    batch_index = 0

    while len(collected) < total_rows:
        need = min(batch_size, total_rows - len(collected))
        prompt = load_prompt(need, batch_index)
        batch_index += 1  # rotate prompt for next batch

        for _ in range(retries):
            raw = generate_raw(model, prompt)
            try:
                parsed = extract_json_block(raw)
                cleaned = normalize_and_repair(parsed)

                # Uniqueness enforcement
                unique_cleaned = []
                for row in cleaned:
                    if row[0] not in seen_texts:
                        seen_texts.add(row[0])
                        unique_cleaned.append(row)

                if unique_cleaned:
                    collected.extend(unique_cleaned)
                    break
            except Exception:
                sleep(0.5)
        else:
            raise RuntimeError("Generation failed after retries.")

    return reindex(collected[:total_rows])

# -----------------------------
# Dataset IO
# -----------------------------

def write_tsv(rows: List[List[str]], path: str):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(EXPECTED_COLUMNS)
        writer.writerows(rows)

def load_tsv(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))

# -----------------------------
# Dataset splitting
# -----------------------------

def split_dataset(
    rows: List[dict],
    train_ratio: float,
    test_ratio: float,
    stop_ratio: float,
):
    groups = defaultdict(list)
    for r in rows:
        key = f"{r['category']}|{r['source_context']}|{r['actionability_hint']}"
        groups[key].append(r)

    train, test, stop = [], [], []
    random.seed(42)

    for items in groups.values():
        random.shuffle(items)
        n = len(items)
        n_train = int(n * train_ratio)
        n_test = int(n * test_ratio)

        train.extend(items[:n_train])
        test.extend(items[n_train : n_train + n_test])
        stop.extend(items[n_train + n_test :])

    return train, test, stop

# -----------------------------
# Main
# -----------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["generate", "split"], required=True)

    parser.add_argument("--model", type=str, default="qwen2.5-coder-14b-instruct-mlx")
    parser.add_argument("--num", type=int, default=500)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--retries", type=int, default=3)

    parser.add_argument("--tsv-path", type=str, default="./dataset/synthetic_feedback_dataset.tsv")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--stop-ratio", type=float, default=0.1)

    args = parser.parse_args()

    if args.mode == "generate":
        rows = generate_dataset(
            model=args.model,
            total_rows=args.num,
            batch_size=args.batch_size,
            retries=args.retries,
        )
        os.makedirs(os.path.dirname(args.tsv_path), exist_ok=True)
        write_tsv(rows, args.tsv_path)
        print(f"Generated dataset: {args.tsv_path}")

    elif args.mode == "split":
        rows = load_tsv(args.tsv_path)
        train, test, stop = split_dataset(
            rows,
            args.train_ratio,
            args.test_ratio,
            args.stop_ratio,
        )

        base = os.path.splitext(args.tsv_path)[0]
        for name, data in [("train", train), ("test", test), ("stop", stop)]:
            out = f"{base}_{name}.tsv"
            with open(out, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=EXPECTED_COLUMNS,
                    delimiter="\t",
                )
                writer.writeheader()
                writer.writerows(data)
            print(f"Saved {len(data)} rows → {out}")

if __name__ == "__main__":
    main()
