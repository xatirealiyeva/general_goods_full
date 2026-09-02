import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { apiErrorMessage } from "../api/client.js";

export default function Register() {
  const { registerCustomer } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({
    email: "", password: "", first_name: "", last_name: "", phone_number: "", account_type: "BUYER",
  });
  const [error, setError] = useState("");

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await registerCustomer(form);
      navigate(location.state?.from?.pathname || (form.account_type === "SELLER" ? "/customer" : "/products"), { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "Registration failed."));
    }
  };

  return (
    <div className="container">
      <span className="eyebrow">New here</span>
      <h2>Create an account</h2>
      {error && <div className="error">{error}</div>}
      <form onSubmit={submit}>
        <label>Register as</label>
        <select value={form.account_type} onChange={update("account_type")}>
          <option value="BUYER">Buyer</option>
          <option value="SELLER">Customer / Seller</option>
        </select>
        <label>First name</label>
        <input value={form.first_name} onChange={update("first_name")} required />
        <label>Last name</label>
        <input value={form.last_name} onChange={update("last_name")} required />
        <label>Email</label>
        <input value={form.email} onChange={update("email")} type="email" required />
        <label>Password</label>
        <input value={form.password} onChange={update("password")} type="password" minLength={8} required />
        <label>Phone number</label>
        <input value={form.phone_number} onChange={update("phone_number")} />
        <p style={{ fontSize: ".82rem", color: "var(--muted)" }}>{form.account_type === "SELLER" ? "You can create your store after registration, and can also shop and review." : "You can shop, purchase, manage your account, and review eligible purchases."}</p>
        <button type="submit">Create account</button>
      </form>
    </div>
  );
}
