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
    clean_text,
    normalise_for_dedup,
)

# Directory helpers


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


# ---------------------------------------------------------------------------
# Public dataset prompt extraction
# ---------------------------------------------------------------------------


def get_prompt_pool_config(project_root):
    """Read the `prompt_pool:` block from configs/data_config.yaml."""
    dirs = ensure_project_dirs(project_root)
    config = load_yaml(dirs["configs"] / "data_config.yaml")
    return config.get("prompt_pool", {})


def get_prompt_pool_path(project_root):
    """Resolve the output path for the combined prompt pool."""
    config = get_prompt_pool_config(project_root)
    relative_path = config.get("output_path", "data/processed/prompt_pool.jsonl")
    return resolve_project_path(project_root, relative_path)


def get_response_candidates_path(project_root):
    """Resolve the output path for extracted response candidates."""
    config = get_prompt_pool_config(project_root)
    relative_path = config.get(
        "response_candidates_path",
        "data/processed/response_candidates.jsonl",
    )
    return resolve_project_path(project_root, relative_path)


def is_useful_prompt(text, min_chars=25, max_chars=1200):
    """
    Decide whether a piece of text is useful enough to become a prompt. This deliberately removes short greetings and fillers. 
    """
    text = clean_text(text)

    if len(text) < min_chars:
        return False

    if len(text) > max_chars:
        return False

    filler_phrases = {
        "hi",
        "hello",
        "hey",
        "okay",
        "ok",
        "thanks",
        "thank you",
        "yes",
        "no",
        "good morning",
        "good afternoon",
        "good evening",
    }

    if text.lower() in filler_phrases:
        return False

    return True


