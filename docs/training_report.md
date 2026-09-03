# Training Report

## Purpose

This document records the training phase for the therapy-specific LLM post-training project. The project investigates whether therapy-specific post-training can improve the safety, empathy, helpfulness, and boundary awareness of an open-source language model for text-based online mental-health support.

The training phase produced two trained adapters for later locked test-set evaluation:

1. a supervised fine-tuning adapter (SFT), and
2. a direct preference optimisation adapter (DPO) trained from the SFT adapter.

The locked test set was not used during training, prompt iteration, validation smoke testing, or safety-router development.

---

## Model variants

The final evaluation compared the following model conditions.

| Label | Model condition | Status |
|---|---|---|
| M0 | Base open-source instruction model | Evaluated |
| M1 | Base model with safety prompt | Evaluated |
| M2 | SFT model with safety prompt | Trained and evaluated |
| M3 | SFT + DPO model with safety prompt | Trained and evaluated |
| M1g | Prompt-only baseline with deterministic safety router | Evaluated |
| M2g | SFT model with deterministic safety router | Evaluated |
| M3g | DPO model with deterministic safety router | Evaluated |

The raw and guarded distinction was introduced because validation-only smoke testing showed that raw prompting and post-training alone did not reliably handle all safety-critical prompts.

---

## Base model

The experimental base model was:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

This model was selected because it is an open-source instruction-tuned model small enough to support local experimentation under the available compute constraints. The originally planned larger model was not used because it was not feasible to train and evaluate locally within the project constraints.

The model and trained adapters are research prototypes only. They are not presented as a clinical product or deployable therapy system.

---

## Compute environment

| Item | Value |
|---|---|
| Local machine | MacBook Pro with Apple Silicon |
| Python environment | `llm-therapy` |
| Final successful training device | CPU |
| Final successful dtype | float32 |
| Entry point | `python main.py --stage train_sft` and `python main.py --stage train_dpo` |

Initial SFT attempts using Apple Silicon MPS failed due to memory limits. One attempted MPS run also produced unstable values, including extremely large loss values and `NaN` gradient norms. Because `NaN` gradients indicate an invalid training run, MPS training was abandoned. The final successful SFT and DPO runs were completed on CPU using float32.

This increased runtime, but produced stable finite training metrics and a reproducible local pipeline.

---

## Training data

Training used only the training and validation response-pair files.

| File | Purpose | Rows |
|---|---|---:|
| `data/splits/train_sft.jsonl` | SFT training data | 513 |
| `data/splits/validation_sft.jsonl` | SFT validation data | 96 |
| `data/splits/train_dpo.jsonl` | DPO training data | 513 |
| `data/splits/validation_dpo.jsonl` | DPO validation data | 96 |
| `data/splits/test_prompts_LOCKED.jsonl` | Locked test set, not used during training | 358 |

The SFT and DPO row counts match within each split, meaning that each retained prompt has both a supervised chosen-response example and a preference pair. Examples were excluded when generated chosen responses failed automatic quality, relevance, completion, or safety checks.

---

## Response-pair validation before training

The response-pair dataset was validated before training. Validation checked for:

- empty fields,
- missing chosen or rejected responses,
- chosen/rejected duplication,
- response cut-off,
- safety flag consistency,
- prompt relevance, and
- basic formatting issues.

The response-pair generation pipeline was revised before training to improve crisis-risk routing, medication-boundary routing, diagnosis-boundary routing, grief prompt handling, cut-off response rejection, and quality filtering for public-dataset prompts.

Manual spot-checking was also used because automatic validation cannot fully assess empathy, appropriateness, or contextual fit.

---

## Training prompt

A compact training system prompt was used during post-training:

```text
You are a supportive mental health assistant for a research prototype.
Respond with empathy, practical coping support, and clear boundaries.
Do not diagnose, give medication instructions, make clinical promises, or encourage dependence.
If the user may be at immediate risk of harm, advise emergency services, a crisis line, or trusted real-world support.
```

The compact prompt preserved the main behavioural constraints while reducing repeated token overhead. The fuller triage-style safety prompt was reserved for inference-time evaluation rather than repeated in every training example.

---

## Token-length analysis

A token-length check was conducted on SFT examples before finalising the training configuration.

