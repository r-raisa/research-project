# Experiment log

This document records the key decisions, events, and outcomes at each stage of the project in chronological order. It serves as the audit trail for the research process.

---
## Stage 1 — Prompt pool split and locked test set

The prompt pool was split into training, validation, and locked test sets. The split used source aware and category aware grouping so that related prompts from the same source item, conversation, or fairness pair did not appear in more than one split.

Final split sizes were:

| Split | Rows |
|---|---:|
| Train | 2429 |
| Validation | 339 |
| Test | 358 |

The locked test set was saved as:

```text
data/splits/test_prompts_LOCKED.jsonl
```

Decision: the locked test set was excluded from all later prompt iteration, response-pair construction, SFT, DPO, smoke testing, router development, and scoring procedure changes.

Reason: the final evaluation needed to measure generalisation to unseen prompts rather than performance on examples used during development.

---

## Stage 2 — Response-pair pilot round 1

A first pilot response-pair dataset was generated to test whether the response-pair construction procedure could produce usable chosen and rejected examples.

Observation: chosen responses generally passed basic safety checks, but several were too generic or insufficiently connected to the user's specific prompt. This made them weak training targets because the model could learn safe but low-specificity support.

Decision: do not scale this version to the full training set.

Fixes introduced after pilot round 1:

- add prompt-specific relevance checks;
- strengthen filtering for generic responses;
- inspect cases where public dataset labels were noisy;
- prevent safety-category labels from forcing controlled templates for unrelated public prompts.

Reason: a high-quality chosen response needed to be both safe and responsive to the actual user message.

---

## Stage 3 — Response-pair pilot round 2

A second pilot was produced after revising the routing and validation logic.

Design decision: SyntheticSafety prompts and direct safety/boundary prompts used controlled chosen templates. Ordinary public prompts used local model generation with quality checks.

Rationale: safety-critical prompts should not rely on generated responses as the desired target, because unsafe generations could be accidentally promoted during training. Public prompts were more varied and benefited from generated responses that could refer to specific details in the prompt.

Pilot outputs:

```text
data/splits/train_sft_pilot.jsonl
data/splits/train_dpo_pilot.jsonl
data/splits/validation_sft_pilot.jsonl
data/splits/validation_dpo_pilot.jsonl
```

Decision: proceed to main response-pair generation after validation and manual spot-checking.

---

## Stage 4 — Main response-pair generation and validation

The main SFT and DPO training files were generated from the training and validation prompt subsets.

Final row counts:

| File | Rows |
|---|---:|
| `data/splits/train_sft.jsonl` | 513 |
| `data/splits/validation_sft.jsonl` | 96 |
| `data/splits/train_dpo.jsonl` | 513 |
| `data/splits/validation_dpo.jsonl` | 96 |

The final SFT and DPO row counts match within train and validation splits. This means each retained prompt has both a supervised chosen-response example and a DPO preference pair.

Examples were excluded when a generated chosen response failed quality, relevance, completion, or safety checks. This reduced the final training set size, but improved the reliability of the retained targets.

Decision: freeze response-pair files for training.

Reason: the files passed validation and provided enough examples for a local proof-of-concept SFT and DPO pipeline.

---

## Stage 5 — SFT attempt 1 on Apple Silicon MPS

The first SFT attempt used Apple Silicon MPS to speed up local training.

Outcome: the run failed due to local memory constraints.

Decision: do not use this run in the final results.

Reason: an incomplete training run cannot be interpreted as a trained model condition.

---

## Stage 6 — SFT attempt 2 on Apple Silicon MPS

A second MPS attempt was made after reducing memory pressure.

Outcome: the run produced unstable training behaviour, including very large loss values and `NaN` gradient norms.

Decision: exclude this run and abandon MPS for the final model.

Reason: `NaN` gradients indicate an invalid optimisation run. The final project needed stable finite training metrics, even if this required slower CPU training.

---

## Stage 7 — Final SFT run on CPU float32

The final SFT run was performed on CPU using float32.

Final SFT configuration included:

- model: `Qwen/Qwen2.5-0.5B-Instruct`;
- seed: 42;
- epochs: 3;
- learning rate: 0.0001;
- train/eval batch size: 1;
- gradient accumulation: 16;
- maximum sequence length: 640;
- LoRA rank/alpha/dropout: 8/16/0.05;
- LoRA target modules: `q_proj`, `v_proj`;
- device/dtype: CPU, float32.

SFT validation loss decreased across epochs:

| Epoch | Validation loss |
|---:|---:|
| 1.0 | 2.1459 |
| 2.0 | 1.5785 |
| 2.99 | 1.3047 |

Final SFT metrics:

| Metric | Value |
|---|---:|
| Train loss | 1.8315 |
| Eval loss | 1.3047 |
| Runtime | 3718.82 seconds |
| Training time | 63.18 minutes |

The final SFT adapter was saved to:

```text
models/sft/seed_42/final_adapter
```

Decision: use this adapter as M2 and as the starting point for DPO.

Reason: the CPU run completed successfully with finite metrics and decreasing validation loss.

---

## Stage 8 — DPO tokeniser bug

The first DPO attempt failed during collation with a token-ID error.

Diagnosis: the DPO dataset contained the expected fields (`prompt`, `chosen`, `rejected`), but the tokenizer had no BOS token ID. Qwen used valid EOS and PAD IDs but returned `None` for BOS.

Fix:

- set BOS to `<|im_start|>`;
- set EOS to `<|im_end|>`;
- set PAD to `<|endoftext|>`;
- synchronise BOS/EOS/PAD IDs to the policy and reference model configs before training.

Decision: keep the DPO dataset unchanged and fix token configuration in code.

Reason: the failure was a tokenizer/model configuration issue, not a preference data issue.

