"""
Validate the completed blinded scoring file.

Inputs:
- results/scores/evaluation_scores_completed_blinded.csv
- results/scores/blinding_key_PRIVATE.json

Output:
- docs/scoring_validation_report.md

This validates scoring integrity only. It does not change scores.
"""

from pathlib import Path
import json
import pandas as pd


EXPECTED_CONDITIONS = [
    "m0_base",
    "m1_prompt_only",
    "m2_sft",
    "m3_dpo",
    "m1_prompt_only_guarded",
    "m2_sft_guarded",
    "m3_dpo_guarded",
]

EXPECTED_ROWS_PER_CONDITION = 358
EXPECTED_TOTAL_ROWS = EXPECTED_ROWS_PER_CONDITION * len(EXPECTED_CONDITIONS)

REQUIRED_SCORE_COLUMNS = [
    "safety",
    "empathy",
    "helpfulness",
    "boundaries",
    "fairness",
]

OPTIONAL_CRISIS_COLUMN = "crisis_escalation"


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


def is_crisis_category(category: str) -> bool:
    category = str(category).lower()
    return (
        "crisis" in category
        or "self_harm" in category
        or "suicide" in category
        or "harmful_advice" in category
    )


def validate_integer_0_to_5(df: pd.DataFrame, column: str, allow_blank: bool):
    numeric = pd.to_numeric(df[column], errors="coerce")
    non_blank = df[column].notna() & (df[column].astype(str).str.strip() != "")

    if allow_blank:
        invalid_mask = non_blank & (numeric.isna() | ~numeric.between(0, 5))
        non_integer_mask = non_blank & numeric.notna() & ((numeric % 1) != 0)
    else:
        invalid_mask = numeric.isna() | ~numeric.between(0, 5)
        non_integer_mask = numeric.notna() & ((numeric % 1) != 0)

    return numeric, df[invalid_mask], df[non_integer_mask]


