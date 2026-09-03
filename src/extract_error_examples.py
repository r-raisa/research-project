"""
Extract candidate examples for qualitative error analysis.

Inputs:
- results/scores/evaluation_scores_completed_blinded.csv
- results/scores/blinding_key_PRIVATE.json

Output:
- docs/error_analysis_candidates.md
"""

from pathlib import Path
import json
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def find_score_file(project_root: Path) -> Path:
    candidates = [
        project_root / "results/scores/evaluation_scores_completed_blinded.csv",
        project_root / "results/scores/evaluation_completed_scores_blinded.csv",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("Could not find completed scoring CSV.")


def extract_error_examples(project_root: Path = PROJECT_ROOT):
    project_root = Path(project_root)
    score_path = find_score_file(project_root)
    key_path = project_root / "results/scores/blinding_key_PRIVATE.json"
    out_path = project_root / "docs/error_analysis_candidates.md"

    df = pd.read_csv(score_path)
    with open(key_path, encoding="utf-8") as f:
        key = json.load(f)

    df["condition"] = df["blind_condition"].map(key["blind_to_condition"])

    numeric_cols = [
        "safety",
        "empathy",
        "helpfulness",
        "boundaries",
        "crisis_escalation",
        "fairness",
        "critical_safety_failure",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    candidates = df[
        (df["critical_safety_failure"] == 1)
        | (df["safety"] <= 2)
        | (df["boundaries"] <= 2)
        | (df["helpfulness"] <= 2)
        | (df["empathy"] <= 2)
        | (df["fairness"] <= 2)
    ].copy()

    candidates = candidates.sort_values(
        by=["critical_safety_failure", "safety", "boundaries", "helpfulness", "empathy", "fairness"],
        ascending=[False, True, True, True, True, True],
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Error Analysis Candidates\n\n")
        f.write(
            "These examples were selected because they had critical safety failures "
            "or low safety, boundary, helpfulness, empathy, or fairness scores. "
            "Use them to complete `docs/error_analysis.md`.\n\n"
        )

        for i, (_, row) in enumerate(candidates.head(50).iterrows(), start=1):
            f.write(f"## Candidate {i}\n\n")
            f.write("| Field | Value |\n")
            f.write("|---|---|\n")
            f.write(f"| Prompt ID | `{row.get('prompt_id')}` |\n")
            f.write(f"| Category | `{row.get('category')}` |\n")
            f.write(f"| Condition | `{row.get('condition')}` |\n")
            f.write(f"| Safety | {row.get('safety')} |\n")
            f.write(f"| Empathy | {row.get('empathy')} |\n")
            f.write(f"| Helpfulness | {row.get('helpfulness')} |\n")
            f.write(f"| Boundaries | {row.get('boundaries')} |\n")
            f.write(f"| Crisis escalation | {row.get('crisis_escalation')} |\n")
            f.write(f"| Fairness | {row.get('fairness')} |\n")
            f.write(f"| Critical safety failure | {row.get('critical_safety_failure')} |\n")
            f.write(f"| Notes | {row.get('notes')} |\n\n")

            f.write("Prompt:\n\n")
            f.write("```text\n")
            f.write(str(row.get("prompt")).strip() + "\n")
            f.write("```\n\n")

            f.write("Generated response:\n\n")
            f.write("```text\n")
            f.write(str(row.get("generated_response")).strip() + "\n")
            f.write("```\n\n")

            f.write("Analysis to write:\n\n")
            f.write("```text\n")
            f.write("[Explain what failed, why it matters, and how it relates to the rubric.]\n")
            f.write("```\n\n")

    print("Saved error-analysis candidates to:", out_path)
