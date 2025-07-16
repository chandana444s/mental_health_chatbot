// Get current time in HH:MM format
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Append a message to chat box
function appendMessage(sender, message, type) {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;

  const messageDiv = document.createElement("div");
  messageDiv.className = type === "user" ? "user-msg" : "bot-msg";

  messageDiv.innerHTML = `<p><strong>${sender}:</strong> ${message} <span class="timestamp">${getCurrentTime()}</span></p>`;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  // Save to localStorage
  localStorage.setItem("chat-history", chatBox.innerHTML);
}

// Restore chat history on page load from backend
window.addEventListener("load", () => {
  const chatBox = document.getElementById("chat-box");
  if (!chatBox) return;

  chatBox.innerHTML = ""; // Clear chat box

  firebase.auth().onAuthStateChanged(async (user) => {
    if (!user) {
      console.log("No user logged in");
      return;
    }

    try {
      const idToken = await user.getIdToken();
      const response = await fetch("http://127.0.0.1:5000/chat_history", {
        method: "GET",
        headers: { Authorization: `Bearer ${idToken}` },
      });

      if (!response.ok) throw new Error("Failed to fetch chat history");

      const data = await response.json();

      if (data.chat_history && Array.isArray(data.chat_history)) {
        data.chat_history.forEach((msg) => {
          const timestamp = msg.timestamp
            ? new Date(msg.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
            : getCurrentTime();

          if (msg.role === "user") {
            chatBox.innerHTML += `<div class="user-msg">🧑‍💬 ${msg.content} <span class="timestamp">${timestamp}</span></div>`;
          } else if (msg.role === "bot") {
            chatBox.innerHTML += `<div class="bot-msg">🤖 <strong>Cinnamon Bot:</strong> ${msg.content} <span class="timestamp">${timestamp}</span></div>`;
          }
        });

        chatBox.scrollTop = chatBox.scrollHeight;
        localStorage.setItem("chat-history", chatBox.innerHTML);
      } else {
        console.warn("No chat history found or unauthorized");
      }
    } catch (err) {
      console.error("Error fetching chat history:", err);
      chatBox.innerHTML += `<div class="bot-msg error">❌ Unable to fetch chat history. Please try again later. <span class="timestamp">${getCurrentTime()}</span></div>`;
    }
  });
});

// Handle chat form submit (user sends message)
document.querySelector("#chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  input.focus();

  const chatBox = document.getElementById("chat-box");

  appendMessage("You", message, "user");

  // Show typing indicator
  const typingDiv = document.createElement("div");
  typingDiv.className = "bot-msg typing";
  typingDiv.id = "typing";
  typingDiv.innerHTML = "🤖 Typing...";
  chatBox.appendChild(typingDiv);
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const user = firebase.auth().currentUser;
    if (!user) {
      alert("User not authenticated");
      typingDiv.remove();
      return;
    }

    const idToken = await user.getIdToken(true);
    const res = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${idToken}`,
      },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();

    typingDiv.remove();

    if (data.reply) {
      appendMessage("Cinnamon Bot", data.reply, "bot");
    } else if (data.error) {
      appendMessage("Cinnamon Bot", `⚠️ ${data.error}`, "bot");
    }
  } catch (error) {
    console.error("Error sending message:", error);
    typingDiv.remove();
    appendMessage("Cinnamon Bot", "❌ Something went wrong. Please try again.", "bot");
  }
});

// Toggle auth menu visibility
function toggleMenu() {
  const authMenu = document.getElementById("authMenu");
  if (authMenu) {
    authMenu.classList.toggle("hidden");
  }
}

// Close auth menu if clicking outside
window.addEventListener("click", (event) => {
  const authMenu = document.getElementById("authMenu");
  if (
    !event.target.closest(".menu-button") &&
    !event.target.closest("#authMenu") &&
    authMenu &&
    !authMenu.classList.contains("hidden")
  ) {
    authMenu.classList.add("hidden");
  }
});

// Enable/disable send button based on input and set up chat features
document.addEventListener("DOMContentLoaded", () => {
  const deleteBtn = document.getElementById('delete-history-btn');
  if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
      const user = firebase.auth().currentUser;
      if (user) {
        user.getIdToken().then(token => {
          fetch('/delete_chat_history', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': 'Bearer ' + token
            },
            body: JSON.stringify({ uid: user.uid }) // Optional
          })
          .then(response => {
            if (response.ok) {
              alert('Chat history deleted successfully.');
            } else {
              return response.json().then(data => {
                throw new Error(data.error || 'Delete failed.');
              });
            }
          })
          .catch(error => {
            console.error('Error:', error);
            alert('Error deleting chat history: ' + error.message);
          });
        });
      } else {
        alert('You must be logged in to delete your chat history.');
      }
    });
  }
});

