import React, { useEffect, useState } from "react";
import client from "../api/client.js";

export default function AdminDashboard() {
  const [state, setState] = useState({
    categories: [],
    users: [],
    orders: [],
    refunds: [],
    disputes: [],
    stock: [],
    discountCodes: [],
    shippingZones: [],
    customers: [],
    stores: [],
    products: [],
    payments: [],
    reviews: [],
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");

  const [discountForm, setDiscountForm] = useState({
    code: "",
    discount_type: "PERCENTAGE",
    value: "",
    starts_at: "",
    ends_at: "",
    is_active: true,
  });

  const [creatingDiscount, setCreatingDiscount] =
    useState(false);

  const [zoneForm, setZoneForm] = useState({
    name: "",
    regions: "",
    delivery_fee: "",
    estimated_days: "3",
    is_active: true,
  });

  const [creatingZone, setCreatingZone] =
    useState(false);

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const r = await Promise.all([
        client.get("/catalog/categories/"),
        client.get("/users/"),
        client.get("/orders/admin/"),
        client.get("/orders/refund-requests/admin/"),
        client.get("/orders/disputes/admin/"),
        client.get("/inventory/low-stock/"),
        client.get("/catalog/discount-codes/"),
        client.get("/shipments/zones/"),
        client.get("/customers/"),
        client.get("/customers/stores/admin/"),
        client.get("/catalog/products/"),
        client.get("/payments/admin/"),
        client.get("/reviews/admin/"),
      ]);

      setState({
        categories: r[0].data.results || r[0].data,
        users: r[1].data.results || r[1].data,
        orders: r[2].data.results || r[2].data,
        refunds: r[3].data.results || r[3].data,
        disputes: r[4].data.results || r[4].data,
        stock: r[5].data.results || r[5].data,
        discountCodes: r[6].data.results || r[6].data,
        shippingZones: r[7].data.results || r[7].data,
        customers: r[8].data.results || r[8].data,
        stores: r[9].data.results || r[9].data,
        products: r[10].data.results || r[10].data,
        payments: r[11].data.results || r[11].data,
        reviews: r[12].data.results || r[12].data,
      });
    } catch (e) {
      setError(
        e.response?.data?.error?.message ||
          "Unable to load administration data."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const create = async (e) => {
    e.preventDefault();

    try {
      await client.post("/catalog/categories/", {
        name,
        slug: name.toLowerCase().replace(/\s+/g, "-"),
      });

      setName("");
      await load();
    } catch (e) {
      setError("Category could not be created.");
    }
  };

  const archive = async (id) => {
    try {
      await client.post(
        `/catalog/categories/${id}/archive/`
      );

      await load();
    } catch (e) {
      setError("Category archive failed.");
    }
  };

  const restore = async (id) => {
    try {
      await client.post(
        `/catalog/categories/${id}/restore/`
      );

      await load();
    } catch (e) {
      setError("Category restore failed.");
    }
  };

  const userStatus = (id, account_status) =>
    client
      .patch(`/users/${id}/status/`, {
        account_status,
      })
      .then(load)
      .catch(() =>
        setError("User update failed.")
      );

  const userRole = (id, role) =>
    client.patch(`/users/${id}/status/`, { role }).then(load).catch(() => setError("User role update failed."));

  const removeStore = async (id, name) => {
    if (!window.confirm(`Archive ${name}? Its products will be removed from the public catalog while order history is preserved.`)) return;
    try { await client.delete(`/customers/stores/admin/${id}/`); await load(); }
    catch (e) { setError(e.response?.data?.error?.message || "Store could not be archived."); }
  };

  const archiveProduct = async (id) => {
    if (!window.confirm("Archive this product?")) return;
    try { await client.delete(`/catalog/products/${id}/`); await load(); }
    catch (e) { setError(e.response?.data?.error?.message || "Product could not be archived."); }
  };

  const moderateReview = async (id, moderation_status) => {
    try { await client.patch(`/reviews/${id}/moderate/`, { moderation_status }); await load(); }
    catch (e) { setError(e.response?.data?.error?.message || "Review could not be updated."); }
  };

  const orderStatus = (id, status) =>
    client
      .patch(`/orders/${id}/status/`, {
        status,
      })
      .then(load)
      .catch(() =>
        setError("Order update failed.")
      );

  const resolveDispute = async (
    id,
    status,
    resolution
  ) => {
    if (!resolution.trim()) {
      setError("Resolution is required.");
      return;
    }

    try {
      await client.patch(
        `/orders/disputes/${id}/`,
        {
          status,
          resolution,
        }
      );

      await load();
    } catch (e) {
      setError(
        e.response?.data?.error?.message ||
          "Dispute could not be updated."
      );
    }
  };

  /* =========================
      DISCOUNT CODES
  ========================== */

  const handleDiscountChange = (e) => {
    const { name, value, type, checked } = e.target;

    setDiscountForm((previous) => ({
      ...previous,
      [name]:
        type === "checkbox" ? checked : value,
    }));
  };

  const createDiscountCode = async (e) => {
    e.preventDefault();

    if (
      !discountForm.code.trim() ||
      !discountForm.value ||
      !discountForm.starts_at ||
      !discountForm.ends_at
    ) {
      setError(
        "Code, value, start date and end date are required."
      );
      return;
    }

    if (Number(discountForm.value) <= 0) {
      setError(
        "Discount value must be greater than zero."
      );
      return;
    }

    if (
      discountForm.discount_type === "PERCENTAGE" &&
      Number(discountForm.value) > 100
    ) {
      setError(
        "Percentage discount cannot be greater than 100."
      );
      return;
    }

    if (
      new Date(discountForm.ends_at) <=
      new Date(discountForm.starts_at)
    ) {
      setError(
        "End date must be after start date."
      );
      return;
    }

    setCreatingDiscount(true);
    setError("");

    try {
      await client.post(
        "/catalog/discount-codes/",
        {
          code: discountForm.code
            .trim()
            .toUpperCase(),

          discount_type:
            discountForm.discount_type,

          value: discountForm.value,

          starts_at: new Date(
            discountForm.starts_at
          ).toISOString(),

          ends_at: new Date(
            discountForm.ends_at
          ).toISOString(),

          is_active:
            discountForm.is_active,
        }
      );

      setDiscountForm({
        code: "",
        discount_type: "PERCENTAGE",
        value: "",
        starts_at: "",
        ends_at: "",
        is_active: true,
      });

      await load();
    } catch (e) {
      setError(
        e.response?.data?.error?.message ||
          "Discount code could not be created."
      );
    } finally {
      setCreatingDiscount(false);
    }
  };

  /* =========================
      SHIPPING ZONES
  ========================== */

  const handleZoneChange = (e) => {
    const { name, value, type, checked } = e.target;

    setZoneForm((previous) => ({
      ...previous,
      [name]:
        type === "checkbox" ? checked : value,
    }));
  };

  const createShippingZone = async (e) => {
    e.preventDefault();

    if (
      !zoneForm.name.trim() ||
      !zoneForm.regions.trim() ||
      !zoneForm.delivery_fee ||
      !zoneForm.estimated_days
    ) {
      setError(
        "Zone name, regions, delivery fee and estimated days are required."
      );
      return;
    }

    if (Number(zoneForm.delivery_fee) < 0) {
      setError(
        "Delivery fee cannot be negative."
      );
      return;
    }

    if (
      !Number.isInteger(
        Number(zoneForm.estimated_days)
      ) ||
      Number(zoneForm.estimated_days) < 1
    ) {
      setError(
        "Estimated days must be a whole number greater than zero."
      );
      return;
    }

    const regions = zoneForm.regions
      .split(",")
      .map((region) => region.trim())
      .filter(Boolean);

    if (regions.length === 0) {
      setError(
        "At least one region is required."
      );
      return;
    }

    setCreatingZone(true);
    setError("");

    try {
      await client.post("/shipments/zones/", {
        name: zoneForm.name.trim(),
        regions,
        delivery_fee: zoneForm.delivery_fee,
        estimated_days:
          Number(zoneForm.estimated_days),
        is_active: zoneForm.is_active,
      });

      setZoneForm({
        name: "",
        regions: "",
        delivery_fee: "",
        estimated_days: "3",
        is_active: true,
      });

      await load();
    } catch (e) {
      setError(
        e.response?.data?.error?.message ||
          "Shipping zone could not be created."
      );
    } finally {
      setCreatingZone(false);
    }
  };

  return (
    <div className="container">
      <span className="eyebrow">
        Administration
      </span>

      <h2>Store management</h2>

      {error && (
        <p className="error">
          {error}
        </p>
      )}

      {loading ? (
        <p>Loading…</p>
      ) : (
        <>
          <h3>Users and customers</h3>
          <p>{state.users.length} user account{state.users.length === 1 ? "" : "s"} loaded. Account role and status controls are available below.</p>
          {state.customers.length > 0 && <p style={{ marginTop: 10 }}>Customer records: {state.customers.map((customer) => `${customer.first_name} ${customer.last_name} (${customer.email})`).join(", ")}</p>}

          <h3 style={{ marginTop: 28 }}>Stores</h3>
          {state.stores.length === 0 ? <p>No stores found.</p> : <table><thead><tr><th>Name</th><th>Owner</th><th>Status</th><th>Products</th><th></th></tr></thead><tbody>{state.stores.map((store) => <tr key={store.id}><td>{store.name}</td><td>{store.owner_name || store.owner_email}</td><td>{store.status}</td><td>{store.product_count}</td><td>{store.status !== "ARCHIVED" && <button className="secondary" onClick={() => removeStore(store.id, store.name)}>Archive</button>}</td></tr>)}</tbody></table>}

          <h3 style={{ marginTop: 28 }}>Products</h3>
          {state.products.length === 0 ? <p>No products found.</p> : <table><thead><tr><th>Product</th><th>Store</th><th>Price</th><th>Status</th><th></th></tr></thead><tbody>{state.products.map((product) => <tr key={product.id}><td>{product.name}</td><td>{product.store_name || "—"}</td><td>${product.min_price}</td><td>{product.status}</td><td>{product.status !== "ARCHIVED" && <button className="secondary" onClick={() => archiveProduct(product.id)}>Archive</button>}</td></tr>)}</tbody></table>}

          <h3 style={{ marginTop: 28 }}>Orders and shipping addresses</h3>
          <p>{state.orders.length === 0 ? "No orders found." : "Order status controls and protected shipping details are available in the order ledger below."}</p>

          <h3 style={{ marginTop: 28 }}>Payments</h3>
          {state.payments.length === 0 ? <p>No payments found.</p> : <table><thead><tr><th>Order</th><th>Buyer</th><th>Provider</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead><tbody>{state.payments.map((payment) => <tr key={payment.id}><td>{payment.order_number}</td><td>{payment.buyer}</td><td>{payment.provider}</td><td>${payment.amount}</td><td>{payment.status}</td><td>{new Date(payment.created_at).toLocaleDateString()}</td></tr>)}</tbody></table>}

          <h3 style={{ marginTop: 28 }}>Reviews</h3>
          {state.reviews.length === 0 ? <p>No reviews found.</p> : <table><thead><tr><th>Product</th><th>Buyer</th><th>Rating</th><th>Comment</th><th>Status</th><th></th></tr></thead><tbody>{state.reviews.map((review) => <tr key={review.id}><td>{review.product}</td><td>{review.customer_name}</td><td>{review.rating}/5</td><td>{review.comment}</td><td>{review.moderation_status}</td><td>{review.moderation_status === "PENDING" && <><button className="secondary" onClick={() => moderateReview(review.id, "APPROVED")}>Approve</button> <button className="secondary" onClick={() => moderateReview(review.id, "REJECTED")}>Reject</button></>}</td></tr>)}</tbody></table>}

          {/* =========================
              CATEGORIES
          ========================== */}

          <form onSubmit={create}>
            <input
              value={name}
              onChange={(e) =>
                setName(e.target.value)
              }
              placeholder="New category"
              required
            />

            <button type="submit">
              Create category
            </button>
          </form>

          <h3>Categories</h3>

          {state.categories.length === 0 ? (
            <p>No categories found.</p>
          ) : (
            state.categories.map((c) => (
              <div
                className="row"
                key={c.id}
              >
                <span>
                  {c.name}

                  {c.status && (
                    <span>
                      {" "}
                      ({c.status})
                    </span>
                  )}
                </span>

                {c.status === "ARCHIVED" ? (
                  <button
                    className="secondary"
                    onClick={() =>
                      restore(c.id)
                    }
                  >
                    Restore
                  </button>
                ) : (
                  <button
                    className="secondary"
                    onClick={() =>
                      archive(c.id)
                    }
                  >
                    Archive
                  </button>
                )}
              </div>
            ))
          )}

          {/* =========================
              USERS
          ========================== */}

          <h3>Users</h3>

          {state.users.length === 0 ? (
            <p>No users found.</p>
          ) : (
            state.users.map((u) => (
              <div
                className="row"
                key={u.id}
              >
                <span>{u.email}</span>

                <select
                  value={u.account_status}
                  onChange={(e) =>
                    userStatus(
                      u.id,
                      e.target.value
                    )
                  }
                >
                  <option value="ACTIVE">
                    ACTIVE
                  </option>

                  <option value="DEACTIVATED">
                    DEACTIVATED
                  </option>

                  <option value="PENDING">
                    PENDING
                  </option>
                </select>

                <select value={u.role || "CUSTOMER"} onChange={(e) => userRole(u.id, e.target.value)} aria-label={`Role for ${u.email}`}>
                  <option value="CUSTOMER">Customer</option>
                  <option value="SELLER">Seller</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>
            ))
          )}

          {/* =========================
              ORDERS & REFUNDS
          ========================== */}

          <h3>Orders & refunds</h3>

          {state.orders.length === 0 ? (
            <p>No orders found.</p>
          ) : (
            state.orders.map((o) => (
              <div
                className="row"
                key={o.id}
              >
                <span>
                  {o.order_number}
                </span>

                <select
                  value={o.status}
                  onChange={(e) =>
                    orderStatus(
                      o.id,
                      e.target.value
                    )
                  }
                >
                  {[
                    "PENDING",
                    "CONFIRMED",
                    "SHIPPED",
                    "DELIVERED",
                    "CANCELLED",
                    "REFUNDED",
                  ].map((x) => (
                    <option
                      key={x}
                      value={x}
                    >
                      {x}
                    </option>
                  ))}
                </select>
              </div>
            ))
          )}

          {state.refunds.length === 0 ? (
            <p>
              No refund requests.
            </p>
          ) : (
            state.refunds.map((r) => (
              <p key={r.id}>
                Refund request:{" "}
                {r.reason} ({r.status})
              </p>
            ))
          )}

          {/* =========================
              DISCOUNT CODES
          ========================== */}

          <h3>
            Discount codes
          </h3>

          <form
            onSubmit={
              createDiscountCode
            }
          >
            <input
              name="code"
              value={
                discountForm.code
              }
              onChange={
                handleDiscountChange
              }
              placeholder="Discount code"
              maxLength={50}
              required
            />

            <select
              name="discount_type"
              value={
                discountForm.discount_type
              }
              onChange={
                handleDiscountChange
              }
            >
              <option value="PERCENTAGE">
                Percentage
              </option>

              <option value="FIXED">
                Fixed
              </option>
            </select>

            <input
              name="value"
              type="number"
              min="0.01"
              step="0.01"
              value={
                discountForm.value
              }
              onChange={
                handleDiscountChange
              }
              placeholder="Discount value"
              required
            />

            <label>
              Starts at
            </label>

            <input
              name="starts_at"
              type="datetime-local"
              value={
                discountForm.starts_at
              }
              onChange={
                handleDiscountChange
              }
              required
            />

            <label>
              Ends at
            </label>

            <input
              name="ends_at"
              type="datetime-local"
              value={
                discountForm.ends_at
              }
              onChange={
                handleDiscountChange
              }
              required
            />

            <label>
              <input
                name="is_active"
                type="checkbox"
                checked={
                  discountForm.is_active
                }
                onChange={
                  handleDiscountChange
                }
              />

              {" "}Active
            </label>

            <button
              type="submit"
              disabled={
                creatingDiscount
              }
            >
              {creatingDiscount
                ? "Creating..."
                : "Create discount code"}
            </button>
          </form>

          <h4>
            Existing discount codes
          </h4>

          {state.discountCodes.length ===
          0 ? (
            <p>
              No discount codes found.
            </p>
          ) : (
            state.discountCodes.map(
              (discount) => (
                <div
                  className="row"
                  key={discount.id}
                >
                  <span>
                    <strong>
                      {discount.code}
                    </strong>{" "}
                    —{" "}
                    {
                      discount.discount_type
                    }{" "}
                    {discount.value}
                  </span>

                  <span>
                    {discount.is_active
                      ? "ACTIVE"
                      : "INACTIVE"}
                  </span>
                </div>
              )
            )
          )}

          {/* =========================
              SHIPPING ZONES
          ========================== */}

          <h3>
            Shipping zones
          </h3>

          <form
            onSubmit={
              createShippingZone
            }
          >
            <input
              name="name"
              value={
                zoneForm.name
              }
              onChange={
                handleZoneChange
              }
              placeholder="Zone name"
              maxLength={100}
              required
            />

            <input
              name="regions"
              value={
                zoneForm.regions
              }
              onChange={
                handleZoneChange
              }
              placeholder="Regions, e.g. Baku, Sumqayit, Ganja"
              required
            />

            <input
              name="delivery_fee"
              type="number"
              min="0"
              step="0.01"
              value={
                zoneForm.delivery_fee
              }
              onChange={
                handleZoneChange
              }
              placeholder="Delivery fee"
              required
            />

            <input
              name="estimated_days"
              type="number"
              min="1"
              step="1"
              value={
                zoneForm.estimated_days
              }
              onChange={
                handleZoneChange
              }
              placeholder="Estimated days"
              required
            />

            <label>
              <input
                name="is_active"
                type="checkbox"
                checked={
                  zoneForm.is_active
                }
                onChange={
                  handleZoneChange
                }
              />

              {" "}Active
            </label>

            <button
              type="submit"
              disabled={
                creatingZone
              }
            >
              {creatingZone
                ? "Creating..."
                : "Create shipping zone"}
            </button>
          </form>

          <h4>
            Existing shipping zones
          </h4>

          {state.shippingZones.length ===
          0 ? (
            <p>
              No shipping zones found.
            </p>
          ) : (
            state.shippingZones.map(
              (zone) => (
                <div
                  className="row"
                  key={zone.id}
                >
                  <div>
                    <strong>
                      {zone.name}
                    </strong>

                    <p>
                      Regions:{" "}
                      {Array.isArray(
                        zone.regions
                      )
                        ? zone.regions.join(
                            ", "
                          )
                        : ""}
                    </p>

                    <p>
                      Delivery fee:{" "}
                      {zone.delivery_fee}
                    </p>

                    <p>
                      Estimated delivery:{" "}
                      {zone.estimated_days}{" "}
                      days
                    </p>
                  </div>

                  <span>
                    {zone.is_active
                      ? "ACTIVE"
                      : "INACTIVE"}
                  </span>
                </div>
              )
            )
          )}

          {/* =========================
              DISPUTES
          ========================== */}

          <h3>Disputes</h3>

          {state.disputes.length ===
          0 ? (
            <p>
              No disputes found.
            </p>
          ) : (
            state.disputes.map((d) => (
              <DisputeItem
                key={d.id}
                dispute={d}
                onResolve={
                  resolveDispute
                }
              />
            ))
          )}

          {/* =========================
              LOW STOCK
          ========================== */}

          <h3>Low stock</h3>

          {state.stock.length ===
          0 ? (
            <p>
              No low-stock products.
            </p>
          ) : (
            state.stock.map((v) => (
              <p key={v.id}>
                {v.sku}:{" "}
                {v.stock_quantity}
              </p>
            ))
          )}
        </>
      )}
    </div>
  );
}

function DisputeItem({
  dispute,
  onResolve,
}) {
  const [status, setStatus] =
    useState(
      dispute.status === "OPEN"
        ? "RESOLVED"
        : dispute.status
    );

  const [resolution, setResolution] =
    useState(
      dispute.resolution || ""
    );

  const [saving, setSaving] =
    useState(false);

  const submit = async () => {
    if (!resolution.trim()) {
      return;
    }

    setSaving(true);

    try {
      await onResolve(
        dispute.id,
        status,
        resolution
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="row"
      style={{
        display: "block",
        marginBottom: "20px",
      }}
    >
      <p>
        <strong>
          Subject:
        </strong>{" "}
        {dispute.subject}
      </p>

      <p>
        <strong>
          Order:
        </strong>{" "}
        {dispute.order}
      </p>

      <p>
        <strong>
          Customer:
        </strong>{" "}
        {dispute.customer}
      </p>

      <p>
        <strong>
          Description:
        </strong>{" "}
        {dispute.description}
      </p>

      <p>
        <strong>
          Status:
        </strong>{" "}
        {dispute.status}
      </p>

      {dispute.status === "OPEN" ? (
        <>
          <select
            value={status}
            onChange={(e) =>
              setStatus(
                e.target.value
              )
            }
          >
            <option value="RESOLVED">
              RESOLVED
            </option>

            <option value="REJECTED">
              REJECTED
            </option>
          </select>

          <textarea
            value={resolution}
            onChange={(e) =>
              setResolution(
                e.target.value
              )
            }
            placeholder="Enter resolution..."
            rows={3}
            style={{
              display: "block",
              width: "100%",
              marginTop: "8px",
              marginBottom: "8px",
            }}
          />

          <button
            onClick={submit}
            disabled={
              saving ||
              !resolution.trim()
            }
          >
            {saving
              ? "Saving..."
              : "Resolve dispute"}
          </button>
        </>
      ) : (
        <p>
          <strong>
            Resolution:
          </strong>{" "}
          {dispute.resolution ||
            "No resolution"}
        </p>
      )}
    </div>
  );
}
