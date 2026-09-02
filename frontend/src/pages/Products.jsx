import React, { useEffect, useState } from "react";
import client, { API_ORIGIN, apiErrorMessage } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { Link, useNavigate } from "react-router-dom";
import "./Products.css";

export default function Products() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = async (q = "") => {
    setLoading(true);

    try {
      const { data } = await client.get("/catalog/products/", {
        params: q ? { q } : {},
      });

      setProducts(data.results || data);
      setMessage("");
    } catch (err) {
      setProducts([]);
      setMessage(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const addToCart = async (product) => {
    try {
      const { data: detail } = await client.get(
        `/catalog/products/${product.id}/`
      );

      const variant = detail.variants?.find((item) => item.in_stock);

      if (!variant) {
        setMessage("This product has no purchasable variant yet.");
        return;
      }

      await client.post("/cart/items/", {
        variant: variant.id,
        quantity: 1,
      });

      setMessage(`${product.name} added to cart.`);
    } catch (err) {
      setMessage(apiErrorMessage(err, "Could not add to cart."));
    }
  };

  const addToWishlist = async (product) => {
    try {
      await client.post("/customers/wishlist/", {
        product: product.id,
      });

      setMessage(`${product.name} saved to wishlist.`);
    } catch (err) {
      setMessage(apiErrorMessage(err, "Could not save this item."));
    }
  };

  const getImageUrl = (image) => {
    if (!image) return null;

    if (image.startsWith("http://") || image.startsWith("https://")) {
      return image;
    }

    return `${API_ORIGIN}${image.startsWith("/") ? "" : "/"}${image}`;
  };

  return (
    <div className="container">
      <span className="eyebrow">Catalog</span>

      <h2>Today's stock</h2>

      <form
        className="catalog-search"
        onSubmit={(e) => {
          e.preventDefault();
          load(search);
        }}
        style={{
          display: "flex",
          gap: 8,
          maxWidth: 620,
          marginTop: 18,
          marginBottom: 4,
        }}
      >
        <input
          placeholder="Search the catalog..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ marginBottom: 0 }}
        />

        <button type="submit" style={{ flexShrink: 0 }}>
          Search
        </button>
      </form>

      {message && (
        <p className="badge" style={{ marginTop: 14 }}>
          {message}
        </p>
      )}

      {loading ? (
        <p style={{ opacity: 0.7, marginTop: 24 }}>
          Checking the shelves…
        </p>
      ) : (
        <div className="grid">
          {products.map((p) => {
            const imageUrl = getImageUrl(p.primary_image);

            return (
              <div className="card catalog-product-card" key={p.id} role="link" tabIndex={0} onClick={() => navigate(`/products/${p.id}`)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") navigate(`/products/${p.id}`); }}>
                {imageUrl ? (
                  <img
                    className="thumb"
                    src={imageUrl}
                    alt={p.name}
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.style.display = "none";
                      e.currentTarget.nextElementSibling.style.display =
                        "flex";
                    }}
                  />
                ) : null}

                <div
                  className="thumb placeholder"
                  style={{
                    display: imageUrl ? "none" : "flex",
                  }}
                >
                  no photo yet
                </div>

                <span className="category-label">
                  {p.category_name}
                </span>

                <h3>
                  <Link to={`/products/${p.id}`}>
                    {p.name}
                  </Link>
                </h3>

                <div className="tear" />

                <span className="price">
                  ${p.min_price}
                </span>

                {p.store_name && <p style={{ margin: "7px 0 0", fontSize: "0.8rem" }}>Store: {p.store_name}</p>}
                {p.rating !== null && p.rating !== undefined && <p style={{ margin: "4px 0 0", fontSize: "0.8rem" }}>★ {p.rating}</p>}

                {user?.role === "CUSTOMER" && (
                  <button onClick={(event) => { event.stopPropagation(); addToCart(p); }}>
                    Add to cart
                  </button>
                )}

                {user?.role === "CUSTOMER" && (
                  <button
                    className="secondary"
                    onClick={(event) => { event.stopPropagation(); addToWishlist(p); }}
                  >
                    Save
                  </button>
                )}
              </div>
            );
          })}

          {!products.length && (
            <p style={{ opacity: 0.7 }}>
              Nothing matches that search.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
