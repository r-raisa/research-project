"""
Data pipeline functions for the LLM therapy post-training project.
"""

from pathlib import Path
from collections import Counter
import json
import re

from datasets import load_dataset, load_from_disk

from src.utils import (
    load_yaml,
    read_jsonl,
    write_jsonl,
    resolve_project_path,
    normalise_for_dedup,
)


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------


def get_project_dirs(project_root):
    """Return the standard project directories used by the data pipeline."""
    project_root = Path(project_root)

    dirs = {
        "root": project_root,
        "configs": project_root / "configs",
        "raw": project_root / "data" / "raw",
        "processed": project_root / "data" / "processed",
        "splits": project_root / "data" / "splits",
        "docs": project_root / "docs",
        "results": project_root / "results",
    }

    return dirs


def ensure_project_dirs(project_root):
    """Create the core directories if they do not already exist."""
    dirs = get_project_dirs(project_root)

    for key in ["raw", "processed", "splits", "docs"]:
        dirs[key].mkdir(parents=True, exist_ok=True)

    return dirs


# ---------------------------------------------------------------------------
# Public dataset download and inspection
# ---------------------------------------------------------------------------


def download_data(project_root):
    """
    Download Hugging Face datasets listed under `datasets:` in data_config.yaml.
    """
    from datasets import load_dataset
    dirs = ensure_project_dirs(project_root)
    config_path = dirs["configs"] / "data_config.yaml"
    config = load_yaml(config_path)

    datasets_config = config.get("datasets", {})

    if not datasets_config:
        print("No downloadable datasets found in configs/data_config.yaml under 'datasets:'.")
        return

    for dataset_name, dataset_info in datasets_config.items():
        # A blank YAML entry such as `empathetic_dialogues:` becomes None.
        # Skipping it gives a clearer error than crashing with AttributeError.
        if dataset_info is None:
            print(f"Skipping {dataset_name}: no dataset information found in config.")
            continue

        if not dataset_info.get("use", True):
            print(f"Skipping {dataset_name}: use is set to false.")
            continue

        hf_id = dataset_info.get("hf_id")
        if not hf_id:
            print(f"Skipping {dataset_name}: missing hf_id in config.")
            continue

        print(f"\nDownloading {dataset_name} from {hf_id}")

        try:
            ds = load_dataset(hf_id)
        except Exception as e:
            print(f"FAILED to download {dataset_name} from {hf_id}")
            print(f"Error: {e}")
            continue

        save_path = dirs["raw"] / dataset_name
        ds.save_to_disk(str(save_path))

        info = {
            "dataset_name": dataset_name,
            "hf_id": hf_id,
            "splits": list(ds.keys()),
            "num_rows": {split: len(ds[split]) for split in ds.keys()},
            "columns": {split: ds[split].column_names for split in ds.keys()},
            "purpose": dataset_info.get("purpose", ""),
        }

        info_path = dirs["raw"] / f"{dataset_name}_info.json"
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

        print(f"Saved {dataset_name} to {save_path}")
        print(f"Saved dataset info to {info_path}")


def load_existing_observations(audit_path):
    """
    Preserve manually written audit observations before regenerating data_audit.md.
    """
    audit_path = Path(audit_path)
    observations = {}

    if not audit_path.exists():
        return observations

    text = audit_path.read_text(encoding="utf-8")
    sections = re.split(r"\n## ", text)

    for section in sections[1:]:
        lines = section.split("\n")
        dataset_name = lines[0].strip()

        match = re.search(
            r"### (Dataset Observations|Planned use)\n(.*)",
            section,
            flags=re.DOTALL,
        )

        if match:
            observations[dataset_name] = match.group(2).strip()

    return observations


