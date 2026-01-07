import os
import sys
import yaml
import lmstudio as lms
import argparse
from time import sleep
from typing import List, Dict
import csv
from collections import defaultdict
import random

PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "feedback_generate_prompt.yaml"
)

EXPECTED_COLUMNS = [
    "feedback_id",
    "feedback_text",
    "category",
    "source_context",
    "actionability_hint",
]

# Hard canonical sets to enforce allowed values
CATEGORY_SET = {"growth", "team", "skill", "subject", "productivity", "communication"}
SOURCE_SET = {"peer_review", "manager_feedback", "self_reflection", "course_feedback"}
ACTIONABILITY_SET = {"actionable", "partially_actionable", "descriptive_only"}

# Optional mapping to fix minor deviations
CATEGORY_MAP = {"learning": "growth", "design": "subject"}
ACTIONABILITY_MAP = {"partially_action": "partially_actionable", "action": "actionable"}

def load_prompt(num_rows: int) -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt.replace("N", str(num_rows))

# -----------------------------
# LM Studio generation
# -----------------------------
def generate_raw(model_name: str, prompt: str) -> str:
    model = lms.llm(model_name)
    print("\n--- Streaming model output ---\n", flush=True)
    chunks: List[str] = []
    try:
        with model.respond_stream(prompt) as stream:
            for frag in stream:
                text = getattr(frag, "content", "")
                print(text, end="", flush=True)
                chunks.append(text)
            result = stream.result()
    except Exception:
        print("\n[stream failed, falling back to respond()]\n", file=sys.stderr)
        result = model.respond(prompt)
        chunks.append(result.content)
    print("\n--- End of generation ---\n", flush=True)
    return "".join(chunks)

def extract_tsv_block(text: str) -> List[str]:
    lines = text.splitlines()
    header_line = "\t".join(EXPECTED_COLUMNS)
    for i, line in enumerate(lines):
        if line.strip() == header_line:
            return lines[i:]
    raise ValueError("TSV header not found in model output.")

def parse_rows(lines: List[str]) -> List[List[str]]:
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) != 5:
            continue
        rows.append(cols)
    return rows

# -----------------------------
# Normalization / Validation
# -----------------------------
def normalize_and_repair(rows: List[List[str]]) -> List[List[str]]:
    cleaned = []
    for row in rows:
        _, text, cat, src, hint = row

        # Enforce ASCII only
        text_ascii = text.encode("ascii", "ignore").decode("ascii")

        # Map to canonical allowed values
        cat_fixed = CATEGORY_MAP.get(cat, cat)
        hint_fixed = ACTIONABILITY_MAP.get(hint, hint)

        if cat_fixed not in CATEGORY_SET:
            continue
        if src not in SOURCE_SET:
            continue
        if hint_fixed not in ACTIONABILITY_SET:
            continue

        cleaned.append([text_ascii, cat_fixed, src, hint_fixed])
    return cleaned

def reindex_rows(rows: List[List[str]]) -> List[List[str]]:
    """Assign feedback_id sequentially starting from 0"""
    return [[str(i)] + r for i, r in enumerate(rows)]

def assemble_tsv(rows: List[List[str]]) -> str:
    lines = ["\t".join(EXPECTED_COLUMNS)]
    for r in rows:
        lines.append("\t".join(r))
    return "\n".join(lines) + "\n"

# -----------------------------
# Batched generation
# -----------------------------
def generate_dataset(model: str, total_rows: int, batch_size: int, retries: int) -> str:
    collected: List[List[str]] = []
    while len(collected) < total_rows:
        need = min(batch_size, total_rows - len(collected))
        prompt = load_prompt(need)
        for attempt in range(retries):
            raw = generate_raw(model, prompt)
            try:
                tsv_lines = extract_tsv_block(raw)
                rows = parse_rows(tsv_lines)
                if rows:
                    cleaned = normalize_and_repair(rows)
                    collected.extend(cleaned)
                    break
            except Exception:
                pass
            sleep(0.5)
        else:
            raise RuntimeError("Failed to collect sufficient valid rows.")
    # Ensure we have enough rows
    if len(collected) < total_rows:
        raise RuntimeError(f"Not enough valid rows after normalization: {len(collected)} < {total_rows}")
    selected = collected[:total_rows]
    selected = reindex_rows(selected)
    return assemble_tsv(selected)

