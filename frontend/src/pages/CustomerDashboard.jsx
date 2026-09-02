import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import client, { apiErrorMessage } from "../api/client.js";

export default function CustomerDashboard() {
  const navigate = useNavigate();

  const [dashboard, setDashboard] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creatingStore, setCreatingStore] = useState(false);
  const [creatingProduct, setCreatingProduct] = useState(false);
  const [removingProduct, setRemovingProduct] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [storeForm, setStoreForm] = useState({
    name: "",
    description: "",
  });

  const [product, setProduct] = useState({
    name: "",
    slug: "",
    description: "",
    base_price: "",
    stock_quantity: "0",
    category: "",
    status: "DRAFT",
  });

  const [image, setImage] = useState(null);

  // ---------------------------------------------------------
  // Convert API errors into readable text
  // ---------------------------------------------------------
  const getApiError = apiErrorMessage;

  // ---------------------------------------------------------
  // Create a safe slug
  // ---------------------------------------------------------
  const makeSlug = (value) => {
    return String(value || "")
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  };

  // ---------------------------------------------------------
  // Create unique slug
  // ---------------------------------------------------------
  const makeUniqueSlug = (name) => {
    const base = makeSlug(name);

    if (!base) {
      return `product-${Date.now()}`;
    }

    return `${base}-${Date.now()}`;
  };

  // ---------------------------------------------------------
  // Load dashboard + categories
  // ---------------------------------------------------------
  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const [storeResult, categoryResult] = await Promise.all([
        client
          .get("/customers/store/dashboard/")
          .catch((err) => {
            if (err?.response?.status === 404) {
              return { data: null };
            }

            throw err;
          }),

        client.get("/catalog/categories/"),
      ]);

      setDashboard(storeResult.data);

      const categoryData = categoryResult.data;

      if (Array.isArray(categoryData)) {
        setCategories(categoryData);
      } else if (Array.isArray(categoryData?.results)) {
        setCategories(categoryData.results);
      } else {
        setCategories([]);
      }
    } catch (err) {
      console.error("Dashboard load error:", err);

      setError(
        getApiError(
          err,
          "Store data could not be loaded."
        )
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  // ---------------------------------------------------------
  // Create store
  // ---------------------------------------------------------
  const createStore = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setCreatingStore(true);

    try {
      await client.post("/customers/store/", {
        name: storeForm.name.trim(),
        description: storeForm.description.trim(),
      });

      setStoreForm({
        name: "",
        description: "",
      });

      setSuccess("Store created successfully.");

      await load();
    } catch (err) {
      console.error("Create store error:", err);

      setError(
        getApiError(
          err,
          "Store could not be created."
        )
      );
    } finally {
      setCreatingStore(false);
    }
  };

  // ---------------------------------------------------------
  // Create product
  // ---------------------------------------------------------
  const createProduct = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");
    setCreatingProduct(true);

    try {
      const productName = product.name.trim();

      if (!productName) {
        setError("Product name is required.");
        setCreatingProduct(false);
        return;
      }

      if (!product.base_price) {
        setError("Product price is required.");
        setCreatingProduct(false);
        return;
      }

      if (!product.category) {
        setError("Please select a category.");
        setCreatingProduct(false);
        return;
      }

      const uniqueSlug = makeUniqueSlug(productName);

      const payload = {
        name: productName,
        slug: uniqueSlug,
        description: product.description.trim(),
        base_price: product.base_price,
        stock_quantity: product.stock_quantity || "0",
        category: product.category,
        status: product.status,
      };

      console.log(
        "Creating product with payload:",
        payload
      );

      const response = await client.post(
        "/catalog/store/products/",
        payload
      );

      const createdProduct = response?.data;

      console.log(
        "Product created successfully:",
        createdProduct
      );

      // -----------------------------------------------------
      // Upload image
      // -----------------------------------------------------
      if (image && createdProduct?.id) {
        try {
          const formData = new FormData();

          formData.append("image", image);

          await client.post(
            `/catalog/store/products/${createdProduct.id}/images/`,
            formData
          );

          console.log("Product image uploaded successfully.");
        } catch (imageError) {
          console.error(
            "Image upload error:",
            imageError?.response?.data || imageError
          );

          setSuccess(
            "Product created successfully, but the image could not be uploaded."
          );
        }
      }

      // -----------------------------------------------------
      // Reset form
      // -----------------------------------------------------
      setProduct({
        name: "",
        slug: "",
        description: "",
        base_price: "",
        stock_quantity: "0",
        category: "",
        status: "DRAFT",
      });

      setImage(null);

      const fileInput = document.getElementById(
        "product-image-input"
      );

      if (fileInput) {
        fileInput.value = "";
      }

      if (createdProduct?.status === "ACTIVE") {
        setSuccess(
          "Product published successfully."
        );
      } else {
        setSuccess(
          "Product created successfully."
        );
      }

      await load();
    } catch (err) {
      console.error(
        "Create/publish product error:",
        err?.response?.data || err
      );

      setError(
        getApiError(
          err,
          "Product could not be created."
        )
      );
    } finally {
      setCreatingProduct(false);
    }
  };

  // ---------------------------------------------------------
  // REMOVE PRODUCT
  // ---------------------------------------------------------
  const removeProduct = async (productId, productName) => {
    if (!productId) {
      setError("Product ID is missing.");
      return;
    }

    const confirmed = window.confirm(
      `Are you sure you want to remove "${productName}"?`
    );

    if (!confirmed) {
      return;
    }

    setError("");
    setSuccess("");
    setRemovingProduct(productId);

    try {
      console.log(
        "Removing product:",
        productId
      );

      await client.delete(
        `/catalog/store/products/${productId}/`
      );

      console.log(
        "Product removed successfully:",
        productId
      );

      // -----------------------------------------------------
      // Remove immediately from dashboard UI
      // -----------------------------------------------------
      setDashboard((currentDashboard) => {
        if (!currentDashboard) {
          return currentDashboard;
        }

        return {
          ...currentDashboard,
          products: Array.isArray(currentDashboard.products)
            ? currentDashboard.products.filter(
                (item) => item.id !== productId
              )
            : [],
        };
      });

      setSuccess(
        `"${productName}" was removed successfully.`
      );

      /*
       * Important:
       * The backend archive operation removes the product
       * from the public catalog as well.
       */
    } catch (err) {
      console.error(
        "Remove product error:",
        err?.response?.data || err
      );

      setError(
        getApiError(
          err,
          "Product could not be removed."
        )
      );
    } finally {
      setRemovingProduct(null);
    }
  };

  // ---------------------------------------------------------
  // View store
  // ---------------------------------------------------------
  const preview = () => {
    if (dashboard?.store?.id) {
      navigate(`/stores/${dashboard.store.id}`);
    }
  };

  // ---------------------------------------------------------
  // Loading
  // ---------------------------------------------------------
  if (loading) {
    return (
      <div className="container">
        <span className="eyebrow">
          Customer workspace
        </span>

        <h2>My Store</h2>

        <p>Loading store data...</p>
      </div>
    );
  }

  // ---------------------------------------------------------
  // No store yet
  // ---------------------------------------------------------
  if (!dashboard) {
    return (
      <div className="container">
        <span className="eyebrow">
          Customer workspace
        </span>

        <h2>Create your store</h2>

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {success && (
          <div className="success">
            {success}
          </div>
        )}

        <form onSubmit={createStore}>
          <label>Store name</label>

          <input
            type="text"
            value={storeForm.name}
            onChange={(e) =>
              setStoreForm({
                ...storeForm,
                name: e.target.value,
              })
            }
            required
          />

          <label>Description</label>

          <textarea
            value={storeForm.description}
            onChange={(e) =>
              setStoreForm({
                ...storeForm,
                description: e.target.value,
              })
            }
          />

          <button
            type="submit"
            disabled={creatingStore}
          >
            {creatingStore
              ? "Creating..."
              : "Create store"}
          </button>
        </form>
      </div>
    );
  }

  // ---------------------------------------------------------
  // Safe dashboard values
  // ---------------------------------------------------------
  const products = Array.isArray(
    dashboard.products
  )
    ? dashboard.products
    : [];

  const sales = Array.isArray(
    dashboard.sales
  )
    ? dashboard.sales
    : [];

  const salesSummary =
    dashboard.sales_summary || {};

  return (
    <div className="container">
      <span className="eyebrow">
        Customer workspace
      </span>

      <h2>My Store</h2>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {success && (
        <div className="success">
          {success}
        </div>
      )}

      {/* --------------------------------------------------- */}
      {/* STORE HEADER */}
      {/* --------------------------------------------------- */}

      <div className="row">
        <span>
          <strong>
            {dashboard.store?.name || "My Store"}
          </strong>

          {" · "}

          {dashboard.store?.status || ""}
        </span>

        <button
          type="button"
          onClick={preview}
        >
          View My Store
        </button>
      </div>

      {/* --------------------------------------------------- */}
      {/* STATS */}
      {/* --------------------------------------------------- */}

      <div
        className="grid"
        style={{ marginTop: 18 }}
      >
        <div className="card">
          <h3>Total products</h3>

          <p className="price">
            {products.length}
          </p>
        </div>

        <div className="card">
          <h3>Orders</h3>

          <p className="price">
            {salesSummary.total_orders || 0}
          </p>
        </div>

        <div className="card">
          <h3>Items sold</h3>

          <p className="price">
            {salesSummary.total_items_sold || 0}
          </p>
        </div>

        <div className="card">
          <h3>Revenue</h3>

          <p className="price">
            ${salesSummary.total_revenue || "0.00"}
          </p>
        </div>
      </div>

      {/* --------------------------------------------------- */}
      {/* ADD PRODUCT */}
      {/* --------------------------------------------------- */}

      <h3 style={{ marginTop: 28 }}>
        Add product
      </h3>

      <form onSubmit={createProduct}>
        <input
          placeholder="Product name"
          type="text"
          value={product.name}
          onChange={(e) => {
            const name = e.target.value;

            setProduct((current) => ({
              ...current,
              name,
              slug: makeSlug(name),
            }));
          }}
          required
        />

        <textarea
          placeholder="Description"
          value={product.description}
          onChange={(e) =>
            setProduct((current) => ({
              ...current,
              description: e.target.value,
            }))
          }
        />

        <input
          placeholder="Price"
          type="number"
          min="0"
          step="0.01"
          value={product.base_price}
          onChange={(e) =>
            setProduct((current) => ({
              ...current,
              base_price: e.target.value,
            }))
          }
          required
        />

        <input
          placeholder="Stock quantity"
          type="number"
          min="0"
          value={product.stock_quantity}
          onChange={(e) =>
            setProduct((current) => ({
              ...current,
              stock_quantity: e.target.value,
            }))
          }
          required
        />

        <select
          value={product.category}
          onChange={(e) =>
            setProduct((current) => ({
              ...current,
              category: e.target.value,
            }))
          }
          required
        >
          <option value="">
            Select category
          </option>

          {categories.map((category) => (
            <option
              key={category.id}
              value={category.id}
            >
              {category.name}
            </option>
          ))}
        </select>

        <input
          id="product-image-input"
          type="file"
          accept="image/*"
          onChange={(e) =>
            setImage(
              e.target.files?.[0] || null
            )
          }
        />

        <select
          value={product.status}
          onChange={(e) =>
            setProduct((current) => ({
              ...current,
              status: e.target.value,
            }))
          }
        >
          <option value="DRAFT">
            Draft
          </option>

          <option value="ACTIVE">
            Publish
          </option>
        </select>

        <button
          type="submit"
          disabled={creatingProduct}
        >
          {creatingProduct
            ? "Creating product..."
            : product.status === "ACTIVE"
            ? "Create & Publish"
            : "Create product"}
        </button>
      </form>

      {/* --------------------------------------------------- */}
      {/* MY PRODUCTS */}
      {/* --------------------------------------------------- */}

      <h3 style={{ marginTop: 28 }}>
        My products
      </h3>

      {products.length ? (
        <table>
          <thead>
            <tr>
              <th>Product</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Sold</th>
              <th>Revenue</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td>
                  {typeof p.name === "string"
                    ? p.name
                    : ""}
                </td>

                <td>
                  ${p.price || "0.00"}
                </td>

                <td>
                  {p.stock_quantity ?? 0}
                </td>

                <td>
                  {p.sold ?? 0}
                </td>

                <td>
                  ${p.revenue || "0.00"}
                </td>

                <td>
                  {typeof p.status === "string"
                    ? p.status
                    : ""}
                </td>

                {/* ----------------------------------------- */}
                {/* REMOVE BUTTON */}
                {/* ----------------------------------------- */}

                <td>
                  <button
                    type="button"
                    onClick={() =>
                      removeProduct(
                        p.id,
                        p.name
                      )
                    }
                    disabled={
                      removingProduct === p.id
                    }
                    style={{
                      border: "none",
                      background: "transparent",
                      color: "#dc2626",
                      cursor:
                        removingProduct === p.id
                          ? "not-allowed"
                          : "pointer",
                      fontWeight: 600,
                      padding: "6px 10px",
                    }}
                  >
                    {removingProduct === p.id
                      ? "Removing..."
                      : "Remove"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No products yet.</p>
      )}

      {/* --------------------------------------------------- */}
      {/* STORE SALES */}
      {/* --------------------------------------------------- */}

      <h3 style={{ marginTop: 28 }}>
        Store sales
      </h3>

      {sales.length ? (
        <table>
          <thead>
            <tr>
              <th>Order</th>
              <th>Product</th>
              <th>Quantity</th>
              <th>Price</th>
              <th>Total</th>
              <th>Status</th>
              <th>Date</th>
            </tr>
          </thead>

          <tbody>
            {sales.map((sale, index) => (
              <tr
                key={`${sale.order_id}-${index}`}
              >
                <td>
                  {sale.order_number || "-"}
                </td>

                <td>
                  {typeof sale.product ===
                  "string"
                    ? sale.product
                    : sale.product?.name ||
                      "-"}
                </td>

                <td>
                  {sale.quantity ?? 0}
                </td>

                <td>
                  ${sale.unit_price || "0.00"}
                </td>

                <td>
                  ${sale.total || "0.00"}
                </td>

                <td>
                  {typeof sale.status ===
                  "string"
                    ? sale.status
                    : ""}
                </td>

                <td>
                  {sale.created_at
                    ? new Date(
                        sale.created_at
                      ).toLocaleDateString()
                    : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>
          No completed sales yet.
        </p>
      )}
    </div>
  );
}
