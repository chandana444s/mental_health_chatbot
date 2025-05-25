document.getElementById("register-form").addEventListener("submit", async function (e) {
    e.preventDefault(); // prevent page reload
  
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    try {
      // Create user with Firebase Auth
      const userCredential = await firebase.auth().createUserWithEmailAndPassword(email, password);
      const user = userCredential.user;
      console.log("User created:", user.uid);
  
      // Save user data in Firestore
      const db = firebase.firestore();
      await db.collection("users").doc(user.uid).set({
        name: name,
        email: email,
        created_at: firebase.firestore.FieldValue.serverTimestamp()
      });
  
      // Optional: also send data to Flask backend
      await fetch("/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          name: name
        })
      });
  
      // Redirect to chatbot or homepage
      window.location.href = "/";
    } catch (error) {
      console.error("Registration Error:", error);
      alert("Error: " + error.message);
    }
  });
  