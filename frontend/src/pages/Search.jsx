import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, qs } from "../api";
import ListingCard from "../components/ListingCard";
import Loading from "../components/Loading";
import { ResultsMap } from "../components/MapView";
import { HOUSE_TYPES, NAIROBI, geocode, myLocation } from "../util";

const LIMIT = 20;

export default function Search() {
  const [sp, setSp] = useSearchParams();
  const p = Object.fromEntries(sp.entries());
  const [form, setForm] = useState({ place: p.place || "", house_type: p.house_type || "", min_price: p.min_price || "", max_price: p.max_price || "" });
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [active, setActive] = useState(null);
  const [view, setView] = useState("list");

  const hasGeo = p.lat && p.lng;
  const query = { lat: p.lat, lng: p.lng, radius_km: p.radius_km || (hasGeo ? 5 : ""), house_type: p.house_type, min_price: p.min_price, max_price: p.max_price };

  const load = async (offset = 0) => {
    setLoading(true); setError("");
    try {
      const r = await api.get("/listings" + qs({ ...query, limit: LIMIT, offset }));
      setItems((prev) => (offset ? [...prev, ...r.items] : r.items)); setTotal(r.total);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  };
  useEffect(() => { load(0); }, [sp.toString()]); // eslint-disable-line

  const submit = async (e) => {
    e.preventDefault(); setError("");
    const next = { house_type: form.house_type, min_price: form.min_price, max_price: form.max_price };
    try {
      if (form.place.trim()) {
        if (form.place === "My location" && hasGeo) { next.lat = p.lat; next.lng = p.lng; }
        else { const g = await geocode(form.place.trim()); next.lat = g.lat; next.lng = g.lng; }
        next.place = form.place.trim();
      }
      if (p.radius_km) next.radius_km = p.radius_km;
      setSp(Object.fromEntries(Object.entries(next).filter(([, v]) => v)));
    } catch (e2) { setError(e2.message); }
  };
  const near = async () => {
    try { const g = await myLocation(); setForm({ ...form, place: "My location" }); setSp({ lat: g.lat, lng: g.lng, place: "My location", ...(form.house_type && { house_type: form.house_type }) }); }
    catch (e2) { setError(e2.message); }
  };
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const center = hasGeo ? [parseFloat(p.lat), parseFloat(p.lng)] : NAIROBI;

  return (
    <div className="container">
      <form className="filters" onSubmit={submit}>
        <div className="wide"><label htmlFor="f-area">Area</label><input id="f-area" value={form.place} onChange={set("place")} placeholder="e.g. Kilimani, Juja, Nyali" /></div>
        <div className="wide"><label htmlFor="f-type">Type</label>
          <select id="f-type" value={form.house_type} onChange={set("house_type")}><option value="">Any</option>{HOUSE_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select></div>
        <div><label htmlFor="f-min-rent">Min rent</label><input id="f-min-rent" type="number" min="0" value={form.min_price} onChange={set("min_price")} placeholder="0" /></div>
        <div><label htmlFor="f-max-rent">Max rent</label><input id="f-max-rent" type="number" min="0" value={form.max_price} onChange={set("max_price")} placeholder="Any" /></div>
        <div className="wide" style={{ display: "flex", gap: 8 }}><button className="btn" style={{ flex: 1 }}>Search</button><button type="button" className="btn ghost" onClick={near} title="Use my location">📍</button></div>
      </form>

      {error && <div className="error">{error}</div>}
      <div className="tabs">
        <button className={"btn sm " + (view === "list" ? "" : "ghost")} onClick={() => setView("list")}>List</button>
        <button className={"btn sm " + (view === "map" ? "" : "ghost")} onClick={() => setView("map")}>Map</button>
      </div>
      <p className="muted" style={{ margin: "0 0 12px" }}>
        {loading && !items.length ? "Searching…" : `${total} vacant ${total === 1 ? "house" : "houses"}${hasGeo ? ` within ${p.radius_km || 5} km of ${p.place || "this spot"}` : ""}`}
      </p>

      <div className={"split show-" + view}>
        <div>
          {loading && !items.length ? <Loading text="Finding houses…" /> : (
            <>
              <div className="list">
                {items.map((l) => <ListingCard key={l.id} l={l} active={active === l.id} onHover={setActive} />)}
              </div>
              {!loading && !items.length && (
                <div className="card center">
                  <h3>No vacant houses found here yet</h3>
                  <p className="muted">Try a wider area or remove a filter.{hasGeo && " "}</p>
                  {hasGeo && <button className="btn sm" onClick={() => setSp({ ...p, radius_km: 20 })}>Search within 20 km</button>}
                </div>
              )}
              {items.length < total && (
                <div className="center more" style={{ marginTop: 20 }}>
                  <button className="btn ghost" disabled={loading} onClick={() => load(items.length)}>{loading ? "Loading…" : "Load more"}</button>
                </div>
              )}
            </>
          )}
        </div>
        <div className="mapwrap">
          <ResultsMap items={items} activeId={active} center={center} visible={view === "map"} onPick={(id) => { setActive(id); document.querySelector(".lcard.active")?.scrollIntoView({ block: "center", behavior: "smooth" }); }} />
        </div>
      </div>
    </div>
  );
}
