"""
Deterministic safety router for LLM therapy post-training project.

This router is used during inference/evaluation, not training.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteResult:
    routed: bool
    route_type: Optional[str]
    response: Optional[str]


def normalise_text(text: str) -> str:
    """Lowercase and normalise whitespace for rule matching."""
    text = text.lower()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_any(text: str, patterns: list[str]) -> bool:
    """Return True if any regex pattern matches the text."""
    return any(re.search(pattern, text) for pattern in patterns)


def detect_crisis_risk(prompt: str) -> bool:
    """
    Detect current or possible self-harm / suicide / immediate safety risk.

    This intentionally focuses on first-person or immediate-risk phrasing.
    It avoids treating every mention of death or grief as a crisis.
    """

    text = normalise_text(prompt)

    crisis_patterns = [
        r"\bi\s+(want|wanted|feel like|keep thinking about)\s+(to\s+)?(die|kill myself|end my life)\b",
        r"\bi\s+(might|may|could|will|am going to|plan to)\s+(hurt|harm|kill)\s+myself\b",
        r"\bthoughts?\s+about\s+(hurting|harming|killing)\s+myself\b",
        r"\bself[- ]?harm\b",
        r"\bsuicidal\b",
        r"\bsuicide\b.*\b(myself|me|i)\b",
        r"\bi\s+(do not|don't)\s+trust\s+myself\s+alone\b",
        r"\bi\s+(do not|don't)\s+feel\s+safe\b",
        r"\bi\s+feel\s+unsafe\b",
        r"\bi\s+(cannot|can't)\s+stay\s+safe\b",
        r"\bno\s+reason\s+to\s+live\b",
        r"\bcan't\s+keep\s+going\b",
        r"\bcannot\s+keep\s+going\b",
        r"\bsaying\s+goodbye\s+to\s+people\s+without\s+them\s+knowing\b",
        r"\bsaid\s+goodbye\s+to\s+everyone\b",
    ]

    return contains_any(text, crisis_patterns)


def detect_medication_boundary(prompt: str) -> bool:
    """
    Detect requests about medication decisions, stopping/restarting medication,
    changing dose, side effects, or whether a medication decision was right.
    """

    text = normalise_text(prompt)

    medication_terms = [
        r"\bmedication\b",
        r"\bmedications\b",
        r"\bmeds\b",
        r"\bprescription\b",
        r"\bantidepressant\b",
        r"\banti[- ]?depressant\b",
        r"\bssri\b",
        r"\bsertraline\b",
        r"\bfluoxetine\b",
        r"\bcitalopram\b",
        r"\bescitalopram\b",
        r"\bprozac\b",
        r"\bzoloft\b",
        r"\bdose\b",
        r"\bdosage\b",
        r"\bside effects?\b",
    ]

    decision_terms = [
        r"\bstop\b",
        r"\bstopped\b",
        r"\bstopping\b",
        r"\brestart\b",
        r"\brestarted\b",
        r"\bstart taking\b",
        r"\bchange\b",
        r"\bchanged\b",
        r"\bincrease\b",
        r"\bdecrease\b",
        r"\blower\b",
        r"\braise\b",
        r"\bskip\b",
        r"\bmissed\b",
        r"\bwas that the right call\b",
        r"\bright decision\b",
        r"\bshould i\b",
        r"\bcan i\b",
    ]

    return contains_any(text, medication_terms) and contains_any(text, decision_terms)


def detect_diagnosis_boundary(prompt: str) -> bool:
    """
    Detect requests asking the assistant to diagnose, identify a disorder,
    or judge whether symptoms indicate a condition.
    """

    text = normalise_text(prompt)

    diagnosis_patterns = [
        r"\bdo i have\b.*\b(disorder|condition|depression|anxiety|bipolar|adhd|ptsd|ocd)\b",
        r"\bam i\b.*\b(depressed|bipolar|mentally ill|traumatised|traumatized)\b",
        r"\bdoes this sound like\b.*\b(disorder|condition|depression|anxiety|bipolar|adhd|ptsd|ocd)\b",
        r"\bdo my\b.*\bsound like\b.*\b(disorder|condition)\b",
        r"\bwhat disorder\b",
        r"\bwhat condition\b",
        r"\bdiagnose\b",
        r"\bdiagnosis\b",
        r"\bis this\b.*\b(depression|anxiety|bipolar|adhd|ptsd|ocd)\b",
    ]

    return contains_any(text, diagnosis_patterns)


def detect_harmful_advice(prompt: str) -> bool:
    """
    Detect requests for harmful advice. This is a conservative lightweight rule.
    It is not the main focus of the first router smoke test, but helps strengthen
    the safety layer for final evaluation.
    """

    text = normalise_text(prompt)

    harmful_patterns = [
        r"\bhow\s+do\s+i\s+(hurt|harm|kill)\b",
        r"\bhow\s+can\s+i\s+(hurt|harm|kill)\b",
        r"\bways?\s+to\s+(hurt|harm|kill)\b",
        r"\bmake\s+someone\s+suffer\b",
        r"\bget\s+revenge\b",
        r"\bhide\s+self[- ]?harm\b",
    ]

    return contains_any(text, harmful_patterns)


def crisis_response() -> str:
    return (
        "I’m really sorry you’re feeling this way. Because you may not be safe "
        "right now, this needs immediate real-world support. Please contact "
        "emergency services, a crisis line, or someone you trust now. Try not "
        "to stay alone, and move away from anything you could use to hurt "
        "yourself while you reach support. I’m not an emergency service, but "
        "your safety matters and you deserve immediate help."
    )


def medication_response() -> str:
    return (
        "I can’t tell you whether stopping or changing medication was the right "
        "decision. Medication decisions can depend on the specific medication, "
        "dose, your history, and your current symptoms. Please contact your "
        "prescriber, GP, doctor, or pharmacist promptly for personalised advice. "
        "Do not stop, restart, or change a dose based only on advice from this "
        "tool. If you feel severely unwell, unsafe, or at risk of harming "
        "yourself, seek urgent help now."
    )


def diagnosis_response() -> str:
    return (
        "I can’t determine whether you have a disorder or give a diagnosis. "
        "What I can do is help you think through what you’re experiencing in a "
        "bounded way. It may help to notice how often this happens, how intense "
        "it feels, whether it affects sleep, relationships, work, study, or "
        "safety, and whether it is getting worse. If it feels intense, "
        "persistent, worsening, unsafe, or disruptive to daily life, it would "
        "be best to speak with a GP, doctor, or mental health professional."
    )


def harmful_advice_response() -> str:
    return (
        "I can’t help with instructions for harming yourself or someone else. "
        "If this is connected to feeling overwhelmed, angry, unsafe, or out of "
        "control, it would be important to step away from anything that could "
        "cause harm and contact a trusted person or emergency support now. I’m "
        "not an emergency service, but immediate real-world support is the "
        "safest next step when there is risk of harm."
    )


def route_prompt(prompt: str) -> RouteResult:
    """
    Route safety-critical prompts to deterministic responses.

    Order matters:
    1. Crisis risk is highest priority.
    2. Harmful advice is next.
    3. Medication boundary.
    4. Diagnosis boundary.
    5. Otherwise, allow model generation.
    """

    if detect_crisis_risk(prompt):
        return RouteResult(
            routed=True,
            route_type="crisis_risk",
            response=crisis_response(),
        )

    if detect_harmful_advice(prompt):
        return RouteResult(
            routed=True,
            route_type="harmful_advice",
            response=harmful_advice_response(),
        )

    if detect_medication_boundary(prompt):
        return RouteResult(
            routed=True,
            route_type="medication_boundary",
            response=medication_response(),
        )

    if detect_diagnosis_boundary(prompt):
        return RouteResult(
            routed=True,
            route_type="diagnosis_boundary",
            response=diagnosis_response(),
        )

    return RouteResult(
        routed=False,
        route_type=None,
        response=None,
    )