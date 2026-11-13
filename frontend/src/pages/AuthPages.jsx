import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth";

function useDone() {
  const [sp] = useSearchParams();
  const nav = useNavigate();
  return (user) => {
    const next = sp.get("next");
    nav(next && next.startsWith("/") ? next : ["landlord", "admin"].includes(user.role) ? "/dashboard" : "/search", { replace: true });
  };
}

export function Login() {
  const { login } = useAuth();
  const done = useDone();
  const [f, setF] = useState({ phone: "", password: "" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { done(await login(f.phone, f.password)); } catch (e2) { setErr(e2.message); } finally { setBusy(false); }
  };
  return (
    <div className="container"><div className="card auth">
      <h2>Welcome back</h2>
      {err && <div className="error">{err}</div>}
      <form onSubmit={submit}>
        <div className="field"><label htmlFor="f-phone-number">Phone number</label><input id="f-phone-number" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} inputMode="tel" placeholder="0712 345 678" required autoComplete="tel" /></div>
        <div className="field"><label htmlFor="f-password">Password</label><input id="f-password" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required autoComplete="current-password" /></div>
        <button className="btn block" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
      </form>
      <p className="muted center" style={{ marginBottom: 0 }}>New here? <Link to={"/register" + window.location.search}>Create an account</Link></p>
    </div></div>
  );
}

export function Register() {
  const { register } = useAuth();
  const done = useDone();
  const [sp] = useSearchParams();
  const [f, setF] = useState({ phone: "", full_name: "", password: "", role: sp.get("role") === "landlord" ? "landlord" : "tenant" });
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { done(await register({ phone_number: f.phone, full_name: f.full_name, password: f.password, role: f.role })); }
    catch (e2) { setErr(e2.message); } finally { setBusy(false); }
  };
  return (
    <div className="container"><div className="card auth">
      <h2>Create your account</h2>
      {err && <div className="error">{err}</div>}
      <div className="seg">
        <button type="button" className={f.role === "tenant" ? "on" : ""} onClick={() => setF({ ...f, role: "tenant" })}>🔎 I'm looking for a house</button>
        <button type="button" className={f.role === "landlord" ? "on" : ""} onClick={() => setF({ ...f, role: "landlord" })}>🏠 I'm a landlord / caretaker</button>
      </div>
      <form onSubmit={submit}>
        <div className="field"><label htmlFor="f-full-name">Full name</label><input id="f-full-name" value={f.full_name} onChange={(e) => setF({ ...f, full_name: e.target.value })} required minLength={2} autoComplete="name" /></div>
        <div className="field"><label htmlFor="f-phone-number-m-pesa">Phone number (M-Pesa)</label><input id="f-phone-number-m-pesa" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} inputMode="tel" placeholder="0712 345 678" required autoComplete="tel" /></div>
        <div className="field"><label htmlFor="f-password-min-8-characters">Password (min 8 characters)</label><input id="f-password-min-8-characters" type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} required minLength={8} maxLength={72} autoComplete="new-password" /></div>
        <button className="btn block" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
      </form>
      <p className="muted center" style={{ marginBottom: 0 }}>Already have an account? <Link to={"/login" + window.location.search}>Log in</Link></p>
    </div></div>
  );
}
