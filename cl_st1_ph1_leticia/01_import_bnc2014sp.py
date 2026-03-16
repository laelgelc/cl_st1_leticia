from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
TOP_TALKERS_PATH = PROJECT_DIR / "top_talkers.ndjson"
XML_DIR = PROJECT_DIR / "corpus" / "bnc2014spoken-xml" / "spoken" / "untagged"
OUTPUT_DIR = PROJECT_DIR / "corpus" / "01_bnc2014sp_dataset"
LOG_PATH = OUTPUT_DIR / "01_import_bnc2014sp.log"


def setup_logging() -> logging.Logger:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("bnc2014sp_import")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None

    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def normalize_for_comparison(value: Any) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    return text.casefold()


def extract_full_text(elem: ET.Element | None) -> str | None:
    if elem is None:
        return None
    return normalize_text("".join(elem.itertext()))


def load_top_talkers(logger: logging.Logger) -> tuple[pd.DataFrame, dict[str, str]]:
    logger.info("Loading top talkers from %s", TOP_TALKERS_PATH)

    if not TOP_TALKERS_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {TOP_TALKERS_PATH}")

    df_top_talkers = pd.read_json(TOP_TALKERS_PATH, orient="records", lines=True)

    required_columns = {"text_id", "top_talker"}
    missing_columns = required_columns - set(df_top_talkers.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns in top_talkers file: {sorted(missing_columns)}"
        )

    df_top_talkers["text_id"] = df_top_talkers["text_id"].map(normalize_text)
    df_top_talkers["top_talker"] = df_top_talkers["top_talker"].map(normalize_text)

    top_talker_map = (
        df_top_talkers.dropna(subset=["text_id"])
        .drop_duplicates(subset=["text_id"], keep="first")
        .set_index("text_id")["top_talker"]
        .to_dict()
    )

    logger.info("Loaded %s top-talker records", len(df_top_talkers))
    return df_top_talkers, top_talker_map


def parse_header(
        header: ET.Element | None,
        text_id: str,
        logger: logging.Logger,
) -> dict[str, Any]:
    row: dict[str, Any] = {"text_id": text_id}

    if header is None:
        logger.warning("Missing <header> in text %s", text_id)
        return row

    for child in header:
        if child.tag == "speakerInfo":
            continue
        row[child.tag] = extract_full_text(child)

    return row


