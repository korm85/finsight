import axios from "axios";
import type { Analysis } from "../types/analysis";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error("API Error:", err);
    return Promise.reject(err);
  }
);

export const marketApi = {
  overview: () => api.get("/api/market/overview").then((r) => r.data),
  quote: (ticker: string) => api.get(`/api/market/quote/${ticker}`).then((r) => r.data),
  chart: (ticker: string, range = "1mo", indicators?: string) =>
    api.get(`/api/market/chart/${ticker}`, { params: { range, indicators } }).then((r) => r.data),
  search: (q: string) => api.get("/api/market/search", { params: { q } }).then((r) => r.data),
  news: () => api.get("/api/market/news").then((r) => r.data),
};

export const portfolioApi = {
  get: () => api.get("/api/portfolio").then((r) => r.data),
  addHolding: (data: {
    ticker: string; name: string; quantity: number; avg_cost: number; purchase_date?: string;
  }) => api.post("/api/portfolio/holding", data).then((r) => r.data),
  updateHolding: (id: number, data: { quantity?: number; avg_cost?: number }) =>
    api.put(`/api/portfolio/holding/${id}`, data).then((r) => r.data),
  deleteHolding: (id: number) => api.delete(`/api/portfolio/holding/${id}`).then((r) => r.data),
};

export const watchlistApi = {
  getAll: () => api.get("/api/watchlists").then((r) => r.data),
  create: (name: string) => api.post("/api/watchlists", { name }).then((r) => r.data),
  addItem: (watchlistId: number, ticker: string, name: string) =>
    api.post(`/api/watchlists/${watchlistId}/items`, { ticker, name }).then((r) => r.data),
  removeItem: (watchlistId: number, ticker: string) =>
    api.delete(`/api/watchlists/${watchlistId}/items/${ticker}`).then((r) => r.data),
};

export const alertsApi = {
  getAll: () => api.get("/api/alerts").then((r) => r.data),
  create: (data: {
    ticker: string; condition: string; threshold: number;
    channel_inapp: boolean; channel_email: boolean; channel_push: boolean;
  }) => api.post("/api/alerts", data).then((r) => r.data),
  update: (id: number, data: Record<string, unknown>) =>
    api.put(`/api/alerts/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/api/alerts/${id}`).then((r) => r.data),
  history: () => api.get("/api/alerts/history").then((r) => r.data),
};

export const settingsApi = {
  get: () => api.get("/api/settings").then((r) => r.data),
  update: (data: Record<string, unknown>) => api.put("/api/settings", data).then((r) => r.data),
};

export const analysisApi = {
  get: (ticker: string) => api.get(`/api/analysis/${ticker}`).then((r) => r.data as Promise<Analysis>),
};

export default api;