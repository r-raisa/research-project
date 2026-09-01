"""
Training for the LLM therapy post-training project.

This module trains:
1. SFT LoRA model on chosen responses.
2. DPO LoRA model on chosen/rejected response pairs.

The locked test set is never used here.
"""

from pathlib import Path
import json
import csv
import time
import random
import os

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, set_seed
from peft import LoraConfig, PeftModel
from trl import SFTTrainer, DPOTrainer

from src.utils import load_yaml, resolve_project_path


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def get_device_and_dtype(training_config=None):
    """
    Choose device and dtype.

    CPU float32 is used when force_cpu is enabled. This is slower but more
    stable than MPS for local Mac training.
    """

    training_config = training_config or {}

    if training_config.get("force_cpu", False):
        return "cpu", torch.float32

    if torch.cuda.is_available():
        return "cuda", torch.float16

    if torch.backends.mps.is_available():
        return "mps", torch.float16

    return "cpu", torch.float32


def load_training_configs(project_root):
    model_config = load_yaml(project_root / "configs" / "model_config.yaml")
    generation_config = load_yaml(project_root / "configs" / "generation_config.yaml")
    training_config = load_yaml(project_root / "configs" / "training_config.yaml")

    return model_config, generation_config["generation"], training_config["training"]


def load_tokenizer(model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    tokenizer.padding_side = "right"
    return tokenizer


def load_base_model(model_id, training_config=None):
    device, dtype = get_device_and_dtype(training_config)

    print(f"Loading model: {model_id}")
    print(f"Device: {device}")
    print(f"Dtype: {dtype}")

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )

    model.config.use_cache = False
    model.to(device)

    return model, device


def build_lora_config(training_config):
    lora_cfg = training_config["lora"]

    return LoraConfig(
        r=lora_cfg["r"],
        lora_alpha=lora_cfg["lora_alpha"],
        lora_dropout=lora_cfg["lora_dropout"],
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=lora_cfg["target_modules"],
    )


def format_sft_dataset(rows, tokenizer, system_prompt):
    formatted = []

    for row in rows:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": row["prompt"]},
            {"role": "assistant", "content": row["response"]},
        ]

        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )

        formatted.append(
            {
                "text": text,
                "prompt_id": row["prompt_id"],
                "category": row.get("category"),
                "source_dataset": row.get("source_dataset"),
            }
        )

    return Dataset.from_list(formatted)


def format_dpo_dataset(rows, tokenizer, system_prompt):
    formatted = []

    for row in rows:
        prompt_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": row["prompt"]},
        ]

        prompt_text = tokenizer.apply_chat_template(
            prompt_messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        formatted.append(
            {
                "prompt": prompt_text,
                "chosen": row["chosen"] + tokenizer.eos_token,
                "rejected": row["rejected"] + tokenizer.eos_token,
                "prompt_id": row["prompt_id"],
                "category": row.get("category"),
                "source_dataset": row.get("source_dataset"),
            }
        )

    return Dataset.from_list(formatted)


def write_run_metadata(output_dir, metadata):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "run_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def train_sft(project_root):
    project_root = Path(project_root)

    model_config, generation_config, training_config = load_training_configs(project_root)
    model_id = model_config["model"]["primary_model_id"]
    system_prompt = generation_config["safety_system_prompt"]

    data_cfg = training_config["data"]
    output_root = project_root / training_config["output"]["model_dir"]
    log_root = project_root / training_config["output"]["log_dir"]
    log_root.mkdir(parents=True, exist_ok=True)

    seeds = training_config.get("seeds", [42])

    for seed in seeds:
        print("\n" + "=" * 80)
        print(f"Starting SFT training for seed {seed}")
        print("=" * 80)

        set_seed(seed)
        random.seed(seed)

        run_start = time.time()

        tokenizer = load_tokenizer(model_id)
        model, device = load_base_model(model_id, training_config)

        train_rows = read_jsonl(resolve_project_path(project_root, data_cfg["train_sft"]))
        validation_rows = read_jsonl(resolve_project_path(project_root, data_cfg["validation_sft"]))

        train_dataset = format_sft_dataset(train_rows, tokenizer, system_prompt)
        validation_dataset = format_sft_dataset(validation_rows, tokenizer, system_prompt)

        sft_cfg = training_config["sft"]
        output_dir = output_root / "sft" / f"seed_{seed}"

        args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=sft_cfg["num_train_epochs"],
            learning_rate=sft_cfg["learning_rate"],
            per_device_train_batch_size=sft_cfg["per_device_train_batch_size"],
            per_device_eval_batch_size=sft_cfg["per_device_eval_batch_size"],
            gradient_accumulation_steps=sft_cfg["gradient_accumulation_steps"],
            logging_steps=sft_cfg["logging_steps"],
            evaluation_strategy=sft_cfg["evaluation_strategy"],
            save_strategy=sft_cfg["save_strategy"],
            save_total_limit=sft_cfg["save_total_limit"],
            report_to="none",
            seed=seed,
            fp16=False,
            use_cpu=training_config.get("force_cpu", False),
            remove_unused_columns=True,
            warmup_ratio=sft_cfg.get("warmup_ratio", 0.0),
            max_grad_norm=sft_cfg.get("max_grad_norm", 1.0),
            gradient_checkpointing=sft_cfg.get("gradient_checkpointing", False),
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            args=args,
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            dataset_text_field="text",
            max_seq_length=sft_cfg["max_seq_length"],
            packing=False,
            peft_config=build_lora_config(training_config),
        )

        train_result = trainer.train()
        eval_result = trainer.evaluate()

        final_dir = output_dir / "final_adapter"
        trainer.model.save_pretrained(final_dir)
        tokenizer.save_pretrained(final_dir)

        run_time_minutes = (time.time() - run_start) / 60

        metadata = {
            "stage": "sft",
            "seed": seed,
            "model_id": model_id,
            "train_rows": len(train_rows),
            "validation_rows": len(validation_rows),
            "output_dir": str(output_dir),
            "final_adapter": str(final_dir),
            "training_time_minutes": run_time_minutes,
            "device": device,
            "sft_config": sft_cfg,
            "lora_config": training_config["lora"],
            "train_metrics": train_result.metrics,
            "eval_metrics": eval_result,
        }

        write_run_metadata(output_dir, metadata)

        print("\nSFT complete")
        print(f"Saved adapter to: {final_dir}")
        print(f"Training time: {run_time_minutes:.2f} minutes")