| Threshold | Examples exceeding threshold |
|---:|---:|
| 512 | 268 |
| 640 | 93 |
| 704 | 35 |
| 768 | 5 |
| 896 | 0 |
| 1024 | 0 |

A maximum sequence length of 512 was too restrictive because it would affect a large proportion of the training examples. The original 768-token setting preserved almost all examples but was less reliable under local compute constraints. The final setup used `max_seq_length=640`, a compact training prompt, CPU float32 training, and a reduced LoRA rank.

---

## Final SFT configuration

| Parameter | Value |
|---|---:|
| Seed | 42 |
| Epochs | 3 |
| Learning rate | 0.0001 |
| Per-device train batch size | 1 |
| Per-device eval batch size | 1 |
| Gradient accumulation steps | 16 |
| Effective batch size | 16 |
| Max sequence length | 640 |
| Gradient checkpointing | true |
| Warmup ratio | 0.05 |
| Max gradient norm | 0.3 |
| Save strategy | epoch |
| Evaluation strategy | epoch |
| Save total limit | 2 |
| Device | CPU |
| Dtype | float32 |

### LoRA configuration

| Parameter | Value |
|---|---:|
| LoRA rank | 8 |
| LoRA alpha | 16 |
| LoRA dropout | 0.05 |
| Target modules | `q_proj`, `v_proj` |
| Task type | causal language modelling |

The LoRA rank was reduced from larger attempted settings after local memory constraints were encountered.

---

## SFT training outcome

SFT training completed successfully for seed 42.

The final SFT adapter was saved to:

```text
models/sft/seed_42/final_adapter
```

| Metric | Value |
|---|---:|
| Training examples | 513 |
| Validation examples | 96 |
| Epochs completed | 2.99 |
| Final training loss | 1.8315 |
| Final validation loss | 1.3047 |
| Training runtime | 3718.82 seconds |
| Training time | 63.18 minutes |
| Train samples per second | 0.414 |
| Train steps per second | 0.026 |
| Device | CPU |
| Dtype | float32 |

### SFT validation loss by epoch

| Epoch | Validation loss |
|---:|---:|
| 1.0 | 2.1459 |
| 2.0 | 1.5785 |
| 2.99 | 1.3047 |

Validation loss decreased across the run, and the successful CPU run did not show `NaN` gradient values. This indicates that the SFT optimisation completed stably.

SFT log files were saved under:

```text
results/training_logs/sft_seed_42_log_history.csv
results/training_logs/sft_seed_42_trainer_state.json
results/training_logs/sft_seed_42_metadata.json
```

---

## DPO preparation and tokenisation fix

DPO training was run after SFT using the trained SFT adapter as its starting point:

```text
models/sft/seed_42/final_adapter
```

The DPO dataset passed to `DPOTrainer` contained only the expected fields:

```text
prompt
chosen
rejected
```

An initial DPO run failed during batch collation with a `NoneType` token-ID error. Tokenizer inspection showed that Qwen had valid EOS and PAD token IDs but no BOS token ID. The training code was updated to set:

```text
bos_token: <|im_start|>
bos_token_id: 151644
```

The policy and reference model configs were synchronised with the tokenizer BOS, EOS, and PAD token IDs before DPO training. After this fix, DPO training proceeded successfully.

---

## Final DPO configuration

| Parameter | Value |
|---|---:|
| Seed | 42 |
| Starting adapter | `models/sft/seed_42/final_adapter` |
| Epochs | 1 |
| Learning rate | 0.00002 |
| Per-device train batch size | 1 |
| Per-device eval batch size | 1 |
| Gradient accumulation steps | 16 |
| Max prompt length | 384 |
| Max total length | 768 |
| Beta | 0.1 |
| Warmup ratio | 0.05 |
| Max gradient norm | 0.3 |
| Save strategy | epoch |
| Evaluation strategy | epoch |
| Save total limit | 2 |
| Device | CPU |
| Dtype | float32 |

---

## DPO training outcome

DPO training completed successfully for seed 42.

The final DPO adapter was saved to:

```text
models/dpo/seed_42/final_adapter
```

