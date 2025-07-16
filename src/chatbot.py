import firebase_admin
from firebase_admin import credentials, initialize_app,auth, firestore
import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, g
from werkzeug.utils import secure_filename
from langchain.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from datetime import datetime
import logging
from functools import wraps
from flask_cors import CORS
import traceback 
from flask import request, jsonify
from datetime import datetime, timezone
from translator import translate_to_english, translate_from_english
from translator import detect_language, translate_full_response

# Helper function to translate full bot response if user's language is not English
def translate_full_response(text, target_lang):
    try:
        if target_lang.lower() == "en":
            return text  # No translation needed

        # Optional: sentence-by-sentence translation for better quality
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        translated = [
            translate_from_english(sentence + '.', target_lang)
            for sentence in sentences
        ]
        return ' '.join(translated)
    except Exception as e:
        print("[ERROR] in translate_full_response:", str(e))
        return text

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Unauthorized"}), 401
        try:
            token = token.split(" ")[1]
            decoded_token = auth.verify_id_token(token)
            g.decoded_token = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 403
    return decorated

# ✅ Load support resources
with open("../resources.json", "r") as f:
    SUPPORT_RESOURCES = json.load(f)

# Initialize Firebase Admin
cred = credentials.Certificate("../serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()
def verify_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # returns user data
    except Exception as e:
        return None
basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(basedir, 'templates')
static_dir = os.path.join(basedir, '../static')

app = Flask(__name__, static_folder=static_dir, template_folder="instance/templates")
app.secret_key = '285627634022592494becd9f8d7192d3'
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, expose_headers=["Authorization"])  # This will allow all origins; for more security, specify the allowed origins.
# Connect to Ollama
llm = OllamaLLM(model="mentalhealth-llama2:latest", base_url="http://localhost:11434")

# System prompt to guide the tone of the bot
SYSTEM_PROMPT = """
You are Cinnamon Bot, a compassionate and supportive mental health assistant.
Your job is to talk gently and kindly to users who may be feeling down, anxious, depressed, or overwhelmed.
Always introduce yourself warmly, like: "Hello there! *smiles* I'm Cinnamon Bot, your gentle companion here to support you."
Always respond with empathy, encouragement, and practical suggestions (e.g., self-care, connecting with loved ones, gentle reminders).
Avoid just listing emergency hotlines unless the user is clearly in danger (e.g., mentions suicide directly).
Speak with kindness, be warm, and create a comforting environment.
"""

# Chat prompt template
chat_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{user_input}"),
])

@app.route("/")
def home():
    print(f"Looking for templates in: {app.template_folder}")
    
    user_email = session.get("user_email")
    user_name = session.get("user_name")
    user_profile_pic = session.get('user_profile_pic')
    
    print(f"User email in session: {user_email}")
    print(f"User name in session: {user_name}")
    
    chat_history = session.get('chat_history', []) 

    if user_email:
        messages_ref = db.collection("chats").document(user_email).collection("messages").order_by("timestamp")
        docs = messages_ref.stream()
        chat_history = [{"role": doc.to_dict()['role'], "content": doc.to_dict()['content']} for doc in docs]
        session['chat_history'] = chat_history

    # ✅ Create welcome message with fallback
    if user_name:
        welcome_message = f"Hello {user_name}! Welcome to Cinnamon Bot. How can I help you today?"
    else:
        welcome_message = "Hello! Welcome to Cinnamon Bot. How can I help you today?"

    # ✅ Debug logs
    print("Session name:", session.get("user_name"))
    print("Final welcome message:", welcome_message)

    return render_template("index.html", 
                           user_email=user_email, 
                           user_name=user_name, 
                           user_profile_pic=user_profile_pic, 
                           messages=chat_history, 
                           welcome_message=welcome_message)

