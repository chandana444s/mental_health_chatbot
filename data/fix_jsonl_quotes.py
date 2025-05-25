import os
import re
import json
import ast  # Safely convert strings that look like Python dicts

input_file = os.path.join("data", "clean_finetune_dataset.jsonl")
output_file = os.path.join("data", "clean_finetune_dataset_fixed.jsonl")

def fix_quotes_in_text(text):
    # Replace curly quotes with straight ones
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace("‘", "'")
    # Escape inner quotes only inside values (leave outer structure alone)
    return text

fixed_lines = []

with open(input_file, 'r', encoding='utf-8') as infile:
    for raw_line in infile:
        line = raw_line.strip()
        if not line:
            continue
        try:
            # Convert Python-like dict to actual Python object
            data = ast.literal_eval(line)
            # Clean the values
            data['prompt'] = fix_quotes_in_text(data.get('prompt', ''))
            data['completion'] = fix_quotes_in_text(data.get('completion', ''))

            # Convert back to valid JSON
            fixed_json_line = json.dumps(data, ensure_ascii=False)
            fixed_lines.append(fixed_json_line)
        except Exception as e:
            print(f"Skipping invalid line:\n{line}\nError: {e}")

with open(output_file, 'w', encoding='utf-8') as outfile:
    for line in fixed_lines:
        outfile.write(line + '\n')

print(f"✅ Fixed file saved as: {output_file} with {len(fixed_lines)} valid entries.")
