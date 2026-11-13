import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { HOUSE_TYPES, geocode, kes, myLocation } from "../util";

export default function Home() {
  const nav = useNavigate();
  const { config } = useAuth();
  const [place, setPlace] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!place.trim()) return nav("/search");
    setBusy(true); setErr("");
    try {
      const g = await geocode(place.trim());
      nav(`/search?lat=${g.lat}&lng=${g.lng}&place=${encodeURIComponent(place.trim())}`);
    } catch (e2) { setErr(e2.message); } finally { setBusy(false); }
  };
  const near = async () => {
    setBusy(true); setErr("");
    try { const p = await myLocation(); nav(`/search?lat=${p.lat}&lng=${p.lng}&place=${encodeURIComponent("My location")}`); }
    catch (e2) { setErr(e2.message); } finally { setBusy(false); }
  };

  return (
    <>
      <section className="hero">
        <div className="container">
          <h1>Find a vacant house <span className="gold">near you</span>.<br />No more walking around.</h1>
          <p className="lead">See real photos and the exact location on a map. Search by estate or use your location, then unlock the landlord's number when you find the one.</p>
          <form className="searchbox" onSubmit={submit}>
            <input value={place} onChange={(e) => setPlace(e.target.value)} placeholder="Search an area, e.g. Kilimani, Ruaka, Kasarani" aria-label="Area" />
            <button className="btn" disabled={busy}>{busy ? "Searching…" : "Search"}</button>
            <button type="button" className="btn ghost" onClick={near} disabled={busy}>📍 Near me</button>
          </form>
          {err && <div className="error" style={{ maxWidth: 720, marginTop: 12 }}>{err}</div>}
          <div className="chips">
            {HOUSE_TYPES.map(([v, label]) => <Link key={v} className="chip" to={`/search?house_type=${v}`}>{label}</Link>)}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>How it works for <span className="gold">tenants</span></h2>
          <div className="steps">
            <div className="card step"><div className="n">1</div><h3>Search for free</h3><p className="muted">Browse every vacant house on the map. Photos, rent and exact location are free to see.</p></div>
            <div className="card step"><div className="n">2</div><h3>Pick one you like</h3><p className="muted">Check the pin to see how far it is from work, school or town before you spend anything.</p></div>
            <div className="card step"><div className="n">3</div><h3>Unlock the contact</h3><p className="muted">Pay {kes(config.unlock_fee)} by M-Pesa to see the landlord or caretaker's number. Call and book a viewing.</p></div>
          </div>
        </div>
      </section>

      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="card" style={{ display: "grid", gap: 24, gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", alignItems: "center", borderColor: "var(--line)" }}>
            <div>
              <h2>Landlord or caretaker?</h2>
              <p className="muted">Stop losing weeks to an empty house. Post it with photos and a map pin, and reach people who are actively looking right now.</p>
              <Link to="/register?role=landlord" className="btn">List your house</Link>
            </div>
            <div>
              <div className="price-card"><span>Listing fee ({config.listing_expiry_days} days online)</span><b>{kes(config.listing_fee)}</b></div>
              <div className="price-card"><span>Unlock fee (paid by tenants)</span><b>{kes(config.unlock_fee)}</b></div>
              <div className="price-card"><span>Browsing for tenants</span><b>Free</b></div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