def infer_prompt_metadata(prompt_text, source_label=None):
    """
    Assign broad category, severity and risk_type from prompt text. Transparent rule-based labelling helper for dataset organisation and stratified splitting.
    """
    text = clean_text(prompt_text).lower()
    source_label = clean_text(source_label).lower()

    crisis_terms = [
        "kill myself",
        "suicide",
        "suicidal",
        "hurt myself",
        "self harm",
        "self-harm",
        "not safe with myself",
        "end my life",
        "can't keep going",
        "cannot keep going",
        "better off without me",
    ]

    medication_terms = [
        "medication",
        "antidepressant",
        "dose",
        "pills",
        "tablet",
        "prescription",
        "doctor prescribed",
    ]

    diagnosis_terms = [
        "diagnose",
        "do i have depression",
        "do i have anxiety",
        "do i have bipolar",
        "do i have ptsd",
        "what disorder",
    ]

    if any(term in text for term in crisis_terms):
        return {
            "category": "crisis_risk",
            "severity": "high",
            "risk_type": "self_harm_risk",
            "requires_escalation": True,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text for term in medication_terms):
        return {
            "category": "medication_boundary",
            "severity": "high",
            "risk_type": "medical_boundary",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": True,
        }

    if any(term in text for term in diagnosis_terms):
        return {
            "category": "diagnosis_boundary",
            "severity": "medium",
            "risk_type": "clinical_boundary",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": True,
        }

    if any(term in text or term in source_label for term in ["anxiety", "anxious", "panic", "worried"]):
        return {
            "category": "anxiety",
            "severity": "medium",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text or term in source_label for term in ["depression", "depressed", "low mood", "sad", "hopeless"]):
        return {
            "category": "low_mood",
            "severity": "medium",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text or term in source_label for term in ["grief", "died", "death", "bereavement", "lost my"]):
        return {
            "category": "grief",
            "severity": "medium",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text or term in source_label for term in ["relationship", "partner", "boyfriend", "girlfriend", "friend", "family"]):
        return {
            "category": "relationship_distress",
            "severity": "medium",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text or term in source_label for term in ["lonely", "alone", "isolated"]):
        return {
            "category": "loneliness",
            "severity": "medium",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    if any(term in text or term in source_label for term in ["job", "work", "academic", "school", "study", "university"]):
        return {
            "category": "everyday_stress",
            "severity": "low",
            "risk_type": "none",
            "requires_escalation": False,
            "requires_refusal": False,
            "boundary_issue": False,
        }

    return {
        "category": "everyday_stress",
        "severity": "low",
        "risk_type": "none",
        "requires_escalation": False,
        "requires_refusal": False,
        "boundary_issue": False,
    }


def make_prompt_row(
    prompt_id,
    source_dataset,
    source_id,
    source_split,
    prompt_text,
    extraction_method,
    source_label=None,
    group_id=None,
    notes="",
):
    """
    Create standard prompt-pool row.
    """
    prompt_text = clean_text(prompt_text)
    metadata = infer_prompt_metadata(prompt_text, source_label=source_label)

    return {
        "prompt_id": prompt_id,
        "source_dataset": source_dataset,
        "source_id": source_id,
        "source_split": source_split,
        "group_id": group_id or source_id,
        "prompt_text": prompt_text,
        "category": metadata["category"],
        "severity": metadata["severity"],
        "risk_type": metadata["risk_type"],
        "requires_escalation": metadata["requires_escalation"],
        "requires_refusal": metadata["requires_refusal"],
        "boundary_issue": metadata["boundary_issue"],
        "fairness_pair_id": None,
        "expected_safe_behaviour": "",
        "intended_use": "candidate",
        "extraction_method": extraction_method,
        "source_label": source_label,
        "notes": notes,
    }


def make_response_candidate_row(
    response_id,
    source_dataset,
    source_id,
    source_split,
    prompt_text,
    response_text,
    candidate_type,
    group_id=None,
    notes="",
):
    """
    Create one response-candidate row.
    """
    return {
        "response_id": response_id,
        "source_dataset": source_dataset,
        "source_id": source_id,
        "source_split": source_split,
        "group_id": group_id or source_id,
        "prompt_text": clean_text(prompt_text),
        "response_text": clean_text(response_text),
        "candidate_type": candidate_type,
        "quality_status": "unchecked",
        "notes": notes,
    }


def extract_counsel_chat(project_root):
    """
    Extract prompts and response candidates from CounselChat.

    - `questionText` becomes the prompt.
    - `answerText` becomes a response candidate only.
    - duplicate questions are deduplicated by normalised question text.
    """
    from datasets import load_from_disk

    dirs = ensure_project_dirs(project_root)
    dataset_path = dirs["raw"] / "counsel_chat"

    if not dataset_path.exists():
        print("CounselChat not found in data/raw/counsel_chat. Skipping.")
        return [], []

    ds = load_from_disk(str(dataset_path))
    split_name = "train"
    split_data = ds[split_name]

    prompt_rows = []
    response_rows = []
    seen_prompts = set()

    for index, row in enumerate(split_data):
        question_id = str(row.get("questionID", index))
        question_text = clean_text(row.get("questionText") or row.get("questionTitle"))
        topic = row.get("topic", "")

        if not is_useful_prompt(question_text):
            continue

        dedup_key = normalise_for_dedup(question_text)
        source_id = f"counsel_chat_{question_id}"
        group_id = source_id

        if dedup_key not in seen_prompts:
            seen_prompts.add(dedup_key)

            prompt_rows.append(
                make_prompt_row(
                    prompt_id=f"counsel_chat_{len(prompt_rows):05d}",
                    source_dataset="counsel_chat",
                    source_id=source_id,
                    source_split=split_name,
                    group_id=group_id,
                    prompt_text=question_text,
                    source_label=topic,
                    extraction_method="questionText",
                    notes="CounselChat questionText extracted as a realistic mental-health-style prompt.",
                )
            )

        answer_text = clean_text(row.get("answerText"))
        if is_useful_prompt(answer_text):
            response_rows.append(
                make_response_candidate_row(
                    response_id=f"counsel_chat_answer_{index:05d}",
                    source_dataset="counsel_chat",
                    source_id=source_id,
                    source_split=split_name,
                    group_id=group_id,
                    prompt_text=question_text,
                    response_text=answer_text,
                    candidate_type="therapist_answer",
                    notes="CounselChat answerText kept as unchecked response candidate, not automatic gold standard.",
                )
            )

    return prompt_rows, response_rows


def parse_esconv_record(text_value):
    """Parse the ESConv JSON stored inside the `text` column."""
    if isinstance(text_value, dict):
        return text_value

    if isinstance(text_value, str):
        try:
            return json.loads(text_value)
        except json.JSONDecodeError:
            return {}

    return {}


def extract_esconv(project_root):
    """
    Extract prompts and response candidates from ESConv.

    - Always extract the `situation` field because it is a clean standalone prompt.
    - Extract only a capped number of meaningful `usr` dialogue turns, because
      extracting every turn makes ESConv dominate the prompt pool.
    - Keep `sys` turns as response candidates paired with the previous useful user turn.
    """
    from datasets import load_from_disk

    dirs = ensure_project_dirs(project_root)
    dataset_path = dirs["raw"] / "esconv"

    if not dataset_path.exists():
        print("ESConv not found in data/raw/esconv. Skipping.")
        return [], []

    config = get_prompt_pool_config(project_root)
    limits = config.get("extraction_limits", {})

    max_conversations = limits.get("esconv_max_conversations", None)
    include_usr_dialog_turns = limits.get("esconv_include_usr_dialog_turns", True)
    max_dialog_turn_prompts = limits.get("esconv_max_dialog_turn_prompts", 500)

    ds = load_from_disk(str(dataset_path))

    prompt_rows = []
    response_rows = []
    seen_prompts = set()

    conversation_count = 0
    dialog_turn_prompt_count = 0

    for split_name in ds.keys():
        split_data = ds[split_name]

        for row_index, row in enumerate(split_data):
            if max_conversations is not None and conversation_count >= max_conversations:
                break

            parsed = parse_esconv_record(row.get("text"))
            if not parsed:
                continue

            conversation_count += 1

            source_id = f"esconv_{split_name}_{row_index:05d}"
            group_id = source_id

            emotion_type = parsed.get("emotion_type", "")
            problem_type = parsed.get("problem_type", "")
            source_label = f"{emotion_type} | {problem_type}".strip(" |")

            # ------------------------------------------------------------
            # Always extract the ESConv situation field
            # ------------------------------------------------------------
            situation = clean_text(parsed.get("situation"))

            if is_useful_prompt(situation):
                dedup_key = normalise_for_dedup(situation)

                if dedup_key not in seen_prompts:
                    seen_prompts.add(dedup_key)

                    prompt_rows.append(
                        make_prompt_row(
                            prompt_id=f"esconv_situation_{len(prompt_rows):05d}",
                            source_dataset="esconv",
                            source_id=source_id,
                            source_split=split_name,
                            group_id=group_id,
                            prompt_text=situation,
                            source_label=source_label,
                            extraction_method="situation",
                            notes=(
                                "ESConv situation field extracted as the cleanest "
                                "standalone emotional-support prompt."
                            ),
                        )
                    )

            # ------------------------------------------------------------
            # Extract a capped number of useful user dialogue turns
            # ------------------------------------------------------------
            previous_user_turn = None

            for turn_index, turn in enumerate(parsed.get("dialog", [])):
                turn_text = clean_text(turn.get("text"))
                speaker = turn.get("speaker")
                strategy = turn.get("strategy", "")

                if speaker == "usr":
                    if is_useful_prompt(turn_text):
                        previous_user_turn = turn_text

                        can_add_dialog_prompt = (
                            include_usr_dialog_turns
                            and (
                                max_dialog_turn_prompts is None
                                or dialog_turn_prompt_count < max_dialog_turn_prompts
                            )
                        )

                        if can_add_dialog_prompt:
                            dedup_key = normalise_for_dedup(turn_text)

                            if dedup_key not in seen_prompts:
                                seen_prompts.add(dedup_key)
                                dialog_turn_prompt_count += 1

                                prompt_rows.append(
                                    make_prompt_row(
                                        prompt_id=f"esconv_usr_{dialog_turn_prompt_count:05d}",
                                        source_dataset="esconv",
                                        source_id=f"{source_id}_usr_{turn_index:02d}",
                                        source_split=split_name,
                                        group_id=group_id,
                                        prompt_text=turn_text,
                                        source_label=source_label,
                                        extraction_method="usr_dialog_turn",
                                        notes=(
                                            "Meaningful ESConv user dialogue turn "
                                            "extracted as a capped supplementary prompt."
                                        ),
                                    )
                                )

                elif speaker == "sys":
                    if previous_user_turn and is_useful_prompt(turn_text):
                        response_rows.append(
                            make_response_candidate_row(
                                response_id=f"esconv_sys_{split_name}_{row_index:05d}_{turn_index:02d}",
                                source_dataset="esconv",
                                source_id=f"{source_id}_sys_{turn_index:02d}",
                                source_split=split_name,
                                group_id=group_id,
                                prompt_text=previous_user_turn,
                                response_text=turn_text,
                                candidate_type="supporter_turn",
                                notes=f"ESConv sys response candidate. Strategy: {strategy}",
                            )
                        )

        if max_conversations is not None and conversation_count >= max_conversations:
            break

    print("\nESConv extraction summary")
    print("=" * 40)
    print(f"Conversations processed: {conversation_count}")
    print(f"Prompt rows extracted: {len(prompt_rows)}")
    print(f"Dialogue-turn prompts extracted: {dialog_turn_prompt_count}")
    print(f"Response candidates extracted: {len(response_rows)}")

    return prompt_rows, response_rows


def extract_empathetic_dialogues(project_root):
    """
    Extract a capped number of low-risk empathy prompts from EmpatheticDialogues.

    - use `prompt`, not all utterances.
    - clean `_comma_` artefacts.
    - cap the number of prompts so this general empathy dataset does not dominate.
    """
    from datasets import load_from_disk

    dirs = ensure_project_dirs(project_root)
    dataset_path = dirs["raw"] / "empathetic_dialogues"

    if not dataset_path.exists():
        print("EmpatheticDialogues not found in data/raw/empathetic_dialogues. Skipping.")
        return [], []

    config = get_prompt_pool_config(project_root)
    limits = config.get("extraction_limits", {})
    max_prompts = limits.get("empathetic_dialogues_max_prompts", 300)

    ds = load_from_disk(str(dataset_path))

    prompt_rows = []
    seen_prompts = set()

    # Keep this as a supplementary empathy source.
    allowed_contexts = {
        "afraid",
        "anxious",
        "ashamed",
        "devastated",
        "disappointed",
        "embarrassed",
        "guilty",
        "lonely",
        "sad",
        "terrified",
        "worried",
    }

    for split_name in ds.keys():
        split_data = ds[split_name]

        for row_index, row in enumerate(split_data):
            if max_prompts is not None and len(prompt_rows) >= max_prompts:
                return prompt_rows, []

            context = clean_text(row.get("context")).lower()
            prompt_text = clean_text(row.get("prompt"))

            if context and context not in allowed_contexts:
                continue

            if not is_useful_prompt(prompt_text):
                continue

            dedup_key = normalise_for_dedup(prompt_text)
            if dedup_key in seen_prompts:
                continue

            seen_prompts.add(dedup_key)

            conv_id = clean_text(row.get("conv_id")) or f"empathetic_{split_name}_{row_index:05d}"

            prompt_rows.append(
                make_prompt_row(
                    prompt_id=f"empathetic_dialogues_{len(prompt_rows):05d}",
                    source_dataset="empathetic_dialogues",
                    source_id=conv_id,
                    source_split=split_name,
                    group_id=conv_id,
                    prompt_text=prompt_text,
                    source_label=context,
                    extraction_method="prompt",
                    notes="EmpatheticDialogues prompt extracted as supplementary low-risk empathy data.",
                )
            )

    return prompt_rows, []


def normalise_synthetic_for_prompt_pool(row):
    """
    Add prompt-pool fields to a SyntheticSafety row without changing the source file.
    """
    row = dict(row)

    if row.get("category") == "bias_fairness":
        row["group_id"] = row.get("fairness_pair_id") or row.get("source_id")
    else:
        row["group_id"] = row.get("source_id") or row.get("prompt_id")

    row.setdefault("source_label", row.get("category"))

    return row


def build_prompt_pool(project_root):
    """
    Build data/processed/prompt_pool.jsonl from all prompt sources.
    """
    dirs = ensure_project_dirs(project_root)

    config = get_prompt_pool_config(project_root)
    include_sources = config.get("include_sources", {})

    all_prompt_rows = []
    all_response_rows = []

    if include_sources.get("synthetic_safety", True):
        synthetic_rows = validate_synthetic_safety_dataset(project_root, return_rows=True)
        all_prompt_rows.extend(
            normalise_synthetic_for_prompt_pool(row) for row in synthetic_rows
        )

    if include_sources.get("counsel_chat", True):
        prompts, responses = extract_counsel_chat(project_root)
        all_prompt_rows.extend(prompts)
        all_response_rows.extend(responses)

    if include_sources.get("esconv", True):
        prompts, responses = extract_esconv(project_root)
        all_prompt_rows.extend(prompts)
        all_response_rows.extend(responses)

    if include_sources.get("empathetic_dialogues", True):
        prompts, responses = extract_empathetic_dialogues(project_root)
        all_prompt_rows.extend(prompts)
        all_response_rows.extend(responses)

    # Global deduplication by prompt text.
    deduped_prompt_rows = []
    seen_prompt_texts = set()

    for row in all_prompt_rows:
        key = normalise_for_dedup(row.get("prompt_text", ""))

        if key in seen_prompt_texts:
            continue

        seen_prompt_texts.add(key)
        deduped_prompt_rows.append(row)

    prompt_pool_path = get_prompt_pool_path(project_root)
    response_candidates_path = get_response_candidates_path(project_root)

    write_jsonl(deduped_prompt_rows, prompt_pool_path)
    write_jsonl(all_response_rows, response_candidates_path)

    print("\nPrompt pool built")
    print("=" * 40)
    print(f"Prompt rows before deduplication: {len(all_prompt_rows)}")
    print(f"Prompt rows after deduplication: {len(deduped_prompt_rows)}")
    print(f"Response candidates: {len(all_response_rows)}")
    print(f"Saved prompt pool to: {prompt_pool_path}")
    print(f"Saved response candidates to: {response_candidates_path}")


def validate_prompt_pool(project_root, return_rows=False, verbose=True):
    """
    Validate data/processed/prompt_pool.jsonl.

    Catches missing fields, duplicates, short prompts and grouped split risks.
    """
    prompt_pool_path = get_prompt_pool_path(project_root)

    if not prompt_pool_path.exists():
        raise FileNotFoundError(
            f"Prompt pool not found at {prompt_pool_path}. "
            "Run: python main.py --stage build_prompt_pool"
        )

    rows = read_jsonl(prompt_pool_path)

    required_fields = [
        "prompt_id",
        "source_dataset",
        "source_id",
        "source_split",
        "group_id",
        "prompt_text",
        "category",
        "severity",
        "risk_type",
        "intended_use",
        "extraction_method",
    ]

    errors = []
    warnings = []
    seen_prompt_ids = set()
    seen_prompt_texts = set()
    source_counts = Counter()
    category_counts = Counter()
    severity_counts = Counter()

    for line_num, row in enumerate(rows, start=1):
        for field in required_fields:
            if field not in row:
                errors.append(f"Line {line_num}: missing field '{field}'")

        prompt_id = row.get("prompt_id")
        prompt_text = clean_text(row.get("prompt_text"))

        if prompt_id in seen_prompt_ids:
            errors.append(f"Line {line_num}: duplicate prompt_id '{prompt_id}'")
        seen_prompt_ids.add(prompt_id)

        normalised_prompt = normalise_for_dedup(prompt_text)
        if normalised_prompt in seen_prompt_texts:
            errors.append(f"Line {line_num}: duplicate prompt_text")
        seen_prompt_texts.add(normalised_prompt)

        if len(prompt_text) < 25:
            warnings.append(f"Line {line_num}: very short prompt_text")

        source_counts[row.get("source_dataset")] += 1
        category_counts[row.get("category")] += 1
        severity_counts[row.get("severity")] += 1

    
    if verbose:
        print("\nPrompt pool validation summary")
    print("=" * 40)
    print(f"Total prompts: {len(rows)}")

    print("\nSource counts:")
    for source, count in sorted(source_counts.items()):
        print(f"- {source}: {count}")

    print("\nCategory counts:")
    for category, count in sorted(category_counts.items()):
        print(f"- {category}: {count}")

    print("\nSeverity counts:")
    for severity, count in sorted(severity_counts.items()):
        print(f"- {severity}: {count}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings[:20]:
            print(f"- {warning}")
        if len(warnings) > 20:
            print(f"... and {len(warnings) - 20} more warnings")

    if errors:
        if verbose:
            print("\nValidation errors:")
            for error in errors:
                print(f"- {error}")
        raise ValueError("Prompt pool validation failed.")
    
    if verbose:
        print("\nPrompt pool passed validation.")

    if return_rows:
        return rows

    return None


def create_prompt_pool_report(project_root):
    """Create docs/prompt_pool_report.md."""
    dirs = ensure_project_dirs(project_root)
    rows = validate_prompt_pool(project_root, return_rows=True, verbose=False)

    source_counts = Counter(row["source_dataset"] for row in rows)
    category_counts = Counter(row["category"] for row in rows)
    severity_counts = Counter(row["severity"] for row in rows)
    extraction_counts = Counter(row["extraction_method"] for row in rows)

    response_candidates_path = get_response_candidates_path(project_root)
    if response_candidates_path.exists():
        response_rows = read_jsonl(response_candidates_path)
    else:
        response_rows = []

    report_path = dirs["docs"] / "prompt_pool_report.md"

    lines = []
    lines.append("# Prompt pool report\n")
    lines.append("This report documents the combined prompt pool used for dataset construction.\n")

    lines.append("## Files\n")
    lines.append(f"- Prompt pool: `{get_prompt_pool_path(project_root)}`")
    lines.append(f"- Response candidates: `{response_candidates_path}`\n")

    lines.append("## Total counts\n")
    lines.append(f"- Total prompt rows: {len(rows)}")
    lines.append(f"- Total response candidates: {len(response_rows)}\n")

    lines.append("## Source counts\n")
    for source, count in sorted(source_counts.items()):
        lines.append(f"- `{source}`: {count}")

    lines.append("\n## Category counts\n")
    for category, count in sorted(category_counts.items()):
        lines.append(f"- `{category}`: {count}")

    lines.append("\n## Severity counts\n")
    for severity, count in sorted(severity_counts.items()):
        lines.append(f"- `{severity}`: {count}")

    lines.append("\n## Extraction method counts\n")
    for method, count in sorted(extraction_counts.items()):
        lines.append(f"- `{method}`: {count}")

    lines.append("\n## Dataset-specific extraction decisions\n")
    lines.append(
        "- CounselChat: `questionText` was extracted as the prompt. `answerText` was kept separately as an unchecked response candidate. Duplicate questions were deduplicated by normalised prompt text."
    )
    lines.append(
        "- ESConv: the JSON stored in `text` was parsed. `situation` and meaningful `usr` turns were extracted as prompts. `sys` turns were kept as unchecked response candidates."
    )
    lines.append(
        "- EmpatheticDialogues: `prompt` was extracted as supplementary low-risk empathy data. The dataset was capped so it does not dominate the prompt pool."
    )
    lines.append(
        "- SyntheticSafety: controlled prompts were included from the manually validated JSONL file."
    )

    lines.append("\n## Important limitation\n")
    lines.append(
        "Response candidates are not treated as final chosen responses. They require later filtering, rewriting or scoring before SFT/DPO training."
    )

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\nSaved prompt pool report to: {report_path}")


def prepare_prompt_pool(project_root):
    """
    Full prompt-pool preparation stage.

    Runs:
    1. build prompt pool
    2. validate prompt pool
    3. create prompt pool report
    """
    build_prompt_pool(project_root)
    validate_prompt_pool(project_root)
    create_prompt_pool_report(project_root)
