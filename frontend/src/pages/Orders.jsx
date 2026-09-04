import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import PayPalButtons from "../components/PayPalButtons.jsx";

export default function Orders() {
  const { user } = useAuth();
  const location = useLocation();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [payingOrderId, setPayingOrderId] = useState(null);
  const [refundOrderId, setRefundOrderId] = useState(null);
  const [refundReason, setRefundReason] = useState("");
  const [submittingRefund, setSubmittingRefund] = useState(false);
  const [refundMessage, setRefundMessage] = useState("");
  const [refundRequestedOrderIds, setRefundRequestedOrderIds] = useState(() => new Set());
  const [error, setError] = useState("");

  const endpoint = user?.role === "SELLER" ? "/orders/seller/"
    : user?.role === "ADMIN" ? "/orders/admin/"
    : "/orders/mine/";

  const load = () => {
    client.get(endpoint).then(({ data }) => setOrders(data.results || data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [user]);

  const handlePaymentApproved = async (order, details) => {
    setError("");
    try {
      await client.post("/payments/", { order: order.id, provider: "PAYPAL", provider_reference: details.id });
      setPayingOrderId(null);
      load();
    } catch (err) {
      setError(apiErrorMessage(err, "Payment could not be recorded."));
    }
  };

  const openRefundRequest = (orderId) => {
    setError("");
    setRefundMessage("");
    setRefundReason("");
    setRefundOrderId(refundOrderId === orderId ? null : orderId);
  };

  const submitRefundRequest = async (event, order) => {
    event.preventDefault();
    const reason = refundReason.trim();
    if (!reason) {
      setError("Please enter a reason for the refund request.");
      return;
    }

    setError("");
    setRefundMessage("");
    setSubmittingRefund(true);
    try {
      const response = await client.post("/orders/refund-requests/", { order: order.id, reason });
      setRefundOrderId(null);
      setRefundReason("");
      setRefundRequestedOrderIds((current) => new Set(current).add(order.id));
      setRefundMessage(
        response.status === 201
          ? "Refund request submitted. An administrator will review it."
          : "A refund request for this order has already been submitted."
      );
    } catch (err) {
      setError(apiErrorMessage(err, "Refund request could not be submitted."));
    } finally {
      setSubmittingRefund(false);
    }
  };

  const heading = user?.role === "SELLER" ? "Order queue" : user?.role === "ADMIN" ? "All orders" : "Order history";

  return (
    <div className="container">
      <span className="eyebrow">Orders</span>
      <h2>{heading}</h2>
      {location.state?.justPlaced && (
        <p className="badge" style={{ marginBottom: 14 }}>Order {location.state.justPlaced} placed successfully</p>
      )}
      {refundMessage && <p className="badge" style={{ marginBottom: 14 }}>{refundMessage}</p>}
      {error && <div className="error">{error}</div>}
      {loading ? (
        <p style={{ opacity: 0.7, marginTop: 16 }}>Pulling the ledger…</p>
      ) : orders.length === 0 ? (
        <p style={{ opacity: 0.75, marginTop: 16 }}>No orders on record yet.</p>
      ) : (
        <table style={{ marginTop: 18 }}>
          <thead><tr><th>Order #</th><th>Status</th><th>Total</th><th>Items</th><th>Placed</th>{user?.role === "CUSTOMER" && <th></th>}</tr></thead>
          <tbody>
            {orders.map((o) => (
              <React.Fragment key={o.id}>
                <tr>
                  <td><small>{o.order_number}</small></td>
                  <td><span className="badge">{o.status}</span></td>
                  <td className="price" style={{ fontSize: "0.95rem" }}>${o.total}</td>
                  <td>{o.items.map((i) => `${i.product_name} ×${i.quantity}`).join(", ")}</td>
                  <td><small>{new Date(o.created_at).toLocaleString()}</small></td>
                  {user?.role === "CUSTOMER" && (
                    <td>
                      {o.status === "PENDING" && (
                        <button
                          className="secondary"
                          onClick={() => setPayingOrderId(payingOrderId === o.id ? null : o.id)}
                        >
                          {payingOrderId === o.id ? "Cancel" : "Pay now"}
                        </button>
                      )}
                      {o.status === "DELIVERED" && !refundRequestedOrderIds.has(o.id) && (
                        <button className="secondary" disabled={submittingRefund} onClick={() => openRefundRequest(o.id)}>
                          {refundOrderId === o.id ? "Cancel" : "Request refund"}
                        </button>
                      )}
                    </td>
                  )}
                </tr>
                {payingOrderId === o.id && (
                  <tr>
                    <td colSpan={6} style={{ background: "var(--paper-dim)" }}>
                      <div style={{ maxWidth: 320, padding: "10px 0" }}>
                        <PayPalButtons
                          amount={o.total}
                          onApproved={(details) => handlePaymentApproved(o, details)}
                          onError={() => setError("PayPal checkout failed. Please try again.")}
                        />
                      </div>
                    </td>
                  </tr>
                )}
                {refundOrderId === o.id && (
                  <tr>
                    <td colSpan={6} style={{ background: "var(--paper-dim)" }}>
                      <form onSubmit={(event) => submitRefundRequest(event, o)} style={{ maxWidth: 520, padding: "16px" }}>
                        <label htmlFor={`refund-reason-${o.id}`}>Why would you like a refund?</label>
                        <textarea
                          id={`refund-reason-${o.id}`}
                          value={refundReason}
                          onChange={(event) => setRefundReason(event.target.value)}
                          placeholder="Describe the reason for your request"
                          required
                          disabled={submittingRefund}
                        />
                        <button disabled={submittingRefund}>
                          {submittingRefund ? "Submitting…" : "Submit refund request"}
                        </button>
                      </form>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
