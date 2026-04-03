"""
imports or reads your raw dataset; if you scraped, include scraper here
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from google_play_scraper import Sort, reviews

APP_NAME = "Medito"
APP_ID = "meditofoundation.medito"
OUTPUT_PATH = Path("data/reviews_raw.jsonl")

# Try to collect at least 1000 if available
TARGET_REVIEW_COUNT = 1500
BATCH_SIZE = 200
LANG = "en"
COUNTRY = "ca"


def normalize_review(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Keep a stable structure for downstream tasks.
    """
    return {
        "id": raw.get("reviewId"),
        "app_name": APP_NAME,
        "app_id": APP_ID,
        "user_name": raw.get("userName"),
        "score": raw.get("score"),
        "content": raw.get("content"),
        "thumbs_up_count": raw.get("thumbsUpCount"),
        "review_created_version": raw.get("reviewCreatedVersion"),
        "at": str(raw.get("at")) if raw.get("at") is not None else None,
        "reply_content": raw.get("replyContent"),
        "replied_at": str(raw.get("repliedAt")) if raw.get("repliedAt") is not None else None,
    }


def collect_reviews() -> list[dict[str, Any]]:
    """
    Collect reviews from Google Play using pagination.
    """
    all_reviews: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    continuation_token = None

    while len(all_reviews) < TARGET_REVIEW_COUNT:
        batch, continuation_token = reviews(
            APP_ID,
            lang=LANG,
            country=COUNTRY,
            sort=Sort.NEWEST,
            count=BATCH_SIZE,
            continuation_token=continuation_token,
        )

        if not batch:
            break

        added_this_round = 0

        for raw in batch:
            normalized = normalize_review(raw)
            review_id = normalized.get("id")

            if not review_id or review_id in seen_ids:
                continue

            seen_ids.add(review_id)
            all_reviews.append(normalized)
            added_this_round += 1

            if len(all_reviews) >= TARGET_REVIEW_COUNT:
                break

        if added_this_round == 0:
            break

        if continuation_token is None:
            break

    return all_reviews


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    print(f"Collecting reviews for {APP_NAME} ({APP_ID})...")
    rows = collect_reviews()
    write_jsonl(OUTPUT_PATH, rows)
    print(f"Saved {len(rows)} raw reviews to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()