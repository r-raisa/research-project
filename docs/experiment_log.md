## Response-pair pilot v1

- Result: Chosen responses passed basic safety checks but were sometimes too generic or not relevant enough to the specific user prompt.
- Decision: Do not scale this version to the main training dataset.
- Fix: Add prompt-specific relevance checks and improve chosen-response generation.

## Response-pair pilot v2 plan
- Change: SyntheticSafety chosen responses will use controlled templates.
- Change: Public dataset chosen responses will be generated with the local model and the safety system prompt.
- Change: Rejected responses will remain controlled flawed templates.
- Reason: Pilot v1 responses were generally safe, but some chosen responses were too generic or not specific enough to the user prompt.
