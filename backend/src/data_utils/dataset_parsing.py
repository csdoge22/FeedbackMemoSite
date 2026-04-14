"""
The dataset generation utilities are responsible for creating a high-quality dataset for training the priority prediction model.
This involves four main steps: planning, generation, validation, and filtering.
"""

import json
import os
import re
from time import sleep
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from google import genai
from openai import OpenAI
from anthropic import Anthropic   # (kept for validation if needed later)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

load_dotenv()

# =========================
# PATH CONSTANTS
# =========================
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
PLAN_PATH = os.path.join(OUTPUT_DIR, "plan.json")
GENERATE_PATH = os.path.join(OUTPUT_DIR, "generate.json")
VALIDATION_PATH = os.path.join(OUTPUT_DIR, "validation.json")


# =========================
# JSON UTILITIES
# =========================
def extract_json(text: str) -> Any:
    if not isinstance(text, str):
        text = str(text)

    text = text.strip()

    code_fence = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S)
    if code_fence:
        text = code_fence.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for i in range(len(text)):
        if text[i] not in "[{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[i:])
            return obj
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON found in response")


# =========================
# CLIENT UTILITIES
# =========================
def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(base_url="http://localhost:1234/v1", api_key=api_key or "lm-studio")


# =========================
# PLANNING STAGE 🔥 CHANGED
# =========================
def plan_generation() -> dict:
    api_key = os.getenv("PLANNING_API_KEY")
    if not api_key:
        raise RuntimeError("PLANNING_API_KEY is not set")

    # 🔴 CHANGED: Claude → Gemini client
    client = genai.Client(api_key=api_key)

    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "planning.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt = f.read()

    # 🔴 CHANGED: Gemini 2.5 Flash instead of Claude Sonnet
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    # 🔴 CHANGED: Gemini response format
    return extract_json(response.text)


# =========================
# BATCH GENERATION (UNCHANGED)
# =========================
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    return OpenAI(base_url="http://localhost:1234/v1", api_key=api_key or "lm-studio")


def generate_batch(client: OpenAI, prompt: str, max_tokens: int) -> list[dict]:
    response = client.chat.completions.create(
        model="qwen/qwen2.5-coder-14b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )

    parsed = extract_json(response.choices[0].message.content)

    if not isinstance(parsed, list):
        raise ValueError("Batch must be a JSON list")

    return parsed


# =========================
# VALIDATION STAGE (UNCHANGED)
# =========================
def validate_batch(data_batch: list[dict]):
    print(os.getenv("VALIDATOR_API_KEY"))
    client = genai.Client(api_key=os.getenv("VALIDATOR_API_KEY"))

    with open(
        os.path.join(os.path.dirname(__file__), "prompts", "validating.txt"),
        "r",
        encoding="utf-8"
    ) as f:
        prompt_template = f.read()

    prompt = prompt_template.replace(
        "{GENERATED_ROWS}",
        json.dumps(data_batch, ensure_ascii=False)
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )

    return extract_json(response.text)

def generate_and_validate_dataset(planned_prompt: dict, batch_size: int = 20):
    client = get_openai_client()

    base_prompt = load_generation_prompt()

    total_rows = planned_prompt["total_rows"]

    dataset = []
    seen_texts = set()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    while len(dataset) < total_rows:
        remaining = total_rows - len(dataset)
        current_batch_size = min(batch_size, remaining)

        print(f"\n=== GENERATING ({len(dataset)}/{total_rows}) ===")

        # 1. GENERATE
        prompt = build_generation_prompt(
            base_prompt,
            planned_prompt,
            current_batch_size,
            dataset
        )

        batch = generate_batch(
            client,
            prompt,
            max_tokens=min(4000, current_batch_size * 150)
        )

        batch = deduplicate_batch(batch, seen_texts)

        if not batch:
            continue

        # 2. VALIDATE (immediately after generation)
        print(f"VALIDATING batch of size {len(batch)}")

        validation_result = validate_batch(batch)

        accepted_indices = set(validation_result.get("accepted", []))
        rejected_info = validation_result.get("rejected", [])

        # 3. FILTER
        accepted_rows = []
        for i, row in enumerate(batch):
            if i in accepted_indices:
                accepted_rows.append(row)

        # 4. UPDATE GLOBAL DATASET
        dataset.extend(accepted_rows)

        # 5. SAVE PROGRESS
        save_json_files(GENERATE_PATH, dataset)

        print(f"Accepted {len(accepted_rows)} rows | Total: {len(dataset)}")

    return dataset

# =========================
# MAIN GENERATION PIPELINE (UNCHANGED)
# =========================
def generate_dataset(planned_prompt: dict, batch_size: int = 20) -> list[dict]:
    client = get_openai_client()

    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "generation.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        base_prompt = f.read()

    total_rows = planned_prompt["total_rows"]

    dataset: list[dict] = []
    seen_texts: set[str] = set()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    while len(dataset) < total_rows:
        remaining = total_rows - len(dataset)
        current_batch_size = min(batch_size, remaining)

        print(f"Generating batch... ({len(dataset)}/{total_rows})")

        prompt = base_prompt.replace("{PLAN_JSON}", json.dumps(planned_prompt))
        prompt = prompt.replace("{BATCH_SIZE}", str(current_batch_size))

        try:
            batch = generate_batch(
                client,
                prompt,
                max_tokens=min(4000, current_batch_size * 150),
            )
        except Exception as exc:
            print(f"Batch failed: {exc}")
            continue

        cleaned = [r for r in batch if r.get("text") and r["text"] not in seen_texts]

        for r in cleaned:
            seen_texts.add(r["text"])

        dataset.extend(cleaned)

    return dataset


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    def save_json_file(path: str, data: Any) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_json_file(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # =========================
    # 1. PLANNING STAGE
    # =========================
    if os.path.exists(PLAN_PATH):
        print("Plan already exists — skipping.")
        plan = load_json_file(PLAN_PATH)
    else:
        print("Generating plan...")
        plan = plan_generation()
        save_json_file(PLAN_PATH, plan)

    print("\n=== PLAN LOADED ===")
    print(json.dumps(plan, indent=2))

    # =========================
    # 2. GENERATION + VALIDATION PIPELINE (NEW CORE LOOP)
    # =========================

    # IMPORTANT CHANGE:
    # Instead of separate generation + validation phases,
    # we now run a unified streaming pipeline per batch.

    final_dataset = []

    if os.path.exists(GENERATE_PATH):
        print("\nDataset already exists — loading...")
        final_dataset = load_json_file(GENERATE_PATH)
    else:
        print("\nStarting streaming generation + validation pipeline...")

        final_dataset = generate_and_validate_dataset(
            planned_prompt=plan,
            batch_size=20
        )

        save_json_file(GENERATE_PATH, final_dataset)

    print(f"\n=== DATASET SIZE: {len(final_dataset)} ===")

    # =========================
    # 3. VALIDATION OUTPUT (OPTIONAL AUDIT FILE)
    # =========================
    # Even though validation already happened inline,
    # you can still run a summary audit if needed.

    if not os.path.exists(VALIDATION_PATH):
        print("\nCreating validation audit file...")

        validation_summary = {
            "total_rows": len(final_dataset),
            "status": "validated_inline",
            "note": "validation already applied per batch during generation"
        }

        save_json_file(VALIDATION_PATH, validation_summary)

    print("\n=== PIPELINE COMPLETE ===")


if __name__ == "__main__":
    main()