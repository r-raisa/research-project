# Data split report

This report documents the train/validation/test split used for the project.

## Split method

- The combined prompt pool was split into train, validation and locked test sets.
- SyntheticSafety was split separately using exact category level counts.
- Bias/fairness prompts were split by `fairness_pair_id`, so matched pairs remain in the same split.
- Public dataset prompts were split using grouped, category aware splitting.
- Grouping prevents related prompts from the same question or conversation appearing in multiple splits.
- The held out test set is saved as `data/splits/test_prompts_LOCKED.jsonl` and must not be used during training or prompt/response generation.

## Train split

- Total prompts: 2429

### Source counts

- `counsel_chat`: 726
- `empathetic_dialogues`: 232
- `esconv`: 1363
- `synthetic_safety`: 108

### Category counts

- `anxiety`: 581
- `bias_fairness`: 24
- `crisis_risk`: 15
- `crisis_risk_ambiguous`: 12
- `crisis_risk_direct`: 12
- `diagnosis_boundary`: 28
- `everyday_stress`: 463
- `grief`: 29
- `harmful_advice`: 12
- `loneliness`: 14
- `low_mood`: 761
- `medication_boundary`: 22
- `over_reassurance_trap`: 12
- `privacy_dependence`: 12
- `relationship_distress`: 432

### Severity counts

- `high`: 68
- `low`: 463
- `medium`: 1898

### SyntheticSafety category counts

- `bias_fairness`: 24
- `crisis_risk_ambiguous`: 12
- `crisis_risk_direct`: 12
- `diagnosis_boundary`: 12
- `harmful_advice`: 12
- `medication_boundary`: 12
- `over_reassurance_trap`: 12
- `privacy_dependence`: 12

## Validation split

- Total prompts: 339

### Source counts

- `counsel_chat`: 78
- `empathetic_dialogues`: 29
- `esconv`: 196
- `synthetic_safety`: 36

### Category counts

- `anxiety`: 80
- `bias_fairness`: 8
- `crisis_risk`: 3
- `crisis_risk_ambiguous`: 4
- `crisis_risk_direct`: 4
- `diagnosis_boundary`: 7
- `everyday_stress`: 55
- `grief`: 4
- `harmful_advice`: 4
- `loneliness`: 4
- `low_mood`: 97
- `medication_boundary`: 7
- `over_reassurance_trap`: 4
- `privacy_dependence`: 4
- `relationship_distress`: 54

### Severity counts

- `high`: 18
- `low`: 55
- `medium`: 266

### SyntheticSafety category counts

- `bias_fairness`: 8
- `crisis_risk_ambiguous`: 4
- `crisis_risk_direct`: 4
- `diagnosis_boundary`: 4
- `harmful_advice`: 4
- `medication_boundary`: 4
- `over_reassurance_trap`: 4
- `privacy_dependence`: 4

## Test split

- Total prompts: 358

### Source counts

- `counsel_chat`: 115
- `empathetic_dialogues`: 39
- `esconv`: 168
- `synthetic_safety`: 36

### Category counts

- `anxiety`: 86
- `bias_fairness`: 8
- `crisis_risk`: 5
- `crisis_risk_ambiguous`: 4
- `crisis_risk_direct`: 4
- `diagnosis_boundary`: 10
- `everyday_stress`: 59
- `grief`: 5
- `harmful_advice`: 4
- `loneliness`: 5
- `low_mood`: 97
- `medication_boundary`: 9
- `over_reassurance_trap`: 4
- `privacy_dependence`: 4
- `relationship_distress`: 54

### Severity counts

- `high`: 25
- `low`: 59
- `medium`: 274

### SyntheticSafety category counts

- `bias_fairness`: 8
- `crisis_risk_ambiguous`: 4
- `crisis_risk_direct`: 4
- `diagnosis_boundary`: 4
- `harmful_advice`: 4
- `medication_boundary`: 4
- `over_reassurance_trap`: 4
- `privacy_dependence`: 4
