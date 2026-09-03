"""
Inference and output generation for the project.

This module supports:
1. Validation-only router smoke testing.
2. Locked test-set generation for raw model conditions.
3. Locked test-set generation for guarded model conditions.

The locked test set is only used after training, prompt selection, and router
development are frozen.
"""

from pathlib import Path
import json
import gc
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

from src.utils import load_yaml, resolve_project_path
from src.safety_router import route_prompt


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

def get_prompt_text(row: dict) -> str:
    """
    Return the prompt text from either response-pair files or locked test files.

    Training/validation response-pair files use:
      - prompt

    The locked test prompt file uses:
      - prompt_text
    """

    prompt = row.get("prompt")

    if prompt is None:
        prompt = row.get("prompt_text")

    if prompt is None:
        raise KeyError(
            "Could not find prompt text. Expected either 'prompt' or 'prompt_text'. "
            f"Available keys: {list(row.keys())}"
        )

    if not isinstance(prompt, str):
        raise TypeError(
            f"Prompt must be a string, but got {type(prompt)} for "
            f"prompt_id={row.get('prompt_id')}"
        )

    if not prompt.strip():
        raise ValueError(f"Empty prompt text for prompt_id={row.get('prompt_id')}")

    return prompt.strip()


def load_inference_configs(project_root: Path):
    model_config = load_yaml(project_root / "configs" / "model_config.yaml")
    generation_config = load_yaml(project_root / "configs" / "generation_config.yaml")
    evaluation_config = load_yaml(project_root / "configs" / "evaluation_config.yaml")

    return (
        model_config,
        generation_config["generation"],
        evaluation_config["evaluation"],
    )


def load_tokenizer_for_inference(model_id: str):
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    if tokenizer.bos_token_id is None:
        tokenizer.bos_token = "<|im_start|>"

    if tokenizer.eos_token_id is None:
        tokenizer.eos_token = "<|im_end|>"

    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"

    if tokenizer.bos_token_id is None:
        raise ValueError("Tokenizer BOS token ID is None.")
    if tokenizer.eos_token_id is None:
        raise ValueError("Tokenizer EOS token ID is None.")
    if tokenizer.pad_token_id is None:
        raise ValueError("Tokenizer PAD token ID is None.")

    print("Tokenizer check:")
    print("bos_token:", tokenizer.bos_token)
    print("bos_token_id:", tokenizer.bos_token_id)
    print("eos_token:", tokenizer.eos_token)
    print("eos_token_id:", tokenizer.eos_token_id)
    print("pad_token:", tokenizer.pad_token)
    print("pad_token_id:", tokenizer.pad_token_id)

    return tokenizer


def sync_model_token_ids(model, tokenizer):
    model.config.bos_token_id = tokenizer.bos_token_id
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id

    if hasattr(model, "generation_config"):
        model.generation_config.bos_token_id = tokenizer.bos_token_id
        model.generation_config.eos_token_id = tokenizer.eos_token_id
        model.generation_config.pad_token_id = tokenizer.pad_token_id

        # Avoid deterministic-generation warnings caused by model defaults.
        model.generation_config.do_sample = False
        model.generation_config.temperature = None
        model.generation_config.top_p = None
        model.generation_config.top_k = None


def build_messages(prompt: str, system_prompt: Optional[str]) -> list[dict]:
    if system_prompt is None:
        return [{"role": "user", "content": prompt}]

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]


def load_model_condition(
    model_id: str,
    tokenizer,
    adapter_path: Optional[Path],
):
    base_model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )

    if adapter_path is not None:
        if not adapter_path.exists():
            raise FileNotFoundError(f"Missing adapter directory: {adapter_path}")
        model = PeftModel.from_pretrained(base_model, adapter_path)
    else:
        model = base_model

    sync_model_token_ids(model, tokenizer)
    model.eval()

    return model


def generate_model_response(
    model,
    tokenizer,
    prompt: str,
    system_prompt: Optional[str],
    max_new_tokens: int,
) -> str:
    messages = build_messages(prompt=prompt, system_prompt=system_prompt)

    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt_text, return_tensors="pt")

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )

    generated = tokenizer.decode(
        output_ids[0][inputs["input_ids"].shape[-1]:],
        skip_special_tokens=True,
    ).strip()

    return generated


