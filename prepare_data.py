from datasets import load_dataset

dataset = load_dataset("json", data_files="oot_training_data.jsonl", split="train")

# Format for Alpaca template
def format_prompts(examples):
    texts = []
    for instruction, input_text, output in zip(examples["instruction"], 
                                               examples.get("input", [""]*len(examples["instruction"])), 
                                               examples["output"]):
        text = alpaca_prompt.format(instruction, input_text, output) + tokenizer.eos_token
        texts.append(text)
    return {"text": texts}

dataset = dataset.map(format_prompts, batched=True)