import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="ftr">
      <div className="container ftr-in">
        <div>
          <img src="/logo.webp" alt="Savivah Netcore Technologies Limited" />
        </div>
        <div>
          <b>Nyumbani Finder</b><br />
          <small>Find vacant rental houses near you, with photos and the exact location.</small><br />
          <small><Link to="/search">Find a house</Link> · <Link to="/register">List your house</Link></small>
        </div>
        <small>© {new Date().getFullYear()} Savivah Netcore Technologies Limited.<br />Nyumbani Finder is a product of Savivah Netcore Technologies Limited.</small>
      </div>
    </footer>
  );
}
