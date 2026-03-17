#!/usr/bin/env python3
"""
04_generate_gpt.py

Reads prompt files from an input directory,
looks up the corresponding file_id in file_index.txt based on filename,
submits the prompt to GPT,
and saves the model output to the output directory as <file_id>_gpt.txt.

Parallel workers included.

Usage:
    python 04_generate_gpt.py \
        --input corpus/04_prompt_profiled \
        --output corpus/05_profiled_gpt \
        --file-index file_index.txt \
        --model gpt-5.1 \
        --workers 4 \
        --test 10
"""

import argparse
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from env/.env
env_path = Path(__file__).resolve().parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# ---------------------------------------------
# API
# ---------------------------------------------
try:
    from openai import OpenAI
except ImportError:
    print("Error: Install with: conda install openai")
    sys.exit(1)

# ---------------------------------------------
# CLI
# ---------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send prompts to GPT."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Directory containing prompt files (e.g., corpus/04_prompt_profiled)."
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Output directory (e.g., corpus/05_gpt)."
    )
    parser.add_argument(
        "--file-index",
        default="file_index.txt",
        help="Path to file_index.txt (default: file_index.txt)."
    )
    parser.add_argument(
        "--model", "-m",
        default="gpt-5.1",
        help="OpenAI model to use (default: gpt-5.1)."
    )
    parser.add_argument(
        "--max-output-tokens", "-t",
        type=int,
        default=6000,
        help="Maximum output tokens."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of parallel workers."
    )
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="If set, process only the first N prompt files (e.g., --test 10)."
    )
    return parser.parse_args()

# ---------------------------------------------
# Helpers
# ---------------------------------------------
def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def candidate_keys_for_path(path: Path) -> list[str]:
    """
    Generate possible lookup keys for a prompt file.

    Example:
        S24A_57_S0261_prompt_profiled.md
    candidates:
        S24A_57_S0261_prompt_profiled
        S24A_57_S0261_prompt
        S24A_57_S0261
        S24A_57
        S24A
    """
    stem = path.stem
    parts = stem.split("_")

    candidates = [stem]
    for i in range(len(parts) - 1, 0, -1):
        candidates.append("_".join(parts[:i]))

    return candidates


def resolve_file_id(path: Path, file_index: dict[str, str]) -> str | None:
    """
    Resolve a prompt filename to a file_id using several fallback keys.
    """
    for key in candidate_keys_for_path(path):
        file_id = file_index.get(key)
        if file_id:
            return file_id
    return None


def load_file_index(index_path: Path) -> dict[str, str]:
    """
    Parse file_index.txt lines of the form:
        t000001 S24A_57_S0261
    and return:
        {"t000001": "S24A_57_S0261", ...}
    """
    mapping: dict[str, str] = {}
    for line in read_text(index_path).splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        file_name, file_id = parts
        mapping[file_name] = file_id
        mapping[Path(file_name).stem] = file_id
    return mapping


def call_api(client: OpenAI, model: str, prompt_text: str, max_output_tokens: int) -> str:
    response = client.responses.create(
        model=model,
        input=prompt_text,
        max_output_tokens=max_output_tokens,
        temperature=0.7,
    )

    out = response.output_text
    if not out:
        raise RuntimeError("API returned empty output.")
    return out

# ---------------------------------------------
# Worker
# ---------------------------------------------
def process_prompt(
        path: Path,
        output_dir: Path,
        client: OpenAI,
        model: str,
        max_tokens: int,
        file_index: dict[str, str],
):
    try:
        print(f"[WORKER] Reading prompt: {path.name}")
        prompt_text = read_text(path)

        file_id = resolve_file_id(path, file_index)
        if not file_id:
            raise KeyError(f"No file_id found in file_index.txt for {path.name}")

        print(f"[WORKER] Calling API for {path.name} → {file_id}")
        result = call_api(
            client=client,
            model=model,
            prompt_text=prompt_text,
            max_output_tokens=max_tokens,
        )

        outpath = output_dir / f"{file_id}_gpt.txt"
        write_text(outpath, result)
        print(f"[WORKER] Saved → {outpath}")

        return True

    except Exception as e:
        print(f"[ERROR] {path.name}: {e}")
        return False

# ---------------------------------------------
# Main
# ---------------------------------------------
def main():
    args = parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_index_path = Path(args.file_index)
    if not file_index_path.exists():
        print(f"Error: file index not found: {file_index_path}")
        sys.exit(1)

    file_index = load_file_index(file_index_path)

    files = sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.name != file_index_path.name
    )
    if not files:
        print("No prompt files found.")
        sys.exit(0)

    if args.test is not None:
        if args.test <= 0:
            print("Error: --test must be a positive integer.")
            sys.exit(1)
        files = files[:args.test]
        print(f"[TEST MODE] Limiting to first {len(files)} prompt files.\n")

    # API client
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        sys.exit(1)
    client = OpenAI(api_key=api_key)

    print(f"Processing {len(files)} prompts with {args.workers} workers…\n")

    futures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in files:
            futures.append(
                pool.submit(
                    process_prompt,
                    f,
                    output_dir,
                    client,
                    args.model,
                    args.max_output_tokens,
                    file_index,
                )
            )

        for fut in as_completed(futures):
            fut.result()

    print("\nAll prompts processed successfully with GPT.")


if __name__ == "__main__":
    main()