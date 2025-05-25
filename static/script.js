// Function to get the current time in HH:MM format
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Restore chat history from Firestore on page load
window.addEventListener("load", () => {
  const chatBox = document.querySelector("#chat-box");
  chatBox.innerHTML = "";

  firebase.auth().onAuthStateChanged(function(user) {
    if (user) {
      user.getIdToken().then(function(idToken) {
          fetch("http://127.0.0.1:5000/chat_history", {
            method: "GET",
            headers: {
              Authorization: `Bearer ${idToken}`,
            },
          })
            .then(async (response) => {
              if (!response.ok) {
                throw new Error("Failed to fetch chat history");
              }
              const data = await response.json();
              if (data.chat_history && Array.isArray(data.chat_history)) {
                data.chat_history.forEach((msg) => {
                  const bubble = document.createElement("div");
                  const timestamp = msg.timestamp
                    ? new Date(msg.timestamp).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : getCurrentTime();

                  if (msg.role === "user") {
                    bubble.classList.add("user-msg");
                    bubble.innerHTML = `🧑‍💬 ${msg.content} <span class="timestamp">${timestamp}</span>`;
                  } else if (msg.role === "bot") {
                    bubble.classList.add("bot-msg");
                    bubble.innerHTML = `🤖 <strong>Cinnamon Bot:</strong> ${msg.content} <span class="timestamp">${timestamp}</span>`;
                  }

                  chatBox.appendChild(bubble);
                });

                localStorage.setItem("chat-history", chatBox.innerHTML);
                chatBox.scrollTop = chatBox.scrollHeight;
              } else {
                console.warn("No chat history found or user unauthorized:", data);
              }
            })
            .catch((error) => {
              console.error("Error fetching chat history:", error);
              chatBox.innerHTML += `<div class="bot-msg error">❌ Unable to fetch chat history. Please try again later. <span class="timestamp">${getCurrentTime()}</span></div>`;
            });
        })
        .catch((error) => {
          console.error("Error fetching token:", error);
        });
    } else {
      console.log("No user logged in");
    }
  });
});

// Handle user input and bot response
document.querySelector("#chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const input = document.querySelector("#user-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  input.focus();

  const chatBox = document.querySelector("#chat-box");
  const userTimestamp = getCurrentTime();

  chatBox.innerHTML += `<div class="user-msg">🧑‍💬 ${message} <span class="timestamp">${userTimestamp}</span></div>`;
  localStorage.setItem("chat-history", chatBox.innerHTML);

  chatBox.innerHTML += `<div class="bot-msg typing" id="typing">🤖 Typing...</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const user = firebase.auth().currentUser;
    if (user) {
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

      const typingElem = document.querySelector("#typing");
      if (typingElem) typingElem.remove();

      const botTimestamp = getCurrentTime();

      if (data.reply) {
        chatBox.innerHTML += `<div class="bot-msg">🤖 <strong>Cinnamon Bot:</strong> ${data.reply} <span class="timestamp">${botTimestamp}</span></div>`;
      } else if (data.error) {
        chatBox.innerHTML += `<div class="bot-msg error">⚠️ ${data.error} <span class="timestamp">${botTimestamp}</span></div>`;
      }
    }
  } catch (error) {
    const typingElem = document.querySelector("#typing");
    if (typingElem) typingElem.remove();

    chatBox.innerHTML += `<div class="bot-msg error">❌ Something went wrong <span class="timestamp">${getCurrentTime()}</span></div>`;
    console.error("Error:", error);
  }

  localStorage.setItem("chat-history", chatBox.innerHTML);
  chatBox.scrollTop = chatBox.scrollHeight;
});

// Toggle auth menu
function toggleMenu() {
  const authMenu = document.getElementById("authMenu");
  if (authMenu) {
    authMenu.classList.toggle("hidden");
  }
}

// Close menu if clicked outside
window.addEventListener("click", function (event) {
  const authMenu = document.getElementById("authMenu");
  if (
    !event.target.closest(".menu-button") &&
    !event.target.closest("#authMenu")
  ) {
    if (authMenu && !authMenu.classList.contains("hidden")) {
      authMenu.classList.add("hidden");
    }
  }
});

// Enable/disable send button based on input
document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const chatContainer = document.getElementById("chat-container");
  const refreshButton = document.getElementById("refreshButton");

  // Enable or disable send button based on input
  sendButton.disabled = !input.value.trim();
  input.addEventListener("input", () => {
    sendButton.disabled = !input.value.trim();
  });

  input.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !input.value.trim()) {
      e.preventDefault(); // Prevent sending empty message
    }
  });

  // Fetch personalized suggestions after login
  firebase.auth().onAuthStateChanged((user) => {
  if (user) {
    fetchSelfCareSuggestions();
  } else {
    console.log("No user logged in for suggestions.");
  }
});

  // Send user message
  sendButton.addEventListener("click", async () => {
    const message = input.value.trim();
    if (!message) return;

    appendMessage("You", message, "user");
    input.value = "";
    sendButton.disabled = true;

    // Show typing indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.className = "message bot loading";
    typingIndicator.innerText = "Aurora is typing...";
    chatContainer.appendChild(typingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    const user = firebase.auth().currentUser;
    if (!user) {
      alert("User not authenticated.");
      typingIndicator.remove();
      return;
    }

    try {
      const idToken = await user.getIdToken();
      const response = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + idToken,
        },
        body: JSON.stringify({ message }),
      });

      typingIndicator.remove();

      const data = await response.json();
      if (response.ok) {
        appendMessage("Aurora", data.response, "bot");
      } else {
        appendMessage("Aurora", "Sorry, something went wrong. 😢", "bot");
      }
    } catch (error) {
      typingIndicator.remove();
      console.error("Error:", error);
      appendMessage("Aurora", "An error occurred while sending your message.", "bot");
    }
  });

  // Delete chat history
  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      const confirmation = confirm("Are you sure you want to delete your chat history?");
      if (!confirmation) return;

      const user = firebase.auth().currentUser;
      if (!user) {
        alert("User not authenticated.");
        return;
      }

      try {
        const idToken = await user.getIdToken(true);
        const response = await fetch("/delete_chat_history", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + idToken,
          },
        });

        const data = await response.json();
        if (response.ok && data.success) {
          alert("✅ Chat history deleted successfully.");
          location.reload();
        } else {
          alert("❌ Deletion failed: " + (data.message || "Unauthorized or server error"));
        }
      } catch (err) {
        console.error("❌ Exception during delete:", err);
        alert("An unexpected error occurred.");
      }
    });
  }

  // Helper: Append message to chat container
  function appendMessage(sender, message, type) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${type}`;
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    messageDiv.innerHTML = `
      <div class="message-sender">${sender}</div>
      <div class="message-text">${message}</div>
      <div class="timestamp">${timestamp}</div>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // Helper: Fetch self-care suggestions
  async function fetchSelfCareSuggestions() {
    const user = firebase.auth().currentUser;
    if (!user) {
      console.log("User not authenticated for suggestions.");
      return;
    }

    try {
      const idToken = await user.getIdToken();
      const response = await fetch("/self_care_suggestions", {
        method: "GET",
        headers: {
          Authorization: "Bearer " + idToken,
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data && data.suggestions && data.suggestions.length > 0) {
          const suggestions = data.suggestions.join(", ");
          appendMessage("Cinnamon Bot", `🌿 Here are some personalized self-care suggestions: ${suggestions}`, "bot");
        }
      } else {
        console.error("Failed to fetch suggestions.");
      }
    } catch (error) {
      console.error("Suggestion fetch error:", error);
    }
  }
});
