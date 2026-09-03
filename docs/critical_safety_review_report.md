# Critical Safety Review Report

## Purpose

This report records the finalisation of the binary `critical_safety_failure` field after manual scoring. Rubric dimensions use a 0-5 scale, while critical safety failure is binary 0/1 for every generated response.

## Files

- Main scoring file: `results/scores/evaluation_scores_completed_blinded.csv`
- Backup before finalisation: `results/scores/evaluation_scores_completed_blinded_before_critical_finalize.csv`
- Backup before final consistency fixes: `results/scores/evaluation_scores_completed_blinded_BACKUP_before_assistant_consistency_fixes.csv`
- Review queue: `results/scores/critical_safety_review_queue_completed.csv`
- Score consistency audit: `docs/score_consistency_audit_report.md`

## Summary

- Reviewed rows merged from critical-safety review queue: 343
- Blank critical labels before final fill: 2044
- Remaining blank labels were filled as 0 after targeted high-risk review.
- Additional manual consistency fixes were applied to rows where `critical_safety_failure`, rubric scores, and notes contradicted each other.
- Final critical safety failures: 51
- Final rows: 2506

## Interpretation

The final `critical_safety_failure` field is complete for every scored response. Only `crisis_escalation` is allowed to remain blank when the prompt does not require crisis escalation scoring.
