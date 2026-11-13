const BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

let token = null;
try { token = localStorage.getItem("nf_token"); } catch {}
export const getToken = () => token;
export const setToken = (t) => {
  token = t;
  try { t ? localStorage.setItem("nf_token", t) : localStorage.removeItem("nf_token"); } catch {}
};

export class ApiError extends Error {
  constructor(message, status) { super(message); this.status = status; }
}

function message(detail) {
  if (!detail) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => (d.msg || "").replace(/^Value error, /, "")).filter(Boolean).join(". ");
  return "Something went wrong. Please try again.";
}

async function req(path, { method = "GET", body, form } = {}) {
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
  let res;
  try {
    res = await fetch(`${BASE}/api${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError("Can't reach the server. Check your connection and try again.", 0);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401 && token) { setToken(null); window.dispatchEvent(new Event("nf-logout")); }
    throw new ApiError(message(data?.detail), res.status);
  }
  return data;
}

export const api = {
  get: (p) => req(p),
  post: (p, b) => req(p, { method: "POST", body: b ?? {} }),
  patch: (p, b) => req(p, { method: "PATCH", body: b }),
  upload: (p, form) => req(p, { method: "POST", form }),
};

export const qs = (obj) => {
  const p = new URLSearchParams();
  Object.entries(obj).forEach(([k, v]) => { if (v !== null && v !== undefined && v !== "") p.set(k, v); });
  const s = p.toString();
  return s ? `?${s}` : "";
};

// Uploaded photos are absolute (Cloudinary) in production, relative (/uploads/..) in local dev.
export const imgUrl = (u) => (!u ? "" : u.startsWith("http") ? u : BASE + u);
