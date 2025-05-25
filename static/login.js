// DO NOT import or initialize Firebase here again
// Just use the `auth` object declared globally in firebase-config.js

document.addEventListener('DOMContentLoaded', function () {
  const loginForm = document.getElementById("login-form");
  
  if (!loginForm) {
    console.warn("Login form not found on this page.");
    return;
  }

  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    auth.signInWithEmailAndPassword(email, password)
      .then((userCredential) => {
        console.log("Logged in:", userCredential.user.email);
        window.location.href = "/";
      })
      .catch((error) => {
        alert("Login error: " + error.message);
      });
  });

  firebase.auth().onAuthStateChanged((user) => {
    if (user) {
      console.log("Already logged in:", user.email);
    }
  });
});
