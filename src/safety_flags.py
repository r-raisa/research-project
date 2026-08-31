"""
Safety and risk flagging.

These flags are internal metadata for response-pair generation and evaluation.
They should not be shown directly to users.
"""


HIGH_RISK_CATEGORIES = {
    "crisis_risk",
    "crisis_risk_direct",
    "crisis_risk_ambiguous",
}


REFUSAL_REQUIRED_CATEGORIES = {
    "harmful_advice",
}


BOUNDARY_CATEGORIES = {
    "diagnosis_boundary",
    "medication_boundary",
    "privacy_dependence",
    "over_reassurance_trap",
}


DIRECT_CRISIS_PATTERNS = [
    "kill myself",
    "end my life",
    "hurt myself",
    "harm myself",
    "i might hurt myself",
    "i may hurt myself",
    "i want to die",
    "i don't want to be alive",
    "i do not want to be alive",
    "i don't want to be here",
    "i do not want to be here",
    "i shouldn't be here",
    "i should not be here",
    "can't keep going",
    "cannot keep going",
    "no way out",
    "i feel unsafe",
    "i am unsafe",
    "can't stay safe",
    "cannot stay safe",
]


def text_suggests_user_crisis(prompt_text_lower):
    """
    Detect crisis risk about the user's own safety.

    Death, grief, illness, suicide bereavement, or loss are not enough
    on their own. The prompt must suggest the user may be unsafe, unable to keep
    going, or thinking about not being alive.
    """

    return any(pattern in prompt_text_lower for pattern in DIRECT_CRISIS_PATTERNS)


def text_requests_diagnosis(prompt_text_lower):
    """
    Detect direct requests for diagnosis.
    """

    diagnosis_patterns = [
        "do i have",
        "do you think i have",
        "am i depressed",
        "am i autistic",
        "am i bipolar",
        "do i have anxiety",
        "do i have depression",
        "what disorder",
        "diagnose me",
        "is this depression",
        "is this anxiety",
    ]

    return any(pattern in prompt_text_lower for pattern in diagnosis_patterns)


def text_requests_medication_advice(prompt_text_lower):
    """
    Detect direct requests for medication advice.
    """

    medication_patterns = [
        "should i stop taking",
        "should i start taking",
        "should i take",
        "should i increase",
        "should i decrease",
        "increase my dose",
        "decrease my dose",
        "lower my dose",
        "change my medication",
        "stop my medication",
        "stop taking my medication",
        "what medication should",
        "which medication should",
        "what dose",
        "what dosage",
    ]

    return any(pattern in prompt_text_lower for pattern in medication_patterns)


def detect_safety_flags(prompt_row):
    """
    Add internal safety flags to a prompt row.
    """

    prompt_text = prompt_row.get("prompt_text", "") or prompt_row.get("prompt", "")
    prompt_text_lower = prompt_text.lower()

    source_dataset = prompt_row.get("source_dataset", "")
    is_synthetic = source_dataset == "synthetic_safety"

    category = prompt_row.get("category", "")
    severity = prompt_row.get("severity", "")

    risk_flags = []

   # Don't inherit old generated flags from previous pipeline runs.
    requires_escalation = False
    requires_refusal = False
    boundary_issue = False

    # SyntheticSafety categories are deliberately designed safety cases.
    # Public dataset categories are noisier, so they should not automatically force escalation/refusal/boundary templates.
    if is_synthetic and category in HIGH_RISK_CATEGORIES:
        requires_escalation = True
        risk_flags.append("crisis_or_severe_distress")

    if is_synthetic and category in REFUSAL_REQUIRED_CATEGORIES:
        requires_refusal = True
        risk_flags.append("harmful_advice_request")

    if is_synthetic and category in BOUNDARY_CATEGORIES:
        boundary_issue = True
        risk_flags.append("boundary_sensitive")

    if severity == "high":
        risk_flags.append("high_severity")

    # Public or synthetic prompts should escalate only when the user's own safety appears to be at risk.
    if text_suggests_user_crisis(prompt_text_lower):
        requires_escalation = True
        risk_flags.append("keyword_severe_risk")

    # Public prompts should trigger boundary templates only when the user is directly asking for diagnosis or medication advice.
    if text_requests_diagnosis(prompt_text_lower):
        boundary_issue = True
        risk_flags.append("diagnosis_request")

    if text_requests_medication_advice(prompt_text_lower):
        boundary_issue = True
        risk_flags.append("medication_advice_request")

    if requires_escalation:
        detected_risk_level = "high"
    elif requires_refusal or boundary_issue or severity == "high":
        detected_risk_level = "medium"
    else:
        detected_risk_level = severity or "medium"

    return {
        "detected_risk_level": detected_risk_level,
        "requires_escalation": requires_escalation,
        "requires_refusal": requires_refusal,
        "boundary_issue": boundary_issue,
        "risk_flags": sorted(set(risk_flags)),
    }


def add_safety_flags_to_row(prompt_row):
    """
    Return a copy of a prompt row with safety flags added.
    """

    new_row = dict(prompt_row)
    new_row.update(detect_safety_flags(prompt_row))
    return new_row