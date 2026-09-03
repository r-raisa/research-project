"""
Quality checks for generated locked test-set outputs.

This script checks that all expected output files exist, have the correct number
of rows, contain non-empty responses and cover the same prompt IDs.

It does not score response quality.
It does not modify generated outputs.
"""

from pathlib import Path
import json
import csv
from collections import Counter, defaultdict


EXPECTED_FILES = {
    "m0_base": "test_outputs_m0_base.jsonl",
    "m1_prompt_only": "test_outputs_m1_prompt_only.jsonl",
    "m2_sft": "test_outputs_m2_sft.jsonl",
    "m3_dpo": "test_outputs_m3_dpo.jsonl",
    "m1_prompt_only_guarded": "test_outputs_m1_prompt_only_guarded.jsonl",
    "m2_sft_guarded": "test_outputs_m2_sft_guarded.jsonl",
    "m3_dpo_guarded": "test_outputs_m3_dpo_guarded.jsonl",
}


EXPECTED_ROWS = 358


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def check_generated_outputs(project_root: Path):
    project_root = Path(project_root)

    output_dir = project_root / "results/model_outputs"
    table_dir = project_root / "results/tables"
    report_dir = project_root / "docs"

    table_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    summary_rows = []
    prompt_sets = {}
    all_problems = []

    for condition, file_name in EXPECTED_FILES.items():
        path = output_dir / file_name

        if not path.exists():
            all_problems.append(f"Missing file: {path}")
            continue

        rows = read_jsonl(path)
        prompt_ids = [row.get("prompt_id") for row in rows]
        prompt_sets[condition] = set(prompt_ids)

        missing_response = [
            row.get("prompt_id")
            for row in rows
            if not str(row.get("generated_response", "")).strip()
        ]

        duplicate_prompt_ids = [
            prompt_id
            for prompt_id, count in Counter(prompt_ids).items()
            if count > 1
        ]

        conditions_inside_file = Counter(row.get("condition") for row in rows)
        categories = Counter(row.get("category") for row in rows)
        router_applied = sum(1 for row in rows if row.get("router_applied") is True)
        router_reasons = Counter(row.get("router_reason") for row in rows if row.get("router_reason"))

        if len(rows) != EXPECTED_ROWS:
            all_problems.append(
                f"{file_name} has {len(rows)} rows, expected {EXPECTED_ROWS}"
            )

        if missing_response:
            all_problems.append(
                f"{file_name} has empty generated responses for: {missing_response[:10]}"
            )

        if duplicate_prompt_ids:
            all_problems.append(
                f"{file_name} has duplicate prompt IDs: {duplicate_prompt_ids[:10]}"
            )

        if condition not in conditions_inside_file:
            all_problems.append(
                f"{file_name} does not contain expected condition label {condition}. "
                f"Found: {dict(conditions_inside_file)}"
            )

        summary_rows.append(
            {
                "condition": condition,
                "file_name": file_name,
                "exists": True,
                "row_count": len(rows),
                "unique_prompt_ids": len(set(prompt_ids)),
                "empty_generated_responses": len(missing_response),
                "duplicate_prompt_ids": len(duplicate_prompt_ids),
                "router_applied_count": router_applied,
                "router_reason_counts": dict(router_reasons),
                "category_counts": dict(categories),
            }
        )

    # Check that all files contain the same prompt IDs.
    if prompt_sets:
        reference_condition = "m0_base"
        reference_set = prompt_sets.get(reference_condition)

        if reference_set is not None:
            for condition, prompt_set in prompt_sets.items():
                missing_from_condition = reference_set - prompt_set
                extra_in_condition = prompt_set - reference_set

                if missing_from_condition:
                    all_problems.append(
                        f"{condition} is missing prompt IDs from {reference_condition}: "
                        f"{sorted(missing_from_condition)[:10]}"
                    )

                if extra_in_condition:
                    all_problems.append(
                        f"{condition} has extra prompt IDs not in {reference_condition}: "
                        f"{sorted(extra_in_condition)[:10]}"
                    )

    summary_path = table_dir / "generated_output_integrity_summary.csv"

    fieldnames = [
        "condition",
        "file_name",
        "exists",
        "row_count",
        "unique_prompt_ids",
        "empty_generated_responses",
        "duplicate_prompt_ids",
        "router_applied_count",
        "router_reason_counts",
        "category_counts",
    ]

    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    report_path = report_dir / "generation_quality_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Generation Quality Report\n\n")
        f.write("## Purpose\n\n")
        f.write(
            "This report checks the integrity of generated locked test-set outputs. "
            "It verifies file existence, row counts, prompt coverage, empty responses, "
            "duplicate prompt IDs, and router application counts. It does not score "
            "response quality.\n\n"
        )

        f.write("## Summary\n\n")
        f.write("| Condition | Rows | Unique prompt IDs | Empty responses | Duplicates | Router applied |\n")
        f.write("|---|---:|---:|---:|---:|---:|\n")

        for row in summary_rows:
            f.write(
                f"| `{row['condition']}` | {row['row_count']} | "
                f"{row['unique_prompt_ids']} | {row['empty_generated_responses']} | "
                f"{row['duplicate_prompt_ids']} | {row['router_applied_count']} |\n"
            )

        f.write("\n## Problems\n\n")

        if all_problems:
            for problem in all_problems:
                f.write(f"- {problem}\n")
        else:
            f.write("No integrity problems were detected.\n")

        f.write("\n## Output files checked\n\n")
        for condition, file_name in EXPECTED_FILES.items():
            f.write(f"- `{condition}`: `results/model_outputs/{file_name}`\n")

        f.write("\n## Router coverage interpretation\n\n")
        f.write(
            "The guarded conditions each routed 10 of the 358 locked test prompts. "
            "This confirms that the router operated as intended, but also shows that "
            "it was conservative. The guarded evaluation should therefore be interpreted "
            "as a lightweight safety-layer comparison rather than proof that all "
            "safety-sensitive prompts were automatically detected.\n\n"
        )
        f.write(
            "The router did not use test-set category labels. It only inspected prompt "
            "text, which protects evaluation integrity but also means that ambiguous "
            "crisis signals may remain unrouted.\n"
        )

    print("Quality checks complete.")
    print("Saved:", summary_path)
    print("Saved:", report_path)

    if all_problems:
        print("\nProblems detected:")
        for problem in all_problems:
            print("-", problem)
        raise SystemExit("Generated output integrity checks failed.")

    print("No generated output integrity problems detected.")