# Response Pair Pilot Review

## Purpose

This document records the pilot review process for the response pair generation stage of the project.

The purpose of the pilot was to test whether the response pair pipeline could generate safe, empathetic, relevant, and bounded chosen responses, alongside lower quality rejected responses, before scaling to the main response pair dataset.

The pilot was used to identify problems in:
- safety flagging
- crisis escalation logic
- boundary detection
- response routing logic
- template quality
- local model generation quality
- validation checks

## Pilot files reviewed

The following pilot files were generated and reviewed:

- `data/splits/train_sft_pilot.jsonl`
- `data/splits/train_dpo_pilot.jsonl`
- `data/splits/validation_sft_pilot.jsonl`
- `data/splits/validation_dpo_pilot.jsonl`

The DPO files were prioritised for manual review because they show the prompt, chosen response, and rejected response together.

## Pilot method

The pilot used a hybrid response-pairing approach.

Chosen responses were generated using either:

1. Controlled templates for prompts requiring fixed safety or boundary behaviour (e.g. cases of self harm or self diagnosis).
2. Local model generation for ordinary or nuanced public dataset prompts.

Rejected responses were generated using controlled flawed templates. These rejected responses were designed to be clearly worse than the chosen responses while still avoiding graphic, instructional, or harmful content.

## Initial pilot issues

Manual inspection found that the initial routing logic was too broad.

Some prompts were routed to controlled templates simply because their category label suggested a safety or boundary issue. However, several public dataset category labels were noisy or too broad.

This caused some responses to be safe but not relevant enough to the user’s actual prompt and thus not helpful.

## Examples of issues found

### 1. Grief prompt handled poorly by the local model

A prompt about the user’s father dying after accidentally ingesting rat poison was initially handled by the local model. The model focused too literally on rat poison safety and medical follow-up rather than grief support.

This was inappropriate because the user had stated that their father had died. The response should have focused on bereavement, emotional shock, and support.

Decision:
- Simple bereavement prompts should use a controlled grief template.
- Grief prompts should not automatically be treated as crisis prompts unless the user’s own safety is at risk.

### 2. Suicide bereavement incorrectly treated as user crisis

A prompt about the user’s boyfriend losing his father to suicide was incorrectly routed to the crisis-escalation template. The resulting chosen response treated the user as if they were personally unsafe.

This was not relevant to the prompt. The user was asking why their boyfriend was emotionally withdrawing after bereavement.

Decision:
- References to suicide as bereavement context should not automatically trigger user crisis escalation.
- Crisis escalation should be based on the user’s own safety risk, not on any mention of suicide, death, or loss.

### 3. Medication mentioned as context incorrectly routed to medication-boundary template

A relationship prompt mentioned that the user’s wife was taking anxiety medication and that low libido may be a side effect. The actual request was about how to communicate honestly about intimacy.

The prompt was incorrectly routed to the medication-boundary template, which focused on not changing medication and speaking to a prescriber. This did not answer the user’s actual concern.

Decision:
- Medication mentions should not automatically trigger medication-boundary templates.
- Medication-boundary templates should only be used when the user directly asks for medication advice, dosage advice, or whether to start, stop, increase, decrease, or change medication.

### 4. Diagnosis-related category incorrectly routed to diagnosis-boundary template

A prompt mentioned autism and abuse history but asked how the user could feel more comfortable around other people. The diagnosis template was too narrow and did not address the user’s actual concern.

Decision:
- Diagnosis-boundary templates should only be used when the user directly asks for diagnosis or diagnostic confirmation.
- Public prompts that mention a diagnosis as context should usually use local model generation.

## Changes made after pilot review

### 1. Safety flags recomputed from scratch

The safety flagging function was revised so that generated flags are recomputed from scratch.

The pipeline no longer blindly preserves old values such as:

- `requires_escalation`
- `requires_refusal`
- `boundary_issue`

This prevents outdated flags from earlier runs being carried forward into new response-pair files.

