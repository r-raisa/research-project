# Evaluation Results Report

## Purpose

This report summarises the final locked test-set evaluation. Generated outputs were manually scored using a 0-5 rubric for safety, empathy, helpfulness, boundaries, crisis escalation where applicable, and fairness. Critical safety failure was scored separately as a binary 0/1 label. Statistical results are regenerated from the completed blinded scoring file rather than edited by hand.

## Condition summary

| condition | n | overall_core_mean | safety_mean | empathy_mean | helpfulness_mean | boundaries_mean | fairness_mean | crisis_escalation_mean | critical_safety_failure_count | critical_safety_failure_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| m0_base | 358.000 | 3.434 | 3.522 | 3.372 | 2.743 | 3.662 | 3.872 | 0.941 | 16.000 | 0.045 |
| m1_prompt_only | 358.000 | 3.094 | 3.209 | 2.603 | 2.366 | 3.335 | 3.955 | 2.765 | 9.000 | 0.025 |
| m2_sft | 358.000 | 3.101 | 3.193 | 2.673 | 2.369 | 3.318 | 3.953 | 2.059 | 5.000 | 0.014 |
| m3_dpo | 358.000 | 3.204 | 3.299 | 2.838 | 2.489 | 3.427 | 3.969 | 2.294 | 6.000 | 0.017 |
| m1_prompt_only_guarded | 358.000 | 3.090 | 3.198 | 2.589 | 2.369 | 3.338 | 3.955 | 2.529 | 8.000 | 0.022 |
| m2_sft_guarded | 358.000 | 3.108 | 3.201 | 2.670 | 2.385 | 3.332 | 3.953 | 2.294 | 3.000 | 0.008 |
| m3_dpo_guarded | 358.000 | 3.205 | 3.296 | 2.827 | 2.497 | 3.436 | 3.969 | 2.294 | 4.000 | 0.011 |

## Main findings

The primary safety outcome was the binary critical safety-failure rate, because a mental-health support system can appear fluent while still failing on rare high-risk prompts. The base model had a critical safety-failure rate of 0.045. The final raw DPO condition reduced this to 0.017, and the guarded DPO condition reduced it to 0.011. The end-to-end M0-M3 McNemar-style comparison gave p=0.006, and the M0-M3g comparison gave p=0.002. This is the strongest evidence that the final framework reduced severe failures relative to the unprompted base model.

Aggregate quality scores show a different pattern. The base model had an overall core mean of 3.434, while M3 scored 3.204 and M3g scored 3.205. This shows why average quality scores are insufficient as the sole measure: the base model often produced more fluent or detailed responses, but those responses were less reliable on non-negotiable safety boundaries.

Prompting reduced critical failures compared with the base model, but reduced empathy, helpfulness, and overall core quality. SFT did not clearly improve aggregate rubric scores over the prompt-only baseline, although it had fewer critical failures. DPO improved safety, empathy, helpfulness, boundaries, and the overall core mean relative to SFT, but did not eliminate critical failures. The Wilcoxon effect size for M0-M3 safety was r=-0.343 and for M0-M3g safety was r=-0.355.

The guarded conditions produced only small aggregate changes because the deterministic router was deliberately conservative and applied to a small subset of prompts. It improved several explicitly detected safety-sensitive cases, especially direct crisis and medication-boundary prompts, but it did not catch all ambiguous crisis signals.

## Primary unresolved failure mode: ambiguous crisis risk

The clearest unresolved weakness was `crisis_risk_ambiguous`. These prompts express hopelessness or indirect risk without always using explicit self-harm language. The deterministic router intentionally avoided using test-set labels and therefore did not route every ambiguous case. Across the category-level results, ambiguous-crisis critical failures remained present (m0_base: 2/4; m1_prompt_only: 1/4; m2_sft: 1/4; m3_dpo: 1/4; m1_prompt_only_guarded: 1/4; m2_sft_guarded: 1/4; m3_dpo_guarded: 1/4). This means the final framework reduced some explicit safety failures but did not solve ambiguous crisis detection.

## Key statistical comparisons

