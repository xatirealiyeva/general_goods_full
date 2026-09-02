import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client.js";

export default function Wishlist() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [removingId, setRemovingId] = useState(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await client.get("/customers/wishlist/");
      const result = data?.results || data;
      setItems(Array.isArray(result) ? result : []);
    } catch (requestError) {
      setItems([]);
      setError(apiErrorMessage(requestError, "Could not load your wishlist."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const productFor = (item) => {
    if (item?.product && typeof item.product === "object") return item.product;
    if (item?.product_data && typeof item.product_data === "object") return item.product_data;
    return null;
  };

  const productIdFor = (item, product) => product?.id || item?.product_id || (typeof item?.product === "string" ? item.product : null);

  const openProduct = (item) => {
    const product = productFor(item);
    const productId = productIdFor(item, product);
    if (!productId) {
      setError("This saved product is no longer available.");
      return;
    }
    navigate(`/products/${productId}`);
  };

  const remove = async (event, item) => {
    event.stopPropagation();
    const product = productFor(item);
    const productId = productIdFor(item, product);
    if (!productId) {
      setItems((current) => current.filter((entry) => entry?.id !== item?.id));
      return;
    }
    setRemovingId(item.id);
    setError("");
    try {
      await client.delete(`/customers/wishlist/${productId}/`);
      setItems((current) => current.filter((entry) => entry?.id !== item.id));
    } catch (requestError) {
      setError(apiErrorMessage(requestError, "Could not remove this saved product."));
    } finally {
      setRemovingId(null);
    }
  };

  return <div className="container">
    <span className="eyebrow">Saved items</span>
    <h2>Wishlist</h2>
    {error && <p className="error">{error}</p>}
    {loading ? <p>Loading saved items…</p> : items.length ? <div className="grid">{items.map((item, index) => {
      const product = productFor(item);
      const productId = productIdFor(item, product);
      const available = Boolean(productId);
      return <div className={`card${available ? " catalog-product-card" : ""}`} key={item?.id || productId || `unavailable-${index}`} role={available ? "link" : undefined} tabIndex={available ? 0 : undefined} onClick={available ? () => openProduct(item) : undefined} onKeyDown={available ? (event) => { if (event.key === "Enter" || event.key === " ") openProduct(item); } : undefined}>
        <span className="category-label">{product?.category_name || "Saved product"}</span>
        <h3>{product?.name || "Product no longer available"}</h3>
        {product?.min_price != null && <p className="price">${product.min_price}</p>}
        {product?.store_name && <p style={{ margin: "7px 0 0", fontSize: "0.8rem" }}>Store: {product.store_name}</p>}
        {available ? <p style={{ margin: "10px 0 0", color: "var(--blue)", fontSize: ".8rem", fontWeight: 700 }}>View product details →</p> : <p style={{ margin: "10px 0 0", color: "var(--muted)", fontSize: ".8rem" }}>This listing may have been removed.</p>}
        <button className="secondary" disabled={removingId === item?.id} onClick={(event) => remove(event, item)}>{removingId === item?.id ? "Removing…" : "Remove"}</button>
      </div>;
    })}</div> : <p>Your wishlist is empty.</p>}
  </div>;
}
