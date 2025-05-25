// firebase-config.js

// Your Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBXhgaji6rKcBcLmATDQ-uBBOkFjPXL0EY",
  authDomain: "mental-health-support-ch-bf5a2.firebaseapp.com",
  projectId: "mental-health-support-ch-bf5a2",
  storageBucket: "mental-health-support-ch-bf5a2.appspot.com",
  messagingSenderId: "430981111988",
  appId: "1:430981111988:web:7f0b65bf69b47a05c377e1",
  measurementId: "G-Q8JZXMJ04W"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// You can now use `auth` in other scripts loaded AFTER this
