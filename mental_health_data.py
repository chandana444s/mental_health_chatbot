import pandas as pd

df = pd.read_csv('data/cleaned_intents.csv')

with open('mental_health_data.txt', 'w', encoding='utf-8') as f:
    for i, row in df.iterrows():
        user_input = row['pattern']
        bot_response = row['response']
        f.write("<|system|>\nYou are a friendly and supportive mental health assistant.\n\n")
        f.write(f"<|user|>\n{user_input}\n\n")
        f.write(f"<|assistant|>\n{bot_response}\n\n")
