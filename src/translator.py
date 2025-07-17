# translator.py

from deep_translator import GoogleTranslator
from langdetect import detect, detect_langs 


def detect_language(text):
    try:
        langs = detect_langs(text)
        if langs:
            lang = langs[0].lang
            prob = langs[0].prob
            print(f"[LANG DETECTED] {lang} with probability {prob}")
            if prob < 0.90 or len(text.strip()) < 5:
                return "en"
            return lang
    except Exception as e:
        print("[ERROR] Language detection failed:", str(e))
        return "en"
def translate_to_english(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text)
    except Exception as e:
        print("[ERROR] Translation to English failed:", str(e))
        return text

def translate_from_english(text, target_language):
    try:
        if target_language == "en":
            return text
        return GoogleTranslator(source='en', target=target_language).translate(text)
    except Exception as e:
        print("[ERROR] Translation from English failed:", str(e))
        return text
    
def translate_full_response(text, target_language):
    try:
        if target_language == "en":
            return text

        # Ensure input is a string and handle any None parts
        if not isinstance(text, str):
            text = str(text)

        # Deep-translator sometimes fails on emojis or markdown. Let's remove them if needed.
        # Optional: Clean up problematic characters
        import re
        clean_text = re.sub(r'[\*\_\~\`\=\[\]]+', '', text)  # remove markdown-style chars

        translated = GoogleTranslator(source='en', target=target_language).translate(clean_text)
        return translated

    except Exception as e:
        print("[ERROR] Full response translation failed:", str(e))
        return text  # fallback to English


