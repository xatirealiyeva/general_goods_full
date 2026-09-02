import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import NavBar from "./components/NavBar.jsx";
import RequireAuth from "./components/RequireAuth.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Products from "./pages/Products.jsx";
import Cart from "./pages/Cart.jsx";
import Orders from "./pages/Orders.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Wishlist from "./pages/Wishlist.jsx";
import ProductDetail from "./pages/ProductDetail.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import SellerDashboard from "./pages/SellerDashboard.jsx";
import Tracking from "./pages/Tracking.jsx";
import CustomerDashboard from "./pages/CustomerDashboard.jsx";
import StorePage from "./pages/StorePage.jsx";

export default function App() {
  return (
    <>
      <NavBar />
      <Routes>
        <Route path="/" element={<Navigate to="/products" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/products" element={<Products />} />
        <Route path="/products/:id" element={<RequireAuth><ProductDetail /></RequireAuth>} />
        <Route path="/stores/:id" element={<StorePage />} />
        <Route path="/cart" element={<RequireAuth><Cart /></RequireAuth>} />
        <Route path="/orders" element={<RequireAuth><Orders /></RequireAuth>} />
        <Route path="/dashboard" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth role="ADMIN"><AdminDashboard /></RequireAuth>} />
        <Route path="/seller" element={<RequireAuth role="SELLER"><SellerDashboard /></RequireAuth>} />
        <Route path="/tracking" element={<RequireAuth role="CUSTOMER"><Tracking /></RequireAuth>} />
        <Route path="/wishlist" element={<RequireAuth><Wishlist /></RequireAuth>} />
        <Route path="/customer" element={<RequireAuth role="CUSTOMER" mode="CUSTOMER"><CustomerDashboard /></RequireAuth>} />
      </Routes>
    </>
  );
}
