import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import client from "../api/client.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("auth_user");
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      localStorage.removeItem("auth_user");
      return null;
    }
  });
  const [mode, setMode] = useState(() => localStorage.getItem("shop_mode") || "BUYER");
  const [hasSellerAccess, setHasSellerAccess] = useState(() => Boolean(user?.has_seller_access));

  const login = useCallback(async (email, password) => {
    const { data } = await client.post("/auth/login/", { email, password });
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    const authUser = { email: data.email, role: data.role, account_status: data.account_status, has_seller_access: data.has_seller_access === true };
    localStorage.setItem("auth_user", JSON.stringify(authUser));
    setUser(authUser);
    const canSell = authUser.has_seller_access;
    setHasSellerAccess(canSell);
    const nextMode = authUser.role === "CUSTOMER" ? (canSell ? (localStorage.getItem("shop_mode") || "CUSTOMER") : "BUYER") : authUser.role;
    localStorage.setItem("shop_mode", nextMode);
    setMode(nextMode);
    return authUser;
  }, []);

  const registerCustomer = useCallback(async (payload) => {
    // Both buyer and seller journeys share the existing Customer identity.
    // Seller capability is activated safely by creating a store afterwards.
    const { account_type, ...registration } = payload;
    await client.post("/customers/register/", { ...registration, seller_access: account_type === "SELLER" });
    localStorage.setItem("shop_mode", account_type === "SELLER" ? "CUSTOMER" : "BUYER");
    return login(registration.email, registration.password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth_user");
    setUser(null);
    setHasSellerAccess(false);
    localStorage.removeItem("shop_mode");
  }, []);

  useEffect(() => {
    window.addEventListener("shop-auth-expired", logout);
    return () => window.removeEventListener("shop-auth-expired", logout);
  }, [logout]);

  return (
    <AuthContext.Provider value={{ user, mode, hasSellerAccess, setMode: (nextMode) => { const allowedMode = nextMode === "CUSTOMER" && !hasSellerAccess ? "BUYER" : nextMode; localStorage.setItem("shop_mode", allowedMode); setMode(allowedMode); }, login, registerCustomer, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