def get_raw_conditions(project_root: Path, safety_system_prompt: str) -> list[dict]:
    """
    M0 receives no explicit safety system prompt.
    M1, M2, and M3 receive the same safety system prompt.
    """

    return [
        {
            "condition": "m0_base",
            "adapter_path": None,
            "system_prompt": None,
            "system_prompt_type": "none",
            "use_router": False,
            "output_file": "test_outputs_m0_base.jsonl",
        },
        {
            "condition": "m1_prompt_only",
            "adapter_path": None,
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": False,
            "output_file": "test_outputs_m1_prompt_only.jsonl",
        },
        {
            "condition": "m2_sft",
            "adapter_path": project_root / "models/sft/seed_42/final_adapter",
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": False,
            "output_file": "test_outputs_m2_sft.jsonl",
        },
        {
            "condition": "m3_dpo",
            "adapter_path": project_root / "models/dpo/seed_42/final_adapter",
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": False,
            "output_file": "test_outputs_m3_dpo.jsonl",
        },
    ]


def get_guarded_conditions(project_root: Path, safety_system_prompt: str) -> list[dict]:
    """
    Guarded conditions use the deterministic safety router before generation.

    The router only inspects the prompt text. It does not use labels/categories.
    """

    return [
        {
            "condition": "m1_prompt_only_guarded",
            "adapter_path": None,
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": True,
            "output_file": "test_outputs_m1_prompt_only_guarded.jsonl",
        },
        {
            "condition": "m2_sft_guarded",
            "adapter_path": project_root / "models/sft/seed_42/final_adapter",
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": True,
            "output_file": "test_outputs_m2_sft_guarded.jsonl",
        },
        {
            "condition": "m3_dpo_guarded",
            "adapter_path": project_root / "models/dpo/seed_42/final_adapter",
            "system_prompt": safety_system_prompt,
            "system_prompt_type": "safety_system_prompt",
            "use_router": True,
            "output_file": "test_outputs_m3_dpo_guarded.jsonl",
        },
    ]


def generate_condition_outputs(
    project_root: Path,
    prompts: list[dict],
    condition: dict,
    model_id: str,
    tokenizer,
    max_new_tokens: int,
    output_dir: Path,
) -> Path:
    condition_name = condition["condition"]
    adapter_path = condition["adapter_path"]
    system_prompt = condition["system_prompt"]
    system_prompt_type = condition["system_prompt_type"]
    use_router = condition["use_router"]
    output_path = output_dir / condition["output_file"]

    print("\n" + "=" * 100)
    print("Generating condition:", condition_name)
    print("Router:", use_router)
    print("Adapter:", adapter_path if adapter_path is not None else "none")
    print("Output:", output_path)

    model = load_model_condition(
        model_id=model_id,
        tokenizer=tokenizer,
        adapter_path=adapter_path,
    )

    outputs = []

    for index, row in enumerate(prompts, start=1):
        prompt = get_prompt_text(row)
        route_result = route_prompt(prompt) if use_router else None

        if use_router and route_result.routed:
            generated = route_result.response
            router_applied = True
            router_reason = route_result.route_type
        else:
            generated = generate_model_response(
                model=model,
                tokenizer=tokenizer,
                prompt=prompt,
                system_prompt=system_prompt,
                max_new_tokens=max_new_tokens,
            )
            router_applied = False
            router_reason = None

        output_row = {
            "prompt_id": row.get("prompt_id"),
            "category": row.get("category"),
            "source_dataset": row.get("source_dataset"),
            "prompt": prompt,
            "condition": condition_name,
            "adapter_path": str(adapter_path) if adapter_path is not None else None,
            "system_prompt_type": system_prompt_type,
            "router_enabled": use_router,
            "router_applied": router_applied,
            "router_reason": router_reason,
            "max_new_tokens": max_new_tokens,
            "do_sample": False,
            "generated_response": generated,
        }

        outputs.append(output_row)

        if index % 25 == 0 or index == len(prompts):
            print(f"{condition_name}: generated {index}/{len(prompts)}")

    write_jsonl(output_path, outputs)

    del model
    gc.collect()

    return output_path


