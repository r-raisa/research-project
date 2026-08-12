"""
Shared utility functions for LLM therapy project.

"""

from pathlib import Path
import json
import re
import yaml


def load_yaml(path):
    """Load a YAML config file."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def read_jsonl(path):
    """
    Read a JSONL file.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {path}")

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {line_num} in {path}: {e}")

    return rows


def write_jsonl(rows, path):
    """Write a list of dictionaries to a JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def resolve_project_path(project_root, path_value):
    """
    Resolve a path from the config.
    """
    project_root = Path(project_root)
    path = Path(path_value)

    if path.is_absolute():
        return path

    return project_root / path


def clean_text(text):
    """
    Basic text normalisation used when deduplicating prompts.
    """
    if text is None:
        return ""

    text = str(text)
    text = text.replace("_comma_", ",")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalise_for_dedup(text):
    """Normalise text for duplicate checks."""
    return clean_text(text).lower()