# -----------------------------
# Dataset split
# -----------------------------
def split_dataset(tsv_path: str, train_ratio: float = 0.8, test_ratio: float = 0.1, stop_ratio: float = 0.1):
    """Split the TSV into train/test/stop sets, stratified by composite key"""
    if abs(train_ratio + test_ratio + stop_ratio - 1.0) > 1e-6:
        raise ValueError("Ratios must sum to 1.")
    
    # Read TSV
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        headers = reader.fieldnames

    # Build composite key
    for r in rows:
        r["_key"] = f"{r['category']}|{r['source_context']}|{r['actionability_hint']}"

    # Group rows by key
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["_key"]].append(r)

    train_rows, test_rows, stop_rows = [], [], []

    random.seed(42)
    for group_rows in grouped.values():
        random.shuffle(group_rows)
        n = len(group_rows)
        n_train = int(round(n * train_ratio))
        n_test = int(round(n * test_ratio))
        n_stop = n - n_train - n_test
        train_rows.extend(group_rows[:n_train])
        test_rows.extend(group_rows[n_train:n_train+n_test])
        stop_rows.extend(group_rows[n_train+n_test:])

    # Save files (overwrite if exist)
    base = os.path.splitext(tsv_path)[0]
    for name, data in [("train", train_rows), ("test", test_rows), ("stop", stop_rows)]:
        out_path = f"{base}_{name}.tsv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
            writer.writeheader()
            writer.writerows(data)
        print(f"Saved {len(data)} rows to {out_path}")

# -----------------------------
# Main
# -----------------------------
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--tsv-path", type=str, defalt="./dataset/synthetic_feedback_dataset.tsv")
#     # parser.add_argument("-n", "--num", type=int, default=500)
#     # parser.add_argument("-m", "--model", type=str, default="qwen/qwen3-14b")
#     # parser.add_argument("--batch-size", type=int, default=200)
#     # parser.add_argument("--retries", type=int, default=3)
#     # parser.add_argument("--api-host", type=str, default=os.environ.get("LMSTUDIO_API_HOST"))
#     parser.add_argument("--train-ratio", type=float, default=0.8)
#     parser.add_argument("--test-ratio", type=float, default=0.1)
#     parser.add_argument("--stop-ratio", type=float, default=0.1)
#     args = parser.parse_args()

#     # if args.api_host:
#     #     lms.configure_default_client(args.api_host)

#     out_dir = "./dataset"
#     # os.makedirs(out_dir, exist_ok=True)
#     out_path = os.path.join(out_dir, "synthetic_feedback_dataset.tsv")

#     # tsv = generate_dataset(
#     #     model=args.model,
#     #     total_rows=args.num,
#     #     batch_size=args.batch_size,
#     #     retries=args.retries
#     # )

#     # with open(out_path, "w", encoding="utf-8") as f:
#     #     f.write(tsv)
#     # print("\nDataset generated successfully:", out_path)

#     # Split the dataset immediately after normalization
#     split_dataset(
#         tsv_path=args.tsv_path,
#         train_ratio=args.train_ratio,
#         test_ratio=args.test_ratio,
#         stop_ratio=args.stop_ratio
#     )