def inspect_data(project_root, num_examples=2):
    """
    Inspect downloaded datasets
    """
    from datasets import load_from_disk
    dirs = ensure_project_dirs(project_root)
    raw_dir = dirs["raw"]
    audit_path = dirs["docs"] / "data_audit.md"

    existing_observations = load_existing_observations(audit_path)

    print(f"Looking for datasets in: {raw_dir}")

    if not raw_dir.exists():
        print("ERROR: data/raw does not exist.")
        return

    dataset_dirs = [p for p in raw_dir.iterdir() if p.is_dir()]
    print(f"Found dataset folders: {[p.name for p in dataset_dirs]}")

    audit_lines = []
    audit_lines.append("# Data audit\n")
    audit_lines.append("This file records the datasets downloaded and inspected for the project.\n")

    if not dataset_dirs:
        audit_lines.append("\nNo dataset folders were found in `data/raw/`.\n")

    for dataset_path in dataset_dirs:
        dataset_name = dataset_path.name

        print("\n" + "=" * 80)
        print(f"Inspecting {dataset_name}")
        print("=" * 80)

        try:
            ds = load_from_disk(str(dataset_path))
        except Exception as e:
            print(f"Could not load {dataset_name}: {e}")
            audit_lines.append(f"\n## {dataset_name}\n")
            audit_lines.append(f"- ERROR: Could not load dataset: `{e}`\n")
            continue

        audit_lines.append(f"\n## {dataset_name}\n")
        audit_lines.append(f"- Local path: `{dataset_path}`\n")
        audit_lines.append(f"- Splits: {list(ds.keys())}\n")

        for split in ds.keys():
            split_data = ds[split]

            print(f"\nSplit: {split}")
            print(f"Rows: {len(split_data)}")
            print(f"Columns: {split_data.column_names}")

            audit_lines.append(f"\n### Split: {split}\n")
            audit_lines.append(f"- Rows: {len(split_data)}\n")
            audit_lines.append(f"- Columns: `{split_data.column_names}`\n")

            for i in range(min(num_examples, len(split_data))):
                example = split_data[i]
                audit_lines.append(f"\n#### Example {i}\n")

                print(f"\nExample {i}:")
                for key, value in example.items():
                    preview = str(value)
                    if len(preview) > 500:
                        preview = preview[:500] + "..."

                    print(f"{key}: {preview}")
                    audit_lines.append(f"- `{key}`: {preview}\n")

        audit_lines.append("\n### Dataset Observations\n")
        saved = existing_observations.get(dataset_name, "")
        if saved:
            audit_lines.append(saved + "\n")
        else:
            audit_lines.append("- To be confirmed after manual inspection.\n")

    failed = [line for line in audit_lines if "ERROR" in line]
    if failed:
        print("\nWARNING: The following datasets failed to load:")
        for msg in failed:
            print(" ", msg.strip())

    with open(audit_path, "w", encoding="utf-8") as f:
        f.write("\n".join(audit_lines))

    print(f"\nSaved audit to: {audit_path}")


# ---------------------------------------------------------------------------
# SyntheticSafety validation and integration
# ---------------------------------------------------------------------------


def get_synthetic_safety_config(project_root):
    """Read the synthetic_safety data."""
    dirs = ensure_project_dirs(project_root)
    config = load_yaml(dirs["configs"] / "data_config.yaml")
    return config.get("synthetic_safety", {})


def get_synthetic_safety_path(project_root):
    """Resolve the SyntheticSafety JSONL path"""
    synthetic_config = get_synthetic_safety_config(project_root)
    relative_path = synthetic_config.get(
        "path",
        "data/processed/synthetic_safety_prompts.jsonl",
    )
    return resolve_project_path(project_root, relative_path)


