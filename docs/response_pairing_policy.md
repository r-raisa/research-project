# Response pairing policy

## Purpose

This document defines how prompt/chosen/rejected response pairs are created for SFT and DPO.

## Data used

Response pairs are created only from:

- `data/splits/train_prompts.jsonl`
- `data/splits/validation_prompts.jsonl`

The locked test set is not used during response-pair generation, model training, prompt tuning, or validation decisions.

## Chosen response definition

A chosen response should:

- acknowledge the user's feelings before offering support
- maintain an empathetic and respectful tone
- avoid diagnosis, clinical claims, medication advice, or treatment instructions
- avoid presenting the assistant as a therapist, clinician, emergency service, or substitute for professional support
- offer one or two realistic next steps where appropriate
- offer simple coping or emotional regulation strategies where appropriate
- avoid encouraging dependence on the assistant
- suggest real-world support where appropriate
- escalate clearly when severe risk, self-harm, harm to others, abuse, or inability to stay safe is present

## Relevance requirement

Chosen responses must respond to the specific situation described in the prompt.

A chosen response is excluded if it:

- gives only generic emotional support
- does not mention or reflect the user's actual concern
- uses the same wording across many unrelated prompts
- offers coping strategies that do not fit the user's situation
- escalates when escalation is not required
- refuses when refusal is not required

For public dataset prompts, the chosen response should naturally refer to at least one concrete detail from the user's message. Public chosen responses that are safe but too generic are excluded before training.
Safe but irrelevant responses are not suitable for SFT or DPO training.

## Rejected response definition

A rejected response should be clearly worse than the chosen response, but must not contain graphic harmful content or actionable dangerous advice.

Rejected responses may be flawed in one of the following ways:

- `low_empathy`: practical but emotionally flat
- `poor_safety`: treats serious risk as routine
- `over_reassurance`: gives false certainty or minimises distress
- `boundary_weak`: oversteps appropriate support-tool limits
- `unhelpful_refusal`: refuses to engage without useful support
- `dependence_encouraging`: encourages reliance on the tool rather than real-world support

## Safety rule for rejected responses

Rejected responses must not include:

- self-harm instructions
- violent instructions
- abuse, deception, or exploitation guidance
- medication dosages or medication-change advice
- clinical advice
- graphic harmful details

## Quality threshold

Response pairs are checked against the same core dimensions used in the evaluation framework:

- Safety
- Empathy
- Helpfulness
- Boundaries
- Crisis Escalation
- Fairness

All chosen responses must be acceptable on Safety, Empathy, Helpfulness and Boundaries.

Crisis Escalation is additionally required for prompts where `requires_escalation = true`. In these cases, the chosen response must clearly encourage immediate real-world support, such as emergency services, a crisis line, or a trusted person who can support the user immediately.

Fairness is additionally assessed for `bias_fairness` prompts and matched fairness pairs. The chosen response should provide substantively equivalent support across paired prompts and should not change tone, helpfulness, concern, or assumptions based only on identity or demographic details.

Pairs that fail required safety or quality checks are excluded from the training dataset.

## Minimum contrast requirement

Chosen and rejected responses must be clearly distinguishable.

A pair is excluded if:

- the chosen and rejected responses are identical
- the chosen and rejected responses are near-identical after normalisation
- the rejected response is not clearly worse than the chosen response on at least one scoring dimension
- the chosen response is less safe than the rejected response

Where implemented, semantic similarity may be checked using sentence embeddings. Pairs with cosine similarity above 0.95 are treated as near-duplicates and excluded. 

## Pair metadata

Each response pair is saved with metadata to support reproducibility and auditing.

Required fields:

- `prompt_id`: links back to the prompt-pool record
- `prompt`: the original user prompt
- `chosen`: the preferred response
- `rejected`: the lower-quality comparison response
- `category`: prompt category
- `severity`: prompt severity
- `source_dataset`: original source dataset
- `detected_risk_level`: internal risk level assigned by the safety-flagging code
- `requires_escalation`: whether the prompt requires crisis escalation
- `requires_refusal`: whether the prompt requires refusal
- `boundary_issue`: whether the prompt involves boundary-sensitive content
- `risk_flags`: internal safety flags assigned to the prompt
- `chosen_generation_method`: for example, `template`, `model`, or `manual`
- `chosen_generator`: template version or model name used for the chosen response
- `rejected_generation_method`: for example, `template`, `model`, or `manual`
- `rejected_type`: the failure mode used to generate the rejected response
- `pair_quality_status`: for example, `checked`, `excluded`, or `pending_review`
- `generation_date`: ISO date of generation

## Chosen response generation

Chosen responses are created using the method recorded for that version of the dataset.

For the first pilot version, chosen responses are created using fixed templates for each category. These templates are designed to make the responses safe, empathetic, helpful, and clear about the assistant’s limits.

For the response-pairing stage, chosen responses are created using a hybrid method.

SyntheticSafety prompts use fixed category-specific templates. This keeps safety critical behaviours controlled and consistent for crisis escalation, harmful advice refusal, diagnosis boundaries, medication boundaries, dependence boundaries, over-reassurance, and fairness prompts.

Public dataset prompts use local model generation with the safety system prompt in `configs/generation_config.yaml`. This is used because public prompts are more varied and require responses that refer to the user's specific situation.

Rejected responses are generated using controlled flawed templates. This keeps the contrast clear while avoiding graphic or procedurally harmful content.

For model generation, the default settings are:

- temperature: 0.7
- top_p: 0.9
- max_new_tokens: 384

Before a response is added to the training dataset, it is checked against the quality rules. Responses that fail the required safety or quality checks are excluded from the training dataset.