if __name__ == "__main__":
    import csv
    import os
    import sys
    import random
    from collections import defaultdict
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tsv-path", type=str, default="./dataset/synthetic_feedback_dataset.tsv",
                        help="Path to existing dataset TSV")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--stop-ratio", type=float, default=0.1)
    parser.add_argument("--repair-mode", type=str, default="drop", choices=["drop", "remap"],
                        help="What to do with invalid rows: drop them or remap to safe defaults")
    args = parser.parse_args()

    if not os.path.exists(args.tsv_path):
        print(f"Error: TSV file not found at {args.tsv_path}")
        sys.exit(1)

    # -----------------------------
    # Load dataset
    # -----------------------------
    with open(args.tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        rows = list(reader)
        headers = reader.fieldnames

    total_rows = len(rows)

    # -----------------------------
    # Normalize text, canonicalize columns, reindex feedback_id
    # -----------------------------
    removed_count = 0
    bad_rows = []

    # print distributions BEFORE normalization
    from collections import Counter
    before_cat = Counter([r.get("category", "").strip() for r in rows])
    before_src = Counter([r.get("source_context", "").strip() for r in rows])
    before_hint = Counter([r.get("actionability_hint", "").strip() for r in rows])
    print("Before normalization counts (category):", dict(before_cat))
    print("Before normalization counts (source_context):", dict(before_src))
    print("Before normalization counts (actionability_hint):", dict(before_hint))

    normalized_rows = []
    for i, row in enumerate(rows):
        # normalize feedback_text
        text = row.get("feedback_text", "")
        safe_text = text.encode("ascii", "ignore").decode("ascii").replace("\t", " ").replace("\n", " ")
        row["feedback_text"] = safe_text

        # canonicalize categorical fields
        cat = row.get("category", "").strip().lower()
        src = row.get("source_context", "").strip().lower()
        hint = row.get("actionability_hint", "").strip().lower()

        # apply known mappings
        cat = CATEGORY_MAP.get(cat, cat)
        hint = ACTIONABILITY_MAP.get(hint, hint)

        # normalize underscores/spaces
        cat = cat.replace(" ", "_")
        hint = hint.replace(" ", "_")
        src = src.replace(" ", "_")

        # repair or drop invalid rows
        if cat not in CATEGORY_SET or src not in SOURCE_SET or hint not in ACTIONABILITY_SET:
            if args.repair_mode == "drop":
                removed_count += 1
                bad_rows.append(row)
                continue
            elif args.repair_mode == "remap":
                if cat not in CATEGORY_SET:
                    cat = "subject"
                if src not in SOURCE_SET:
                    src = "self_reflection"
                if hint not in ACTIONABILITY_SET:
                    hint = "partially_actionable"

        row["category"] = cat
        row["source_context"] = src
        row["actionability_hint"] = hint

        row["feedback_id"] = str(len(normalized_rows))  # sequential ID
        normalized_rows.append(row)

    print(f"Removed or remapped {removed_count} invalid rows. Kept {len(normalized_rows)} valid rows.")
    rows = normalized_rows
    total_rows = len(rows)

    # write bad rows for inspection
    if removed_count > 0:
        bad_path = os.path.splitext(args.tsv_path)[0] + "_bad_rows.tsv"
        with open(bad_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
            writer.writeheader()
            writer.writerows(bad_rows)
        print(f"Saved {removed_count} invalid rows to {bad_path}")

    # -----------------------------
    # Overwrite main TSV with cleaned dataset
    # -----------------------------
    with open(args.tsv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Main dataset TSV updated with normalized text, canonicalized columns, and reindexed IDs: {args.tsv_path}")

    # -----------------------------
    # Delete old split files if they exist
    # -----------------------------
    base = os.path.splitext(args.tsv_path)[0]
    for split_name in ["train", "test", "stop"]:
        split_file = f"{base}_{split_name}.tsv"
        if os.path.exists(split_file):
            os.remove(split_file)

    # -----------------------------
    # Stratify by composite key and split
    # -----------------------------
    groups = defaultdict(list)
    for row in rows:
        key = f"{row['category']}|{row['source_context']}|{row['actionability_hint']}"
        groups[key].append(row)

    train_rows, test_rows, stop_rows = [], [], []
    random.seed(42)

    for items in groups.values():
        random.shuffle(items)
        n = len(items)
        n_train = int(round(n * args.train_ratio))
        n_test = int(round(n * args.test_ratio))
        n_stop = n - n_train - n_test

        train_rows.extend(items[:n_train])
        test_rows.extend(items[n_train:n_train+n_test])
        stop_rows.extend(items[n_train+n_test:])

    # Shuffle each split
    random.shuffle(train_rows)
    random.shuffle(test_rows)
    random.shuffle(stop_rows)

    # -----------------------------
    # Save splits
    # -----------------------------
    def save_split(split_rows, split_name):
        out_path = f"{base}_{split_name}.tsv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter="\t")
            writer.writeheader()
            writer.writerows(split_rows)
        print(f"Saved {len(split_rows)} rows to {out_path}")

    save_split(train_rows, "train")
    save_split(test_rows, "test")
    save_split(stop_rows, "stop")

    print("\nDataset fully normalized, canonicalized, reindexed, and stratified into train/test/stop successfully.")
