import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth";
import { PinPicker } from "../components/MapView";
import { HOUSE_TYPES, geocode, myLocation, showPhone } from "../util";

const MAX = 8;

export default function PostListing() {
  const { user, config } = useAuth();
  const nav = useNavigate();
  const [f, setF] = useState({ title: "", house_type: "1br", rent_amount: "", area_name: "", description: "", contact_phone: showPhone(user.phone_number).replace(/\s/g, "") });
  const [pin, setPin] = useState(null);
  const [files, setFiles] = useState([]);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [find, setFind] = useState("");
  const previews = useMemo(() => files.map((x) => URL.createObjectURL(x)), [files]);
  useEffect(() => () => previews.forEach(URL.revokeObjectURL), [previews]);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const addFiles = (e) => {
    const next = [...files, ...Array.from(e.target.files)].slice(0, MAX);
    setFiles(next); e.target.value = "";
  };
  const jump = async () => {
    try { const g = await geocode(find); setPin({ lat: g.lat, lng: g.lng }); setErr(""); } catch (e) { setErr(e.message); }
  };
  const here = async () => { try { setPin(await myLocation()); setErr(""); } catch (e) { setErr(e.message); } };

  const submit = async (e) => {
    e.preventDefault(); setErr("");
    if (!pin) return setErr("Tap the map to mark the exact location of the house.");
    if (!files.length) return setErr("Add at least one photo. Houses with photos get far more calls.");
    setBusy(true);
    let created;
    try {
      created = await api.post("/listings", {
        title: f.title.trim(), house_type: f.house_type, rent_amount: parseFloat(f.rent_amount), area_name: f.area_name.trim() || null,
        description: f.description.trim() || null, latitude: pin.lat, longitude: pin.lng, contact_phone: f.contact_phone,
      });
      const form = new FormData();
      files.forEach((x) => form.append("files", x));
      await api.upload(`/listings/${created.id}/photos`, form);
      nav(`/dashboard?pay=${created.id}`);
    } catch (e2) {
      setErr(e2.message + (created ? " Your draft was saved. Open My listings to add photos." : ""));
      if (created) setTimeout(() => nav("/dashboard"), 2500);
    } finally { setBusy(false); }
  };

  return (
    <div className="container" style={{ maxWidth: 780 }}>
      <h1 style={{ fontSize: "2rem" }}>Post a vacant house</h1>
      <p className="muted">Fill in the details, mark the spot on the map and add photos. You'll pay the listing fee of KES {config.listing_fee} to publish for {config.listing_expiry_days} days.</p>
      {err && <div className="error">{err}</div>}
      <form onSubmit={submit}>
        <div className="card" style={{ marginBottom: 18 }}>
          <div className="field"><label htmlFor="f-listing-title">Listing title</label><input id="f-listing-title" value={f.title} onChange={set("title")} placeholder="e.g. Spacious 1 bedroom near Yaya Centre" required minLength={5} maxLength={150} /></div>
          <div className="row">
            <div className="field"><label htmlFor="f-house-type">House type</label><select id="f-house-type" value={f.house_type} onChange={set("house_type")}>{HOUSE_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
            <div className="field"><label htmlFor="f-monthly-rent-kes">Monthly rent (KES)</label><input id="f-monthly-rent-kes" type="number" min="1" value={f.rent_amount} onChange={set("rent_amount")} required /></div>
          </div>
          <div className="row">
            <div className="field"><label htmlFor="f-estate-area">Estate / area</label><input id="f-estate-area" value={f.area_name} onChange={set("area_name")} placeholder="e.g. Kilimani" maxLength={120} /></div>
            <div className="field"><label htmlFor="f-phone-number-tenants-will-call">Phone number tenants will call</label><input id="f-phone-number-tenants-will-call" value={f.contact_phone} onChange={set("contact_phone")} inputMode="tel" required /></div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}><label htmlFor="f-description-water-parking-security-deposit">Description (water, parking, security, deposit…)</label><textarea id="f-description-water-parking-security-deposit" value={f.description} onChange={set("description")} maxLength={2000} /></div>
        </div>

        <div className="card" style={{ marginBottom: 18 }}>
          <h3>Exact location</h3>
          <p className="muted" style={{ marginTop: 0 }}>Tap the map where the house is. You can drag the pin to adjust it.</p>
          <div style={{ display: "flex", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
            <input style={{ flex: "1 1 200px" }} value={find} onChange={(e) => setFind(e.target.value)} placeholder="Jump to an area…" onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), jump())} />
            <button type="button" className="btn ghost sm" onClick={jump}>Go</button>
            <button type="button" className="btn ghost sm" onClick={here}>📍 I'm at the house</button>
          </div>
          <PinPicker value={pin} onChange={setPin} />
          <p className="muted" style={{ marginBottom: 0 }}>{pin ? `Pin set (${pin.lat.toFixed(5)}, ${pin.lng.toFixed(5)})` : "No pin yet."}</p>
        </div>

        <div className="card" style={{ marginBottom: 18 }}>
          <h3>Photos <span className="muted" style={{ fontWeight: 400 }}>({files.length}/{MAX})</span></h3>
          <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={addFiles} disabled={files.length >= MAX} />
          <div className="previews">{previews.map((u, i) => <div key={u} style={{ backgroundImage: `url(${u})` }} title="Click to remove" onClick={() => setFiles(files.filter((_, j) => j !== i))} />)}</div>
          {files.length > 0 && <p className="muted" style={{ marginBottom: 0, fontSize: ".85rem" }}>Click a photo to remove it. JPEG, PNG or WebP, up to 5MB each.</p>}
        </div>

        <button className="btn block" disabled={busy}>{busy ? "Saving & uploading photos…" : "Save and continue to payment"}</button>
      </form>
    </div>
  );
}