| comparison | outcome | n_pairs | mean_a | mean_b | mean_difference_b_minus_a | bootstrap_ci_low | bootstrap_ci_high | effect_size_r | test | p_value | p_value_fdr_bh |
|---|---|---|---|---|---|---|---|---|---|---|---|
| m0_base vs m1_prompt_only | safety | 358.000 | 3.522 | 3.209 | -0.313 | -0.402 | -0.221 | -0.411 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m1_prompt_only | empathy | 358.000 | 3.372 | 2.603 | -0.768 | -0.891 | -0.648 | -0.687 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m1_prompt_only | helpfulness | 358.000 | 2.743 | 2.366 | -0.377 | -0.461 | -0.293 | -0.535 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m1_prompt_only | boundaries | 358.000 | 3.662 | 3.335 | -0.327 | -0.419 | -0.229 | -0.440 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m1_prompt_only | critical_safety_failure | 358.000 | 0.045 | 0.025 | -0.020 |  |  |  | mcnemar_exact_binomial | 0.118 | 0.215 |
| m0_base vs m3_dpo | safety | 358.000 | 3.522 | 3.299 | -0.223 | -0.318 | -0.131 | -0.343 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo | empathy | 358.000 | 3.372 | 2.838 | -0.534 | -0.654 | -0.416 | -0.571 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo | helpfulness | 358.000 | 2.743 | 2.489 | -0.254 | -0.338 | -0.170 | -0.463 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo | boundaries | 358.000 | 3.662 | 3.427 | -0.235 | -0.338 | -0.134 | -0.365 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo | critical_safety_failure | 358.000 | 0.045 | 0.017 | -0.028 |  |  |  | mcnemar_exact_binomial | 0.006 | 0.015 |
| m0_base vs m3_dpo_guarded | safety | 358.000 | 3.522 | 3.296 | -0.226 | -0.318 | -0.134 | -0.355 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo_guarded | empathy | 358.000 | 3.372 | 2.827 | -0.545 | -0.665 | -0.425 | -0.572 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo_guarded | helpfulness | 358.000 | 2.743 | 2.497 | -0.246 | -0.330 | -0.162 | -0.441 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo_guarded | boundaries | 358.000 | 3.662 | 3.436 | -0.226 | -0.330 | -0.126 | -0.345 | wilcoxon_signed_rank | 0.000 | 0.000 |
| m0_base vs m3_dpo_guarded | critical_safety_failure | 358.000 | 0.045 | 0.011 | -0.034 |  |  |  | mcnemar_exact_binomial | 0.002 | 0.005 |
| m1_prompt_only vs m2_sft | safety | 358.000 | 3.209 | 3.193 | -0.017 | -0.103 | 0.067 | -0.025 | wilcoxon_signed_rank | 0.720 | 0.800 |
| m1_prompt_only vs m2_sft | empathy | 358.000 | 2.603 | 2.673 | 0.070 | -0.056 | 0.196 | 0.103 | wilcoxon_signed_rank | 0.135 | 0.232 |
| m1_prompt_only vs m2_sft | helpfulness | 358.000 | 2.366 | 2.369 | 0.003 | -0.084 | 0.087 | 0.001 | wilcoxon_signed_rank | 0.990 | 1.000 |
| m1_prompt_only vs m2_sft | boundaries | 358.000 | 3.335 | 3.318 | -0.017 | -0.112 | 0.078 | -0.035 | wilcoxon_signed_rank | 0.614 | 0.722 |
| m1_prompt_only vs m2_sft | critical_safety_failure | 358.000 | 0.025 | 0.014 | -0.011 |  |  |  | mcnemar_exact_binomial | 0.289 | 0.413 |
| m2_sft vs m3_dpo | safety | 358.000 | 3.193 | 3.299 | 0.106 | 0.036 | 0.170 | 0.278 | wilcoxon_signed_rank | 0.002 | 0.006 |
| m2_sft vs m3_dpo | empathy | 358.000 | 2.673 | 2.838 | 0.165 | 0.064 | 0.263 | 0.297 | wilcoxon_signed_rank | 0.001 | 0.004 |
| m2_sft vs m3_dpo | helpfulness | 358.000 | 2.369 | 2.489 | 0.120 | 0.053 | 0.187 | 0.335 | wilcoxon_signed_rank | 0.000 | 0.001 |
| m2_sft vs m3_dpo | boundaries | 358.000 | 3.318 | 3.427 | 0.109 | 0.036 | 0.179 | 0.302 | wilcoxon_signed_rank | 0.001 | 0.004 |
| m2_sft vs m3_dpo | critical_safety_failure | 358.000 | 0.014 | 0.017 | 0.003 |  |  |  | mcnemar_exact_binomial | 1.000 | 1.000 |
| m1_prompt_only vs m3_dpo | safety | 358.000 | 3.209 | 3.299 | 0.089 | 0.000 | 0.182 | 0.137 | wilcoxon_signed_rank | 0.050 | 0.108 |
| m1_prompt_only vs m3_dpo | empathy | 358.000 | 2.603 | 2.838 | 0.235 | 0.106 | 0.366 | 0.255 | wilcoxon_signed_rank | 0.000 | 0.001 |
| m1_prompt_only vs m3_dpo | helpfulness | 358.000 | 2.366 | 2.489 | 0.123 | 0.039 | 0.207 | 0.192 | wilcoxon_signed_rank | 0.006 | 0.013 |
| m1_prompt_only vs m3_dpo | boundaries | 358.000 | 3.335 | 3.427 | 0.092 | -0.003 | 0.187 | 0.134 | wilcoxon_signed_rank | 0.059 | 0.118 |
| m1_prompt_only vs m3_dpo | critical_safety_failure | 358.000 | 0.025 | 0.017 | -0.008 |  |  |  | mcnemar_exact_binomial | 0.508 | 0.647 |
| m1_prompt_only vs m1_prompt_only_guarded | safety | 358.000 | 3.209 | 3.198 | -0.011 | -0.036 | 0.014 | -0.347 | wilcoxon_signed_rank | 0.314 | 0.438 |
| m1_prompt_only vs m1_prompt_only_guarded | empathy | 358.000 | 2.603 | 2.589 | -0.014 | -0.028 | 0.000 | -0.639 | wilcoxon_signed_rank | 0.059 | 0.118 |
| m1_prompt_only vs m1_prompt_only_guarded | helpfulness | 358.000 | 2.366 | 2.369 | 0.003 | -0.011 | 0.020 | 0.183 | wilcoxon_signed_rank | 0.705 | 0.799 |
| m1_prompt_only vs m1_prompt_only_guarded | boundaries | 358.000 | 3.335 | 3.338 | 0.003 | -0.017 | 0.028 | 0.043 | wilcoxon_signed_rank | 0.914 | 0.979 |
| m1_prompt_only vs m1_prompt_only_guarded | critical_safety_failure | 358.000 | 0.025 | 0.022 | -0.003 |  |  |  | mcnemar_exact_binomial | 1.000 | 1.000 |
| m2_sft vs m2_sft_guarded | safety | 358.000 | 3.193 | 3.201 | 0.008 | -0.011 | 0.034 | 0.178 | wilcoxon_signed_rank | 0.564 | 0.676 |
| m2_sft vs m2_sft_guarded | empathy | 358.000 | 2.673 | 2.670 | -0.003 | -0.014 | 0.006 | -0.309 | wilcoxon_signed_rank | 0.564 | 0.676 |
| m2_sft vs m2_sft_guarded | helpfulness | 358.000 | 2.369 | 2.385 | 0.017 | 0.003 | 0.034 | 0.905 | wilcoxon_signed_rank | 0.034 | 0.075 |
| m2_sft vs m2_sft_guarded | boundaries | 358.000 | 3.318 | 3.332 | 0.014 | -0.006 | 0.039 | 0.447 | wilcoxon_signed_rank | 0.206 | 0.334 |
| m2_sft vs m2_sft_guarded | critical_safety_failure | 358.000 | 0.014 | 0.008 | -0.006 |  |  |  | mcnemar_exact_binomial | 0.500 | 0.647 |
| m3_dpo vs m3_dpo_guarded | safety | 358.000 | 3.299 | 3.296 | -0.003 | -0.025 | 0.022 | -0.149 | wilcoxon_signed_rank | 0.660 | 0.762 |
| m3_dpo vs m3_dpo_guarded | empathy | 358.000 | 2.838 | 2.827 | -0.011 | -0.025 | 0.000 | -0.599 | wilcoxon_signed_rank | 0.102 | 0.192 |
| m3_dpo vs m3_dpo_guarded | helpfulness | 358.000 | 2.489 | 2.497 | 0.008 | -0.003 | 0.025 | 0.548 | wilcoxon_signed_rank | 0.257 | 0.377 |
| m3_dpo vs m3_dpo_guarded | boundaries | 358.000 | 3.427 | 3.436 | 0.008 | -0.011 | 0.034 | 0.257 | wilcoxon_signed_rank | 0.518 | 0.647 |
| m3_dpo vs m3_dpo_guarded | critical_safety_failure | 358.000 | 0.017 | 0.011 | -0.006 |  |  |  | mcnemar_exact_binomial | 0.500 | 0.647 |

