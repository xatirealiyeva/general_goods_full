import React, { useEffect, useState } from "react";
import client from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Dashboard() {
  const { user } = useAuth(); const [data, setData] = useState(null); const [error, setError] = useState("");
  useEffect(() => { const url = user?.role === "SELLER" ? "/orders/seller/analytics/" : "/inventory/low-stock/"; client.get(url).then(r => setData(r.data)).catch(() => setError("Dashboard data could not be loaded.")); }, [user]);
  const money = value => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(value || 0));
  const sellerSummary = user?.role === "SELLER" && data && <section style={{ marginTop: 22 }}><h3>Sales Summary</h3><div className="grid"><article className="card"><span>Orders</span><p className="price">{data.orders ?? 0}</p></article><article className="card"><span>Customers</span><p className="price">{data.customers ?? 0}</p></article><article className="card"><span>Revenue</span><p className="price">{money(data.revenue)}</p></article></div></section>;
  return <div className="container"><span className="eyebrow">{user?.role} dashboard</span><h2>{user?.role === "SELLER" ? "Seller dashboard" : "Store administration"}</h2>{error && <p className="error">{error}</p>}{sellerSummary}{user?.role !== "SELLER" && data && <pre className="card">{JSON.stringify(data, null, 2)}</pre>}<p>Use Orders to manage order status and refunds. Sellers can manage listings and create shipments through the API-backed order queue.</p></div>;
}
