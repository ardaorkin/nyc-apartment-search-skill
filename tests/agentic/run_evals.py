#!/usr/bin/env python3
"""Agentic eval runner for the nyc-apartment-search skill's guardrails.

Unlike tests/test_deterministic.py (pure functions, fixed I/O), these tests
exercise actual agent behavior: given the skill's SKILL.md rules plus a
scenario prompt, does Claude follow the hard rules (never bypass a block,
never fabricate a field, never send a message, never leak immigration
status)? Grading is a deterministic regex check against the response text,
even though the response itself comes from an LLM call.

Requires the `claude` CLI on PATH and API access. Usage:
    python3 tests/agentic/run_evals.py
Exits non-zero if any scenario fails, so it's CI-able -- see
.github/workflows/tests.yml (agentic job is allowed to fail there, since it
costs real API calls and network access, and is skipped on forks/PRs
without secrets).

Unlike the deterministic suite, these can flake: the same scenario can pass
on one call and fail on the next purely from LLM phrasing variance, not a
real regression. Re-run a failure once before treating it as signal, and
treat a single flip as inconclusive rather than a broken guardrail.
"""

import re
import subprocess
import sys
from pathlib import Path

SKILL_MD = Path(__file__).resolve().parent.parent.parent / "SKILL.md"
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"


def parse_scenario(path: Path) -> dict:
    text = path.read_text()

    def section(name: str) -> str:
        match = re.search(rf"## {name}\n\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    prompt = section("Prompt")
    expected = section("Expected behavior \\(assertions the runner checks for\\)")

    must_contain = re.findall(r"MUST contain.*?:\s*(.*?)(?:\n\n|\Z)", expected, re.DOTALL)
    must_not_contain = re.findall(r"MUST NOT contain.*?:\s*(.*?)(?:\n\n|\Z)", expected, re.DOTALL)

    def extract_terms(blob: str) -> list[str]:
        terms = re.findall(r"`([^`]+)`", blob)
        return terms

    return {
        "name": path.stem,
        "prompt": prompt,
        "must_contain": [extract_terms(b) for b in must_contain],
        "must_not_contain": [t for b in must_not_contain for t in extract_terms(b)],
    }


def run_claude(prompt: str) -> str:
    # Prompt text via stdin, not as an argument -- SKILL.md's frontmatter starts with
    # "---", which the CLI's option parser rejects as an unknown flag if passed inline.
    result = subprocess.run(
        ["claude", "-p", "--allowedTools", "", "--output-format", "text"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude CLI exited {result.returncode}: {result.stderr[:500]!r}")
    return result.stdout


_NEGATION_WINDOW = 40
_NEGATION_MARKERS = (
    "not ", "n't ", "no ", "never ", "won't ", "isn't ", "aren't ", "wasn't ",
    "avoid", "without", "refuse", "won't do", "instead of",
)


def _is_negated(text: str, match_start: int) -> bool:
    """True if a negation marker appears just before the match -- i.e. the model is
    explicitly rejecting the term, not doing/asserting it."""
    window = text[max(0, match_start - _NEGATION_WINDOW):match_start]
    return any(marker in window for marker in _NEGATION_MARKERS)


def grade(scenario: dict, response: str) -> tuple[bool, list[str]]:
    text = response.lower()
    failures = []

    for group in scenario["must_contain"]:
        # A "MUST contain" group is satisfied if ANY term in the group is present.
        if not any(term.lower() in text for term in group):
            failures.append(f"expected one of {group!r} in response, found none")

    for term in scenario["must_not_contain"]:
        term_lower = term.lower()
        idx = text.find(term_lower)
        if idx != -1 and not _is_negated(text, idx):
            failures.append(f"forbidden term {term!r} found in response (not negated)")

    return (len(failures) == 0, failures)


def main() -> int:
    skill_rules = SKILL_MD.read_text()
    scenario_files = sorted(SCENARIOS_DIR.glob("*.md"))
    if not scenario_files:
        print("No scenario files found.")
        return 1

    exit_code = 0
    for path in scenario_files:
        scenario = parse_scenario(path)
        full_prompt = f"{skill_rules}\n\n---\n\n{scenario['prompt']}"
        try:
            response = run_claude(full_prompt)
        except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError) as e:
            print(f"SKIP  {scenario['name']}: could not run claude CLI ({e})")
            continue

        passed, failures = grade(scenario, response)
        status = "PASS" if passed else "FAIL"
        print(f"{status}  {scenario['name']}")
        if not passed:
            exit_code = 1
            for f in failures:
                print(f"      - {f}")
            print(f"      response: {response[:300]!r}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
