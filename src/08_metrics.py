"""computes metrics: coverage/traceability/ambiguity/testability"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REVIEWS_FILE = ROOT / "data" / "reviews_clean.jsonl"
GROUPS_FILE = ROOT / "data" / "review_groups_auto.json"
PERSONAS_FILE = ROOT / "personas" / "personas_auto.json"
SPEC_FILE = ROOT / "spec" / "spec_auto.md"
TESTS_FILE = ROOT / "tests" / "tests_auto.json"
OUTPUT_FILE = ROOT / "metrics" / "metrics_auto.json"


AMBIGUOUS_TERMS = {
    "fast",
    "easy",
    "better",
    "user-friendly",
    "simple",
    "quick",
    "quickly",
    "efficient",
    "efficiently",
    "seamless",
    "smooth",
    "intuitive",
    "convenient",
    "reliable",
    "responsive",
    "effective",
    "improved",
    "appropriate",
    "flexible",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def parse_spec_markdown(content: str) -> list[dict]:
    pattern = re.compile(
        r"# Requirement ID:\s*(?P<requirement_id>.+?)\n"
        r"- Description:\s*\[(?P<description>.*?)\]\n\s*\n"
        r"- Source Persona:\s*\[(?P<source_persona>.*?)\]\n"
        r"- Traceability:\s*\[(?P<traceability>.*?)\]\n"
        r"- Acceptance Criteria:\s*\[(?P<acceptance_criteria>.*?)\]",
        re.DOTALL,
    )

    requirements = []
    for match in pattern.finditer(content):
        requirements.append({
            "requirement_id": match.group("requirement_id").strip(),
            "description": match.group("description").strip(),
            "source_persona": match.group("source_persona").strip(),
            "traceability": match.group("traceability").strip(),
            "acceptance_criteria": match.group("acceptance_criteria").strip(),
        })

    return requirements


def count_traceability_links(
    groups_data: dict,
    personas_data: dict,
    requirements: list[dict],
    tests_data: dict,
) -> int:
    group_ids = {group.get("id") for group in groups_data.get("review_groups", [])}
    persona_ids = {persona.get("id") for persona in personas_data.get("personas", [])}
    persona_names = {persona.get("name") for persona in personas_data.get("personas", [])}
    requirement_ids = {req.get("requirement_id") for req in requirements}

    links = 0

    for persona in personas_data.get("personas", []):
        if persona.get("source_review_group") in group_ids:
            links += 1

    for req in requirements:
        if req.get("source_persona") in persona_names or req.get("source_persona") in persona_ids:
            links += 1

        traceability_text = req.get("traceability", "")
        if any(group_id and group_id in traceability_text for group_id in group_ids):
            links += 1

    for test in tests_data.get("tests", []):
        if test.get("requirement_id") in requirement_ids:
            links += 1

    return links


def compute_review_coverage(groups_data: dict, dataset_size: int) -> float:
    covered_review_ids = set()

    for group in groups_data.get("review_groups", []):
        for review_id in group.get("review_ids", []):
            covered_review_ids.add(review_id)

    if dataset_size == 0:
        return 0.0

    return round(len(covered_review_ids) / dataset_size, 2)


def compute_traceability_ratio(requirements: list[dict]) -> float:
    if not requirements:
        return 0.0

    traceable = 0
    for req in requirements:
        source_persona = req.get("source_persona", "").strip()
        traceability = req.get("traceability", "").strip()
        if source_persona and traceability:
            traceable += 1

    return round(traceable / len(requirements), 2)


def compute_testability_rate(requirements: list[dict], tests_data: dict) -> float:
    if not requirements:
        return 0.0

    requirement_ids = {req.get("requirement_id") for req in requirements}
    tested_ids = {
        test.get("requirement_id")
        for test in tests_data.get("tests", [])
        if test.get("requirement_id")
    }

    covered = len(requirement_ids.intersection(tested_ids))
    return round(covered / len(requirement_ids), 2)


def contains_ambiguous_language(text: str) -> bool:
    lowered = text.lower()
    for term in AMBIGUOUS_TERMS:
        if term in lowered:
            return True
    return False


def compute_ambiguity_ratio(requirements: list[dict]) -> float:
    if not requirements:
        return 0.0

    ambiguous_count = 0
    for req in requirements:
        description = req.get("description", "")
        acceptance = req.get("acceptance_criteria", "")
        if contains_ambiguous_language(description) or contains_ambiguous_language(acceptance):
            ambiguous_count += 1

    return round(ambiguous_count / len(requirements), 2)


def main() -> None:
    reviews = load_jsonl(REVIEWS_FILE)
    groups_data = load_json(GROUPS_FILE)
    personas_data = load_json(PERSONAS_FILE)
    spec_content = load_text(SPEC_FILE)
    requirements = parse_spec_markdown(spec_content)
    tests_data = load_json(TESTS_FILE)

    dataset_size = len(reviews)
    persona_count = len(personas_data.get("personas", []))
    requirements_count = len(requirements)
    tests_count = len(tests_data.get("tests", []))

    metrics = {
        "pipeline": "automated",
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": count_traceability_links(
            groups_data,
            personas_data,
            requirements,
            tests_data,
        ),
        "review_coverage": compute_review_coverage(groups_data, dataset_size),
        "traceability_ratio": compute_traceability_ratio(requirements),
        "testability_rate": compute_testability_rate(requirements, tests_data),
        "ambiguity_ratio": compute_ambiguity_ratio(requirements),
    }

    save_json(OUTPUT_FILE, metrics)
    print(f"Saved automated metrics to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()