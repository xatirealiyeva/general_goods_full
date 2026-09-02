import React, { useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiErrorMessage } from "../api/client.js";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("customer-demo@example.com");
  const [password, setPassword] = useState("CustomerPass123!");
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const authUser = await login(email, password);
      const destination = location.state?.from?.pathname;
      navigate(destination || (authUser.role === "CUSTOMER" ? (localStorage.getItem("shop_mode") === "BUYER" ? "/products" : "/customer") : authUser.role === "ADMIN" ? "/admin" : "/seller"), { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Invalid email or password."));
    }
  };

  return (
    <div className="container">
      <span className="eyebrow">Welcome back</span>
      <h2>Log in</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={submit}>
        <label>Email</label>
        <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        <label>Password</label>
        <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        <button type="submit">Log in</button>
      </form>
      <p>No account? <Link to="/register" state={location.state}>Register as a buyer or customer / seller</Link></p>
      <p style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem", opacity: 0.55 }}>
        demo: seller-demo@example.com / SellerPass123!<br />
        demo: customer-demo@example.com / CustomerPass123!
      </p>
    </div>
  );
}
