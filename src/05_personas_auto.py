"""automated persona generation pipeline"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
REVIEWS_FILE = ROOT / "data" / "reviews_clean.jsonl"
GROUPS_FILE = ROOT / "data" / "review_groups_auto.json"
PERSONAS_FILE = ROOT / "personas" / "personas_auto.json"
PROMPT_FILE = ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
GROUP_COUNT = 5
THEME_SAMPLE_SIZE = 120
ASSIGNMENT_BATCH_SIZE = 30
MAX_EXAMPLE_REVIEWS_FOR_PERSONA = 12
MAX_EXAMPLE_REVIEWS_PER_GROUP = 3


def load_reviews(path: Path) -> list[dict]:
    reviews = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reviews.append(json.loads(line))
    return reviews


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def chunk_list(items: list, batch_size: int) -> list[list]:
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def get_review_text(review: dict) -> str:
    clean_text = review.get("content_clean")
    if isinstance(clean_text, str) and clean_text.strip():
        return clean_text.strip()

    raw_text = review.get("content_raw")
    if isinstance(raw_text, str) and raw_text.strip():
        return raw_text.strip()

    raise KeyError(f"No usable review text found in review: {review}")


def build_theme_generation_prompt(sample_reviews: list[dict]) -> str:
    joined_reviews = "\n".join(
        [f'{review["id"]}: {get_review_text(review)}' for review in sample_reviews]
    )

    return f"""
You are given cleaned app reviews.

Your task is to create exactly {GROUP_COUNT} review group themes that represent the main types of feedback in the dataset.

Rules:
1. Create exactly {GROUP_COUNT} groups.
2. Each group must have:
   - id: G1 to G{GROUP_COUNT}
   - theme
   - description
3. Themes must be distinct and broad enough to cover many related reviews.
4. Do not include review_ids yet.
5. Do not invent information not supported by the reviews.
6. Return valid JSON only in exactly this format:

{{
  "themes": [
    {{
      "id": "G1",
      "theme": "theme name",
      "description": "short description"
    }}
  ]
}}

Reviews:
{joined_reviews}
""".strip()


def build_assignment_prompt(review_batch: list[dict], themes: list[dict]) -> str:
    theme_text = "\n".join(
        [f'{theme["id"]}: {theme["theme"]} - {theme["description"]}' for theme in themes]
    )

    review_text = "\n".join(
        [f'{review["id"]}: {get_review_text(review)}' for review in review_batch]
    )

    expected_ids = [review["id"] for review in review_batch]

    return f"""
Assign each review to exactly one of the following {GROUP_COUNT} review groups.

Groups:
{theme_text}

Rules:
1. Every review must be assigned to exactly one group id from G1 to G{GROUP_COUNT}.
2. Do not skip any review.
3. Do not create new groups.
4. Use each review_id exactly as written.
5. Return one assignment for every review_id listed below.
6. Return valid JSON only in exactly this format:

{{
  "assignments": [
    {{
      "review_id": "exact review id from input",
      "group_id": "G1"
    }}
  ]
}}

Review IDs that must all appear exactly once:
{json.dumps(expected_ids, ensure_ascii=False)}

Reviews:
{review_text}
""".strip()

def build_persona_prompt(group: dict, review_texts: list[str], persona_id: str) -> str:
    joined_reviews = "\n".join(
        [f"- {text}" for text in review_texts[:MAX_EXAMPLE_REVIEWS_FOR_PERSONA]]
    )

    return f"""
Create one grounded user persona from the following automated review group.

Rules:
1. Use only the evidence in the review group and review texts.
2. Do not invent demographic details, medical conditions, profession, age, or personal background unless explicitly supported by the reviews.
3. The persona must summarize common goals, pain points, and usage context.
4. Keep the persona realistic and concise.
5. Return valid JSON only in exactly this format:

