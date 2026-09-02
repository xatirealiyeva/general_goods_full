import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function NavBar() {
  const { user, mode, hasSellerAccess, setMode, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="navbar">
      <Link to="/products" className="brand">
        <span className="mark">✦</span> General Goods
      </Link>
      <div className="nav-links">
        {(user?.role !== "CUSTOMER" || !hasSellerAccess || mode === "BUYER") && <Link to="/products" className="nav-link">Catalog</Link>}
        {user?.role === "CUSTOMER" && hasSellerAccess && mode === "CUSTOMER" && <Link to="/customer" className="nav-link">My Store</Link>}
        {user?.role === "CUSTOMER" && mode === "BUYER" && <Link to="/cart" className="nav-link">Cart</Link>}
        {user?.role === "CUSTOMER" && mode === "BUYER" && <Link to="/wishlist" className="nav-link">Wishlist</Link>}
        {user?.role === "CUSTOMER" && mode === "BUYER" && <Link to="/tracking" className="nav-link">Tracking</Link>}
        {user && <Link to="/orders" className="nav-link">Orders</Link>}
        {(user?.role === "ADMIN" || user?.role === "SELLER") && <Link to="/dashboard" className="nav-link">Dashboard</Link>}
        {user?.role === "ADMIN" && <Link to="/admin" className="nav-link">Manage</Link>}
        {user?.role === "SELLER" && <Link to="/seller" className="nav-link">Manage</Link>}
        {user?.role === "CUSTOMER" && hasSellerAccess && <button className="secondary" onClick={() => { const next = mode === "BUYER" ? "CUSTOMER" : "BUYER"; setMode(next); navigate(next === "BUYER" ? "/products" : "/customer"); }}>{mode === "BUYER" ? "Switch to Seller Mode" : "Switch to Buyer Mode"}</button>}
        {user ? (
          <>
            <span className="role-chip">{user.role}</span>
            <button className="secondary" style={{ marginLeft: 12 }} onClick={() => { logout(); navigate("/login"); }}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-link">Log in</Link>
            <Link to="/register" className="nav-link">Register</Link>
          </>
        )}
      </div>
    </div>
  );
}
