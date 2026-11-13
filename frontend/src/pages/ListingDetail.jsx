import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, imgUrl } from "../api";
import { useAuth } from "../auth";
import Loading from "../components/Loading";
import { LockIcon } from "../components/ListingCard";
import { SingleMap } from "../components/MapView";
import PayModal from "../components/PayModal";
import { kes, showPhone, typeLabel } from "../util";

const REASONS = [["already_rented", "Already rented"], ["wrong_location", "Wrong location"], ["fake", "Fake / scam"], ["unreachable_number", "Number doesn't work"], ["other", "Other"]];

export default function ListingDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { user, config } = useAuth();
  const [l, setL] = useState(null);
  const [err, setErr] = useState("");
  const [idx, setIdx] = useState(0);
  const [paying, setPaying] = useState(false);
  const [reporting, setReporting] = useState(false);
  const [report, setReport] = useState({ reason: "already_rented", notes: "" });
  const [msg, setMsg] = useState("");

  const load = () => api.get(`/listings/${id}`).then(setL).catch((e) => setErr(e.message));
  useEffect(() => { setL(null); load(); }, [id]); // eslint-disable-line

  if (err) return <div className="container"><div className="error">{err}</div><Link to="/search">← Back to search</Link></div>;
  if (!l) return <Loading />;

  const wantUnlock = () => (user ? setPaying(true) : nav(`/login?next=${encodeURIComponent(`/listing/${id}`)}`));
  const sendReport = async () => {
    try { await api.post(`/listings/${id}/flag`, report); setReporting(false); setMsg("Thanks for reporting. We'll look into it."); }
    catch (e) { setErr(e.message); setReporting(false); }
  };

  return (
    <div className="container">
      <p><Link to="/search">← Back to search</Link></p>
      {msg && <div className="ok">{msg}</div>}
      {l.status !== "active" && <div className="notice" style={{ marginBottom: 14 }}>This listing is <b>{l.status.replace("_", " ")}</b> and is only visible to you.</div>}
      <div className="detail">
        <div>
          <div className="gallery">
            <div className="main" style={l.photos[idx] ? { backgroundImage: `url(${imgUrl(l.photos[idx])})` } : undefined} />
            {l.photos.length > 1 && (
              <div className="thumbs">
                {l.photos.map((u, i) => <button key={u} className={i === idx ? "on" : ""} style={{ backgroundImage: `url(${imgUrl(u)})` }} onClick={() => setIdx(i)} aria-label={`Photo ${i + 1}`} />)}
              </div>
            )}
          </div>
          <h1 style={{ fontSize: "1.9rem", marginTop: 22 }}>{l.title}</h1>
          <div className="facts"><span className="tag">{typeLabel(l.house_type)}</span><span className="badge">{l.area_name || "Nairobi"}</span></div>
          {l.description && <p style={{ whiteSpace: "pre-wrap", color: "#c3c9d8" }}>{l.description}</p>}
          <h3 style={{ marginTop: 26 }}>Exact location</h3>
          <SingleMap lat={l.latitude} lng={l.longitude} />
          <p style={{ marginTop: 10 }}><a target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${l.latitude},${l.longitude}`}>Get directions ↗</a></p>
        </div>

        <aside>
          <div className="card contact" style={{ position: "sticky", top: 84 }}>
            <div className="price" style={{ fontSize: "1.8rem" }}>{kes(l.rent_amount)} <small>/ month</small></div>
            <hr style={{ border: 0, borderTop: "1px solid var(--line2)", margin: "16px 0" }} />
            {l.contact_unlocked ? (
              <>
                <label>Landlord / caretaker</label>
                <div className="phone">{showPhone(l.contact_phone)}</div>
                <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap" }}>
                  <a className="btn" href={`tel:+${l.contact_phone}`}>📞 Call</a>
                  <a className="btn ghost" target="_blank" rel="noreferrer" href={`https://wa.me/${l.contact_phone}?text=${encodeURIComponent(`Hi, I saw "${l.title}" on Nyumbani Finder. Is it still available?`)}`}>WhatsApp</a>
                </div>
              </>
            ) : (
              <>
                <label><LockIcon /> Landlord / caretaker number</label>
                <div className="phone locked" aria-hidden>{l.contact_phone}</div>
                <p className="muted" style={{ fontSize: ".9rem" }}>Pay once to see the number. You won't be charged again for this house.</p>
                <button className="btn block" onClick={wantUnlock}>Unlock contact · {kes(config.unlock_fee)}</button>
                {!user && <p className="muted center" style={{ fontSize: ".85rem", marginBottom: 0 }}>You'll be asked to log in first.</p>}
              </>
            )}
            {user && l.status === "active" && user.role === "tenant" && (
              <button className="btn ghost sm block" style={{ marginTop: 16 }} onClick={() => setReporting(true)}>Report a problem with this listing</button>
            )}
          </div>
        </aside>
      </div>

      {paying && (
        <PayModal title="Unlock contact" amount={config.unlock_fee} defaultPhone={user.phone_number}
          start={(phone) => api.post(`/payments/unlock/${l.id}`, { phone_number: phone })}
          onDone={() => { setPaying(false); load(); }} onClose={() => setPaying(false)} />
      )}
      {reporting && (
        <div className="overlay" onClick={(e) => e.target === e.currentTarget && setReporting(false)}>
          <div className="modal">
            <h3>Report this listing</h3>
            <div className="field"><label htmlFor="f-what-s-wrong">What's wrong?</label>
              <select id="f-what-s-wrong" value={report.reason} onChange={(e) => setReport({ ...report, reason: e.target.value })}>{REASONS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></div>
            <div className="field"><label htmlFor="f-details-optional">Details (optional)</label><textarea id="f-details-optional" value={report.notes} onChange={(e) => setReport({ ...report, notes: e.target.value })} /></div>
            <div style={{ display: "flex", gap: 10 }}><button className="btn" onClick={sendReport}>Send report</button><button className="btn ghost" onClick={() => setReporting(false)}>Cancel</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
