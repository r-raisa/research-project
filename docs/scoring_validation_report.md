# Scoring Validation Report

## Input file

`results/scores/evaluation_scores_completed_blinded.csv`

## Expected structure

- Expected total rows: 2506
- Expected rows per condition: 358
- Score range: 0-5 for rubric dimensions
- Crisis escalation: 0-5 where applicable, blank otherwise
- Critical safety failure: binary 0/1 for every row

## Row counts by condition

| Condition | Rows |
|---|---:|
| `m0_base` | 358 |
| `m1_prompt_only` | 358 |
| `m2_sft` | 358 |
| `m3_dpo` | 358 |
| `m1_prompt_only_guarded` | 358 |
| `m2_sft_guarded` | 358 |
| `m3_dpo_guarded` | 358 |

## Missing values

| Column | Missing |
|---|---:|
| `safety` | 0 |
| `empathy` | 0 |
| `helpfulness` | 0 |
| `boundaries` | 0 |
| `fairness` | 0 |
| `crisis_escalation` | 2387 |
| `critical_safety_failure` | 0 |

## Validation result

Validation passed. No scoring integrity problems were detected.
