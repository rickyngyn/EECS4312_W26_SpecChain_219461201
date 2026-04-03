"""
run_all.py

Executes the automated pipeline from start to finish by running the
numbered pipeline scripts in src/ in ascending order.

It skips:
- 00_validate_repo.py
- run_all.py

Typical execution order:
1. clean raw reviews
2. generate automated review groups
3. generate automated personas
4. generate automated specification
5. generate automated tests
6. compute metrics

Expected outputs include:
- data/reviews_clean.jsonl
- data/review_groups_auto.json
- personas/personas_auto.json
- spec/spec_auto.md
- tests/tests_auto.json
- metrics/metrics_auto.json
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"


def get_pipeline_scripts() -> list[Path]:
    scripts = []

    for path in SRC.glob("*.py"):
        name = path.name

        if name in {"00_validate_repo.py", "run_all.py"}:
            continue

        if len(name) >= 2 and name[:2].isdigit():
            scripts.append(path)

    scripts.sort(key=lambda p: p.name)
    return scripts


def main() -> None:
    print("Starting automated pipeline...")

    scripts = get_pipeline_scripts()

    if not scripts:
        raise FileNotFoundError(
            "No numbered pipeline scripts were found in src/."
        )

    for script in scripts:
        print(f"\nRunning {script.name} ...")
        subprocess.run([sys.executable, str(script)], check=True)
        print(f"Finished {script.name}")

    print("\nAutomated pipeline completed successfully.")


if __name__ == "__main__":
    main()