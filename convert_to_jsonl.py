import pandas as pd
import ast
import os

def create_jsonl(data):
    os.makedirs("data", exist_ok=True)
    with open("data/clean_finetune_dataset.jsonl", "w", encoding="utf-8") as f:
        for _, row in data.iterrows():
            pattern = row['pattern']

            # Parse the response list
            try:
                responses = ast.literal_eval(row['response']) if isinstance(row['response'], str) else []
            except (ValueError, SyntaxError):
                responses = []

            # Format as prompt-completion pairs for Ollama/Mistral
            for response in responses:
                entry = {
                    "prompt": f"User: {pattern}",
                    "completion": f"Bot: {response.strip()}"
                }
                f.write(str(entry).replace("'", '"') + "\n")

    print("✅ clean_finetune_dataset.jsonl file created successfully!")

# Load and process the CSV
data = pd.read_csv("data/cleaned_intents.csv")
create_jsonl(data)
