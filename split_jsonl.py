# split_jsonl.py

import os

input_file = "data/finetune_dataset.jsonl"  # Path to your large JSONL file
output_dir = "data/split_files"  # Directory to store split files
chunk_size = 100_000  # Number of lines per chunk

os.makedirs(output_dir, exist_ok=True)

def split_jsonl(file_path, output_dir, chunk_size):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = []
        file_count = 1

        for line_num, line in enumerate(file, start=1):
            lines.append(line)

            # Write a new chunk when chunk_size lines are reached
            if line_num % chunk_size == 0:
                output_path = os.path.join(output_dir, f"part_{file_count}.jsonl")
                with open(output_path, "w", encoding="utf-8") as output_file:
                    output_file.writelines(lines)
                lines.clear()
                file_count += 1

        # Write remaining lines if any
        if lines:
            output_path = os.path.join(output_dir, f"part_{file_count}.jsonl")
            with open(output_path, "w", encoding="utf-8") as output_file:
                output_file.writelines(lines)

split_jsonl(input_file, output_dir, chunk_size)
print("✅ Splitting complete! Check the 'split_files' folder.")
