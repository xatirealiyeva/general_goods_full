import React, { useEffect, useState } from "react";
import client, { apiErrorMessage } from "../api/client.js";

export default function SellerDashboard() {
  const [s, setS] = useState({
    products: [],
    orders: [],
    customers: [],
    analytics: null,
    shipments: [],
  });

  const [err, setErr] = useState("");

  const [shipmentForm, setShipmentForm] = useState({
    order: "",
    carrier: "",
    tracking_number: "",
    estimated_arrival: "",
  });

  const [creatingShipment, setCreatingShipment] = useState(false);

  const load = async () => {
    try {
      setErr("");

      const r = await Promise.all([
        client.get("/catalog/products/mine/"),
        client.get("/orders/seller/"),
        client.get("/orders/seller/customers/"),
        client.get("/orders/seller/analytics/"),
      ]);

      setS((previous) => ({
        ...previous,
        products: r[0].data.results || r[0].data,
        orders: r[1].data.results || r[1].data,
        customers: r[2].data.results || r[2].data,
        analytics: r[3].data,
      }));
    } catch (e) {
      setErr(apiErrorMessage(e, "Seller data could not be loaded."));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const loadShipmentsForOrders = async (orders) => {
    try {
      const results = await Promise.all(
        orders.map(async (order) => {
          try {
            const response = await client.get(
              `/shipments/order/${order.id}/`
            );

            return {
              orderId: order.id,
              shipments:
                response.data.results || response.data,
            };
          } catch {
            return {
              orderId: order.id,
              shipments: [],
            };
          }
        })
      );

      const shipments = results.flatMap((item) =>
        item.shipments.map((shipment) => ({
          ...shipment,
          orderId: item.orderId,
        }))
      );

      setS((previous) => ({
        ...previous,
        shipments,
      }));
    } catch {
      setErr("Shipments could not be loaded.");
    }
  };

  useEffect(() => {
    if (s.orders.length > 0) {
      loadShipmentsForOrders(s.orders);
    }
  }, [s.orders]);

  const handleShipmentChange = (e) => {
    const { name, value } = e.target;

    setShipmentForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const createShipment = async (e) => {
    e.preventDefault();

    if (
      !shipmentForm.order ||
      !shipmentForm.carrier ||
      !shipmentForm.tracking_number
    ) {
      setErr(
        "Order, carrier and tracking number are required."
      );
      return;
    }

    setCreatingShipment(true);
    setErr("");

    try {
      const payload = {
        order: shipmentForm.order,
        carrier: shipmentForm.carrier,
        tracking_number: shipmentForm.tracking_number,
      };

      if (shipmentForm.estimated_arrival) {
        payload.estimated_arrival =
          shipmentForm.estimated_arrival;
      }

      await client.post("/shipments/", payload);

      setShipmentForm({
        order: "",
        carrier: "",
        tracking_number: "",
        estimated_arrival: "",
      });

      await load();
    } catch (e) {
      setErr(apiErrorMessage(e, "Shipment could not be created."));
    } finally {
      setCreatingShipment(false);
    }
  };

  const updateShipmentStatus = async (
    shipmentId,
    status
  ) => {
    try {
      setErr("");

      await client.patch(
        `/shipments/${shipmentId}/status/`,
        { status }
      );

      const orders = s.orders;

      await loadShipmentsForOrders(orders);
    } catch (e) {
      setErr(apiErrorMessage(e, "Shipment status could not be updated."));
    }
  };

  const getShipmentsForOrder = (orderId) => {
    return s.shipments.filter(
      (shipment) => shipment.orderId === orderId
    );
  };

  return (
    <div className="container">
      <span className="eyebrow">
        Seller dashboard
      </span>

      <h2>Listings and fulfilment</h2>

      {err && <p className="error">{err}</p>}

      {s.analytics && (
        <p>
          Revenue: ${s.analytics.revenue} · Orders:{" "}
          {s.analytics.orders}
        </p>
      )}

      {/* =========================
          MY LISTINGS
      ========================== */}

      <h3>My listings</h3>

      {s.products.length === 0 ? (
        <p>No products found.</p>
      ) : (
        s.products.map((p) => (
          <div className="row" key={p.id}>
            {p.name} <span>{p.status}</span>
          </div>
        ))
      )}

      {/* =========================
          ORDER QUEUE
      ========================== */}

      <h3>Order queue</h3>

      {s.orders.length === 0 ? (
        <p>No orders found.</p>
      ) : (
        s.orders.map((o) => (
          <div key={o.id}>
            <div className="row">
              <span>{o.order_number}</span>

              <span>{o.status}</span>
            </div>

            {/* Shipments belonging to this order */}

            {getShipmentsForOrder(o.id).map(
              (shipment) => (
                <div
                  className="row"
                  key={shipment.id}
                  style={{
                    display: "block",
                    marginBottom: "12px",
                  }}
                >
                  <p>
                    <strong>Carrier:</strong>{" "}
                    {shipment.carrier}
                  </p>

                  <p>
                    <strong>Tracking:</strong>{" "}
                    {shipment.tracking_number}
                  </p>

                  <p>
                    <strong>Status:</strong>{" "}
                    {shipment.status}
                  </p>

                  {shipment.estimated_arrival && (
                    <p>
                      <strong>
                        Estimated arrival:
                      </strong>{" "}
                      {shipment.estimated_arrival}
                    </p>
                  )}

                  <select
                    value={shipment.status}
                    onChange={(e) =>
                      updateShipmentStatus(
                        shipment.id,
                        e.target.value
                      )
                    }
                  >
                    <option value="PREPARING">
                      PREPARING
                    </option>

                    <option value="DISPATCHED">
                      DISPATCHED
                    </option>

                    <option value="IN_TRANSIT">
                      IN TRANSIT
                    </option>

                    <option value="DELIVERED">
                      DELIVERED
                    </option>
                  </select>
                </div>
              )
            )}
          </div>
        ))
      )}

      {/* =========================
          CREATE SHIPMENT
      ========================== */}

      <h3>Create shipment</h3>

      <form onSubmit={createShipment}>
        <select
          name="order"
          value={shipmentForm.order}
          onChange={handleShipmentChange}
          required
        >
          <option value="">
            Select order
          </option>

          {s.orders.map((order) => (
            <option
              key={order.id}
              value={order.id}
            >
              {order.order_number} — {order.status}
            </option>
          ))}
        </select>

        <input
          name="carrier"
          value={shipmentForm.carrier}
          onChange={handleShipmentChange}
          placeholder="Carrier"
          required
        />

        <input
          name="tracking_number"
          value={shipmentForm.tracking_number}
          onChange={handleShipmentChange}
          placeholder="Tracking number"
          required
        />

        <label>
          Estimated arrival
        </label>

        <input
          type="date"
          name="estimated_arrival"
          value={
            shipmentForm.estimated_arrival
          }
          onChange={handleShipmentChange}
        />

        <button
          type="submit"
          disabled={creatingShipment}
        >
          {creatingShipment
            ? "Creating..."
            : "Create shipment"}
        </button>
      </form>

      {/* =========================
          PURCHASING CUSTOMERS
      ========================== */}

      <h3>Purchasing customers</h3>

      {s.customers.length === 0 ? (
        <p>No purchasing customers found.</p>
      ) : (
        s.customers.map((c) => (
          <p key={c.id}>
            {c.first_name} {c.last_name}
          </p>
        ))
      )}
    </div>
  );
}