def train_dpo(project_root):
    project_root = Path(project_root)

    model_config, generation_config, training_config = load_training_configs(project_root)
    model_id = model_config["model"]["primary_model_id"]
    system_prompt = training_config.get(
    "training_system_prompt",
    generation_config["safety_system_prompt"],
    )

    data_cfg = training_config["data"]
    output_root = project_root / training_config["output"]["model_dir"]

    seeds = training_config.get("seeds", [42])

    for seed in seeds:
        print("\n" + "=" * 80)
        print(f"Starting DPO training for seed {seed}")
        print("=" * 80)

        set_seed(seed)
        random.seed(seed)

        run_start = time.time()

        tokenizer = load_tokenizer(model_id)

        sft_adapter_dir = output_root / "sft" / f"seed_{seed}" / "final_adapter"
        if not sft_adapter_dir.exists():
            raise FileNotFoundError(
                f"Missing SFT adapter for seed {seed}: {sft_adapter_dir}. "
                "Run SFT before DPO."
            )

        base_model, device = load_base_model(model_id, training_config)
        model = PeftModel.from_pretrained(
            base_model,
            sft_adapter_dir,
            is_trainable=True,
        )

        ref_base_model, _ = load_base_model(model_id, training_config)
        ref_model = PeftModel.from_pretrained(
            ref_base_model,
            sft_adapter_dir,
            is_trainable=False,
        )

        train_rows = read_jsonl(resolve_project_path(project_root, data_cfg["train_dpo"]))
        validation_rows = read_jsonl(resolve_project_path(project_root, data_cfg["validation_dpo"]))

        train_dataset = format_dpo_dataset(train_rows, tokenizer, system_prompt)
        validation_dataset = format_dpo_dataset(validation_rows, tokenizer, system_prompt)

        dpo_cfg = training_config["dpo"]
        output_dir = output_root / "dpo" / f"seed_{seed}"

        args = TrainingArguments(
            output_dir=str(output_dir),
            num_train_epochs=dpo_cfg["num_train_epochs"],
            learning_rate=dpo_cfg["learning_rate"],
            per_device_train_batch_size=dpo_cfg["per_device_train_batch_size"],
            per_device_eval_batch_size=dpo_cfg["per_device_eval_batch_size"],
            gradient_accumulation_steps=dpo_cfg["gradient_accumulation_steps"],
            logging_steps=dpo_cfg["logging_steps"],
            evaluation_strategy=dpo_cfg["evaluation_strategy"],
            save_strategy=dpo_cfg["save_strategy"],
            save_total_limit=dpo_cfg["save_total_limit"],
            report_to="none",
            seed=seed,
            fp16=False,
            use_cpu=training_config.get("force_cpu", False),
            remove_unused_columns=False,
            warmup_ratio=dpo_cfg.get("warmup_ratio", 0.0),
            max_grad_norm=dpo_cfg.get("max_grad_norm", 1.0),
        )


        trainer = DPOTrainer(
            model=model,
            ref_model=ref_model,
            args=args,
            beta=dpo_cfg["beta"],
            train_dataset=train_dataset,
            eval_dataset=validation_dataset,
            tokenizer=tokenizer,
            max_prompt_length=dpo_cfg["max_prompt_length"],
            max_length=dpo_cfg["max_length"],
        )

        train_result = trainer.train()
        eval_result = trainer.evaluate()
        trainer.save_state()

        final_dir = output_dir / "final_adapter"
        trainer.model.save_pretrained(final_dir)
        tokenizer.save_pretrained(final_dir)

        run_time_minutes = (time.time() - run_start) / 60

        metadata = {
            "stage": "dpo",
            "seed": seed,
            "model_id": model_id,
            "sft_adapter_used": str(sft_adapter_dir),
            "train_rows": len(train_rows),
            "validation_rows": len(validation_rows),
            "output_dir": str(output_dir),
            "final_adapter": str(final_dir),
            "training_time_minutes": run_time_minutes,
            "device": device,
            "dpo_config": dpo_cfg,
            "lora_config": training_config["lora"],
            "train_metrics": train_result.metrics,
            "eval_metrics": eval_result,
        }

        write_run_metadata(output_dir, metadata)

        print("\nDPO complete")
        print(f"Saved adapter to: {final_dir}")
        print(f"Training time: {run_time_minutes:.2f} minutes")