def run_router_smoke_test(project_root: Path):
    """
    Validation-only smoke test for the deterministic router.

    This must be run before locked test-set generation.
    """

    validation_files = [
        project_root / "data/splits/validation_sft.jsonl",
        project_root / "data/splits/validation_dpo.jsonl",
    ]

    target_prompt_ids = [
        "synthetic_crisis_direct_005",
        "synthetic_diagnosis_boundary_017",
        "synthetic_medication_boundary_005",
    ]

    rows_by_id = {}

    for file_path in validation_files:
        if not file_path.exists():
            continue

        for row in read_jsonl(file_path):
            prompt_id = row.get("prompt_id")
            if prompt_id in target_prompt_ids and prompt_id not in rows_by_id:
                rows_by_id[prompt_id] = row

    missing = [pid for pid in target_prompt_ids if pid not in rows_by_id]
    if missing:
        raise ValueError(f"Missing validation prompts: {missing}")

    rows = [rows_by_id[pid] for pid in target_prompt_ids]

    results = []

    for row in rows:
        prompt = get_prompt_text(row)
        route_result = route_prompt(prompt)

        results.append(
             {
                "prompt_id": row.get("prompt_id"),
                "category": row.get("category"),
                "source_dataset": row.get("source_dataset"),
                "prompt": prompt,
                "router_applied": route_result.routed,
                "router_reason": route_result.route_type,
                "generated_response": route_result.response,
            }
        )

    output_jsonl = project_root / "results/model_outputs/router_smoke_test_validation.jsonl"
    output_txt = project_root / "results/model_outputs/router_smoke_test_validation_readable.txt"

    write_jsonl(output_jsonl, results)

    output_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(output_txt, "w", encoding="utf-8") as f:
        f.write("Validation-only router smoke test\n")
        f.write("=" * 100 + "\n\n")

        for result in results:
            f.write("-" * 100 + "\n")
            f.write(f"Prompt ID: {result['prompt_id']}\n")
            f.write(f"Category: {result['category']}\n")
            f.write(f"Router applied: {result['router_applied']}\n")
            f.write(f"Router reason: {result['router_reason']}\n\n")
            f.write("Prompt:\n")
            f.write(result["prompt"] + "\n\n")
            f.write("Router response:\n")
            f.write(str(result["generated_response"]) + "\n\n")

    print("\nRouter smoke test complete.")
    print("Saved JSONL:", output_jsonl)
    print("Saved readable file:", output_txt)

    for result in results:
        print("\n" + "-" * 100)
        print("Prompt ID:", result["prompt_id"])
        print("Category:", result["category"])
        print("Router applied:", result["router_applied"])
        print("Router reason:", result["router_reason"])
        print("Response:")
        print(result["generated_response"])


def generate_test_outputs_raw(project_root: Path):
    """
    Generate locked test-set outputs for raw model conditions.

    This uses the locked test set. Only run after training, prompt choice,
    and router development are frozen.
    """

    model_config, generation_config, evaluation_config = load_inference_configs(project_root)

    model_id = model_config["model"]["primary_model_id"]
    safety_system_prompt = generation_config["safety_system_prompt"]
    max_new_tokens = evaluation_config.get("max_new_tokens", 384)

    test_path = resolve_project_path(
        project_root,
        evaluation_config.get("locked_test_path", "data/splits/test_prompts_LOCKED.jsonl"),
    )

    prompts = read_jsonl(test_path)

    tokenizer = load_tokenizer_for_inference(model_id)
    conditions = get_raw_conditions(project_root, safety_system_prompt)

    output_dir = project_root / "results/model_outputs"

    generated_paths = []

    for condition in conditions:
        output_path = generate_condition_outputs(
            project_root=project_root,
            prompts=prompts,
            condition=condition,
            model_id=model_id,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            output_dir=output_dir,
        )
        generated_paths.append(str(output_path))

    print("\nRaw locked test generation complete.")
    for path in generated_paths:
        print("-", path)


def generate_test_outputs_guarded(project_root: Path):
    """
    Generate locked test-set outputs for guarded model conditions.
    """

    model_config, generation_config, evaluation_config = load_inference_configs(project_root)

    model_id = model_config["model"]["primary_model_id"]
    safety_system_prompt = generation_config["safety_system_prompt"]
    max_new_tokens = evaluation_config.get("max_new_tokens", 384)

    test_path = resolve_project_path(
        project_root,
        evaluation_config.get("locked_test_path", "data/splits/test_prompts_LOCKED.jsonl"),
    )

    prompts = read_jsonl(test_path)

    tokenizer = load_tokenizer_for_inference(model_id)
    conditions = get_guarded_conditions(project_root, safety_system_prompt)

    output_dir = project_root / "results/model_outputs"

    generated_paths = []

    for condition in conditions:
        output_path = generate_condition_outputs(
            project_root=project_root,
            prompts=prompts,
            condition=condition,
            model_id=model_id,
            tokenizer=tokenizer,
            max_new_tokens=max_new_tokens,
            output_dir=output_dir,
        )
        generated_paths.append(str(output_path))

    print("\nGuarded locked test generation complete.")
    for path in generated_paths:
        print("-", path)