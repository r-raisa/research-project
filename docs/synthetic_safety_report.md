# SyntheticSafety dataset report

This report documents the manually created SyntheticSafety prompt dataset.

## Dataset location

- Path: `/Users/raisa/Desktop/Research Project/git-repo/research-project/data/processed/synthetic_safety_prompts.jsonl`

## Purpose

SyntheticSafety provides controlled prompts for evaluating safety-critical behaviour in therapy-style language model responses. It covers crisis risk, harmful-advice refusal, diagnosis boundaries, medication boundaries, privacy/dependence boundaries, over-reassurance, and bias/fairness.

## Total prompts

- Total: 180

## Category counts

- `bias_fairness`: 40
- `crisis_risk_ambiguous`: 20
- `crisis_risk_direct`: 20
- `diagnosis_boundary`: 20
- `harmful_advice`: 20
- `medication_boundary`: 20
- `over_reassurance_trap`: 20
- `privacy_dependence`: 20

## Severity counts

- `high`: 70
- `medium`: 110

## Risk type counts

- `altering_tablets`: 1
- `ambiguous_self_harm_risk`: 20
- `availability_boundary`: 2
- `avoidance_of_real_support`: 1
- `chatbot_dependence`: 3
- `chatbot_overattachment`: 2
- `clinical_boundary`: 20
- `concealment_of_self_harm_risk`: 2
- `coping_dependence`: 1
- `deceptive_help_seeking`: 2
- `dose_increase_request`: 1
- `dose_misuse`: 1
- `drug_interaction_question`: 1
- `eating_related_harm`: 2
- `fairness`: 40
- `false_reassurance`: 20
- `harmful_advice_seeking`: 3
- `isolation_and_escape_risk`: 1
- `isolation_risk`: 1
- `medication_access_problem`: 1
- `medication_adherence`: 1
- `medication_alcohol_interaction`: 1
- `medication_choice_request`: 1
- `medication_discontinuation_question`: 1
- `medication_misuse_harm`: 1
- `missed_dose_double_dose`: 1
- `pregnancy_medication_safety`: 1
- `privacy_boundary`: 1
- `professional_support_boundary`: 1
- `reassurance_dependence`: 1
- `refusal_of_real_support`: 1
- `risk_seeking_harm`: 1
- `secrecy_and_dependence`: 1
- `self_harm_detail_seeking`: 1
- `self_harm_method_seeking`: 1
- `self_harm_minimisation`: 1
- `self_harm_normalisation`: 1
- `self_harm_risk`: 20
- `self_punishment_harm`: 1
- `side_effect_question`: 1
- `sleeping_pill_use`: 1
- `social_withdrawal`: 3
- `stopping_medication`: 5
- `substance_related_harm`: 2
- `supplement_interaction`: 1
- `taking_someone_elses_medication`: 1
- `therapy_replacement`: 2
- `unsafe_coping_seeking`: 1

## Fairness pairs

- Matched fairness pairs: 20

## Notes

- Prompts are synthetic and do not contain real patient data.
- Crisis prompts are non-graphic and test escalation behaviour without harmful detail.
- Bias/fairness prompts use matched pairs so that only one identity or contextual attribute changes within a pair.
- The dataset must be split before training so held-out prompts are not seen during post-training.
