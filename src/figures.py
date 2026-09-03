"""
Create dissertation figures from final evaluation tables.

Inputs:
- results/tables/condition_summary.csv

Outputs:
- results/figures/overall_core_mean_by_condition.png
- results/figures/safety_by_condition.png
- results/figures/critical_safety_failure_rate_by_condition.png
- results/figures/raw_vs_guarded_safety.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONDITION_ORDER = [
    "m0_base",
    "m1_prompt_only",
    "m2_sft",
    "m3_dpo",
    "m1_prompt_only_guarded",
    "m2_sft_guarded",
    "m3_dpo_guarded",
]

CONDITION_LABELS = {
    "m0_base": "M0 Base",
    "m1_prompt_only": "M1 Prompt",
    "m2_sft": "M2 SFT",
    "m3_dpo": "M3 DPO",
    "m1_prompt_only_guarded": "M1g Prompt+Router",
    "m2_sft_guarded": "M2g SFT+Router",
    "m3_dpo_guarded": "M3g DPO+Router",
}

UCL_PURPLE = "#361a54"
UCL_BRIGHT_PURPLE = "#993bff"
UCL_LIGHT_PURPLE = "#ddbdff"
UCL_BLUE = "#30d6ff"


def prepare_condition_df(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["condition"] = pd.Categorical(df["condition"], CONDITION_ORDER, ordered=True)
    df = df.sort_values("condition")
    df["label"] = df["condition"].astype(str).map(CONDITION_LABELS)
    return df


def save_bar(df, y_col, ylabel, title, out_path, ylim, color):
    plt.figure(figsize=(10, 6))
    plt.bar(df["label"], df[y_col], color=color)
    plt.ylabel(ylabel)
    plt.xlabel("Condition")
    plt.title(title)
    plt.ylim(*ylim)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


def create_figures(project_root: Path = PROJECT_ROOT):
    project_root = Path(project_root)
    table_dir = project_root / "results/tables"
    figure_dir = project_root / "results/figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    condition_path = table_dir / "condition_summary.csv"
    if not condition_path.exists():
        raise FileNotFoundError(f"Missing {condition_path}. Run analyse_results first.")

    df = prepare_condition_df(condition_path)

    save_bar(
        df=df,
        y_col="overall_core_mean",
        ylabel="Mean score",
        title="Overall core evaluation score by condition",
        out_path=figure_dir / "overall_core_mean_by_condition.png",
        ylim=(0, 5),
        color=UCL_PURPLE,
    )

    save_bar(
        df=df,
        y_col="safety_mean",
        ylabel="Mean safety score",
        title="Safety score by condition",
        out_path=figure_dir / "safety_by_condition.png",
        ylim=(0, 5),
        color=UCL_BRIGHT_PURPLE,
    )

    save_bar(
        df=df,
        y_col="critical_safety_failure_rate",
        ylabel="Critical safety failure rate",
        title="Critical safety failure rate by condition",
        out_path=figure_dir / "critical_safety_failure_rate_by_condition.png",
        ylim=(0, 1),
        color=UCL_PURPLE,
    )

    pairs = [
        ("m1_prompt_only", "m1_prompt_only_guarded", "M1"),
        ("m2_sft", "m2_sft_guarded", "M2"),
        ("m3_dpo", "m3_dpo_guarded", "M3"),
    ]

    rows = []
    for raw, guarded, label in pairs:
        raw_row = df[df["condition"].astype(str) == raw]
        guarded_row = df[df["condition"].astype(str) == guarded]
        if raw_row.empty or guarded_row.empty:
            continue
        rows.append(
            {
                "model": label,
                "raw_safety": raw_row["safety_mean"].iloc[0],
                "guarded_safety": guarded_row["safety_mean"].iloc[0],
            }
        )

    pair_df = pd.DataFrame(rows)
    x = np.arange(len(pair_df))
    width = 0.35

    plt.figure(figsize=(8, 6))
    plt.bar(x - width / 2, pair_df["raw_safety"], width, label="Raw", color=UCL_LIGHT_PURPLE)
    plt.bar(x + width / 2, pair_df["guarded_safety"], width, label="Guarded", color=UCL_BLUE)
    plt.ylabel("Mean safety score")
    plt.xlabel("Model")
    plt.title("Raw vs guarded safety scores")
    plt.ylim(0, 5)
    plt.xticks(x, pair_df["model"])
    plt.legend()
    plt.tight_layout()
    plt.savefig(figure_dir / "raw_vs_guarded_safety.png", dpi=300)
    plt.close()

    print("Figures saved to:", figure_dir)
