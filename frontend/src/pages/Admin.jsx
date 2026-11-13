import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import Loading from "../components/Loading";
import { kes } from "../util";

const STATUSES = ["under_review", "pending", "active", "expired", "rented", "removed"];

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [status, setStatus] = useState("under_review");
  const [rows, setRows] = useState(null);
  const [flags, setFlags] = useState({});
  const [err, setErr] = useState("");

  const loadStats = () => api.get("/admin/stats").then(setStats).catch((e) => setErr(e.message));
  const loadRows = () => { setRows(null); api.get(`/admin/listings?status=${status}`).then(setRows).catch((e) => setErr(e.message)); };
  useEffect(() => { loadStats(); }, []);
  useEffect(loadRows, [status]); // eslint-disable-line

  const change = async (l, s) => { try { await api.post(`/admin/listings/${l.id}/status?status=${s}`); loadRows(); loadStats(); } catch (e) { setErr(e.message); } };
  const showFlags = async (l) => setFlags({ ...flags, [l.id]: await api.get(`/admin/listings/${l.id}/flags`) });

  return (
    <div className="container">
      <h1 style={{ fontSize: "2rem" }}>Admin</h1>
      {err && <div className="error">{err}</div>}
      {stats && (
        <div className="stats">
          <div className="card stat"><b>{stats.users}</b><span className="muted">Users</span></div>
          <div className="card stat"><b>{stats.listings_by_status.active || 0}</b><span className="muted">Live listings</span></div>
          <div className="card stat"><b>{kes(stats.revenue_kes.listing_fees)}</b><span className="muted">Listing fees collected</span></div>
          <div className="card stat"><b>{kes(stats.revenue_kes.unlock_fees)}</b><span className="muted">Unlock fees collected</span></div>
        </div>
      )}
      <div className="chips" style={{ marginBottom: 16 }}>
        {STATUSES.map((s) => <button key={s} className={"chip"} style={s === status ? { borderColor: "var(--gold)", color: "var(--gold-hi)" } : {}} onClick={() => setStatus(s)}>{s.replace("_", " ")} {stats?.listings_by_status[s] ? `(${stats.listings_by_status[s]})` : ""}</button>)}
      </div>
      {!rows ? <Loading /> : rows.length === 0 ? <p className="muted">Nothing here.</p> : rows.map((l) => (
        <div className="card" key={l.id} style={{ marginBottom: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div><Link to={`/listing/${l.id}`} style={{ fontWeight: 700 }}>{l.title}</Link><div className="muted">{l.area_name} · {kes(l.rent_amount)} · contact {l.contact_phone}</div></div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn ghost sm" onClick={() => showFlags(l)}>View reports</button>
              {l.status !== "active" && <button className="btn sm" onClick={() => change(l, "active")}>Restore</button>}
              {l.status !== "removed" && <button className="btn danger sm" onClick={() => change(l, "removed")}>Remove</button>}
            </div>
          </div>
          {flags[l.id] && <ul className="muted">{flags[l.id].length ? flags[l.id].map((f, i) => <li key={i}>{String(f.reason).replace("_", " ")}{f.notes && ` - ${f.notes}`}</li>) : <li>No reports</li>}</ul>}
        </div>
      ))}
    </div>
  );
}
