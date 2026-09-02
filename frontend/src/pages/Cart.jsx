import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client.js";
import PayPalButtons from "../components/PayPalButtons.jsx";

const money = (value) => Number(value || 0).toFixed(2);

export default function Cart() {
  const [cart, setCart] = useState(null);
  const [selected, setSelected] = useState([]);
  const [address, setAddress] = useState("");
  const [discountCode, setDiscountCode] = useState("");
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState("");
  const [discountMessage, setDiscountMessage] = useState("");
  const [applyingDiscount, setApplyingDiscount] = useState(false);
  const [pendingOrder, setPendingOrder] = useState(null);
  const [paying, setPaying] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    try {
      const { data } = await client.get("/cart/");
      setCart(data);
      setSelected((current) => current.filter((id) => data.items.some((item) => item.id === id)));
    } catch (err) { setError(apiErrorMessage(err, "Could not load your cart.")); }
  };

  useEffect(() => { void load(); }, []);

  const selectedItems = useMemo(() => cart?.items.filter((item) => selected.includes(item.id)) || [], [cart, selected]);
  const allSelected = !!cart?.items.length && selected.length === cart.items.length;
  const selectedSubtotal = useMemo(() => selectedItems.reduce((total, item) => total + Number(item.line_total), 0), [selectedItems]);

  const toggleItem = (itemId) => {
    setQuote(null); setDiscountMessage("");
    setSelected((current) => current.includes(itemId) ? current.filter((id) => id !== itemId) : [...current, itemId]);
  };
  const toggleAll = () => {
    setQuote(null); setDiscountMessage("");
    setSelected(allSelected ? [] : cart.items.map((item) => item.id));
  };
  const updateQty = async (itemId, quantity) => {
    if (!Number.isInteger(quantity) || quantity < 1) return;
    setError(""); setQuote(null); setDiscountMessage("");
    try { await client.patch(`/cart/items/${itemId}/`, { quantity }); await load(); }
    catch (err) { setError(apiErrorMessage(err, "Could not update quantity.")); }
  };
  const removeItem = async (itemId) => {
    setError(""); setQuote(null); setDiscountMessage("");
    try { await client.delete(`/cart/items/${itemId}/`); await load(); }
    catch (err) { setError(apiErrorMessage(err, "Could not remove this item.")); }
  };
  const applyDiscount = async () => {
    if (!selected.length) { setError("Please select at least one product."); return; }
    const code = discountCode.trim();
    if (!code) { setQuote(null); setDiscountMessage(""); setError("Enter a discount code to apply it."); return; }
    setError("");
    setDiscountMessage("");
    setApplyingDiscount(true);
    try {
      const { data } = await client.post("/orders/checkout/preview/", { cart_item_ids: selected, discount_code: code });
      if (!data || String(data.discount_code || "").toLowerCase() !== code.toLowerCase() || !Number.isFinite(Number(data.discount_amount)) || !Number.isFinite(Number(data.total))) {
        throw new Error("The checkout preview returned an invalid discount quote.");
      }
      setQuote(data);
      setDiscountMessage(`Code ${data.discount_code} applied: -$${money(data.discount_amount)}.`);
    } catch (err) { setQuote(null); setError(apiErrorMessage(err, "Could not apply the discount code.")); }
    finally { setApplyingDiscount(false); }
  };
  const checkout = async () => {
    if (!selected.length) { setError("Please select at least one product."); return; }
    setError("");
    try {
      const { data: order } = await client.post("/orders/checkout/", { shipping_address: address, cart_item_ids: selected, discount_code: discountCode });
      setPendingOrder(order);
      await load();
    } catch (err) { setError(apiErrorMessage(err, "Checkout failed.")); }
  };
  const handlePaymentApproved = async (details) => {
    setPaying(true); setError("");
    try {
      await client.post("/payments/", { order: pendingOrder.id, provider: "PAYPAL", provider_reference: details.id });
      navigate("/orders", { state: { justPlaced: pendingOrder.order_number } });
    } catch (err) { setError(apiErrorMessage(err, "Payment could not be recorded.")); }
    finally { setPaying(false); }
  };

  if (!cart) return <div className="container"><p style={{ opacity: 0.7 }}>Loading your cart…</p></div>;
  if (pendingOrder) return <div className="container"><span className="eyebrow">Checkout</span><h2>Pay for order {pendingOrder.order_number}</h2>{error && <div className="error">{error}</div>}<div className="card" style={{ maxWidth: 380, marginTop: 18 }}><h3>Total due</h3><p className="price" style={{ fontSize: "1.6rem" }}>${pendingOrder.total}</p><div className="tear" />{paying ? <p style={{ opacity: 0.7 }}>Recording your payment…</p> : <PayPalButtons amount={pendingOrder.total} onApproved={handlePaymentApproved} onError={() => setError("PayPal checkout failed. Please try again.")} />}</div></div>;

  const shownQuote = quote || { subtotal: selectedSubtotal, discount_amount: 0, total: selectedSubtotal, discount_code: null };
  return <div className="container"><span className="eyebrow">Cart</span><h2>Your basket</h2>{error && <div className="error">{error}</div>}{!cart.items.length ? <p style={{ opacity: 0.75, marginTop: 16 }}>Your basket is empty — browse the catalog to add something.</p> : <><p><label><input type="checkbox" checked={allSelected} onChange={toggleAll} /> {allSelected ? "Deselect all" : "Select all"}</label></p><table style={{ marginTop: 18 }}><thead><tr><th>Select</th><th>Item</th><th>Unit</th><th>Qty</th><th>Line total</th><th /></tr></thead><tbody>{cart.items.map((item) => <tr key={item.id}><td><input aria-label={`Select ${item.product_name}`} type="checkbox" checked={selected.includes(item.id)} onChange={() => toggleItem(item.id)} /></td><td>{item.product_name}<br /><small>{item.sku}</small></td><td className="price" style={{ fontSize: "0.95rem" }}>${item.unit_price}</td><td><input type="number" min={1} value={item.quantity} style={{ width: 66, marginBottom: 0 }} onChange={(e) => updateQty(item.id, Number(e.target.value))} /></td><td className="price" style={{ fontSize: "0.95rem" }}>${item.line_total}</td><td><button className="secondary" onClick={() => removeItem(item.id)}>Remove</button></td></tr>)}</tbody></table><div className="card" style={{ maxWidth: 480, marginTop: 24 }}><h3>Selected checkout total</h3><label>Discount code<input value={discountCode} onChange={(e) => { setDiscountCode(e.target.value); setQuote(null); setDiscountMessage(""); }} placeholder="Enter discount code" /></label><button type="button" className="secondary" disabled={!selected.length || applyingDiscount} onClick={applyDiscount}>{applyingDiscount ? "Applying…" : "Apply"}</button>{discountMessage && <p role="status" style={{ color: "#166534" }}>{discountMessage}</p>}<p>Subtotal <span className="price" style={{ float: "right" }}>${money(shownQuote.subtotal)}</span></p><p>Discount <span className="price" style={{ float: "right" }}>-${money(shownQuote.discount_amount)}</span></p><h3>Total <span className="price" style={{ float: "right" }}>${money(shownQuote.total)}</span></h3>{shownQuote.discount_code && <small>Applied code: {shownQuote.discount_code}</small>}</div><form onSubmit={(e) => { e.preventDefault(); checkout(); }} style={{ marginTop: 12 }}><label>Shipping address<textarea value={address} onChange={(e) => setAddress(e.target.value)} rows={3} required /></label><button type="submit" disabled={!address || !selected.length}>Continue to payment</button></form></>}</div>;
}
