"""checks required files/folders exist"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "data",
    "personas",
    "spec",
    "tests",
    "metrics",
    "prompts",
    "src",
]

REQUIRED_FILES = [
    # Data
    "data/reviews_clean.jsonl",
    "data/review_groups_manual.json",
    "data/review_groups_auto.json",
    "data/review_groups_hybrid.json",

    # Personas
    "personas/personas_manual.json",
    "personas/personas_auto.json",
    "personas/personas_hybrid.json",

    # Specifications
    "spec/spec_manual.md",
    "spec/spec_auto.md",
    "spec/spec_hybrid.md",

    # Tests
    "tests/tests_manual.json",
    "tests/tests_auto.json",
    "tests/tests_hybrid.json",

    # Metrics
    "metrics/metrics_manual.json",
    "metrics/metrics_auto.json",
    "metrics/metrics_hybrid.json",
    "metrics/metrics_summary.json",

    # Prompts
    "prompts/prompt_auto.json",

    # Scripts
    "src/00_validate_repo.py",
    "src/run_all.py",
    "src/08_metrics.py",
]


def main() -> None:
    print("Checking repository structure...")

    missing_dirs: list[str] = []
    missing_files: list[str] = []

    for dir_name in REQUIRED_DIRS:
        path = ROOT / dir_name
        if path.exists() and path.is_dir():
            print(f"{dir_name}/ found")
        else:
            print(f"{dir_name}/ MISSING")
            missing_dirs.append(dir_name)

    for file_name in REQUIRED_FILES:
        path = ROOT / file_name
        if path.exists() and path.is_file():
            print(f"{file_name} found")
        else:
            print(f"{file_name} MISSING")
            missing_files.append(file_name)

    if missing_dirs or missing_files:
        print("\nRepository validation complete")
        print("Repository structure is NOT complete.")
        if missing_dirs:
            print("Missing folders:")
            for item in missing_dirs:
                print(f"  - {item}/")
        if missing_files:
            print("Missing files:")
            for item in missing_files:
                print(f"  - {item}")
    else:
        print("\nRepository validation complete")
        print("Repository structure is complete.")


if __name__ == "__main__":
    main()