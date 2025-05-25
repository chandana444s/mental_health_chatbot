import os
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_bcrypt import Bcrypt
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from datetime import datetime

# Function to get the current time in a friendly format
def get_current_time():
    return datetime.now().strftime("%I:%M %p")

# Function to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app = Flask(__name__, static_folder='src/static', template_folder='src/templates')
app.secret_key = "285627634022592494becd9f8d7192d3"  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# Set allowed extensions and upload folder
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'src/static/uploads/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    profile_pic = db.Column(db.String(200), nullable=True)  # For storing profile image path

# Create DB tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Chatbot model connection
llm = OllamaLLM(model="mentalhealth-llama2:latest", base_url="http://localhost:11435")

SYSTEM_PROMPT = """
You are a compassionate and supportive mental health assistant.
Your job is to talk gently and kindly to users who may be feeling down, anxious, depressed, or overwhelmed.
Always respond with empathy, encouragement, and practical suggestions (e.g., self-care, connecting with loved ones, gentle reminders).
Do NOT just list emergency hotlines unless the user is clearly in danger (e.g., mentions suicide directly).
Be gentle, thoughtful, and warm in every response.
"""

# ROUTES

@app.route("/")
@login_required
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
@login_required
def chat():
    try:
        user_input = request.json["message"]
        chat_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", user_input),
        ])

         # Get current time for the response
        current_time = get_current_time()

        response = llm.invoke(chat_template.format())

        # Combine the timestamp with the bot's response
        response_with_timestamp = f"{current_time} - {response[0]}"
        
        return jsonify({"reply": response_with_timestamp})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": f"Something went wrong: {str(e)}"})

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="User already exists.")
        
        # Hash password before storing
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        return render_template("login.html", error="Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        # Check if the form has the file part
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            # If a file is selected and it's allowed
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Save the file to the 'uploads' folder
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Update the user's profile_pic field in the database
                current_user.profile_pic = filename
                db.session.commit()
                flash("Profile picture updated successfully!", "success")
            else:
                flash("Invalid file type. Please upload an image (PNG, JPG, JPEG, GIF).", "danger")
        return render_template("profile.html", user_email=current_user.email, profile_pic=current_user.profile_pic)
    
    # For GET requests, just render the profile page with the current user details
    return render_template("profile.html", user_email=current_user.email, profile_pic=current_user.profile_pic)

# TEST ROUTES for login and register
@app.route("/test_login")
def test_login():
    return render_template("login.html")

@app.route("/test_register")
def test_register():
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)