| Metric | Value |
|---|---:|
| Training examples | 513 |
| Validation examples | 96 |
| Epochs completed | 1.0 |
| Final training loss | 0.3530 |
| Final validation loss | 0.2587 |
| Training runtime | 9745.71 seconds |
| Training time | 171.16 minutes |
| Train samples per second | 0.053 |
| Train steps per second | 0.003 |
| Device | CPU |
| Dtype | float32 |

### DPO validation preference metrics

| Metric | Value |
|---|---:|
| Validation chosen reward | -0.0780 |
| Validation rejected reward | -1.5850 |
| Validation reward accuracy | 0.9583 |
| Validation reward margin | 1.5070 |
| Validation chosen log probability | -187.3399 |
| Validation rejected log probability | -105.6449 |

The DPO validation reward accuracy of 0.9583 indicates that the DPO objective assigned higher relative preference to the chosen response than the rejected response for most validation preference pairs. This is evidence that preference optimisation succeeded on the constructed validation preference dataset.

These metrics are not treated as proof of safety or clinical appropriateness. Final conclusions are based on locked test-set evaluation, not training metrics alone.

DPO log files were saved under:

```text
results/training_logs/dpo_seed_42_log_history.csv
results/training_logs/dpo_seed_42_trainer_state.json
results/training_logs/dpo_seed_42_metadata.json
results/training_logs/training_summary.csv
```

---

## Validation-only smoke testing

After training, validation-only smoke tests were run to check whether the saved adapters could load and respond to safety-sensitive prompts. The locked test set was not used.

The smoke tests examined direct crisis, diagnosis-boundary, and medication-boundary prompts. They showed that raw prompting and post-training alone did not reliably produce safe behaviour in all safety-critical cases.

The most important finding from smoke testing was:

```text
Post-training and safety prompting alone were not sufficient to guarantee reliable safety-critical behaviour in this small local model.
```

This finding shaped the final evaluation design. The trained models were retained as research prototypes, but not presented as deployment-ready safety solutions.

---

## Deterministic safety router used in evaluation

A deterministic safety router was added after validation-only smoke testing. The router operated before model generation in the guarded evaluation conditions.

The inference flow was:

```text
User prompt
→ rule-based safety check
→ if crisis / diagnosis boundary / medication boundary / harmful-advice risk is detected:
      return controlled safety response
→ otherwise:
      use model generation
```

The router checked only the user prompt text. It did not use test-set labels, scores, or expected answers.

The router is not presented as a complete safety solution. It is a lightweight deterministic guardrail evaluated alongside raw model behaviour.

In the locked test-set outputs, the router was applied to 10 prompts per guarded condition. This conservative coverage means the guarded results should not be interpreted as proof that all safety-sensitive prompts were solved. Ambiguous crisis signals remained a limitation.

---

## Completed training status

Both post-training stages completed successfully:

| Stage | Status | Adapter |
|---|---|---|
| SFT | Complete | `models/sft/seed_42/final_adapter` |
| DPO | Complete | `models/dpo/seed_42/final_adapter` |

Training remained frozen during locked test-set evaluation. The locked test set was not used to retrain, retune, or modify the SFT adapter, DPO adapter, safety prompt, or deterministic router.

The final evaluation results are reported in:

```text
docs/evaluation_results_report.md
docs/error_analysis.md
```

---

## Limitations

The training phase has several limitations.

First, training was constrained by local Apple Silicon memory limits. This required CPU float32 training and a smaller LoRA configuration.

Second, `max_seq_length=640` may truncate some longer training examples. This was accepted as a compute-driven compromise after token-length analysis and memory testing.

Third, only one seed was trained. Multiple seeds would provide stronger evidence of robustness, but were not feasible within the local compute and time constraints.

Fourth, the base model is small. Absolute response quality is likely limited compared with larger open-source models.

Fifth, training and validation losses are useful for checking optimisation stability, but they do not directly measure safety, empathy, helpfulness, or clinical appropriateness.

Sixth, DPO validation reward accuracy and margin show that the model learned the constructed preference objective, but they do not prove that the model is safe.

Seventh, validation smoke testing and locked evaluation showed that raw post-trained outputs still failed or partially failed safety-sensitive prompts. The project therefore concludes that post-training alone should not be presented as sufficient for safe online mental-health support.
