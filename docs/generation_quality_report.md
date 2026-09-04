# Generation Quality Report

## Purpose

This report checks the integrity of generated locked test-set outputs. It verifies file existence, row counts, prompt coverage, empty responses, duplicate prompt IDs, and router application counts. It does not score response quality.

## Summary

| Condition | Rows | Unique prompt IDs | Empty responses | Duplicates | Router applied |
|---|---:|---:|---:|---:|---:|
| `m0_base` | 358 | 358 | 0 | 0 | 0 |
| `m1_prompt_only` | 358 | 358 | 0 | 0 | 0 |
| `m2_sft` | 358 | 358 | 0 | 0 | 0 |
| `m3_dpo` | 358 | 358 | 0 | 0 | 0 |
| `m1_prompt_only_guarded` | 358 | 358 | 0 | 0 | 10 |
| `m2_sft_guarded` | 358 | 358 | 0 | 0 | 10 |
| `m3_dpo_guarded` | 358 | 358 | 0 | 0 | 10 |

## Problems

No integrity problems were detected.

## Output files checked

- `m0_base`: `results/model_outputs/test_outputs_m0_base.jsonl`
- `m1_prompt_only`: `results/model_outputs/test_outputs_m1_prompt_only.jsonl`
- `m2_sft`: `results/model_outputs/test_outputs_m2_sft.jsonl`
- `m3_dpo`: `results/model_outputs/test_outputs_m3_dpo.jsonl`
- `m1_prompt_only_guarded`: `results/model_outputs/test_outputs_m1_prompt_only_guarded.jsonl`
- `m2_sft_guarded`: `results/model_outputs/test_outputs_m2_sft_guarded.jsonl`
- `m3_dpo_guarded`: `results/model_outputs/test_outputs_m3_dpo_guarded.jsonl`

## Router coverage interpretation

The guarded conditions each routed 10 of the 358 locked test prompts. This confirms that the router operated as intended, but also shows that it was conservative. The guarded evaluation should therefore be interpreted as a lightweight safety-layer comparison rather than proof that all safety-sensitive prompts were automatically detected.

The router did not use test-set category labels. It only inspected prompt text, which protects evaluation integrity but also means that ambiguous crisis signals may remain unrouted.
