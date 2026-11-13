import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, imgUrl } from "../api";
import { useAuth } from "../auth";
import Loading from "../components/Loading";
import PayModal from "../components/PayModal";
import { kes, typeLabel } from "../util";

const STATUS_HELP = {
  pending: "Not live yet. Pay the listing fee to publish.",
  active: "Live and visible to tenants.",
  expired: "Listing period ended. Relist to put it back online.",
  under_review: "Hidden while we check reports from tenants.",
  rented: "Marked as rented.",
  removed: "Removed.",
};

export default function Dashboard() {
  const { user, config } = useAuth();
  const [sp, setSp] = useSearchParams();
  const [items, setItems] = useState(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [paying, setPaying] = useState(null);
  const fileRef = useRef(null);
  const [uploadFor, setUploadFor] = useState(null);

  const load = () => api.get("/listings/mine").then(setItems).catch((e) => setErr(e.message));
  useEffect(() => { load(); }, []);
  useEffect(() => {
    const id = sp.get("pay");
    if (id && items) { const l = items.find((x) => String(x.id) === id); if (l && ["pending", "expired"].includes(l.status)) setPaying(l); }
  }, [items]); // eslint-disable-line

  const setStatus = async (l, status) => {
    if (!confirm(status === "rented" ? "Mark this house as rented? It will be taken off the search." : "Remove this listing?")) return;
    try { await api.patch(`/listings/${l.id}`, { status }); load(); } catch (e) { setErr(e.message); }
  };
  const onFiles = async (e) => {
    const files = Array.from(e.target.files); e.target.value = "";
    if (!files.length || !uploadFor) return;
    const form = new FormData(); files.forEach((f) => form.append("files", f));
    try { await api.upload(`/listings/${uploadFor}/photos`, form); setMsg("Photos added."); load(); } catch (e2) { setErr(e2.message); }
  };
  const closePay = () => { setPaying(null); if (sp.get("pay")) { sp.delete("pay"); setSp(sp, { replace: true }); } };

  if (!items && !err) return <Loading />;
  const live = (items || []).filter((l) => l.status === "active").length;

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12, marginBottom: 18 }}>
        <div><h1 style={{ fontSize: "2rem", marginBottom: 4 }}>My listings</h1><span className="muted">Hello {user.full_name.split(" ")[0]} 👋</span></div>
        <Link className="btn" to="/post">+ Post a house</Link>
      </div>
      {err && <div className="error">{err}</div>}
      {msg && <div className="ok">{msg}</div>}
      <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" multiple hidden onChange={onFiles} />

      <div className="stats">
        <div className="card stat"><b>{items?.length || 0}</b><span className="muted">Total listings</span></div>
        <div className="card stat"><b>{live}</b><span className="muted">Live now</span></div>
      </div>

      {items?.length === 0 && (
        <div className="card center"><h3>You haven't posted a house yet</h3><p className="muted">Post your first vacant house and reach people searching right now.</p><Link className="btn" to="/post">Post a house</Link></div>
      )}

      {items?.map((l) => (
        <div className="lrow" key={l.id}>
          <div className="th" style={l.photos[0] ? { backgroundImage: `url(${imgUrl(l.photos[0])})` } : undefined} />
          <div>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <Link to={`/listing/${l.id}`} style={{ fontWeight: 700, color: "var(--text)" }}>{l.title}</Link>
              <span className={"badge " + l.status}>{l.status.replace("_", " ")}</span>
            </div>
            <div className="muted" style={{ fontSize: ".9rem" }}>{typeLabel(l.house_type)} · {kes(l.rent_amount)}/mo · {l.photos.length} photo{l.photos.length === 1 ? "" : "s"}{l.status === "active" && l.expires_at && ` · expires ${new Date(l.expires_at).toLocaleDateString()}`}</div>
            <div className="muted" style={{ fontSize: ".82rem" }}>{STATUS_HELP[l.status]}</div>
          </div>
          <div className="acts">
            {["pending", "expired"].includes(l.status) && (
              l.photos.length
                ? <button className="btn sm" onClick={() => setPaying(l)}>{l.status === "expired" ? "Relist" : "Publish"} · {kes(config.listing_fee)}</button>
                : <span className="muted" style={{ fontSize: ".85rem", alignSelf: "center" }}>Add a photo to publish</span>
            )}
            {!["removed", "rented"].includes(l.status) && <button className="btn ghost sm" onClick={() => { setUploadFor(l.id); fileRef.current.click(); }}>+ Photos</button>}
            {l.status === "active" && <button className="btn ghost sm" onClick={() => setStatus(l, "rented")}>Mark rented</button>}
            {!["removed", "rented"].includes(l.status) && <button className="btn danger sm" onClick={() => setStatus(l, "removed")}>Remove</button>}
          </div>
        </div>
      ))}

      {paying && (
        <PayModal title={paying.status === "expired" ? "Relist your house" : "Publish your house"} amount={config.listing_fee} defaultPhone={user.phone_number}
          start={(phone) => api.post(`/payments/listing-fee/${paying.id}`, { phone_number: phone })}
          onDone={() => { closePay(); setMsg("Your house is now live! 🎉"); load(); }} onClose={closePay} />
      )}
    </div>
  );
}