### 2. Crisis detection narrowed

Crisis detection was changed so that broad keywords such as death, grief, poison, or suicide bereavement do not automatically require escalation.

Escalation is now triggered only when the prompt suggests that the user’s own safety may be at risk.

Examples of direct crisis indicators include:

- “I want to die”
- “I want to kill myself”
- “I do not want to be alive”
- “I should not be here”
- “I cannot keep going”
- “I cannot stay safe”

This keeps crisis escalation for genuinely high-risk user-safety prompts, while avoiding inappropriate crisis templates for bereavement or third-person references.

### 3. SyntheticSafety handled separately from public datasets

SyntheticSafety prompts are deliberately constructed safety cases. Therefore, their category labels can be used to trigger safety and boundary flags.

Public dataset categories are noisier and broader. Therefore, public category labels no longer automatically force controlled templates.

This prevents nuanced public prompts from being over-routed to generic safety templates.

### 4. Boundary detection narrowed

Boundary templates are now used only when the prompt directly requests a diagnosis or medication advice.

Direct diagnosis requests include prompts such as:

- “Do I have depression?”
- “Do you think I have anxiety?”
- “Am I bipolar?”
- “Diagnose me”
- “What disorder do I have?”

Direct medication advice requests include prompts such as:

- “Should I stop taking my medication?”
- “Should I increase my dose?”
- “What dose should I take?”
- “Should I change my medication?”

Prompts that merely mention a diagnosis or medication as context are routed to local model generation.

### 5. Simple bereavement template added

A controlled grief template was added for short, direct bereavement prompts.

This was added because the local model sometimes responded too literally to details around the death, rather than providing grief support.

The grief template is used for simple bereavement prompts, while longer nuanced prompts that mention loss as context are routed to local model generation.

### 6. Response routing narrowed

The final routing logic is:

Controlled templates are used for:
- SyntheticSafety prompts.
- Direct user-safety or crisis prompts.
- Direct harmful-advice/refusal prompts.
- Direct diagnosis requests.
- Direct medication-advice requests.
- Simple bereavement prompts.

Local model generation is used for:
- ordinary public dataset prompts
- nuanced public prompts
- relationship prompts
- low mood prompts
- anxiety prompts
- prompts where grief, suicide bereavement, medication, or diagnosis are mentioned as context but are not the direct request

### 7. Validation checks improved

Validation was expanded to check for:

- missing prompt IDs
- missing prompts
- missing chosen or rejected responses
- identical chosen and rejected responses
- very short responses
- responses that appear cut off or unfinished
- missing crisis escalation when escalation is required
- weak refusal wording when refusal is required
- generic responses with little prompt-specific overlap

Warnings are used for cases that may need manual inspection. Errors are used for failures that should stop the pipeline.

## Final pilot validation result

After the safety flagging and routing changes, the pilot response-pair files passed automatic validation.

Manual inspection also showed improved relevance for nuanced public prompts after they were routed to local model generation instead of broad templates.

## Manual review checklist

Chosen responses were reviewed for:

- safety
- empathy
- relevance to the user’s specific prompt
- appropriate emotional support
- appropriate crisis escalation where required
- refusal of harmful advice where required
- avoidance of diagnosis
- avoidance of medication advice
- avoidance of over-reassurance
- avoidance of dependence encouragement
- no obvious hallucinated details
- no cut-off or unfinished responses

Rejected responses were reviewed for:

- being clearly worse than the chosen response
- being less empathetic, less safe, less bounded, or less helpful
- not containing graphic, instructional, or procedurally harmful content
- preserving a controlled failure mode

## Final pilot decision

The pilot identified important problems in the initial routing logic.

These problems were addressed by narrowing safety and boundary detection, separating SyntheticSafety logic from public dataset logic, adding a simple bereavement template, and routing nuanced public prompts to the local model.

Final decision:

Proceed to main response-pair generation, followed by automatic validation and manual spot-checking of the main response-pair files.
