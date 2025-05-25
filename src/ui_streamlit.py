import streamlit as st
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from chatbot import generate_response

st.set_page_config(page_title="Mental Health Chatbot")
st.title("🧠 Mental Health Support Chatbot")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat form input
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", placeholder="How are you feeling today?")
    submitted = st.form_submit_button("Send")

# Handle submission
if submitted and user_input:
    with st.spinner("Generating response..."):
        response = generate_response(user_input)
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", response))

# ✅ Always display chat history (after processing)
for sender, msg in st.session_state.chat_history:
    if sender == "You":
        st.chat_message("user").write(msg)
    else:
        st.chat_message("assistant").write(msg)

