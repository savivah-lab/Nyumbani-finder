import { useEffect, useState } from "react";

// Render's free tier sleeps after inactivity, so the first request can take ~50s. Say so instead of looking broken.
export default function Loading({ text = "Loading…" }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => { const t = setTimeout(() => setSlow(true), 5000); return () => clearTimeout(t); }, []);
  return (
    <div className="loading">
      <div>
        <div className="spin" />
        <div>{text}</div>
        {slow && <div className="muted" style={{ marginTop: 8, maxWidth: 320 }}>The server is waking up. This can take up to a minute the first time.</div>}
      </div>
    </div>
  );
}
