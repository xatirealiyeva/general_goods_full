import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client.js";

export default function StorePage() {
  const { id } = useParams(); const [data, setData] = useState(null); const [error, setError] = useState("");
  useEffect(() => { client.get(`/customers/stores/${id}/`).then((response) => setData(response.data)).catch((err) => setError(apiErrorMessage(err, "Store not found."))); }, [id]);
  if (error) return <div className="container"><h2>Store unavailable</h2><p className="error">{error}</p></div>;
  if (!data) return <div className="container"><p>Loading store…</p></div>;
  return <div className="container"><span className="eyebrow">Store</span><h2>{data.store.name}</h2><p>{data.store.description || "No store description provided."}</p><h3 style={{ marginTop: 24 }}>Store products</h3>{data.products.length ? <div className="grid">{data.products.map((product) => <div className="card" key={product.id}><h3><Link to={`/products/${product.id}`}>{product.name}</Link></h3><p className="price">${product.min_price}</p><p>Rating: {product.rating ?? "—"}</p></div>)}</div> : <p>No products in this store yet.</p>}</div>;
}