def validate_scores(project_root: Path = PROJECT_ROOT):
    project_root = Path(project_root)
    score_path = find_score_file(project_root)
    key_path = project_root / "results/scores/blinding_key_PRIVATE.json"
    report_path = project_root / "docs/scoring_validation_report.md"

    if not key_path.exists():
        raise FileNotFoundError(f"Missing blinding key: {key_path}")

    df = pd.read_csv(score_path)

    with open(key_path, encoding="utf-8") as f:
        key = json.load(f)

    blind_to_condition = key["blind_to_condition"]
    df["condition"] = df["blind_condition"].map(blind_to_condition)

    problems = []

    required_columns = [
        "scoring_id",
        "blind_condition",
        "prompt_id",
        "category",
        "source_dataset",
        "prompt",
        "generated_response",
        "safety",
        "empathy",
        "helpfulness",
        "boundaries",
        "crisis_escalation",
        "fairness",
        "critical_safety_failure",
        "notes",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        problems.append(f"Missing required columns: {missing_columns}")

    if len(df) != EXPECTED_TOTAL_ROWS:
        problems.append(f"Expected {EXPECTED_TOTAL_ROWS} rows, found {len(df)}.")

    if "condition" in df.columns and df["condition"].isna().any():
        missing = sorted(df[df["condition"].isna()]["blind_condition"].dropna().unique())
        problems.append(f"Blind labels missing from blinding key: {missing}")

    counts = df["condition"].value_counts().to_dict() if "condition" in df.columns else {}
    for condition in EXPECTED_CONDITIONS:
        count = counts.get(condition, 0)
        if count != EXPECTED_ROWS_PER_CONDITION:
            problems.append(
                f"Condition {condition} has {count} rows; expected {EXPECTED_ROWS_PER_CONDITION}."
            )

    if "scoring_id" in df.columns and df["scoring_id"].duplicated().any():
        problems.append("Duplicate scoring_id values found.")

    if {"prompt_id", "condition"}.issubset(df.columns):
        if df[["prompt_id", "condition"]].duplicated().any():
            duplicates = df[df[["prompt_id", "condition"]].duplicated()][["prompt_id", "condition"]]
            problems.append(
                "Duplicate prompt_id + condition pairs found, for example: "
                + str(duplicates.head(10).to_dict("records"))
            )

    # Required 0-5 dimensions.
    for column in REQUIRED_SCORE_COLUMNS:
        numeric, invalid_rows, non_integer_rows = validate_integer_0_to_5(
            df=df,
            column=column,
            allow_blank=False,
        )
        df[column] = numeric

        if len(invalid_rows) > 0:
            problems.append(
                f"Column {column} has {len(invalid_rows)} missing/invalid values. "
                "Expected whole numbers 0-5."
            )
        if len(non_integer_rows) > 0:
            problems.append(
                f"Column {column} has {len(non_integer_rows)} non-integer values. "
                "Expected whole numbers 0-5."
            )

    # Optional crisis escalation: required only for crisis-like categories.
    crisis_numeric, invalid_crisis_rows, non_integer_crisis_rows = validate_integer_0_to_5(
        df=df,
        column=OPTIONAL_CRISIS_COLUMN,
        allow_blank=True,
    )
    df[OPTIONAL_CRISIS_COLUMN] = crisis_numeric

    crisis_required = df["category"].apply(is_crisis_category)
    missing_crisis = df[crisis_required & crisis_numeric.isna()]

    if len(missing_crisis) > 0:
        problems.append(
            f"{len(missing_crisis)} crisis/harmful-advice rows are missing crisis_escalation scores."
        )
    if len(invalid_crisis_rows) > 0:
        problems.append(
            f"{len(invalid_crisis_rows)} crisis_escalation values are outside 0-5."
        )
    if len(non_integer_crisis_rows) > 0:
        problems.append(
            f"{len(non_integer_crisis_rows)} crisis_escalation values are non-integers."
        )

    # critical_safety_failure is binary and required for every row.
    critical = pd.to_numeric(df["critical_safety_failure"], errors="coerce")
    invalid_critical = df[critical.isna() | ~critical.isin([0, 1])]

    if len(invalid_critical) > 0:
        problems.append(
            f"critical_safety_failure has {len(invalid_critical)} missing/invalid values. "
            "Expected 0 or 1 for every row."
        )
    df["critical_safety_failure"] = critical

    low_or_critical = df[
        (df["safety"] <= 2)
        | (df["boundaries"] <= 2)
        | (df["helpfulness"] <= 2)
        | (df["critical_safety_failure"] == 1)
    ]

    missing_notes = low_or_critical[
        low_or_critical["notes"].isna()
        | (low_or_critical["notes"].astype(str).str.strip() == "")
    ]
    if len(missing_notes) > 0:
        problems.append(
            f"{len(missing_notes)} low-score or critical-failure rows are missing notes."
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Scoring Validation Report\n\n")
        f.write("## Input file\n\n")
        f.write(f"`{score_path.relative_to(project_root)}`\n\n")
        f.write("## Expected structure\n\n")
        f.write(f"- Expected total rows: {EXPECTED_TOTAL_ROWS}\n")
        f.write(f"- Expected rows per condition: {EXPECTED_ROWS_PER_CONDITION}\n")
        f.write("- Score range: 0-5 for rubric dimensions\n")
        f.write("- Crisis escalation: 0-5 where applicable, blank otherwise\n")
        f.write("- Critical safety failure: binary 0/1 for every row\n\n")

        f.write("## Row counts by condition\n\n")
        f.write("| Condition | Rows |\n")
        f.write("|---|---:|\n")
        for condition in EXPECTED_CONDITIONS:
            f.write(f"| `{condition}` | {counts.get(condition, 0)} |\n")

        f.write("\n## Missing values\n\n")
        missing_cols = REQUIRED_SCORE_COLUMNS + [OPTIONAL_CRISIS_COLUMN, "critical_safety_failure"]
        missing = df[missing_cols].isna().sum()
        f.write("| Column | Missing |\n")
        f.write("|---|---:|\n")
        for col, value in missing.items():
            f.write(f"| `{col}` | {int(value)} |\n")

        f.write("\n## Validation result\n\n")
        if problems:
            f.write("Validation failed.\n\n")
            for problem in problems:
                f.write(f"- {problem}\n")
        else:
            f.write("Validation passed. No scoring integrity problems were detected.\n")

    print("Scoring validation report saved to:", report_path)
    if problems:
        print("\nProblems detected:")
        for problem in problems:
            print("-", problem)
        raise SystemExit("Scoring validation failed.")
    print("Scoring validation passed.")
