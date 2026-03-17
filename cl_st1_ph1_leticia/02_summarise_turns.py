#!/usr/bin/env python3
"""
02_summarise_turns.py

Loads selected BNC2014 Spoken conversation data from NDJSON files, builds
summary prompts around marked turns, submits them to GPT, and saves one
summary per marked turn.

Usage:
    python 02_summarise_turns.py \
        --model gpt-5.1 \
        --workers 4 \
        --test 10
"""

import argparse
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv


# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)


# ------------------------------------------------------------
# API (OpenAI SDK)
# ------------------------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Install with: conda install openai")
    sys.exit(1)


# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "corpus" / "01_bnc2014sp_dataset"
OUTPUT_DIR_DEFAULT = BASE_DIR / "corpus" / "03_summary"
PROMPT_PATH = BASE_DIR / "summary_gpt_prompt_model_v2.md"

SELECTED_TOP_TALKER_PATH = DATA_DIR / "bnc2014sp_conversation_selected_top_talker_94plus.ndjson"
SELECTED_PATH = DATA_DIR / "bnc2014sp_conversation_selected.ndjson"
HEADER_PATH = DATA_DIR / "bnc2014sp_header.ndjson"


# ------------------------------------------------------------
# CLI ARGUMENTS
# ------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize marked BNC2014 turns using GPT (OpenAI SDK / Responses API)."
    )
    parser.add_argument("--model", "-m", default="gpt-5.1", help="GPT model to use (default: gpt-5.1).")
    parser.add_argument("--max-output-tokens", "-t", type=int, default=3000, help="Maximum output tokens.")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers.")
    parser.add_argument(
        "--output",
        "-o",
        default=str(OUTPUT_DIR_DEFAULT),
        help=f"Folder to save GPT summaries (default: {OUTPUT_DIR_DEFAULT}).",
    )
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="If set, process only the first N marked turns (e.g., --test 10).",
    )
    return parser.parse_args()


# ------------------------------------------------------------
# I/O
# ------------------------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_ndjson(path: Path) -> pd.DataFrame:
    return pd.read_json(path, lines=True)


# ------------------------------------------------------------
# PROMPTS
# ------------------------------------------------------------
def parse_prompt_template(prompt_text: str) -> tuple[str, str]:
    system_match = re.search(
        r"# System Prompt\s*(.*?)\s*# User Prompt",
        prompt_text,
        flags=re.DOTALL,
    )
    user_match = re.search(
        r"# User Prompt\s*(.*)",
        prompt_text,
        flags=re.DOTALL,
    )

    if not system_match or not user_match:
        raise ValueError("Could not parse system/user prompts from summary_gpt_prompt_model_v2.md")

    system_prompt = system_match.group(1).strip()
    user_prompt_template = user_match.group(1).strip()
    return system_prompt, user_prompt_template


def safe_str(value: object, fallback: str = "Not available") -> str:
    if pd.isna(value) or value is None:
        return fallback
    value_str = str(value).strip()
    return value_str if value_str else fallback


def format_turn(turn_n: object, speaker_id: object, utterance: object, marked: bool = False) -> str:
    prefix = "→ " if marked else ""
    return f"{prefix}{safe_str(turn_n)} {safe_str(speaker_id)} {safe_str(utterance, fallback='')}"


def build_transcript_segment(
        target_row: pd.Series,
        conversation_turns: pd.DataFrame,
) -> str:
    target_turn_n = int(target_row["turn_n"])

    ordered_turns = conversation_turns.sort_values("turn_n").copy()

    preceding = ordered_turns[ordered_turns["turn_n"] < target_turn_n].tail(10)
    following = ordered_turns[ordered_turns["turn_n"] > target_turn_n].head(9)

    lines: list[str] = []

    for _, row in preceding.iterrows():
        lines.append(format_turn(row["turn_n"], row["speaker_id"], row["utterance"]))

    lines.append(
        format_turn(
            target_row["turn_n"],
            target_row["speaker_id"],
            target_row["utterance"],
            marked=True,
        )
    )

    for _, row in following.iterrows():
        lines.append(format_turn(row["turn_n"], row["speaker_id"], row["utterance"]))

    return "\n\n".join(lines)


def build_user_prompt(
        user_prompt_template: str,
        header_row: pd.Series,
        transcript_segment: str,
) -> str:
    replacements = {
        "<rec_year>": safe_str(header_row.get("rec_year")),
        "<n_speakers>": safe_str(header_row.get("n_speakers")),
        "<list_speakers>": safe_str(header_row.get("list_speakers")),
        "<rec_loc>": safe_str(header_row.get("rec_loc")),
        "<relationships>": safe_str(header_row.get("relationships")),
        "<topics>": safe_str(header_row.get("topics")),
        "<activity>": safe_str(header_row.get("activity")),
        "<conv_type>": safe_str(header_row.get("conv_type")),
    }

    prompt = user_prompt_template
    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    prompt = prompt.replace("→ <turn_n> <speaker_id> <utterance>", transcript_segment, 1)

    remaining_placeholder_pattern = r"\n\s*<turn_n> <speaker_id> <utterance>\s*"
    prompt = re.sub(remaining_placeholder_pattern, "", prompt)

    return prompt.strip()


