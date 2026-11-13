import { Link } from "react-router-dom";
import { imgUrl } from "../api";
import { kes, typeLabel } from "../util";

export const LockIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="11" width="16" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
);

export default function ListingCard({ l, active, onHover }) {
  return (
    <Link to={`/listing/${l.id}`} className={"lcard" + (active ? " active" : "")} onMouseEnter={() => onHover?.(l.id)} onMouseLeave={() => onHover?.(null)}>
      <div className="ph" style={l.photos[0] ? { backgroundImage: `url(${imgUrl(l.photos[0])})` } : undefined}>
        <span className="tag">{typeLabel(l.house_type)}</span>
      </div>
      <div className="bd">
        <div className="price">{kes(l.rent_amount)} <small>/ month</small></div>
        <div style={{ fontWeight: 600, margin: "2px 0" }}>{l.title}</div>
        <div className="muted" style={{ fontSize: ".9rem" }}>
          {l.area_name || "Nairobi"}{l.distance_km != null && ` · ${l.distance_km} km away`}
        </div>
        {!l.contact_unlocked && <div className="lock"><LockIcon /> Contact locked</div>}
      </div>
    </Link>
  );
}
