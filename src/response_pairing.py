import json
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone

from src.safety_flags import add_safety_flags_to_row
from src.utils import load_yaml, read_jsonl, write_jsonl, resolve_project_path


def get_response_pairing_config(project_root):
    config = load_yaml(project_root / "configs" / "data_config.yaml")
    return config.get("response_pairing", {})


def get_generation_config(project_root):
    config = load_yaml(project_root / "configs" / "generation_config.yaml")
    return config["generation"]


def resolve_pairing_path(project_root, path_value):
    return resolve_project_path(project_root, path_value)


def sample_public_rows_by_category(public_rows, target_n, seed):
    rng = random.Random(seed)
    by_category = defaultdict(list)

    for row in public_rows:
        by_category[row.get("category", "unknown")].append(row)

    selected = []

    categories = sorted(by_category.keys())
    per_category = max(1, target_n // max(1, len(categories)))

    for category in categories:
        rows = list(by_category[category])
        rng.shuffle(rows)
        selected.extend(rows[:per_category])

    if len(selected) < target_n:
        already_selected = {row["prompt_id"] for row in selected}
        remaining = [
            row for row in public_rows
            if row["prompt_id"] not in already_selected
        ]
        rng.shuffle(remaining)
        selected.extend(remaining[: target_n - len(selected)])

    rng.shuffle(selected)
    return selected[:target_n]


def create_pairing_prompt_subsets(project_root, pilot=False):
    """
    Create train/validation prompt subsets for response-pair generation.

    Uses only train and validation prompts. Never samples from the locked test set.
    """

    config = get_response_pairing_config(project_root)
    seed = config.get("seed", 42)

    input_paths = config["input_paths"]
    output_paths = config["pairing_prompt_outputs"]
    subset_sizes = config["subset_sizes"]

    train_rows = read_jsonl(resolve_pairing_path(project_root, input_paths["train_prompts"]))
    validation_rows = read_jsonl(resolve_pairing_path(project_root, input_paths["validation_prompts"]))
    test_rows = read_jsonl(resolve_pairing_path(project_root, input_paths["locked_test_prompts"]))

    test_prompt_ids = {row["prompt_id"] for row in test_rows}

    train_total = (
        subset_sizes["pilot_train_total"]
        if pilot
        else subset_sizes["main_train_total"]
    )
    validation_total = (
        subset_sizes["pilot_validation_total"]
        if pilot
        else subset_sizes["main_validation_total"]
    )

    def select_subset(rows, target_total):
        synthetic_rows = [
            row for row in rows
            if row.get("source_dataset") == "synthetic_safety"
        ]
        public_rows = [
            row for row in rows
            if row.get("source_dataset") != "synthetic_safety"
        ]

        if pilot:
            # For pilot, include a small stratified sample from both synthetic and public.
            all_rows = list(rows)
            random.Random(seed).shuffle(all_rows)
            selected = sample_public_rows_by_category(all_rows, target_total, seed)
        else:
            # For main, include all available SyntheticSafety rows first.
            remaining_n = max(0, target_total - len(synthetic_rows))
            selected = synthetic_rows + sample_public_rows_by_category(
                public_rows,
                remaining_n,
                seed,
            )

        for row in selected:
            if row["prompt_id"] in test_prompt_ids:
                raise ValueError(f"Test prompt leaked into pairing subset: {row['prompt_id']}")

        return [add_safety_flags_to_row(row) for row in selected]

    train_subset = select_subset(train_rows, train_total)
    validation_subset = select_subset(validation_rows, validation_total)

    write_jsonl(
        train_subset,
        resolve_pairing_path(project_root, output_paths["train"]),
    )
    write_jsonl(
        validation_subset,
        resolve_pairing_path(project_root, output_paths["validation"]),
    )

    print("Created response-pairing prompt subsets")
    print("=" * 40)
    print(f"Train subset: {len(train_subset)}")
    print(f"Validation subset: {len(validation_subset)}")


TEMPLATE_CHOSEN_VERSION = "controlled_safety_template_v2"
REJECTED_TEMPLATE_VERSION = "rejected_template_v1"


def choose_rejected_prompt_type(row):
    """
    Choose the rejected-response failure mode.

    Rejected responses stay template-based so that the failure mode is controlled.
    """

    category = row.get("category", "")

    if row.get("requires_escalation"):
        return "poor_safety"

    if row.get("requires_refusal"):
        return "boundary_weak"

    if category == "diagnosis_boundary":
        return "boundary_weak"

    if category == "medication_boundary":
        return "boundary_weak"

    if category == "privacy_dependence":
        return "dependence_encouraging"

    if category == "over_reassurance_trap":
        return "over_reassurance"

    return "low_empathy"


def should_use_controlled_chosen_template(row):
    """
    Use controlled chosen-response templates only for prompts where a fixed
    safety or boundary behaviour is required.
    """

    return (
        row.get("source_dataset") == "synthetic_safety"
        or row.get("requires_escalation") is True
        or row.get("requires_refusal") is True
        or row.get("boundary_issue") is True
        or is_simple_bereavement_prompt(row)
    )

def create_controlled_template_chosen_response(row):
    """
    Controlled chosen responses for safety-sensitive prompts.

    These templates are used for:
    - SyntheticSafety prompts
    - crisis-escalation prompts
    - harmful-advice/refusal prompts
    - diagnosis, medication, dependence and over-reassurance boundary prompts
    """

    category = row.get("category", "")
    prompt_lower = row.get("prompt_text", "").lower()

    if row.get("requires_escalation"):
        if (
            "worthless" in prompt_lower
            or "shouldn't be here" in prompt_lower
            or "should not be here" in prompt_lower
        ):
            opening = (
                "I'm really sorry you're feeling so worthless and having thoughts about not being here. "
            )
        else:
            opening = (
                "I'm really sorry you're feeling this unsafe or overwhelmed right now. "
            )

        return (
            opening
            + "This deserves real support, and you should not have to handle it alone. "
            "If you feel at risk of hurting yourself, or feel unable to stay safe, please contact emergency services, a crisis line, or someone you trust immediately. "
            "I am not an emergency service, but your safety matters and this is a moment to involve real-world support now."
        )

    if is_simple_bereavement_prompt(row):
        return (
            "I'm really sorry about your loss. "
            "That sounds sudden and deeply painful, especially given the distressing way it happened. "
            "It is understandable if you feel shocked, upset, confused, or unsure how to process it. "
            "It may help to speak with someone you trust, or with a grief counsellor or mental health professional if this feels too heavy to carry alone. "
          "If this loss is making you feel unsafe or unable to cope right now, please contact emergency services, a crisis line, or someone who can support you immediately."
        )

    if row.get("requires_refusal"):
        return (
            "I'm sorry you're dealing with this, and I can understand wanting a way to make the situation feel easier. "
            "I cannot help with anything harmful, deceptive, abusive, or unsafe. "
            "A safer next step would be to pause, focus on what support you need, and consider speaking honestly with someone trusted or qualified."
        )

    if category == "diagnosis_boundary":
        return (
            "I'm sorry this has been worrying you. "
            "I cannot diagnose you, but what you are describing sounds important and worth taking seriously. "
            "It may help to write down what you have noticed and discuss it with a qualified mental health professional or GP."
        )

    if category == "medication_boundary":
        return (
            "That sounds stressful to manage. "
            "I cannot advise you to start, stop, increase, decrease, or change medication. "
            "The safest next step is to speak with your prescriber, GP, pharmacist, or another qualified healthcare professional, especially if this feels urgent."
        )

    if category == "privacy_dependence":
        return (
            "It makes sense that you would want support when things feel difficult. "
            "I can be a place to reflect, but it is important not to rely on this tool as your main source of support. "
            "It may help to reach out to someone you trust or use an offline coping strategy alongside this conversation."
        )

    if category == "over_reassurance_trap":
        return (
            "I'm sorry you're sitting with so much uncertainty. "
            "I cannot promise exactly how things will turn out, but I can help you focus on what is manageable right now. "
            "One small next step could be to ground yourself, write down the main worry, and decide what support or information would help most."
        )

    if category == "bias_fairness":
        return (
            "I'm sorry this has been difficult to deal with. "
            "Your feelings deserve to be taken seriously. "
            "A helpful next step may be to pause, name what feels hardest right now, and consider reaching out to someone trusted or qualified if you need more support."
        )

    return (
        "I'm sorry this has been difficult for you. "
        "It makes sense that you would want support. "
        "One small next step could be to pause, name what feels most urgent, and consider whether someone trusted could support you with this."
    )


def create_template_rejected_response(row):
    """
    Controlled rejected responses.

    These are intentionally lower quality but should not contain graphic,
    instructional, or procedurally harmful content.
    """

    rejected_type = choose_rejected_prompt_type(row)

    if rejected_type == "poor_safety":
        return (
            "That sounds difficult, but try not to think about it too much. "
            "Maybe distract yourself with something else for now and see how you feel later."
        )

    if rejected_type == "boundary_weak":
        return (
            "It sounds like this could be a specific mental health issue, and you should probably treat it directly. "
            "You may want to decide on a treatment plan soon so it does not get worse."
        )

    if rejected_type == "over_reassurance":
        return (
            "Everything will definitely be fine, so try not to worry. "
            "This feeling is temporary and things will work out."
        )

    if rejected_type == "unhelpful_refusal":
        return (
            "I cannot help with this topic. "
            "Please speak to someone else."
        )

    if rejected_type == "dependence_encouraging":
        return (
            "You can keep coming back here whenever you feel bad. "
            "It is okay to rely on this chat if talking to other people feels too hard."
        )

    return (
        "You should make a list of things to fix and try to stay busy. "
        "That is probably the most practical thing to do."
    )


def load_local_generation_model(project_root):
    """
    Load the local model used to generate chosen responses for public prompts.

    This is loaded so that validation and template only stages do not
    require loading the model.
    """

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_config = load_yaml(project_root / "configs" / "model_config.yaml")
    model_id = model_config["model"]["primary_model_id"]

    if torch.backends.mps.is_available():
        device = "mps"
        torch_dtype = torch.float16
    else:
        device = "cpu"
        torch_dtype = torch.float32

    print(f"Loading local generation model: {model_id}")
    print(f"Device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_id)

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        low_cpu_mem_usage=True,
    )

    model.to(device)
    model.eval()

    return {
        "model": model,
        "tokenizer": tokenizer,
        "device": device,
        "model_id": model_id,
    }


def build_chosen_messages(row, generation_config):
    """
    Build the chat messages used for model-generated chosen responses.
    """

    system_prompt = generation_config["safety_system_prompt"]
    chosen_instruction = generation_config.get("chosen_response_instruction", "")

    full_system_prompt = "\n\n".join(
        part for part in [system_prompt, chosen_instruction] if part
    )

    return [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": row["prompt_text"]},
    ]


def generate_model_chosen_response(row, model_bundle, generation_config):
    """
    Generate a chosen response for a public prompt using the local model.
    """

    import torch

    model = model_bundle["model"]
    tokenizer = model_bundle["tokenizer"]
    device = model_bundle["device"]

    messages = build_chosen_messages(row, generation_config)

    if hasattr(tokenizer, "apply_chat_template"):
        encoded = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        )

        if isinstance(encoded, dict):
            input_ids = encoded["input_ids"].to(device)
            attention_mask = encoded.get("attention_mask")
            if attention_mask is not None:
                attention_mask = attention_mask.to(device)
        else:
            input_ids = encoded.to(device)
            attention_mask = None
    else:
        prompt_text = (
            f"System: {messages[0]['content']}\n\n"
            f"User: {messages[1]['content']}\n\n"
            "Assistant:"
        )
        encoded = tokenizer(prompt_text, return_tensors="pt")
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)

    generation_kwargs = {
        "max_new_tokens": generation_config.get("max_new_tokens", 384),
        "do_sample": generation_config.get("do_sample", True),
        "repetition_penalty": generation_config.get("repetition_penalty", 1.0),
        "pad_token_id": tokenizer.eos_token_id,
    }

    if generation_kwargs["do_sample"]:
        generation_kwargs["temperature"] = generation_config.get("temperature", 0.7)
        generation_kwargs["top_p"] = generation_config.get("top_p", 0.9)

    if attention_mask is not None:
        generation_kwargs["attention_mask"] = attention_mask

    with torch.no_grad():
        output_ids = model.generate(
            input_ids=input_ids,
            **generation_kwargs,
        )

    new_tokens = output_ids[0][input_ids.shape[-1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    return response



def response_appears_cut_off(response):
    """
    Detect responses that appear unfinished.
    """

    unfinished_endings = [
        "but",
        "and",
        "or",
        "because",
        "although",
        "while",
        "taking small, consistent",
        "for example",
        "such as",
        "including",
        "to help you",
        "you can try to",
    ]

    response_lower = response.strip().lower()

    if response_lower.endswith(tuple(unfinished_endings)):
        return True

    return False

def public_response_passes_relevance_check(row, response):
    """
    Check whether a public chosen response is prompt-specific enough.

    SyntheticSafety rows do not use this check because they use controlled
    safety templates.
    """

    if should_use_controlled_chosen_template(row):
        return True, ""

    if len(response.split()) < 25:
        return False, "response too short"

    if response_appears_cut_off(response):
        return False, "response appears cut off or unfinished"

    generic_fragments = [
        "i'm sorry you're feeling this way",
        "that sounds difficult to carry",
        "one small step could be to pause",
        "write down what feels most urgent",
    ]

    response_lower = response.lower()

    for fragment in generic_fragments:
        if fragment in response_lower:
            return False, "response contains generic template wording"

    if not has_prompt_specific_overlap(row.get("prompt_text", ""), response):
        return False, "response does not clearly reflect the specific prompt"

    return True, ""


def create_chosen_response(row, model_bundle, generation_config):
    """
    Create one chosen response.

    - SyntheticSafety uses controlled templates.
    - Public prompts use local model generation.
    """

    if should_use_controlled_chosen_template(row):
        return create_controlled_template_chosen_response(row), {
            "chosen_generation_method": "template",
            "chosen_generator": TEMPLATE_CHOSEN_VERSION,
            "pair_quality_status": "checked",
            "exclusion_reason": "",
        }

    # Public prompts: generate with the local model.
    max_attempts = 2

    for attempt in range(1, max_attempts + 1):
        response = generate_model_chosen_response(
            row=row,
            model_bundle=model_bundle,
            generation_config=generation_config,
        )

        passes, reason = public_response_passes_relevance_check(row, response)

        if passes:
            return response, {
                "chosen_generation_method": "model",
                "chosen_generator": model_bundle["model_id"],
                "pair_quality_status": "checked",
                "exclusion_reason": "",
            }

        print(
            f"Regenerating {row.get('prompt_id')} because public response failed relevance check: {reason}"
        )

    return "", {
        "chosen_generation_method": "model",
        "chosen_generator": model_bundle["model_id"],
        "pair_quality_status": "excluded",
        "exclusion_reason": reason,
    }


def make_sft_row(row, chosen_response, chosen_metadata, generation_date):
    return {
        "prompt_id": row["prompt_id"],
        "prompt": row["prompt_text"],
        "response": chosen_response,
        "category": row.get("category"),
        "severity": row.get("severity"),
        "source_dataset": row.get("source_dataset"),
        "detected_risk_level": row.get("detected_risk_level"),
        "requires_escalation": row.get("requires_escalation"),
        "requires_refusal": row.get("requires_refusal"),
        "boundary_issue": row.get("boundary_issue"),
        "risk_flags": row.get("risk_flags", []),
        "chosen_generation_method": chosen_metadata.get("chosen_generation_method"),
        "chosen_generator": chosen_metadata.get("chosen_generator"),
        "pair_quality_status": chosen_metadata.get("pair_quality_status"),
        "exclusion_reason": chosen_metadata.get("exclusion_reason", ""),
        "generation_date": generation_date,
    }


def make_dpo_row(
    row,
    chosen_response,
    rejected_response,
    rejected_type,
    chosen_metadata,
    generation_date,
):
    return {
        "prompt_id": row["prompt_id"],
        "prompt": row["prompt_text"],
        "chosen": chosen_response,
        "rejected": rejected_response,
        "rejected_type": rejected_type,
        "category": row.get("category"),
        "severity": row.get("severity"),
        "source_dataset": row.get("source_dataset"),
        "detected_risk_level": row.get("detected_risk_level"),
        "requires_escalation": row.get("requires_escalation"),
        "requires_refusal": row.get("requires_refusal"),
        "boundary_issue": row.get("boundary_issue"),
        "risk_flags": row.get("risk_flags", []),
        "chosen_generation_method": chosen_metadata.get("chosen_generation_method"),
        "chosen_generator": chosen_metadata.get("chosen_generator"),
        "rejected_generation_method": "template",
        "rejected_generator": REJECTED_TEMPLATE_VERSION,
        "pair_quality_status": chosen_metadata.get("pair_quality_status"),
        "exclusion_reason": chosen_metadata.get("exclusion_reason", ""),
        "generation_date": generation_date,
    }


def create_hybrid_response_pairs(project_root, pilot=True):
    """
    Create SFT and DPO files using the hybrid policy:

    - SyntheticSafety chosen responses: controlled templates
    - Public chosen responses: local model generation
    - Rejected responses: controlled flawed templates
    """

    config = get_response_pairing_config(project_root)
    generation_config = get_generation_config(project_root)

    pairing_paths = config["pairing_prompt_outputs"]
    outputs = config["pilot_outputs"] if pilot else config["main_outputs"]

    train_prompts = read_jsonl(
        resolve_pairing_path(project_root, pairing_paths["train"])
    )
    validation_prompts = read_jsonl(
        resolve_pairing_path(project_root, pairing_paths["validation"])
    )

    all_prompts = train_prompts + validation_prompts
    needs_model = any(not should_use_controlled_chosen_template(row) for row in all_prompts)

    model_bundle = None
    if needs_model:
        model_bundle = load_local_generation_model(project_root)

    generation_date = datetime.now(timezone.utc).date().isoformat()

    excluded_rows = []

    def convert(rows):
        sft_rows = []
        dpo_rows = []

        for row in rows:
            chosen, chosen_metadata = create_chosen_response(
                row=row,
                model_bundle=model_bundle,
                generation_config=generation_config,
            )

            if chosen_metadata.get("pair_quality_status") == "excluded":
                excluded_rows.append(
                    {
                        "prompt_id": row.get("prompt_id"),
                        "source_dataset": row.get("source_dataset"),
                        "category": row.get("category"),
                        "reason": chosen_metadata.get("exclusion_reason"),
                    }
                )
                continue

            rejected_type = choose_rejected_prompt_type(row)
            rejected = create_template_rejected_response(row)

            sft_rows.append(
                make_sft_row(
                    row=row,
                    chosen_response=chosen,
                    chosen_metadata=chosen_metadata,
                    generation_date=generation_date,
                )
            )

            dpo_rows.append(
                make_dpo_row(
                    row=row,
                    chosen_response=chosen,
                    rejected_response=rejected,
                    rejected_type=rejected_type,
                    chosen_metadata=chosen_metadata,
                    generation_date=generation_date,
                )
            )

        return sft_rows, dpo_rows

    train_sft, train_dpo = convert(train_prompts)
    validation_sft, validation_dpo = convert(validation_prompts)

    write_jsonl(train_sft, resolve_pairing_path(project_root, outputs["train_sft"]))
    write_jsonl(train_dpo, resolve_pairing_path(project_root, outputs["train_dpo"]))
    write_jsonl(validation_sft, resolve_pairing_path(project_root, outputs["validation_sft"]))
    write_jsonl(validation_dpo, resolve_pairing_path(project_root, outputs["validation_dpo"]))

    print("Created hybrid response-pair files")
    print("=" * 40)
    print(f"Train SFT: {len(train_sft)}")
    print(f"Train DPO: {len(train_dpo)}")
    print(f"Validation SFT: {len(validation_sft)}")
    print(f"Validation DPO: {len(validation_dpo)}")
    print(f"Excluded during generation: {len(excluded_rows)}")

    if excluded_rows:
        print("\nExcluded examples:")
        for row in excluded_rows[:20]:
            print(
                f"- {row['prompt_id']} | {row['source_dataset']} | {row['category']} | {row['reason']}"
            )



def has_prompt_specific_overlap(prompt, response):
    """
    Simple relevance check.

    This function flags responses that are very generic and do not reflect the user's actual concern.
    """

    stopwords = {
        "the", "and", "but", "you", "your", "that", "this", "with", "for",
        "are", "was", "were", "have", "has", "had", "feel", "feeling",
        "really", "very", "just", "like", "about", "because", "what",
        "when", "where", "how", "why", "can", "could", "would", "should",
        "i", "me", "my", "to", "of", "in", "it", "is", "am", "be", "been",
    }

    prompt_words = {
        word.strip(".,!?;:()[]\"'").lower()
        for word in prompt.split()
    }

    response_words = {
        word.strip(".,!?;:()[]\"'").lower()
        for word in response.split()
    }

    prompt_keywords = {
        word
        for word in prompt_words
        if len(word) >= 5 and word not in stopwords
    }

    if not prompt_keywords:
        return True

    overlap = prompt_keywords.intersection(response_words)

    return len(overlap) >= 1

def is_simple_bereavement_prompt(row):
    """
    Detect short, direct bereavement prompts that are better handled by a
    controlled grief template.

    Longer public prompts may mention death/loss as context while asking about
    something else. Those should usually go to the local model so the response
    can address the full situation.
    """

    prompt_text = row.get("prompt_text", "") or row.get("prompt", "")
    prompt_lower = prompt_text.lower()
    word_count = len(prompt_text.split())

    grief_keywords = [
        "died",
        "death",
        "dead",
        "passed away",
        "lost my",
        "loss of",
        "funeral",
        "grieving",
        "bereaved",
    ]

    has_grief_signal = any(keyword in prompt_lower for keyword in grief_keywords)

    return has_grief_signal and word_count <= 25


def validate_response_pair_rows(rows, mode):
    errors = []
    warnings = []

    for index, row in enumerate(rows, start=1):
        prompt_id = row.get("prompt_id")

        if not prompt_id:
            errors.append(f"Line {index}: missing prompt_id")

        if not row.get("prompt"):
            errors.append(f"Line {index}: missing prompt")

        if mode == "sft":
            if not row.get("response"):
                errors.append(f"Line {index}: missing response")

        if mode == "dpo":
            chosen = row.get("chosen", "")
            rejected = row.get("rejected", "")

            if not chosen:
                errors.append(f"Line {index}: missing chosen")

            if not rejected:
                errors.append(f"Line {index}: missing rejected")

            if chosen and rejected and chosen.strip() == rejected.strip():
                errors.append(f"Line {index}: chosen and rejected are identical")

        response_text = row.get("response") or row.get("chosen") or ""

        if response_appears_cut_off(response_text):
            errors.append(
                f"Line {index}: chosen/response appears to be cut off or unfinished"
            )

        prompt_text = row.get("prompt", "")
        if response_text and prompt_text:
            if not has_prompt_specific_overlap(prompt_text, response_text):
                warnings.append(f"Line {index}: chosen/response may be too generic or not prompt-specific")


        if len(response_text) < 40:
            warnings.append(f"Line {index}: chosen/response is very short")

        if row.get("requires_escalation"):
            escalation_terms = [
                "emergency services",
                "crisis line",
                "someone you trust",
                "trusted person",
                "immediately",
                "unable to stay safe",
                "real-world support",
            ]
            lower_response = response_text.lower()

            if not any(term in lower_response for term in escalation_terms):
                errors.append(
                    f"Line {index}: escalation required but chosen response does not clearly escalate"
                )

        if row.get("requires_refusal"):
        
            refusal_terms = [
                "cannot help",
                "can't help",
                "cannot support",
                "can't support",
                "not able to help",
                "i cannot help",
                "i can't help",
                "i cannot provide",
                "i can't provide",
                "i cannot assist",
                "i can't assist",
                "i cannot advise",
                "i can't advise",
            ]

            lower_response = response_text.lower()

            if not any(term in lower_response for term in refusal_terms):
                warnings.append(
                    f"Line {index}: refusal may be required but response may not refuse clearly"
                )

    return errors, warnings


def validate_response_pair_files(project_root, pilot=True):
    config = get_response_pairing_config(project_root)
    outputs = config["pilot_outputs"] if pilot else config["main_outputs"]

    files = {
        "train_sft": ("sft", resolve_pairing_path(project_root, outputs["train_sft"])),
        "train_dpo": ("dpo", resolve_pairing_path(project_root, outputs["train_dpo"])),
        "validation_sft": ("sft", resolve_pairing_path(project_root, outputs["validation_sft"])),
        "validation_dpo": ("dpo", resolve_pairing_path(project_root, outputs["validation_dpo"])),
    }

    total_errors = []
    total_warnings = []

    for name, (mode, path) in files.items():
        rows = read_jsonl(path)
        errors, warnings = validate_response_pair_rows(rows, mode)

        total_errors.extend([f"{name}: {error}" for error in errors])
        total_warnings.extend([f"{name}: {warning}" for warning in warnings])

        print(f"{name}: {len(rows)} rows checked")

    if total_warnings:
        print("\nWarnings:")
        for warning in total_warnings[:30]:
            print(f"- {warning}")

    if total_errors:
        print("\nErrors:")
        for error in total_errors[:30]:
            print(f"- {error}")
        raise ValueError("Response-pair validation failed.")

    print("\nResponse-pair validation passed.")