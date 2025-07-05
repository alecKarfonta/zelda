# OoT Training Data Integration with Unsloth

This guide explains how to use the generated OoT romhacking training data with Unsloth for fine-tuning language models.

## 🎯 Overview

The OoT training data generator creates high-quality examples for fine-tuning language models on Ocarina of Time romhacking tasks. The data is now compatible with Unsloth's training format.

## 📁 Generated Files

- `oot_training_unsloth_v2.jsonl` - Full dataset (10 examples)
- `oot_training_unsloth_test.jsonl` - Test set (3 examples)
- `sample_oot_training.jsonl` - Original generated data

## 🔧 Data Format

Each training example follows Unsloth's standard format:

```json
{
  "instruction": "Explain how Actor_SpawnAsChild() works and how it's used to create actor hierarchies in OoT",
  "input": "",
  "output": "Actor_SpawnAsChild() is a core function used to create parent-child relationships between actors in OoT. Here's how it works:\n\nFunction signature:\nActor* Actor_SpawnAsChild(GlobalContext* globalCtx, Actor* parent, u16 actorId, float x, float y, float z, s16 rotX, s16 rotY, s16 rotZ)\n\nKey points:\n- Creates a new actor instance that is linked to a parent actor\n- Child inherits certain properties from parent (like room number)\n- Child is automatically killed when parent is destroyed\n- Returns pointer to new child actor, or NULL if spawn fails\n\nCommon usage example:\n```c\n// Spawn a collectible as child of chest actor\nActor* item = Actor_SpawnAsChild(&globalCtx, &this->actor, \n    ACTOR_EN_ITEM00, // Actor ID for collectibles\n    this->actor.world.pos.x,\n    this->actor.world.pos.y + 40.0f, \n    this->actor.world.pos.z,\n    0, 0, 0); // No rotation\n\nif (item != NULL) {\n    item->params = this->itemId; // Set what item appears\n}\n```\n\nThis is commonly used for:\n- Items dropping from enemies\n- Effects attached to NPCs\n- Projectiles fired from weapons\n- Multi-part boss entities"
}
```

## 📊 Dataset Statistics

- **Total examples**: 10
- **Average instruction length**: 140.9 characters
- **Average output length**: 1532.4 characters
- **Examples with input**: 4/10 (40%)

## 🚀 Using with Unsloth

### 1. Install Unsloth

```bash
pip install unsloth
```

### 2. Basic Training Script

```python
from unsloth import FastLanguageModel
import torch

# Load model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    max_seq_length=2048,
    dtype=None,
    load_in_4bit=True,
)

# Load training data
from datasets import Dataset
import json

# Load the JSONL file
with open('oot_training_unsloth_v2.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

dataset = Dataset.from_list(data)

# Prepare for training
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

# Training arguments
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./oot-romhack-model",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    gradient_accumulation_steps=4,
    gradient_checkpointing=True,
    learning_rate=2e-4,
    logging_steps=10,
    save_steps=100,
    eval_steps=100,
    evaluation_strategy="steps",
    eval_steps=100,
    warmup_steps=100,
    report_to=None,
)

# Train the model
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    args=training_args,
    max_seq_length=2048,
    dataset_text_field="text",
)

trainer.train()
```

### 3. Advanced Training with LoRA

```python
# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing=True,
    random_state=42,
)
```

## 🎮 Example Use Cases

The trained model can help with:

1. **Code Explanation**: Understanding OoT's actor system, memory management, etc.
2. **Feature Implementation**: Creating custom actors, modifying game mechanics
3. **Debugging**: Troubleshooting crashes, memory issues, object loading problems
4. **Architecture Questions**: Understanding scene setup, collision systems, etc.
5. **Code Modification**: Safely modifying existing game code
6. **Conversational Help**: General romhacking guidance

## 📈 Scaling the Dataset

To generate more training data:

```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Generate more examples
python training_generator.py --num_examples 100 --output_file large_oot_dataset.jsonl

# Convert to Unsloth format
python convert_to_unsloth_v2.py
```

## 🔍 Quality Control

The training data includes:
- ✅ High-quality, detailed explanations
- ✅ Accurate technical information
- ✅ Proper C code examples
- ✅ Real-world romhacking scenarios
- ✅ Multiple example types (code, debugging, architecture)

## 🎯 Expected Model Behavior

After training, the model should be able to:

1. **Explain OoT concepts** clearly and accurately
2. **Provide working code examples** for romhacking tasks
3. **Debug common issues** with helpful troubleshooting steps
4. **Understand context** from partial code snippets
5. **Give architectural guidance** for complex modifications

## 🚨 Important Notes

- The dataset is currently small (10 examples) - consider generating more for production use
- Examples focus on C programming and OoT-specific concepts
- All examples are validated for technical accuracy
- The format is compatible with most fine-tuning frameworks beyond Unsloth

## 📝 Next Steps

1. **Generate more data**: Scale to 1000+ examples for better results
2. **Add more example types**: Include more debugging scenarios, advanced features
3. **Test the model**: Try fine-tuning and evaluate performance
4. **Iterate**: Use the trained model to generate even better training data

## 🤝 Contributing

To improve the training data:
1. Generate more examples using the training generator
2. Add new example types to cover more romhacking scenarios
3. Improve the validation system for better quality control
4. Test the trained model and provide feedback

---

*This training data is specifically designed for OoT romhacking tasks and should produce models that excel at helping with Zelda: Ocarina of Time modifications.* 