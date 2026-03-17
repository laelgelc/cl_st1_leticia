#!/usr/bin/env python3
"""
04_generate_human.py

Load the top-talker selected turns, assign a file_id to each row, write a
file index, overwrite the NDJSON with the updated DataFrame, and export each
utterance as a human text file.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "corpus" / "01_bnc2014sp_dataset"
HUMAN_DIR = BASE_DIR / "corpus" / "05_human"

INPUT_PATH = DATA_DIR / "bnc2014sp_conversation_selected_top_talker_94plus.ndjson"
FILE_INDEX_PATH = BASE_DIR / "file_index.txt"


def load_ndjson(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_json(path, lines=True)


def save_ndjson(df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", lines=True, force_ascii=False)


def safe_str(value: object, fallback: str = "") -> str:
    if value is None or pd.isna(value):
        return fallback
    return str(value)


def main() -> int:
    df_selected_top_talker_94plus = load_ndjson(INPUT_PATH)

    file_ids = [f"t{i:06d}" for i in range(1, len(df_selected_top_talker_94plus) + 1)]
    df_selected_top_talker_94plus.insert(0, "file_id", file_ids)

    file_index_lines: list[str] = []
    HUMAN_DIR.mkdir(parents=True, exist_ok=True)

    for _, row in df_selected_top_talker_94plus.iterrows():
        file_id = safe_str(row["file_id"])
        text_id = safe_str(row.get("text_id"))
        turn_n = safe_str(row.get("turn_n"))
        speaker_id = safe_str(row.get("speaker_id"))
        utterance = safe_str(row.get("utterance"))

        file_index_lines.append(f"{file_id} {text_id}_{turn_n}_{speaker_id}")

        human_path = HUMAN_DIR / f"{file_id}_human.txt"
        human_path.write_text(utterance, encoding="utf-8")

    FILE_INDEX_PATH.write_text("\n".join(file_index_lines) + "\n", encoding="utf-8")

    save_ndjson(df_selected_top_talker_94plus, INPUT_PATH)

    print(f"Loaded {len(df_selected_top_talker_94plus)} rows from {INPUT_PATH}")
    print(f"Wrote file index to {FILE_INDEX_PATH}")
    print(f"Overwrote NDJSON at {INPUT_PATH}")
    print(f"Saved human text files to {HUMAN_DIR}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())