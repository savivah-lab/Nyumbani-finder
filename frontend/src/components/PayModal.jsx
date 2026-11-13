import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { kes, showPhone } from "../util";

/**
 * Generic M-Pesa payment flow: confirm number -> STK push -> poll until paid.
 * `start(phone)` must call the backend and resolve to { payment, already_unlocked }.
 */
export default function PayModal({ title, amount, defaultPhone, start, onDone, onClose }) {
  const { config } = useAuth();
  const [phone, setPhone] = useState(showPhone(defaultPhone).replace(/\s/g, ""));
  const [stage, setStage] = useState("form"); // form | waiting | success | failed
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearInterval(timer.current), []);

  const poll = (id) => {
    let n = 0;
    clearInterval(timer.current);
    timer.current = setInterval(async () => {
      n++;
      try {
        const p = await api.get(`/payments/${id}`);
        if (p.status !== "pending") { clearInterval(timer.current); setPayment(p); setStage(p.status === "success" ? "success" : "failed"); }
      } catch { /* keep polling */ }
      if (n > 60) clearInterval(timer.current);
    }, 3000);
  };

  const go = async () => {
    setBusy(true); setError("");
    try {
      const r = await start(phone);
      if (r.already_unlocked) return setStage("success");
      setPayment(r.payment); setStage("waiting"); poll(r.payment.id);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const simulate = async (ok) => {
    try {
      const p = await api.post(`/payments/mock/${payment.id}/complete?success=${ok}`);
      clearInterval(timer.current); setPayment(p); setStage(p.status === "success" ? "success" : "failed");
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="overlay" onClick={(e) => e.target === e.currentTarget && stage !== "waiting" && onClose()}>
      <div className="modal">
        <h3>{title}</h3>
        {stage === "form" && (
          <>
            <p className="muted">You'll pay <b style={{ color: "var(--gold-hi)" }}>{kes(amount)}</b> by M-Pesa. We'll send a prompt to your phone.</p>
            {error && <div className="error">{error}</div>}
            <div className="field">
              <label htmlFor="f-m-pesa-phone-number">M-Pesa phone number</label>
              <input id="f-m-pesa-phone-number" value={phone} onChange={(e) => setPhone(e.target.value)} inputMode="tel" placeholder="0712 345 678" />
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn" onClick={go} disabled={busy || phone.length < 9}>{busy ? "Sending…" : `Pay ${kes(amount)}`}</button>
              <button className="btn ghost" onClick={onClose}>Cancel</button>
            </div>
          </>
        )}
        {stage === "waiting" && (
          <div className="center">
            <div className="spin" />
            <p><b>Check your phone</b> and enter your M-Pesa PIN.<br /><span className="muted">Waiting for confirmation…</span></p>
            {error && <div className="error">{error}</div>}
            {config.mpesa_mode === "mock" && (
              <div className="notice" style={{ textAlign: "left" }}>
                <b>Test mode:</b> no real money moves. Simulate the customer's response:
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button className="btn sm" onClick={() => simulate(true)}>Enter PIN (success)</button>
                  <button className="btn sm ghost" onClick={() => simulate(false)}>Cancel</button>
                </div>
              </div>
            )}
          </div>
        )}
        {stage === "success" && (
          <div className="center">
            <div style={{ fontSize: "2.4rem" }}>✅</div>
            <p><b>Payment received.</b>{payment?.mpesa_receipt && <><br /><span className="muted">M-Pesa receipt {payment.mpesa_receipt}</span></>}</p>
            <button className="btn block" onClick={onDone}>Continue</button>
          </div>
        )}
        {stage === "failed" && (
          <div className="center">
            <div style={{ fontSize: "2.4rem" }}>⚠️</div>
            <p><b>Payment didn't go through.</b><br /><span className="muted">{payment?.failure_reason || "The request was cancelled or timed out."} You have not been charged.</span></p>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn" onClick={() => { setStage("form"); setError(""); }}>Try again</button>
              <button className="btn ghost" onClick={onClose}>Close</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