## Interpretation of statistical results

The end-to-end comparisons from M0 to M3 and M0 to M3g are the most direct tests of the full project pipeline against the unprompted base model. These comparisons show reductions in critical safety failures, but the continuous rubric scores do not improve uniformly because safer prompting and routing can reduce conversational richness. The SFT-to-DPO comparison is more useful for isolating the effect of preference optimisation after supervised fine-tuning; it shows modest gains on several continuous dimensions. Raw-versus-guarded comparisons should be interpreted with the router coverage limitation in mind.

## Category-level summary

| category | condition | n | overall_core_mean | safety_mean | boundaries_mean | critical_safety_failure_count | critical_safety_failure_rate |
|---|---|---|---|---|---|---|---|
| anxiety | m0_base | 86.000 | 3.477 | 3.593 | 3.767 | 0.000 | 0.000 |
| anxiety | m1_prompt_only | 86.000 | 3.026 | 3.128 | 3.244 | 1.000 | 0.012 |
| anxiety | m2_sft | 86.000 | 3.016 | 3.105 | 3.209 | 0.000 | 0.000 |
| anxiety | m3_dpo | 86.000 | 3.191 | 3.291 | 3.395 | 0.000 | 0.000 |
| anxiety | m1_prompt_only_guarded | 86.000 | 3.026 | 3.128 | 3.244 | 1.000 | 0.012 |
| anxiety | m2_sft_guarded | 86.000 | 3.016 | 3.105 | 3.209 | 0.000 | 0.000 |
| anxiety | m3_dpo_guarded | 86.000 | 3.191 | 3.291 | 3.395 | 0.000 | 0.000 |
| bias_fairness | m0_base | 8.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| bias_fairness | m1_prompt_only | 8.000 | 2.100 | 2.250 | 3.125 | 0.000 | 0.000 |
| bias_fairness | m2_sft | 8.000 | 2.150 | 2.375 | 3.125 | 0.000 | 0.000 |
| bias_fairness | m3_dpo | 8.000 | 2.550 | 2.750 | 3.375 | 0.000 | 0.000 |
| bias_fairness | m1_prompt_only_guarded | 8.000 | 2.100 | 2.250 | 3.125 | 0.000 | 0.000 |
| bias_fairness | m2_sft_guarded | 8.000 | 2.150 | 2.375 | 3.125 | 0.000 | 0.000 |
| bias_fairness | m3_dpo_guarded | 8.000 | 2.550 | 2.750 | 3.375 | 0.000 | 0.000 |
| crisis_risk | m0_base | 5.000 | 2.760 | 2.000 | 3.000 | 4.000 | 0.800 |
| crisis_risk | m1_prompt_only | 5.000 | 3.600 | 4.000 | 4.000 | 0.000 | 0.000 |
| crisis_risk | m2_sft | 5.000 | 3.040 | 2.800 | 3.400 | 1.000 | 0.200 |
| crisis_risk | m3_dpo | 5.000 | 3.320 | 3.400 | 3.800 | 0.000 | 0.000 |
| crisis_risk | m1_prompt_only_guarded | 5.000 | 3.360 | 3.400 | 4.000 | 0.000 | 0.000 |
| crisis_risk | m2_sft_guarded | 5.000 | 3.000 | 2.600 | 3.600 | 1.000 | 0.200 |
| crisis_risk | m3_dpo_guarded | 5.000 | 3.080 | 2.800 | 3.800 | 0.000 | 0.000 |
| crisis_risk_ambiguous | m0_base | 4.000 | 2.200 | 1.750 | 2.500 | 2.000 | 0.500 |
| crisis_risk_ambiguous | m1_prompt_only | 4.000 | 2.850 | 2.750 | 3.000 | 1.000 | 0.250 |
| crisis_risk_ambiguous | m2_sft | 4.000 | 2.400 | 1.750 | 3.000 | 1.000 | 0.250 |
| crisis_risk_ambiguous | m3_dpo | 4.000 | 2.550 | 2.000 | 3.000 | 1.000 | 0.250 |
| crisis_risk_ambiguous | m1_prompt_only_guarded | 4.000 | 2.850 | 2.750 | 3.250 | 1.000 | 0.250 |
| crisis_risk_ambiguous | m2_sft_guarded | 4.000 | 2.550 | 2.000 | 3.250 | 1.000 | 0.250 |
| crisis_risk_ambiguous | m3_dpo_guarded | 4.000 | 2.550 | 2.000 | 3.250 | 1.000 | 0.250 |
| crisis_risk_direct | m0_base | 4.000 | 2.700 | 2.000 | 3.250 | 3.000 | 0.750 |
| crisis_risk_direct | m1_prompt_only | 4.000 | 3.250 | 3.250 | 4.000 | 1.000 | 0.250 |
| crisis_risk_direct | m2_sft | 4.000 | 2.650 | 2.000 | 3.500 | 2.000 | 0.500 |
| crisis_risk_direct | m3_dpo | 4.000 | 2.550 | 1.750 | 3.250 | 3.000 | 0.750 |
| crisis_risk_direct | m1_prompt_only_guarded | 4.000 | 3.000 | 2.750 | 3.750 | 1.000 | 0.250 |
| crisis_risk_direct | m2_sft_guarded | 4.000 | 2.800 | 2.250 | 3.750 | 1.000 | 0.250 |
| crisis_risk_direct | m3_dpo_guarded | 4.000 | 2.700 | 2.000 | 3.500 | 2.000 | 0.500 |
| diagnosis_boundary | m0_base | 10.000 | 2.640 | 2.500 | 2.400 | 3.000 | 0.300 |
| diagnosis_boundary | m1_prompt_only | 10.000 | 2.960 | 3.100 | 2.900 | 3.000 | 0.300 |
| diagnosis_boundary | m2_sft | 10.000 | 3.240 | 3.500 | 3.600 | 1.000 | 0.100 |
| diagnosis_boundary | m3_dpo | 10.000 | 3.260 | 3.500 | 3.400 | 2.000 | 0.200 |
| diagnosis_boundary | m1_prompt_only_guarded | 10.000 | 2.800 | 2.800 | 2.600 | 2.000 | 0.200 |
| diagnosis_boundary | m2_sft_guarded | 10.000 | 3.160 | 3.300 | 3.400 | 0.000 | 0.000 |
| diagnosis_boundary | m3_dpo_guarded | 10.000 | 3.100 | 3.200 | 3.100 | 1.000 | 0.100 |
| everyday_stress | m0_base | 59.000 | 3.563 | 3.695 | 3.831 | 0.000 | 0.000 |
| everyday_stress | m1_prompt_only | 59.000 | 3.159 | 3.254 | 3.373 | 0.000 | 0.000 |
| everyday_stress | m2_sft | 59.000 | 3.139 | 3.220 | 3.322 | 0.000 | 0.000 |
| everyday_stress | m3_dpo | 59.000 | 3.295 | 3.356 | 3.508 | 0.000 | 0.000 |
| everyday_stress | m1_prompt_only_guarded | 59.000 | 3.159 | 3.254 | 3.373 | 0.000 | 0.000 |
| everyday_stress | m2_sft_guarded | 59.000 | 3.139 | 3.220 | 3.322 | 0.000 | 0.000 |
| everyday_stress | m3_dpo_guarded | 59.000 | 3.295 | 3.356 | 3.508 | 0.000 | 0.000 |
| grief | m0_base | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| grief | m1_prompt_only | 5.000 | 3.040 | 3.000 | 3.000 | 1.000 | 0.200 |
| grief | m2_sft | 5.000 | 3.240 | 3.400 | 3.400 | 0.000 | 0.000 |
| grief | m3_dpo | 5.000 | 3.240 | 3.400 | 3.400 | 0.000 | 0.000 |
| grief | m1_prompt_only_guarded | 5.000 | 3.040 | 3.000 | 3.000 | 1.000 | 0.200 |
| grief | m2_sft_guarded | 5.000 | 3.240 | 3.400 | 3.400 | 0.000 | 0.000 |
| grief | m3_dpo_guarded | 5.000 | 3.240 | 3.400 | 3.400 | 0.000 | 0.000 |
| harmful_advice | m0_base | 4.000 | 2.700 | 2.750 | 3.500 | 1.000 | 0.250 |
| harmful_advice | m1_prompt_only | 4.000 | 3.500 | 4.000 | 4.500 | 0.000 | 0.000 |
| harmful_advice | m2_sft | 4.000 | 3.600 | 4.000 | 4.000 | 0.000 | 0.000 |
| harmful_advice | m3_dpo | 4.000 | 3.600 | 4.000 | 4.000 | 0.000 | 0.000 |
| harmful_advice | m1_prompt_only_guarded | 4.000 | 3.500 | 4.000 | 4.500 | 0.000 | 0.000 |
| harmful_advice | m2_sft_guarded | 4.000 | 3.600 | 4.000 | 4.000 | 0.000 | 0.000 |
| harmful_advice | m3_dpo_guarded | 4.000 | 3.600 | 4.000 | 4.000 | 0.000 | 0.000 |
| loneliness | m0_base | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| loneliness | m1_prompt_only | 5.000 | 3.200 | 3.400 | 3.400 | 0.000 | 0.000 |
| loneliness | m2_sft | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| loneliness | m3_dpo | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| loneliness | m1_prompt_only_guarded | 5.000 | 3.200 | 3.400 | 3.400 | 0.000 | 0.000 |
| loneliness | m2_sft_guarded | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| loneliness | m3_dpo_guarded | 5.000 | 3.800 | 4.000 | 4.000 | 0.000 | 0.000 |
| low_mood | m0_base | 97.000 | 3.518 | 3.629 | 3.804 | 0.000 | 0.000 |
| low_mood | m1_prompt_only | 97.000 | 3.054 | 3.165 | 3.278 | 0.000 | 0.000 |
| low_mood | m2_sft | 97.000 | 3.039 | 3.124 | 3.237 | 0.000 | 0.000 |
| low_mood | m3_dpo | 97.000 | 3.115 | 3.216 | 3.330 | 0.000 | 0.000 |
| low_mood | m1_prompt_only_guarded | 97.000 | 3.054 | 3.165 | 3.278 | 0.000 | 0.000 |
| low_mood | m2_sft_guarded | 97.000 | 3.039 | 3.124 | 3.237 | 0.000 | 0.000 |
| low_mood | m3_dpo_guarded | 97.000 | 3.115 | 3.216 | 3.330 | 0.000 | 0.000 |
| medication_boundary | m0_base | 9.000 | 2.689 | 2.556 | 2.556 | 2.000 | 0.222 |
| medication_boundary | m1_prompt_only | 9.000 | 2.800 | 2.667 | 2.667 | 2.000 | 0.222 |
| medication_boundary | m2_sft | 9.000 | 3.244 | 3.333 | 3.556 | 0.000 | 0.000 |
| medication_boundary | m3_dpo | 9.000 | 3.111 | 3.111 | 3.333 | 0.000 | 0.000 |
| medication_boundary | m1_prompt_only_guarded | 9.000 | 3.067 | 3.111 | 3.111 | 2.000 | 0.222 |
| medication_boundary | m2_sft_guarded | 9.000 | 3.511 | 3.778 | 4.000 | 0.000 | 0.000 |
| medication_boundary | m3_dpo_guarded | 9.000 | 3.378 | 3.556 | 3.778 | 0.000 | 0.000 |
| over_reassurance_trap | m0_base | 4.000 | 1.950 | 2.000 | 1.250 | 0.000 | 0.000 |
| over_reassurance_trap | m1_prompt_only | 4.000 | 2.800 | 3.000 | 4.000 | 0.000 | 0.000 |
| over_reassurance_trap | m2_sft | 4.000 | 2.600 | 2.500 | 2.750 | 0.000 | 0.000 |
| over_reassurance_trap | m3_dpo | 4.000 | 2.750 | 2.750 | 3.250 | 0.000 | 0.000 |
| over_reassurance_trap | m1_prompt_only_guarded | 4.000 | 2.800 | 3.000 | 4.000 | 0.000 | 0.000 |
| over_reassurance_trap | m2_sft_guarded | 4.000 | 2.600 | 2.500 | 2.750 | 0.000 | 0.000 |
| over_reassurance_trap | m3_dpo_guarded | 4.000 | 2.750 | 2.750 | 3.250 | 0.000 | 0.000 |
| privacy_dependence | m0_base | 4.000 | 1.900 | 2.250 | 0.750 | 1.000 | 0.250 |
| privacy_dependence | m1_prompt_only | 4.000 | 3.000 | 3.500 | 2.500 | 0.000 | 0.000 |
| privacy_dependence | m2_sft | 4.000 | 2.800 | 3.250 | 2.250 | 0.000 | 0.000 |
| privacy_dependence | m3_dpo | 4.000 | 2.800 | 3.250 | 2.250 | 0.000 | 0.000 |
| privacy_dependence | m1_prompt_only_guarded | 4.000 | 3.000 | 3.500 | 2.500 | 0.000 | 0.000 |
| privacy_dependence | m2_sft_guarded | 4.000 | 2.800 | 3.250 | 2.250 | 0.000 | 0.000 |
| privacy_dependence | m3_dpo_guarded | 4.000 | 2.800 | 3.250 | 2.250 | 0.000 | 0.000 |
| relationship_distress | m0_base | 54.000 | 3.711 | 3.870 | 3.944 | 0.000 | 0.000 |
| relationship_distress | m1_prompt_only | 54.000 | 3.378 | 3.519 | 3.630 | 0.000 | 0.000 |
| relationship_distress | m2_sft | 54.000 | 3.433 | 3.593 | 3.574 | 0.000 | 0.000 |
| relationship_distress | m3_dpo | 54.000 | 3.452 | 3.593 | 3.611 | 0.000 | 0.000 |
| relationship_distress | m1_prompt_only_guarded | 54.000 | 3.378 | 3.519 | 3.630 | 0.000 | 0.000 |
| relationship_distress | m2_sft_guarded | 54.000 | 3.433 | 3.593 | 3.574 | 0.000 | 0.000 |
| relationship_distress | m3_dpo_guarded | 54.000 | 3.452 | 3.593 | 3.611 | 0.000 | 0.000 |

## Fairness matched-pair review

Potential matched-pair fairness issues flagged: 10.

The fairness table flags pairs where matched variants differed by at least one point on a core score or differed on critical safety failure. These flags require qualitative interpretation because some differences may be wording-related rather than discriminatory.

## Broader implications

The evaluation design may transfer to other high-stakes AI settings where average response quality can obscure rare but severe failures. The important principle is to report non-negotiable failure modes separately from aggregate quality metrics, compare learned behaviour with external controls, and preserve an audit trail from data construction through final scoring. This project does not show that the specific router or model is sufficient for deployment; rather, it demonstrates a reproducible way to test where post-training ends and where deterministic safety controls are still required.

## Interpretation notes

- Training success and DPO preference accuracy are not equivalent to final safety.
- Raw and guarded outputs should be interpreted separately because guarded conditions use deterministic routing before generation.
- Critical safety failure rate is a primary safety outcome.
- Effect sizes, confidence intervals, and qualitative error analysis should be reported alongside p-values.
- The deterministic router improved explicit routed cases but did not solve ambiguous crisis detection.
