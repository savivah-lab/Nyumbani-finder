import { useEffect } from "react";
import L from "leaflet";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { NAIROBI } from "../util";

const TILES = import.meta.env.VITE_MAP_TILES_URL || "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const DARK = import.meta.env.VITE_MAP_TILES_DARK === "true";
const ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

const pin = (active) => L.divIcon({ className: "pin" + (active ? " pin-active" : ""), html: "<span></span>", iconSize: [26, 34], iconAnchor: [13, 32] });

function Fit({ points, center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [40, 40], maxZoom: 16 });
    else if (points.length === 1) map.setView(points[0], 16);
    else map.setView(center, zoom);
  }, [JSON.stringify(points), center[0], center[1], zoom]); // eslint-disable-line
  return null;
}

function Resize({ visible }) {
  const map = useMap();
  useEffect(() => { const t = setTimeout(() => map.invalidateSize(), 150); return () => clearTimeout(t); }, [visible, map]);
  return null;
}

export function ResultsMap({ items, activeId, onPick, center = NAIROBI, visible = true }) {
  const points = items.map((l) => [l.latitude, l.longitude]);
  return (
    <MapContainer center={center} zoom={12} className={DARK ? "" : "dark-tiles"} style={{ height: "100%", width: "100%" }} scrollWheelZoom>
      <TileLayer url={TILES} attribution={ATTR} />
      <Fit points={points} center={center} zoom={12} />
      <Resize visible={visible} />
      {items.map((l) => (
        <Marker key={l.id} position={[l.latitude, l.longitude]} icon={pin(l.id === activeId)} eventHandlers={{ click: () => onPick?.(l.id) }} />
      ))}
    </MapContainer>
  );
}

export function SingleMap({ lat, lng }) {
  return (
    <div style={{ height: 300, borderRadius: 12, overflow: "hidden", border: "1px solid var(--line)" }}>
      <MapContainer center={[lat, lng]} zoom={16} className={DARK ? "" : "dark-tiles"} style={{ height: "100%" }} scrollWheelZoom={false}>
        <TileLayer url={TILES} attribution={ATTR} />
        <Marker position={[lat, lng]} icon={pin(true)} />
      </MapContainer>
    </div>
  );
}

function Clicker({ onChange }) {
  useMapEvents({ click: (e) => onChange({ lat: e.latlng.lat, lng: e.latlng.lng }) });
  return null;
}

function Follow({ value }) {
  const map = useMap();
  useEffect(() => { if (value) map.setView([value.lat, value.lng], Math.max(map.getZoom(), 16)); }, [value?.lat, value?.lng]); // eslint-disable-line
  return null;
}

// Landlord taps the map (or drags the pin) to mark the exact house location.
export function PinPicker({ value, onChange }) {
  return (
    <div className={"picker" + (DARK ? "" : " dark-tiles")}>
      <MapContainer center={value ? [value.lat, value.lng] : NAIROBI} zoom={value ? 16 : 12} style={{ height: "100%" }}>
        <TileLayer url={TILES} attribution={ATTR} />
        <Clicker onChange={onChange} />
        <Follow value={value} />
        {value && (
          <Marker position={[value.lat, value.lng]} icon={pin(true)} draggable
            eventHandlers={{ dragend: (e) => { const p = e.target.getLatLng(); onChange({ lat: p.lat, lng: p.lng }); } }} />
        )}
      </MapContainer>
    </div>
  );
}
