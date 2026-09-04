# Therapy Specific Post-Training for Safer Online Mental Health Support

This repository contains the code, data processing pipeline, training scripts, evaluation outputs, and documentation for a research prototype.

We investigate whether therapy specific post-training can improve the safety, empathy, helpfulness, and boundary awareness of an open-source LLM for text-based online mental health support.

The system is a research prototype only. It is not a clinical tool and should not be used for real mental health care.

---

## Research question and hypothesis

**Research question:** Can therapy specific post-training, using supervised fine-tuning (SFT) followed by direct preference optimisation (DPO) applied to a small open-source instruction model, measurably improve the safety, empathy, helpfulness, and boundary awareness of that model for text-based online mental health support compared with the unmodified base model?

**Hypothesis:** A two stage SFT - DPO pipeline applied using preference pairs constructed from therapy style prompts with clinically grounded chosen and rejected responses will produce a model with fewer critical safety failures and higher rubric scores on safety, empathy, and helpfulness than the base model, without an unacceptable reduction in helpfulness.

**Falsification criterion:** The hypothesis fails if safety gains come only at the cost of helpfulness, or if post-training produces no statistically significant improvement on any rubric dimension compared with the prompt-only safety baseline.

---


## Project summary

The project compares raw and guarded versions of a small open-source instruction model:

| Label | Condition |
|---|---|
| M0 | `m0_base` |
| M1 | `m1_prompt_only` |
| M2 | `m2_sft` |
| M3 | `m3_dpo` |
| M1g | `m1_prompt_only_guarded` |
| M2g | `m2_sft_guarded` |
| M3g | `m3_dpo_guarded` |

The guarded conditions use a deterministic safety router before model generation.

The final conclusion should be interpreted cautiously: SFT and DPO were implemented successfully, but post-training alone did not guarantee reliable safety critical behaviour. The deterministic router improved some explicit safety sensitive cases, but did not catch every ambiguous crisis signal.

---
## Main contribution

The project contributes a reproducible local post-training and evaluation pipeline that separates:

1. behaviour from the original open-weight instruction model;
2. behaviour induced by a safety system prompt;
3. behaviour learned through SFT and DPO; and
4. behaviour enforced by a deterministic inference-time safety router.

This separation is important because a safer final system may owe its performance to learned model behaviour, an external control layer, or both.

---

## Key limitations

- Training was completed on a single random seed (42) under local CPU compute constraints. Results should be interpreted as an initial empirical observation rather than a stable multi-run estimate.
- The base model (Qwen/Qwen2.5-0.5B-Instruct) is much smaller than the originally planned Llama 3 8B. Absolute response quality is limited by model capacity.
- Post-training alone did not reliably handle ambiguous crisis signals. A deterministic safety router was added for guarded evaluation conditions but covered only 10 of 358 locked test prompts per condition.
- The evaluation uses manual rubric scoring rather than automated metrics, introducing potential rater variance despite using blinded scoring and consistency auditing.

---

## Main entry point

All main stages are run through:

```bash
python main.py --stage <stage_name>
```

List available stages with:

```bash
python main.py --help
```

---

## Main pipeline stages

### Data preparation

```bash
python main.py --stage prepare_synthetic_safety
python main.py --stage prepare_prompt_pool
python main.py --stage create_splits
python main.py --stage validate_splits
```

### Response-pair creation

```bash
python main.py --stage create_pairing_subset_pilot
python main.py --stage create_response_pairs_pilot
python main.py --stage validate_response_pairs_pilot

python main.py --stage create_pairing_subset_main
python main.py --stage create_response_pairs_main
python main.py --stage validate_response_pairs_main
```

### Training

```bash
python main.py --stage train_sft
python main.py --stage train_dpo
```

### Evaluation generation

```bash
python main.py --stage router_smoke_test
python main.py --stage generate_test_outputs_raw
python main.py --stage generate_test_outputs_guarded
```

### Scoring preparation and checks

```bash
python main.py --stage prepare_scoring
python main.py --stage quality_check_outputs
python main.py --stage create_critical_review_queue
python main.py --stage apply_critical_review_queue
python main.py --stage validate_scores
python main.py --stage audit_score_consistency
```

### Final analysis

```bash
python main.py --stage analyse_results
python main.py --stage create_figures
python main.py --stage extract_error_examples
```

---

## Important documentation

```text
docs/data_audit.md
docs/data_split_report.md
docs/prompt_pool_report.md
docs/response_pair_report.md
docs/training_report.md
docs/evaluation_plan.md
docs/scoring_rubric.md
docs/generation_quality_report.md
docs/critical_safety_review_report.md
docs/scoring_validation_report.md
docs/score_consistency_audit_report.md
docs/evaluation_results_report.md
docs/error_analysis.md
```
`docs/experiment_log.md` records the main chronological decisions and implementation changes made during the project.
---

## Final generated outputs

Locked test-set model outputs are stored in:

```text
results/model_outputs/
```

The seven final output files are:

```text
results/model_outputs/test_outputs_m0_base.jsonl
results/model_outputs/test_outputs_m1_prompt_only.jsonl
results/model_outputs/test_outputs_m2_sft.jsonl
results/model_outputs/test_outputs_m3_dpo.jsonl
results/model_outputs/test_outputs_m1_prompt_only_guarded.jsonl
results/model_outputs/test_outputs_m2_sft_guarded.jsonl
results/model_outputs/test_outputs_m3_dpo_guarded.jsonl
```

Each file contains 358 generated responses.

---

## Manual scoring files

The completed blinded scoring file is:

```text
results/scores/evaluation_scores_completed_blinded.csv
```

The private blinding key is:

```text
results/scores/blinding_key_PRIVATE.json
```

The critical-safety review file is:

```text
results/scores/critical_safety_review_queue_completed.csv
```

Generated model outputs were not manually edited before scoring.

---

## Final analysis outputs

```text
results/tables/generated_output_integrity_summary.csv
results/tables/condition_summary.csv
results/tables/category_condition_summary.csv
results/tables/statistical_tests.csv
results/tables/fairness_pair_review.csv

results/figures/overall_core_mean_by_condition.png
results/figures/safety_by_condition.png
results/figures/critical_safety_failure_rate_by_condition.png
results/figures/raw_vs_guarded_safety.png
```

---

## Reproducibility notes

- The locked test set is `data/splits/test_prompts_LOCKED.jsonl`.
- The locked test set was not used during training, prompt iteration, validation smoke testing, or router development.
- Rubric dimensions are scored on a 0-5 scale.
- `critical_safety_failure` is binary: `0` means no critical safety failure and `1` means a critical safety failure was present.
- `crisis_escalation` is blank for non-crisis prompts.
- Final training used CPU float32 after MPS/float16 attempts were unstable or exceeded local memory.
- Only one training seed was used because repeated SFT/DPO runs were not feasible under local compute constraints.

---

## Final interpretation

The project should not be interpreted as demonstrating a clinically safe therapy chatbot. It demonstrates a reproducible post-training and evaluation framework, and shows that small-model SFT/DPO alone is insufficient for reliable safety critical, mental health support. The strongest contribution is the distinction between optimisation success and safety success, supported by locked test-set evaluation and qualitative error analysis.
