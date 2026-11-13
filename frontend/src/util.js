export const kes = (n) => "KES " + Number(n).toLocaleString("en-KE", { maximumFractionDigits: 0 });

// 254712345678 -> 0712 345 678
export const showPhone = (p) => {
  if (!p) return "";
  const d = p.startsWith("254") ? "0" + p.slice(3) : p;
  return d.length === 10 ? `${d.slice(0, 4)} ${d.slice(4, 7)} ${d.slice(7)}` : d;
};

export const HOUSE_TYPES = [
  ["single_room", "Single room"], ["bedsitter", "Bedsitter"], ["studio", "Studio"],
  ["1br", "1 bedroom"], ["2br", "2 bedrooms"], ["3br", "3 bedrooms"], ["maisonette", "Maisonette"],
];
export const typeLabel = (t) => (HOUSE_TYPES.find(([v]) => v === t) || [t, t])[1];

export const NAIROBI = [-1.2921, 36.8219];

// Free OpenStreetMap geocoder. Fine for MVP search; use a paid geocoder at scale.
export async function geocode(place) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=ke&q=${encodeURIComponent(place)}`;
  const r = await fetch(url, { headers: { Accept: "application/json" } });
  const j = await r.json();
  if (!j.length) throw new Error(`We couldn't find "${place}". Try a nearby estate or town name.`);
  return { lat: parseFloat(j[0].lat), lng: parseFloat(j[0].lon), name: j[0].display_name.split(",")[0] };
}

export const myLocation = () =>
  new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error("Your browser doesn't support location."));
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => reject(new Error("Couldn't get your location. Allow location access or type an area instead.")),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  });
