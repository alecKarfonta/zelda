#!/usr/bin/env python3
"""
Minimal Unsloth training test on OoT dataset
"""
import json
from datasets import Dataset
from unsloth import FastLanguageModel
from transformers import TrainingArguments
import torch

# Load a small model for quick test
MODEL_NAME = "unsloth/zephyr-1.1-1b-bnb-4bit"  # Small, fast model for test

# Load dataset
with open('oot_training_unsloth_v2.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]
dataset = Dataset.from_list(data)

def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs = examples["input"]
    outputs = examples["output"]
    texts = []
    for instruction, input_text, output in zip(instructions, inputs, outputs):
        if input_text:
            text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output}"
        else:
            text = f"### Instruction:\n{instruction}\n\n### Response:\n{output}"
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(formatting_prompts_func, batched=True)

# Load model and tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=MODEL_NAME,
    max_seq_length=1024,
    dtype=None,
    load_in_4bit=True,
)

# Training arguments (very short run)
training_args = TrainingArguments(
    output_dir="./oot-romhack-test-model",
    num_train_epochs=1,
    per_device_train_batch_size=2,
    max_steps=5,  # Only a few steps for test
    logging_steps=1,
    save_steps=5,
    report_to=None,
)

# Import SFTTrainer
from unsloth import SFTTrainer

# Train
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    args=training_args,
    max_seq_length=1024,
    dataset_text_field="text",
)

print("🚦 Starting minimal training run...")
trainer.train()
print("✅ Training test completed successfully!") 