{{
  "id": "{persona_id}",
  "name": "persona name",
  "description": "1 to 2 sentence summary",
  "goals": ["goal 1", "goal 2", "goal 3"],
  "pain_points": ["pain point 1", "pain point 2", "pain point 3"],
  "context": "short context paragraph",
  "source_review_group": "{group["id"]}"
}}

Review Group ID: {group["id"]}
Theme: {group["theme"]}
Description: {group.get("description", "")}

Example Reviews:
{joined_reviews}
""".strip()


def generate_themes(client: Groq, reviews: list[dict]) -> list[dict]:
    sample_reviews = reviews[:THEME_SAMPLE_SIZE]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are helping with software requirements engineering. "
                    "Create meaningful review themes from app reviews. "
                    "Return valid JSON only."
                ),
            },
            {"role": "user", "content": build_theme_generation_prompt(sample_reviews)},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_completion_tokens=2000,
    )

    data = json.loads(response.choices[0].message.content)
    themes = data.get("themes", [])

    if len(themes) != GROUP_COUNT:
        raise ValueError(f"Expected {GROUP_COUNT} themes, got {len(themes)}")

    expected_ids = [f"G{i}" for i in range(1, GROUP_COUNT + 1)]
    actual_ids = [theme.get("id") for theme in themes]
    if actual_ids != expected_ids:
        raise ValueError(f"Expected theme IDs {expected_ids}, got {actual_ids}")

    return themes


def assign_batch(client: Groq, batch: list[dict], themes: list[dict]) -> list[dict]:
    batch_ids = [review["id"] for review in batch]
    remaining_reviews = batch[:]
    final_assignments = []

    max_attempts = 3
    attempt = 0

    while remaining_reviews and attempt < max_attempts:
        attempt += 1

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are helping with software requirements engineering. "
                        "Assign every review to exactly one existing theme only. "
                        "Do not skip any review. Return valid JSON only."
                    ),
                },
                {"role": "user", "content": build_assignment_prompt(remaining_reviews, themes)},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_completion_tokens=2500,
        )

        data = json.loads(response.choices[0].message.content)
        assignments = data.get("assignments", [])

        assigned_ids_this_round = set()

        for item in assignments:
            review_id = item.get("review_id")
            group_id = item.get("group_id")

            if review_id in batch_ids and group_id in {f"G{i}" for i in range(1, GROUP_COUNT + 1)}:
                if review_id not in assigned_ids_this_round and review_id not in {
                    a["review_id"] for a in final_assignments
                }:
                    final_assignments.append({
                        "review_id": review_id,
                        "group_id": group_id
                    })
                    assigned_ids_this_round.add(review_id)

        assigned_ids_total = {a["review_id"] for a in final_assignments}
        remaining_reviews = [review for review in batch if review["id"] not in assigned_ids_total]

        if remaining_reviews:
            print(
                f"Assignment retry {attempt}: still missing {len(remaining_reviews)} reviews."
            )

    if remaining_reviews:
        print(
            f"Warning: {len(remaining_reviews)} reviews were still unassigned after retries. "
            f"Assigning them to G1 as fallback."
        )
        for review in remaining_reviews:
            final_assignments.append({
                "review_id": review["id"],
                "group_id": "G1"
            })

    return final_assignments

def build_final_groups(
    reviews: list[dict],
    themes: list[dict],
    assignments: list[dict]
) -> dict:
    review_lookup = {review["id"]: get_review_text(review) for review in reviews}

    grouped = {
        theme["id"]: {
            "id": theme["id"],
            "theme": theme["theme"],
            "description": theme["description"],
            "review_ids": [],
            "example_reviews": []
        }
        for theme in themes
    }

    seen_review_ids = set()

    for item in assignments:
        review_id = item.get("review_id")
        group_id = item.get("group_id")

        if review_id in seen_review_ids:
            continue

        if review_id in review_lookup and group_id in grouped:
            grouped[group_id]["review_ids"].append(review_id)
            seen_review_ids.add(review_id)

    for group in grouped.values():
        group["example_reviews"] = [
            review_lookup[rid][:160]
            for rid in group["review_ids"][:MAX_EXAMPLE_REVIEWS_PER_GROUP]
        ]

    return {"review_groups": list(grouped.values())}


def validate_persona(persona: dict, persona_id: str) -> None:
    required_fields = [
        "id",
        "name",
        "description",
        "goals",
        "pain_points",
        "context",
        "source_review_group",
    ]
    missing = [field for field in required_fields if field not in persona]
    if missing:
        raise ValueError(f"Missing fields in persona {persona_id}: {missing}")


def generate_persona(
    client: Groq,
    group: dict,
    review_texts: list[str],
    persona_id: str
) -> dict:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are helping with software requirements engineering. "
                    "Generate grounded personas from grouped app reviews. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": build_persona_prompt(group, review_texts, persona_id),
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_completion_tokens=1200,
    )

    persona = json.loads(response.choices[0].message.content)
    validate_persona(persona, persona_id)
    return persona


def generate_review_groups(client: Groq, reviews: list[dict]) -> dict:
    print("Generating review themes...")
    themes = generate_themes(client, reviews)

    print("Assigning reviews to themes...")
    assignments = []
    batches = chunk_list(reviews, ASSIGNMENT_BATCH_SIZE)

    for batch_index, batch in enumerate(batches, start=1):
        print(f"Processing assignment batch {batch_index}/{len(batches)}...")
        batch_assignments = assign_batch(client, batch, themes)
        assignments.extend(batch_assignments)

    final_groups = build_final_groups(reviews, themes, assignments)
    return final_groups


def generate_all_personas(client: Groq, reviews: list[dict], groups_data: dict) -> dict:
    review_lookup = {review["id"]: get_review_text(review) for review in reviews}
    groups = groups_data.get("review_groups", [])
    personas = []

    for index, group in enumerate(groups, start=1):
        persona_id = f"P{index}"
        review_ids = group.get("review_ids", [])
        review_texts = [review_lookup[rid] for rid in review_ids if rid in review_lookup]

        if not review_texts:
            print(f"Skipping group {group['id']} because it has no matched reviews.")
            continue

        try:
            print(f"Generating persona for group {group['id']}...")
            persona = generate_persona(client, group, review_texts, persona_id)
            personas.append(persona)
        except Exception as e:
            print(f"Failed to generate persona for group {group['id']}: {e}")

    return {"personas": personas}


def save_prompt_record() -> None:
    prompt_record = {
        "review_grouping": {
            "task": "Automatic review grouping",
            "model": MODEL_NAME,
            "theme_generation_prompt": (
                f"Create exactly {GROUP_COUNT} review group themes from a sample of cleaned reviews. "
                "Return only JSON with id, theme, and description."
            ),
            "assignment_prompt": (
                f"Assign each review to exactly one of the {GROUP_COUNT} predefined group IDs. "
                "Return only JSON with review_id and group_id."
            ),
        },
        "persona_generation": {
            "task": "Automatic persona generation",
            "model": MODEL_NAME,
            "persona_prompt_template": (
                "Create one grounded persona from a review group using only the theme, "
                "description, and grouped reviews. Include id, name, description, goals, "
                "pain_points, context, and source_review_group."
            ),
        },
    }

    save_json(PROMPT_FILE, prompt_record)


def main() -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in environment.")

    reviews = load_reviews(REVIEWS_FILE)
    if not reviews:
        raise ValueError("No reviews found in data/reviews_clean.jsonl")

    client = Groq(api_key=api_key)

    review_groups_data = generate_review_groups(client, reviews)
    save_json(GROUPS_FILE, review_groups_data)
    print(f"Saved review groups to {GROUPS_FILE}")

    personas_data = generate_all_personas(client, reviews, review_groups_data)
    save_json(PERSONAS_FILE, personas_data)
    print(f"Saved personas to {PERSONAS_FILE}")

    save_prompt_record()
    print(f"Saved prompts to {PROMPT_FILE}")


if __name__ == "__main__":
    main()