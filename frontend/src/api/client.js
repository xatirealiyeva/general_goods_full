import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

const client = axios.create({ baseURL: API_BASE_URL });

export function apiErrorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (typeof data === "string") return data;
  if (!data || typeof data !== "object") return error?.message || fallback;
  if (typeof data.detail === "string") return data.detail;
  if (typeof data.message === "string") return data.message;
  if (typeof data.error === "string") return data.error;
  if (typeof data.error?.message === "string") return data.error.message;
  const flatten = (value) => {
    if (typeof value === "string" || typeof value === "number") return String(value);
    if (Array.isArray(value)) return value.map(flatten).filter(Boolean).join(" ");
    if (value && typeof value === "object") return Object.entries(value).map(([key, item]) => `${key}: ${flatten(item)}`).filter(Boolean).join("; ");
    return "";
  };
  const fieldErrors = Object.entries(data).map(([field, value]) => {
    const readable = flatten(value);
    return readable ? `${field}: ${readable}` : "";
  }).filter(Boolean);
  return fieldErrors.join("; ") || fallback;
}

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh access token on 401 using the stored refresh token.
client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh_token");
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh });
          localStorage.setItem("access_token", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch (e) {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          localStorage.removeItem("auth_user");
          window.dispatchEvent(new Event("shop-auth-expired"));
        }
      } else {
        // A stale access token must not turn a public catalog request into a
        // permanent 401. Remove it and retry safe reads anonymously.
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        if (String(original.method || "get").toLowerCase() === "get") {
          delete original.headers.Authorization;
          return client(original);
        }
      }
    }
    return Promise.reject(error);
  }
);

export default client;
