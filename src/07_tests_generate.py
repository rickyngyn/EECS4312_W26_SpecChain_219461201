"""generates tests from specs"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT / "spec" / "spec_auto.md"
TESTS_FILE = ROOT / "tests" / "tests_auto.json"
PROMPT_FILE = ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


def build_tests_prompt(requirements: list[dict]) -> str:
    requirements_json = json.dumps(requirements, indent=2, ensure_ascii=False)

    return f"""
Generate validation test scenarios for the following functional requirements.

Rules:
1. Create at least one test scenario for every requirement.
2. Every test must include:
   - test_id
   - requirement_id
   - scenario
   - steps
   - expected_result
3. Use test IDs in the format T_auto_1, T_auto_2, T_auto_3, and so on.
4. requirement_id must exactly match one of the provided requirement IDs.
5. steps must be a clear list of execution steps.
6. expected_result must reflect what should happen if the requirement is satisfied.
7. Return valid JSON only in exactly this format:

{{
  "tests": [
    {{
      "test_id": "T_auto_1",
      "requirement_id": "FR_auto_1",
      "scenario": "Short scenario name",
      "steps": [
        "Step 1",
        "Step 2",
        "Step 3"
      ],
      "expected_result": "Expected outcome"
    }}
  ]
}}

Requirements:
{requirements_json}
""".strip()


def generate_tests(client: Groq, requirements: list[dict]) -> list[dict]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are helping with software requirements engineering. "
                    "Generate clear validation test scenarios from functional requirements. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": build_tests_prompt(requirements),
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_completion_tokens=4000,
    )

    data = json.loads(response.choices[0].message.content)
    tests = data.get("tests", [])

    if not tests:
        raise ValueError("No tests were generated.")

    return tests


def validate_tests(tests: list[dict], requirements: list[dict]) -> None:
    valid_requirement_ids = {req["requirement_id"] for req in requirements}
    covered_requirement_ids = set()

    for index, test in enumerate(tests, start=1):
        required_fields = [
            "test_id",
            "requirement_id",
            "scenario",
            "steps",
            "expected_result",
        ]
        missing = [field for field in required_fields if field not in test]
        if missing:
            raise ValueError(f"Test missing fields: {missing}")

        expected_test_id = f"T_auto_{index}"
        if test["test_id"] != expected_test_id:
            raise ValueError(
                f"Expected test_id {expected_test_id}, got {test['test_id']}"
            )

        requirement_id = test["requirement_id"]
        if requirement_id not in valid_requirement_ids:
            raise ValueError(
                f"Invalid requirement_id in test {test['test_id']}: {requirement_id}"
            )

        if not isinstance(test["steps"], list) or not test["steps"]:
            raise ValueError(
                f"Test {test['test_id']} must contain a non-empty list of steps."
            )

        covered_requirement_ids.add(requirement_id)

    missing_requirements = valid_requirement_ids - covered_requirement_ids
    if missing_requirements:
        raise ValueError(
            f"Some requirements have no linked test scenarios: {sorted(missing_requirements)}"
        )


def update_prompt_record() -> None:
    prompt_data = {}
    if PROMPT_FILE.exists():
        prompt_data = load_json(PROMPT_FILE)

    prompt_data["test_generation"] = {
        "task": "Automatic validation test generation",
        "model": MODEL_NAME,
        "test_prompt_template": (
            "Generate at least one validation test per requirement. "
            "Each test must include test_id, requirement_id, scenario, steps, and expected_result."
        ),
    }

    save_json(PROMPT_FILE, prompt_data)


def main() -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in environment.")

    spec_content = load_text(SPEC_FILE)
    requirements = parse_spec_markdown(spec_content)

    if not requirements:
        raise ValueError("No requirements found in spec/spec_auto.md")

    client = Groq(api_key=api_key)

    print("Generating automated validation tests...")
    tests = generate_tests(client, requirements)

    validate_tests(tests, requirements)
    save_json(TESTS_FILE, {"tests": tests})

    update_prompt_record()

    print(f"Saved tests to {TESTS_FILE}")
    print(f"Updated prompts in {PROMPT_FILE}")


if __name__ == "__main__":
    main()