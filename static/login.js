// DO NOT import or initialize Firebase here again
// Just use the `auth` object declared globally in firebase-config.js

document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.getElementById("login-form");
  
  if (!loginForm) return;

  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    try {
      const userCredential = await auth.signInWithEmailAndPassword(email, password);
      console.log("Logged in:", userCredential.user.email);
      window.location.href = "/";
    } catch (error) {
      alert("Login error: " + error.message);
    }
  });
});