def validate_synthetic_safety_dataset(project_root, return_rows=False):
    """
    Validate the manually created SyntheticSafety dataset.

    This validates the dataset before it enters the main prompt pool.
    """
    path = get_synthetic_safety_path(project_root)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find SyntheticSafety file at {path}. "
            "Check configs/data_config.yaml and the file location."
        )

    required_fields = [
        "prompt_id",
        "source_dataset",
        "source_id",
        "source_split",
        "prompt_text",
        "category",
        "severity",
        "risk_type",
        "requires_escalation",
        "requires_refusal",
        "boundary_issue",
        "fairness_pair_id",
        "expected_safe_behaviour",
        "intended_use",
        "extraction_method",
        "notes",
    ]

    allowed_categories = {
        "crisis_risk_direct",
        "crisis_risk_ambiguous",
        "harmful_advice",
        "diagnosis_boundary",
        "medication_boundary",
        "privacy_dependence",
        "over_reassurance_trap",
        "bias_fairness",
    }

    allowed_severities = {"low", "medium", "high"}
    boolean_fields = ["requires_escalation", "requires_refusal", "boundary_issue"]

    rows = read_jsonl(path)

    seen_ids = set()
    seen_prompts = set()
    category_counts = {}
    fairness_pairs = {}
    errors = []
    warnings = []

    for line_num, row in enumerate(rows, start=1):
        for field in required_fields:
            if field not in row:
                errors.append(f"Line {line_num}: missing required field '{field}'")

        prompt_id = row.get("prompt_id")
        prompt_text = row.get("prompt_text", "").strip()
        category = row.get("category")
        severity = row.get("severity")
        fairness_pair_id = row.get("fairness_pair_id")

        if prompt_id in seen_ids:
            errors.append(f"Line {line_num}: duplicate prompt_id '{prompt_id}'")
        seen_ids.add(prompt_id)

        normalised_prompt = normalise_for_dedup(prompt_text)
        if normalised_prompt in seen_prompts:
            errors.append(f"Line {line_num}: duplicate prompt_text '{prompt_text}'")
        seen_prompts.add(normalised_prompt)

        if row.get("source_dataset") != "synthetic_safety":
            errors.append(f"Line {line_num}: source_dataset should be 'synthetic_safety'")

        if category not in allowed_categories:
            errors.append(f"Line {line_num}: unknown category '{category}'")

        if severity not in allowed_severities:
            errors.append(f"Line {line_num}: invalid severity '{severity}'")

        if len(prompt_text) < 15:
            errors.append(f"Line {line_num}: prompt_text is too short")

        if len(prompt_text) > 500:
            errors.append(f"Line {line_num}: prompt_text is too long")

        for field in boolean_fields:
            if not isinstance(row.get(field), bool):
                errors.append(f"Line {line_num}: field '{field}' should be true or false")

        category_counts[category] = category_counts.get(category, 0) + 1

        if category == "bias_fairness":
            if not fairness_pair_id:
                errors.append(f"Line {line_num}: bias_fairness prompt needs fairness_pair_id")
            else:
                fairness_pairs.setdefault(fairness_pair_id, []).append(prompt_id)
        else:
            if fairness_pair_id is not None:
                errors.append(
                    f"Line {line_num}: non-fairness prompt should have fairness_pair_id set to null"
                )

        expected = str(row.get("expected_safe_behaviour", "")).lower()

        # Catch a specific inconsistency: lower-risk refusal prompts
        # should not instruct escalation unless the metadata requires escalation.
        if row.get("requires_escalation") is False and "escalat" in expected:
            errors.append(
                f"Line {line_num}: requires_escalation=false but "
                "expected_safe_behaviour mentions escalation"
            )

    for pair_id, prompt_ids in fairness_pairs.items():
        if len(prompt_ids) != 2:
            errors.append(
                f"Fairness pair '{pair_id}' has {len(prompt_ids)} prompts. "
                "Each fairness pair should contain exactly 2 prompts."
            )

    synthetic_config = get_synthetic_safety_config(project_root)

    expected_total = synthetic_config.get("expected_total")
    if expected_total is not None and len(rows) != expected_total:
        warnings.append(f"Expected {expected_total} synthetic prompts, but found {len(rows)}.")

    expected_categories = synthetic_config.get("expected_categories", {})
    for category, expected_count in expected_categories.items():
        actual_count = category_counts.get(category, 0)
        if actual_count != expected_count:
            warnings.append(
                f"Expected {expected_count} prompts for {category}, but found {actual_count}."
            )

    print("\nSyntheticSafety validation summary")
    print("=" * 40)
    print(f"File: {path}")
    print(f"Total prompts: {len(rows)}")

    print("\nCategory counts:")
    for category in sorted(category_counts):
        print(f"- {category}: {category_counts[category]}")

    print(f"\nFairness pairs: {len(fairness_pairs)}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print(f"- {error}")
        raise ValueError("SyntheticSafety validation failed.")

    print("\nSyntheticSafety dataset passed validation.")

    if return_rows:
        return rows

    return None


def create_synthetic_safety_report(project_root):
    """Create docs/synthetic_safety_report.md from the validated JSONL file."""
    dirs = ensure_project_dirs(project_root)
    rows = validate_synthetic_safety_dataset(project_root, return_rows=True)

    category_counts = Counter(row["category"] for row in rows)
    severity_counts = Counter(row["severity"] for row in rows)
    risk_type_counts = Counter(row["risk_type"] for row in rows)

    fairness_pair_ids = {
        row["fairness_pair_id"]
        for row in rows
        if row.get("category") == "bias_fairness"
    }

    report_path = dirs["docs"] / "synthetic_safety_report.md"

    lines = []
    lines.append("# SyntheticSafety dataset report\n")
    lines.append("This report documents the manually created SyntheticSafety prompt dataset.\n")

    lines.append("## Dataset location\n")
    lines.append(f"- Path: `{get_synthetic_safety_path(project_root)}`\n")

    lines.append("## Purpose\n")
    lines.append(
        "SyntheticSafety provides controlled prompts for evaluating safety-critical "
        "behaviour in therapy-style language model responses. It covers crisis risk, "
        "harmful-advice refusal, diagnosis boundaries, medication boundaries, "
        "privacy/dependence boundaries, over-reassurance, and bias/fairness.\n"
    )

    lines.append("## Total prompts\n")
    lines.append(f"- Total: {len(rows)}\n")

    lines.append("## Category counts\n")
    for category, count in sorted(category_counts.items()):
        lines.append(f"- `{category}`: {count}")

    lines.append("\n## Severity counts\n")
    for severity, count in sorted(severity_counts.items()):
        lines.append(f"- `{severity}`: {count}")

    lines.append("\n## Risk type counts\n")
    for risk_type, count in sorted(risk_type_counts.items()):
        lines.append(f"- `{risk_type}`: {count}")

    lines.append("\n## Fairness pairs\n")
    lines.append(f"- Matched fairness pairs: {len(fairness_pair_ids)}")

    lines.append("\n## Notes\n")
    lines.append(
        "- Prompts are synthetic and do not contain real patient data.\n"
        "- Crisis prompts are non-graphic and test escalation behaviour without harmful detail.\n"
        "- Bias/fairness prompts use matched pairs so that only one identity or contextual attribute changes within a pair.\n"
        "- The dataset must be split before training so held-out prompts are not seen during post-training.\n"
    )

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nSaved SyntheticSafety report to: {report_path}")


def add_synthetic_safety_to_prompt_pool(project_root):
    """
    Add SyntheticSafety prompts to data/processed/prompt_pool.jsonl.
    """
    dirs = ensure_project_dirs(project_root)
    synthetic_rows = validate_synthetic_safety_dataset(project_root, return_rows=True)

    prompt_pool_path = dirs["processed"] / "prompt_pool.jsonl"

    if prompt_pool_path.exists():
        existing_rows = read_jsonl(prompt_pool_path)
    else:
        existing_rows = []

    kept_rows = [
        row for row in existing_rows
        if row.get("source_dataset") != "synthetic_safety"
    ]

    combined_rows = kept_rows + synthetic_rows
    write_jsonl(combined_rows, prompt_pool_path)

    print("\nPrompt pool updated")
    print("=" * 40)
    print(f"Previous rows: {len(existing_rows)}")
    print(f"Kept non-synthetic rows: {len(kept_rows)}")
    print(f"Added SyntheticSafety rows: {len(synthetic_rows)}")
    print(f"New total rows: {len(combined_rows)}")
    print(f"Saved to: {prompt_pool_path}")


def prepare_synthetic_safety(project_root):
    """
    Full SyntheticSafety preparation stage.

    Runs:
    1. validation
    2. report creation
    3. prompt-pool integration
    """
    validate_synthetic_safety_dataset(project_root)
    create_synthetic_safety_report(project_root)
    add_synthetic_safety_to_prompt_pool(project_root)
