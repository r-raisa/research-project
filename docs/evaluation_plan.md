# Evaluation Plan

## Purpose

This document defines the evaluation phase for the therapy-specific LLM post-training project.

The aim is to assess whether post-training improves the safety, empathy, helpfulness, and boundary awareness of an open-source language model for text-based mental-health support.

The evaluation also tests whether raw post-training is sufficient for safety-critical prompts, or whether deterministic safety routing is required.

## Locked test set

The locked test set is:

```text
data/splits/test_prompts_LOCKED.jsonl

The locked test set was not used during:

- training
- response-pair generation after splitting
- SFT
- DPO
- prompt iteration
- validation smoke testing
- router development

It is used only after the inference setup is frozen.

## Model conditions

The raw model conditions are:

Label	Condition	Description
M0	| m0_base | Base model without the safety system prompt
M1	| m1_prompt_only |	Base model with the safety system prompt
M2	| m2_sft	| SFT adapter with the safety system prompt
M3	| m3_dpo |	DPO adapter with the safety system prompt

The guarded model conditions are:

Label	Condition	Description
M1g	| m1_prompt_only_guarded |	Prompt-only baseline with deterministic safety router
M2g	| m2_sft_guarded |	SFT model with deterministic safety router
M3g	| m3_dpo_guarded |	DPO model with deterministic safety router

The guarded conditions use the same underlying models as the raw conditions, but apply a deterministic safety router before model generation.

## Router

Validation-only smoke testing showed that raw model outputs were not reliably safe for crisis, diagnosis-boundary, and medication-boundary prompts.

A deterministic safety router was therefore added before locked test-set evaluation.

The router checks only the user prompt text. It does not use the dataset category label, test-set metadata, or expected answer

Route type:
Crisis risk
Behaviour:
Immediate real-world support, emergency/crisis/trusted-person escalation, do not stay alone, move away from means, not an emergency service

Route type:
Diagnosis boundary
Behaviour:
No diagnosis, no specific disorder suggestion, bounded reflection, professional support if intense/persistent/worsening/unsafe

Route type:
Medication boundary
Behaviour:
No medication instruction, no claim that stopping/restarting/changing medication is safe, contact prescriber/GP/doctor/pharmacist promptly

Route type:
Harmful advice
Behaviour:
Refuse harmful instructions and direct to safe real-world support if risk is present. 

For non-routed prompts, the model generates normally.

## Router smoke test

Prompt ID                          Category
synthetic_crisis_direct_005 |      crisis_risk_direct
synthetic_diagnosis_boundary_017 | diagnosis_boundary
