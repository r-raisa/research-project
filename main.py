"""
Entry point for the LLM therapy post-training project.


Run stages from the project root using:
    python main.py --stage <stage_name>
"""

from pathlib import Path
import argparse

from src.data_pipeline import (
    download_data,
    inspect_data,
    validate_synthetic_safety_dataset,
    create_synthetic_safety_report,
    add_synthetic_safety_to_prompt_pool,
    prepare_synthetic_safety,
    build_prompt_pool,
    validate_prompt_pool,
    create_prompt_pool_report,
    prepare_prompt_pool,
    create_train_validation_test_splits,
    validate_existing_splits,
)

from src.response_pairing import (
    create_pairing_prompt_subsets,
    create_hybrid_response_pairs,
    validate_response_pair_files,
)

PROJECT_ROOT = Path(__file__).resolve().parent


STAGES = [
    "download_data",
    "inspect_data",
    "validate_synthetic_safety",
    "report_synthetic_safety",
    "add_synthetic_to_prompt_pool",
    "prepare_synthetic_safety",
    "build_prompt_pool",
    "validate_prompt_pool",
    "report_prompt_pool",
    "prepare_prompt_pool",
    "create_splits",
    "validate_splits",
    "prepare_data",
    "create_pairing_subset_pilot",
    "create_response_pairs_pilot",
    "validate_response_pairs_pilot",
    "create_pairing_subset_main",
    "create_response_pairs_main",
    "validate_response_pairs_main",
    "all",
]


def parse_args():
    """Parse the command-line stage argument."""
    parser = argparse.ArgumentParser(
        description="Run stages of the LLM therapy data pipeline."
    )
    parser.add_argument(
        "--stage",
        type=str,
        required=True,
        choices=STAGES,
        help="Pipeline stage to run.",
    )
    return parser.parse_args()


def main():
    """Route the requested stage to the correct pipeline function."""
    args = parse_args()

    if args.stage == "download_data":
        download_data(PROJECT_ROOT)

    elif args.stage == "inspect_data":
        inspect_data(PROJECT_ROOT)

    elif args.stage == "validate_synthetic_safety":
        validate_synthetic_safety_dataset(PROJECT_ROOT)

    elif args.stage == "report_synthetic_safety":
        create_synthetic_safety_report(PROJECT_ROOT)

    elif args.stage == "add_synthetic_to_prompt_pool":
        add_synthetic_safety_to_prompt_pool(PROJECT_ROOT)

    elif args.stage == "prepare_synthetic_safety":
        prepare_synthetic_safety(PROJECT_ROOT)

    elif args.stage == "build_prompt_pool":
        build_prompt_pool(PROJECT_ROOT)

    elif args.stage == "validate_prompt_pool":
        validate_prompt_pool(PROJECT_ROOT)

    elif args.stage == "report_prompt_pool":
        create_prompt_pool_report(PROJECT_ROOT)

    elif args.stage == "prepare_prompt_pool":
        prepare_prompt_pool(PROJECT_ROOT)
    
    elif args.stage == "create_splits":
        create_train_validation_test_splits(PROJECT_ROOT)

    elif args.stage == "validate_splits":
        validate_existing_splits(PROJECT_ROOT)

    elif args.stage == "prepare_data":
        download_data(PROJECT_ROOT)
        inspect_data(PROJECT_ROOT)

    elif args.stage == "create_pairing_subset_pilot":
        create_pairing_prompt_subsets(PROJECT_ROOT, pilot=True)

    elif args.stage == "create_response_pairs_pilot":
        create_hybrid_response_pairs(PROJECT_ROOT, pilot=True)

    elif args.stage == "validate_response_pairs_pilot":
        validate_response_pair_files(PROJECT_ROOT, pilot=True)

    elif args.stage == "create_pairing_subset_main":
        create_pairing_prompt_subsets(PROJECT_ROOT, pilot=False)

    elif args.stage == "create_response_pairs_main":
        create_hybrid_response_pairs(PROJECT_ROOT, pilot=False)

    elif args.stage == "validate_response_pairs_main":
        validate_response_pair_files(PROJECT_ROOT, pilot=False)

    elif args.stage == "all":
        download_data(PROJECT_ROOT)
        inspect_data(PROJECT_ROOT)
        prepare_synthetic_safety(PROJECT_ROOT)


if __name__ == "__main__":
    main()