def parse_speaker_info_occurrences(
        header: ET.Element | None,
        text_id: str,
        logger: logging.Logger,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if header is None:
        return rows

    speaker_info = header.find("speakerInfo")
    if speaker_info is None:
        logger.warning("Missing <speakerInfo> in text %s", text_id)
        return rows

    for speaker in speaker_info.findall("speaker"):
        speaker_id = normalize_text(speaker.get("id"))
        if speaker_id is None:
            logger.warning("Speaker without id in text %s", text_id)
            continue

        row: dict[str, Any] = {
            "text_id": text_id,
            "speaker_id": speaker_id,
        }

        for child in speaker:
            row[child.tag] = extract_full_text(child)

        rows.append(row)

    return rows


def build_speaker_master(
        speaker_occurrence_rows: list[dict[str, Any]],
        logger: logging.Logger,
) -> list[dict[str, Any]]:
    master_by_speaker: dict[str, dict[str, Any]] = {}

    for row in speaker_occurrence_rows:
        speaker_id = row["speaker_id"]

        if speaker_id not in master_by_speaker:
            master_by_speaker[speaker_id] = {
                key: value
                for key, value in row.items()
                if key != "text_id"
            }
            continue

        master_row = master_by_speaker[speaker_id]

        for key, new_value in row.items():
            if key in {"text_id", "speaker_id"}:
                continue

            existing_value = master_row.get(key)

            existing_cmp = normalize_for_comparison(existing_value)
            new_cmp = normalize_for_comparison(new_value)

            if existing_cmp is None and new_value is not None:
                master_row[key] = new_value
                continue

            if new_cmp is None:
                continue

            if existing_cmp != new_cmp:
                logger.warning(
                    "Speaker metadata mismatch for %s | field=%s | existing=%r | new=%r | text_id=%s",
                    speaker_id,
                    key,
                    existing_value,
                    new_value,
                    row["text_id"],
                )

    return list(master_by_speaker.values())


def parse_conversation_rows(
        body: ET.Element | None,
        text_id: str,
        top_talker_map: dict[str, str],
        logger: logging.Logger,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if body is None:
        logger.warning("Missing <body> in text %s", text_id)
        return rows

    top_talker_id = top_talker_map.get(text_id)
    if top_talker_id is None:
        logger.warning("No top_talker match found for text %s", text_id)

    for utterance in body.findall("u"):
        speaker_id = normalize_text(utterance.get("who"))
        turn_n_raw = normalize_text(utterance.get("n"))
        turn_n = pd.to_numeric(turn_n_raw, errors="coerce")

        row: dict[str, Any] = {
            "text_id": text_id,
            "turn_n": int(turn_n) if pd.notna(turn_n) else None,
            "speaker_id": speaker_id,
            "utterance": extract_full_text(utterance),
        }

        for attr_name, attr_value in utterance.attrib.items():
            if attr_name == "n":
                continue
            if attr_name == "who":
                continue
            row[attr_name] = normalize_text(attr_value)

        if top_talker_id is None or speaker_id is None:
            row["top_talker"] = None
        else:
            row["top_talker"] = "Yes" if speaker_id == top_talker_id else "No"

        rows.append(row)

    return rows


def save_ndjson(df: pd.DataFrame, output_path: Path, logger: logging.Logger) -> None:
    df.to_json(output_path, orient="records", lines=True, force_ascii=False)
    logger.info("Wrote %s rows to %s", len(df), output_path)


def main() -> None:
    logger = setup_logging()
    logger.info("Starting BNC 2014 Spoken import")

    _, top_talker_map = load_top_talkers(logger)

    if not XML_DIR.exists():
        raise FileNotFoundError(f"Missing XML directory: {XML_DIR}")

    xml_files = sorted(XML_DIR.glob("*.xml"))
    logger.info("Found %s XML files in %s", len(xml_files), XML_DIR)

    header_rows: list[dict[str, Any]] = []
    speaker_occurrence_rows: list[dict[str, Any]] = []
    conversation_rows: list[dict[str, Any]] = []

    for xml_file in xml_files:
        logger.info("Processing %s", xml_file.name)

        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            logger.error("Failed to parse %s: %s", xml_file.name, exc)
            continue

        text_id = normalize_text(root.get("id")) or xml_file.stem
        if root.get("id") is None:
            logger.warning("Missing root id in %s; using filename stem %s", xml_file.name, text_id)

        header = root.find("header")
        body = root.find("body")

        header_rows.append(parse_header(header, text_id, logger))
        speaker_occurrence_rows.extend(
            parse_speaker_info_occurrences(header, text_id, logger)
        )
        conversation_rows.extend(
            parse_conversation_rows(body, text_id, top_talker_map, logger)
        )

    speaker_master_rows = build_speaker_master(speaker_occurrence_rows, logger)

    df_bnc2014sp_header = pd.DataFrame(header_rows)
    if not df_bnc2014sp_header.empty:
        df_bnc2014sp_header = df_bnc2014sp_header.sort_values(
            by=["text_id"],
            na_position="last",
        ).reset_index(drop=True)

    df_bnc2014sp_speaker_info_occurrences = pd.DataFrame(speaker_occurrence_rows)
    if not df_bnc2014sp_speaker_info_occurrences.empty:
        df_bnc2014sp_speaker_info_occurrences = (
            df_bnc2014sp_speaker_info_occurrences.sort_values(
                by=["speaker_id", "text_id"],
                na_position="last",
            ).reset_index(drop=True)
        )

    df_bnc2014sp_speakers = pd.DataFrame(speaker_master_rows)
    if not df_bnc2014sp_speakers.empty:
        df_bnc2014sp_speakers = df_bnc2014sp_speakers.sort_values(
            by=["speaker_id"],
            na_position="last",
        ).reset_index(drop=True)

    df_bnc2014sp_conversation = pd.DataFrame(conversation_rows)
    if not df_bnc2014sp_conversation.empty:
        sort_columns = [col for col in ["text_id", "turn_n"] if col in df_bnc2014sp_conversation.columns]
        df_bnc2014sp_conversation = df_bnc2014sp_conversation.sort_values(
            by=sort_columns,
            na_position="last",
        ).reset_index(drop=True)

    save_ndjson(
        df_bnc2014sp_header,
        OUTPUT_DIR / "bnc2014sp_header.ndjson",
        logger,
        )
    save_ndjson(
        df_bnc2014sp_speaker_info_occurrences,
        OUTPUT_DIR / "bnc2014sp_speaker_info_occurrences.ndjson",
        logger,
        )
    save_ndjson(
        df_bnc2014sp_speakers,
        OUTPUT_DIR / "bnc2014sp_speakers.ndjson",
        logger,
        )
    save_ndjson(
        df_bnc2014sp_conversation,
        OUTPUT_DIR / "bnc2014sp_conversation.ndjson",
        logger,
        )

    logger.info("Import finished successfully")


if __name__ == "__main__":
    main()