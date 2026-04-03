"""
cleans raw data & make clean dataset
"""

from __future__ import annotations

import json
import re
import string
import unicodedata
from pathlib import Path
from typing import Any

import emoji
import inflect
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

RAW_PATH = Path("data/reviews_raw.jsonl")
CLEAN_PATH = Path("data/reviews_clean.jsonl")
META_PATH = Path("data/dataset_metadata.json")

APP_NAME = "Medito"
APP_ID = "meditofoundation.medito"
MIN_WORDS = 3

_number_engine = inflect.engine()


def ensure_nltk() -> None:
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)


ensure_nltk()

STOP_WORDS = set(stopwords.words("english"))
LEMMATIZER = WordNetLemmatizer()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    with path.open("r", encoding="utf 8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf 8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_for_duplicate_check(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def numbers_to_words(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        try:
            return " " + _number_engine.number_to_words(value) + " "
        except Exception:
            return " "

    return re.sub(r"\d+", repl, text)


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = emoji.replace_emoji(text, replace="")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = numbers_to_words(text)
    text = text.lower()

    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"[^a-z\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens: list[str] = []
    for token in text.split():
        if token in STOP_WORDS:
            continue
        lemma = LEMMATIZER.lemmatize(token)
        if lemma:
            tokens.append(lemma)

    return " ".join(tokens)


def build_metadata(
    raw_count: int,
    clean_count: int,
    duplicate_count: int,
    empty_count: int,
    short_count: int,
) -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "app_id": APP_ID,
        "raw_dataset_size": raw_count,
        "cleaned_dataset_size": clean_count,
        "collection_method": "Google Play reviews collected programmatically in src/01_collect_or_import.py using google-play-scraper",
        "cleaning_decisions": [
            "Removed duplicate reviews",
            "Removed empty entries",
            f"Removed extremely short reviews with fewer than {MIN_WORDS} words after cleaning",
            "Removed punctuation",
            "Removed special characters",
            "Removed emojis",
            "Converted numbers to text",
            "Removed extra whitespace",
            "Converted all words to lowercase",
            "Removed stop words",
            "Lemmatized the reviews",
        ],
    }


def main() -> None:
    raw_rows = load_jsonl(RAW_PATH)

    seen_texts: set[str] = set()
    cleaned_rows: list[dict[str, Any]] = []

    duplicate_count = 0
    empty_count = 0
    short_count = 0

    for row in raw_rows:
        raw_text = (row.get("content") or "").strip()

        if not raw_text:
            empty_count += 1
            continue

        dedupe_key = normalize_for_duplicate_check(raw_text)
        if dedupe_key in seen_texts:
            duplicate_count += 1
            continue
        seen_texts.add(dedupe_key)

        cleaned_text = clean_text(raw_text)
        if not cleaned_text:
            empty_count += 1
            continue

        if len(cleaned_text.split()) < MIN_WORDS:
            short_count += 1
            continue

        cleaned_rows.append(
            {
                "id": row.get("id"),
                "app_name": row.get("app_name", APP_NAME),
                "app_id": row.get("app_id", APP_ID),
                "score": row.get("score"),
                "content_raw": raw_text,
                "content_clean": cleaned_text,
                "at": row.get("at"),
            }
        )

    write_jsonl(CLEAN_PATH, cleaned_rows)

    metadata = build_metadata(
        raw_count=len(raw_rows),
        clean_count=len(cleaned_rows),
        duplicate_count=duplicate_count,
        empty_count=empty_count,
        short_count=short_count,
    )

    META_PATH.parent.mkdir(parents=True, exist_ok=True)
    with META_PATH.open("w", encoding="utf 8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Raw reviews loaded: {len(raw_rows)}")
    print(f"Clean reviews saved: {len(cleaned_rows)}")
    print(f"Duplicates removed: {duplicate_count}")
    print(f"Empty removed: {empty_count}")
    print(f"Short removed: {short_count}")
    print(f"Saved cleaned dataset to {CLEAN_PATH}")
    print(f"Saved metadata to {META_PATH}")


if __name__ == "__main__":
    main()