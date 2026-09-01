# Response Pair Generation Report

## Purpose

This document summarises the response-pair generation stage of the project.

The response-pair dataset is used to support therapy-specific post-training of an open-source language model for text-based online mental health support.

The goal of this stage was to create training and validation examples where the chosen response is safer, more empathetic, more bounded, and more helpful than the rejected response.

## Research context

This project investigates whether therapy-specific post-training can improve the safety and empathy of an open-source LLM for online mental health support compared with:

- the original base/instruct model
- a prompt-only safety baseline
- a supervised fine-tuned model
- an optional preference-trained model

The response-pair dataset supports the supervised fine-tuning and optional DPO stages.

## Input data

Response pairs were generated from the training and validation prompt splits only.

The locked test set was not used for response-pair generation.

Input prompt sources included:

- ESConv
- CounselChat
- EmpatheticDialogues
- SyntheticSafety

The locked test file remains separate:

- `data/splits/test_prompts_LOCKED.jsonl`

## Output files

The response-pair generation stage produces SFT and DPO files.

Pilot files:

- `data/splits/train_sft_pilot.jsonl`
- `data/splits/train_dpo_pilot.jsonl`
- `data/splits/validation_sft_pilot.jsonl`
- `data/splits/validation_dpo_pilot.jsonl`

Main files:

- `data/splits/train_sft.jsonl`
- `data/splits/train_dpo.jsonl`
- `data/splits/validation_sft.jsonl`
- `data/splits/validation_dpo.jsonl`

## Final row counts

| File | Row count |
|---|---:|
| `train_sft_pilot.jsonl` | 44 |
| `train_dpo_pilot.jsonl` | 44 |
| `validation_sft_pilot.jsonl` | 18 |
| `validation_dpo_pilot.jsonl` | 18 |
| `train_sft_main.jsonl` | 513 |
| `train_dpo_main.jsonl` | 513 |
| `validation_sft_main.jsonl` | 96 |
| `validation_dpo_main.jsonl` | 96 |

The final row counts are lower than the initial sampled prompt subsets because examples were excluded when model-generated chosen responses failed automatic quality or relevance checks. SFT and DPO row counts match within each split, indicating that each retained prompt has both a supervised chosen-response example and a preference pair.

## Generation method

Response pairs were generated using a hybrid method.

Chosen responses were generated using either:

1. Controlled templates.
2. Local model generation.

Rejected responses were generated using controlled flawed templates.

This hybrid approach was chosen because some prompts require fixed safety behaviour, while other prompts require flexible, prompt-specific support.

## Controlled chosen templates

Controlled chosen templates were used for prompts requiring fixed safety or boundary behaviour.

These included:

- SyntheticSafety prompts.
- Direct user-safety or crisis prompts.
- Direct harmful-advice/refusal prompts.
- Direct diagnosis requests.
- Direct medication-advice requests.
- Simple bereavement prompts.

Controlled templates were used in these cases to reduce the risk of unsafe model-generated responses.

## Local model-generated chosen responses

Local model generation was used for ordinary or nuanced public dataset prompts.

This included prompts where sensitive topics were mentioned as context but were not the direct user request.

Examples include:

- a relationship prompt mentioning medication as context
- a prompt involving suicide bereavement in another person
- a prompt mentioning an existing diagnosis
- a prompt where grief is part of a broader relational or emotional situation

Manual pilot review showed that these prompts were usually better handled by the model than by narrow templates, because the model could respond to the full context of the user’s message.

## Rejected responses

Rejected responses were generated using controlled flawed templates.

The rejected responses were intentionally lower quality than the chosen responses.

Rejected response failure modes included:

- low empathy
- poor safety
- weak boundaries
- over-reassurance
- unhelpful refusal
- dependence encouragement

Rejected responses were designed to be clearly worse than chosen responses without including graphic, instructional, or harmful content.

## Safety flagging approach

Safety flags were added as internal metadata for response-pair generation and validation.

The main internal flags were:

- `detected_risk_level`
- `requires_escalation`
- `requires_refusal`
- `boundary_issue`
- `risk_flags`

These flags were not intended to be shown to end users.

## Crisis escalation logic

Crisis escalation was narrowed during pilot review.

The pipeline does not automatically escalate based only on broad terms such as:

- death
- grief
- poison
- suicide bereavement
- loss

Instead, escalation is triggered when the prompt suggests that the user’s own safety may be at risk.

Direct crisis indicators include phrases such as:

- “I want to die”
- “I want to kill myself”
- “I do not want to be alive”
- “I should not be here”
- “I cannot keep going”
- “I cannot stay safe”

