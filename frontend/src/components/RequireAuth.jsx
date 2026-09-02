import React from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function RequireAuth({ children, role, mode }) {
  const { user, mode: currentMode, hasSellerAccess } = useAuth();
  const location = useLocation();
  if (!user) {
    const from = { pathname: location.pathname, search: location.search, hash: location.hash };
    return <main className="container"><span className="eyebrow">Account required</span><h2>Please log in or create an account to continue.</h2><p>You will return here as soon as authentication is complete.</p><div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 20 }}><Link className="button" to="/login" state={{ from }}>Log in</Link><Link className="button secondary" to="/register" state={{ from }}>Register</Link></div></main>;
  }
  if (role && user.role !== role) return <Navigate to="/products" replace />;
  if (mode === "CUSTOMER" && !hasSellerAccess) return <Navigate to="/products" replace />;
  if (mode && currentMode !== mode) return <div className="container"><h2>Customer mode is required</h2><p>Switch to Customer mode to manage a store or create products.</p></div>;
  return children;
}
