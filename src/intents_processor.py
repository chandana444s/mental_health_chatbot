def recognize_intent(user_input, intents_data):
    for index, row in intents_data.iterrows():
        if user_input in row['patterns']:
            return row['tag']
    return "unknown"
