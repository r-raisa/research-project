# Prompt pool report

This report documents the combined prompt pool used for dataset construction.

## Files

- Prompt pool: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/processed/prompt_pool.jsonl`
- Response candidates: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/processed/response_candidates.jsonl`

## Total counts

- Total prompt rows: 3126
- Total response candidates: 17522

## Source counts

- `counsel_chat`: 919
- `empathetic_dialogues`: 300
- `esconv`: 1727
- `synthetic_safety`: 180

## Category counts

- `anxiety`: 747
- `bias_fairness`: 40
- `crisis_risk`: 23
- `crisis_risk_ambiguous`: 20
- `crisis_risk_direct`: 20
- `diagnosis_boundary`: 45
- `everyday_stress`: 577
- `grief`: 38
- `harmful_advice`: 20
- `loneliness`: 23
- `low_mood`: 955
- `medication_boundary`: 38
- `over_reassurance_trap`: 20
- `privacy_dependence`: 20
- `relationship_distress`: 540

## Severity counts

- `high`: 111
- `low`: 577
- `medium`: 2438

## Extraction method counts

- `manual_synthetic`: 180
- `prompt`: 300
- `questionText`: 919
- `situation`: 1227
- `usr_dialog_turn`: 500

## Dataset-specific extraction decisions

- CounselChat: `questionText` was extracted as the prompt. `answerText` was kept separately as an unchecked response candidate. Duplicate questions were deduplicated by normalised prompt text.
- ESConv: the JSON stored in `text` was parsed. `situation` and meaningful `usr` turns were extracted as prompts. `sys` turns were kept as unchecked response candidates.
- EmpatheticDialogues: `prompt` was extracted as supplementary low-risk empathy data. The dataset was capped so it does not dominate the prompt pool.
- SyntheticSafety: controlled prompts were included from the manually validated JSONL file.

## Important limitation

Response candidates are not treated as final chosen responses. They require later filtering, rewriting or scoring before SFT/DPO training.