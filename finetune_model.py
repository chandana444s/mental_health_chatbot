# finetune_model.py

from datasets import load_dataset
from transformers import LlamaForCausalLM, LlamaTokenizer
from torch.utils.data import DataLoader
from torch.optim import AdamW
import torch

# Load the preprocessed dataset
dataset_path = "D:/mental_health_chatbot/data/dataset.jsonl"
dataset = load_dataset("json", data_files=dataset_path, split="train")

# Load the tokenizer and model
model_name = "llama2:latest"  # Replace with your model name if necessary
tokenizer = LlamaTokenizer.from_pretrained(model_name)
model = LlamaForCausalLM.from_pretrained(model_name)

# Tokenize the dataset
def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True)

tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Prepare the DataLoader
batch_size = 4
train_dataloader = DataLoader(tokenized_datasets, batch_size=batch_size, shuffle=True)

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

# Optimizer setup
optimizer = AdamW(model.parameters(), lr=5e-5)

# Training loop
num_epochs = 3
for epoch in range(num_epochs):
    model.train()
    total_loss = 0
    for batch in train_dataloader:
        inputs = {key: value.to(device) for key, value in batch.items()}
        
        # Forward pass
        outputs = model(**inputs, labels=inputs["input_ids"])
        
        # Compute loss
        loss = outputs.loss
        total_loss += loss.item()
        
        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    avg_loss = total_loss / len(train_dataloader)
    print(f"Epoch {epoch + 1}, Loss: {avg_loss:.4f}")

# Save the fine-tuned model
model.save_pretrained("D:/mental_health_chatbot/fine_tuned_model")
tokenizer.save_pretrained("D:/mental_health_chatbot/fine_tuned_model")