@app.route("/chat", methods=["POST"])
@token_required
def chat():
    try:
        print("All request headers:", dict(request.headers))

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or malformed Authorization header"}), 401

        id_token = auth_header.split("Bearer ")[-1].strip()
        if not id_token:
            return jsonify({"error": "Authorization token missing"}), 401

        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]

        user_message = request.json.get("message")
        user_lang = detect_language(user_message)
        print("[DEBUG] Detected language:", user_lang)

        if not user_message:
            return jsonify({"error": "No message received"}), 400

        print("[DEBUG] Received message:", user_message)
        print("[DEBUG] Requested language:", user_lang)

        # Translate input to English
        translated_input = translate_to_english(user_message)
        print("[DEBUG] Translated to English:", translated_input)

        formatted_prompt = chat_template.format(user_input=translated_input)
        print("[DEBUG] Formatted prompt:", formatted_prompt)

        response_obj = llm.invoke(formatted_prompt)
        print(response_obj)

        raw_response = getattr(response_obj, "content", str(response_obj))
        if user_lang != "en" and len(user_message.strip()) >= 5:
            response_text = translate_full_response(raw_response, user_lang)
            print("[DEBUG] Response translated to:", user_lang)
        else:
            response_text = raw_response
            print("[DEBUG] Skipping translation, sending English response")

        print("[DEBUG] Translated response back to user's language:", response_text)

        # Emotion detection optimization
        user_msg_lower = user_message.lower()
        matched_emotion = None
        emotion_data = None
        for emotion, data in SUPPORT_RESOURCES.items():
            if any(keyword in user_msg_lower for keyword in data["keywords"]):
                matched_emotion = emotion
                emotion_data = data
                break

        if emotion_data:
            resource_text = "<br><br><b>📺 Helpful Videos:</b><br>"
            for video in emotion_data.get("links", []):
                resource_text += f'<a href="{video["link"]}" target="_blank">{video["title"]}</a><br>'
            resource_text += "<br><b>📚 Book Suggestions:</b><br>"
            for book in emotion_data.get("books", []):
                resource_text += f'<a href="{book["link"]}" target="_blank">{book["title"]}</a><br>'
            response_text += resource_text

        chat_ref = db.collection("users").document(user_id).collection("chats")
        chat_ref.add({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow()
        })
        chat_ref.add({
            "role": "bot",
            "content": response_text,
            "timestamp": datetime.utcnow(),
            "detected_emotion": matched_emotion or "neutral"
        })

        return jsonify({"reply": response_text})

    except Exception as e:
        print("[ERROR] Exception occurred:")
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500
    
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        import requests

        api_key = "AIzaSyBXhgaji6rKcBcLmATDQ-uBBOkFjPXL0EY"
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        response = requests.post(url, json=payload)
        data = response.json()

        if "idToken" in data:
            session["user"] = email
            session["user_email"] = email
            session["user_id"] = data["localId"]
            id_token = data["idToken"]

            info_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
            info_payload = {"idToken": id_token}
            info_response = requests.post(info_url, json=info_payload).json()

            if "users" in info_response:
                user_info = info_response["users"][0]
                print("🔥 User info fetched:", user_info)

                user_name = user_info.get("displayName")
                if not user_name:
                    user_name = email.split('@')[0]  # fallback if displayName is empty

                session["user_name"] = user_name

            return redirect(url_for("home"))
        else:
            error_message = data.get("error", {}).get("message", "Invalid credentials.")
            return render_template("login.html", error=error_message)

    return render_template("login.html")  # ✅ This must be returned for GET requests

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            return "Please provide name, email, and password."

        try:
            # Create the user in Firebase
            user = auth.create_user(
                email=email,
                password=password
            )
            # ✅ Set the display name after creation
            auth.update_user(
                user.uid,
                display_name=name
            )

            # Store user info in session for auto-login
            session["user_email"] = email
            session["user_name"] = name

            return redirect(url_for("home"))  # Auto-login redirect
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return f"Error: {e}"

    return render_template("register.html")

# chatbot.py

@app.route("/profile")
def profile():
    user_email = session.get("user_email")
    if not user_email:
        return redirect(url_for("login"))

    # Get the ID token from session or request headers (depends on your app flow)
    id_token = session.get("id_token") or request.headers.get("Authorization").split("Bearer ")[-1]

    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token["uid"]
        user_doc = db.collection("users").document(user_id).get()
        # Handle the rest...
        return jsonify(user_doc.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/logout')
def logout():
    session.pop('user_email', None)  # Remove user_email from session
    session.pop('user_name', None)  # Remove user_name if applicable
    return redirect(url_for('home'))  # Redirect to home after logout

@app.route('/chat_history', methods=['GET'])
def get_chat_history():
    try:
        print("All request headers:", dict(request.headers))  # ADD THIS
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({"error": "Authorization header missing"}), 401

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Invalid authorization header format"}), 401

        token = auth_header.split("Bearer ")[1]

        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get("uid")

        if not user_id:
            return jsonify({"error": "Invalid token: UID not found"}), 401

        # Get chat history
        chat_ref = db.collection("users").document(user_id).collection("chats").order_by("timestamp")
        chat_docs = chat_ref.stream()

        chat_history = []
        for doc in chat_docs:
            data = doc.to_dict()
            chat_history.append({
                "role": data.get("role"),
                "content": data.get("content"),
                "timestamp": data.get("timestamp").isoformat() if data.get("timestamp") else None,
                "emotion": data.get("detected_emotion", "neutral")
            })

        return jsonify({"chat_history": chat_history})

    except auth.InvalidIdTokenError:
        return jsonify({"error": "Invalid ID token"}), 401

    except auth.ExpiredIdTokenError:
        return jsonify({"error": "Expired ID token"}), 401

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Unexpected error: " + str(e)}), 500

def delete_chat_subcollection(user_id):
    chats_ref = db.collection("users").document(user_id).collection("chats")
    docs = chats_ref.stream()
    for doc in docs:
        doc.reference.delete()

@app.route('/delete_chat_history', methods=['POST'])
def delete_chat_history():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'message': 'Missing or invalid Authorization header'}), 401

    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        user_id = decoded_token['uid']

        delete_chat_subcollection(user_id)

        return jsonify({'success': True, 'message': 'Chat history deleted successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route("/self_care_suggestions", methods=["GET"])
def get_self_care_suggestions(current_user):
    try:
        # Example suggestions based on user's previous emotion or preferences
        suggestions = [
            "Go for a walk 🌳",
            "Practice deep breathing 🧘‍♂️",
            "Talk to a trusted friend 💬",
            "Write down your thoughts 📝",
            "Listen to calming music 🎧",
        ]

        return jsonify({
            "success": True,
            "suggestions": suggestions
        }), 200

    except Exception as e:
        print("Error in self_care_suggestions:", str(e))
        return jsonify({"success": False, "message": "Could not retrieve suggestions"}), 500

if __name__ == "__main__":
    app.run(debug=True)