This prevents inappropriate crisis templates from being applied to bereavement or third-person suicide references.

## Boundary detection logic

Boundary detection was also narrowed during pilot review.

Diagnosis-boundary templates are used when the user directly asks for diagnosis or diagnostic confirmation.

Medication-boundary templates are used when the user directly asks for medication advice, dosage advice, or whether to start, stop, increase, decrease, or change medication.

Prompts that merely mention medication or diagnosis as context are routed to local model generation.

## Simple bereavement handling

A controlled grief template was added for short, direct bereavement prompts.

This was added after pilot review found that the local model could respond too literally to the cause of death, rather than providing grief support.

The grief template focuses on:

- acknowledging the loss
- validating shock, confusion, and sadness
- encouraging trusted support
- suggesting professional support if the grief feels too heavy
- including crisis escalation only if the user feels unsafe or unable to cope

Longer nuanced prompts that mention loss as context are routed to local model generation.

## Pilot review findings

The pilot review found that the initial routing logic was too broad.

Some public prompts were routed to controlled templates because of category labels, even when the actual user request was more nuanced.

Examples included:

- a relationship prompt mentioning anxiety medication being incorrectly routed to a medication-boundary template
- a relationship prompt involving suicide bereavement being incorrectly routed to a crisis template
- a prompt mentioning a diagnosis being incorrectly routed to a diagnosis-boundary template
- a direct bereavement prompt initially being handled poorly by the local model

The response-pairing pipeline was revised based on these findings.

## Final routing policy

The final routing policy is:

Controlled templates are used for:
- SyntheticSafety prompts.
- Direct user-safety or crisis prompts.
- Direct harmful-advice/refusal prompts.
- Direct diagnosis requests.
- Direct medication-advice requests.
- Simple bereavement prompts.

Local model generation is used for:
- ordinary public prompts
- nuanced public prompts
- relationship prompts
- anxiety prompts
- low-mood prompts
- prompts where medication, diagnosis, grief, or suicide bereavement are mentioned as context rather than as the direct request

## Automatic validation

The response-pair files were automatically validated.

Validation checked for:

- missing prompt IDs
- missing prompts
- missing chosen responses
- missing rejected responses
- identical chosen and rejected responses
- very short responses
- cut-off or unfinished responses
- missing escalation language where escalation was required
- weak refusal wording where refusal was required
- responses that may be too generic or not prompt-specific

Errors caused validation to fail.

Warnings were used to flag examples for manual review.

## Manual inspection

Manual inspection was conducted because automatic validation cannot fully assess response relevance, empathy, or contextual appropriateness.

Manual inspection focused on examples from categories including:

- grief
- crisis risk
- diagnosis boundary
- medication boundary
- harmful advice
- anxiety
- low mood
- relationship distress

Chosen responses were reviewed for:

- safety
- empathy
- prompt relevance
- crisis escalation where required
- appropriate refusal where required
- appropriate boundaries
- avoidance of diagnosis
- avoidance of medication advice
- avoidance of over-reassurance
- avoidance of dependence encouragement
- no obvious hallucinated details
- no cut-off or unfinished responses

Rejected responses were reviewed for:

- being clearly worse than the chosen response
- representing the intended failure mode
- avoiding graphic or instructional harmful content
- avoiding unsafe procedural detail

## Validation outcome

Pilot validation passed after revisions to the safety flagging and routing logic.
During main response-pair validation, one generated response was found to be cut off. The response-pair generation pipeline was updated so that unfinished responses are rejected before training-file creation. The main response-pair files were then regenerated and revalidated successfully.

Main validation outcome:

- The main response-pair files passed automatic validation.

## Manual inspection outcome

Manual inspection of the main response-pair files found that the final routing logic improved relevance for nuanced public prompts while preserving controlled safety behaviour for clear safety and boundary cases.

The dataset was considered suitable for the next stage of the project, with the limitation that manual inspection was spot-check based rather than exhaustive.

## Limitations

This response-pair dataset has several limitations.

First, automatic validation can detect formatting and obvious safety issues, but it cannot fully judge clinical quality, nuance, or emotional appropriateness.

Second, manual review was based on spot checks rather than exhaustive review of every generated response.

Third, local model-generated responses may still contain some generic, awkward, or imperfect phrasing.

Fourth, controlled templates improve consistency for safety-critical cases but may be less natural than model-generated responses.

Fifth, the response pairs are intended for a research prototype only and are not a substitute for clinically validated mental health support.

## Final decision

The response-pair generation stage is complete. The files passed automatic validation and were manually spot-checked for safety, relevance, empathy, and boundary handling.

The response-pair dataset is ready for the next stage: supervised fine-tuning.
