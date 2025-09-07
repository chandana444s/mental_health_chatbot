// Function to get the current time in HH:MM format
function getCurrentTime() {
  const now = new Date();
  return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

// Restore chat history from Firestore on page load
window.addEventListener("load", () => {
  const chatBox = document.querySelector("#chat-box");
  chatBox.innerHTML = "";

  firebase.auth().onAuthStateChanged(function (user) {
    if (user) {
      user.getIdToken(true).then(function (idToken) { // Force refresh token
        fetch("http://127.0.0.1:5000/chat_history", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${idToken}`,
          },
        })
          .then(async (response) => {
            if (!response.ok) {
              if (response.status === 401 || response.status === 403) {
                alert("⚠️ Session expired. Please log in again.");
                firebase.auth().signOut();
                window.location.href = "/login";
              }
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
      });
    } else {
      console.log("No user logged in");
    }
  });
});

// Handle user input and bot response
document.querySelector("#chat-form").addEventListener("submit", function (e) {
  e.preventDefault();

  const input = document.querySelector("#user-input");
  const message = input.value.trim();
  if (!message) return;

  firebase.auth().onAuthStateChanged(async function (user) {
    if (!user) {
      alert("⚠️ Please log in to chat.");
      return;
    }

    try {
      const idToken = await user.getIdToken(true); // Force refresh token

      const chatBox = document.querySelector("#chat-box");
      const timestamp = getCurrentTime();

      chatBox.innerHTML += `<div class="user-msg">🧑‍💬 ${message} <span class="timestamp">${timestamp}</span></div>`;
      chatBox.innerHTML += `<div class="bot-msg typing" id="typing">🤖 Typing...</div>`;
      chatBox.scrollTop = chatBox.scrollHeight;

      const res = await fetch("/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      document.getElementById("typing").remove();

      const botTimestamp = getCurrentTime();

      if (res.status === 401 || res.status === 403) {
        alert("⚠️ Invalid or expired token. Please log in again.");
        firebase.auth().signOut();
        window.location.href = "/login";
        return;
      }

      if (data.reply) {
        chatBox.innerHTML += `<div class="bot-msg">🤖 <strong>Cinnamon Bot:</strong> ${data.reply} <span class="timestamp">${botTimestamp}</span></div>`;
      } else {
        chatBox.innerHTML += `<div class="bot-msg error">⚠️ ${data.error || "No response"} <span class="timestamp">${botTimestamp}</span></div>`;
      }
    } catch (error) {
      console.error("Chat error:", error);
      const typingElem = document.querySelector("#typing");
      if (typingElem) typingElem.remove();

      chatBox.innerHTML += `<div class="bot-msg error">❌ Internal error occurred. <span class="timestamp">${getCurrentTime()}</span></div>`;
    }
  });
});