# ------------------------------------------------------------
# OPENAI CALL (Responses API)
# ------------------------------------------------------------
def gpt_api_call_v2(
        client: OpenAI,
        model: str,
        system_prompt: str,
        user_prompt: str,
        max_output_tokens: int,
) -> str:
    """
    One request = one isolated context.

    We do NOT reuse any conversation/thread state. Each call provides only the
    system+user messages for that single document.
    """
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_output_tokens=max_output_tokens,
        temperature=0.0,
    )

    out = getattr(resp, "output_text", None)
    if not out:
        raise RuntimeError("API returned empty output.")
    return out


# ------------------------------------------------------------
# DATA PREPARATION
# ------------------------------------------------------------
def build_lookup_tables(
        df_selected: pd.DataFrame,
        df_header: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series]]:
    selected_by_text_id: dict[str, pd.DataFrame] = {
        text_id: group.sort_values("turn_n").reset_index(drop=True)
        for text_id, group in df_selected.groupby("text_id", sort=False)
    }

    header_by_text_id: dict[str, pd.Series] = {
        row["text_id"]: row
        for _, row in df_header.iterrows()
    }

    return selected_by_text_id, header_by_text_id


# ------------------------------------------------------------
# WORKER
# ------------------------------------------------------------
def process_turn(
        target_row: pd.Series,
        output_dir: Path,
        client: OpenAI,
        model: str,
        max_tokens: int,
        system_prompt: str,
        user_prompt_template: str,
        selected_by_text_id: dict[str, pd.DataFrame],
        header_by_text_id: dict[str, pd.Series],
) -> bool:
    try:
        text_id = safe_str(target_row["text_id"])
        turn_n = int(target_row["turn_n"])
        speaker_id = safe_str(target_row["speaker_id"])

        print(f"[WORKER] Processing: {text_id} turn {turn_n} speaker {speaker_id}")

        if text_id not in selected_by_text_id:
            raise KeyError(f"No selected conversation turns found for text_id={text_id}")

        if text_id not in header_by_text_id:
            raise KeyError(f"No header row found for text_id={text_id}")

        conversation_turns = selected_by_text_id[text_id]
        header_row = header_by_text_id[text_id]

        transcript_segment = build_transcript_segment(target_row, conversation_turns)
        user_prompt = build_user_prompt(user_prompt_template, header_row, transcript_segment)

        response = gpt_api_call_v2(
            client=client,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_output_tokens=max_tokens,
        )

        outname = f"{text_id}_{turn_n}_{speaker_id}_extracted_summarised.txt"
        write_text(output_dir / outname, response.strip())

        print(f"[WORKER] Saved → {outname}")
        return True

    except Exception as e:
        text_id = safe_str(target_row.get("text_id", "UNKNOWN"))
        turn_n = safe_str(target_row.get("turn_n", "UNKNOWN"))
        speaker_id = safe_str(target_row.get("speaker_id", "UNKNOWN"))
        print(f"[ERROR] {text_id} turn {turn_n} speaker {speaker_id}: {e}")
        return False


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main() -> int:
    args = parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_text = read_text(PROMPT_PATH)
    system_prompt, user_prompt_template = parse_prompt_template(prompt_text)

    df_selected_top_talker_94plus = load_ndjson(SELECTED_TOP_TALKER_PATH)
    df_selected = load_ndjson(SELECTED_PATH)
    df_header = load_ndjson(HEADER_PATH)

    if df_selected_top_talker_94plus.empty:
        print("No rows found in top-talker selected turns file.")
        return 0

    if args.test is not None:
        if args.test <= 0:
            print("Error: --test must be a positive integer.")
            return 1
        df_selected_top_talker_94plus = df_selected_top_talker_94plus.head(args.test).copy()
        print(f"[TEST MODE] Limiting to first {len(df_selected_top_talker_94plus)} marked turns.\n")

    selected_by_text_id, header_by_text_id = build_lookup_tables(df_selected, df_header)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        return 1

    client = OpenAI(api_key=api_key)

    print(f"Processing {len(df_selected_top_talker_94plus)} marked turns with {args.workers} workers...\n")

    rows = [row for _, row in df_selected_top_talker_94plus.iterrows()]

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                process_turn,
                row,
                output_dir,
                client,
                args.model,
                args.max_output_tokens,
                system_prompt,
                user_prompt_template,
                selected_by_text_id,
                header_by_text_id,
            )
            for row in rows
        ]
        for fut in as_completed(futures):
            fut.result()

    print("\nCompleted summarizing marked turns using GPT (OpenAI SDK / Responses API).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())