---

## Stage 9 — Final DPO run on CPU float32

DPO was run after SFT. The policy model started from the SFT adapter. The reference model used the same SFT adapter but was non-trainable.

Final DPO configuration included:

- starting adapter: `models/sft/seed_42/final_adapter`;
- seed: 42;
- epochs: 1;
- learning rate: 0.00002;
- train/eval batch size: 1;
- gradient accumulation: 16;
- maximum prompt length: 384;
- maximum total length: 768;
- beta: 0.1;
- device/dtype: CPU, float32.

Final DPO metrics:

| Metric | Value |
|---|---:|
| Train loss | 0.3530 |
| Eval loss | 0.2587 |
| Validation reward accuracy | 0.9583 |
| Validation reward margin | 1.5070 |
| Runtime | 9745.71 seconds |
| Training time | 171.16 minutes |

The final DPO adapter was saved to:

```text
models/dpo/seed_42/final_adapter
```

Decision: use this adapter as M3.

Interpretation: the DPO metrics show that preference optimisation succeeded on the constructed validation preference pairs. They do not prove clinical safety or final response quality.

Note: `total_flos` was reported as 0.0 in the trainer logs. This was treated as a logging artefact associated with the DPO/LoRA training setup rather than as evidence of training failure, because the run completed successfully and produced finite loss, reward accuracy, and reward margin values.

---

## Stage 10 — Validation-only safety smoke testing

After training, targeted validation-only smoke tests were run on safety-sensitive prompts. The locked test set was not used.

The smoke tests compared:

- M1: base model with safety prompt;
- M2: SFT adapter with safety prompt;
- M3: DPO adapter with safety prompt.

Finding: raw prompted and post-trained outputs remained unreliable on safety-sensitive cases. Earlier prompt versions produced unsafe or incomplete crisis handling, diagnosis-boundary failures, over-refusal, and medication-boundary weaknesses.

Decision: do not claim that post-training alone created a safe mental-health support model.

Reason: training success and validation preference accuracy did not guarantee safety-critical behaviour in generation.

---

## Stage 11 — Deterministic safety router added

A deterministic safety router was added for guarded evaluation conditions.

The router checks only the user prompt text and does not use category labels or expected responses. It routes prompts matching explicit patterns for:

- crisis risk;
- harmful advice;
- medication boundary;
- diagnosis boundary.

If a route is triggered, the router returns a controlled response instead of calling the generative model. Otherwise, the model generates normally.

Decision: evaluate both raw and guarded conditions.

Reason: this separates learned model behaviour from external inference-time control. It also makes the negative finding academically useful: post-training alone was not sufficient, so a guardrail-assisted framework needed to be evaluated separately.

---

## Stage 12 — Locked test-set output generation

After the final inference prompt and router were frozen, locked test-set outputs were generated.

Raw conditions:

- `m0_base`;
- `m1_prompt_only`;
- `m2_sft`;
- `m3_dpo`.

Guarded conditions:

- `m1_prompt_only_guarded`;
- `m2_sft_guarded`;
- `m3_dpo_guarded`.

Each condition generated 358 responses, one per locked test prompt. Generated outputs were saved under:

```text
results/model_outputs/
```
Output integrity checks confirmed that all seven output files contained 358 rows, with no empty generated responses and no duplicate prompt IDs.

Decision: do not manually edit generated outputs.

Reason: unsafe, low-quality, or malformed generations are part of the evaluation evidence.

---

## Stage 13 — Manual scoring and critical-safety review

Generated outputs were converted into a condition-blinded scoring CSV. The completed file contains 2,506 scored responses:

```text
7 conditions × 358 locked prompts = 2506 responses
```

The main dimensions were scored from 0 to 5:

- safety;
- empathy;
- helpfulness;
- boundaries;
- crisis escalation where applicable;
- fairness.

Critical safety failure was scored as a binary variable:

- 0 = no critical safety failure;
- 1 = critical safety failure present.

A critical-safety review queue was used to resolve blanks and ambiguous critical-failure labels. Score validation and a score-consistency audit were then run.

Decision: keep `critical_safety_failure` separate from average quality scores.

Reason: high average fluency or empathy should not hide rare severe failures.

Score validation confirmed that all required 0-5 rubric scores and binary critical-safety-failure labels were present. A score-consistency audit found no remaining contradictions between scores, critical-failure labels, and notes.

---

## Stage 14 — Final quantitative analysis

The final analysis generated:

```text
results/tables/condition_summary.csv
results/tables/category_condition_summary.csv
results/tables/statistical_tests.csv
results/tables/fairness_pair_review.csv
```

The statistical analysis used paired comparisons because every condition answered the same locked prompts. Wilcoxon signed-rank tests were used for 0--5 rubric scores, exact McNemar-style binomial tests were used for critical safety failures, bootstrap confidence intervals were used for mean paired differences, and Benjamini--Hochberg correction was used for multiple comparisons.

End-to-end comparisons from M0 to M3 and M0 to M3g were added to make the main baseline comparison explicit.

Wilcoxon effect sizes were computed for ordinal score comparisons, alongside bootstrap confidence intervals and false discovery rate adjusted p-values.

Decision: report critical safety failure rate as a primary safety outcome and interpret mean scores alongside failure rates.

Reason: the base model could achieve higher average conversational quality while still producing more severe safety failures.

---

## Final project interpretation

The final project does not claim that the model is clinically safe. The supported conclusion is narrower:

```text
SFT and DPO were implemented successfully, but post-training alone did not guarantee reliable safety critical, mental health behaviour. A deterministic router improved some explicitly detected cases, but conservative rule-based routing did not solve every ambiguous crisis prompt.
```

This interpretation preserves the difference between optimisation success, average response quality, and safety-critical reliability.
