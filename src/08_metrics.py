"""Compute metrics for manual, automated, and hybrid pipelines, then build a summary."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REVIEWS_FILE = ROOT / "data" / "reviews_clean.jsonl"
METRICS_DIR = ROOT / "metrics"

PIPELINES = {
    "manual": {
        "groups": ROOT / "data" / "review_groups_manual.json",
        "personas": ROOT / "personas" / "personas_manual.json",
        "spec": ROOT / "spec" / "spec_manual.md",
        "tests": ROOT / "tests" / "tests_manual.json",
        "output": ROOT / "metrics" / "metrics_manual.json",
    },
    "automated": {
        "groups": ROOT / "data" / "review_groups_auto.json",
        "personas": ROOT / "personas" / "personas_auto.json",
        "spec": ROOT / "spec" / "spec_auto.md",
        "tests": ROOT / "tests" / "tests_auto.json",
        "output": ROOT / "metrics" / "metrics_auto.json",
    },
    "hybrid": {
        "groups": ROOT / "data" / "review_groups_hybrid.json",
        "personas": ROOT / "personas" / "personas_hybrid.json",
        "spec": ROOT / "spec" / "spec_hybrid.md",
        "tests": ROOT / "tests" / "tests_hybrid.json",
        "output": ROOT / "metrics" / "metrics_hybrid.json",
    },
}

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
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
        r"- Description:\s*\[(?P<description>.*?)\]\n"
        r"- Source Persona:\s*\[(?P<source_persona>.*?)\]\n"
        r"- Traceability:\s*\[(?P<traceability>.*?)\]\n"
        r"- Acceptance Criteria:\s*\[(?P<acceptance_criteria>.*?)\]"
        r"(?:\n- Notes:\s*\[(?P<notes>.*?)\])?",
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
            "notes": (match.group("notes") or "").strip(),
        })
    return requirements


def get_group_list(groups_data: dict) -> list[dict]:
    return groups_data.get("review_groups", []) or groups_data.get("groups", [])


def get_group_ids(groups_data: dict) -> set[str]:
    ids = set()
    for group in get_group_list(groups_data):
        gid = group.get("id") or group.get("group_id")
        if gid:
            ids.add(gid)
    return ids


def get_persona_group_link(persona: dict) -> str:
    return (
        persona.get("source_review_group")
        or persona.get("derived_from_group")
        or persona.get("review_group")
        or ""
    )


def count_traceability_links(
    groups_data: dict,
    personas_data: dict,
    requirements: list[dict],
    tests_data: dict,
) -> int:
    group_ids = get_group_ids(groups_data)
    persona_ids = {persona.get("id") for persona in personas_data.get("personas", []) if persona.get("id")}
    persona_names = {persona.get("name") for persona in personas_data.get("personas", []) if persona.get("name")}
    requirement_ids = {req.get("requirement_id") for req in requirements if req.get("requirement_id")}

    links = 0

    for persona in personas_data.get("personas", []):
        if get_persona_group_link(persona) in group_ids:
            links += 1

    for req in requirements:
        if req.get("source_persona") in persona_names or req.get("source_persona") in persona_ids:
            links += 1

        traceability_text = req.get("traceability", "")
        if any(group_id in traceability_text for group_id in group_ids):
            links += 1

    for test in tests_data.get("tests", []):
        if test.get("requirement_id") in requirement_ids:
            links += 1

    return links


def compute_review_coverage(groups_data: dict, dataset_size: int) -> float:
    covered_review_ids = set()

    for group in get_group_list(groups_data):
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
        if req.get("source_persona", "").strip() and req.get("traceability", "").strip():
            traceable += 1

    return round(traceable / len(requirements), 2)


def compute_testability_rate(requirements: list[dict], tests_data: dict) -> float:
    if not requirements:
        return 0.0

    requirement_ids = {req.get("requirement_id") for req in requirements if req.get("requirement_id")}
    tested_ids = {test.get("requirement_id") for test in tests_data.get("tests", []) if test.get("requirement_id")}

    covered = len(requirement_ids.intersection(tested_ids))
    return round(covered / len(requirement_ids), 2)


def contains_ambiguous_language(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in AMBIGUOUS_TERMS)


def compute_ambiguity_ratio(requirements: list[dict]) -> float:
    if not requirements:
        return 0.0

    ambiguous_count = 0
    for req in requirements:
        if contains_ambiguous_language(req.get("description", "")) or contains_ambiguous_language(req.get("acceptance_criteria", "")):
            ambiguous_count += 1

    return round(ambiguous_count / len(requirements), 2)


def compute_pipeline_metrics(pipeline_name: str, config: dict, dataset_size: int) -> dict:
    groups_data = load_json(config["groups"])
    personas_data = load_json(config["personas"])
    spec_content = load_text(config["spec"])
    requirements = parse_spec_markdown(spec_content)
    tests_data = load_json(config["tests"])

    metrics = {
        "pipeline": pipeline_name,
        "dataset_size": dataset_size,
        "persona_count": len(personas_data.get("personas", [])),
        "requirements_count": len(requirements),
        "tests_count": len(tests_data.get("tests", [])),
        "traceability_links": count_traceability_links(groups_data, personas_data, requirements, tests_data),
        "review_coverage": compute_review_coverage(groups_data, dataset_size),
        "traceability_ratio": compute_traceability_ratio(requirements),
        "testability_rate": compute_testability_rate(requirements, tests_data),
        "ambiguity_ratio": compute_ambiguity_ratio(requirements),
    }

    save_json(config["output"], metrics)
    return metrics


def build_summary(metrics_by_pipeline: dict[str, dict]) -> dict:
    summary = {"pipelines": metrics_by_pipeline}

    compare_fields = [
        "persona_count",
        "requirements_count",
        "tests_count",
        "review_coverage",
        "traceability_ratio",
        "testability_rate",
        "ambiguity_ratio",
    ]

    best = {}
    for field in compare_fields:
        reverse = field != "ambiguity_ratio"
        ordered = sorted(
            ((name, metrics[field]) for name, metrics in metrics_by_pipeline.items()),
            key=lambda item: item[1],
            reverse=reverse,
        )
        best[field] = {
            "best_pipeline": ordered[0][0],
            "best_value": ordered[0][1],
        }

    summary["comparison"] = best
    return summary


def main() -> None:
    reviews = load_jsonl(REVIEWS_FILE)
    dataset_size = len(reviews)

    metrics_by_pipeline = {}
    for pipeline_name, config in PIPELINES.items():
        metrics_by_pipeline[pipeline_name] = compute_pipeline_metrics(pipeline_name, config, dataset_size)

    summary = build_summary(metrics_by_pipeline)
    save_json(METRICS_DIR / "metrics_summary.json", summary)

    for pipeline_name, config in PIPELINES.items():
        print(f"Saved {pipeline_name} metrics to {config['output']}")
    print(f"Saved metrics summary to {METRICS_DIR / 'metrics_summary.json'}")


if __name__ == "__main__":
    main()