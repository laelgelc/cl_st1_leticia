#!/usr/bin/env python3
"""
03_build_prompts_profiled.py

Build profiled GPT prompt Markdown files from BNC2014 Spoken NDJSON data.

For each marked turn in:
    corpus/01_bnc2014sp_dataset/bnc2014sp_conversation_selected_top_talker_94plus.ndjson

this script:
- loads the relevant selected-turn, conversation, header, and speaker metadata
- reads the corresponding turn summary from corpus/03_summary/
- fills profiled_gpt_prompt_model_v2.md
- saves one Markdown prompt per marked turn to corpus/04_prompt_profiled/

Usage:
    python 03_build_prompts_profiled.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "corpus" / "01_bnc2014sp_dataset"
SUMMARY_DIR = BASE_DIR / "corpus" / "03_summary"
OUTPUT_DIR = BASE_DIR / "corpus" / "04_prompt_profiled"
PROMPT_MODEL_PATH = BASE_DIR / "profiled_gpt_prompt_model_v2.md"

SELECTED_TOP_TALKER_PATH = DATA_DIR / "bnc2014sp_conversation_selected_top_talker_94plus.ndjson"
SELECTED_PATH = DATA_DIR / "bnc2014sp_conversation_selected.ndjson"
HEADER_PATH = DATA_DIR / "bnc2014sp_header.ndjson"
SPEAKER_INFO_PATH = DATA_DIR / "bnc2014sp_speaker_info_occurrences.ndjson"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build profiled prompt markdown files.")
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="If set, process only the first N marked turns.",
    )
    return parser.parse_args()


def load_ndjson(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return pd.read_json(path, lines=True)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing text file: {path}")
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def safe_str(value: object, fallback: str = "Not available") -> str:
    if value is None or pd.isna(value):
        return fallback
    text = str(value).strip()
    return text if text else fallback


def format_gender(value: object) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    value_str = str(value).strip()
    if value_str == "M":
        return "Male"
    if value_str == "F":
        return "Female"
    return "Other"


def pick_first_available(row: pd.Series, candidates: list[str]) -> object:
    for col in candidates:
        if col in row.index:
            val = row[col]
            if val is not None and not pd.isna(val) and str(val).strip():
                return val
    return None


def format_turn(turn_n: object, speaker_id: object, utterance: object, marked: bool = False) -> str:
    prefix = "→ " if marked else ""
    return f"{prefix}{safe_str(turn_n)} {safe_str(speaker_id)} {safe_str(utterance, fallback='')}"


def parse_prompt_template(prompt_text: str) -> str:
    required_sections = [
        "## Your speaker socio-demographic profile",
        "### NS-SEC table (National Statistics Socio-economic Classification)",
        "## Conversation context",
        "## Conversation transcript segment",
    ]
    for section in required_sections:
        if section not in prompt_text:
            raise ValueError(f"Missing required template section: {section}")
    return prompt_text.strip()


def compute_length_band(utterance_word_count: object) -> str:
    try:
        count = int(float(utterance_word_count))
    except Exception:
        return "- Length: Not available words."

    low = round(count * 0.8)
    high = round(count * 1.2)
    return f"- Length: {low}–{high} words."


def build_speaker_profile(target_row: pd.Series, speaker_info_df: pd.DataFrame) -> str:
    speaker_id = safe_str(target_row.get("speaker_id"))
    speaker_rows = speaker_info_df[speaker_info_df["speaker_id"].astype(str) == speaker_id]
    speaker_row = speaker_rows.iloc[0] if not speaker_rows.empty else pd.Series(dtype=object)

    return "\n".join(
        [
            f"- Speaker ID: {speaker_id}",
            f"- Age: {safe_str(pick_first_available(speaker_row, ['exactage']))}",
            f"- Gender: {format_gender(pick_first_available(speaker_row, ['gender']))}",
            f"- Nationality: {safe_str(pick_first_available(speaker_row, ['nat']))}",
            f"- Birthplace: {safe_str(pick_first_available(speaker_row, ['birthplace']))}",
            f"- Birth country: {safe_str(pick_first_available(speaker_row, ['birthcountry']))}",
            f"- Language: {safe_str(pick_first_available(speaker_row, ['l1']))}",
            f"- Language origin: {safe_str(pick_first_available(speaker_row, ['lingorig']))}",
            f"- City of residence: {safe_str(pick_first_available(speaker_row, ['hab_city']))}",
            f"- Country of residence: {safe_str(pick_first_available(speaker_row, ['hab_country']))}",
            f"- Occupation: {safe_str(pick_first_available(speaker_row, ['occupation']))}",
            f"- Socio-economic status (refer to the NS-SEC table): {safe_str(pick_first_available(speaker_row, ['nssec']))}",
        ]
    )


def build_conversation_context(header_row: pd.Series) -> str:
    return "\n".join(
        [
            f"- Year: {safe_str(header_row.get('rec_year'))}",
            f"- Number of speakers: {safe_str(header_row.get('n_speakers'))}",
            f"- Speaker IDs: {safe_str(header_row.get('list_speakers'))}",
            f"- Location: {safe_str(header_row.get('rec_loc'))}",
            f"- Relationships: {safe_str(header_row.get('relationships'))}",
            f"- Topics: {safe_str(header_row.get('topics'))}",
            f"- Activity: {safe_str(header_row.get('activity'))}",
            f"- Conversation type: {safe_str(header_row.get('conv_type'))}",
        ]
    )


def build_transcript_segment(
        target_row: pd.Series,
        conversation_turns: pd.DataFrame,
        summary_text: str,
) -> str:
    target_turn_n = int(target_row["turn_n"])
    ordered_turns = conversation_turns.sort_values("turn_n").copy()

    preceding = ordered_turns[ordered_turns["turn_n"] < target_turn_n].tail(10)
    following = ordered_turns[ordered_turns["turn_n"] > target_turn_n].head(9)

    lines: list[str] = []

    for _, row in preceding.iterrows():
        lines.append(format_turn(row["turn_n"], row["speaker_id"], row["utterance"]))

    lines.append(f"→ {safe_str(target_row['turn_n'])} {safe_str(target_row['speaker_id'])} {summary_text}")

    for _, row in following.iterrows():
        lines.append(format_turn(row["turn_n"], row["speaker_id"], row["utterance"]))

    return "\n\n".join(lines)


def build_prompt_markdown(
        template_text: str,
        target_row: pd.Series,
        speaker_profile: str,
        conversation_context: str,
        transcript_segment: str,
) -> str:
    prompt = template_text

    prompt = prompt.replace(
        "- Length: <+/-20% band (rounded) of <utterance_word_count>> words.",
        compute_length_band(target_row.get("utterance_word_count")),
    )

    replacements = {
        "<speaker_id>": safe_str(target_row.get("speaker_id")),
        "<exactage>": safe_str(target_row.get("exactage")),
        '<"Male" if <gender>=="M", "Female" if <gender>=="F", "Other" if <gender>=="n/a (multiple)">': format_gender(
            target_row.get("gender")
        ),
        "<nat>": safe_str(target_row.get("nat")),
        "<birthplace>": safe_str(target_row.get("birthplace")),
        "<birthcountry>": safe_str(target_row.get("birthcountry")),
        "<l1>": safe_str(target_row.get("l1")),
        "<lingorig>": safe_str(target_row.get("lingorig")),
        "<hab_city>": safe_str(target_row.get("hab_city")),
        "<hab_country>": safe_str(target_row.get("hab_country")),
        "<occupation>": safe_str(target_row.get("occupation")),
        "<nssec>": safe_str(target_row.get("nssec")),
        "<rec_year>": safe_str(target_row.get("rec_year")),
        "<n_speakers>": safe_str(target_row.get("n_speakers")),
        "<list_speakers>": safe_str(target_row.get("list_speakers")),
        "<rec_loc>": safe_str(target_row.get("rec_loc")),
        "<relationships>": safe_str(target_row.get("relationships")),
        "<topics>": safe_str(target_row.get("topics")),
        "<activity>": safe_str(target_row.get("activity")),
        "<conv_type>": safe_str(target_row.get("conv_type")),
        "<utterance_word_count>": safe_str(target_row.get("utterance_word_count")),
    }

    for placeholder, value in replacements.items():
        prompt = prompt.replace(placeholder, value)

    prompt = re.sub(
        r"## Your speaker socio-demographic profile\s*.*?(?=### NS-SEC table)",
        f"## Your speaker socio-demographic profile\n\n{speaker_profile}\n\n",
        prompt,
        flags=re.DOTALL,
    )

    prompt = re.sub(
        r"## Conversation context\s*.*?(?=## Conversation transcript segment)",
        f"## Conversation context\n\n{conversation_context}\n\n",
        prompt,
        flags=re.DOTALL,
    )

    prompt = re.sub(
        r"## Conversation transcript segment\s*.*\Z",
        f"## Conversation transcript segment\n\n{transcript_segment}\n",
        prompt,
        flags=re.DOTALL,
    )

    return prompt.strip() + "\n"


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    template_text = parse_prompt_template(read_text(PROMPT_MODEL_PATH))

    df_selected_top_talker_94plus = load_ndjson(SELECTED_TOP_TALKER_PATH)
    df_selected = load_ndjson(SELECTED_PATH)
    df_header = load_ndjson(HEADER_PATH)
    df_speaker_info = load_ndjson(SPEAKER_INFO_PATH)

    required_selected_cols = {"text_id", "turn_n", "speaker_id", "utterance", "utterance_word_count"}
    missing_selected = required_selected_cols - set(df_selected_top_talker_94plus.columns)
    if missing_selected:
        raise ValueError(f"Missing required columns in selected top-talker file: {sorted(missing_selected)}")

    if args.test is not None:
        if args.test <= 0:
            raise ValueError("--test must be a positive integer")
        df_selected_top_talker_94plus = df_selected_top_talker_94plus.head(args.test).copy()

    header_by_text_id = {
        str(row["text_id"]): row
        for _, row in df_header.iterrows()
        if not pd.isna(row.get("text_id"))
    }

    turns_by_text_id = {
        str(text_id): group.sort_values("turn_n").reset_index(drop=True)
        for text_id, group in df_selected.groupby("text_id", sort=False)
        if not pd.isna(text_id)
    }

    processed = 0
    for _, target_row in df_selected_top_talker_94plus.iterrows():
        text_id = safe_str(target_row.get("text_id"))
        turn_n = safe_str(target_row.get("turn_n"))
        speaker_id = safe_str(target_row.get("speaker_id"))

        if text_id not in header_by_text_id:
            raise KeyError(f"Missing header row for text_id={text_id}")
        if text_id not in turns_by_text_id:
            raise KeyError(f"Missing selected turns for text_id={text_id}")

        summary_path = SUMMARY_DIR / f"{text_id}_{turn_n}_{speaker_id}_extracted_summarised.txt"
        summary_text = read_text(summary_path).strip()

        speaker_profile = build_speaker_profile(target_row, df_speaker_info)
        conversation_context = build_conversation_context(header_by_text_id[text_id])
        transcript_segment = build_transcript_segment(
            target_row=target_row,
            conversation_turns=turns_by_text_id[text_id],
            summary_text=summary_text,
        )

        prompt_markdown = build_prompt_markdown(
            template_text=template_text,
            target_row=target_row,
            speaker_profile=speaker_profile,
            conversation_context=conversation_context,
            transcript_segment=transcript_segment,
        )

        output_path = OUTPUT_DIR / f"{text_id}_{turn_n}_{speaker_id}_prompt_profiled.md"
        write_text(output_path, prompt_markdown)
        processed += 1
        print(f"Saved {output_path}")

    print(f"\nDone. Built {processed} profiled prompts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())