import { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

const Ctx = createContext(null);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(!getToken());
  const [config, setConfig] = useState({ listing_fee: 250, unlock_fee: 30, listing_expiry_days: 30, mpesa_mode: "mock" });

  useEffect(() => {
    api.get("/config").then(setConfig).catch(() => {});
    if (getToken()) api.get("/auth/me").then(setUser).catch(() => setToken(null)).finally(() => setReady(true));
    const out = () => setUser(null);
    window.addEventListener("nf-logout", out);
    return () => window.removeEventListener("nf-logout", out);
  }, []);

  const finish = (r) => { setToken(r.access_token); setUser(r.user); return r.user; };
  const value = {
    user, ready, config,
    login: async (phone, password) => finish(await api.post("/auth/login", { phone_number: phone, password })),
    register: async (data) => finish(await api.post("/auth/register", data)),
    logout: () => { setToken(null); setUser(null); },
  };
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
