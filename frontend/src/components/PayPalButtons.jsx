import React, { useEffect, useRef, useState } from "react";

const PAYPAL_CLIENT_ID = import.meta.env.VITE_PAYPAL_CLIENT_ID || "sb"; // "sb" = PayPal's public sandbox test client id

let sdkLoadPromise = null;

function loadPayPalSdk() {
  if (window.paypal) return Promise.resolve(window.paypal);
  if (sdkLoadPromise) return sdkLoadPromise;

  sdkLoadPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://www.paypal.com/sdk/js?client-id=${PAYPAL_CLIENT_ID}&currency=USD`;
    script.onload = () => resolve(window.paypal);
    script.onerror = () => reject(new Error("Could not load the PayPal SDK."));
    document.body.appendChild(script);
  });
  return sdkLoadPromise;
}

/**
 * Renders the official PayPal Smart Buttons for a given order total.
 * Uses PayPal's sandbox ("sb") client id by default so this works out of
 * the box for testing — set VITE_PAYPAL_CLIENT_ID to your own sandbox/live
 * client id for real transactions.
 */
export default function PayPalButtons({ amount, onApproved, onError }) {
  const containerRef = useRef(null);
  const onApprovedRef = useRef(onApproved);
  const onErrorRef = useRef(onError);
  const [status, setStatus] = useState("loading"); // loading | ready | error

  useEffect(() => {
    onApprovedRef.current = onApproved;
    onErrorRef.current = onError;
  }, [onApproved, onError]);

  useEffect(() => {
    let cancelled = false;
    let buttonsInstance = null;

    loadPayPalSdk()
      .then(async (paypal) => {
        if (cancelled || !containerRef.current) return;
        if (typeof paypal?.Buttons !== "function") {
          throw new Error("PayPal Buttons is unavailable.");
        }
        containerRef.current.innerHTML = "";
        buttonsInstance = paypal.Buttons({
          style: { layout: "vertical", color: "gold", shape: "pill", label: "paypal" },
          createOrder: (_, actions) =>
            actions.order.create({
              purchase_units: [{ amount: { value: Number(amount).toFixed(2), currency_code: "USD" } }],
            }),
          onApprove: async (_, actions) => {
            const details = await actions.order.capture();
            if (typeof onApprovedRef.current === "function") {
              await onApprovedRef.current(details);
            }
          },
          onError: (err) => {
            console.error("PayPal error:", err);
            // Popup closure is a normal cancellation path.  Notify the UI
            // when a handler exists, but never throw from the SDK callback.
            if (typeof onErrorRef.current === "function") {
              onErrorRef.current(err);
            }
          },
        });
        await buttonsInstance.render(containerRef.current);
        if (!cancelled) setStatus("ready");
      })
      .catch(() => {
        if (!cancelled) setStatus("error");
      });

    return () => {
      cancelled = true;
      if (typeof buttonsInstance?.close === "function") {
        // The SDK may reject cleanup while a popup is being closed.  Cleanup
        // must not be allowed to escape a React unmount.
        Promise.resolve(buttonsInstance.close()).catch(() => {});
      }
    };
  }, [amount]);

  return (
    <div>
      {status === "loading" && <p style={{ opacity: 0.7, fontSize: "0.88rem" }}>Loading PayPal…</p>}
      {status === "error" && <p className="error">Could not load PayPal checkout. Check your connection and try again.</p>}
      <div ref={containerRef} />
    </div>
  );
}
