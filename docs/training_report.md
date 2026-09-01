# Training Report

## Purpose

This document records the training phase for the project.

The aim of this phase was to train post-trained model variants that can later be compared against the original base model and a prompt-only safety baseline.

The overall project investigates whether therapy-specific post-training can improve the safety, empathy, helpfulness, and boundary awareness of an open-source language model for text-based online mental health support.

This training phase uses the response-pair dataset created in the previous stage. The locked test set is not used during training.

## Training stages

The intended training pipeline consists of two stages:

1. Supervised Fine-Tuning (SFT)
2. Direct Preference Optimisation (DPO)

SFT is used to teach the model the style and content of safe, empathetic, bounded responses.

DPO is used to further optimise the model to prefer safer and more empathetic chosen responses over controlled lower-quality rejected responses.

Initial SFT attempts using Apple Silicon MPS failed due to out-of-memory errors. One MPS run also produced unstable values, including `NaN` gradient norms. To ensure a valid and reproducible training run, SFT was moved to CPU float32 training. This increased training time but produced stable finite losses and successfully saved the LoRA adapter.

## Model variants for evaluation

The final evaluation phase will compare the following model conditions:

| Label | Model condition | Status |
|---|---|---|
| M0 | Base open-source instruction model | Pending evaluation |
| M1 | Prompt-only safety baseline | Pending evaluation |
| M2 | SFT model | Trained |
| M3 | SFT + DPO model | Pending training |

## Base model

The base model used for training was:

```text
Qwen/Qwen2.5-0.5B-Instruct

## SFT training outcome

SFT training completed successfully for seed 42.

The model was trained on CPU using float32 after earlier MPS attempts failed due to memory limits and unstable gradients. The final successful run used the compute-adjusted configuration described above.

### SFT metrics

| Metric | Value |
|---|---:|
| Training examples | 513 |
| Validation examples | 96 |
| Epochs completed | 2.99 |
| Final training loss | 1.8315 |
| Final validation loss | 1.3047 |
| Training runtime | 3718.82 seconds |
| Training time | approximately 63.18 minutes |
| Device | CPU |
| Dtype | float32 |
| Adapter path | `models/sft/seed_42/final_adapter` |

## SFT smoke test

After SFT training, the saved LoRA adapter was loaded with the base model and tested on a small number of validation prompts. The locked test set was not used.

The purpose of this check was only to confirm that the adapter could be loaded and used for generation before moving to DPO. Formal model comparison is deferred to the evaluation phase.

Smoke-test result:

- Passed
- Notes:
  - Outputs were coherent, relevant, and safe.

### Validation loss by epoch

| Epoch | Validation loss |
|---:|---:|
| 1.0 | 2.1459 |
| 2.0 | 1.5785 |
| 2.99 | 1.3047 |

The training and validation losses decreased over the run, and gradient norms remained finite during the successful CPU run. This indicates that the SFT run completed stably.