"""generates structured specs from personas"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
PERSONAS_FILE = ROOT / "personas" / "personas_auto.json"
OUTPUT_FILE = ROOT / "spec" / "spec_auto.md"
PROMPT_FILE = ROOT / "prompts" / "prompt_auto.json"

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
MIN_REQUIREMENTS = 10


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(content)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_spec_prompt(personas: list[dict]) -> str:
    persona_lines = []

    for persona in personas:
        persona_lines.append(
            {
                "id": persona.get("id", ""),
                "name": persona.get("name", ""),
                "description": persona.get("description", ""),
                "goals": persona.get("goals", []),
                "pain_points": persona.get("pain_points", []),
                "context": persona.get("context", ""),
                "source_review_group": persona.get("source_review_group", ""),
            }
        )

    personas_json = json.dumps(persona_lines, indent=2, ensure_ascii=False)

    return f"""
Generate at least {MIN_REQUIREMENTS} functional software requirements from the personas below.

Rules:
1. Generate grounded requirements only from the provided personas.
2. Do not invent unsupported features.
3. Each requirement must be testable and written clearly.
4. Use requirement IDs in the format FR_auto_1, FR_auto_2, FR_auto_3, and so on.
5. Each requirement must include:
   - requirement_id
   - description
   - source_persona
   - traceability
   - acceptance_criteria
6. The traceability field must reference the persona's source review group.
7. Acceptance criteria must use a Given When Then style.
8. Return valid JSON only in exactly this format:

{{
  "requirements": [
    {{
      "requirement_id": "FR_auto_1",
      "description": "The system shall ...",
      "source_persona": "Persona Name",
      "traceability": "Derived from review group G1",
      "acceptance_criteria": "Given ..., When ..., Then ..."
    }}
  ]
}}

Personas:
{personas_json}
""".strip()


def generate_requirements(client: Groq, personas: list[dict]) -> list[dict]:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are helping with software requirements engineering. "
                    "Generate clear, testable functional requirements from personas. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": build_spec_prompt(personas),
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
        max_completion_tokens=4000,
    )

    data = json.loads(response.choices[0].message.content)
    requirements = data.get("requirements", [])

    if len(requirements) < MIN_REQUIREMENTS:
        raise ValueError(
            f"Expected at least {MIN_REQUIREMENTS} requirements, got {len(requirements)}"
        )

    return requirements


def validate_requirement(requirement: dict, expected_number: int) -> None:
    required_fields = [
        "requirement_id",
        "description",
        "source_persona",
        "traceability",
        "acceptance_criteria",
    ]

    missing = [field for field in required_fields if field not in requirement]
    if missing:
        raise ValueError(f"Requirement missing fields: {missing}")

    expected_id = f"FR_auto_{expected_number}"
    if requirement["requirement_id"] != expected_id:
        raise ValueError(
            f"Expected requirement_id {expected_id}, got {requirement['requirement_id']}"
        )

    description = requirement["description"].strip()
    if not description.startswith("The system shall"):
        raise ValueError(
            f"{requirement['requirement_id']} description must start with 'The system shall'"
        )

    acceptance = requirement["acceptance_criteria"]
    normalized = acceptance.lower()
    if "given" not in normalized or "when" not in normalized or "then" not in normalized:
        raise ValueError(
            f"{requirement['requirement_id']} acceptance criteria must use Given When Then"
        )


def requirements_to_markdown(requirements: list[dict]) -> str:
    sections = []

    for req in requirements:
        section = (
            f"# Requirement ID: {req['requirement_id']}\n"
            f"- Description: [{req['description']}]\n\n"
            f"- Source Persona: [{req['source_persona']}]\n"
            f"- Traceability: [{req['traceability']}]\n"
            f"- Acceptance Criteria: [{req['acceptance_criteria']}]\n"
        )
        sections.append(section)

    return "\n".join(sections).strip() + "\n"


def update_prompt_record() -> None:
    prompt_data = {}
    if PROMPT_FILE.exists():
        prompt_data = load_json(PROMPT_FILE)

    prompt_data["spec_generation"] = {
        "task": "Automatic specification generation",
        "model": MODEL_NAME,
        "spec_prompt_template": (
            "Generate at least 10 grounded and testable functional requirements from automated personas. "
            "Each requirement must include requirement_id, description, source_persona, traceability, "
            "and acceptance_criteria in Given When Then form."
        ),
    }

    save_json(PROMPT_FILE, prompt_data)


def main() -> None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Missing GROQ_API_KEY in environment.")

    personas_data = load_json(PERSONAS_FILE)
    personas = personas_data.get("personas", [])

    if not personas:
        raise ValueError("No personas found in personas/personas_auto.json")

    client = Groq(api_key=api_key)

    print("Generating automated specifications...")
    requirements = generate_requirements(client, personas)

    for index, requirement in enumerate(requirements, start=1):
        validate_requirement(requirement, index)

    markdown_output = requirements_to_markdown(requirements)
    save_text(OUTPUT_FILE, markdown_output)

    update_prompt_record()

    print(f"Saved generated specification to {OUTPUT_FILE}")
    print(f"Updated prompts in {PROMPT_FILE}")


if __name__ == "__main__":
    main()